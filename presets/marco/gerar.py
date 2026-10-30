"""Preset MARCO: milhares de pontos se juntam e formam o número do marco (acabamento premium do launch).

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4] [--gif]

plano.json: { "w": 1080, "h": 1920, "fps": 60, "dur": 6, "cor": "#C4A34F", "letra": "apple"|"editorial"|"cinema",
  "numero": "10 mil" (o texto EXATO que aparece: "1 milhão", "+10", "98%"), "texto": "alunos|*formados*",
  "olho": "linha pequena em cima", "sub": "...", "fonte": "linha da fonte (quando o número vem de pesquisa)",
  "destaqueNumero": true (número na cor da marca; false = branco), "pontos": 4200, "tam": 420 }
O número vem da lista de fatos aprovados (docs/etapas/revisor.md). Combina com o POINT CLOUD (mesma linguagem de pontos).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from hf_preset import montar, renderizar, args_render

AQUI = os.path.dirname(os.path.abspath(__file__))


def gerar(plano, pasta):
    plano = json.loads(json.dumps(plano))
    for k, v in (("w", 1080), ("h", 1920), ("fps", 60), ("dur", 6), ("cor", "#C4A34F"), ("cor2", "#F2E2B3")):
        plano.setdefault(k, v)
    if not str(plano.get("numero", "")).strip():
        raise SystemExit('Falta "numero" (o texto exato do marco, ex.: "10 mil").')
    montar(os.path.join(AQUI, "kit"), plano, pasta, plano["dur"])
    print("  ▸", os.path.basename(os.path.normpath(pasta)) + " ·", plano["numero"], plano["dur"], "s")
    return pasta


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    pasta = gerar(json.load(open(a[0], encoding="utf-8")), os.path.abspath(a[1]))
    saida, gif = args_render(a)
    if saida:
        renderizar(pasta, saida, gif)
