"""Guias de tela e medição de centralização dos motions (regra do usuário: motion SEMPRE centralizado).

  python3 guias.py guia [saida.png]
      -> guia 1080x1920 transparente: linhas de centro, área do cutaway, faixa abaixo do queixo,
         faixa da legenda, zonas da interface do Instagram.
  python3 guias.py medir <arquivo.mov|.png> --alvo cutaway|imersivo [--quadros 7] [--json saida.json]
      -> área visível (canal alfa > 40, união de vários quadros), centro e distância do alvo. PASSA com até 6 px.
  python3 guias.py sobrepor <arquivo.mov|.png> <fundo.png> <saida.png> [--t 2.0]
      -> prova visual: fundo + quadro do motion + guia.
"""
import json, os, subprocess, sys, tempfile

W, H = 1080, 1920
ALVOS = {  # centro e área permitida (x0, y0, x1, y1)
    "cutaway": dict(c=(540, 960), area=(60, 740, 1020, 1160)),
    "imersivo": dict(c=(540, 1310), area=(40, 1160, 1040, 1465)),
}
LEGENDA = (1166, 1226)
TOL = 6


def guia(saida="guia_1080x1920.png"):
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 220), fill=(255, 0, 0, 40)); d.rectangle((0, 1600, W, H), fill=(255, 0, 0, 40))   # UI do Instagram
    for nome, cor in (("cutaway", (0, 200, 255, 255)), ("imersivo", (0, 255, 120, 255))):
        a = ALVOS[nome]; d.rectangle(a["area"], outline=cor, width=4)
        cx, cy = a["c"]; d.line((cx - 40, cy, cx + 40, cy), fill=cor, width=4); d.line((cx, cy - 40, cx, cy + 40), fill=cor, width=4)
    d.rectangle((0, LEGENDA[0], W, LEGENDA[1]), fill=(255, 160, 0, 90))
    d.line((W // 2, 0, W // 2, H), fill=(255, 255, 255, 120), width=2); d.line((0, H // 2, W, H // 2), fill=(255, 255, 255, 120), width=2)
    im.save(saida); print("guia ->", saida); return saida


def _quadros(arq, n):
    from PIL import Image
    if arq.lower().endswith(".png"): return [Image.open(arq).convert("RGBA")]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", arq],
                               capture_output=True, text=True).stdout)
    out = []
    with tempfile.TemporaryDirectory() as td:
        for k in range(n):
            t = dur * (0.25 + 0.6 * k / max(1, n - 1)); f = os.path.join(td, f"{k}.png")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", arq, "-frames:v", "1", "-pix_fmt", "rgba", f], check=True)
            out.append(Image.open(f).convert("RGBA").copy())
    return out


def medir(arq, alvo="cutaway", n=7):
    bb = None
    for im in _quadros(arq, n):
        b = im.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
        if b: bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
    if not bb: print("nada visível"); return None
    a = ALVOS[alvo]; cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    dx, dy = a["c"][0] - cx, a["c"][1] - cy; x0, y0, x1, y1 = a["area"]
    dentro = bb[0] >= x0 and bb[1] >= y0 and bb[2] <= x1 and bb[3] <= y1
    ok = abs(dx) <= TOL and abs(dy) <= TOL and dentro
    r = dict(bbox=bb, centro=(round(cx, 1), round(cy, 1)), corrigir=(round(dx, 1), round(dy, 1)), dentro=dentro, ok=ok)
    print(f"{os.path.basename(arq)} [{alvo}] bbox={bb} centro={r['centro']} corrigir={r['corrigir']} dentro={dentro} -> {'PASSA' if ok else 'NÃO PASSA'}")
    return r


def sobrepor(arq, fundo, saida, t=2.0):
    from PIL import Image
    fr = _quadros(arq, 1)[0] if arq.lower().endswith(".png") else None
    if fr is None:
        with tempfile.TemporaryDirectory() as td:
            f = os.path.join(td, "q.png")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", arq, "-frames:v", "1", "-pix_fmt", "rgba", f], check=True)
            fr = Image.open(f).convert("RGBA").copy()
    g = os.path.join(tempfile.gettempdir(), "guia_tmp.png"); guia(g)
    base = Image.open(fundo).convert("RGBA").resize((W, H)); base.alpha_composite(fr); base.alpha_composite(Image.open(g))
    base.convert("RGB").save(saida); print("prova ->", saida)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit()
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if a[0] == "guia": guia(a[1] if len(a) > 1 else "guia_1080x1920.png")
    elif a[0] == "medir":
        r = medir(a[1], opt("--alvo", "cutaway"), int(opt("--quadros", 7)))
        if opt("--json"): json.dump(r, open(opt("--json"), "w"))
        sys.exit(0 if r and r["ok"] else 1)
    elif a[0] == "sobrepor": sobrepor(a[1], a[2], a[3], float(opt("--t", 2.0)))
