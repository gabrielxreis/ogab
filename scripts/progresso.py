#!/usr/bin/env python3
"""Progresso do render de MOTION em tempo real, para o usuário acompanhar no Terminal (regra do usuário, 27/10/2026:
"todo motion gerado tem que aparecer no terminal a porcentagem e o link para o usuário tocar e ver o progresso";
export dos softwares de edição não entra).

Uma linha limpa por trabalho: barra, %, fase, quadros e tempo restante. Os logs técnicos vão para <saida>.log.
Rodar SEMPRE no painel Terminal do app (run_in_terminal, aba "Render: <nome>") e mandar o link da aba na conversa.

  python3 progresso.py -- <comando ...>                 # render de motion (HyperFrames, gerar.py --render)
  python3 progresso.py --nome "Vídeo 1" -- <comando ...>
  python3 progresso.py fila "Nome 1::comando 1" "Nome 2::comando 2" ...   # vários em sequência, com o total

Dentro do Python: progresso.hf(cmd, nome, log) (já usado pelo hf_preset.renderizar de todos os presets).
"""
import os, re, shlex, shutil, subprocess, sys, time

TTY = sys.stdout.isatty()
_ultimo = {}
# visual do painel Terminal (pedido do Gabriel 30/10/2026: "o log tá feio e bagunçado"): título em caixa, uma etapa por
# motion, barra recuada e colorida, nada de caminho absoluto na tela (vai tudo para o .log)
_C = {"azul": "\033[38;5;39m", "verde": "\033[38;5;42m", "verm": "\033[38;5;203m", "cinza": "\033[38;5;245m",
      "neg": "\033[1m", "fim": "\033[0m"} if TTY else dict.fromkeys(["azul", "verde", "verm", "cinza", "neg", "fim"], "")


# fila do script de render (pedido do Gabriel 30/10/2026: "mostre quantos de quantos faltam e o progresso total"):
# o titulo grava o total de etapas num arquivo da sessão do script (cada etapa é outro processo python, mas todos
# filhos do mesmo zsh); a etapa marca qual é a atual e a barra mostra uma 2ª linha com o TOTAL.
_ESTADO = os.path.join(os.path.expanduser("~"), ".claude", f"ogab_render_estado_{os.getppid()}.json")


def _estado(novo=None):
    import json
    if novo is not None:
        try: json.dump(novo, open(_ESTADO, "w"))
        except OSError: pass
        return novo
    try: return json.load(open(_ESTADO))
    except (OSError, ValueError): return None


def titulo(txt, limpar=True, total=None):
    """Cabeçalho do trabalho: limpa a aba (o comando comprido que a abriu some) e desenha uma caixa com o nome.
    total = quantas etapas o script vai ter (aí cada etapa mostra 'k de N' e a barra ganha a linha do total)."""
    if total:
        _estado({"total": int(total), "atual": 0, "feitas": 0, "t0": time.time()})
    elif os.path.exists(_ESTADO):
        os.remove(_ESTADO)
    larg = min(64, max(40, len(txt) + 8))
    if TTY and limpar:
        sys.stdout.write("\033[2J\033[3J\033[H")
    c, f = _C["azul"], _C["fim"]
    print(f"{c}╭{'─' * (larg - 2)}╮{f}")
    print(f"{c}│{f}  {_C['neg']}{txt[:larg - 6]}{f}{' ' * (larg - 4 - len(txt[:larg - 6]))}{c}│{f}")
    print(f"{c}╰{'─' * (larg - 2)}╯{f}", flush=True)


def etapa(txt):
    e = _estado(); k = ""
    if e:
        e["atual"] = min(e["total"], e["atual"] + 1); _estado(e)
        k = f"  {_C['cinza']}{e['atual']} de {e['total']}{_C['fim']}"
    print(f"\n  {_C['azul']}▸{_C['fim']} {_C['neg']}{txt}{_C['fim']}{k}", flush=True)


def _linha_total(pct_item):
    """2ª linha da barra: progresso do trabalho inteiro (etapas prontas + a fração da atual) e o tempo que falta."""
    e = _estado()
    if not e or not e.get("atual"):
        return None
    tot = min(100.0, (e["atual"] - 1 + pct_item / 100) / e["total"] * 100)
    n = 25; cheio = int(tot / 100 * n)
    resta = ""
    if tot > 2:
        gasto = time.time() - e["t0"]; resta = f" · falta ~{_fmt_s(gasto * (100 - tot) / tot)}"
    return (f"    {_C['verde']}{'█' * cheio}{_C['cinza']}{'░' * (n - cheio)}{_C['fim']} {tot:3.0f}%  "
            f"{_C['neg']}TOTAL{_C['fim']} · {e['atual']} de {e['total']}{resta}")


