"""Monta e renderiza um preset HyperFrames de kit único (gráfico, marco, logo reveal...). Usado pelos gerar.py.

  from hf_preset import montar, renderizar
  pasta = montar(kit, plano, pasta, dur, base)                 # copia o kit, grava plano.js, preenche index.html
  renderizar(pasta, "saida.mp4", gif=True)                     # MP4 (HyperFrames) + prévia GIF opcional
"""
import json, os, re, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from componentes import hf  # noqa: E402

HYPERFRAMES = hf()  # versão fixada em versoes.json


def traz(caminho, base, pasta):
    """Copia um arquivo do plano para assets/ e devolve o caminho relativo."""
    if not caminho or re.match(r"^(https?:|data:)", caminho):
        return caminho
    orig = caminho if os.path.isabs(caminho) else os.path.join(base, caminho)
    nome = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(orig))
    os.makedirs(os.path.join(pasta, "assets"), exist_ok=True)
    shutil.copy(orig, os.path.join(pasta, "assets", nome))
    return "assets/" + nome


def montar(kit, plano, pasta, dur):
    os.makedirs(pasta, exist_ok=True)
    for a in os.listdir(kit):
        if a != "index.html":
            shutil.copy(os.path.join(kit, a), pasta)
    open(os.path.join(pasta, "plano.js"), "w", encoding="utf-8").write("window.PLANO = " + json.dumps(plano, ensure_ascii=False) + ";\n")
    html = open(os.path.join(kit, "index.html"), encoding="utf-8").read()
    for k, v in (("%W%", plano["w"]), ("%H%", plano["h"]), ("%FPS%", plano["fps"]), ("%DUR%", round(dur, 3))):
        html = html.replace(k, str(v))
    open(os.path.join(pasta, "index.html"), "w", encoding="utf-8").write(html)
    json.dump({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}},
              open(os.path.join(pasta, "hyperframes.json"), "w"))
    return pasta


def renderizar(pasta, saida, gif=False, trabalhadores=2):
    subprocess.run(["npx", "--yes", HYPERFRAMES, "render", pasta, "--format", "mp4", "-q", "high", "-w", str(trabalhadores), "-o", saida], check=True)
    print("render", saida)
    if gif:   # prévia leve para README e chat: 15 fps, paleta própria
        g = os.path.splitext(saida)[0] + ".gif"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", saida, "-vf",
                        "fps=15,scale=270:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4", g], check=True)
        print("gif", g)


def args_render(a):
    """--render saida.mp4 [--gif] da linha de comando."""
    return (os.path.abspath(a[a.index("--render") + 1]) if "--render" in a else None), "--gif" in a
