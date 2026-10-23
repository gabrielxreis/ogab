"""RITMO: zoom, punch-in e transição de lente dos estilos do grupo `ritmo` (motor "davinci").

  python3 presets/estilos/ritmo/ritmo.py previa <id> [<id> ...]     -> exemplo.gif sobre uma gravação REAL (OGAB_PREVIA_VIDEO)
  python3 presets/estilos/ritmo/ritmo.py chaves <id> palavras.json [--rosto x0,y0,x1,y1] [--video take.mp4]

No DaVinci (regra 1h2: o take NUNCA é re-renderizado, tudo vira keyframe no editor):
  import ritmo; ritmo.aplicar(item, "punch-inicio", palavras, rostos=None, fps_arquivo=None)
  -> chaves(...) e R.animar_clipe(item, chaves) (nó Transform no Fusion do clipe). `palavras` = [{"w", "ini", "fim"}]
  em segundos do ARQUIVO (transcrição do próprio take). `rostos` = {t: (x0, y0, x1, y1)} de presets/cena/rosto.py
  (sem isso, `aplicar` mede sozinho no arquivo do clipe quando o estilo precisa do rosto).

Conta do Transform do Fusion: tela = Center + zoom * (fonte - 0.5), coordenadas 0-1. O Center é sempre preso para a
imagem cobrir o quadro inteiro (nunca aparece borda preta). Aqui tudo em y para baixo; `animar_clipe` recebe y para cima.
"""
import json, os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__)); ESTILOS = os.path.dirname(AQUI); OGAB = os.path.dirname(os.path.dirname(ESTILOS))
TRAB = os.path.expanduser("~/.cache/ogab_estilos")
ALVO_Y = .40                        # onde o rosto fica na tela quando o zoom puxa para ele (um pouco acima do meio)


# ------------------------------------------------------------ frases
def frases(palavras, max_pal=4, max_s=2.2, pausa=.30):
    """Quebra a fala em frases: pontuação, pausa >= `pausa` s, ou `max_pal` palavras / `max_s` s. -> [(ini, fim, n)]."""
    out, cur = [], []
    for i, p in enumerate(palavras):
        cur.append(p)
        prox = palavras[i + 1] if i + 1 < len(palavras) else None
        fim_pont = p["w"].rstrip()[-1:] in ".,!?;:"
        if (prox is None or fim_pont or prox["ini"] - p["fim"] >= pausa or len(cur) >= max_pal
                or p["fim"] - cur[0]["ini"] >= max_s):
            out.append((cur[0]["ini"], cur[-1]["fim"], len(cur))); cur = []
    return out


# ------------------------------------------------------------ geometria
def _centro(z, foco=None, w=1080, h=1920):
    """Center (x, y para baixo) do Transform para zoom z: com `foco` (caixa do rosto em px) leva o rosto para o meio
    (x 0.5, y ALVO_Y) o quanto der sem mostrar borda; sem foco, zoom no meio."""
    if not foco or z <= 1.0001:
        return .5, .5
    fx, fy = (foco[0] + foco[2]) / 2 / w, (foco[1] + foco[3]) / 2 / h
    lo, hi = 1 - z / 2, z / 2
    cx = min(hi, max(lo, .5 - z * (fx - .5)))
    cy = min(hi, max(lo, ALVO_Y - z * (fy - .5)))
    return round(cx, 4), round(cy, 4)


def _rosto_em(rostos, t):
    if not rostos:
        return None
    if isinstance(rostos, (list, tuple)):
        return rostos
    k = min(rostos, key=lambda x: abs(float(x) - t))
    return rostos[k]


def _k(t, z, rostos, w, h):
    cx, cy = _centro(z, _rosto_em(rostos, t), w, h)
    return (round(max(0.0, t), 4), {"zoom": round(z, 4), "x": cx, "y": cy})


