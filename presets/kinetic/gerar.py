"""Preset KINETIC (tipografia cinética): cada batida da fala vira 1-3 palavras ENORMES, fundo alternando preto (brilho
vermelho), vermelho chapado e branco; entradas variadas (zoom, chicote com desfoque, pilha, queda, máquina de escrever,
esticada, glitch), ponto final vermelho, etiqueta pequena ("HA"), círculo de cor e tremor no impacto.

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4]

plano.json:
{ "w": 1080, "h": 1920, "fps": 30, "cor": "#E8202A", "centro_y": 960, "largura": 0.86,
  "cenas": [
    {"texto": "NÃO", "dur": 0.6, "fundo": "preto", "entrada": "glitch"},
    {"texto": "NÃO|DÁ PRA|ACREDITAR.", "dur": 1.2, "fundo": "branco", "entrada": "pilha", "destaque": 1},
    {"texto": "OKAY.", "dur": 0.9, "fundo": "preto", "entrada": "zoom", "tag": "HA", "flash": true},
    ... ] }
Por batida: texto ("|" quebra linha; ponto/!/? final sai na cor), dur (s, = tempo da fala), fundo preto|vermelho|branco
(padrão alterna), entrada zoom|blur|pilha|queda|digita|estica|glitch, destaque (índice da linha na cor), tag (texto
pequeno que pula), circulo (true), flash (true), impacto (false tira o tremor), saida "chicote", zoom (padrão 1.05).
"""
import json, os, shutil, subprocess, sys
AQUI = os.path.dirname(os.path.abspath(__file__))


def gerar(plano, pasta):
    os.makedirs(pasta, exist_ok=True); K = os.path.join(AQUI, "kit")
    plano = dict(plano)
    for k, v in (("w", 1080), ("h", 1920), ("fps", 30), ("cor", "#E8202A"), ("centro_y", 960)): plano.setdefault(k, v)
    for c in plano["cenas"]: c.setdefault("dur", 0.8)
    dur = round(sum(c["dur"] for c in plano["cenas"]), 3)
    open(os.path.join(pasta, "plano.js"), "w").write("window.PLANO = " + json.dumps(plano, ensure_ascii=False) + ";\n")
    shutil.copy(os.path.join(K, "kinetic.js"), pasta)
    html = open(os.path.join(K, "index.html")).read()
    for a, b in (("%W%", plano["w"]), ("%H%", plano["h"]), ("%FPS%", plano["fps"]), ("%DUR%", dur), ("%CY%", plano["centro_y"])): html = html.replace(a, str(b))
    open(os.path.join(pasta, "index.html"), "w").write(html)
    json.dump({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}}, open(os.path.join(pasta, "hyperframes.json"), "w"))
    print("ok", pasta, len(plano["cenas"]), "batidas", dur, "s"); return pasta


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2: raise SystemExit(__doc__)
    pasta = gerar(json.load(open(a[0])), os.path.abspath(a[1]))
    if "--render" in a:
        saida = os.path.abspath(a[a.index("--render") + 1])
        subprocess.run(["npx", "--yes", "hyperframes@0.8.151", "render", pasta, "--format", "mp4", "-q", "high", "-w", "2", "-o", saida], check=True); print("render", saida)
