"""Casa a cor de um objeto/pessoa do remake com o da referência: devolve curvas por canal (R, G, B) para
`Y.curvas(pontos, "CASA COR", grupo)` recortada na foto (camada de ajuste, continua editável).

    .venv/bin/python casar_cor.py ref.png remake.png --mref ref.mascara.png --mrem remake.mascara.png [--forca 1]

- Máscaras: as do `medir_objeto.py --ps "the hand"` (rodar nas duas imagens). Sem máscara usa a imagem toda.
- Casamento de histograma em 7 quantis por canal (2, 10, 25, 50, 75, 90, 98%): pega contraste e tom, não só a
  média. `--forca 0.6` aproxima só 60% do caminho (quando a foto é outra e casar 100% fica artificial).
- Saída: JSON {"r": [[x,y],...], "g": ..., "b": ...} pronto para colar no arte.jsx.
- `--modo luz` (RECOMENDADO quando a diferença é grande, ex.: mão clara -> mão em contraluz): curva SUAVE só
  no composto (luminância em 3 quantis) + `tom` (cor mediana da referência) para um sólido em modo Cor
  recortado. Curvas por canal muito íngremes posterizam (manchas ciano/vermelhas na pele).
"""
import argparse
import json

import numpy as np
from PIL import Image

Q = (2, 10, 25, 50, 75, 90, 98)


def pixels(img, masc, menos=None):
    im = Image.open(img).convert("RGB"); a = np.asarray(im).reshape(-1, 3)
    if masc:
        m = np.asarray(Image.open(masc).convert("L").resize(im.size)).reshape(-1) > 128
        if menos:   # tira outro objeto da máscara (mão MENOS celular)
            m &= ~(np.asarray(Image.open(menos).convert("L").resize(im.size)).reshape(-1) > 128)
        a = a[m]
    return a.astype(np.float32)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("ref"); ap.add_argument("remake")
    ap.add_argument("--mref"); ap.add_argument("--mrem"); ap.add_argument("--menos-ref"); ap.add_argument("--menos-rem"); ap.add_argument("--forca", type=float, default=1.0)
    ap.add_argument("--modo", default="canais", choices=["canais", "luz"])
    a = ap.parse_args()
    pr, pm = pixels(a.ref, a.mref, a.menos_ref), pixels(a.remake, a.mrem, a.menos_rem)
    if a.modo == "luz":
        luma = lambda p: p @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        lr, lm = luma(pr), luma(pm); xs = np.percentile(lm, (10, 50, 90)); ys = np.percentile(lr, (10, 50, 90))
        ys = xs + (ys - xs) * a.forca; pts = [[0, 0]]
        for x, y in zip(xs, ys):
            x = float(np.clip(x, 4, 251))
            if x > pts[-1][0] + 8: pts.append([round(x), round(float(np.clip(max(y, pts[-1][1]), 0, 255)))])
        pts.append([255, round(min(255, pts[-1][1] + (255 - pts[-1][0]) * 0.8))])
        med = np.median(pr, axis=0); sat = float((pr.max(axis=1) - pr.min(axis=1)).mean() / max(1, pr.max(axis=1).mean()))
        print(f"luz: mediana remake {np.median(lm):.0f} -> ref {np.median(lr):.0f}; saturação ref {sat:.2f}")
        print(json.dumps({"rgb": pts, "tom": "#%02X%02X%02X" % tuple(int(v) for v in med), "op_tom": round(min(80, 30 + sat * 100))}))
        return
    saida = {}
    for i, c in enumerate("rgb"):
        xs = np.percentile(pm[:, i], Q); ys = np.percentile(pr[:, i], Q)
        ys = xs + (ys - xs) * a.forca
        pts = [[0, 0]]
        for x, y in zip(xs, ys):
            x, y = float(np.clip(x, 1, 254)), float(np.clip(y, 0, 255))
            if x > pts[-1][0] + 3 and y >= pts[-1][1]:
                pts.append([round(x), round(y)])
        # extremos: segue a inclinação do último trecho
        if pts[-1][0] < 255:
            pts.append([255, round(min(255, pts[-1][1] + (255 - pts[-1][0]) * max(0.2, (pts[-1][1] - pts[-2][1]) / max(1, pts[-1][0] - pts[-2][0]))))])
        saida[c] = pts
        print(f"{c}: média remake {pm[:, i].mean():.0f} -> ref {pr[:, i].mean():.0f}", flush=True)
    print(json.dumps(saida))


if __name__ == "__main__":
    main()
