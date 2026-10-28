"""Preset POSTER: pôster editorial em movimento (estudado num Reel de design em 27/10/2026). Cada frase vira um pôster:
fundo cinza-claro com vinheta OU preto chapado, um recorte em preto e branco de alto contraste no centro, uma forma
vermelha chapada atrás (disco, quadro com moldura fina ou pedestal), microtipografia de pôster (rótulos miúdos, código
de barras, grade de linhas finas, órbita pontilhada) e o texto entrando palavra a palavra: frase pequena em cima, a
palavra-chave grande embaixo, cada palavra nasce apagada e desfocada e "acende". Uma palavra GIGANTE desfocada atravessa
a tela. Câmera sempre viva (afasta, aproxima, anda, gira), corte seco entre os pôsteres e fecho com a marca no preto.

  python3 gerar.py plano.json <pasta_saida> [--tema padrao|<marca>|caminho/tema.json] [--render saida.mp4 --gif]

plano.json (x/y em px a partir do CENTRO da tela 540,960; texto dentro da caixa segura 900x1200):
{ "w": 1080, "h": 1920, "fps": 30,
  "referencia": ".../referencia.json",             # opcional (storyboard.py/revisor.py)
  "transcricao": "transcricao.json",               # opcional: aí "em" pode ser uma palavra da fala
  "cenas": [
    { "dur": 3.0, "fundo": "claro" | "escuro",
      "camera": ["afasta", "esquerda"],            # afasta | aproxima | direita | esquerda | sobe | desce | gira
      "ritmo": "media" | "rapida" | "lenta",
      "foto": {"arquivo": "fotos/x.jpg", "credito": "NASA, domínio público",
               "recorte": "sujeito" | "escuro" | "nenhum", "altura": 900, "largura": 900, "x": 0, "y": 120,
               "rot": 0, "frente": false},          # recorte escuro = objeto sobre fundo preto (planeta, produto)
      "forma": {"tipo": "disco" | "quadro" | "pedestal", "x": -60, "y": 40, "raio": 330,
                "larg": 420, "alt": 520, "orbita": true},
      "texto": {"linhas": ["ninguém nasce", "sabendo criar"], "x": 0, "y": -300, "em": 0.15, "ate": 1.6,
                "alinhar": "centro" | "esquerda", "grande": 1},   # índice da linha grande (padrão: a última)
      "gigante": {"texto": "CRIAR", "y": 560, "linhas": 1, "frente": true},
      "micro": true,                                # rótulos miúdos, código de barras, grade (padrão true)
      "hud": false,                                 # cantos finos e chip de rótulo (bom no fundo escuro)
      "ref_plano": 1, "ref_o_que": "afasta + anda p/ esquerda" },
    { "dur": 2.0, "fundo": "escuro", "fecho": "nome da marca" } ] }
  em/ate: segundos desde o começo da cena (ou palavra da fala com "transcricao"): as palavras entram uma a uma
  entre em e ate. Cena com "fecho": só a marca no preto (entra pesada e assenta leve, câmera afastando).
Do tema (temas/padrao.json): claro, borda, escuro, tinta, acento, acento2, fontes e os rótulos miúdos (micro).
Marca do cliente = copiar o tema e trocar acento (cor da marca) e os textos miúdos.
"""
import hashlib, json, os, shutil, sys, unicodedata
import numpy as np
from PIL import Image, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__))

SCRIPTS = os.path.join(AQUI, "..", "..", "scripts")
sys.path.insert(0, SCRIPTS)
from hf_preset import renderizar, args_render  # noqa: E402

SEGURA = (90, 360, 990, 1560)   # caixa segura do Instagram (docs/etapas/lettering_motions.md)
CAMERAS = {"afasta", "aproxima", "direita", "esquerda", "sobe", "desce", "gira"}


def _hash(*partes):
    return hashlib.md5("|".join(map(str, partes)).encode()).hexdigest()[:10]


