"""Preset PAINEL (apresentação de app/fintech): fundo navy contínuo, uma cor de destaque, grotesca pesada em caixa
alta, linha de gráfico que se desenha com a ponta acesa, cartões de interface flutuando em 3D com números rolando,
câmera que mergulha no cartão, disco da cor cobrindo a tela e fecho com a marca.

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4]

plano.json: { "w": 1080, "h": 1920, "fps": 30, "cor": "#3FE0B5", "cor2": "#5B8DEF", "cor3": "#8C7CF0",
              "fundo": "#0A0F1E", "tinta": "#0B1530", "marca": "rumo", "final_cartao": "4821", "cenas": [ ... ] }
Campos comuns da cena: tipo, dur (s = tempo da fala), transicao desfoque|chicote|corte|disco (revela usa disco sozinho).
Marcação no texto: *azul* (cor2), [destaque] (cor), ~cinza~, "|" quebra de linha; ponto/vírgula final sai na cor.
Valores que contam: {"de": 0, "ate": 24860.42, "pre": "R$ ", "suf": "", "casas": 2} ou texto fixo "R$ 486".
Tipos:
  linha    texto ("SEU|DINHEIRO": a última linha nasce em contorno e se preenche quando a ponta passa), y, tam
  pilha    grupos [["NÃO","PRECISA"],["FICAR","PARADO."]], em [s de cada grupo], tam (o grupo anterior encolhe e sai)
  painel   titulo, cartoes [{tipo saldo|barras|rosca|meta|lista|aviso|cartao, rotulo, titulo, valor, chip, sub,
           valores, dias, segmentos [{frac, cor}], itens [[nome, valor, fração da barra]], pos [x, y, largura]}],
           foco (índice do cartão onde a câmera mergulha), depois (índice do 2º), zoom, giro
  revela   texto, y, objeto (false tira o cartão), origem [x, y] do disco
  troca    palavras ["SIMPLES.","RÁPIDO."], em [s], rotulo, valor, chip, selo
  cresce   texto, valor, chip, rotulos ["R$ 6 mil", ...], meta ("R$ 50.000"), meta_rotulo
  caos     antes ("MENOS *CAOS.*"), depois (["~MAIS~","CONTROLE."]), valor, chip, meta, itens, virada (0-1)
  regras   titulo, itens [[regra, detalhe]], texto, y
  fecho    linhas, marca, frase (aceita <b>), virada (0-1)
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
    for k, v in (("w", 1080), ("h", 1920), ("fps", 30), ("cor", "#3FE0B5")): plano.setdefault(k, v)
    plano.setdefault("centro_y", plano["h"] / 2)
    for c in plano["cenas"]: c.setdefault("dur", 2.0)
    dur = round(sum(c["dur"] for c in plano["cenas"]), 3)
    open(os.path.join(pasta, "plano.js"), "w").write("window.PLANO = " + json.dumps(plano, ensure_ascii=False) + ";\n")
    shutil.copy(os.path.join(K, "painel.js"), pasta); shutil.copy(os.path.join(K, "painel.css"), pasta)
    html = open(os.path.join(K, "index.html")).read()
    for a, b in (("%W%", plano["w"]), ("%H%", plano["h"]), ("%FPS%", plano["fps"]), ("%DUR%", dur)): html = html.replace(a, str(b))
    open(os.path.join(pasta, "index.html"), "w").write(html)
    json.dump({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}}, open(os.path.join(pasta, "hyperframes.json"), "w"))
    print("  ▸", os.path.basename(os.path.normpath(pasta)) + " ·", len(plano["cenas"]), "cenas", dur, "s"); return pasta


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2: raise SystemExit(__doc__)
    pasta = gerar(json.load(open(a[0])), os.path.abspath(a[1]))
    if "--render" in a:
        saida = os.path.abspath(a[a.index("--render") + 1])
        _barra().hf(["npx", "--yes", "hyperframes@0.8.151", "render", pasta, "--format", "mp4", "-q", "high", "-w", "2", "-o", saida], os.path.basename(os.path.dirname(os.path.abspath(__file__)))); print("    →", os.path.basename(saida))
