"""COR: gera as LUTs (.cube 33x33x33) dos estilos do grupo `cor` (motor "lut"), a vinheta e a prévia.

  python3 presets/estilos/cor/luts.py gerar             -> <id>/<id>.cube (+ vinheta_9x16.png / vinheta_16x9.png se pedir)
  python3 presets/estilos/cor/luts.py previa [<id> ...] -> <id>/exemplo.gif (LUT + vinheta numa gravação REAL: OGAB_PREVIA_VIDEO)
  python3 presets/estilos/cor/luts.py instalar          -> copia os .cube para <pasta MASTER de LUTs>/OGAB ESTILOS/

Cada look é uma conta nossa, feita aqui do zero, sobre imagem Rec.709 já corrigida (vai DEPOIS da correção normal).
No DaVinci: `instalar` uma vez (a pasta MASTER pede administrador no Mac; sem permissão o script imprime o sudo cp),
depois R.aplicar_grade(r, t, drx=None, lut="OGAB ESTILOS/<id>.cube") põe a LUT no nó 1 de cada take (Graph.SetLUT,
no lugar da LUT DO GAB: o estilo já é a cor final). Conferir com GetNodeGraph().GetLUT(1). A vinheta (LUT não faz
vinheta: é efeito de posição) entra como imagem `vinheta_9x16.png` (ou 16x9) numa trilha acima de tudo, modo Normal.
"""
import json, os, shutil, subprocess, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__)); ESTILOS = os.path.dirname(AQUI)
TRAB = os.path.expanduser("~/.cache/ogab_estilos")
N = 33
LUT_PASTA = ("/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT" if sys.platform == "darwin" else
             os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"), "Blackmagic Design", "DaVinci Resolve", "Support", "LUT"))
SUB = "OGAB ESTILOS"


# ------------------------------------------------------------ ferramentas de cor (rgb 0-1, arrays [..., 3])
def luma(c):
    return c[..., 0:1] * .2126 + c[..., 1:2] * .7152 + c[..., 2:3] * .0722


def sat(c, s):
    y = luma(c)
    return y + (c - y) * s


def curva_s(x, forca):
    """Contraste em S em torno de 0.5 (forca 0 = nada, negativo = suaviza)."""
    s = x - forca * np.sin(2 * np.pi * x) / (2 * np.pi)
    return s


def zonas(c):
    """Pesos de sombra, meio e luz pela luma."""
    y = np.clip(luma(c), 0, 1)
    sh = np.clip(1 - y / .45, 0, 1) ** 1.5
    hi = np.clip((y - .55) / .45, 0, 1) ** 1.5
    return sh, 1 - sh - hi, hi


def pele(c):
    """Peso 0-1 de tom de pele (matiz entre vermelho e amarelo, saturação média, não muito escuro)."""
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    mx, mn = np.max(c, -1), np.min(c, -1)
    s = (mx - mn) / np.maximum(mx, 1e-4)
    # matiz pela ordem r >= g >= b e g no meio do caminho
    h = np.where(mx - mn > 1e-4, (g - b) / np.maximum(mx - mn, 1e-4), 0)
    w = (r >= g) * (g >= b) * np.clip(1 - np.abs(h - .45) / .4, 0, 1) * np.clip((s - .08) / .12, 0, 1) * np.clip(1 - (s - .6) / .25, 0, 1)
    w = w * np.clip((mx - .12) / .15, 0, 1)
    return w[..., None]


# ------------------------------------------------------------ looks
def quente_cinema(c):
    sh, md, hi = zonas(c)
    c = c + sh * np.array([-.004, .006, .018]) + md * np.array([.022, .008, -.018]) + hi * np.array([.026, .012, -.022])
    c = curva_s(np.clip(c, 0, 1), .22)
    c = sat(c, .97)
    return c * .985 + .012   # pretos levemente abertos


def claro_limpo(c):
    c = np.clip(c, 0, 1) ** .86 * 1.02                 # sobe o meio sem estourar
    c = curva_s(np.clip(c, 0, 1), -.12)                # contraste suave
    y = luma(c)
    k = np.clip((y - .7) / .3, 0, 1)                   # brancos limpos: luz quase neutra
    c = c * (1 - k * .6) + y * (k * .6)
    return sat(c, 1.04) * .97 + .03


def pastel_azul(c):
    sh, md, hi = zonas(c)
    c = sat(np.clip(c, 0, 1), .72)
    c = c * .86 + .1                                   # pretos e brancos lavados (pastel)
    c = c + sh * np.array([-.01, .015, .05]) + md * np.array([-.025, .005, .04]) + hi * np.array([-.012, .01, .03])
    return curva_s(np.clip(c, 0, 1), -.08)


def sepia_quente(c):
    y = luma(np.clip(c, 0, 1))
    tom = np.concatenate([y * 1.08 + .03, y * .93 + .02, y * .72 + .01], -1)   # sépia nossa: puxa vermelho/amarelo, tira azul
    c = c * .38 + tom * .62
    c = curva_s(np.clip(c, 0, 1), -.06)
    return c * .88 + np.array([.075, .06, .045])        # pretos lavados e quentes


def editorial_frio(c):
    c = np.clip(c, 0, 1)
    p = pele(c)
    sh, md, hi = zonas(c)
    f = c ** 1.18 * .97                                 # sala mais escura
    f = f + sh * np.array([-.02, .012, .02]) + md * np.array([-.04, .014, .02]) + hi * np.array([-.01, .004, .0])
    f = curva_s(np.clip(f, 0, 1), .18)
    f = sat(f, .86)
    pele_ok = sat(c ** 1.08, .95)                       # pele: só um pouco mais densa, sem o verde-azulado
    return f * (1 - p * .8) + pele_ok * (p * .8)


LOOKS = {
    "quente-cinema": dict(f=quente_cinema, vinheta=.38),
    "claro-limpo": dict(f=claro_limpo, vinheta=0),
    "pastel-azul": dict(f=pastel_azul, vinheta=0),
    "sepia-quente": dict(f=sepia_quente, vinheta=0),
    "editorial-frio": dict(f=editorial_frio, vinheta=.5),
}


# ------------------------------------------------------------ arquivos
def cubo(eid):
    g = np.linspace(0, 1, N)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")     # .cube: vermelho varia mais rápido
    c = np.stack([r, gg, b], -1).reshape(-1, 3)
    o = np.clip(LOOKS[eid]["f"](c), 0, 1)
    arq = os.path.join(AQUI, eid, eid + ".cube")
    with open(arq, "w") as fh:
        fh.write(f'TITLE "ogab {eid}"\n# gerado por presets/estilos/cor/luts.py (skill /ogab)\nLUT_3D_SIZE {N}\n'
                 'DOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n')
        fh.writelines(f"{x:.6f} {y:.6f} {z:.6f}\n" for x, y, z in o)
    return arq


def vinheta(eid, w, h, nome):
    from PIL import Image
    forca = LOOKS[eid]["vinheta"]
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 * .8 + ((yy - h / 2) / (h / 2)) ** 2 * .8)   # elipse no formato do quadro
    a = np.clip((d - .62) / .75, 0, 1) ** 1.6 * forca
    img = np.zeros((h, w, 4), np.uint8); img[..., 3] = (a * 255).astype(np.uint8)
    Image.fromarray(img, "RGBA").save(os.path.join(AQUI, eid, nome), optimize=True)


