"""Centro do motion ANTES do render (regra do usuário, 12/10/2026: "verifica sempre o centro antes de gerar").

  python3 centro.py medir    <pasta_do_motion> [--tempos 0.5,1.5,3,5]
  python3 centro.py corrigir <pasta_do_motion> [--tempos ...] [--fit fit.json]

Como mede: copia a composição para uma pasta temporária, esconde o fundo (#bg / canvas e o background do body),
tira snapshots do HyperFrames em vários tempos e faz a UNIÃO da caixa do conteúdo visível (canal alfa).
Alvo: centro (540, 960) com tolerância de 6 px. O MOTION NUNCA FOGE DA LEGENDA (regra do usuário, 12/10/2026): não sobe
nem encolhe por causa dela; quem se ajusta é a legenda (desce para Y 390 nas que cruzam o motion). Só reduz se não
couber na ÁREA SEGURA DO INSTAGRAM (regra do usuário, 15/10/2026: "coloque um limite nas bordas... quando postar no
instagram ele dá um cropzinho"): o feed e a grade cortam o Reels 9:16 para 4:5 (1080x1350, perde 285 px em cima e
embaixo) e a interface cobre as laterais; o conteúdo do motion fica numa caixa central de LARGURA_MAX x ALTURA_MAX.
CTA: a regra é a LOGO no centro exato (medir a logo, não a união).
corrigir: calcula translate (+ scale só se não couber na tela) e grava em fit.json {id: "transform-origin...; transform..."};
o build do motion aplica esse estilo num wrapper (#fit) em volta do conteúdo (o fundo fica fora). Depois mede de novo.
Sai com código 1 se não passar (para o build não renderizar motion torto).
"""
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ALVO = (540, 960)
TOL = 6
ALTURA_MAX = 1200   # 4:5 do feed (1350) menos margem: y de 360 a 1560
LARGURA_MAX = 900   # 90 px de margem em cada lado
HF = ["npx", "--yes", "hyperframes@0.8.145"]


def _snap(pasta, tempos):
    pasta = Path(pasta).resolve(); tmp = Path(tempfile.mkdtemp(prefix="centro_"))
    dst = tmp / pasta.name; shutil.copytree(pasta, dst, ignore=shutil.ignore_patterns("snapshots"))
    html = (dst / "index.html").read_text()
    html = html.replace("</style>", "#bg, canvas { display: none !important; } html, body { background: transparent !important; }\n</style>", 1)
    (dst / "index.html").write_text(html)
    subprocess.run(HF + ["snapshot", str(dst), "--at", ",".join(str(t) for t in tempos)],
                   capture_output=True, text=True, cwd=str(tmp))
    pngs = sorted((dst / "snapshots").glob("*.png"))
    if not pngs: raise SystemExit(f"sem snapshots de {pasta}")
    return pngs, tmp


def medir(pasta, tempos):
    import numpy as np
    from PIL import Image
    pngs, tmp = _snap(pasta, tempos)
    x0 = y0 = 10 ** 9; x1 = y1 = -1
    for p in pngs:
        im = Image.open(p)
        a = np.asarray(im.convert("RGBA"))[..., 3] if im.mode in ("RGBA", "LA") or "transparency" in im.info else None
        if a is None or a.max() == 0 or a.min() == 255:   # snapshot sem alfa: usa brilho sobre preto
            rgb = np.asarray(im.convert("RGB")).astype(int); a = (rgb.max(axis=2) > 40).astype(np.uint8) * 255
        ys, xs = np.where(a > 40)
        if len(xs) == 0: continue
        x0, x1 = min(x0, xs.min()), max(x1, xs.max()); y0, y1 = min(y0, ys.min()), max(y1, ys.max())
    shutil.rmtree(tmp, ignore_errors=True)
    if x1 < 0: raise SystemExit("nada visível nos snapshots")
    cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    ok = abs(cx - ALVO[0]) <= TOL and abs(cy - ALVO[1]) <= TOL and h <= ALTURA_MAX + 2 and w <= LARGURA_MAX + 2
    return dict(cx=round(cx, 1), cy=round(cy, 1), w=int(w), h=int(h), y0=int(y0), y1=int(y1), ok=bool(ok))


def correcao(m):
    s = min(1.0, ALTURA_MAX / max(m["h"], 1), LARGURA_MAX / max(m["w"], 1))
    dx, dy = ALVO[0] - m["cx"], ALVO[1] - m["cy"]
    return f"transform-origin: {m['cx']}px {m['cy']}px; transform: translate({dx:.1f}px, {dy:.1f}px) scale({s:.4f});"


def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); sys.exit(2)
    cmd, pasta = a[0], a[1]
    tempos = [float(x) for x in a[a.index("--tempos") + 1].split(",")] if "--tempos" in a else [0.6, 1.5, 2.5, 3.5, 4.5, 5.5]
    m = medir(pasta, tempos)
    print(f"{Path(pasta).name}: centro ({m['cx']}, {m['cy']}) | {m['w']}x{m['h']} | y {m['y0']}..{m['y1']} | {'OK' if m['ok'] else 'FORA'}")
    if cmd == "corrigir" and not m["ok"]:
        fit = Path(a[a.index("--fit") + 1]) if "--fit" in a else Path(pasta).parent.parent / "fit.json"
        d = json.loads(fit.read_text()) if fit.exists() else {}
        d[Path(pasta).name] = correcao(m); fit.write_text(json.dumps(d, indent=1, ensure_ascii=False))
        print("correção gravada em", fit, "->", d[Path(pasta).name])
    sys.exit(0 if m["ok"] else 1)


if __name__ == "__main__":
    main()
