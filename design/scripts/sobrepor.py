"""Sobrepõe a referência e o remake para conferir alinhamento (as duas na mesma largura).

    .venv/bin/python sobrepor.py ref.png remake.png saida.png [--cor "#FFFFFF" --tol 50] [--regiao x1 y1 x2 y2]

Gera uma folha com 3 painéis: (1) 50/50, (2) bordas: referência em VERMELHO, remake em CIANO (onde bate fica branco),
(3) diferença. Com --cor, calcula a nota de alinhamento do texto daquela cor (IoU dos pixels, 1.0 = idêntico)
e o deslocamento médio (dx, dy) que falta corrigir. Regiões em pixels do remake (1080 de largura).
"""
import argparse
import numpy as np
from PIL import Image, ImageChops, ImageFilter, ImageOps


def mascara(im, cor, tol):
    alvo = np.array([int(cor[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32)
    return np.sqrt(((np.asarray(im, dtype=np.float32) - alvo) ** 2).sum(axis=2)) < tol


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("ref"); ap.add_argument("remake"); ap.add_argument("saida")
    ap.add_argument("--cor"); ap.add_argument("--tol", type=int, default=50); ap.add_argument("--regiao", type=int, nargs=4)
    a = ap.parse_args()
    b = Image.open(a.remake).convert("RGB"); W, H = b.size
    r0 = Image.open(a.ref).convert("RGB"); wr = r0.width; r = r0.resize((W, round(r0.height * W / r0.width)))
    r = r.crop((0, 0, W, H)) if r.height >= H else ImageOps.pad(r, (W, H), centering=(0, 0))
    mix = Image.blend(r, b, 0.5)
    er = ImageOps.grayscale(r).filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 40 else 0)
    eb = ImageOps.grayscale(b).filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 40 else 0)
    bordas = Image.merge("RGB", (er, eb, eb))
    dif = ImageChops.difference(r, b)
    folha = Image.new("RGB", (W * 3 + 40, H), "white")
    for i, im in enumerate((mix, bordas, dif)): folha.paste(im, (i * (W + 20), 0))
    folha.thumbnail((2400, 2400)); folha.save(a.saida)
    # nota geral de alinhamento: bordas da referência que têm borda do remake a até 2 px (e vice-versa)
    from PIL import ImageFilter as F
    def mbord(im):
        e = np.asarray(ImageOps.grayscale(im).filter(F.FIND_EDGES)) > 24
        if a.regiao:
            x1, y1, x2, y2 = a.regiao; z = np.zeros_like(e); z[y1:y2, x1:x2] = e[y1:y2, x1:x2]; e = z
        return e
    # comparação justa: o remake passa pela MESMA resolução da referência (captura de 536-980 px ampliada fica
    # borrada e quase sem borda; sem isso a nota despenca mesmo com o texto no lugar certo) + desfoque leve
    bj = b.resize((wr, round(H * wr / W)), Image.LANCZOS).resize((W, H), Image.LANCZOS) if wr < W else b
    suave = lambda im: im.filter(F.GaussianBlur(1.2))
    er_, eb_ = mbord(suave(r)), mbord(suave(bj))
    dil = lambda m: np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(F.MaxFilter(5))) > 0
    prec = (eb_ & dil(er_)).sum() / max(1, eb_.sum()); rec = (er_ & dil(eb_)).sum() / max(1, er_.sum())
    print(f"nota bordas (2 px): {2 * prec * rec / max(1e-6, prec + rec):.3f}  (remake->ref {prec:.2f}, ref->remake {rec:.2f})")
    if a.cor:
        mr, mb = mascara(r, a.cor, a.tol), mascara(b, a.cor, a.tol)
        if a.regiao:
            x1, y1, x2, y2 = a.regiao; z = np.zeros_like(mr); mr = (z.copy() + 0).astype(bool) | False
            mr2 = np.zeros_like(mb); mr2[y1:y2, x1:x2] = mascara(r, a.cor, a.tol)[y1:y2, x1:x2]; mr = mr2
            mb2 = np.zeros_like(mb); mb2[y1:y2, x1:x2] = mb[y1:y2, x1:x2]; mb = mb2
        iou = (mr & mb).sum() / max(1, (mr | mb).sum())
        def centro(m):
            ys, xs = np.where(m); return (xs.mean(), ys.mean()) if len(xs) else (0, 0)
        cr, cb = centro(mr), centro(mb)
        print(f"nota texto {a.cor}: {iou:.3f}   falta mover dx={cr[0]-cb[0]:+.1f} dy={cr[1]-cb[1]:+.1f}")
    print(a.saida)


if __name__ == "__main__":
    main()