def gerar():
    for eid, m in LOOKS.items():
        os.makedirs(os.path.join(AQUI, eid), exist_ok=True)
        print("ok:", cubo(eid))
        if m["vinheta"]:
            vinheta(eid, 1080, 1920, "vinheta_9x16.png"); vinheta(eid, 1920, 1080, "vinheta_16x9.png")


def previa(ids):
    video = os.environ.get("OGAB_PREVIA_VIDEO") or os.path.join(TRAB, "gravacao.mp4")
    if not os.path.exists(video):
        raise SystemExit("sem gravação REAL para a prévia (nada de personagem ilustrado): defina OGAB_PREVIA_VIDEO")
    for eid in ids:
        pasta = os.path.join(AQUI, eid); m = json.load(open(os.path.join(pasta, "estilo.json"), encoding="utf-8"))
        ex = m.get("exemplo") or {}; de, ate = ex.get("de", .4), ex.get("ate", 3.4)
        lut = os.path.join(pasta, eid + ".cube").replace("'", r"\'").replace(":", r"\:")
        vin = os.path.join(pasta, "vinheta_9x16.png")
        ent = ["-i", video] + (["-i", vin] if os.path.exists(vin) else [])
        corte = .9   # o look entra varrendo da esquerda para a direita em 0,9 s: dá para ver o antes e o depois
        fx = f"[0:v]split[o][c];[c]lut3d=file='{lut}'"
        fx += "[l];[l][1:v]overlay=0:0[g]" if os.path.exists(vin) else "[g]"
        fx += (f";[o][g]overlay=x='-W+W*min(1,max(0,(t-.25)/{corte}))':y=0,"
               "fps=15,scale=300:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=4")
        gif = os.path.join(pasta, "exemplo.gif")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(de), "-t", str(ate - de)] + ent[:2] +
                       (["-loop", "1", "-t", str(ate - de)] + ent[2:] if len(ent) > 2 else []) +
                       ["-filter_complex", fx, "-loop", "0", gif], check=True)
        print("ok:", gif)


def instalar():
    dst = os.path.join(LUT_PASTA, SUB)
    arqs = [os.path.join(AQUI, e, e + ".cube") for e in LOOKS]
    try:
        os.makedirs(dst, exist_ok=True)
        for a in arqs:
            shutil.copy2(a, dst)
        print("LUTs em", dst, "(no DaVinci: Project.RefreshLUTList(); SetLUT(1, \"OGAB ESTILOS/<id>.cube\"))")
    except PermissionError:
        print("sem permissão na pasta de LUTs do DaVinci; rode:\n  sudo mkdir -p '%s' && sudo cp %s '%s/'"
              % (dst, " ".join(f"'{a}'" for a in arqs), dst))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    if a[0] == "gerar":
        gerar()
    elif a[0] == "previa":
        previa(a[1:] or list(LOOKS))
    elif a[0] == "instalar":
        instalar()
    else:
        raise SystemExit(__doc__)
