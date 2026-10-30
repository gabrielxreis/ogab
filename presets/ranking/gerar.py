"""Preset RANKING: quadro de ranking que se monta conforme a fala (tier S-D ou pódio top 3).

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4] [--gif]
  (com "fundo": "transparente", --render saida.mov sai com canal alfa para ir por cima do vídeo)

plano.json: { "w": 1080, "h": 1920, "fps": 60, "dur": 13, "cor": "#C4A34F" (cor da marca),
  "letra": "inter" (Inter Tight, padrão) | "bebas" (Bebas Neue), "fundo": "escuro" (padrão) | "transparente",
  "titulo": "Melhores hábitos|de *manhã*" ("|" quebra linha, "*palavra*" na cor da marca),
  "forma": "tier" | "top3",
  "faixas": ["S", "A", "B", "C", "D"]  (só no tier; também [{"nome": "S", "cor": "#..."}]; sem cor = tons da "cor"),
  "destaque": true (o item cresce no centro antes de voar para a vaga; false = entra direto na vaga),
  "itens": [ {"texto": "Água", "imagem": "agua.png" (opcional), "faixa": "S" (tier) | 1, 2, 3 (top3), "em": 1.2}, ... ] }
"em" = segundo em que o item é dito (transcrição palavra a palavra). Depois de assentar, o item FICA no lugar.
Top3: sem "faixa", a ordem de entrada vira 3º, 2º, 1º. Itens com menos de 1,4 s até o próximo entram direto (sem destaque).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from hf_preset import montar, renderizar, args_render, traz, HYPERFRAMES


def _barra():
    """Render com a barra do progresso.py (LEI do usuário, 30/10/2026: todo render de motion com link para acompanhar)."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
    import progresso
    return progresso

AQUI = os.path.dirname(os.path.abspath(__file__))


def gerar(plano, pasta, base="."):
    plano = json.loads(json.dumps(plano))
    for k, v in (("w", 1080), ("h", 1920), ("fps", 60), ("cor", "#C4A34F"), ("forma", "tier"), ("letra", "inter"), ("fundo", "escuro")):
        plano.setdefault(k, v)
    itens = plano.get("itens") or []
    if not itens or any("em" not in x or not str(x.get("texto", "")).strip() for x in itens):
        raise SystemExit('"itens" precisa de pelo menos 1 item com "texto" e "em" (segundo em que é dito).')
    if plano["forma"] == "tier":
        nomes = [str(f["nome"] if isinstance(f, dict) else f).strip().lower() for f in (plano.get("faixas") or ["S", "A", "B", "C", "D"])]
        fora = [x["texto"] for x in itens if str(x.get("faixa", "")).strip().lower() not in nomes]
        if fora:
            raise SystemExit(f"Itens sem faixa válida ({', '.join(nomes)}): {', '.join(fora)}")
    elif plano["forma"] == "top3":
        if len(itens) > 3:
            raise SystemExit("top3 aceita no máximo 3 itens.")
    else:
        raise SystemExit('"forma" é "tier" ou "top3".')
    plano.setdefault("dur", round(max(float(x["em"]) for x in itens) + 2.5, 2))
    os.makedirs(pasta, exist_ok=True)
    for x in itens:
        if x.get("imagem"):
            x["imagem"] = traz(x["imagem"], base, pasta)
    plano["itens"] = itens
    montar(os.path.join(AQUI, "kit"), plano, pasta, plano["dur"])
    print("  ▸", os.path.basename(os.path.normpath(pasta)) + " ·", plano["forma"], len(itens), "itens", plano["dur"], "s")
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
