"""LEGADO: a planilha foi desativada em 26/10/2026; presets e relatos chegam SÓ pela VPS (scripts/presets_vps.py).
Os comandos listar/ver/previa/aceitar/recusar seguem valendo para os candidatos já baixados.

Banco de presets da comunidade (lado do DONO): puxa os motions que os usuários criaram, compara com o banco
inteiro e publica os bons para todo mundo no próximo update. Assim a biblioteca cresce com quem usa o Gab.

  python3 banco_presets.py puxar [--csv respostas.csv]   # lê a planilha, remonta cada motion novo e cada INVENÇÃO
                                                         # (script novo ou melhoria na skill, em candidatos/<id>/pacote.txt)
  python3 banco_presets.py listar                        # candidatos do mais novo (diferente) ao mais repetido
  python3 banco_presets.py ver <id>                      # descrição, novidade, arquivos e de quantas máquinas veio
  python3 banco_presets.py previa <id>                   # renderiza a prévia (HyperFrames) em cinza: só para avaliar
  python3 banco_presets.py aceitar <id> --nome <nome> [--descricao "..."] [--previa quadro.png] [--sem-push]
  python3 banco_presets.py recusar <id> ["motivo"]       # fraco ou repetido: marca resolvido e apaga o candidato
  python3 banco_presets.py catalogo                      # refaz biblioteca_motions/CATALOGO.md (o banco inteiro)

De onde vem: a planilha "Relatos do Gab (respostas)" (relatos/destino.json). Leitura pelo `gws` (Google Workspace
CLI logado numa conta que enxerga a planilha; basta Leitor) ou, se o gws não estiver logado, por um CSV baixado no Chrome logado:
  https://docs.google.com/spreadsheets/d/<planilha_id>/export?format=csv&gid=<aba_gid>
Só entram as linhas de `tipo` preset que ainda não foram resolvidas (relatos.py resolvidos). Partes do mesmo motion
(pacote HyperFrames em até 4 relatos) são juntadas pela assinatura; motion enviado por várias máquinas conta "vezes".

Candidatos ficam em ~/.claude/ogab_relatos/candidatos/<id>/ (fora do git). A novidade é recalculada aqui contra
o banco ATUAL (presets/ da skill + biblioteca_motions/), porque outro usuário pode ter mandado parecido antes.
Aceitar = recolorir/preencher se precisar, salvar na biblioteca com "autor": "comunidade" (biblioteca_motions.salvar),
refazer o catálogo, commit + push (todo usuário recebe no auto-update) e `relatos.py resolver`. Depois apagar as
linhas da planilha (ver relatos/LEIA.md).
"""
import csv, glob, io, json, os, re, shutil, subprocess, sys, tempfile, time

AQUI = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import relatar, relatos   # noqa: E402

CAND = os.path.expanduser("~/.claude/ogab_relatos/candidatos")
CATALOGO = os.path.join(SKILL, "biblioteca_motions", "CATALOGO.md")
COLUNAS = ("titulo", "erro", "causa", "correcao", "diff", "assinatura", "versao", "sistema", "editor", "instalacao", "tipo")


# ------------------------------------------------------------------ leitura da planilha
def _destino():
    return json.load(open(os.path.join(SKILL, "relatos", "destino.json"), encoding="utf-8"))


def _linhas_gws():
    d = _destino()
    meta = subprocess.run(["gws", "sheets", "spreadsheets", "get", "--params",
                           json.dumps({"spreadsheetId": d["planilha_id"], "fields": "sheets.properties"})],
                          capture_output=True, text=True, timeout=60)
    if meta.returncode:
        raise RuntimeError((meta.stdout + meta.stderr).strip()[-300:])
    abas = json.loads(meta.stdout[meta.stdout.index("{"):]).get("sheets", [])
    aba = next((s["properties"]["title"] for s in abas if str(s["properties"].get("sheetId")) == str(d.get("aba_gid"))),
               abas[0]["properties"]["title"] if abas else "Sheet1")
    r = subprocess.run(["gws", "sheets", "spreadsheets", "values", "get", "--params",
                        json.dumps({"spreadsheetId": d["planilha_id"], "range": f"'{aba}'"})],
                       capture_output=True, text=True, timeout=120)
    if r.returncode:
        raise RuntimeError((r.stdout + r.stderr).strip()[-300:])
    return json.loads(r.stdout[r.stdout.index("{"):]).get("values", [])


