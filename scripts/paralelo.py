"""Produção em paralelo com trava de segurança (regra do usuário, 30/10/2026: "em vez de fazer uma coisa de cada vez,
faz forks... implementa sistemas de segurança para não dar bug"). Cada frente (voz, música, takes, motion...) roda ao
mesmo tempo que as outras, mas só quando o que ela precisa já existe, sem gastar crédito duas vezes, sem dois agentes no
mesmo navegador ou no editor, e cada uma escrevendo só na sua pasta. Estado em <pasta>/paralelo.json.

  python3 paralelo.py liberar <pasta> roteiro|voz_escolhida|plano|fala_cortada   (SÓ o Gab principal, depois do ok)
  python3 paralelo.py pode <pasta>                       (o que já pode começar agora, o que espera e por quê)
  python3 paralelo.py iniciar <pasta> <frente>[:<bloco>] [--quem <agente>] [--refazer "motivo"]
  python3 paralelo.py concluir <pasta> <frente>[:<bloco>] --saida <arq> [--saida <arq> ...]
  python3 paralelo.py falhou <pasta> <frente>[:<bloco>] --erro "motivo curto"
  python3 paralelo.py dispensar <pasta> <frente>[:<bloco>] --motivo "..."   (tirar do vídeo, SÓ com o ok do usuário)
  python3 paralelo.py recurso <pasta> pegar|soltar navegador|editor --quem <agente>
  python3 paralelo.py status <pasta>
  python3 paralelo.py juntar <pasta>                     (OBRIGATÓRIO antes de montar no editor: sai 0 = PODE_MONTAR)
  python3 paralelo.py painel <pasta do lote|vídeo> [...]  (painel ao vivo no Terminal; OBRIGATÓRIO aberto para `iniciar`)

Frentes: voz, musica, takes, video_ia, imagens, motion:<n> (um bloco de cenas por agente), legenda, sfx.
Sai 1 com o motivo quando a frente não pode (dependência faltando, já rodou, pasta ou recurso de outra frente).
"""
import contextlib, fcntl, json, os, shutil, subprocess, sys, time

# depende: portões (liberar) e/ou frentes concluídas; pasta: a ÚNICA onde a frente escreve; credito: gasta crédito/geração;
# recurso: o que só um agente usa por vez (navegador = o Chrome do usuário; o editor nunca é de uma frente)
FRENTES = {
    "voz":      {"depende": ["roteiro", "voz_escolhida"], "pasta": "narracoes", "credito": True},
    "musica":   {"depende": ["roteiro"], "pasta": "musica", "recurso": "navegador"},
    "takes":    {"depende": ["roteiro", "plano"], "pasta": "brolls/banco", "recurso": "navegador"},
    "video_ia": {"depende": ["roteiro", "plano"], "pasta": "brolls/ia", "credito": True, "recurso": "navegador"},
    "imagens":  {"depende": ["roteiro", "plano"], "pasta": "imagens"},
    "motion":   {"depende": ["plano", "@tempo"], "pasta": "motions/bloco_{bloco}"},
    "legenda":  {"depende": ["@tempo"], "pasta": "legenda"},
    "sfx":      {"depende": ["plano", "motion:*"], "pasta": "sfx"},
}
PORTOES = ("roteiro", "voz_escolhida", "plano", "fala_cortada")
MAX_AGENTES = 3          # frentes rodando ao mesmo tempo (cada agente custa tokens)
TRAVADA_MIN = 45         # rodando há mais que isso sem concluir = travada (conferir antes de esperar mais)
MIDIA = (".wav", ".mp3", ".m4a", ".aac", ".mp4", ".mov", ".webm")


def arq(pasta): return os.path.join(pasta, "paralelo.json")


