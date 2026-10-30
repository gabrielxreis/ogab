"""Preset GRAVURA: cada frase vira uma prancha de gravura em cobre que se grava sozinha (contorno, hachura, cruzamento),
com título em romanas cortadas letra a letra, nota em letra cursiva escrita num traço só e aquarela à mão no fim.
Canvas determinístico dirigido pelo HyperFrames. Motor de traço do lemo-opuscar (MIT, LemoLab); ver LICENCAS.md.

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4]

plano.json:
{ "w": 1080, "h": 1920, "fps": 30, "centro_y": 900,
  "cenas": [
    {"dur": 5.5, "kicker": "Atos 1:8", "titulo": "A Grande Missão", "nota": "até os confins da terra",
     "forma": "lamparina"},                                   # forma pronta (lista em FORMAS)
    {"dur": 5, "titulo": "...", "icone": "game-icons:sailboat", "cor": "#4f7a8a"},   # ícone do Iconify (traço cheio)
    {"dur": 5, "titulo": "...", "svg": "M0 0 C...Z", "cor": "#b0552f"},             # caminho SVG próprio
    ...] }
Campos por cena: dur (s, mínimo 4), titulo (romanas, até 2 linhas), kicker (linha pequena em cima), nota (cursiva, embaixo),
credito (rodapé em itálico), cor (aquarela na figura inteira; nas formas prontas pinta só a parte de destaque),
largura/altura (fração da tela que a figura ocupa, padrão .62/.36), estilo ("contour" acompanha a forma, "hatch" retas).
"""
import json, os, re, shutil, subprocess, sys, urllib.request


def _barra():
    """Render com a barra do progresso.py (LEI do usuário, 30/10/2026: todo render de motion com link para acompanhar)."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
    import progresso
    return progresso

AQUI = os.path.dirname(os.path.abspath(__file__))

# Formas prontas, coordenadas locais (a figura é escalada para caber). "destaque" recebe a cor da cena.
FORMAS = {
    "lamparina": [
        {"d": "M-170 0 C-170 -55 -95 -85 0 -85 C70 -85 115 -68 150 -42 L250 -28 C285 -24 292 8 262 16 L160 32 "
              "C122 70 66 88 0 88 C-95 88 -170 55 -170 0 Z"},
        {"d": "M-160 -30 C-240 -60 -270 35 -172 42 L-168 22 C-228 16 -220 -28 -164 -10 Z"},
        {"d": "M262 -32 C226 -52 220 -104 262 -196 C304 -104 298 -52 262 -32 Z", "destaque": True, "fino": True},
    ],
    "chama": [{"d": "M0 160 C-90 120 -110 0 0 -220 C110 0 90 120 0 160 Z", "destaque": True}],
    "pergaminho": [
        {"d": "M-200 -150 H200 V150 H-200 Z", "estilo": "hatch"},
        {"d": "M-232 -186 H232 C254 -186 254 -132 232 -132 H-232 C-254 -132 -254 -186 -232 -186 Z", "estilo": "hatch"},
        {"d": "M-232 132 H232 C254 132 254 186 232 186 H-232 C-254 186 -254 132 -232 132 Z", "estilo": "hatch", "destaque": True},
    ],
    "cruz": [{"d": "M-35 -260 H35 V-110 H150 V-40 H35 V260 H-35 V-40 H-150 V-110 H-35 Z", "estilo": "hatch", "destaque": True}],
    "selo": [{"d": "M0 -200 C110 -200 200 -110 200 0 C200 110 110 200 0 200 C-110 200 -200 110 -200 0 C-200 -110 -110 -200 0 -200 Z",
              "destaque": True}],
}


def icone(nome):
    """Caminho SVG de um ícone do Iconify ("colecao:nome"). game-icons (CC BY 3.0) tem navios, pombas, coroas, mapas."""
    pre, n = nome.split(":", 1)
    req = urllib.request.Request(f"https://api.iconify.design/{pre}/{n}.svg", headers={"User-Agent": "Mozilla/5.0 ogab"})
    svg = urllib.request.urlopen(req, timeout=20).read().decode()
    ds = re.findall(r'\sd="([^"]+)"', svg)
    if not ds:
        raise SystemExit(f"ícone sem caminho: {nome}")
    return " ".join(ds)


def partes(c):
    if c.get("forma"):
        if c["forma"] not in FORMAS:
            raise SystemExit(f"forma '{c['forma']}' não existe; use uma de {sorted(FORMAS)} ou 'icone'/'svg'")
        return [{"d": p["d"], "estilo": p.get("estilo"), "fino": p.get("fino", False),
                 "cor": c.get("cor") if p.get("destaque") else None} for p in FORMAS[c["forma"]]]
    d = c.get("svg") or icone(c["icone"])
    return [{"d": d, "estilo": c.get("estilo", "hatch" if c.get("icone") else "contour"), "cor": c.get("cor")}]


def gerar(plano, pasta):
    os.makedirs(pasta, exist_ok=True)
    cenas = []
    for c in plano["cenas"]:
        if c.get("dur", 0) < 4:
            print(f"aviso: cena '{c.get('titulo', '')}' com {c.get('dur')} s; a gravura precisa de pelo menos 4 s para ler", file=sys.stderr)
        cenas.append({k: c.get(k) for k in ("dur", "titulo", "kicker", "nota", "credito", "largura", "altura")} | {"partes": partes(c)})
    dados = {"w": plano.get("w", 1080), "h": plano.get("h", 1920), "centro_y": plano.get("centro_y", 900), "cenas": cenas}
    open(os.path.join(pasta, "dados.js"), "w").write("window.GRAVURA = " + json.dumps(dados, ensure_ascii=False) + ";\n")
    for item in ("engine", "fonts"):
        shutil.copytree(os.path.join(AQUI, "kit", item), os.path.join(pasta, item), dirs_exist_ok=True)
    shutil.copy(os.path.join(AQUI, "kit", "gravura.js"), pasta)
    dur = round(sum(c["dur"] for c in cenas), 3)
    html = open(os.path.join(AQUI, "kit", "index.html")).read().replace("%DUR%", str(dur)).replace("%W%", str(dados["w"])) \
        .replace("%H%", str(dados["h"])).replace("%FPS%", str(plano.get("fps", 30)))
    open(os.path.join(pasta, "index.html"), "w").write(html)
    json.dump({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}},
              open(os.path.join(pasta, "hyperframes.json"), "w"))
    print("  ▸", os.path.basename(os.path.normpath(pasta)) + " ·", f"{len(cenas)} cenas, {dur} s")
    return pasta, dur


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    pasta, dur = gerar(json.load(open(a[0])), os.path.abspath(a[1]))
    if "--render" in a:
        saida = os.path.abspath(a[a.index("--render") + 1])
        _barra().hf(["npx", "--yes", "hyperframes", "render", pasta, "--format", "mp4", "-q", "delivery", "--workers", "1", "-o", saida], os.path.basename(os.path.dirname(os.path.abspath(__file__))))
        print("    →", os.path.basename(saida))
