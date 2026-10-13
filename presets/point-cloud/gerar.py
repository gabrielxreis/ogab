"""Preset POINT CLOUD: milhares de pontos desenham fotos reais, textos com volume e formas, e migram de uma cena para a
outra com câmera 3D (HyperFrames + canvas, determinístico, renderiza quadro a quadro).

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4] [--previa]

plano.json:
{ "w": 1080, "h": 1920, "fps": 30, "pontos": 7000, "semente": 7,
  "fundo": "#050505", "cor": "#f4f1ea", "destaque": "#f4f1ea",       # cores dos pontos e do texto em destaque
  "centro_y": 860, "largura": 0.82,                                    # onde fica a figura (px) e quanto da largura ocupa
  "cenas": [
    {"tipo": "galaxia", "dur": 3.2, "giro": 40, "inclinacao": 62, "titulo": "Tudo começa", "kicker": "CAPÍTULO 1"},
    {"tipo": "texto", "valor": "?", "dur": 3.0, "profundidade": 0.18, "giro": 30},
    {"tipo": "imagem", "arquivo": "einstein.jpg", "dur": 4.0, "giro": 18, "relevo": 0.22, "inverter": false,
     "mascara": "oval", "limiar": 0.12, "titulo": "uma <i>pergunta</i>", "credito": "Orren J. Turner, 1947 · domínio público"},
    {"tipo": "esfera" | "anel" | "onda" | "grade" | "nuvem", ...}
  ] }
Campos por cena: dur (s), transicao (s, padrão 1.1), giro (graus girados durante a cena), inclinacao (graus no eixo X),
zoom ([de, para], padrão [1, 1.06]), titulo (aceita <i>itálico</i>), kicker (linha pequena em cima), credito (rodapé).
"""
import json, math, os, random, shutil, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(os.path.dirname(AQUI))
FONTES = os.path.join(RAIZ, "assets", "fontes")


def _reamostrar(pts, n, rng, jitter=0.004):
    """Exatamente n pontos (repete com leve tremor se faltar, sorteia se sobrar)."""
    pts = np.asarray(pts, np.float32)
    idx = rng.choice(len(pts), n, replace=len(pts) < n)
    out = pts[idx].copy()
    if len(pts) < n:
        out[:, :3] += rng.normal(0, jitter, (n, 3)).astype(np.float32)
    return out


def _ordenar(p):
    """Ordem estável (faixas em y, depois x): pontos vizinhos numa cena viram vizinhos na outra (morph limpo)."""
    faixa = np.floor((p[:, 1] + 2) * 22)
    return p[np.lexsort((p[:, 0], faixa))]


def alvo_imagem(c, n, rng):
    im = Image.open(c["arquivo"]).convert("L")
    if c.get("inverter"): im = ImageOps.invert(im)
    im = ImageOps.autocontrast(im, cutoff=1)
    im.thumbnail((420, 420)); a = np.asarray(im, np.float32) / 255.0; H, W = a.shape
    yy, xx = np.mgrid[0:H, 0:W]
    if c.get("mascara") == "oval":
        m = (((xx - W / 2) / (W * 0.46)) ** 2 + ((yy - H / 2) / (H * 0.5)) ** 2) <= 1
        a = a * m
    lim = c.get("limiar", 0.12); peso = np.clip(a - lim, 0, None) ** c.get("gama", 1.4)
    peso = peso.ravel(); peso /= peso.sum()
    k = min(n * 2, int((peso > 0).sum()))
    idx = rng.choice(len(peso), k, replace=False, p=peso)
    s = 2.0 / max(W, H)
    x = (xx.ravel()[idx] - W / 2 + rng.random(k) - 0.5) * s; y = (yy.ravel()[idx] - H / 2 + rng.random(k) - 0.5) * s
    b = a.ravel()[idx]; z = (0.5 - b) * c.get("relevo", 0.22)     # claro vem para frente: relevo ao girar
    return np.stack([x, y, z, b], 1)


def alvo_texto(c, n, rng):
    fonte = c.get("fonte") or os.path.join(FONTES, "PlayfairDisplay", "PlayfairDisplay-Black.ttf")
    f = ImageFont.truetype(fonte, 600); txt = c["valor"]
    l, t, r, b = ImageDraw.Draw(Image.new("L", (10, 10))).textbbox((0, 0), txt, font=f)
    im = Image.new("L", (r - l + 40, b - t + 40), 0); ImageDraw.Draw(im).text((20 - l, 20 - t), txt, font=f, fill=255)
    a = np.asarray(im) > 127; H, W = a.shape
    camadas = c.get("camadas", 7); passo = max(2, int(math.sqrt(a.sum() * camadas / (n * 1.1))))
    ys, xs = np.nonzero(a[::passo, ::passo]); ys, xs = ys * passo, xs * passo
    s = 2.0 / max(W, H); prof = c.get("profundidade", 0.18); pts = []
    for i in range(camadas):
        z = -prof / 2 + prof * i / max(1, camadas - 1); bri = 1.0 if i == 0 else 0.55 + 0.25 * (i % 2)
        pts.append(np.stack([(xs - W / 2) * s, (ys - H / 2) * s, np.full(len(xs), z), np.full(len(xs), bri)], 1))
    return np.concatenate(pts)


