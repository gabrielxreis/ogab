#!/usr/bin/env python3
"""Entrega de carrossel: páginas (PNG de qualquer tamanho) -> versão do Instagram + folha com todas.

    python3 carrossel_entrega.py <pasta_das_paginas> [--saida <pasta>] [--formato 4x5|1x1|9x16] [--colunas 4] [--abrir]

Lê os PNG/JPG da pasta em ordem de nome (01_capa.png, 02_...), corta no centro para a proporção certa sem distorcer,
grava <saida>/instagram_1080x1350/NN_nome.jpg (qualidade 95) e <saida>/folha_carrossel.jpg (miniaturas numeradas
para mostrar ao usuário ou ao cliente de uma vez). Saída padrão: a própria pasta.
--abrir (Mac): abre o Finder com as páginas finais já selecionadas, prontas para AirDrop ou arrastar.
"""
import argparse, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

FORMATOS = {"4x5": (1080, 1350), "1x1": (1080, 1080), "9x16": (1080, 1920)}


def encaixar(img, w, h):
    """Corta no centro para a proporção w:h e redimensiona (cover)."""
    iw, ih = img.size
    if iw * h > ih * w:
        nw = round(ih * w / h); x = (iw - nw) // 2; img = img.crop((x, 0, x + nw, ih))
    else:
        nh = round(iw * h / w); y = (ih - nh) // 2; img = img.crop((0, y, iw, y + nh))
    return img.resize((w, h), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--saida")
    ap.add_argument("--formato", default="4x5", choices=FORMATOS)
    ap.add_argument("--colunas", type=int, default=4)
    ap.add_argument("--abrir", action="store_true")
    a = ap.parse_args()
    saida = a.saida or a.pasta
    w, h = FORMATOS[a.formato]
    pags = sorted(f for f in os.listdir(a.pasta)
                  if f.lower().endswith((".png", ".jpg", ".jpeg")) and not f.startswith(("folha", ".")))
    if not pags:
        sys.exit("nenhuma página (PNG/JPG) na pasta")
    dest = os.path.join(saida, f"instagram_{w}x{h}")
    os.makedirs(dest, exist_ok=True)
    finais = []
    for f in pags:
        img = encaixar(Image.open(os.path.join(a.pasta, f)).convert("RGB"), w, h)
        nome = os.path.splitext(f)[0] + ".jpg"
        img.save(os.path.join(dest, nome), quality=95)
        finais.append(img)
        print(f"{nome}  {w}x{h}")

    # folha: miniaturas de 360 px de largura com o número da página
    tw = 360; th = round(tw * h / w); m = 24; cols = min(a.colunas, len(finais)); lin = -(-len(finais) // cols)
    folha = Image.new("RGB", (m + cols * (tw + m), m + lin * (th + m)), "#111111")
    d = ImageDraw.Draw(folha)
    try:
        fonte = ImageFont.truetype("arial.ttf" if os.name == "nt" else "/System/Library/Fonts/Helvetica.ttc", 28)
    except OSError:
        fonte = ImageFont.load_default()
    for i, img in enumerate(finais):
        x = m + (i % cols) * (tw + m); y = m + (i // cols) * (th + m)
        folha.paste(img.resize((tw, th), Image.LANCZOS), (x, y))
        d.rectangle((x, y, x + 46, y + 40), fill="#000000")
        d.text((x + 10, y + 5), f"{i + 1:02d}", fill="#FFFFFF", font=fonte)
    caminho = os.path.join(saida, "folha_carrossel.jpg")
    folha.save(caminho, quality=90)
    print(f"folha: {caminho}")

    if a.abrir and sys.platform == "darwin":
        arqs = ", ".join(f'POSIX file "{os.path.abspath(os.path.join(dest, os.path.splitext(f)[0] + ".jpg"))}"'
                         for f in pags)
        subprocess.run(["osascript", "-e", f'tell application "Finder" to reveal {{{arqs}}}',
                        "-e", 'tell application "Finder" to activate'], check=False)


if __name__ == "__main__":
    main()
