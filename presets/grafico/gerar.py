"""Preset GRÁFICO: dado animado com o valor exato e a fonte na tela (acabamento premium do launch).

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4] [--gif]

plano.json: { "w": 1080, "h": 1920, "fps": 60, "dur": 7, "cor": "#C4A34F", "letra": "apple"|"editorial"|"cinema",
  "tipo": "barras" | "linha" | "rosca" | "comparacao",
  "olho": "linha pequena em cima", "titulo": "Alunos|por *ano*", "sub": "...",
  "dados": [ {"rotulo": "2023", "valor": 1200}, ... ], "destaque": índice (padrão: o último),
  "prefixo": "R$ ", "sufixo": "%", "decimais": 0, "zero": false (linha sem começar no zero), "valores": "todos" (linha),
  "fonte": "Fonte: IBGE, 2025" }   <- OBRIGATÓRIA: de onde vem o número (do cliente, do roteiro aprovado ou da pesquisa)
Regras: o valor aparece EXATO como está no plano; nunca inventar dado (docs/etapas/revisor.md, "Fatos aprovados").
Barras e comparação: 2-6 itens. Rosca: 2-5 fatias (o total é a soma). Linha: 3-12 pontos.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from hf_preset import montar, renderizar, args_render

AQUI = os.path.dirname(os.path.abspath(__file__))


def gerar(plano, pasta):
    plano = json.loads(json.dumps(plano))
    for k, v in (("w", 1080), ("h", 1920), ("fps", 60), ("dur", 7), ("tipo", "barras"), ("cor", "#C4A34F"), ("cor2", "#F2E2B3")):
        plano.setdefault(k, v)
    if not str(plano.get("fonte", "")).strip():
        raise SystemExit('Falta "fonte": todo gráfico mostra de onde vem o número (ex.: "Fonte: dados internos da empresa, 2026").')
    d = plano.get("dados") or []
    if len(d) < 2 or any("valor" not in x or "rotulo" not in x for x in d):
        raise SystemExit('"dados" precisa de pelo menos 2 itens com "rotulo" e "valor".')
    montar(os.path.join(AQUI, "kit"), plano, pasta, plano["dur"])
    print("ok", pasta, plano["tipo"], len(d), "itens", plano["dur"], "s")
    return pasta


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    pasta = gerar(json.load(open(a[0], encoding="utf-8")), os.path.abspath(a[1]))
    saida, gif = args_render(a)
    if saida:
        renderizar(pasta, saida, gif)
