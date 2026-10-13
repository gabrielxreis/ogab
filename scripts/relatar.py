"""Relatos de erro do Gab: quem instalou e CONCORDOU manda, anônimo, o que quebrou e como foi corrigido (o dono atualiza).

  python3 relatar.py consentir sim|nao     # resposta da pergunta única (instalador ou 1ª abertura); grava "relatos" no config
  python3 relatar.py perguntar             # imprime PERGUNTAR se esta instalação ainda não respondeu (o Gab pergunta 1 vez)
  python3 relatar.py registrar --titulo "..." --erro "..." --causa "..." --correcao "..." [--arquivo scripts/x.py ...]
  python3 relatar.py preset <pasta do modelo | modelo.json>   # motion novo da biblioteca local (biblioteca_motions salvar chama sozinho)
  python3 relatar.py parecido <pasta do modelo | modelo.json>  # quão diferente é da biblioteca (e dos já enviados)
  python3 relatar.py enviar                # manda os pendentes (ao abrir o Gab, em segundo plano) SÓ se "relatos": true
  python3 relatar.py status                # consentimento, pendentes e enviados

Consentimento: sem "relatos": true no config.json nada sai da máquina (relatos ficam só em ~/.claude/ogab_relatos/).
Motions (presets) só saem com o consentimento da pergunta nova ("relatos_v" >= 2), que cita erros E motions.
Preset vai como ESTRUTURA: elementos, tempos, animações e campos; textos de exemplo viram genéricos, sai o autor,
nome de cliente sai pela anonimização e as cores nem ficam no modelo (vêm do cliente na hora de aplicar).
O relato é ANONIMIZADO antes de ser gravado: caminhos viram ~/..., saem e-mails, chaves/tokens, parâmetros de link,
o nome do usuário e o nome de cada cliente (pastas de clientes/ e da pasta de saída). Não vai vídeo, roteiro, legenda
nem transcrição: só o que quebrou na skill, a causa, a correção e o diff dos arquivos DA SKILL.
Na máquina do dono ("dono_biblioteca": true) não envia (ele corrige direto). Destino: relatos/destino.json
(Formulário Google do dono: quem envia só responde; não vê, não edita e não apaga nada).
"""
import glob, hashlib, json, os, platform, re, subprocess, sys, time, urllib.request

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(SKILL, "config.json")
PASTA = os.path.expanduser("~/.claude/ogab_relatos")
PEND, ENV = os.path.join(PASTA, "pendentes"), os.path.join(PASTA, "enviados")
CHAVE_ENVIO = "ogab-relato-v1"
LIMITES = {"titulo": 200, "erro": 3000, "causa": 2000, "correcao": 3000, "diff": 15000}
CONSENTIMENTO_V = 2   # 2 = erros + motions novos
PERGUNTA = ("Posso mandar ao Gabriel, de forma ANÔNIMA, (1) os erros da skill que eu corrigir aqui e (2) a estrutura dos "
            "motions novos que você salvar na biblioteca, para ele melhorar o Gab e publicar os melhores motions para todo "
            "mundo? Não vai vídeo, roteiro, texto do cliente, cor da marca, nome nem pasta. Dá para mudar depois: "
            "/ogab config relatos sim|nao")


def _config():
    try:
        return json.load(open(CONFIG, encoding="utf-8"))
    except Exception:
        return {}