# ------------------------------------------------------------ estilos
def chaves(eid, palavras, rostos=None, w=1080, h=1920, fps=24.0, cortes=None):
    """Lista [(t_arquivo, {"zoom", "x", "y"})] (y para baixo) do estilo `eid`. `cortes` (zoom-blur): instantes dos
    cortes; sem eles, usa o começo de cada frase depois da primeira."""
    q = 1.0 / fps
    fr = frases(palavras)
    K = []
    if eid == "punch-inicio":
        # zoom seco no começo de cada frase: degrau de 3 quadros com um tranco de +4% que assenta em 0,25 s;
        # níveis 1.00 -> 1.08 -> 1.16 e volta ao aberto (a volta é corte seco), então o plano sempre muda.
        niveis, ant = [1.0, 1.08, 1.16], 1.0
        for i, (a, b, _) in enumerate(fr):
            z = niveis[i % 3]
            K += [_k(a - q, ant, rostos, w, h), _k(a + 2 * q, z + .04, rostos, w, h), _k(a + .25, z, rostos, w, h)]
            ant = z
    elif eid == "dois-enquadramentos":
        # um take, dois planos: aberto (1.0) e fechado (1.32 no rosto), trocando a cada frase com corte seco (2 chaves
        # a 1 quadro de distância). Fica parado dentro da frase, como duas câmeras.
        for i, (a, b, _) in enumerate(fr):
            z = 1.0 if i % 2 == 0 else 1.32
            ant = 1.32 if i % 2 == 0 else 1.0
            if i == 0:
                K.append(_k(a - q, z, rostos, w, h))
            else:
                K += [_k(a - q, ant, rostos, w, h), _k(a, z, rostos, w, h)]
    elif eid == "zoom-rosto":
        # frase curta (até 3 palavras ou 1,2 s): punch-in de 118% em 0,12 s, segura, volta seco no fim.
        # frase longa: aproxima devagar até 108% e volta suave em 0,35 s no fim. Sempre levando o rosto para o meio.
        for a, b, n in fr:
            if n <= 3 or b - a <= 1.2:
                K += [_k(a - q, 1.0, rostos, w, h), _k(a + .12, 1.18, rostos, w, h), _k(b, 1.18, rostos, w, h),
                      _k(b + q, 1.0, rostos, w, h)]
            else:
                K += [_k(a, 1.0, rostos, w, h), _k(b - .35, 1.08, rostos, w, h), _k(b, 1.0, rostos, w, h)]
    elif eid == "zoom-blur":
        # transição: 0,14 s antes do corte a imagem dispara para 135% (desfoque de movimento no Transform), e o plano
        # seguinte entra de 135% voltando a 100% em 0,18 s. A luz quente vaza no meio (ver aplicar/_luz).
        cs = cortes if cortes is not None else [a for a, _, _ in fr[1:]]
        for c in cs:
            K += [_k(c - .14, 1.0, rostos, w, h), _k(c - q, 1.35, rostos, w, h), _k(c, 1.35, rostos, w, h),
                  _k(c + .18, 1.0, rostos, w, h)]
    else:
        raise SystemExit(f"ritmo sem chaves: {eid}")
    K = sorted(((round(t * fps) / fps, c) for t, c in K), key=lambda x: x[0])   # na grade de quadros: corte seco = 1 quadro
    limpo = []
    for t, c in K:   # duas chaves no mesmo quadro: fica a última
        if limpo and abs(limpo[-1][0] - t) < q / 2:
            limpo[-1] = (t, c)
        else:
            limpo.append((t, c))
    return limpo


def luz(eid, palavras, cortes=None):
    """Força (0-1) da luz quente vazando em cada chave (só zoom-blur): pico no corte."""
    if eid != "zoom-blur":
        return []
    cs = cortes if cortes is not None else [a for a, _, _ in frases(palavras)[1:]]
    return [x for c in cs for x in ((c - .16, 0.0), (c, .55), (c + .22, 0.0))]


