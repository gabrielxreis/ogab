"""Preset APPLE DESIGN: folha de desenho técnico (estilo desenho dimensional da Apple) que se desenha sozinha e vira o
produto acabado com o título do lançamento.

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4] [--gif]

plano.json: { "w": 1080, "h": 1920, "fps": 24 (padrão: config.regras.fps), "dur": 13, "cor": "#C4A34F" (metal do produto
  e destaques), "tema": "papel" (branco, padrão) | "noite" (folha escura), "rotulos": "en" (padrão, como as folhas da
  Apple) | "pt",
  "produto": "nome no carimbo", "codigo": "DWG-A01",
  "medidas": { "largura": 71.9, "altura": 150, "espessura": 8.75, "raio": 12 } (mm, SÓ medida publicada ou do cliente),
  "notas": ["até 3 notas da folha"] (opcional),
  "olho": "linha pequena em cima do título", "titulo": "Nome *destaque*|segunda linha", "sub": "frase", "rodape": "data ou CTA",
  "tamTitulo": 112 }
Batidas fixas (s): 0-2,3 close no módulo de câmera · 2,3-4,4 vista de trás · 4,6-7,6 vista explodida · 7,6-9,6 folha
inteira · 9,8-fim o desenho vira produto e o título sobe. dur mínimo 12.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from hf_preset import montar, renderizar, args_render

AQUI = os.path.dirname(os.path.abspath(__file__))


def fps_padrao():
    try:
        return json.load(open(os.path.join(AQUI, "..", "..", "config.json"), encoding="utf-8"))["regras"]["fps"]
    except Exception:
        return 24


def gerar(plano, pasta):
    plano = json.loads(json.dumps(plano))
    for k, v in (("w", 1080), ("h", 1920), ("fps", fps_padrao()), ("dur", 13), ("cor", "#C4A34F"), ("tema", "papel"), ("rotulos", "en")):
        plano.setdefault(k, v)
    plano["dur"] = max(12, plano["dur"])
    if not str(plano.get("titulo", "")).strip():
        raise SystemExit('Falta "titulo" (o nome do produto no fecho, ex.: "iPhone *18 Pro*").')
    montar(os.path.join(AQUI, "kit"), plano, pasta, plano["dur"])
    print("  ▸", os.path.basename(os.path.normpath(pasta)) + " ·", plano["titulo"], plano["dur"], "s")
    return pasta


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    pasta = gerar(json.load(open(a[0], encoding="utf-8")), os.path.abspath(a[1]))
    saida, gif = args_render(a)
    if saida:
        renderizar(pasta, saida, gif)
