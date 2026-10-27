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


def _fmt_s(s):
    s = int(max(0, s)); return f"{s // 60}min{s % 60:02d}s" if s >= 60 else f"{s}s"


def barra(nome, pct, fase="", extra="", t0=None, fim=False):
    pct = max(0.0, min(100.0, float(pct)))
    larg = shutil.get_terminal_size((100, 24)).columns - 1   # a linha NUNCA pode quebrar: quebrada, o \r não volta e vira uma linha nova por atualização
    n = 25 if larg >= 100 else 16 if larg >= 60 else 10
    cheio = int(pct / 100 * n); b = "█" * cheio + "░" * (n - cheio)
    resta = ""
    if t0 and 2 < pct < 100:
        gasto = time.time() - t0; resta = f" · falta ~{_fmt_s(gasto * (100 - pct) / pct)}"
    txt = f"{nome}  {b} {pct:5.1f}%{resta}  {fase}{(' · ' + extra) if extra else ''}"
    if len(txt) > larg:
        txt = txt[:max(10, larg - 1)] + "…"
    chave = (nome, int(pct), fase)
    if TTY:
        sys.stdout.write("\r\033[K" + txt + ("\n" if fim else "")); sys.stdout.flush()
    elif fim or _ultimo.get(nome) != chave and (int(pct) % 5 == 0 or fase != (_ultimo.get(nome) or ("", 0, ""))[2]):
        print(txt, flush=True)
    _ultimo[nome] = chave


PCT = re.compile(r"(\d{1,3}(?:[.,]\d+)?)\s*%\s+([^\[\n\r]{0,60})")
QUADROS = re.compile(r"(\d+)\s*/\s*(\d+)\s*(?:frames?|quadros?)", re.I)


def rodar(cmd, nome="render", log=None, shell=False):
    """Roda o comando mostrando só a barra; devolve o código de saída. Porcentagem lida da saída do próprio comando
    (HyperFrames: "45%  Capturing frames"; ffmpeg com -progress: out_time). Sem % na saída, mostra o tempo correndo."""
    log = log or os.path.join(os.path.expanduser("~"), ".claude", "ogab_render_" + re.sub(r"\W+", "_", nome) + ".log")
    t0 = time.time(); pct, fase, extra = 0.0, "começando", ""
    barra(nome, 0, fase)
    with open(log, "w", encoding="utf-8") as lg:
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
    for k, it in enumerate(itens, 1):
        nome, cmd = it.split("::", 1) if "::" in it else (f"trabalho {k}", it)
        print(f"\n[{k}/{n}] {nome}", flush=True)
        if rodar(cmd, nome.strip(), shell=True):
            falhas.append(nome)
    print(f"\nFila: {n - len(falhas)} de {n} prontos" + (f" · falharam: {', '.join(falhas)}" if falhas else ""), flush=True)
    return 1 if falhas else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    if a[0] == "fila":
        raise SystemExit(fila(a[1:]))
    nome = a[a.index("--nome") + 1] if "--nome" in a else "render"
    cmd = a[a.index("--") + 1:] if "--" in a else a
    raise SystemExit(rodar(cmd, nome))
