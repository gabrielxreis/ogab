"""Gab em equipe (regra do usuário, 03/11/2026: "ele cria uma bifurcação nova naquele processo, cria um para design,
vídeo, tráfego, gestão, e vai ajustando tudo ali; se precisa mandar um orçamento para o cliente, tudo é feito por
ali"). Um pedido que toca várias áreas (calendário de conteúdo, campanha, lançamento, "cuida de tudo do cliente") vira
um PROJETO EM EQUIPE: o Gab principal é o GERENTE (planeja, pega os oks, distribui ajustes, junta e entrega) e cada área
roda numa frente própria (sessão nova no app ou agente), lendo só o mapa da sua área e escrevendo só na sua pasta.
Estado em <pasta>/equipe.json (com trava de arquivo), resumo legível em <pasta>/EQUIPE.md.

  python3 equipe.py criar <pasta> --cliente <nome> --nome "<projeto>" [--frentes design,video,trafego,comercial,gestao]
  python3 equipe.py calendario <pasta> --arquivo calendario.csv     (data,canal,formato,tema,area[,obs]; 1 linha = 1 peça)
  python3 equipe.py liberar <pasta> plano|calendario|escopo          (SÓ o gerente, depois do ok do usuário)
  python3 equipe.py pode <pasta>                                     (frentes que já podem começar e o que falta)
  python3 equipe.py brief <pasta> <frente>                           (texto pronto para abrir a sessão/agente da frente)
  python3 equipe.py iniciar <pasta> <frente> --sessao <id ou nome>
  python3 equipe.py pedido <pasta> <frente> "<ajuste do usuário>"     (fila de ajustes; o gerente também avisa a sessão)
  python3 equipe.py aguardando <pasta> <frente> --pergunta "<decisão que só o usuário toma>"
  python3 equipe.py retomar <pasta> <frente>                         (o usuário respondeu: a frente volta a rodar)
  python3 equipe.py peca <pasta> <id> pronta|aprovada|refazer [--saida <arq>] [--nota "..."]
  python3 equipe.py entregar <pasta> <frente> --resumo "<1-2 linhas>" [--saida <arq> ...]
  python3 equipe.py falhou <pasta> <frente> --erro "<motivo curto>"
  python3 equipe.py recurso <pasta> pegar|soltar navegador|editor --quem <frente>
  python3 equipe.py status <pasta>                                   (compacto: o gerente lê isto, não as pastas)
  python3 equipe.py painel <pasta> [--uma-vez]                       (ao vivo no painel Terminal)

Sai 1 com o motivo quando algo não pode (portão fechado, frente já rodando, recurso de outra frente).
"""
import contextlib, csv, fcntl, json, os, shutil, sys, time

# depende: portões que o gerente libera com o ok do usuário; le: o mapa da área no cofre (a frente lê SÓ isto);
# entrega: o que a frente devolve; recurso: o que só uma frente usa por vez
FRENTES = {
    "design":    {"nome": "Design", "depende": ["calendario"], "le": "docs/etapas/design.md",
                  "entrega": "artes do calendário (post, carrossel, story, capa, criativo em imagem) na marca do cliente"},
    "video":     {"nome": "Vídeo", "depende": ["calendario"], "le": "SKILL.md (Fluxo do vídeo) e docs/etapas/paralelo.md",
                  "entrega": "Reels/vídeos do calendário montados no editor (dentro dela, as frentes do paralelo.py)",
                  "recurso": "editor"},
    "trafego":   {"nome": "Tráfego", "depende": ["plano"], "le": "docs/etapas/trafego.md",
                  "entrega": "plano de mídia, verba, públicos, copy e ganchos; criativos vêm de design e vídeo"},
    "comercial": {"nome": "Comercial", "depende": ["escopo"], "le": "docs/etapas/comercial.md",
                  "entrega": "orçamento/proposta em PDF e mensagem para o cliente (nada sai sem o ok do usuário)"},
    "gestao":    {"nome": "Gestão", "depende": ["plano"], "le": "docs/etapas/negocios.md",
                  "entrega": "cronograma, custos e margem do projeto, números da semana"},
}
PORTOES = ("plano", "calendario", "escopo")
MAX_RODANDO = 4          # frentes ao mesmo tempo (cada sessão custa tokens)
TRAVADA_MIN = 60
AREA_DA_PECA = {"design": "design", "arte": "design", "post": "design", "carrossel": "design", "story": "design",
                "video": "video", "vídeo": "video", "reels": "video", "trafego": "trafego", "tráfego": "trafego",
                "anuncio": "trafego", "anúncio": "trafego"}