def consentir(sim):
    c = _config(); c["relatos"] = bool(sim); c["relatos_respondido"] = time.strftime("%Y-%m-%d")
    c["relatos_v"] = CONSENTIMENTO_V
    json.dump(c, open(CONFIG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return c["relatos"]


def precisa_perguntar():
    c = _config()
    if c.get("dono_biblioteca"):
        return False
    return "relatos" not in c or (c.get("relatos") is True and int(c.get("relatos_v", 1)) < CONSENTIMENTO_V)


def _destino():
    try:
        return json.load(open(os.path.join(SKILL, "relatos", "destino.json"), encoding="utf-8"))
    except Exception:
        return {}


def _versao():
    try:
        for l in open(os.path.join(SKILL, "CHANGELOG.md"), encoding="utf-8"):
            m = re.match(r"## (\S+)", l)
            if m:
                return m.group(1)
    except Exception:
        pass
    return "?"


def _instalacao():
    """Id aleatório da instalação (conta em quantas máquinas o mesmo erro aconteceu). Não identifica a pessoa."""
    os.makedirs(PASTA, exist_ok=True); arq = os.path.join(PASTA, "instalacao.txt")
    if not os.path.exists(arq):
        open(arq, "w").write(hashlib.sha256(os.urandom(32)).hexdigest()[:12])
    return open(arq).read().strip()


def _nomes_privados(cfg):
    nomes = set()
    for d in glob.glob(os.path.join(SKILL, "clientes", "*")):
        b = os.path.basename(d)
        if os.path.isdir(d) and not b.startswith(("_", ".")):
            nomes.add(b)
            try:
                for l in open(os.path.join(d, "cliente.md"), encoding="utf-8"):
                    m = re.match(r"#\s+(.+)", l)
                    if m:
                        nomes.add(m.group(1).strip()); break
            except Exception:
                pass
    saida = os.path.expanduser(cfg.get("pasta_saida", "~/Desktop"))
    for d in glob.glob(os.path.join(saida, "*")):
        if os.path.isdir(d):
            nomes.add(os.path.basename(d))
    try:
        import pwd
        nomes.add(pwd.getpwuid(os.getuid()).pw_gecos.split(",")[0])
    except Exception:
        pass
    nomes.add(os.path.basename(os.path.expanduser("~")))
    return sorted((n for n in nomes if n and len(n) >= 3), key=len, reverse=True)


def anonimizar(txt, nomes):
    if not txt:
        return ""
    t = str(txt).replace(SKILL, "SKILL_DIR").replace(os.path.expanduser("~"), "~")
    t = re.sub(r"(/Users/|/home/|[A-Za-z]:\\\\?Users\\\\?)[^/\\\s]+", "~", t)
    def _so_ext(m):   # caminho fora da skill (pode ter espaço): sobra só a extensão do arquivo
        e = re.findall(r"\.(\w{1,5})$", m.group(0).rstrip(". "))
        return "~/…/*" + ("." + e[0] if e else "")
    t = re.sub(r"~[/\\](?:(?!, |: |;|\n|['\"]).)*", _so_ext, t)
    t = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "<email>", t)
    t = re.sub(r"\b(sk|pk|rk|ghp|gho|ghs|xox[abp]|AKIA|AIza|ya29)[-_A-Za-z0-9]{12,}", "<chave>", t)
    t = re.sub(r"(?i)\b(api[_-]?key|token|secret|senha|password|authorization|bearer)\b(\s*[:=]\s*|\s+)\S+", r"\1=<oculto>", t)
    t = re.sub(r"\b[A-Za-z0-9_\-]{40,}\b", "<longo>", t)
    t = re.sub(r"(https?://[^\s?#]+)\?[^\s)\"']+", r"\1?<params>", t)
    for n in nomes:
        t = re.sub(re.escape(n), "<cliente>", t, flags=re.I)
    return t


def _assinatura(erro):
    """Mesmo erro em máquinas diferentes = mesma assinatura (números, caminhos e textos entre aspas viram curinga)."""
    e = re.sub(r"\d+(\.\d+)?", "N", erro.lower()); e = re.sub(r"['\"][^'\"]{0,80}['\"]", "S", e)
    e = re.sub(r"~[^\s:]*", "P", e); e = re.sub(r"\s+", " ", e).strip()[:300]
    return hashlib.sha1(e.encode()).hexdigest()[:10]


def registrar(titulo, erro, causa="", correcao="", arquivos=()):
    cfg = _config(); nomes = _nomes_privados(cfg); diff = ""
    if arquivos:
        diff = subprocess.run(["git", "-C", SKILL, "diff", "--"] + list(arquivos), capture_output=True, text=True).stdout
    rel = {"chave_envio": CHAVE_ENVIO, "tipo": "bug", "titulo": titulo, "erro": erro, "causa": causa, "correcao": correcao, "diff": diff}
    for k, lim in LIMITES.items():
        rel[k] = anonimizar(rel[k], nomes)[:lim]
    rel.update({"assinatura": _assinatura(rel["erro"] or rel["titulo"]), "versao": _versao(),
                "sistema": f"{platform.system()} {platform.release()} {platform.machine()}", "python": platform.python_version(),
                "editor": cfg.get("editor", ""), "motion": cfg.get("motion", ""), "instalacao": _instalacao(),
                "quando": time.strftime("%Y-%m-%dT%H:%M:%S")})
    os.makedirs(PEND, exist_ok=True)
    arq = os.path.join(PEND, f"{time.strftime('%Y%m%d-%H%M%S')}-{rel['assinatura']}.json")
    json.dump(rel, open(arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return arq


def _generico(v, i=1):
    if isinstance(v, list):
        return [f"Item {k + 1}" for k in range(len(v))]
    if isinstance(v, (int, float)):
        return v
    return f"Texto {i}"


def _limpar_spec(x):
    """Textos literais do spec (sem {{campo}}) viram genéricos; o resto (tempos, animações, posições) fica."""
    if isinstance(x, dict):
        return {k: (("Texto" if isinstance(v, str) and "{{" not in v else v) if k in ("texto", "text", "rotulo", "legenda")
                    else _limpar_spec(v)) for k, v in x.items()}
    if isinstance(x, list):
        return [_limpar_spec(v) for v in x]
    return x


# ------------------------------------------------------------ motion "bem diferente" do que já existe?
LIMIAR_PARECIDO = 0.70   # similaridade >= isto = variação de um motion que já existe: não manda
BASICAS = {"w", "h", "fps", "nome", "texto", "fonte", "tamanho", "cor", "x", "y", "inicio", "dur", "dur_entrada", "saida_em",
           "elementos", "tipo", "de", "para", "t", "ate", "sufixo", "vars", "passo", "lista", "anim", "entrada", "saida",
           "ease", "repetir", "centralizar"}
VISTOS = os.path.join(PASTA, "presets_vistos.json")


def tracos_motion(modelo):
    """Marcas da ESTRUTURA do motion (elementos, quantidades, animações, técnicas), com peso. Textos, cores, tempos e
    posições não contam: mudar só isso não faz um motion novo."""
    t, cont = {}, {}

    def add(k, w):
        t[k] = max(t.get(k, 0), w)

    def walk(x):
        if isinstance(x, dict):
            if isinstance(x.get("tipo"), str):
                tp = x["tipo"]; cont[tp] = cont.get(tp, 0) + 1
                add(f"el:{tp}", 3.0); add(f"el:{tp}#{min(cont[tp], 4)}", 1.0)
            if "repetir" in x:
                add("repetir", 2.0)
            for k in ("entrada", "saida"):
                if isinstance(x.get(k), str):
                    add(f"{k}:{x[k]}", 2.0)
            if isinstance(x.get("ease"), str):
                add(f"ease:{x['ease'].split('.')[0]}", 0.5)
            for a in (x.get("anim") or []) if isinstance(x.get("anim"), list) else [x.get("anim")] if isinstance(x.get("anim"), dict) else []:
                if isinstance(a, dict):
                    for k in a:
                        if k not in ("t", "dur", "ease", "de", "para", "inicio"):
                            add(f"anima:{k}", 1.5)
            for k, v in x.items():
                if k not in BASICAS:
                    add(f"usa:{k}", 1.0)
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(modelo.get("spec", {}))
    return t


def similaridade(a, b):
    ks = set(a) | set(b)
    if not ks:
        return 1.0
    return sum(min(a.get(k, 0), b.get(k, 0)) for k in ks) / sum(max(a.get(k, 0), b.get(k, 0)) for k in ks)


def _referencias():
    refs = {}
    for f in glob.glob(os.path.join(SKILL, "biblioteca_motions", "*", "modelo.json")):
        try:
            refs["biblioteca:" + os.path.basename(os.path.dirname(f))] = tracos_motion(json.load(open(f, encoding="utf-8")))
        except Exception:
            pass
    try:
        for nome, tr in json.load(open(VISTOS, encoding="utf-8")).items():
            refs["enviado:" + nome] = tr
    except Exception:
        pass
    return refs


def parecido(modelo, ignorar=""):
    """[(similaridade, referência)] do mais parecido ao menos parecido."""
    tr = tracos_motion(modelo)
    return sorted(((round(similaridade(tr, r), 2), n) for n, r in _referencias().items() if n.split(":", 1)[1] != ignorar),
                  reverse=True)


def registrar_preset(caminho):
    arq = os.path.join(caminho, "modelo.json") if os.path.isdir(caminho) else caminho
    m = json.load(open(arq, encoding="utf-8"))
    ranking = parecido(m, ignorar=m.get("nome", ""))
    if ranking and ranking[0][0] >= LIMIAR_PARECIDO:
        return None   # variação de um motion que já existe (mesma estrutura com outros textos/tempos): não manda
    tracos = tracos_motion(m)
    m.pop("autor", None)
    for i, (k, c) in enumerate((m.get("campos") or {}).items(), 1):
        if isinstance(c, dict) and "exemplo" in c:
            c["exemplo"] = _generico(c["exemplo"], i)
    m["spec"] = _limpar_spec(m.get("spec", {}))
    cfg = _config(); nomes = _nomes_privados(cfg)
    corpo = anonimizar(json.dumps(m, ensure_ascii=False, indent=1), nomes)[:40000]
    estrutura = json.dumps(m.get("spec", {}), sort_keys=True)
    rel = {"chave_envio": CHAVE_ENVIO, "tipo": "preset", "titulo": anonimizar(m.get("nome", "motion"), nomes)[:200],
           "erro": anonimizar(m.get("descricao", ""), nomes)[:3000], "causa": ", ".join(m.get("tags", []))[:2000],
           "correcao": (f"novidade {1 - (ranking[0][0] if ranking else 0):.0%} (mais parecido: "
                        f"{ranking[0][1] if ranking else 'nenhum'} {ranking[0][0] if ranking else 0:.0%}); "
                        f"dur {m.get('dur', '?')} s; campos: {', '.join(m.get('campos', {}))}")[:3000], "diff": corpo,
           "assinatura": hashlib.sha1(estrutura.encode()).hexdigest()[:10], "versao": _versao(),
           "sistema": f"{platform.system()} {platform.release()} {platform.machine()}", "python": platform.python_version(),
           "editor": cfg.get("editor", ""), "motion": cfg.get("motion", ""), "instalacao": _instalacao(),
           "quando": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if any(rel["assinatura"] in os.path.basename(f) for f in glob.glob(os.path.join(PASTA, "*", "*.json"))):
        return None   # este motion (mesma estrutura) já foi registrado
    os.makedirs(PEND, exist_ok=True)
    try:
        vistos = json.load(open(VISTOS, encoding="utf-8"))
    except Exception:
        vistos = {}
    vistos[rel["titulo"]] = tracos
    json.dump(vistos, open(VISTOS, "w", encoding="utf-8"), ensure_ascii=False)
    saida = os.path.join(PEND, f"{time.strftime('%Y%m%d-%H%M%S')}-preset-{rel['assinatura']}.json")
    json.dump(rel, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return saida


def _log(msg):
    os.makedirs(PASTA, exist_ok=True)
    with open(os.path.join(PASTA, "envio.log"), "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


def enviar():
    cfg = _config(); dest = _destino()
    if cfg.get("relatos") is not True or cfg.get("dono_biblioteca") or not dest.get("action"):   # só com consentimento
        return 0
    import urllib.parse
    os.makedirs(ENV, exist_ok=True); n = 0
    for arq in sorted(glob.glob(os.path.join(PEND, "*.json")))[:20]:
        try:
            rel = json.load(open(arq, encoding="utf-8"))
            if rel.get("tipo") == "preset" and int(cfg.get("relatos_v", 1)) < CONSENTIMENTO_V:
                continue   # motion só com o consentimento novo
            dados = urllib.parse.urlencode({f"entry.{eid}": str(rel.get(nome, ""))
                                            for nome, eid in dest["campos"].items()}).encode()
            req = urllib.request.Request(dest["action"], data=dados, method="POST",
                                         headers={"Content-Type": "application/x-www-form-urlencoded"})
            if urllib.request.urlopen(req, timeout=20).status == 200:   # Formulário Google: 200 = resposta gravada
                os.replace(arq, os.path.join(ENV, os.path.basename(arq))); n += 1
        except Exception as e:
            _log(f"falhou {os.path.basename(arq)}: {e}"); break   # sem internet: tenta de novo na próxima abertura
    if n:
        _log(f"{n} relato(s) enviado(s)")
    return n


def status():
    cfg = _config(); url = _destino().get("action", "")
    cons = "sim" if cfg.get("relatos") is True else "não" if cfg.get("relatos") is False else "ainda não respondeu"
    return {"consentimento": cons, "maquina_do_dono": bool(cfg.get("dono_biblioteca")), "destino": bool(url),
            "pendentes": len(glob.glob(os.path.join(PEND, "*.json"))), "enviados": len(glob.glob(os.path.join(ENV, "*.json")))}


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    if a[0] == "consentir" and len(a) >= 2:
        print("relatos:", "sim" if consentir(a[1].lower() in ("sim", "s", "yes", "y", "1", "true")) else "não")
    elif a[0] == "perguntar":
        if precisa_perguntar():
            print("PERGUNTAR: " + PERGUNTA)
    elif a[0] == "registrar":
        def arg(n, pad=""):
            return a[a.index(n) + 1] if n in a else pad
        arqs = [a[i + 1] for i, x in enumerate(a) if x == "--arquivo" and i + 1 < len(a)]
        print(registrar(arg("--titulo"), arg("--erro"), arg("--causa"), arg("--correcao"), arqs))
    elif a[0] == "preset" and len(a) >= 2:
        print(registrar_preset(a[1]) or "não registrado: igual ou parecido demais com um motion que já existe")
    elif a[0] == "parecido" and len(a) >= 2:
        arq = os.path.join(a[1], "modelo.json") if os.path.isdir(a[1]) else a[1]
        m = json.load(open(arq, encoding="utf-8"))
        for sim, n in parecido(m, ignorar=m.get("nome", ""))[:5]:
            print(f"  {sim:.0%}  {n}" + ("  <- parecido demais, não seria enviado" if sim >= LIMIAR_PARECIDO else ""))
    elif a[0] == "enviar":
        enviar()
    elif a[0] == "status":
        print(json.dumps(status(), ensure_ascii=False))
    else:
        raise SystemExit(__doc__)
