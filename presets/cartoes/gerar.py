"""Preset CARTÕES: cartões de prova empilhando em profundidade (número, depoimento, print/foto), com final em leque ou grade.

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4] [--gif]

plano.json: { "w": 1080, "h": 1920, "fps": 60, "dur": 14 (padrão: final + 3,4 s; sem final, último "em" + 2,8 s), "cor": "#FF8B3D",
  "fundo": "escuro" (padrão) | "transparente" (vai por cima do vídeo da pessoa; renderizar em .mov para ter alfa),
  "cartoes": [ { "tipo": "numero" | "texto" | "imagem",
     numero: "titulo" (linha pequena em cima), "numero": "+3.200" (texto EXATO; conta no mesmo formato), "texto" (embaixo)
     texto (depoimento): "texto" (a fala), "titulo" (quem disse)
     imagem (print, foto): "imagem": "print.png", "titulo", "texto" (legenda)
     "em": 0.3 (segundo em que o cartão entra; padrão a cada 2,1 s) } ],
  "final": "leque" | "grade" | "nenhum" (padrão), "emFinal": segundo do final (padrão: último "em" + 2,3 s),
  "frase": "linha que sobe no final" (opcional; "|" quebra a linha) }
Até 4 cartões visíveis na pilha; os mais antigos saem pelo fundo e voltam no final. Números e depoimentos SÓ da lista de
fatos aprovados (docs/etapas/revisor.md). Imagens com caminho absoluto ou relativo à pasta do plano.json.
"""
import json, os, subprocess, sys
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
    for k, v in (("w", 1080), ("h", 1920), ("fps", 60), ("cor", "#FF8B3D"), ("fundo", "escuro"), ("final", "nenhum")):
        plano.setdefault(k, v)
    cs = plano.get("cartoes") or []
    if not cs:
        raise SystemExit('Falta "cartoes" (lista com tipo e conteúdo).')
    for i, c in enumerate(cs):
        c.setdefault("em", round(.3 + i * 2.1, 3))
        if c.get("imagem"):
            c["imagem"] = traz(c["imagem"], base, pasta)
    ultimo = max(c["em"] for c in cs)
    if plano["final"] != "nenhum" and len(cs) > 1:
        plano.setdefault("emFinal", round(ultimo + 2.3, 2))
        plano.setdefault("dur", round(plano["emFinal"] + 3.4, 2))
    plano.setdefault("dur", round(ultimo + 2.8, 2))
    montar(os.path.join(AQUI, "kit"), plano, pasta, plano["dur"])
    print("  ▸", os.path.basename(os.path.normpath(pasta)) + " ·", len(cs), "cartão(ões)", plano["final"], plano["dur"], "s")
    return pasta


def render(pasta, saida, gif):
    """MP4 pelo hf_preset; com saída .mov renderiza com alfa (fundo transparente)."""
    if saida.lower().endswith(".mov"):
        _barra().hf(["npx", "--yes", HYPERFRAMES, "render", pasta, "--format", "mov", "-q", "high", "-o", saida], os.path.basename(os.path.dirname(os.path.abspath(__file__))))
        print("    →", os.path.basename(saida))
    else:
        renderizar(pasta, saida, gif)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    arq = os.path.abspath(a[0])
    pasta = gerar(json.load(open(arq, encoding="utf-8")), os.path.abspath(a[1]), os.path.dirname(arq))
    saida, gif = args_render(a)
    if saida:
        render(pasta, saida, gif)
