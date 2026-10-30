"""Preset COLAGEM: colagem dadaísta de revista. Fotos de domínio público recortadas com borda branca de tesoura e
meio-tom, coladas em papel kraft ou jornal, etiquetas de papel rasgado para o texto e movimento em passos de 12 qps
("on twos", cara de stop-motion). Ideia portada do 06-collage do mg-styles-15 (MIT, Vincentwei1021); código nosso.

  python3 gerar.py plano.json <pasta_saida> [--tema padrao|<marca>|caminho/tema.json] [--render saida.mp4 --gif]

plano.json (coordenadas x/y em px a partir do CENTRO da tela 540,960; tudo tem que caber na caixa segura 900x1200):
{ "w": 1080, "h": 1920, "fps": 30,
  "transcricao": "transcricao.json",            # opcional: aí "em" pode ser uma palavra da fala
  "cenas": [
    { "dur": 3.4, "papel": "kraft" | "jornal",  # sem papel: alterna, começando pelo do tema
      "forma": {"tipo": "disco" | "faixa", "x": 0, "y": -40, "raio": 330, "em": 0.1, "cor": "acento" | "#hex"},
      "jornal": [{"x": -280, "y": -300, "rot": -6, "em": 0.05}],          # retalhos de jornal atrás da foto
      "fotos": [{"arquivo": "fotos/x.jpg", "credito": "Nadar, domínio público", "recorte": "sujeito" | "retangulo",
                 "altura": 880, "largura": 760, "x": 0, "y": 40, "rot": -2, "em": 0.25, "cor": false, "fita": true}],
      "rotulos": [{"texto": "VOCÊ SABIA?", "estilo": "tinta" | "acento" | "papel" | "jornal",
                   "tam": 104, "x": 0, "y": -470, "rot": -4, "em": 0.6}] } ] }
  em: segundos desde o começo da cena (ou palavra da fala com "transcricao"). Cada peça "cai" na página no tempo em
  (3 passos antes ela já aparece no ar, perto da câmera; no quadro do em ela bate e solta fiapos de papel).
  recorte "sujeito": Apple Vision (scripts/sujeito.py, Mac 14+; sem Vision cai no retângulo). "retangulo": a foto
  inteira cortada à tesoura. altura/largura: tamanho máximo da foto recortada em px. cor: meio-tom colorido (CMYK)
  em vez de preto e branco. Rótulo com "|" quebra em tiras separadas, uma por linha (entram uma depois da outra).
Do tema (temas/padrao.json): tinta, acento, claro, fita, papel, fontes. Marca do cliente = copiar o tema e trocar.
"""
import hashlib, json, os, shutil, sys, unicodedata
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(AQUI, "..", "..", "scripts")
sys.path.insert(0, SCRIPTS)
from hf_preset import renderizar, args_render  # noqa: E402

SEGURA = (90, 360, 990, 1560)   # caixa segura do Instagram (docs/etapas/lettering_motions.md)


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _hash(*partes):
    return hashlib.md5("|".join(map(str, partes)).encode()).hexdigest()[:10]


# ---------------------------------------------------------------- meio-tom e borda de tesoura
def _tela(h, w, periodo, angulo):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.deg2rad(angulo)
    u = (x * np.cos(a) + y * np.sin(a)) / periodo
    v = (-x * np.sin(a) + y * np.cos(a)) / periodo
    return (np.cos(2 * np.pi * u) + np.cos(2 * np.pi * v)) * .25 + .5


def _ponto(cob, periodo, angulo):
    return np.clip((cob - _tela(*cob.shape, periodo, angulo)) / (1.6 / periodo) + .5, 0, 1)


def _lum(rgb):
    return rgb[..., 0] * .3 + rgb[..., 1] * .59 + rgb[..., 2] * .11


def meio_tom(rgb, mask, tema, cor=False, periodo=7.0):
    L = _lum(rgb)
    sel = L[mask > .5] if (mask > .5).any() else L.ravel()
    lo, hi = np.percentile(sel, 2), np.percentile(sel, 98)
    L = np.clip((L - lo) / max(hi - lo, 1e-3), 0, 1)
    papel = hexrgb(tema["claro"])
    tinta = hexrgb(tema["tinta"])
    if not cor:
        tinta_pt = _ponto(1 - L, periodo, 45)[..., None]
        base = papel * (.7 + .3 * L[..., None])          # tom contínuo fraco por baixo (reprodução de jornal)
        return base * (1 - tinta_pt) + tinta * tinta_pt
    g = L[..., None]
    rgb = np.clip(g + (rgb - _lum(rgb)[..., None]) * 1.15, 0, 1)
    C, M, Y = 1 - rgb[..., 0], 1 - rgb[..., 1], 1 - rgb[..., 2]
    K = np.minimum(np.minimum(C, M), Y)
    d = 1 - K + 1e-5
    out = np.ones_like(rgb) * papel
    for cob, ang, c in (((C - K) / d, 15, (0, .62, .88)), ((M - K) / d, 75, (.9, .12, .48)),
                        ((Y - K) / d, 0, (1, .9, .05)), (K * .95, 45, tuple(tinta))):
        p = _ponto(cob, periodo, ang)[..., None]
        out = out * (1 - p + p * np.array(c, np.float32))
    return rgb * .35 + out * .65


