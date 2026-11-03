"""Perspectiva exata por 4 cantos (mockup: arte numa tela, outdoor, papel, parede).

    .venv/bin/python perspectiva.py arte.png saida.png --doc 1080 1350 --cantos x0 y0 x1 y1 x2 y2 x3 y3 [--raio 34]

- Cantos em pixels do documento: sup-esq, sup-dir, inf-dir, inf-esq. Saída = PNG transparente do tamanho do
  documento com a arte já na posição; no arte.jsx: Y.colocar(saida, "ARTE NA TELA", g, {x:0,y:0,w:W,h:H}, "conter").
- `--raio`: cantos arredondados (tela de celular), aplicados ANTES da perspectiva (acompanham a distorção).
- Por que em Python: o warp customizado do Photoshop (transform + warpCustom + meshPoints) grava os cantos certos
  mas o resultado na tela depende de onde a camada nasceu (testado 16/10/2026, docs/tecnicas.md). A homografia
  aqui é exata. Para continuar editável, guarde a arte original como objeto inteligente oculto no PSD.
"""
import argparse

import numpy as np
from PIL import Image, ImageDraw


def coefs(destino, origem):
    """Coeficientes do PIL (mapeia saída -> entrada) para a homografia origem -> destino."""
    A, B = [], []
    for (x, y), (u, v) in zip(destino, origem):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("arte"); ap.add_argument("saida")
    ap.add_argument("--doc", type=int, nargs=2, required=True); ap.add_argument("--cantos", type=float, nargs=8, required=True)
    ap.add_argument("--raio", type=float, default=0); ap.add_argument("--super", type=int, default=2)
    a = ap.parse_args()
    im = Image.open(a.arte).convert("RGBA"); w, h = im.size
    if a.raio:
        # raio em px do documento -> px da arte, pela largura média do destino
        c = np.array(a.cantos).reshape(4, 2); larg = (np.linalg.norm(c[1] - c[0]) + np.linalg.norm(c[2] - c[3])) / 2
        r = a.raio * w / larg; m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
        im.putalpha(Image.fromarray(np.minimum(np.asarray(im.getchannel("A")), np.asarray(m))))
    S = a.super; W, H = a.doc[0] * S, a.doc[1] * S
    dst = [(a.cantos[i] * S, a.cantos[i + 1] * S) for i in range(0, 8, 2)]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    out = im.transform((W, H), Image.PERSPECTIVE, coefs(dst, src), Image.BICUBIC)
    out.resize(tuple(a.doc), Image.LANCZOS).save(a.saida); print(a.saida)


if __name__ == "__main__":
    main()
