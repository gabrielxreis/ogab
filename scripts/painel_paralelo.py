"""Painel ao vivo da produção em paralelo (regra do usuário, 30/10/2026: "esse progresso tem que ser padrão em todos,
crie algo visualmente atrativo no terminal"). Roda no painel Terminal do app e redesenha a cada 2 s: barra TOTAL do
lote, um cartão por vídeo com cada frente (voz, música, takes, motions...) como selo colorido, quem está rodando há
quanto tempo e o que precisa de atenção. Enquanto roda, grava `<vídeo>/.painel_vivo`: sem ele vivo o
`paralelo.py iniciar` recusa (PAINEL_FECHADO), então ninguém dispara frente sem o painel aberto.

  python3 paralelo.py painel <pasta do lote | pasta do vídeo> [<outra pasta> ...]
      (o Gab abre com run_in_terminal, aba "Progresso: <lote>", e manda o link da aba na conversa)
  python3 painel_paralelo.py <pastas...> --uma-vez      (desenha uma vez e sai; para conferir)
"""
import json, os, shutil, sys, time

VIVO = ".painel_vivo"
VIVO_SEG = 30            # painel sem atualizar há mais que isso = fechado
TRAVADA_MIN = 45
ORDEM = ["voz", "musica", "takes", "video_ia", "imagens", "motion", "legenda", "sfx"]
NOME = {"voz": "voz", "musica": "música", "takes": "takes", "video_ia": "vídeo IA", "imagens": "imagens",
        "motion": "motion", "legenda": "legenda", "sfx": "efeitos"}
GIRO = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

TTY = sys.stdout.isatty()
def _c(cod): return f"\033[{cod}m" if TTY else ""
C = {"fim": _c("0"), "neg": _c("1"), "fraco": _c("2"), "azul": _c("38;5;39"), "verde": _c("38;5;42"),
     "verm": _c("38;5;203"), "amar": _c("38;5;214"), "cinza": _c("38;5;245"), "lar": _c("38;5;208"),
     "fundo": _c("48;5;236")}


def videos(args):
    """Aceita a pasta do lote (subpastas com paralelo.json) ou pastas de vídeo; devolve as pastas de vídeo."""
    out = []
    for a in args:
        a = os.path.abspath(os.path.expanduser(a))
        if os.path.isfile(os.path.join(a, "paralelo.json")):
            out.append(a); continue
        for d in sorted(os.listdir(a)) if os.path.isdir(a) else []:
            p = os.path.join(a, d)
            if os.path.isdir(p) and (os.path.isfile(os.path.join(p, "paralelo.json"))
                                     or os.path.isfile(os.path.join(p, "roteiro.txt"))):
                out.append(p)
    return out


def ler(p):
    try: return json.load(open(os.path.join(p, "paralelo.json"), encoding="utf-8"))
    except (OSError, ValueError): return {"portoes": {}, "frentes": {}, "recursos": {}}


def marcar_vivo(pastas):
    t = {"pid": os.getpid(), "t": time.time()}
    for p in pastas:
        try: json.dump(t, open(os.path.join(p, VIVO), "w"))
        except OSError: pass


def vivo(pasta):
    """True se algum painel aberto está cuidando desta pasta de vídeo (o arquivo é renovado a cada 2 s)."""
    try: return time.time() - json.load(open(os.path.join(pasta, VIVO)))["t"] < VIVO_SEG
    except (OSError, ValueError, KeyError): return False


def _min(t): return (time.time() - t) / 60


def _tempo(m): return f"{m:.0f} min" if m >= 1 else f"{m * 60:.0f} s"


def barra(pct, n, cor):
    cheio = int(round(pct / 100 * n))
    return f"{cor}{'━' * cheio}{C['cinza']}{C['fraco']}{'━' * (n - cheio)}{C['fim']}"


def selo(nome, v, giro):
    e = v["estado"]; rot = NOME.get(nome.split(":")[0], nome) + (f" {nome.split(':')[1]}" if ":" in nome else "")
    if e == "concluida": return f"{C['verde']}✓ {rot}{C['fim']}"
    if e == "rodando":
        m = _min(v["inicio"])
        if m > TRAVADA_MIN: return f"{C['amar']}⚠ {rot} {_tempo(m)}{C['fim']}"
        return f"{C['azul']}{giro} {rot}{C['fim']} {C['cinza']}{_tempo(m)}{C['fim']}"
    if e == "falhou": return f"{C['verm']}✗ {rot}{C['fim']}"
    if e == "desatualizada": return f"{C['amar']}↻ {rot}{C['fim']}"
    if e == "dispensada": return f"{C['cinza']}{C['fraco']}– {rot}{C['fim']}"
    return f"{C['cinza']}· {rot}{C['fim']}"


def _vis(s):
    """Largura visível (sem os códigos de cor)."""
    import re
    return len(re.sub(r"\033\[[0-9;]*m", "", s))


def _chave(k):
    t = k.split(":")[0]
    return (ORDEM.index(t) if t in ORDEM else 99, k)


