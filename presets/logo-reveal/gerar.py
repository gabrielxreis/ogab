"""Preset LOGO REVEAL: abertura de marca de 5-8 s (acabamento premium do launch).

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4] [--gif]

plano.json: { "w": 1080, "h": 1920, "fps": 60, "dur": 6, "cor": "#C4A34F", "cor2": "#F2E2B3",
  "estilo": "luz" | "linhas" | "pontos",
  "marca": { "logo": "logo.png" (PNG com fundo transparente; SVG serve para luz e linhas), "nome": "Marca" },
  "nome": "texto embaixo do logo (só se o logo não tiver o nome escrito)", "frase": "a frase da marca",
  "tamLogo": 720 largo, 460 quadrado (largura na base 1080), "pontos": 4800 }
Estilo pontos: o desenho do logo é amostrado aqui (Pillow) e vira os alvos dos pontos; sem Pillow ou com SVG, cai em luz.
Logo e cores SÓ do material do cliente; sem logo, vira monograma da inicial na cor da marca.
"""
import json, os, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from hf_preset import montar, renderizar, args_render, traz

AQUI = os.path.dirname(os.path.abspath(__file__))


def proporcao(caminho):
    try:
        with open(caminho, "rb") as f:
            cab = f.read(24)
        if cab[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", cab[16:24]); return h / w
    except Exception:
        pass
    try:
        from PIL import Image
        w, h = Image.open(caminho).size; return h / w
    except Exception:
        return 1


def pontos_do_logo(caminho, maximo=2600):
    """Pontos (0-1) onde o logo tem tinta: canal alfa, ou brilho quando a imagem não tem transparência."""
    from PIL import Image
    im = Image.open(caminho).convert("RGBA"); w, h = im.size
    escala = 520 / max(w, h); im = im.resize((max(1, round(w * escala)), max(1, round(h * escala)))); w, h = im.size
    tem_alfa = im.getextrema()[3][0] < 250
    px = im.load(); out = []
    passo = 2
    while True:
        out = []
        for y in range(0, h, passo):
            for x in range(0, w, passo):
                r, g, b, a = px[x, y]
                if (a > 128) if tem_alfa else (0.299 * r + 0.587 * g + 0.114 * b > 128):
                    out.append([round(x / w, 4), round(y / h, 4)])
        if len(out) <= maximo:
            return out
        passo += 1


def gerar(plano, pasta, base):
    plano = json.loads(json.dumps(plano))
    for k, v in (("w", 1080), ("h", 1920), ("fps", 60), ("dur", 6), ("estilo", "luz"), ("cor", "#C4A34F"), ("cor2", "#F2E2B3")):
        plano.setdefault(k, v)
    m = plano.setdefault("marca", {})
    os.makedirs(pasta, exist_ok=True)
    if m.get("logo"):
        orig = m["logo"] if os.path.isabs(m["logo"]) else os.path.join(base, m["logo"])
        m["logoProp"] = proporcao(orig)
        if plano["estilo"] == "pontos":
            try:
                plano["pontosLogo"] = pontos_do_logo(orig)
            except Exception as e:
                print("aviso: sem amostra do logo (", e, "), estilo luz"); plano["estilo"] = "luz"
        m["logo"] = traz(m["logo"], base, pasta)
    elif plano["estilo"] == "pontos":
        print("aviso: estilo pontos precisa de logo PNG; usando luz"); plano["estilo"] = "luz"
    montar(os.path.join(AQUI, "kit"), plano, pasta, plano["dur"])
    print("  ▸", os.path.basename(os.path.normpath(pasta)) + " ·", plano["estilo"], plano["dur"], "s")
    return pasta


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    arq = os.path.abspath(a[0])
    pasta = gerar(json.load(open(arq, encoding="utf-8")), os.path.abspath(a[1]), os.path.dirname(arq))
    saida, gif = args_render(a)
    if saida:
        renderizar(pasta, saida, gif)