def linhas(csv_arq=None):
    """[{coluna: valor}] das respostas. Cabeçalho do Formulário: carimbo + os títulos das perguntas (titulo, erro...)."""
    if csv_arq:
        brutas = list(csv.reader(io.open(csv_arq, encoding="utf-8-sig", newline="")))
    else:
        try:
            brutas = _linhas_gws()
        except Exception as e:
            d = _destino()
            raise SystemExit(
                "Não consegui ler a planilha pelo gws (" + str(e)[:160] + ").\n"
                "Opção 1: logar no terminal com a conta que enxerga a planilha (ou compartilhar a planilha como Leitor "
                "com a conta do gws; 403 = essa conta não tem acesso):\n  gws auth login --scopes "
                "https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets\n"
                "Opção 2: no Chrome logado na conta da planilha, baixar o CSV e rodar com --csv:\n  "
                f"https://docs.google.com/spreadsheets/d/{d['planilha_id']}/export?format=csv&gid={d.get('aba_gid', '0')}")
    if not brutas:
        return []
    cab = [c.strip().lower() for c in brutas[0]]
    r = []
    for n, v in enumerate(brutas[1:], 2):
        d = {cab[i]: (v[i] if i < len(v) else "") for i in range(len(cab))}
        d["_linha"] = n
        r.append(d)
    return r


# ------------------------------------------------------------------ candidatos
def _titulo_base(t):
    return re.sub(r"\s*\(parte \d+/\d+\)\s*$", "", t or "").strip() or "motion"


def _novidade(pasta):
    m = _modelo_da_pasta(pasta)
    rk = relatar.parecido(m, ignorar=m.get("nome", ""))
    rk = [x for x in rk if not x[1].startswith("enviado:")]   # só o banco publicado conta
    return (round(1 - rk[0][0], 2), rk[0][1]) if rk else (1.0, "nenhum")


def _modelo_da_pasta(pasta):
    m = json.load(open(os.path.join(pasta, "modelo.json"), encoding="utf-8"))
    m["_pasta"] = pasta
    if relatar._e_hyperframes(m):
        m["_arquivos"] = relatar._arquivos_hf(pasta)
    return m


