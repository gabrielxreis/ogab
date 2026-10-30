"""Preset RESPOSTAS: faixa no topo com N espaços "?" que viram ícone + palavra quando a resposta é dita.

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4] [--gif]
  (com "fundo": "transparente", --render saida.mov sai com canal alfa para ir por cima do vídeo da pessoa)

plano.json: { "w": 1080, "h": 1920, "fps": 60, "dur": 8, "cor": "#C4A34F" (cor da marca),
  "letra": "inter" (Inter Tight, padrão) | "bebas" (Bebas Neue), "fundo": "escuro" (padrão) | "transparente",
  "pergunta": "3 regras para juntar o *primeiro milhão*" (opcional; "*palavra*" na cor da marca),
  "itens": [ {"icone": "💰" (emoji) ou "icones/cofre.png" (imagem/SVG), "rotulo": "Gastar menos", "em": 1.2}, ... ] }
2 a 5 itens. "em" = segundo em que a resposta é dita (transcrição palavra a palavra). Rótulo curto: 1-3 palavras.
A faixa fica no topo (y ~140-420) e deixa o resto do quadro livre para a pessoa e a legenda.
"""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from hf_preset import montar, renderizar, args_render, traz, HYPERFRAMES


def _barra():
    """Render com a barra do progresso.py (LEI do usuário, 30/10/2026: todo render de motion com link para acompanhar)."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
    import progresso
    return progresso

AQUI = os.path.dirname(os.path.abspath(__file__))
IMG = re.compile(r"\.(png|jpe?g|webp|svg|gif)$", re.I)


def gerar(plano, pasta, base="."):
    plano = json.loads(json.dumps(plano))
    for k, v in (("w", 1080), ("h", 1920), ("fps", 60), ("cor", "#C4A34F"), ("letra", "inter"), ("fundo", "escuro")):
        plano.setdefault(k, v)
    itens = plano.get("itens") or []
    if not 2 <= len(itens) <= 5 or any("em" not in x or not str(x.get("rotulo", "")).strip() for x in itens):
        raise SystemExit('"itens" precisa de 2 a 5 respostas, cada uma com "rotulo" e "em" (segundo em que é dita).')
    plano.setdefault("dur", round(max(float(x["em"]) for x in itens) + 2.5, 2))
    os.makedirs(pasta, exist_ok=True)
    for x in itens:
        if x.get("icone") and IMG.search(str(x["icone"])):
            x["icone"] = traz(x["icone"], base, pasta)
    plano["itens"] = itens
    montar(os.path.join(AQUI, "kit"), plano, pasta, plano["dur"])
    print("  ▸", os.path.basename(os.path.normpath(pasta)) + " ·", len(itens), "respostas", plano["dur"], "s")
    return pasta


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    pasta = gerar(json.load(open(a[0], encoding="utf-8")), os.path.abspath(a[1]), os.path.dirname(os.path.abspath(a[0])))
    saida, gif = args_render(a)
    if saida and saida.endswith(".mov"):   # fundo transparente: ProRes 4444 com alfa
        import subprocess
        _barra().hf(["npx", "--yes", HYPERFRAMES, "render", pasta, "--format", "mov", "-o", saida], os.path.basename(os.path.dirname(os.path.abspath(__file__))))
    elif saida:
        renderizar(pasta, saida, gif)