# ------------------------------------------------------------ DaVinci
def aplicar(item, eid, palavras, rostos=None, fps_arquivo=None, cortes=None):
    """Grava o estilo no clipe da timeline (keyframes no Fusion do clipe, sem render)."""
    sys.path.insert(0, os.path.join(OGAB, "scripts"))
    import resolve_lib as R
    mpi = item.GetMediaPoolItem()
    arq = mpi.GetClipProperty("File Path")
    res = (mpi.GetClipProperty("Resolution") or "1080x1920").lower().split("x")
    w, h = int(res[0]), int(res[1])
    fps = fps_arquivo or float(mpi.GetClipProperty("FPS") or 30)
    if rostos is None and eid in ("zoom-rosto", "dois-enquadramentos", "punch-inicio") and arq and os.path.exists(arq):
        sys.path.insert(0, os.path.join(OGAB, "presets", "cena"))
        import rosto
        from gerar import sonda
        _, _, _, dur = sonda(arq)
        rostos = rosto.rostos(arq, w, h, dur) or None
    K = chaves(eid, palavras, rostos, w, h, fps, cortes)
    nome = R.animar_clipe(item, [(t, dict(c, y=round(1 - c["y"], 4))) for t, c in K], fps, nome="RitmoGab")
    if eid == "zoom-blur":
        _blur_e_luz(R, item, nome, luz(eid, palavras, cortes), fps)
    return K


def _blur_e_luz(R, item, nome, forcas, fps):
    """Desfoque de movimento no Transform + luz quente (fundo laranja numa elipse suave, modo Screen) com Blend
    animado. Valores gravados FORA do Lock (davinci_api.md: dentro do Lock não sai no render)."""
    comp = R._comp_do_clipe(item)
    tf = comp.FindTool(nome)
    for k, v in (("MotionBlur", 1), ("Quality", 8), ("ShutterAngle", 220)):
        tf.SetInput(k, v)
    mo = comp.FindTool("MediaOut1")
    mg = comp.FindTool("LuzGab")
    if not mg:
        comp.Lock()
        bg = comp.AddTool("Background", -32768, -32768); el = comp.AddTool("EllipseMask", -32768, -32768)
        mg = comp.AddTool("Merge", -32768, -32768); mg.SetAttrs({"TOOLS_Name": "LuzGab"})
        comp.Unlock()
        anterior = mo.Input.GetConnectedOutput()
        bg.EffectMask = el.Mask
        mg.Background = anterior; mg.Foreground = bg.Output; mo.Input = mg.Output
        for k, v in (("TopLeftRed", 1.0), ("TopLeftGreen", .55), ("TopLeftBlue", .18), ("TopLeftAlpha", 1.0)):
            bg.SetInput(k, v)
        el.SetInput("Center", {1: .82, 2: .78}); el.SetInput("Width", 1.1); el.SetInput("Height", .9); el.SetInput("SoftEdge", .45)
        mg.SetInput("ApplyMode", "Screen")
        mg.AddModifier("Blend", "BezierSpline")
    for t, v in forcas:
        mg.SetInput("Blend", v, R._quadro_comp(comp, t, fps))


# ------------------------------------------------------------ prévia (gravação real, ffmpeg + PIL)
def _quadros(video, w, h):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", video, "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(w * h * 3)
        if len(b) < w * h * 3:
            break
        yield b


def _interp(K, t):
    if t <= K[0][0]:
        return K[0][1]
    for (t0, a), (t1, b) in zip(K, K[1:]):
        if t0 <= t <= t1:
            u = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            u = u * u * (3 - 2 * u)   # Bezier suave como o spline do Fusion
            return {k: a[k] + (b[k] - a[k]) * u for k in a}
    return K[-1][1]


def _forca(L, t):
    if not L:
        return 0.0
    for (t0, a), (t1, b) in zip(L, L[1:]):
        if t0 <= t <= t1:
            return a + (b - a) * (t - t0) / (t1 - t0)
    return 0.0