@contextlib.contextmanager
def estado(pasta, gravar=True):
    """Lê e grava o paralelo.json com trava de arquivo: vários agentes chamando ao mesmo tempo não se atropelam."""
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, ".paralelo.lock"), "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            st = json.load(open(arq(pasta), encoding="utf-8"))
        except FileNotFoundError:
            st = {}
        st.setdefault("portoes", {}); st.setdefault("frentes", {}); st.setdefault("recursos", {})
        yield st
        if gravar:
            tmp = arq(pasta) + ".tmp"
            json.dump(st, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            os.replace(tmp, arq(pasta))   # gravação atômica: nunca fica um JSON pela metade


def voz_do_menu(pasta):
    try:
        d = json.load(open(os.path.join(pasta, "menu_escolha.json"), encoding="utf-8"))
        return ((d.get("escolhas") or {}).get("voz") or [None])[0]
    except Exception:
        return None


def tipo(nome): return nome.split(":")[0]


def requisitos(pasta, nome):
    """Lista do que a frente precisa, já trocando @tempo pelo que dá o tempo das cenas neste vídeo."""
    voz = voz_do_menu(pasta); r = []
    for d in FRENTES[tipo(nome)]["depende"]:
        if d == "@tempo":   # o tempo de cada cena vem da fala: narração por IA, fala gravada já cortada, ou nada
            r += [] if voz == "sem_voz" else (["fala_cortada"] if voz in ("gravacao", "audio") else ["voz"])
        else:
            r.append(d)
    return r


def faltando(st, pasta, nome):
    f = []
    for d in requisitos(pasta, nome):
        if d in PORTOES:
            if not st["portoes"].get(d): f.append(f"portão '{d}' não liberado")
        elif d == "motion:*":
            ms = {k: v for k, v in st["frentes"].items() if tipo(k) == "motion"}
            if not ms: f.append("nenhum bloco de motion iniciado")
            f += [f"{k} ainda {v['estado']}" for k, v in ms.items() if v["estado"] != "concluida"]
        elif st["frentes"].get(d, {}).get("estado") != "concluida":
            f.append(f"frente '{d}' não concluída")
    if tipo(nome) == "voz" and voz_do_menu(pasta) in ("gravacao", "audio", "sem_voz"):
        f.append("o menu diz que este vídeo NÃO tem voz por IA")
    if tipo(nome) == "legenda" and voz_do_menu(pasta) == "sem_voz":
        f.append("vídeo sem voz não tem legenda")
    return f


def pasta_da(nome):
    b = nome.split(":")[1] if ":" in nome else ""
    return FRENTES[tipo(nome)]["pasta"].format(bloco=b)


def minutos(t): return (time.time() - t) / 60


def validar_saida(p):
    """Saída que conta como pronta: existe, não está vazia e, se for mídia, abre com duração."""
    if not os.path.isfile(p): return "não existe"
    if os.path.getsize(p) == 0: return "arquivo vazio"
    if p.lower().endswith(MIDIA) and shutil.which("ffprobe"):
        o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                           capture_output=True, text=True)
        try:
            if float(o.stdout.strip()) < 0.3: return "duração quase zero"
        except ValueError:
            return "ffprobe não lê (arquivo corrompido ou baixando ainda)"
    return None


def cmd_liberar(pasta, portao):
    if portao not in PORTOES: raise SystemExit(f"portão desconhecido: {portao} (use {', '.join(PORTOES)})")
    with estado(pasta) as st:
        st["portoes"][portao] = time.strftime("%Y-%m-%d %H:%M")
    print(f"LIBERADO {portao}")


def cmd_pode(pasta):
    with estado(pasta, gravar=False) as st:
        for t in FRENTES:
            if t == "motion":
                print(f"  motion:<n>  {'PODE (um agente por bloco de cenas)' if not faltando(st, pasta, 'motion:1') else 'espera: ' + '; '.join(faltando(st, pasta, 'motion:1'))}")
                continue
            e = st["frentes"].get(t, {}).get("estado")
            f = faltando(st, pasta, t)
            print(f"  {t:<10} " + (e.upper() if e else ("PODE" if not f else "espera: " + "; ".join(f))))