def alvo_forma(c, n, rng):
    t = c["tipo"]; u = rng.random(n); v = rng.random(n)
    if t == "galaxia":
        braco = rng.integers(0, c.get("bracos", 2), n); r = np.sqrt(u) * 0.95
        th = braco * 2 * math.pi / c.get("bracos", 2) + r * c.get("voltas", 1.6) * 2 * math.pi + rng.normal(0, 0.35 * (1 - r) + 0.08, n)
        x, z = r * np.cos(th), r * np.sin(th); y = rng.normal(0, 0.03, n) * (1 - r); b = 1 - 0.6 * r
    elif t == "esfera":
        i = np.arange(n) + 0.5; phi = np.arccos(1 - 2 * i / n); th = math.pi * (1 + 5 ** 0.5) * i
        x, y, z = 0.8 * np.cos(th) * np.sin(phi), 0.8 * np.cos(phi), 0.8 * np.sin(th) * np.sin(phi); b = 0.5 + 0.5 * v
    elif t == "anel":
        th = u * 2 * math.pi; r = 0.75 + rng.normal(0, 0.04, n); x, z = r * np.cos(th), r * np.sin(th); y = rng.normal(0, 0.03, n); b = 0.6 + 0.4 * v
    elif t == "onda":
        x = u * 2 - 1; z = v * 1.2 - 0.6; y = 0.12 * np.sin(x * 6) * np.cos(z * 5); b = 0.5 + 0.5 * (1 - abs(x))
    elif t == "grade":
        g = int(math.sqrt(n)); i = np.arange(n); x = (i % g) / g * 1.8 - 0.9; y = (i // g) / g * 1.8 - 0.9; z = np.zeros(n); b = np.full(n, 0.8)
    else:  # nuvem
        x, y, z = rng.normal(0, 0.45, (3, n)); b = 0.4 + 0.6 * v
    return np.stack([x, y, z, b], 1)


def gerar(plano, pasta):
    rng = np.random.default_rng(plano.get("semente", 7)); n = plano.get("pontos", 7000)
    os.makedirs(pasta, exist_ok=True); cenas = []; alvos = []
    for c in plano["cenas"]:
        if c["tipo"] == "imagem":
            if not os.path.isabs(c["arquivo"]): c["arquivo"] = os.path.join(os.path.dirname(plano["_arquivo"]), c["arquivo"])
            p = alvo_imagem(c, n, rng)
        elif c["tipo"] == "texto": p = alvo_texto(c, n, rng)
        else: p = alvo_forma(c, n, rng)
        p = _ordenar(_reamostrar(p, n, rng))
        alvos.append(np.round(p, 4).ravel().tolist())
        cenas.append({k: c.get(k, d) for k, d in (("dur", 3.0), ("transicao", 1.1), ("giro", 24), ("inclinacao", 0), ("zoom", [1, 1.06]),
                                                ("titulo", ""), ("kicker", ""), ("credito", ""))})
    dados = {"w": plano.get("w", 1080), "h": plano.get("h", 1920), "n": n, "fundo": plano.get("fundo", "#050505"),
             "cor": plano.get("cor", "#f4f1ea"), "destaque": plano.get("destaque", "#f4f1ea"), "cy": plano.get("centro_y", 860),
             "largura": plano.get("largura", 0.82), "fase": rng.random(n).round(3).tolist(), "atraso": rng.random(n).round(3).tolist(),
             "cenas": cenas, "alvos": alvos}
    open(os.path.join(pasta, "dados.js"), "w").write("window.PONTOS = " + json.dumps(dados, separators=(",", ":")) + ";\n")
    shutil.copy(os.path.join(AQUI, "kit", "pointcloud.js"), pasta)
    os.makedirs(os.path.join(pasta, "fonts"), exist_ok=True)
    for f in ("PlayfairDisplay/PlayfairDisplay-Italic.ttf", "PlayfairDisplay/PlayfairDisplay-Regular.ttf", "Poppins/Poppins-Light.ttf"):
        shutil.copy(os.path.join(FONTES, f), os.path.join(pasta, "fonts"))
    dur = round(sum(c["dur"] for c in cenas), 3)
    html = open(os.path.join(AQUI, "kit", "index.html")).read().replace("%DUR%", str(dur)).replace("%W%", str(dados["w"])).replace("%H%", str(dados["h"])) \
        .replace("%FPS%", str(plano.get("fps", 30))).replace("%FUNDO%", dados["fundo"]).replace("%COR%", dados["cor"]).replace("%DESTAQUE%", dados["destaque"])
    open(os.path.join(pasta, "index.html"), "w").write(html)
    json.dump({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}}, open(os.path.join(pasta, "hyperframes.json"), "w"))
    print("ok", pasta, f"{len(cenas)} cenas, {n} pontos, {dur} s"); return pasta, dur


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2: raise SystemExit(__doc__)
    plano = json.load(open(a[0])); plano["_arquivo"] = os.path.abspath(a[0])
    pasta, dur = gerar(plano, os.path.abspath(a[1]))
    if "--render" in a:
        saida = os.path.abspath(a[a.index("--render") + 1])
        subprocess.run(["npx", "--yes", "hyperframes", "render", pasta, "--format", "mp4", "-q", "delivery", "--workers", "1", "-o", saida], check=True)
        print("render", saida)
