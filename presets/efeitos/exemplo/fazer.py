"""Renderiza o exemplo dos EFEITOS e corta um GIF por efeito em presets/efeitos/exemplos/.
  python3 presets/efeitos/exemplo/fazer.py <pasta_trabalho>
"""
import os, shutil, subprocess, sys
AQUI = os.path.dirname(os.path.abspath(__file__)); EF = os.path.dirname(AQUI); RAIZ = os.path.dirname(os.path.dirname(EF))
trab = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "efeitos_exemplo"); proj = os.path.join(trab, "proj")
os.makedirs(os.path.join(proj, "fonts"), exist_ok=True)
for f in ("Poppins-Black.ttf", "Poppins-Bold.ttf"):
    shutil.copy(os.path.join(RAIZ, "assets", "fontes", "Poppins", f), os.path.join(proj, "fonts"))
for f in os.listdir(os.path.join(EF, "kit")):
    shutil.copy(os.path.join(EF, "kit", f), proj)
shutil.copy(os.path.join(AQUI, "index.html"), proj)
mp4 = os.path.join(trab, "efeitos.mp4")
subprocess.run(["npx", "--yes", "hyperframes", "render", proj, "--format", "mp4", "--fps", "30", "-o", mp4], check=True)
os.makedirs(os.path.join(EF, "exemplos"), exist_ok=True)
for nome, de, d in (("fisica", 0, 4.2), ("orbe", 4.6, 3.6), ("ascii", 8.5, 3.0), ("lupa", 11.7, 2.6), ("rabisco", 14.5, 3.0)):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(de), "-t", str(d), "-i", mp4, "-vf",
                    "fps=15,scale=300:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                    os.path.join(EF, "exemplos", f"{nome}.gif")], check=True)
print("ok:", mp4)
