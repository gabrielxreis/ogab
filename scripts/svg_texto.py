"""Texto -> contorno vetorial (atributo "d" de um <path> SVG), para morphing de formas complexas (logo, letras).

  python3 svg_texto.py "CALVERSTONE" fonte.ttf --tamanho 110 --espaco 0.25 --centro 540,960
  -> imprime o "d" (centrado em --centro, em px)

Usa fontTools (vem com o Python da skill). --espaco = letter-spacing em ems (0.25 = .25em).
Em Python: from svg_texto import caminho; d, largura, altura = caminho("C", fonte, 600, centro=(540, 960))
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen


def caminho(texto, fonte, tamanho=100, espaco=0.0, centro=(540, 960)):
    f = TTFont(fonte)
    gs, cmap, upm = f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm
    esc = tamanho / upm
    # 1ª passada: medir (caixa de desenho) com a origem em 0
    x, partes = 0.0, []
    for ch in texto:
        nome = cmap.get(ord(ch))
        if not nome:
            x += tamanho * 0.3
            continue
        partes.append((nome, x))
        x += gs[nome].width * esc + espaco * tamanho
    bp = BoundsPen(gs)
    for nome, x0 in partes:
        gs[nome].draw(TransformPen(bp, (esc, 0, 0, -esc, x0, 0)))
    xmin, ymin, xmax, ymax = bp.bounds or (0, 0, 0, 0)
    dx, dy = centro[0] - (xmin + xmax) / 2, centro[1] - (ymin + ymax) / 2
    sp = SVGPathPen(gs)
    for nome, x0 in partes:
        gs[nome].draw(TransformPen(sp, (esc, 0, 0, -esc, x0 + dx, dy)))
    return sp.getCommands(), round(xmax - xmin, 1), round(ymax - ymin, 1)


def letras(texto, fonte, tamanho=100, espaco=0.0, centro=(540, 960)):
    """Como caminho(), mas uma forma POR LETRA (na posição exata da palavra inteira): para morphar uma forma numa
    letra só e animar as outras em cascata. Devolve [(letra, d), ...] (espaços pulados)."""
    f = TTFont(fonte)
    gs, cmap, upm = f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm
    esc = tamanho / upm
    x, partes = 0.0, []
    for ch in texto:
        nome = cmap.get(ord(ch))
        if not nome:
            x += tamanho * 0.3
            continue
        partes.append((ch, nome, x))
        x += gs[nome].width * esc + espaco * tamanho
    bp = BoundsPen(gs)
    for _, nome, x0 in partes:
        gs[nome].draw(TransformPen(bp, (esc, 0, 0, -esc, x0, 0)))
    xmin, ymin, xmax, ymax = bp.bounds or (0, 0, 0, 0)
    dx, dy = centro[0] - (xmin + xmax) / 2, centro[1] - (ymin + ymax) / 2
    saida = []
    for ch, nome, x0 in partes:
        sp = SVGPathPen(gs)
        gs[nome].draw(TransformPen(sp, (esc, 0, 0, -esc, x0 + dx, dy)))
        if ch.strip():
            saida.append((ch, sp.getCommands()))
    return saida


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    tam = float(a[a.index("--tamanho") + 1]) if "--tamanho" in a else 100
    esp = float(a[a.index("--espaco") + 1]) if "--espaco" in a else 0.0
    cen = tuple(float(v) for v in a[a.index("--centro") + 1].split(",")) if "--centro" in a else (540, 960)
    print(caminho(a[0], a[1], tam, esp, cen)[0])