def puxar(csv_arq=None):
    resolvidos = relatos.resolvidos()
    grupos = {}
    for l in linhas(csv_arq):
        tipo = (l.get("tipo") or "").strip().lower()
        if tipo not in ("preset", "invencao"):
            continue
        a = (l.get("assinatura") or "").strip()
        if not a or a in resolvidos:
            continue
        g = grupos.setdefault(a, {"titulo": _titulo_base(l.get("titulo")), "descricao": l.get("erro", ""),
                                  "tags": l.get("causa", ""), "relato": l.get("correcao", ""), "partes": {},
                                  "instalacoes": set(), "linhas": [], "versao": l.get("versao", ""), "tipo": tipo})
        diff = l.get("diff", "")
        m = re.match(r"=== PACOTE (?:HYPERFRAMES|INVENCAO) ogab v1 parte (\d+)/(\d+) ===", diff)
        g["partes"][int(m.group(1)) if m else 1] = diff
        g["total"] = int(m.group(2)) if m else 1
        g["instalacoes"].add(l.get("instalacao", "?"))
        g["linhas"].append(l["_linha"])
    os.makedirs(CAND, exist_ok=True)
    saida = []
    for a, g in grupos.items():
        pasta = os.path.join(CAND, a)
        if os.path.isdir(pasta):
            shutil.rmtree(pasta)
        os.makedirs(pasta)
        completo = partes_ok = len(g["partes"]) >= g["total"]
        corpo = "".join(g["partes"][k] for k in sorted(g["partes"]))
        if g["tipo"] == "invencao":   # script novo ou melhoria na skill: o dono lê, testa e incorpora à mão
            texto = re.sub(r"^=== PACOTE INVENCAO ogab v1 parte \d+/\d+ ===\n", "", corpo, flags=re.M)
            open(os.path.join(pasta, "pacote.txt"), "w", encoding="utf-8").write(texto)
            arqs = ["pacote.txt"]
        elif corpo.startswith("=== PACOTE HYPERFRAMES"):
            arqs = relatar.desempacotar(corpo, pasta)
            if completo:   # todas as partes chegaram: confere arquivo por arquivo contra o manifesto do envio
                completo, problemas = relatar.conferir_pacote(pasta)
                g["problemas"] = problemas
        else:   # motion do After Effects: a coluna diff é o próprio modelo.json
            open(os.path.join(pasta, "modelo.json"), "w", encoding="utf-8").write(corpo)
            arqs = ["modelo.json"]
        meta = {"id": a, "tipo": g["tipo"], "titulo": g["titulo"], "descricao": g["descricao"], "tags": g["tags"], "relato": g["relato"],
                "vezes": len(g["linhas"]) // max(1, g["total"]), "maquinas": len(g["instalacoes"]),
                "linhas_planilha": sorted(g["linhas"]), "completo": completo,
                "partes": f"{len(g['partes'])}/{g['total']}", "arquivos": arqs, "versao": g["versao"],
                "problemas": ([] if partes_ok else [f"chegaram {len(g['partes'])} de {g['total']} parte(s)"]) + g.get("problemas", []),
                "puxado": time.strftime("%Y-%m-%d %H:%M")}
        if g["tipo"] == "invencao":
            meta["novidade"], meta["mais_parecido"] = 1.0, "invenção (ler pacote.txt)"
        else:
          try:
            json.load(open(os.path.join(pasta, "modelo.json"), encoding="utf-8"))
            meta["novidade"], meta["mais_parecido"] = _novidade(pasta)
          except Exception as e:
            meta["novidade"], meta["mais_parecido"], meta["problema"] = 0, "?", f"modelo ilegível: {e}"
        json.dump(meta, open(os.path.join(pasta, "candidato.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        saida.append(meta)
    return saida


def candidatos():
    r = []
    for f in glob.glob(os.path.join(CAND, "*", "candidato.json")):
        try:
            r.append(json.load(open(f, encoding="utf-8")))
        except Exception:
            pass
    return sorted(r, key=lambda m: (-m.get("novidade", 0), -m.get("maquinas", 0)))


def _cand(id_):
    pasta = os.path.join(CAND, id_)
    if not os.path.exists(os.path.join(pasta, "candidato.json")):
        ids = [c["id"] for c in candidatos() if c["id"].startswith(id_)]
        if len(ids) != 1:
            raise SystemExit(f"candidato não encontrado: {id_}. Rode `banco_presets.py listar`.")
        pasta = os.path.join(CAND, ids[0])
    return pasta, json.load(open(os.path.join(pasta, "candidato.json"), encoding="utf-8"))


def previa(id_):
    """Renderiza a prévia do candidato HyperFrames (gerar.py + exemplo/plano.json, ou o index.html direto)."""
    pasta, meta = _cand(id_)
    saida = os.path.join(pasta, "previa.mp4")
    if os.path.exists(os.path.join(pasta, "gerar.py")) and os.path.exists(os.path.join(pasta, "exemplo", "plano.json")):
        subprocess.run([sys.executable, os.path.join(pasta, "gerar.py"), os.path.join(pasta, "exemplo", "plano.json"),
                        tempfile.mkdtemp(prefix="banco_previa_"), "--render", saida, "--gif"], check=True)
        return saida
    raiz = next((d for d in (pasta, os.path.join(pasta, "kit")) if os.path.exists(os.path.join(d, "index.html"))), None)
    if not raiz:
        raise SystemExit("sem index.html nem gerar.py: motion do After Effects, a prévia sai no AE "
                         "(biblioteca_motions.py aplicar + ae_lib.motion)")
    from hf_preset import renderizar
    renderizar(raiz, saida, gif=True)
    return saida


def aceitar(id_, nome, descricao=None, previa_png=None, push=True):
    pasta, meta = _cand(id_)
    if meta.get("tipo") == "invencao":
        raise SystemExit("invenção não vira modelo: ler pacote.txt, testar, incorporar à mão na skill (commit normal) "
                         "e marcar com `recusar <id> \"incorporado em <commit>\"`")
    if not meta.get("completo"):
        print(f"aviso: chegaram só {meta['partes']} partes; conferir se o motion funciona antes de publicar")
    import biblioteca_motions as bm
    m = json.load(open(os.path.join(pasta, "modelo.json"), encoding="utf-8"))
    m["nome"] = nome
    if descricao:
        m["descricao"] = descricao
    m["autor"] = "comunidade"
    m["comunidade"] = {"assinatura": meta["id"], "maquinas": meta.get("maquinas", 1), "recebido": meta.get("puxado", "")}
    if isinstance(m.get("tags"), list) and "comunidade" not in m["tags"]:
        m["tags"].append("comunidade")
    if not previa_png and os.path.exists(os.path.join(pasta, "previa.mp4")):
        previa_png = os.path.join(pasta, "previa.png")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "1.5", "-i", os.path.join(pasta, "previa.mp4"),
                        "-frames:v", "1", previa_png])
    hf = relatar._e_hyperframes(m)
    destino = bm.salvar(m, previa_png, pasta if hf else None, publicar=False)
    gif = os.path.join(pasta, "previa.gif")
    pasta_bib = os.path.join(SKILL, "biblioteca_motions", re.sub(r"[^a-z0-9-]", "-", nome.lower()).strip("-"))
    if os.path.exists(gif):
        shutil.copy(gif, os.path.join(pasta_bib, "previa.gif"))
    for lixo in ("candidato.json", "previa.mp4"):   # meta e render não vão para o repo
        f = os.path.join(pasta_bib, lixo)
        if os.path.exists(f):
            os.remove(f)
    catalogo()
    g = ["git", "-C", SKILL]
    subprocess.run(g + ["add", pasta_bib, CATALOGO], check=True)
    subprocess.run(g + ["commit", "-q", "-m", f"banco de presets: {os.path.basename(pasta_bib)} (comunidade)\n\n"
                        f"{m.get('descricao', '')[:400]}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"],
                   check=True)
    commit = subprocess.run(g + ["rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    ok = (subprocess.run(g + ["push", "-q"]).returncode == 0) if push else False
    relatos.resolver(meta["id"], commit, f"aceito: {os.path.basename(pasta_bib)}")
    shutil.rmtree(pasta, ignore_errors=True)
    return (f"{destino} | commit {commit}" + (" | publicado" if ok else " | push pendente")
            + f"\napagar da planilha as linhas {meta.get('linhas_planilha')}")


def recusar(id_, motivo=""):
    pasta, meta = _cand(id_)
    relatos.resolver(meta["id"], "recusado", motivo or "fraco ou repetido")
    shutil.rmtree(pasta, ignore_errors=True)
    return f"recusado {meta['id']} ({meta['titulo']}); apagar da planilha as linhas {meta.get('linhas_planilha')}"


# ------------------------------------------------------------------ catálogo (o banco inteiro, visível no GitHub)
def _resumo_md(arq):
    try:
        linhas_ = open(arq, encoding="utf-8").read().splitlines()
    except Exception:
        return "", ""
    titulo = next((l[2:].strip() for l in linhas_ if l.startswith("# ")), "")
    para = []
    for l in linhas_:
        if l.startswith(("#", "<", "!", "|", "```")) or not l.strip():
            if para:
                break
            continue
        para.append(l.strip())
    return titulo, " ".join(para)


def _curto(t, n=170):
    t = re.sub(r"\s+", " ", t or "").strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "..."


def catalogo():
    linhas_ = ["# Banco de presets do Gab", "",
               "Todo motion que o Gab sabe fazer: os presets da skill (`presets/`) e os modelos da biblioteca "
               "(`biblioteca_motions/`), incluindo os que vieram da comunidade. Quem usa o Gab e cria um motion bem "
               "diferente destes pode mandar (anônimo, com consentimento) e, se for aprovado, ele entra aqui para "
               "todo mundo no próximo update. Arquivo gerado por `scripts/banco_presets.py catalogo`.", ""]
    pres = []
    for d in sorted(glob.glob(os.path.join(SKILL, "presets", "*", ""))):
        nome = os.path.basename(os.path.dirname(d))
        md = next((os.path.join(d, x) for x in ("PRESET.md", "LEIA.md", "EFEITOS.md") if os.path.exists(os.path.join(d, x))), None)
        if not md or subprocess.run(["git", "-C", SKILL, "ls-files", "--error-unmatch", md],
                                    capture_output=True).returncode:
            continue   # só o que está publicado
        _, desc = _resumo_md(md)
        gif = next((f"presets/{nome}/{g}" for g in ("exemplo.gif",) if os.path.exists(os.path.join(d, g))), "")
        pres.append((nome, desc, gif))
    linhas_ += [f"## Presets da skill ({len(pres)})", "", "| Preset | O que faz | Prévia |", "| --- | --- | --- |"]
    for nome, desc, gif in pres:
        img = f'<img src="../{gif}" width="120">' if gif else ""
        linhas_.append(f"| [{nome}](../presets/{nome}/) | {_curto(desc)} | {img} |")
    bib = []
    for f in sorted(glob.glob(os.path.join(SKILL, "biblioteca_motions", "*", "modelo.json"))):
        try:
            m = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        nome = os.path.basename(os.path.dirname(f))
        prev = next((x for x in ("previa.gif", "previa.png") if os.path.exists(os.path.join(os.path.dirname(f), x))), "")
        bib.append((nome, m, prev))
    linhas_ += ["", f"## Biblioteca de modelos ({len(bib)})", "",
                "| Modelo | Motor | Autor | O que faz | Prévia |", "| --- | --- | --- | --- | --- |"]
    for nome, m, prev in bib:
        motor = "HyperFrames" if m.get("motor") == "hyperframes" else "After Effects"
        img = f'<img src="{nome}/{prev}" width="120">' if prev else ""
        linhas_.append(f"| [{nome}]({nome}/) | {motor} | {m.get('autor', '?')} | {_curto(m.get('descricao'))} | {img} |")
    n_com = sum(1 for _, m, _ in bib if m.get("autor") == "comunidade")
    linhas_ += ["", f"Total: {len(pres) + len(bib)} motions ({n_com} da comunidade).", ""]
    open(CATALOGO, "w", encoding="utf-8").write("\n".join(linhas_))
    return CATALOGO


def main(a):
    if not a:
        raise SystemExit(__doc__)
    cmd = a[0]
    if cmd == "puxar":   # a planilha foi desativada em 26/10/2026: a fila agora é a da VPS
        raise SystemExit("A planilha dos relatos foi DESATIVADA (26/10/2026): presets e relatos chegam SÓ pela VPS.\n"
                         "Use: python3 scripts/presets_vps.py listar | puxar | apagar <path>. Não recriar planilha.")
    if cmd == "puxar_planilha_antiga":
        r = puxar(a[a.index("--csv") + 1] if "--csv" in a else None)
        print(f"{len(r)} motion(s) novo(s) da comunidade em {CAND}")
        main(["listar"])
    elif cmd == "listar":
        cs = candidatos()
        if not cs:
            print("nenhum candidato (rode `banco_presets.py puxar`)")
        for c in cs:
            alerta = "" if c.get("novidade", 0) >= 1 - relatar.LIMIAR_PARECIDO else "  <- parecido com o banco"
            if c.get("tipo") == "invencao":
                print(f"- {c['id']}  INVENÇÃO  {c['maquinas']} máquina(s)  partes {c['partes']}\n    {_curto(c['descricao'], 160)}"
                      f"\n    ler: {os.path.join(CAND, c['id'], 'pacote.txt')} (testar, incorporar à mão e `recusar <id> \"incorporado\"`)")
                continue
            print(f"- {c['id']}  novidade {c.get('novidade', 0):.0%} (mais parecido: {c.get('mais_parecido')})"
                  f"  {c['maquinas']} máquina(s)  partes {c['partes']}{alerta}{'' if c.get('completo') else '  INCOMPLETO: ' + '; '.join(c.get('problemas', [])[:3])}"
                  f"\n    {c['titulo']}: {_curto(c['descricao'], 140)}"
                  + (f"\n    PROBLEMA: {c['problema']}" if c.get("problema") else ""))
    elif cmd == "ver" and len(a) >= 2:
        pasta, meta = _cand(a[1])
        print(json.dumps(meta, ensure_ascii=False, indent=1)); print("pasta:", pasta)
    elif cmd == "previa" and len(a) >= 2:
        print(previa(a[1]))
    elif cmd == "aceitar" and len(a) >= 2 and "--nome" in a:
        def arg(n):
            return a[a.index(n) + 1] if n in a else None
        print(aceitar(a[1], arg("--nome"), arg("--descricao"), arg("--previa"), "--sem-push" not in a))
    elif cmd == "recusar" and len(a) >= 2:
        print(recusar(a[1], " ".join(a[2:])))
    elif cmd == "catalogo":
        print(catalogo())
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