def borda_tesoura(alfa, r, semente):
    """Corte de tesoura em volta da silhueta: dilata, fecha reentrâncias e aproxima por retas (facetas)."""
    import cv2
    rng = np.random.default_rng(semente)
    H, W = alfa.shape
    a = (alfa > .45).astype(np.uint8) * 255
    d = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
    c = r * 3
    d = cv2.morphologyEx(d, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * c + 1, 2 * c + 1)))
    cnts, _ = cv2.findContours(d, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    ss = 3
    out = np.zeros((H * ss, W * ss), np.uint8)
    for cn in cnts:
        if cv2.contourArea(cn) < 200:
            continue
        ap = cv2.approxPolyDP(cn, max(2.5, r * .8), True)[:, 0, :].astype(np.float32)
        ap += rng.uniform(-.9, .9, ap.shape)
        cv2.fillPoly(out, [np.round(ap * ss).astype(np.int32)], 255, lineType=cv2.LINE_AA)
    out = cv2.resize(out, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    return np.maximum(out, alfa)


def mascara(caminho, img, modo):
    """Máscara 0-1 do sujeito (Apple Vision) ou None (retângulo)."""
    if modo == "retangulo":
        return None
    try:
        from sujeito import mascara_sujeito
        m = mascara_sujeito(caminho).astype(np.float32)
    except Exception as e:
        print(f"aviso: recorte automático falhou em {os.path.basename(caminho)} ({str(e)[:70]}); usando retângulo", file=sys.stderr)
        return None
    if m.shape != (img.height, img.width):
        m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize(img.size, Image.BILINEAR)).astype(np.float32) / 255
    if m.mean() < .02:
        print(f"aviso: quase nada recortado em {os.path.basename(caminho)}; usando retângulo", file=sys.stderr)
        return None
    import cv2
    b = (m > .5).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(b)
    if n > 2:   # fica só com os pedaços grandes (some a sujeira solta)
        maior = st[1:, cv2.CC_STAT_AREA].max()
        keep = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= maior * .05]
        b = np.isin(lab, keep).astype(np.uint8)
    m = np.asarray(Image.fromarray(b * 255).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
    return m


def recortar(f, base, pasta, tema, i):
    """Foto -> PNG recortado (meio-tom + borda branca de tesoura). Devolve (arquivo relativo, w, h)."""
    orig = f["arquivo"] if os.path.isabs(f["arquivo"]) else os.path.join(base, f["arquivo"])
    if not os.path.exists(orig):
        raise SystemExit("Foto não encontrada: " + orig)
    modo = f.get("recorte", "sujeito")
    alt, larg = f.get("altura", 820), f.get("largura", 820)
    nome = "foto_" + _hash(orig, os.path.getmtime(orig), modo, alt, larg, f.get("cor"), json.dumps(tema, sort_keys=True)) + ".png"
    destino = os.path.join(pasta, "assets", nome)
    if not os.path.exists(destino):
        img = Image.open(orig).convert("RGB")
        m = mascara(orig, img, modo)
        rgb = np.asarray(img).astype(np.float32) / 255
        if m is None:   # retângulo: a foto inteira, cantos cortados à mão
            m = np.ones(rgb.shape[:2], np.float32)
        ys, xs = np.where(m > .1)
        rgb, m = rgb[ys.min():ys.max() + 1, xs.min():xs.max() + 1], m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        s = min(alt / rgb.shape[0], larg / rgb.shape[1])
        tw, th = max(8, int(rgb.shape[1] * s)), max(8, int(rgb.shape[0] * s))
        rgb = np.asarray(Image.fromarray((rgb * 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)).astype(np.float32) / 255
        m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)).astype(np.float32) / 255
        ht = meio_tom(rgb, m, tema, cor=bool(f.get("cor")))
        r = 9
        p = r * 3 + 4
        ht = np.pad(ht, ((p, p), (p, p), (0, 0)))
        m = np.pad(m, ((p, p), (p, p)))
        if f.get("recorte") == "retangulo" or m.min() > .9 or (m[p:-p, p:-p] > .5).mean() > .97:
            borda = _quad(m.shape, p - r, semente=i + 3)
        else:
            borda = borda_tesoura(m, r, semente=i + 3)
        claro = hexrgb(tema["claro"])
        rgbf = ht * m[..., None] + claro * (1 - m[..., None])
        out = np.dstack([rgbf, borda])
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        Image.fromarray(np.clip(out * 255 + .5, 0, 255).astype(np.uint8), "RGBA").save(destino, optimize=True)
    w, h = Image.open(destino).size
    return "assets/" + nome, w, h