def previa(eid):
    from PIL import Image, ImageFilter, ImageChops
    pasta = os.path.join(AQUI, eid)
    m = json.load(open(os.path.join(pasta, "estilo.json"), encoding="utf-8"))
    video = os.environ.get("OGAB_PREVIA_VIDEO") or os.path.join(TRAB, "gravacao.mp4")
    if not os.path.exists(video):
        raise SystemExit("sem gravação REAL para a prévia (nada de personagem ilustrado): defina OGAB_PREVIA_VIDEO ou ponha "
                         f"gravacao.mp4 + palavras.json em {TRAB}")
    pal = json.load(open(os.environ.get("OGAB_PREVIA_PALAVRAS") or os.path.join(TRAB, "palavras.json"), encoding="utf-8"))
    W, H, fps = 540, 960, 24.0
    sys.path.insert(0, os.path.join(OGAB, "presets", "cena"))
    import rosto as _ro
    from gerar import sonda
    vw, vh, fps, dur = sonda(video)
    W, H = (540, 960) if vh >= vw else (960, 540)
    rosto = {t: [v * W / vw if i % 2 == 0 else v * H / vh for i, v in enumerate(c)]
             for t, c in _ro.rostos(video, vw, vh, dur).items()} or None
    K = chaves(eid, pal, rosto, W, H, fps)
    L = luz(eid, pal)
    ex = m.get("exemplo") or {}
    de, ate = ex.get("de", 0), ex.get("ate", 5)
    luzimg = None
    if L:   # mesma luz do Fusion: laranja numa elipse suave no canto de cima à direita, modo Screen
        import numpy as np
        yy, xx = np.mgrid[0:H, 0:W]
        d = np.sqrt(((xx - W * .82) / (W * .55)) ** 2 + ((yy - H * .22) / (H * .45)) ** 2)
        msk = Image.fromarray((np.clip(1 - d, 0, 1) ** 1.6 * 255).astype("uint8"), "L")
        luzimg = (Image.new("RGB", (W, H), (255, 140, 46)), msk)
    out = os.path.join(TRAB, f"ritmo_{eid}"); os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))
    ant, n = None, 0
    for i, b in enumerate(_quadros(video, W, H)):
        t = i / fps
        if t < de or t > ate:
            continue
        c = _interp(K, t) if K else {"zoom": 1, "x": .5, "y": .5}
        z, cx, cy = c["zoom"], c["x"], c["y"]
        x0, y0 = (.5 + (0 - cx) / z) * W, (.5 + (0 - cy) / z) * H
        x1, y1 = (.5 + (1 - cx) / z) * W, (.5 + (1 - cy) / z) * H
        img = Image.frombytes("RGB", (W, H), b).transform((W, H), Image.EXTENT, (x0, y0, x1, y1), Image.BICUBIC)
        if eid == "zoom-blur":
            dz = abs(z - (ant or z)); ant = z
            if dz > .004:   # desfoque radial aproximado: média de cópias levemente maiores
                acc = img.copy()
                for k in range(1, 16):
                    s = 1 + dz * k * .22
                    cp = img.transform((W, H), Image.EXTENT, (W / 2 - W / 2 / s, H * .4 - H * .4 / s, W / 2 + W / 2 / s, H * .4 + H * .6 / s), Image.BILINEAR)
                    acc = Image.blend(acc, cp, 1 / (k + 1))
                img = acc.filter(ImageFilter.GaussianBlur(min(3.5, dz * 60)))
            a = _forca(L, t)
            if a > 0:
                tela = ImageChops.screen(img, luzimg[0])
                img = Image.composite(tela, img, luzimg[1].point(lambda v: int(v * a)))
        img.save(os.path.join(out, f"q_{n:04d}.png")); n += 1
    gif = os.path.join(pasta, "exemplo.gif")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", os.path.join(out, "q_%04d.png"), "-vf",
                    "fps=15,scale=300:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=%d[p];[b][p]paletteuse=dither=bayer:bayer_scale=%d"
                    % ((160, 3) if L else (72, 5)),
                    "-loop", "0", gif], check=True)
    print("ok:", gif)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    if a[0] == "previa":
        for e in a[1:]:
            previa(e)
    elif a[0] == "chaves":
        pal = json.load(open(a[2], encoding="utf-8"))
        rz = [float(v) for v in a[a.index("--rosto") + 1].split(",")] if "--rosto" in a else None
        print(json.dumps(chaves(a[1], pal, rz), ensure_ascii=False, indent=1))
    else:
        raise SystemExit(__doc__)