def ok(txt):
    print(f"    {_C['verde']}✓{_C['fim']} {txt}", flush=True)


def aviso(txt):
    print(f"    {_C['cinza']}{txt}{_C['fim']}", flush=True)


def resumo(arquivos, pasta=None):
    """Fecho: lista curta do que ficou pronto (só o nome do arquivo) e a pasta uma vez só."""
    e = _estado(); tempo = ""
    if e:
        tempo = f"  {_C['cinza']}{e['total']} de {e['total']} · {_fmt_s(time.time() - e['t0'])} no total{_C['fim']}"
        try: os.remove(_ESTADO)
        except OSError: pass
    print(f"\n  {_C['verde']}{_C['neg']}PRONTO{_C['fim']}{tempo}" + (f"  {_C['cinza']}{pasta}{_C['fim']}" if pasta else ""))
    for a in arquivos:
        print(f"    {_C['verde']}•{_C['fim']} {os.path.basename(a)}")
    sys.stdout.flush()


def _fmt_s(s):
    s = int(max(0, s)); return f"{s // 60}min{s % 60:02d}s" if s >= 60 else f"{s}s"


def barra(nome, pct, fase="", extra="", t0=None, fim=False):
    pct = max(0.0, min(100.0, float(pct)))
    larg = shutil.get_terminal_size((100, 24)).columns - 1   # a linha NUNCA pode quebrar: quebrada, o \r não volta e vira uma linha nova por atualização
    n = 25 if larg >= 100 else 16 if larg >= 60 else 10
    cheio = int(pct / 100 * n); b = "█" * cheio + "░" * (n - cheio)
    falhou = fim and "FALHOU" in fase
    resta = ""
    if t0 and 2 < pct < 100:
        gasto = time.time() - t0; resta = f" · falta ~{_fmt_s(gasto * (100 - pct) / pct)}"
    if fim:   # linha final limpa: ✓ nome · pronto em Xs (ou ✗ em vermelho)
        txt = f"    {'✗' if falhou else '✓'} {nome} · {fase}"
    else:
        txt = f"    {b} {pct:3.0f}%  {nome}{resta}  {fase}{(' · ' + extra) if extra else ''}"
    if len(txt) > larg:
        txt = txt[:max(10, larg - 1)] + "…"
    if TTY:   # cor depois de medir (os códigos não ocupam espaço na tela)
        cor = _C["verm"] if falhou else _C["verde"] if fim else _C["azul"]
        marca = ("✗" if falhou else "✓") if fim else b
        txt = txt.replace(marca, cor + marca + _C["fim"], 1)
    chave = (nome, int(pct), fase)
    if TTY:
        tot = None if fim else _linha_total(pct)
        if tot and len(re.sub(r"\x1b\[[0-9;]*m", "", tot)) > larg:
            tot = None
        # com o total: escreve as 2 linhas e volta o cursor para a 1ª (a próxima atualização reescreve as duas)
        sys.stdout.write("\r\033[K" + txt + (("\n\033[K" + tot + "\033[1A\r") if tot else "")
                         + ("\n\033[K" if fim else "")); sys.stdout.flush()
    elif fim or _ultimo.get(nome) != chave and (int(pct) % 5 == 0 or fase != (_ultimo.get(nome) or ("", 0, ""))[2]):
        print(txt, flush=True)
    _ultimo[nome] = chave


def trava_sem_terminal(nome):
    """LEI do usuário (30/10/2026): todo render de motion tem o link para acompanhar a barra em tempo real. Escondido em
    segundo plano (Bash do agente, subagente, fork) a saída não é um terminal e ninguém vê a barra: recusa. Sem o painel
    Terminal do app (outro app/CLI), OGAB_SEM_PAINEL=1 libera, e aí avisar a pessoa onde acompanhar."""
    if TTY or os.environ.get("OGAB_SEM_PAINEL") == "1":
        return
    raise SystemExit(f"RENDER_SEM_TERMINAL ({nome}): render de motion só no painel Terminal do app (run_in_terminal, aba "
                     f"\"Render: <vídeo>\") e com o link da aba na conversa: [Render: <vídeo>](#terminal/<tab_id>). "
                     f"Lei do usuário, 30/10/2026. Sem painel Terminal: OGAB_SEM_PAINEL=1 e dizer onde acompanhar.")


PCT = re.compile(r"(\d{1,3}(?:[.,]\d+)?)\s*%\s+([^\[\n\r]{0,60})")
QUADROS = re.compile(r"(\d+)\s*/\s*(\d+)\s*(?:frames?|quadros?)", re.I)


