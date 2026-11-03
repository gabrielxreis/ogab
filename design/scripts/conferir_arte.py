"""Conferência automática de uma arte (o checklist do docs/composicao_e_tipografia.md que dá para medir).

    .venv/bin/python conferir_arte.py arte.psd [arte.png] [--formato feed|story|quadrado]

Lê as camadas de texto do PSD (psd-tools: caixa, tamanho, cor) e o PNG exportado e aponta:
- CONTRASTE: razão WCAG entre a cor do texto e o fundo real atrás dele (mediana dos pixels da caixa que não são
  da cor do texto). < 3 em título ou < 4,5 em texto pequeno = problema.
- ZONA SEGURA: texto nos 250 px de cima / 340 px de baixo do story; no feed 4:5, fora do miolo 3:4 da grade.
- TAMANHO: texto < 30 px no feed (apoio), < 18 px (rótulo/@).
- MARGENS: texto a menos de 48 px da borda lateral; margens esquerda/direita dos blocos centralizados desiguais.
Saída: lista de avisos + nota (0-10). Não substitui olhar a prévia, mas pega erro bobo antes de entregar.
"""
import argparse
import os

import numpy as np
from PIL import Image
from psd_tools import PSDImage


def lum(c):
    c = np.array(c, float) / 255; c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contraste(a, b):
    la, lb = lum(a), lum(b); return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def textos(psd):
    for l in psd.descendants():
        if l.kind == "type" and l.is_visible():
            try:
                ed = l.engine_dict; rs = ed["StyleRun"]["RunArray"][0]["StyleSheet"]["StyleSheetData"]
                tam = float(rs.get("FontSize", 0)) * (l.transform[3] if hasattr(l, "transform") else 1)
                fc = rs.get("FillColor", {}).get("Values", [1, 0, 0, 0]); cor = [round(v * 255) for v in fc[1:4]]
            except Exception:
                tam, cor = 0, [255, 255, 255]
            try:
                just = ed["ParagraphRun"]["RunArray"][0]["ParagraphSheet"]["Properties"].get("Justification", 0)   # 2 = centro
            except Exception:
                just = 0
            yield l.name, l.bbox, tam, cor, l.text.replace("\r", " ")[:40], just


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("psd"); ap.add_argument("png", nargs="?"); ap.add_argument("--formato")
    a = ap.parse_args()
    psd = PSDImage.open(a.psd); W, H = psd.width, psd.height
    png = a.png or os.path.splitext(a.psd)[0] + ".png"
    im = np.asarray(Image.open(png).convert("RGB")).astype(int)
    fmt = a.formato or ("story" if H / W > 1.6 else ("feed" if H / W > 1.1 else "quadrado"))
    av, pontos = [], 10.0
    for nome, (x1, y1, x2, y2), tam, cor, txt, just in textos(psd):
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(W, x2), min(H, y2)
        if x2 <= x1 or y2 <= y1:
            continue
        caixa = im[y1:y2, x1:x2].reshape(-1, 3); dist = np.sqrt(((caixa - np.array(cor)) ** 2).sum(1))
        fundo = caixa[dist > 90]
        if len(fundo) > 30:
            fc = np.median(fundo, 0); cr = contraste(cor, fc); lim = 3.0 if tam >= 40 else 4.5
            if cr < lim:
                av.append(f"CONTRASTE {cr:.1f}:1 (mín {lim}) em '{txt}' [{nome}]: escurecer/clarear o fundo (degradê/scrim) ou trocar a cor"); pontos -= 1.5
        if fmt == "story" and (y1 < 250 or y2 > H - 340) and not any(k in nome.upper() for k in ("ARRASTE", "@")):
            av.append(f"ZONA SEGURA story: '{txt}' em y {y1}-{y2} (livre: 250 em cima, 340 embaixo)"); pontos -= 1
        if fmt == "feed" and (y1 < (H - W * 4 / 3) / 2 or y2 > H - (H - W * 4 / 3) / 2) and tam >= 60:
            av.append(f"GRADE 3:4: título '{txt}' sai do miolo que aparece no perfil (y {y1}-{y2})"); pontos -= 0.5
        if 0 < tam < 18:
            av.append(f"TAMANHO {tam:.0f}px em '{txt}': ilegível no celular (mín 18 rótulo, 30 apoio)"); pontos -= 1
        elif 0 < tam < 30 and len(txt) > 25:
            av.append(f"TAMANHO {tam:.0f}px em texto corrido '{txt}': apoio pede >= 30 px no feed"); pontos -= 0.5
        if x1 < 48 or x2 > W - 48:
            av.append(f"MARGEM: '{txt}' a {min(x1, W - x2)} px da borda (mín 48, ideal 60-80)"); pontos -= 0.5
        cx = (x1 + x2) / 2
        if just == 2 and abs((W - x2) - x1) > 12 and (x2 - x1) < W * 0.9:
            av.append(f"CENTRO: '{txt}' desviado {abs((W - x2) - x1) / 2:.0f} px do eixo"); pontos -= 0.3
    print(f"{os.path.basename(a.psd)} ({fmt} {W}x{H})  nota {max(0, pontos):.1f}/10")
    for x in av:
        print(" -", x)
    if not av:
        print(" - nada a apontar no que dá para medir; conferir a prévia no olho")


if __name__ == "__main__":
    main()