def cmd_iniciar(pasta, nome, quem, refazer):
    if tipo(nome) not in FRENTES: raise SystemExit(f"frente desconhecida: {nome} (use {', '.join(FRENTES)})")
    # painel ao vivo obrigatório (regra do usuário, 30/10/2026: "faltou o terminal com o progresso das coisas, não pode
    # deixar de ter"); OGAB_SEM_PAINEL=1 só onde não existe painel Terminal (outro app/CLI)
    import painel_paralelo
    if not painel_paralelo.vivo(pasta) and os.environ.get("OGAB_SEM_PAINEL") != "1":
        raise SystemExit("PAINEL_FECHADO: abra antes o painel ao vivo no painel Terminal (run_in_terminal, aba "
                         "\"Progresso: <lote>\"): python3 SKILL_DIR/scripts/paralelo.py painel <pasta do lote ou do vídeo>, "
                         "mande o link [Progresso: <lote>](#terminal/<tab_id>) na conversa e tente de novo. "
                         "Sem painel Terminal (outro app): OGAB_SEM_PAINEL=1 e dizer onde acompanhar.")
    if tipo(nome) == "motion" and ":" not in nome: raise SystemExit("motion precisa do bloco: motion:1, motion:2...")
    with estado(pasta) as st:
        atual = st["frentes"].get(nome)
        if atual and atual["estado"] == "rodando":
            raise SystemExit(f"NAO: {nome} já está rodando ({atual.get('quem')}, há {minutos(atual['inicio']):.0f} min)")
        if atual and atual["estado"] in ("concluida", "dispensada") and not refazer:
            raise SystemExit(f"NAO: {nome} já foi concluída. Refazer só com --refazer \"motivo\""
                             + (" e o OK do usuário (gasta crédito de novo)" if FRENTES[tipo(nome)].get("credito") else ""))
        f = faltando(st, pasta, nome)
        if f: raise SystemExit(f"NAO: {nome} espera: " + "; ".join(f))
        rodando = [k for k, v in st["frentes"].items() if v["estado"] == "rodando"]
        if len(rodando) >= MAX_AGENTES:
            raise SystemExit(f"NAO: já tem {len(rodando)} frentes rodando ({', '.join(rodando)}); máximo {MAX_AGENTES}")
        minha = pasta_da(nome)
        for k in rodando:   # pasta exclusiva: nenhuma frente escreve dentro da pasta de outra
            p = pasta_da(k)
            if minha == p or minha.startswith(p + "/") or p.startswith(minha + "/"):
                raise SystemExit(f"NAO: a pasta {minha} cruza com a de {k} ({p})")
        os.makedirs(os.path.join(pasta, minha), exist_ok=True)
        for k, v in st["frentes"].items():   # refez uma base: quem foi feito em cima dela fica desatualizado
            req = requisitos(pasta, k)
            if v["estado"] == "concluida" and (nome in req or (tipo(nome) == "motion" and "motion:*" in req)):
                v["estado"] = "desatualizada"; v["erro"] = f"{nome} foi refeita depois"
        st["frentes"][nome] = {"estado": "rodando", "quem": quem or "?", "inicio": time.time(), "pasta": minha,
                               "refazer": refazer, "saidas": {}}
    rec = FRENTES[tipo(nome)].get("recurso")
    print(f"INICIADA {nome} -> escreve SÓ em {minha}/"
          + (f"; usa o {rec}: pegar com `recurso pegar {rec}` antes e soltar logo depois" if rec else "")
          + ("; GASTA CRÉDITO: conferir custo antes" if FRENTES[tipo(nome)].get("credito") else ""))


def cmd_concluir(pasta, nome, saidas):
    if not saidas: raise SystemExit("concluir precisa de --saida <arquivo> (o que a frente entregou)")
    with estado(pasta) as st:
        fr = st["frentes"].get(nome)
        if not fr or fr["estado"] != "rodando": raise SystemExit(f"NAO: {nome} não está rodando")
        ruins = []
        for s in saidas:
            p = s if os.path.isabs(s) else os.path.join(pasta, s)
            rel = os.path.relpath(p, pasta)
            if not (rel == fr["pasta"] or rel.startswith(fr["pasta"] + "/")):
                ruins.append(f"{rel}: fora da pasta da frente ({fr['pasta']}/)"); continue
            erro = validar_saida(p)
            if erro: ruins.append(f"{rel}: {erro}")
            else: fr["saidas"][rel] = os.path.getsize(p)
        if ruins:
            fr["saidas"] = {}
            raise SystemExit("NAO concluída (continua rodando):\n  " + "\n  ".join(ruins))
        fr["estado"] = "concluida"; fr["fim"] = time.time()
    soltar_da_frente(pasta, nome)
    print(f"CONCLUIDA {nome} ({len(saidas)} arquivo(s) conferido(s))")


def cmd_falhou(pasta, nome, erro):
    with estado(pasta) as st:
        fr = st["frentes"].get(nome)
        if not fr: raise SystemExit(f"NAO: {nome} nunca foi iniciada")
        fr["estado"] = "falhou"; fr["erro"] = erro; fr["fim"] = time.time()
    soltar_da_frente(pasta, nome)
    print(f"FALHOU {nome}: {erro} (o Gab principal decide: refazer, outra fonte ou seguir sem)")


def soltar_da_frente(pasta, nome):
    """Frente terminou (bem ou mal): solta o recurso SÓ se ainda está com o mesmo agente dela."""
    rec = FRENTES[tipo(nome)].get("recurso")
    if not rec: return
    with estado(pasta) as st:
        dono = st["recursos"].get(rec); quem = st["frentes"][nome].get("quem")
        if dono and dono["quem"] == quem: st["recursos"].pop(rec)


def cmd_dispensar(pasta, nome, motivo):
    if not motivo: raise SystemExit("dispensar precisa de --motivo (e do ok do usuário)")
    with estado(pasta) as st:
        fr = st["frentes"].get(nome)
        if not fr: raise SystemExit(f"NAO: {nome} nunca foi iniciada")
        if fr["estado"] == "rodando": raise SystemExit(f"NAO: {nome} ainda está rodando; parar o agente antes")
        fr["estado"] = "dispensada"; fr["erro"] = motivo; fr["saidas"] = {}
    soltar_da_frente(pasta, nome)
    print(f"DISPENSADA {nome}: {motivo}")