def rodar(cmd, nome="render", log=None, shell=False):
    """Roda o comando mostrando só a barra; devolve o código de saída. Porcentagem lida da saída do próprio comando
    (HyperFrames: "45%  Capturing frames"; ffmpeg com -progress: out_time). Sem % na saída, mostra o tempo correndo."""
    log = log or os.path.join(os.path.expanduser("~"), ".claude", "ogab_render_" + re.sub(r"\W+", "_", nome) + ".log")
    trava_sem_terminal(nome)
    t0 = time.time(); pct, fase, extra = 0.0, "começando", ""
    barra(nome, 0, fase)
    with open(log, "w", encoding="utf-8") as lg:
        if not shell and isinstance(cmd, list) and cmd and str(cmd[0]).lower() in ("npx", "npm"):
            cmd = [shutil.which(str(cmd[0])) or cmd[0]] + list(cmd[1:])   # Windows: npx é npx.cmd e o Popen sem shell não acha (o sitecustomize só cobre subprocess.run)
        pr = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
        buf = b""
        while True:
            ch = pr.stdout.read(256)
            if not ch:
                break
            lg.write(ch.decode("utf-8", "replace")); buf += ch
            partes = re.split(rb"[\r\n]", buf); buf = partes.pop()
            for p in partes:
                s = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", p.decode("utf-8", "replace"))
                m = PCT.search(s)
                if m and not s.lstrip().startswith(("[INFO]", "{")):
                    pct = float(m[1].replace(",", ".")); fase = re.sub(r"\s*·\s*falta\s*~\S+", "", m[2]).strip() or fase   # barra de dentro já traz o "falta"
                q = QUADROS.search(s)
                if q:
                    extra = f"quadro {q[1]}/{q[2]}"
                barra(nome, pct, fase, extra, t0)
        code = pr.wait()
    if code == 0:
        barra(nome, 100, f"pronto em {_fmt_s(time.time() - t0)}", "", fim=True)
    else:
        barra(nome, pct, f"FALHOU (código {code}) · log: {log}", "", fim=True)
    return code


def hf(cmd, nome, log=None):
    """Render do HyperFrames com a barra (usado pelo hf_preset.renderizar de todos os presets)."""
    code = rodar(cmd, nome, log)
    if code:
        raise subprocess.CalledProcessError(code, cmd)


def fila(itens):
    """Vários trabalhos em sequência: cada um com a sua barra e o total no cabeçalho."""
    n = len(itens); falhas = []
    if not _estado():   # sem titulo --total antes: a própria fila conta "k de N" e o total
        _estado({"total": n, "atual": 0, "feitas": 0, "t0": time.time()})
    for k, it in enumerate(itens, 1):
        nome, cmd = it.split("::", 1) if "::" in it else (f"trabalho {k}", it)
        etapa(nome.strip())
        if rodar(cmd, nome.strip(), shell=True):
            falhas.append(nome)
    (aviso if falhas else ok)(f"{n - len(falhas)} de {n} prontos" + (f" · falharam: {', '.join(falhas)}" if falhas else ""))
    return 1 if falhas else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    if a[0] == "fila":
        raise SystemExit(fila(a[1:]))
    if a[0] == "titulo":
        total = a[a.index("--total") + 1] if "--total" in a else None
        txt = [x for i, x in enumerate(a[1:], 1) if x != "--total" and a[i - 1] != "--total"]
        titulo(" ".join(txt), total=total); raise SystemExit(0)
    if a[0] in ("etapa", "ok", "aviso"):
        globals()[a[0]](" ".join(a[1:])); raise SystemExit(0)
    if a[0] == "resumo":
        resumo(a[1:]); raise SystemExit(0)
    nome = a[a.index("--nome") + 1] if "--nome" in a else "render"
    cmd = a[a.index("--") + 1:] if "--" in a else a
    # chamada avulsa (sem titulo --total antes): usa o painel novo inteiro, caixa + etapa + resumo, e não a barra solta
    # com o comando comprido em cima (pedido do Gabriel 30/10/2026: "o terminal que apareceu é o antigo, não o novo modelo")
    avulso = not _estado()
    if avulso:
        titulo(nome, total=1); etapa(nome)
    code = rodar(cmd, nome)
    if avulso and code == 0:
        saida = cmd[cmd.index("-o") + 1] if "-o" in cmd[:-1] else None
        resumo([saida] if saida else [], os.path.dirname(saida) if saida else None)
    raise SystemExit(code)
