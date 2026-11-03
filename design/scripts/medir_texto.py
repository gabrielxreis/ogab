"""Mede onde está cada linha de texto numa referência (para o remake bater pixel a pixel).

    .venv/bin/python medir_texto.py ref.png --cor "#FFF9ED" [--tol 60] [--largura 1080] [--regiao x1 y1 x2 y2] [--min-alt 8]

- Pega os pixels da cor do texto (tolerância em distância RGB), agrupa em LINHAS pela projeção horizontal e devolve
  a caixa justa de cada linha (x, y, w, h) já convertida para a largura do documento final (padrão 1080).
- `--regiao` limita a busca (em pixels da referência ORIGINAL), útil para separar título de apoio.
- Saída: JSON (uma lista) + prévia `*.medidas.png` com as caixas desenhadas para conferir.
- `cy`/`ch` = topo e altura do CORPO (altura das maiúsculas): use em texto caixa alta, o motor encaixa pela letra H
  e ignora acento/cedilha (que mudam a caixa total e faziam o tamanho sair errado).
- `xy`/`xh` = faixa da altura-x (minúsculas). Linha com minúscula: passar no alvo e o motor encaixa pelo "x".
Use as caixas no arte.jsx com `alvo: {x, y, w, h}` em Y.texto: o motor ajusta tamanho e posição até bater.
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("img"); ap.add_argument("--cor", required=True); ap.add_argument("--tol", default="auto",
                    help="distância RGB máxima; 'auto' (padrão com --regiao) = metade da distância texto x fundo = borda a 50%% de cobertura")
    ap.add_argument("--largura", type=int, default=1080); ap.add_argument("--regiao", type=int, nargs=4)
    ap.add_argument("--min-alt", type=int, default=6); ap.add_argument("--juntar", type=int, default=3,
                    help="linhas separadas por até N px vazios viram uma só")
    ap.add_argument("--corpo", type=float, default=0.25, help="densidade mínima (fração da linha mais cheia) para o corpo")
    a = ap.parse_args()
    im = Image.open(a.img).convert("RGB"); W0, H0 = im.size
    px = np.asarray(im, dtype=np.float32)
    cores = [np.array([int(c.strip()[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32) for c in a.cor.split(",")]
    if a.tol == "auto":
        if a.regiao:   # fundo = mediana da moldura da região (o texto não encosta na borda da região)
            x1, y1, x2, y2 = a.regiao; sub = px[y1:y2, x1:x2]
            fundo = np.median(np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]]), axis=0)
            tol = max(25.0, min(np.sqrt(((c - fundo) ** 2).sum()) for c in cores) * 0.5)
        else:
            tol = 60.0
    else:
        tol = float(a.tol)
    m = np.zeros(px.shape[:2], dtype=bool)
    for c in a.cor.split(","):  # várias cores: "#FFFFFF,#3ED6A6" (linha com palavra destacada)
        c = c.strip(); alvo = np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32)
        m |= np.sqrt(((px - alvo) ** 2).sum(axis=2)) < tol
    if a.regiao:
        x1, y1, x2, y2 = a.regiao; z = np.zeros_like(m); z[y1:y2, x1:x2] = m[y1:y2, x1:x2]; m = z
    linhas_on = m.sum(axis=1) > max(2, m.shape[1] * 0.004)
    # agrupa faixas verticais contínuas
    faixas, ini, vazio = [], None, 0
    for y, on in enumerate(linhas_on):
        if on:
            if ini is None: ini = y
            vazio = 0
        elif ini is not None:
            vazio += 1
            if vazio > a.juntar:
                faixas.append((ini, y - vazio + 1)); ini = None; vazio = 0
    if ini is not None: faixas.append((ini, len(linhas_on)))
    k = a.largura / W0; res = []
    prev = im.copy(); d = ImageDraw.Draw(prev)
    for (ya, yb) in faixas:
        if yb - ya < a.min_alt: continue
        cols = np.where(m[ya:yb].sum(axis=0) > 0)[0]
        if len(cols) == 0: continue
        xa, xb = cols.min(), cols.max() + 1
        # corpo = faixa densa da linha (altura de maiúscula em texto CAIXA ALTA): ignora acento, cedilha, vírgula, cauda do Q
        cont = m[ya:yb].sum(axis=1); den = np.where(cont >= cont.max() * a.corpo)[0]
        cy, cb = ya + den.min(), ya + den.max() + 1
        # faixa do x (minúsculas): linhas bem cheias (>= 45%); ascendentes, acentos e descendentes ficam de fora
        dx_ = np.where(cont >= cont.max() * 0.45)[0]; xy_, xb_ = ya + dx_.min(), ya + dx_.max() + 1
        # cor real do texto: mediana dos pixels do miolo das letras (sem a borda antisserrilhada)
        sel = px[ya:yb, xa:xb][m[ya:yb, xa:xb]]
        lum = sel.sum(axis=1); miolo = sel[lum >= np.percentile(lum, 50)] if len(sel) > 20 else sel
        cor = "#%02X%02X%02X" % tuple(int(v) for v in np.median(miolo, axis=0)) if len(miolo) else ""
        res.append({"x": round(xa * k), "y": round(ya * k), "w": round((xb - xa) * k), "h": round((yb - ya) * k),
                    "cy": round(cy * k), "ch": round((cb - cy) * k),
                    "xy": round(xy_ * k), "xh": round((xb_ - xy_) * k), "cor": cor})
        d.rectangle([xa, ya, xb, yb], outline=(255, 0, 0), width=2)
    saida = os.path.splitext(a.img)[0] + ".medidas.png"; prev.save(saida)
    print(json.dumps(res)); print(saida, f"(tol {tol:.0f})")


if __name__ == "__main__":
    main()