def arq(pasta): return os.path.join(pasta, "equipe.json")


@contextlib.contextmanager
def estado(pasta, gravar=True):
    """Lê e grava o equipe.json com trava: o gerente e várias frentes chamando ao mesmo tempo não se atropelam."""
    if not os.path.isfile(arq(pasta)) and gravar is not None:
        raise SystemExit(f"SEM_EQUIPE: {pasta} não tem equipe.json (rode antes: equipe.py criar)")
    with open(os.path.join(pasta, ".equipe.lock"), "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            st = json.load(open(arq(pasta), encoding="utf-8"))
        except FileNotFoundError:
            st = {}
        for k in ("portoes", "frentes", "recursos"):
            st.setdefault(k, {})
        st.setdefault("pecas", [])
        yield st
        if gravar:
            tmp = arq(pasta) + ".tmp"
            json.dump(st, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            os.replace(tmp, arq(pasta))
            escrever_md(pasta, st)


def agora(): return time.strftime("%Y-%m-%d %H:%M")
def minutos(t): return (time.time() - t) / 60


def frente_ok(st, f):
    if f not in st["frentes"]:
        raise SystemExit(f"FRENTE_FORA: '{f}' não faz parte deste projeto ({', '.join(st['frentes'])})")
    return st["frentes"][f]


def faltando(st, f):
    return [p for p in FRENTES[f]["depende"] if p not in st["portoes"]]


def escrever_md(pasta, st):
    """EQUIPE.md: o resumo que qualquer sessão (ou o usuário) lê primeiro ao entrar no projeto."""
    L = [f"# {st.get('nome', 'Projeto')} ({st.get('cliente', '')})", "",
         f"Gerente: Gab principal. Criado em {st.get('criado', '')}. Estado completo em `equipe.json`.", "",
         "## Portões (oks do usuário)"]
    L += [f"- {p}: {'liberado ' + st['portoes'][p] if p in st['portoes'] else 'esperando'}" for p in PORTOES]
    L += ["", "## Frentes"]
    for f, e in st["frentes"].items():
        linha = f"- **{FRENTES[f]['nome']}** ({e.get('estado')})"
        if e.get("sessao"): linha += f", sessão `{e['sessao']}`"
        if e.get("pergunta"): linha += f", PERGUNTA: {e['pergunta']}"
        if e.get("resumo"): linha += f": {e['resumo']}"
        L.append(linha)
        L += [f"  - ajuste pendente: {p['texto']}" for p in e.get("pedidos", []) if not p.get("feito")]
    if st["pecas"]:
        L += ["", "## Calendário", "| # | data | canal | formato | tema | área | estado |", "|---|---|---|---|---|---|---|"]
        L += [f"| {p['id']} | {p['data']} | {p['canal']} | {p['formato']} | {p['tema']} | {p['area']} | {p['estado']} |"
              for p in st["pecas"]]
    open(os.path.join(pasta, "EQUIPE.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")


def cmd_criar(pasta, cliente, nome, frentes):
    if os.path.isfile(arq(pasta)):
        raise SystemExit(f"JA_EXISTE: {pasta} já tem equipe (use status)")
    fs = [f.strip() for f in frentes.split(",") if f.strip()]
    ruins = [f for f in fs if f not in FRENTES]
    if ruins:
        raise SystemExit(f"FRENTE_DESCONHECIDA: {ruins} (existem: {', '.join(FRENTES)})")
    os.makedirs(pasta, exist_ok=True)
    for f in fs:
        os.makedirs(os.path.join(pasta, f), exist_ok=True)
    json.dump({}, open(arq(pasta), "w"))
    with estado(pasta) as st:
        st.update({"cliente": cliente, "nome": nome, "criado": agora()})
        st["frentes"] = {f: {"estado": "esperando", "pedidos": []} for f in fs}
    print(f"EQUIPE_CRIADA: {pasta}\nfrentes: {', '.join(fs)}\nPróximo: plano + calendário para o usuário aprovar.")


def cmd_calendario(pasta, arquivo):
    linhas = list(csv.DictReader(open(arquivo, encoding="utf-8-sig")))
    falta = {"data", "canal", "formato", "tema", "area"} - set(linhas[0] if linhas else {})
    if falta:
        raise SystemExit(f"CSV_INCOMPLETO: faltam as colunas {sorted(falta)}")
    with estado(pasta) as st:
        pecas = []
        for i, l in enumerate(linhas, 1):
            area = AREA_DA_PECA.get(l["area"].strip().lower(), l["area"].strip().lower())
            if area not in st["frentes"]:
                raise SystemExit(f"PECA_SEM_FRENTE: linha {i} é da área '{area}', que não está no projeto")
            pecas.append({"id": i, "data": l["data"], "canal": l["canal"], "formato": l["formato"], "tema": l["tema"],
                          "area": area, "obs": l.get("obs", ""), "estado": "a fazer"})
        st["pecas"] = pecas
        st["portoes"].pop("calendario", None)   # calendário novo pede novo ok
    por = {}
    for p in pecas: por[p["area"]] = por.get(p["area"], 0) + 1
    print(f"CALENDARIO: {len(pecas)} peças ({', '.join(f'{a} {n}' for a, n in por.items())}). Mostrar ao usuário e, "
          "com o ok, `liberar calendario`.")


def cmd_liberar(pasta, portao):
    if portao not in PORTOES:
        raise SystemExit(f"PORTAO_DESCONHECIDO: {portao} (existem: {', '.join(PORTOES)})")
    with estado(pasta) as st:
        if portao == "calendario" and not st["pecas"]:
            raise SystemExit("SEM_CALENDARIO: importe antes (equipe.py calendario --arquivo ...)")
        st["portoes"][portao] = agora()
    print(f"LIBERADO: {portao}")
    cmd_pode(pasta)


def cmd_pode(pasta):
    with estado(pasta, gravar=False) as st:
        for f, e in st["frentes"].items():
            if e["estado"] != "esperando":
                continue
            fal = faltando(st, f)
            print(f"{'PODE' if not fal else 'ESPERA'} {f}" + (f" (falta o ok: {', '.join(fal)})" if fal else ""))


def cmd_brief(pasta, f):
    """O brief é tudo que a sessão nova sabe: curto, sem a conversa do gerente (economia de tokens)."""
    with estado(pasta, gravar=False) as st:
        frente_ok(st, f)
        d = FRENTES[f]
        minhas = [p for p in st["pecas"] if p["area"] == f]
    py = "python3 ~/.claude/skills/ogab/scripts/equipe.py"
    L = [f"/ogab Você é a frente de {d['nome'].upper()} do projeto em equipe \"{st['nome']}\" do cliente {st['cliente']}.",
         f"O gerente é o Gab principal; você cuida SÓ de {d['nome'].lower()}.",
         f"1. Passo zero normal do Gab; depois leia SÓ `{d['le']}` (e o que ele mandar ler na sua etapa) e `{pasta}/EQUIPE.md`.",
         f"2. Escreva SÓ em `{os.path.join(pasta, f)}/`. Dossiê e Instagram do cliente mandam (lei do Gab).",
         f"3. Entrega: {d['entrega']}."]
    if minhas:
        L.append("4. Suas peças do calendário (marcar cada uma com `" + py + f" peca {pasta} <id> pronta --saida <arq>`):")
        L += [f"   - #{p['id']} {p['data']} {p['canal']} {p['formato']}: {p['tema']}" + (f" ({p['obs']})" if p['obs'] else "")
              for p in minhas]
    L += [f"5. Decisão que só o usuário toma (aprovar roteiro, voz, arte, gastar crédito, mandar algo ao cliente): "
          f"`{py} aguardando {pasta} {f} --pergunta \"...\"` e pergunte NESTA sessão; com a resposta, `retomar`.",
          f"6. Ajustes chegam pela fila: confira `{py} status {pasta}` ao terminar cada peça.",
          f"7. Navegador ou editor: `{py} recurso {pasta} pegar navegador --quem {f}` antes e `soltar` depois.",
          f"8. Ao acabar: `{py} entregar {pasta} {f} --resumo \"1-2 linhas\" --saida <arq>`. Não fale com o cliente: "
          "quem entrega é o gerente."]
    print("\n".join(L))


def cmd_iniciar(pasta, f, sessao):
    with estado(pasta) as st:
        e = frente_ok(st, f)
        fal = faltando(st, f)
        if fal:
            raise SystemExit(f"PORTAO_FECHADO: {f} espera o ok de {', '.join(fal)}")
        if e["estado"] == "rodando":
            raise SystemExit(f"JA_RODANDO: {f} na sessão {e.get('sessao')}")
        rod = [x for x, v in st["frentes"].items() if v["estado"] in ("rodando", "aguardando")]
        if len(rod) >= MAX_RODANDO:
            raise SystemExit(f"LIMITE: já há {len(rod)} frentes abertas ({', '.join(rod)}); espere uma entregar")
        e.update({"estado": "rodando", "sessao": sessao, "inicio": time.time(), "erro": None, "pergunta": None})
    print(f"INICIADA: {f} ({sessao})")


def cmd_pedido(pasta, f, texto):
    with estado(pasta) as st:
        e = frente_ok(st, f)
        e.setdefault("pedidos", []).append({"texto": texto, "quando": agora()})
        if e["estado"] == "entregue":
            e["estado"] = "rodando"; e["inicio"] = time.time()   # ajuste reabre a frente
        sessao = e.get("sessao")
    print(f"PEDIDO_ANOTADO: {f}" + (f". Mande à sessão {sessao} (SendMessage)." if sessao else ". Frente ainda não aberta."))


def cmd_aguardando(pasta, f, pergunta):
    with estado(pasta) as st:
        e = frente_ok(st, f)
        e.update({"estado": "aguardando", "pergunta": pergunta})
    print(f"AGUARDANDO: {f}: {pergunta}")


def cmd_retomar(pasta, f):
    with estado(pasta) as st:
        e = frente_ok(st, f)
        e.update({"estado": "rodando", "pergunta": None, "inicio": time.time()})
    print(f"RETOMADA: {f}")


def cmd_peca(pasta, pid, novo, saida, nota):
    if novo not in ("pronta", "aprovada", "refazer"):
        raise SystemExit("ESTADO_PECA: pronta, aprovada ou refazer")
    if saida and not os.path.exists(saida):
        raise SystemExit(f"SAIDA_SUMIU: {saida}")
    with estado(pasta) as st:
        p = next((x for x in st["pecas"] if x["id"] == int(pid)), None)
        if not p:
            raise SystemExit(f"PECA_DESCONHECIDA: #{pid}")
        p["estado"] = novo
        if saida: p["saida"] = os.path.abspath(saida)
        if nota: p["nota"] = nota
        if novo == "refazer":
            st["frentes"][p["area"]].setdefault("pedidos", []).append(
                {"texto": f"refazer peça #{pid}: {nota or 'ver com o usuário'}", "quando": agora()})
    print(f"PECA: #{pid} {novo}")


def cmd_entregar(pasta, f, resumo, saidas):
    for s in saidas:
        if not os.path.exists(s):
            raise SystemExit(f"SAIDA_SUMIU: {s}")
    with estado(pasta) as st:
        e = frente_ok(st, f)
        abertas = [p["id"] for p in st["pecas"] if p["area"] == f and p["estado"] in ("a fazer", "refazer")]
        if abertas:
            raise SystemExit(f"PECAS_ABERTAS: {f} ainda tem as peças {abertas} (marque com `peca` antes de entregar)")
        for p in e.get("pedidos", []):
            p["feito"] = True
        e.update({"estado": "entregue", "resumo": resumo, "saidas": [os.path.abspath(s) for s in saidas],
                  "fim": agora(), "pergunta": None})
        for r, dono in list(st["recursos"].items()):
            if dono == f: del st["recursos"][r]
    print(f"ENTREGUE: {f}: {resumo}")


def cmd_falhou(pasta, f, erro):
    with estado(pasta) as st:
        frente_ok(st, f).update({"estado": "falhou", "erro": erro})
        for r, dono in list(st["recursos"].items()):
            if dono == f: del st["recursos"][r]
    print(f"FALHOU: {f}: {erro}")


def cmd_recurso(pasta, acao, rec, quem):
    if rec not in ("navegador", "editor"):
        raise SystemExit("RECURSO: navegador ou editor")
    with estado(pasta) as st:
        dono = st["recursos"].get(rec)
        if acao == "pegar":
            if dono and dono != quem:
                raise SystemExit(f"RECURSO_OCUPADO: {rec} está com {dono}; adiante outra coisa e tente de novo")
            st["recursos"][rec] = quem
        elif dono == quem:
            del st["recursos"][rec]
    print(f"RECURSO: {rec} {'com ' + quem if acao == 'pegar' else 'livre'}")


def resumo(st):
    """Uma linha por frente + o que precisa do usuário: é o que o gerente lê (nunca as pastas das frentes)."""
    out, atencao = [], []
    for f, e in st["frentes"].items():
        pecas = [p for p in st["pecas"] if p["area"] == f]
        feitas = sum(p["estado"] in ("pronta", "aprovada") for p in pecas)
        linha = f"{f:<10} {e['estado']:<11}" + (f" peças {feitas}/{len(pecas)}" if pecas else "")
        if e["estado"] == "rodando" and e.get("inicio") and minutos(e["inicio"]) > TRAVADA_MIN:
            linha += f"  ⚠ {int(minutos(e['inicio']))} min sem entregar"
        if e.get("resumo") and e["estado"] == "entregue": linha += f"  {e['resumo']}"
        if e.get("erro"): linha += f"  erro: {e['erro']}"
        out.append(linha)
        if e.get("pergunta"): atencao.append(f"{f} pergunta: {e['pergunta']}")
        pend = [p["texto"] for p in e.get("pedidos", []) if not p.get("feito")]
        if pend: atencao.append(f"{f} tem {len(pend)} ajuste(s) na fila")
    falta = [p for p in PORTOES if p not in st["portoes"] and any(p in FRENTES[f]["depende"] for f in st["frentes"])]
    if falta: atencao.append(f"esperando o ok do usuário: {', '.join(falta)}")
    return out, atencao


def cmd_status(pasta):
    with estado(pasta, gravar=False) as st:
        out, atencao = resumo(st)
        tot = len(st["pecas"]); feitas = sum(p["estado"] in ("pronta", "aprovada") for p in st["pecas"])
    print(f"{st['nome']} ({st['cliente']})" + (f": calendário {feitas}/{tot}" if tot else ""))
    print("\n".join(out))
    for a in atencao: print(f"ATENÇÃO: {a}")
    if all(e["estado"] == "entregue" for e in st["frentes"].values()):
        print("TUDO_ENTREGUE: juntar e mostrar ao usuário")


def cmd_painel(pasta, uma_vez):
    tty = sys.stdout.isatty()
    cor = {"entregue": "38;5;42", "rodando": "38;5;39", "aguardando": "38;5;214", "falhou": "38;5;203",
           "esperando": "38;5;245"}
    while True:
        with estado(pasta, gravar=False) as st:
            out, atencao = resumo(st)
            tot = len(st["pecas"]); feitas = sum(p["estado"] in ("pronta", "aprovada") for p in st["pecas"])
            estados = [e["estado"] for e in st["frentes"].values()]
        larg = min(shutil.get_terminal_size((80, 20)).columns, 100) - 20
        frac = feitas / tot if tot else estados.count("entregue") / max(len(estados), 1)
        if tty: print("\033[2J\033[H", end="")
        print(f"\n  {st['nome']}  ·  {st['cliente']}\n")
        print(f"  TOTAL [{'█' * int(larg * frac)}{'░' * (larg - int(larg * frac))}] {int(frac * 100)}%\n")
        for l, e in zip(out, estados):
            c = cor.get(e, "0")
            print(f"  \033[{c}m●\033[0m {l}" if tty else f"  * {l}")
        if atencao:
            print()
            for a in atencao: print(f"  ⚠ {a}")
        print(f"\n  {time.strftime('%H:%M:%S')}")
        if uma_vez or all(e == "entregue" for e in estados):
            return
        time.sleep(3)


def main(a):
    if len(a) < 2:
        raise SystemExit(__doc__)
    c, pasta = a[0], os.path.abspath(os.path.expanduser(a[1]))

    def opt(n, varios=False, padrao=None):
        v = [a[i + 1] for i in range(len(a) - 1) if a[i] == n]
        return v if varios else (v[0] if v else padrao)

    if c == "criar":
        return cmd_criar(pasta, opt("--cliente", padrao=""), opt("--nome", padrao=os.path.basename(pasta)),
                         opt("--frentes", padrao=",".join(FRENTES)))
    if c == "calendario": return cmd_calendario(pasta, opt("--arquivo"))
    if c == "liberar": return cmd_liberar(pasta, a[2])
    if c == "pode": return cmd_pode(pasta)
    if c == "brief": return cmd_brief(pasta, a[2])
    if c == "iniciar": return cmd_iniciar(pasta, a[2], opt("--sessao", padrao="?"))
    if c == "pedido": return cmd_pedido(pasta, a[2], a[3])
    if c == "aguardando": return cmd_aguardando(pasta, a[2], opt("--pergunta", padrao=""))
    if c == "retomar": return cmd_retomar(pasta, a[2])
    if c == "peca": return cmd_peca(pasta, a[2], a[3], opt("--saida"), opt("--nota"))
    if c == "entregar": return cmd_entregar(pasta, a[2], opt("--resumo", padrao=""), opt("--saida", varios=True))
    if c == "falhou": return cmd_falhou(pasta, a[2], opt("--erro", padrao=""))
    if c == "recurso": return cmd_recurso(pasta, a[2], a[3], opt("--quem", padrao="?"))
    if c == "status": return cmd_status(pasta)
    if c == "painel": return cmd_painel(pasta, "--uma-vez" in a)
    raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
