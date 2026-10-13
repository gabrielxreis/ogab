"""Preset VECTOR MOTION ("1 prompt, 1 vídeo"): roteiro curto -> cada frase vira uma metáfora visual num estilo.

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4]

plano.json:
{ "estilo": "destaque" | "bolhas" | "grade" | "objetos", "w": 1080, "h": 1920, "fps": 30,
  "cores": {"hi": "#ffffff"},                                   # opcional: troca o branco do protagonista pela cor da marca
  "cenas": [ {"metafora": "um_entre_muitos", "fala": "Enquanto todos esperam", "dur": 2.2}, ... ] }
Metáforas: um_entre_muitos (icone?, alvo?), trabalhando, multidao, frase (check: true/false), sobe_da_pilha, empurra,
forma_vira, revoada, porta, caminho (icone?), calendario (dia, mes), cartoes (icones: [...]), heroi, identidade.
Campo comum: dur (s), zoom (padrão 1.06), fala (texto da tela; na "frase" vira o texto grande).
Ícones: os nomes em kit/icones.json (Material Symbols, Apache 2.0); para outro ícone, ver kit/MaterialSymbolsRounded.codepoints.
"""
import json, os, shutil, subprocess, sys
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(os.path.dirname(AQUI)); FON = os.path.join(RAIZ, "assets", "fontes")


def gerar(plano, pasta):
    os.makedirs(os.path.join(pasta, "fonts"), exist_ok=True); K = os.path.join(AQUI, "kit")
    plano = dict(plano); plano.setdefault("w", 1080); plano.setdefault("h", 1920); plano.setdefault("fps", 30); plano.setdefault("estilo", "destaque")
    plano["icones"] = json.load(open(os.path.join(K, "icones.json")))
    open(os.path.join(pasta, "plano.js"), "w").write("window.PLANO = " + json.dumps(plano, ensure_ascii=False) + ";\n")
    shutil.copy(os.path.join(K, "vectormotion.js"), pasta)
    shutil.copy(os.path.join(K, "icones.ttf"), os.path.join(pasta, "fonts")); shutil.copy(os.path.join(K, "Oswald-SemiBold.ttf"), os.path.join(pasta, "fonts"))
    for f in ("Medium", "SemiBold", "Bold", "ExtraBold"): shutil.copy(os.path.join(FON, "Poppins", f"Poppins-{f}.ttf"), os.path.join(pasta, "fonts"))
    dur = round(sum(c.get("dur", 2.5) for c in plano["cenas"]), 3)
    for c in plano["cenas"]: c.setdefault("dur", 2.5)
    open(os.path.join(pasta, "plano.js"), "w").write("window.PLANO = " + json.dumps(plano, ensure_ascii=False) + ";\n")
    html = open(os.path.join(K, "index.html")).read()
    for a, b in (("%W%", plano["w"]), ("%H%", plano["h"]), ("%FPS%", plano["fps"]), ("%DUR%", dur), ("%EST%", plano["estilo"])): html = html.replace(a, str(b))
    open(os.path.join(pasta, "index.html"), "w").write(html)
    json.dump({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}}, open(os.path.join(pasta, "hyperframes.json"), "w"))
    print("ok", pasta, plano["estilo"], len(plano["cenas"]), "cenas", dur, "s"); return pasta


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2: raise SystemExit(__doc__)
    pasta = gerar(json.load(open(a[0])), os.path.abspath(a[1]))
    if "--render" in a:
        saida = os.path.abspath(a[a.index("--render") + 1])
        subprocess.run(["npx", "--yes", "hyperframes", "render", pasta, "--format", "mp4", "-q", "delivery", "--workers", "1", "-o", saida], check=True); print("render", saida)
