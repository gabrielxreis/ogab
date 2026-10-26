#!/usr/bin/env python3
"""Preset WHITEBOARD: uma ilustração vira animação de lousa (a mão desenha as linhas, pinta os personagens e depois o
fundo) e sai em MP4. Motor: whiteboard-animation-vi (letuandat131, código CC0), instalado FORA da skill, em
~/.claude/ogab_ferramentas/whiteboard, com Python próprio (o PyTorch dele não roda no Python 3.14).

  whiteboard.py instalar           instala ou conserta (clona o motor fixado, cria o Python, PyTorch, modelo de recorte)
  whiteboard.py checar             sai 0 se está pronto para gerar
  whiteboard.py garantir           passo zero: se ainda não tem, instala em SEGUNDO PLANO e imprime COMPONENTES: ...
  whiteboard.py gerar <imagem> <saida.mp4> [--formato vertical|horizontal|quadrado|original] [--duracao 8]
                [--modo detalhado|rapido] [--fundo #ffffff] [--sem-mao] [--fps 30]

As mãos e o modelo NÃO vêm no repositório do Gab (sem licença para redistribuir): são baixados do projeto original
na máquina de cada pessoa. Não é preciso placa NVIDIA: no Mac e em PC sem CUDA roda no processador (mais lento).
"""
import json, os, shutil, subprocess, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
MAC, WIN = sys.platform == "darwin", os.name == "nt"
REPO = "https://github.com/letuandat131/whiteboard-animation-vi.git"
COMMIT = "c689bf7fd75fb4cb84f6ae2880a4dac6f40b92d0"   # versão testada; trocar só depois de renderizar o exemplo de novo
BASE = os.path.join(os.path.expanduser("~"), ".claude", "ogab_ferramentas", "whiteboard")
MOTOR = os.path.join(BASE, "motor")
VENV = os.path.join(BASE, "venv")
PRONTO = os.path.join(BASE, "pronto.json")
LOG = os.path.join(BASE, "instalacao.log")
TENTOU = os.path.join(BASE, "tentou_em")
PY = os.path.join(VENV, "Scripts", "python.exe") if WIN else os.path.join(VENV, "bin", "python")
TORCH = ["torch==2.8.0", "torchvision==0.23.0"]
# requirements.txt do motor sem o gradio (o Gab chama a API direto, sem a tela)
PACOTES = ["numpy>=2.4,<2.5", "opencv-python>=5.0,<6", "scipy>=1.17,<1.18", "scikit-image>=0.26,<0.27",
           "safetensors>=0.8,<0.9", "Pillow>=11,<13"]
FORMATOS = {"vertical": (1080, 1920), "horizontal": (1920, 1080), "quadrado": (1080, 1080), "original": (1920, 1080)}


def log(msg):
    os.makedirs(BASE, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
    print(msg, flush=True)


def roda(cmd, **k):
    log("$ " + " ".join(cmd))
    with open(LOG, "a", encoding="utf-8") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, **k)
    if r.returncode:
        raise SystemExit(f"falhou: {' '.join(cmd[:4])}... (detalhes em {LOG})")


def pronto():
    try:
        d = json.load(open(PRONTO, encoding="utf-8"))
        return d.get("commit") == COMMIT and os.path.exists(PY) and os.path.exists(
            os.path.join(MOTOR, "assets", "v181d", "model.safetensors"))
    except (OSError, ValueError):
        return False


def python_base():
    """Um Python 3.10-3.13 para o venv (o PyTorch 2.8 não tem roda para o 3.14)."""
    ok = lambda exe: subprocess.run([*exe, "-c", "import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,13) else 1)"],
                                    capture_output=True).returncode == 0
    cands = [["py", f"-3.{m}"] for m in (12, 11, 13, 10)] if WIN else []
    cands += [[n] for n in ("python3.12", "python3.11", "python3.13", "python3.10", "python3", "python") if shutil.which(n)]
    for c in cands:
        try:
            if ok(c):
                return c
        except OSError:
            pass
    if MAC and shutil.which("brew"):
        roda(["brew", "install", "python@3.12"])
        for p in ("/opt/homebrew/bin/python3.12", "/usr/local/bin/python3.12"):
            if os.path.exists(p):
                return [p]
    if WIN and shutil.which("winget"):
        roda(["winget", "install", "-e", "--id", "Python.Python.3.12", "--accept-package-agreements", "--accept-source-agreements"])
        return ["py", "-3.12"]
    raise SystemExit("preciso de um Python entre 3.10 e 3.13 (Mac: brew install python@3.12; Windows: winget install Python.Python.3.12)")


def tem_cuda():
    return not MAC and shutil.which("nvidia-smi") is not None and subprocess.run(["nvidia-smi"], capture_output=True).returncode == 0