# ---------------------------------------------------------------- recorte P&B de alto contraste
def mascara(caminho, img, modo):
    """Máscara 0-1: sujeito (Apple Vision), escuro (objeto claro sobre preto) ou None (foto inteira)."""
    if modo == "nenhum":
        return None
    rgb = np.asarray(img).astype(np.float32) / 255
    if modo == "escuro":
        L = rgb.max(axis=2)
        return np.clip((L - .06) / .12, 0, 1)
    try:
        from sujeito import mascara_sujeito
        m = mascara_sujeito(caminho).astype(np.float32)
    except Exception as e:
        print(f"aviso: recorte automático falhou em {os.path.basename(caminho)} ({str(e)[:70]}); usando a foto inteira", file=sys.stderr)
        return None
    if m.shape != (img.height, img.width):
        m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize(img.size, Image.BILINEAR)).astype(np.float32) / 255
    if m.mean() < .02:
        print(f"aviso: quase nada recortado em {os.path.basename(caminho)}; usando a foto inteira", file=sys.stderr)
        return None
    import cv2
    b = (m > .5).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(b)
    if n > 2:   # só os pedaços grandes (some a sujeira solta)
        maior = st[1:, cv2.CC_STAT_AREA].max()
        b = np.isin(lab, [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= maior * .05]).astype(np.uint8)
    return np.asarray(Image.fromarray(b * 255).filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32) / 255


def pb(rgb, m):
    """Preto e branco de pôster: luminância esticada pelos percentis do sujeito e curva em S."""
    L = rgb[..., 0] * .3 + rgb[..., 1] * .59 + rgb[..., 2] * .11
    sel = L[m > .5] if m is not None and (m > .5).any() else L.ravel()
    lo, hi = np.percentile(sel, 1.5), np.percentile(sel, 99.2)
    L = np.clip((L - lo) / max(hi - lo, 1e-3), 0, 1)
    L = L * L * (3 - 2 * L) * .55 + L * .45      # S suave: preto fundo, branco que não estoura
    return np.clip(L * .97 + .015, 0, 1)