def _quad(forma, margem, semente):
    """Retângulo cortado à tesoura: quatro cantos levemente tortos."""
    rng = np.random.default_rng(semente)
    H, W = forma
    pts = [(margem, margem), (W - margem, margem), (W - margem, H - margem), (margem, H - margem)]
    pts = [(x + rng.uniform(-5, 5), y + rng.uniform(-5, 5)) for x, y in pts]
    im = Image.new("L", (W * 3, H * 3), 0)
    ImageDraw.Draw(im).polygon([(x * 3, y * 3) for x, y in pts], fill=255)
    return np.asarray(im.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255


# ---------------------------------------------------------------- papéis, jornal e grão (gerados, sem direito autoral)
def papeis(pasta, W, H, tema):
    rng = np.random.default_rng(7)
    os.makedirs(os.path.join(pasta, "assets"), exist_ok=True)
    def fibra(base, forca):
        n = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
        n = np.asarray(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1))
                       .resize((W, H), Image.BICUBIC)).astype(np.float32) / 255 - .5
        fios = np.zeros((H, W), np.float32)
        for _ in range(900):   # fibras curtas
            x, y = rng.integers(0, W), rng.integers(0, H)
            L, a = rng.integers(6, 26), rng.uniform(0, np.pi)
            xs = np.clip((x + np.cos(a) * np.arange(L)).astype(int), 0, W - 1)
            ys = np.clip((y + np.sin(a) * np.arange(L)).astype(int), 0, H - 1)
            fios[ys, xs] += rng.uniform(-.5, .5)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        vin = 1 - .16 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        img = base[None, None, :] * (1 + n[..., None] * forca + fios[..., None] * .05) * vin[..., None]
        return np.clip(img, 0, 1)
    kraft = fibra(hexrgb(tema.get("kraft", "#B9976B")), .22)
    Image.fromarray((kraft * 255).astype(np.uint8)).save(os.path.join(pasta, "assets", "papel_kraft.jpg"), quality=90)
    jor = fibra(hexrgb(tema.get("jornal", "#E6DDC9")), .10)
    jim = Image.fromarray((jor * 255).astype(np.uint8))
    _colunas(jim, rng, alpha=26, area=(40, 40, W - 40, H - 40), ncol=4)
    jim.save(os.path.join(pasta, "assets", "papel_jornal.jpg"), quality=90)
    for k in range(2):   # retalhos de jornal (texto falso em colunas, só a textura de longe)
        w, h = 430, 560
        im = Image.new("RGB", (w, h), tuple(int(c * 255) for c in hexrgb(tema.get("jornal", "#E6DDC9"))))
        d = ImageDraw.Draw(im)
        d.rectangle((24, 22, w - 24, 76), fill=(34, 30, 26))
        d.rectangle((24, 86, w - 24, 92), fill=(34, 30, 26))
        _colunas(im, rng, alpha=200, area=(24, 104, w - 24, h - 20), ncol=3)
        a = Image.new("L", (w, h), 0)
        pts = []
        for i in range(25):
            pts.append((i * w / 24, 4 + rng.uniform(0, 8)))
        for i in range(1, 31):
            pts.append((w - 4 - rng.uniform(0, 12), i * h / 30))
        for i in range(24, -1, -1):
            pts.append((i * w / 24, h - 4 - rng.uniform(0, 8)))
        for i in range(29, 0, -1):
            pts.append((4 + rng.uniform(0, 12), i * h / 30))
        ImageDraw.Draw(a).polygon(pts, fill=255)
        im.putalpha(a.filter(ImageFilter.GaussianBlur(.6)))
        im.save(os.path.join(pasta, "assets", f"jornal_{k}.png"), optimize=True)
    for k in range(3):   # grão que muda a cada passo
        g = rng.normal(128, 38, (384, 384)).clip(0, 255).astype(np.uint8)
        Image.fromarray(g, "L").save(os.path.join(pasta, "assets", f"grao_{k}.png"))