def instalar():
    os.makedirs(BASE, exist_ok=True)
    log(f"instalando o motor do whiteboard em {BASE}")
    if not os.path.isdir(os.path.join(MOTOR, ".git")):
        shutil.rmtree(MOTOR, ignore_errors=True)
        roda(["git", "clone", "--quiet", REPO, MOTOR])
    roda(["git", "-C", MOTOR, "fetch", "--quiet", "origin"])
    roda(["git", "-C", MOTOR, "checkout", "--quiet", "--force", COMMIT])
    if not os.path.exists(PY):
        shutil.rmtree(VENV, ignore_errors=True)
        roda([*python_base(), "-m", "venv", VENV])
    roda([PY, "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    # Mac: roda padrão do PyPI (CPU/MPS). Windows/Linux: CUDA 12.8 se tem NVIDIA, senão a de CPU (bem menor)
    idx = [] if MAC else ["--index-url", "https://download.pytorch.org/whl/" + ("cu128" if tem_cuda() else "cpu")]
    roda([PY, "-m", "pip", "install", "--quiet", *TORCH, *idx])
    roda([PY, "-m", "pip", "install", "--quiet", *PACOTES])
    roda([PY, os.path.join(MOTOR, "scripts", "download_model.py")], cwd=MOTOR)
    json.dump({"commit": COMMIT, "quando": time.strftime("%Y-%m-%d %H:%M"), "cuda": tem_cuda()},
              open(PRONTO, "w", encoding="utf-8"))
    log("whiteboard pronto")


def garantir():
    """Passo zero (componentes.py checar): quem recebeu o preset no update e ainda não tem o motor instala sozinho, sem
    esperar. Imprime linhas COMPONENTES: (o Gab mostra numa linha): ao começar e, uma vez, quando ficou pronto."""
    if pronto():
        if os.path.exists(TENTOU):   # instalou em segundo plano: avisa uma vez que já dá para usar
            os.remove(TENTOU)
            print("COMPONENTES: preset novo Whiteboard pronto (lousa com a mão desenhando): peça \"no preset whiteboard\" ou marque no /ogab menu")
        return
    try:   # uma tentativa por dia, para não ficar refazendo um download que falha
        if time.time() - os.path.getmtime(TENTOU) < 24 * 3600:
            return
        print(f"COMPONENTES: o motor do preset Whiteboard não instalou ontem (log: {LOG}); tentando de novo em segundo plano")
    except OSError:
        print("COMPONENTES: preset novo Whiteboard (lousa com a mão desenhando): instalando o motor em segundo plano (~1 GB, alguns minutos)")
    os.makedirs(BASE, exist_ok=True)
    open(TENTOU, "w").write(time.strftime("%Y-%m-%d %H:%M"))
    k = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    if WIN:
        k["creationflags"] = 0x00000008 | 0x00000200
    else:
        k["start_new_session"] = True
    subprocess.Popen([sys.executable, os.path.abspath(__file__), "instalar"], **k)


RENDER = r"""
import json, sys, shutil
import numpy as np
from PIL import Image
sys.path.insert(0, sys.argv[1])
from handdraw.settings import Settings
from handdraw.render import render_video
a = json.loads(sys.argv[2])
img = np.asarray(Image.open(a.pop("imagem")).convert("RGBA"))
saida = a.pop("saida")
caminho, rel = render_video(img, Settings(**a).validate())
shutil.move(str(caminho), saida)
print(json.dumps({"saida": saida, "relatorio": rel}, default=str))
"""


def gerar(a):
    import argparse
    p = argparse.ArgumentParser(prog="whiteboard.py gerar")
    p.add_argument("imagem")
    p.add_argument("saida")
    p.add_argument("--formato", default="vertical", choices=list(FORMATOS))
    p.add_argument("--duracao", type=float, default=8.0)
    p.add_argument("--modo", default="detalhado", choices=["detalhado", "rapido"])
    p.add_argument("--fundo", default="#ffffff")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--desenho", type=float, default=70, help="%% do tempo desenhando (o resto segura a imagem pronta)")
    p.add_argument("--sem-mao", action="store_true")
    o = p.parse_args(a)
    if not pronto():
        raise SystemExit("WHITEBOARD_NAO_INSTALADO: rode `whiteboard.py instalar` (ou espere a instalação em segundo plano)")
    w, h = FORMATOS[o.formato]
    cuda = json.load(open(PRONTO, encoding="utf-8")).get("cuda")
    conf = {"imagem": os.path.abspath(o.imagem), "saida": os.path.abspath(o.saida), "mode": "d" if o.modo == "detalhado" else "e",
            "duration": o.duracao, "draw_percent": o.desenho, "width": w, "height": h, "fps": o.fps, "paper_color": o.fundo,
            "fit": "original" if o.formato == "original" else "contain", "show_hand": not o.sem_mao,
            "device": "cuda" if cuda else "cpu", "encoder": "cpu"}
    os.makedirs(os.path.dirname(conf["saida"]) or ".", exist_ok=True)
    t = time.time()
    r = subprocess.run([PY, "-c", RENDER, MOTOR, json.dumps(conf)], cwd=MOTOR, capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr[-3000:])
        raise SystemExit("falhou o render do whiteboard")
    print(f"whiteboard: {conf['saida']} ({time.time() - t:.0f} s de render)")


def main(a):
    sub = a[0] if a else ""
    if sub == "instalar":
        instalar()
    elif sub == "checar":
        sys.exit(0 if pronto() else 1)
    elif sub == "garantir":
        garantir()
    elif sub == "gerar":
        gerar(a[1:])
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
