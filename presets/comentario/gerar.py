"""Preset COMENTÁRIO: card de comentário de seguidor entrando na tela (formato "respondendo comentário").

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4] [--gif]

plano.json: { "w": 1080, "h": 1920, "fps": 60, "dur": 8 (padrão: último "em" + 2,8 s), "cor": "#FF8B3D",
  "estilo": "claro" (card branco genérico) | "vidro" (glass escuro), "posicao": "topo" | "centro",
  "fundo": "escuro" (padrão) | "transparente" (vai por cima do vídeo da pessoa; renderizar em .mov para ter alfa),
  "responder": "Responder" (texto do rodapé),
  "comentarios": [ { "usuario": "ana.lima", "texto": "Como você organiza a semana?", "curtidas": 248 (número conta;
     texto como "1,2 mil" fica fixo), "tempo": "há 2 h", "avatar": "foto.png" (opcional; sem ela, círculo na cor
     com a inicial), "destaque": "organiza" (opcional: palavra que ganha marca-texto; também vale *palavra* no texto),
     "em": 0.3 (segundo em que o card entra; padrão a cada 2,6 s) } ] }
Caminhos de avatar absolutos ou relativos à pasta do plano.json. Comentário de verdade só com autorização; no exemplo, fictício.
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
    for k, v in (("w", 1080), ("h", 1920), ("fps", 60), ("cor", "#FF8B3D"), ("estilo", "claro"), ("posicao", "topo"), ("fundo", "escuro")):
        plano.setdefault(k, v)
    cs = plano.get("comentarios") or []
    if not cs:
        raise SystemExit('Falta "comentarios" (lista com usuario e texto).')
    for i, c in enumerate(cs):
        c.setdefault("em", round(.3 + i * 2.6, 3))
        if c.get("avatar"):
            c["avatar"] = traz(c["avatar"], base, pasta)
    plano.setdefault("dur", round(max(c["em"] for c in cs) + 2.8, 2))
    montar(os.path.join(AQUI, "kit"), plano, pasta, plano["dur"])
    print("  ▸", os.path.basename(os.path.normpath(pasta)) + " ·", len(cs), "comentário(s)", plano["dur"], "s")
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