def _colunas(im, rng, alpha, area, ncol):
    """Linhas de 'texto' de jornal: palavras como barrinhas, colunas justificadas."""
    over = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    x0, y0, x1, y1 = area
    cw = (x1 - x0 - (ncol - 1) * 14) / ncol
    for c in range(ncol):
        cx = x0 + c * (cw + 14)
        y = y0
        while y < y1 - 8:
            if rng.random() < .06:   # subtítulo
                d.rectangle((cx, y, cx + cw * rng.uniform(.5, .9), y + 9), fill=(28, 24, 20, alpha))
                y += 16
                continue
            x = cx
            fim = cx + (cw if rng.random() > .12 else cw * rng.uniform(.3, .8))
            while x < fim - 6:
                L = min(rng.integers(8, 34), fim - x)
                d.rectangle((x, y, x + L, y + 4), fill=(28, 24, 20, int(alpha * rng.uniform(.6, 1))))
                x += L + 5
            y += 9
    base = im.convert("RGBA")
    base.alpha_composite(over)
    im.paste(base.convert("RGB"))


# ---------------------------------------------------------------- tempos pela fala
def _norm(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if c.isalnum() and unicodedata.category(c) != "Mn")


def palavras(transcricao, base):
    arq = transcricao if os.path.isabs(transcricao) else os.path.join(base, transcricao)
    j = json.load(open(arq, encoding="utf-8"))
    out = []
    for s in j.get("segments", []):
        for w in s.get("words", []):
            out.append({"t": w.get("text", w.get("word", "")), "s": float(w.get("start", 0))})
    return out


def gerar(plano, pasta, base, tema):
    plano = json.loads(json.dumps(plano))
    W, H = plano.setdefault("w", 1080), plano.setdefault("h", 1920)
    plano.setdefault("fps", 30)
    os.makedirs(pasta, exist_ok=True)
    pal = palavras(plano["transcricao"], base) if plano.get("transcricao") else None
    papeis(pasta, W, H, tema)
    S, papel0 = 0.0, tema.get("papel", "kraft")
    outro = {"kraft": "jornal", "jornal": "kraft"}
    for k, c in enumerate(plano["cenas"]):
        c["S"] = S
        c.setdefault("papel", papel0 if k % 2 == 0 else outro[papel0])

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
        for grupo in ("fotos", "rotulos", "jornal"):
            for e in c.get(grupo, []):
                e["em"] = quando(e.get("em", 0))
        if c.get("forma"):
            c["forma"]["em"] = quando(c["forma"].get("em", 0))
        for i, f in enumerate(c.get("fotos", [])):
            f["src"], f["w"], f["h"] = recortar(f, base, pasta, tema, k * 10 + i)
            esc = f.get("escala", 1)
            cx, cy = W / 2 + f.get("x", 0), H / 2 + f.get("y", 0)
            x0, y0, x1, y1 = cx - f["w"] * esc / 2, cy - f["h"] * esc / 2, cx + f["w"] * esc / 2, cy + f["h"] * esc / 2
            if (W, H) == (1080, 1920) and (x0 < SEGURA[0] - 4 or x1 > SEGURA[2] + 4 or y0 < SEGURA[1] - 4 or y1 > SEGURA[3] + 4):
                print(f"aviso: foto {os.path.basename(f['arquivo'])} da cena {k + 1} sai da caixa segura "
                      f"({int(x0)},{int(y0)})-({int(x1)},{int(y1)}); diminuir altura/largura ou mexer x/y", file=sys.stderr)
        S += c["dur"]
    dur = round(S, 3)
    tema = dict(tema)
    for chave in ("fonte_arquivo", "fonte_pequena_arquivo"):   # fonte da marca fora do kit: vai junto para a pasta
        arq = tema.get(chave)
        if arq and os.path.isabs(arq):
            os.makedirs(os.path.join(pasta, "fontes"), exist_ok=True)
            shutil.copy(arq, os.path.join(pasta, "fontes", os.path.basename(arq)))
            tema[chave] = "fontes/" + os.path.basename(arq)
    plano["tema"] = tema
    plano["segura"] = SEGURA
    # kit
    for a in os.listdir(os.path.join(AQUI, "kit")):
        o = os.path.join(AQUI, "kit", a)
        if os.path.isdir(o):
            shutil.copytree(o, os.path.join(pasta, a), dirs_exist_ok=True)
        elif a != "index.html":
            shutil.copy(o, pasta)
    open(os.path.join(pasta, "plano.js"), "w", encoding="utf-8").write("window.PLANO = " + json.dumps(plano, ensure_ascii=False) + ";\n")
    html = open(os.path.join(AQUI, "kit", "index.html"), encoding="utf-8").read()
    for k, v in (("%W%", W), ("%H%", H), ("%FPS%", plano["fps"]), ("%DUR%", dur), ("%PAPEL%", tema["claro"])):
        html = html.replace(k, str(v))
    open(os.path.join(pasta, "index.html"), "w", encoding="utf-8").write(html)
    json.dump({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}},
              open(os.path.join(pasta, "hyperframes.json"), "w"))
    print("  ▸", os.path.basename(os.path.normpath(pasta)) + " ·", f"{len(plano['cenas'])} cenas, {dur} s, tema {tema.get('nome')}")
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