def desenhar(pastas, lote, quadro):
    w = max(60, min(110, shutil.get_terminal_size((90, 40)).columns - 2))
    giro = GIRO[quadro % len(GIRO)]
    linhas, atencao, rodando = [], [], []
    feitas = total = 0
    cartoes = []
    for p in pastas:
        st = ler(p); fr = st.get("frentes", {})
        vals = {k: v for k, v in fr.items() if v["estado"] != "dispensada"}
        f_ok = sum(1 for v in vals.values() if v["estado"] == "concluida")
        feitas += f_ok; total += len(vals)
        pct = f_ok / len(vals) * 100 if vals else 0
        selos = [selo(k, fr[k], giro) for k in sorted(fr, key=_chave)]
        port = st.get("portoes", {})
        for k, v in fr.items():
            if v["estado"] == "rodando":
                rodando.append(f"{os.path.basename(p)} · {k} ({v.get('quem', '?')}, {_tempo(_min(v['inicio']))})")
                if _min(v["inicio"]) > TRAVADA_MIN:
                    atencao.append(f"{os.path.basename(p)}: {k} rodando há {_tempo(_min(v['inicio']))} (TRAVADA? conferir o agente)")
            elif v["estado"] == "falhou":
                atencao.append(f"{os.path.basename(p)}: {k} falhou: {v.get('erro', '')[:60]}")
            elif v["estado"] == "desatualizada":
                atencao.append(f"{os.path.basename(p)}: {k} desatualizada ({v.get('erro', '')[:50]})")
        for r, d in st.get("recursos", {}).items():
            rodando.append(f"{os.path.basename(p)} · {r} com {d.get('quem')}")
        cartoes.append((os.path.basename(p), pct, selos, port))

    pct_tot = feitas / total * 100 if total else 0
    agora = time.strftime("%H:%M:%S")
    # cabeçalho
    tit = f"{C['lar']}◆{C['fim']} {C['neg']}GAB · produção em paralelo{C['fim']}"
    linhas.append(f"{C['azul']}╭{'─' * (w - 2)}╮{C['fim']}")
    pad = w - 4 - _vis(tit) - len(agora)
    linhas.append(f"{C['azul']}│{C['fim']} {tit}{' ' * max(1, pad)}{C['cinza']}{agora}{C['fim']} {C['azul']}│{C['fim']}")
    sub = lote[: w - 6]
    linhas.append(f"{C['azul']}│{C['fim']} {C['cinza']}{sub}{C['fim']}{' ' * (w - 3 - len(sub))}{C['azul']}│{C['fim']}")
    linhas.append(f"{C['azul']}╰{'─' * (w - 2)}╯{C['fim']}")
    # total
    n = w - 34
    cor = C["verde"] if pct_tot >= 100 else C["lar"]
    linhas.append("")
    linhas.append(f"  {C['neg']}TOTAL{C['fim']}  {barra(pct_tot, n, cor)}  {C['neg']}{pct_tot:3.0f}%{C['fim']}"
                  f"  {C['cinza']}{feitas} de {total} prontas{C['fim']}")
    # cartões
    for nome, pct, selos, port in cartoes:
        linhas.append("")
        cor = C["verde"] if pct >= 100 and selos else C["azul"]
        lab = f"  {C['neg']}{nome}{C['fim']} "
        bn = 16
        fio = w - _vis(lab) - bn - 8
        linhas.append(f"{lab}{C['cinza']}{C['fraco']}{'─' * max(2, fio)}{C['fim']} {barra(pct, bn, cor)} {pct:3.0f}%")
        if not selos:
            linhas.append(f"    {C['cinza']}nenhuma frente disparada ainda{C['fim']}")
            continue
        atual, larg = "    ", 4
        for s in selos:
            if larg + _vis(s) + 3 > w and larg > 4:
                linhas.append(atual); atual, larg = "    ", 4
            atual += s + "   "; larg += _vis(s) + 3
        linhas.append(atual)
        g = "  ".join(f"{g} {'✓' if port.get(g) else '·'}" for g in ("roteiro", "voz_escolhida", "plano"))
        linhas.append(f"    {C['cinza']}{C['fraco']}portões: {g.replace('voz_escolhida', 'voz')}{C['fim']}")
    # rodando / atenção
    linhas.append("")
    linhas.append(f"  {C['azul']}{giro}{C['fim']} {C['neg']}Rodando agora{C['fim']}")
    for r in rodando[:8] or ["nada rodando"]:
        linhas.append(f"    {C['cinza']}{r}{C['fim']}")
    if atencao:
        linhas.append("")
        linhas.append(f"  {C['amar']}⚠ Atenção{C['fim']}")
        for a in atencao[:6]:
            linhas.append(f"    {C['amar']}{a}{C['fim']}")
    if total and feitas == total:
        linhas.append("")
        linhas.append(f"  {C['verde']}{C['neg']}✓ Tudo pronto: o Gab pode juntar e montar no editor{C['fim']}")
    linhas.append("")
    linhas.append(f"  {C['cinza']}{C['fraco']}atualiza a cada 2 s · Ctrl-C fecha (e trava frentes novas){C['fim']}")
    return linhas


def main(a):
    uma = "--uma-vez" in a
    args = [x for x in a if not x.startswith("--")]
    if not args: raise SystemExit(__doc__)
    pastas = videos(args)
    if not pastas: raise SystemExit("nenhuma pasta de vídeo achada (precisa de paralelo.json ou roteiro.txt)")
    lote = os.path.basename(os.path.abspath(args[0])) if len(args) == 1 else f"{len(pastas)} vídeos"
    if uma:
        print("\n".join(desenhar(pastas, lote, 0))); return 0
    if TTY: sys.stdout.write("\033[?1049h\033[?25l")   # tela alternativa, sem cursor
    q = 0
    try:
        while True:
            marcar_vivo(pastas)
            tela = desenhar(pastas, lote, q)
            sys.stdout.write("\033[H\033[2J" + "\n".join(tela) + "\n"); sys.stdout.flush()
            q += 1
            for _ in range(4):   # gira o indicador entre as leituras do disco
                time.sleep(0.5)
                if TTY:
                    tela2 = desenhar(pastas, lote, q); q += 1
                    sys.stdout.write("\033[H\033[2J" + "\n".join(tela2) + "\n"); sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        if TTY: sys.stdout.write("\033[?25h\033[?1049l")
        for p in pastas:
            try: os.remove(os.path.join(p, VIVO))
            except OSError: pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