def cmd_recurso(pasta, acao, rec, quem, silencioso=False):
    if rec not in ("navegador", "editor"): raise SystemExit("recurso: navegador ou editor")
    with estado(pasta) as st:
        dono = st["recursos"].get(rec)
        if acao == "pegar":
            if rec == "editor" and quem != "principal":
                raise SystemExit("NAO: o editor (DaVinci/Premiere/CapCut) é só do Gab principal, nunca de uma frente")
            if dono and dono["quem"] != quem and minutos(dono["desde"]) < TRAVADA_MIN:
                raise SystemExit(f"NAO: o {rec} está com {dono['quem']} há {minutos(dono['desde']):.0f} min; esperar soltar")
            st["recursos"][rec] = {"quem": quem, "desde": time.time()}
        else:
            st["recursos"].pop(rec, None)
    if not silencioso: print(f"{rec.upper()} {'com ' + quem if acao == 'pegar' else 'livre'}")


def problemas(st, pasta):
    p = []
    for k, v in st["frentes"].items():
        if v["estado"] == "rodando":
            p.append(f"{k} {'TRAVADA' if minutos(v['inicio']) > TRAVADA_MIN else 'rodando'} há {minutos(v['inicio']):.0f} min ({v.get('quem')})")
        elif v["estado"] == "falhou":
            p.append(f"{k} FALHOU: {v.get('erro')} (refazer com `iniciar`, ou `dispensar` com o ok do usuário)")
        elif v["estado"] == "desatualizada":
            p.append(f"{k} DESATUALIZADA: {v.get('erro')} (refazer com `iniciar --refazer`)")
        for rel, tam in v.get("saidas", {}).items():   # saída sumiu ou mudou depois de conferida
            f = os.path.join(pasta, rel)
            if not os.path.isfile(f): p.append(f"{k}: {rel} sumiu depois de concluída")
            elif os.path.getsize(f) != tam: p.append(f"{k}: {rel} mudou depois de concluída (conferir e concluir de novo)")
    return p


def cmd_status(pasta):
    with estado(pasta, gravar=False) as st:
        print("portões: " + ", ".join(f"{g} {'ok' if st['portoes'].get(g) else '-'}" for g in PORTOES))
        for k, v in sorted(st["frentes"].items()):
            extra = f" há {minutos(v['inicio']):.0f} min" if v["estado"] == "rodando" else ""
            print(f"  {k:<10} {v['estado']}{extra} ({v.get('quem')}) -> {', '.join(v.get('saidas', {})) or v['pasta'] + '/'}")
        for r, d in st["recursos"].items(): print(f"  {r}: com {d['quem']} há {minutos(d['desde']):.0f} min")
        for x in problemas(st, pasta): print("  ATENCAO " + x)


def cmd_juntar(pasta):
    with estado(pasta, gravar=False) as st:
        p = problemas(st, pasta)
        if st["recursos"].get("navegador"): p.append(f"navegador ainda com {st['recursos']['navegador']['quem']}")
    if p:
        print("NAO_MONTAR: resolver antes de mexer no editor:\n  " + "\n  ".join(p)); return 1
    print("PODE_MONTAR: todas as frentes concluídas e conferidas; só o Gab principal monta, um script por vez no editor")
    return 0


def main(a):
    if len(a) < 2: raise SystemExit(__doc__)
    def opt(n, varios=False):
        v = [a[i + 1] for i, x in enumerate(a[:-1]) if x == n]
        return v if varios else (v[0] if v else None)
    c, pasta = a[0], a[1]
    if c == "painel":
        import painel_paralelo; return painel_paralelo.main(a[1:])
    if c == "liberar": cmd_liberar(pasta, a[2])
    elif c == "pode": cmd_pode(pasta)
    elif c == "iniciar": cmd_iniciar(pasta, a[2], opt("--quem"), opt("--refazer"))
    elif c == "concluir": cmd_concluir(pasta, a[2], opt("--saida", True))
    elif c == "falhou": cmd_falhou(pasta, a[2], opt("--erro") or "sem motivo")
    elif c == "dispensar": cmd_dispensar(pasta, a[2], opt("--motivo"))
    elif c == "recurso": cmd_recurso(pasta, a[2], a[3], opt("--quem"))
    elif c == "status": cmd_status(pasta)
    elif c == "juntar": return cmd_juntar(pasta)
    else: raise SystemExit(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
