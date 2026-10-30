"""Preset KINETIC (tipografia cinética, estilo "Katana"): cada batida da fala vira uma CENA de 0,4-2 s com palavras
enormes, hierarquia de tamanhos, caixas e formas vermelhas, interface (prompt, render, rec, visor) e transições rápidas
(chicote, glitch, risco de luz, zoom, vertical, flash). Fundo preto vivo (brilho vermelho, bokeh, grade de pontos),
vermelho chapado, branco com grade ou grafite. A câmera nunca para.

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4]

plano.json: { "w": 1080, "h": 1920, "fps": 30, "cor": "#E8202A", "centro_y": 960, "cenas": [ ... ] }
Campos comuns da cena: tipo, dur (s = tempo da fala), tema preto|vermelho|branco|carvao, transicao corte|chicote|glitch|
risco|zoom|vertical|flash (padrão: roda entre elas), flash (true), zoom (deriva da câmera, padrão 1.07).
Marcação no texto: [palavra] = caixa vermelha, *palavra* = vermelho, "|" = quebra de linha, ponto final sai na cor.
Tipos:
  palavra    texto, entrada zoom|blur|subir|queda|estica|digita|glitch|peso, destaque (índice da linha), contorno (índice)
  hierarquia linhas [{t, tam p|m|g, cor, contorno, entrada, em (s)}], forma estrela|interrogacao|circulo|cubo|morph
  eco        texto (palavra com cópias em contorno acima e abaixo)
  faixa      texto (itálico sobre faixa vermelha inclinada)
  caixa      texto com [caixa] e *vermelho* (palavras entram uma a uma)
  prompt     texto com [tokens] (caixa de prompt digitando, botão enter, câmera entra)
  render     texto, de, ate (s do contador ETA) (barra de progresso e porcentagem)
  rec        texto (ponto vermelho pulsando, anel tracejado girando, texto digitado ao lado)
  visor      texto, entrada (cantos de câmera e REC piscando)
  forma      texto, sub, figura cubo|morph|circulo|estrela|interrogacao
  pilha_eco  palavras [3-4] (empilham e viram pirâmide de ecos)
  explosao   linhas [{t, cor}] (estrela vermelha atrás; no fim a letra afina e a estrela vira círculo)
"""
import json, os, shutil, subprocess, sys


def _barra():
    """Render com a barra do progresso.py (LEI do usuário, 30/10/2026: todo render de motion com link para acompanhar)."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
    import progresso
    return progresso
AQUI = os.path.dirname(os.path.abspath(__file__))


def gerar(plano, pasta):
    os.makedirs(pasta, exist_ok=True); K = os.path.join(AQUI, "kit")
    plano = dict(plano)
    for k, v in (("w", 1080), ("h", 1920), ("fps", 30), ("cor", "#E8202A"), ("centro_y", 960)): plano.setdefault(k, v)
    for c in plano["cenas"]: c.setdefault("dur", 0.8)
    dur = round(sum(c["dur"] for c in plano["cenas"]), 3)
    open(os.path.join(pasta, "plano.js"), "w").write("window.PLANO = " + json.dumps(plano, ensure_ascii=False) + ";\n")
    shutil.copy(os.path.join(K, "kinetic.js"), pasta); shutil.copy(os.path.join(K, "kinetic.css"), pasta)
    html = open(os.path.join(K, "index.html")).read()
    for a, b in (("%W%", plano["w"]), ("%H%", plano["h"]), ("%FPS%", plano["fps"]), ("%DUR%", dur), ("%CY%", plano["centro_y"])): html = html.replace(a, str(b))
    open(os.path.join(pasta, "index.html"), "w").write(html)
    json.dump({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}}, open(os.path.join(pasta, "hyperframes.json"), "w"))
    print("  ▸", os.path.basename(os.path.normpath(pasta)) + " ·", len(plano["cenas"]), "batidas", dur, "s"); return pasta


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2: raise SystemExit(__doc__)
    pasta = gerar(json.load(open(a[0])), os.path.abspath(a[1]))
    if "--render" in a:
        saida = os.path.abspath(a[a.index("--render") + 1])
        _barra().hf(["npx", "--yes", "hyperframes@0.8.151", "render", pasta, "--format", "mp4", "-q", "high", "-w", "2", "-o", saida], os.path.basename(os.path.dirname(os.path.abspath(__file__)))); print("    →", os.path.basename(saida))
