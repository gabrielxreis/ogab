"""Apara PNG com borda quase transparente (sombra/ruído de exportação) antes de colocar no Photoshop.

    .venv/bin/python aparar.py logo.png [--alfa 24]   ->  logo.aparado.png

O Photoshop mede a camada por QUALQUER pixel com alfa > 0: um logo exportado com halo de 1-5% de opacidade
ocupa a imagem inteira e o Y.colocar encaixa a caixa errada (logo sai menor e deslocado). Aqui os pixels com
alfa <= --alfa viram transparentes e a imagem é recortada na caixa real.
"""
import argparse
import os

from PIL import Image


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("png"); ap.add_argument("--alfa", type=int, default=24)
    a = ap.parse_args()
    im = Image.open(a.png).convert("RGBA"); al = im.getchannel("A").point(lambda v: 0 if v <= a.alfa else v)
    im.putalpha(al); caixa = al.getbbox()
    saida = os.path.splitext(a.png)[0] + ".aparado.png"
    im.crop(caixa).save(saida); print(saida, caixa)


if __name__ == "__main__":
    main()