def recortar(f, base, pasta):
    orig = f["arquivo"] if os.path.isabs(f["arquivo"]) else os.path.join(base, f["arquivo"])
    if not os.path.exists(orig):
        raise SystemExit("Foto não encontrada: " + orig)
    modo = f.get("recorte", "sujeito")
    alt, larg = f.get("altura", 900), f.get("largura", 900)
    nome = "foto_" + _hash(orig, os.path.getmtime(orig), modo, alt, larg) + ".png"
    destino = os.path.join(pasta, "assets", nome)
    if not os.path.exists(destino):
        img = Image.open(orig).convert("RGB")
        m = mascara(orig, img, modo)
        rgb = np.asarray(img).astype(np.float32) / 255
        if m is None:
            m = np.ones(rgb.shape[:2], np.float32)
        ys, xs = np.where(m > .1)
        rgb, m = rgb[ys.min():ys.max() + 1, xs.min():xs.max() + 1], m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        g = pb(rgb, m)
        s = min(alt / g.shape[0], larg / g.shape[1], 1.6)
        tw, th = max(8, int(g.shape[1] * s)), max(8, int(g.shape[0] * s))
        g = Image.fromarray((g * 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
        a = Image.fromarray((m * 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        Image.merge("RGBA", (g, g, g, a)).save(destino, optimize=True)
    w, h = Image.open(destino).size
    return "assets/" + nome, w, h


# ---------------------------------------------------------------- tempos pela fala
def _norm(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if c.isalnum() and unicodedata.category(c) != "Mn")


def palavras(transcricao, base):
    arq = transcricao if os.path.isabs(transcricao) else os.path.join(base, transcricao)
    j = json.load(open(arq, encoding="utf-8"))
    return [{"t": w.get("text", w.get("word", "")), "s": float(w.get("start", 0))}
            for s in j.get("segments", []) for w in s.get("words", [])]


def gerar(plano, pasta, base, tema):
    plano = json.loads(json.dumps(plano))
    W, H = plano.setdefault("w", 1080), plano.setdefault("h", 1920)
    plano.setdefault("fps", 30)
    os.makedirs(os.path.join(pasta, "assets"), exist_ok=True)
    pal = palavras(plano["transcricao"], base) if plano.get("transcricao") else None
    S = 0.0
    for k, c in enumerate(plano["cenas"]):
        c["S"] = S
        c.setdefault("fundo", "escuro" if c.get("fecho") else "claro")
        cams = c.get("camera", [])
        c["camera"] = [cams] if isinstance(cams, str) else cams
        for x in c["camera"]:
            if x not in CAMERAS:
                raise SystemExit(f"cena {k + 1}: câmera '{x}' não existe ({', '.join(sorted(CAMERAS))})")
        if c["dur"] > 4.5 and not c.get("fecho"):
            print(f"aviso: cena {k + 1} com {c['dur']} s; tela parada demais (regra: trocar elemento a cada 2,5-4 s)", file=sys.stderr)

        def quando(v):
            if isinstance(v, (int, float)) or v is None:
                return v or 0
            if not pal:
                raise SystemExit(f'"em": "{v}" é palavra, mas o plano não tem "transcricao"')
            alvo = _norm(v)
            for w in pal:
                if w["s"] >= S - .3 and _norm(w["t"]) == alvo:
                    return round(w["s"] - S, 3)
            raise SystemExit(f'palavra "{v}" não achada depois de {S:.2f} s')
        t = c.get("texto")
        if t:
            t["em"] = quando(t.get("em", .12))
            t["ate"] = quando(t["ate"]) if "ate" in t else round(min(c["dur"] * .62, t["em"] + .32 * sum(len(x.split()) for x in t["linhas"])), 3)
            if (W, H) == (1080, 1920):
                y = H / 2 + t.get("y", 0)
                if y < SEGURA[1] or y > SEGURA[3]:
                    print(f"aviso: texto da cena {k + 1} fora da caixa segura (y={int(y)})", file=sys.stderr)
        f = c.get("foto")
        if f:
            f["src"], f["w"], f["h"] = recortar(f, base, pasta)
        S += c["dur"]
    dur = round(S, 3)
    plano["tema"] = tema
    plano["segura"] = SEGURA
    for a in os.listdir(os.path.join(AQUI, "kit")):   # kit (fontes Inter Tight em kit/fontes/)
        o = os.path.join(AQUI, "kit", a)
        if os.path.isdir(o):
            shutil.copytree(o, os.path.join(pasta, a), dirs_exist_ok=True)
        elif a != "index.html":
            shutil.copy(o, pasta)
    open(os.path.join(pasta, "plano.js"), "w", encoding="utf-8").write("window.PLANO = " + json.dumps(plano, ensure_ascii=False) + ";\n")
    html = open(os.path.join(AQUI, "kit", "index.html"), encoding="utf-8").read()
    for k, v in (("%W%", W), ("%H%", H), ("%FPS%", plano["fps"]), ("%DUR%", dur)):
        html = html.replace(k, str(v))
    open(os.path.join(pasta, "index.html"), "w", encoding="utf-8").write(html)
    json.dump({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}},
              open(os.path.join(pasta, "hyperframes.json"), "w"))
    print("ok", pasta, f"{len(plano['cenas'])} cenas, {dur} s, tema {tema.get('nome')}")
    return pasta


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    nome_tema = a[a.index("--tema") + 1] if "--tema" in a else "padrao"
    arq_tema = nome_tema if nome_tema.endswith(".json") else os.path.join(AQUI, "temas", nome_tema + ".json")
    tema = json.load(open(arq_tema, encoding="utf-8"))
    caminho_plano = os.path.abspath(a[0])
    pasta = gerar(json.load(open(caminho_plano, encoding="utf-8")), os.path.abspath(a[1]), os.path.dirname(caminho_plano), tema)
    saida, gif = args_render(a)
    if saida:
        renderizar(pasta, saida, gif)
