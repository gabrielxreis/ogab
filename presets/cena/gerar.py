"""Motor comum dos presets de apresentador: DESTAQUE (legenda), PALCO (texto atrás), ÓRBITA (cartões),
LENTE (câmera) e BANCADA (tela verde). Um plano pode usar um preset só ou vários juntos.

  python3 gerar.py plano.json <pasta_saida> [--sem-render]

Saída em <pasta_saida> (só o que o plano usa):
  palco.mov   texto atrás (alfa)            -> fica ENTRE o vídeo e o recorte da pessoa
  recorte.mov a pessoa recortada (alfa)     -> só quando há PALCO
  frente.mov  DESTAQUE + ÓRBITA (alfa)     -> por cima de tudo
  base.mp4    vídeo com a LENTE aplicada (zooms); o recorte recebe a mesma lente (recorte_lente.mov)
  previa.mp4  tudo montado, com o áudio
No DaVinci: V1 base.mp4, V2 palco.mov, V3 recorte_lente.mov, V4 frente.mov (Fusion/HyperFrames continua editável no
projeto gerado: proj_palco/ e proj_frente/).

plano.json:
{ "video": "talking.mp4", "palavras": "palavras.json", "recorte": "recorte.mov" (opcional), "dest": "#F2D16B",
  "destaque": {"y": 1180, "max_palavras": 3,
               "enfase": {"joão": "grande", "a grande missão": "serifa", "de graça": "marca"},   # grande|serifa|pequena|marca
               "empilhadas": [{"de": 20.1, "ate": 23.0, "linhas": [["estar", "pequena"], ["um passo", "grande"],
                                                                   ["à frente", "serifa"], ["mesmo com pouco tempo", "pequena"]]}]},
  "palco":    [{"texto": "JOÃO", "de": 1.0, "ate": 2.6, "sub": "ALUNO", "estilo": "sans|serifa", "y": 330, "cor": "#fff"}],
  "orbita":  [{"tipo": "checklist", "de": 15, "ate": 19.8, "titulo": "O QUE MUDOU", "itens": [["Aprendi na prática", 15.6]]},
               {"tipo": "progresso", "de": 5, "ate": 8, "titulo": "Seu reel está pronto", "itens": ["Cortes", "Legenda"]},
               {"tipo": "cta", "de": 27.2, "ate": 30, "texto": "MISSÃO", "rotulo": "comenta", "y": 1460}],
  "lente":    {"zoom": [{"de": 11.0, "ate": 13.4, "escala": 1.25}]} }
palavras.json: [{"w": "Olá", "ini": 0.0, "fim": 0.3}, ...] (transcrição com tempo por palavra).
Ênfase "marca": o grupo inteiro vira PÍLULA branca e a palavra ganha marca-texto.
"""
import json, os, re, shutil, subprocess, sys, unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__)); PRESETS = os.path.dirname(AQUI); RAIZ = os.path.dirname(PRESETS)
FONTES = [("Poppins", f) for f in ("Poppins-Bold.ttf", "Poppins-ExtraBold.ttf", "Poppins-Black.ttf")] + \
         [("PlayfairDisplay", f) for f in ("PlayfairDisplay-Italic.ttf", "PlayfairDisplay-SemiBoldItalic.ttf")]
ALTURA = {"grande": 150, "serifa": 120, "pilula": 84}


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower()); s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", "", s).strip()


def sonda(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                        "-show_entries", "format=duration", "-of", "json", arq], capture_output=True, text=True, check=True)
    d = json.loads(r.stdout); st = d["streams"][0]; n, den = st["r_frame_rate"].split("/")
    return int(st["width"]), int(st["height"]), float(n) / float(den), float(d["format"]["duration"])


# ------------------------------------------------------------ DESTAQUE: grupos, ênfases, pílula e frases empilhadas
def destaque(palavras, cfg, dur):
    max_p = cfg.get("max_palavras", 3); y0 = cfg.get("y", 1180)
    enf = {norm(k): v for k, v in (cfg.get("enfase") or {}).items()}
    pilhas = cfg.get("empilhadas") or []
    dentro = lambda t: any(p["de"] - .05 <= t < p["ate"] for p in pilhas)
    txt = [norm(p["w"]) for p in palavras]
    estilo = ["base"] * len(palavras); prende = [False] * len(palavras)   # prende: não quebrar depois desta palavra
    for k, e in enf.items():
        kw = k.split()
        for s in range(len(txt) - len(kw) + 1):
            if txt[s:s + len(kw)] == kw:
                for j in range(s, s + len(kw)):
                    estilo[j] = e; prende[j] = j < s + len(kw) - 1
    grupos, cur = [], []
    for i, p in enumerate(palavras):
        if dentro(p["ini"]):
            continue
        cur.append(i)
        prox = palavras[i + 1] if i + 1 < len(palavras) else None
        fim_frase = p["w"].rstrip().endswith((".", ",", "?", "!", ":"))
        pausa = prox is not None and prox["ini"] - p["fim"] > .4
        if prox is None or dentro(prox["ini"]) or (not prende[i] and (pausa or fim_frase or len(cur) >= max_p)):
            grupos.append(cur); cur = []
    if cur:
        grupos.append(cur)

    def bloco(ini, fim, linhas):
        alto = sum(ALTURA.get(l["tipo"], 62) for l in linhas)
        return {"ini": round(ini, 3), "fim": round(fim, 3), "y": round(y0 - max(0, alto - 62) * .5), "linhas": linhas,
                "brilho": any(l["tipo"] == "serifa" for l in linhas)}

    out = []
    for gi, g in enumerate(grupos):
        pil = any(estilo[i] == "marca" for i in g)
        linhas = []
        for i in g:
            p = palavras[i]; tp = "pilula" if pil else estilo[i]
            pal = {"w": p["w"] if tp in ("base", "pilula") else p["w"].rstrip(","), "ini": round(p["ini"], 3)}
            if estilo[i] == "marca":
                pal["marca"] = True; pal["w"] = p["w"].rstrip(".,")
            if linhas and linhas[-1]["tipo"] == tp:
                linhas[-1]["palavras"].append(pal)
            else:
                linhas.append({"tipo": tp, "palavras": [pal]})
        ini = palavras[g[0]]["ini"]
        prox_ini = palavras[grupos[gi + 1][0]]["ini"] if gi + 1 < len(grupos) else dur
        for pl in pilhas:
            if ini < pl["de"] < prox_ini:
                prox_ini = pl["de"]
        out.append(bloco(ini, min(prox_ini, palavras[g[-1]]["fim"] + 1.2), linhas))
    for pl in pilhas:   # casa as palavras do trecho com as linhas pedidas, na ordem
        trecho = [p for p in palavras if pl["de"] - .05 <= p["ini"] < pl["ate"]]; k = 0; linhas = []
        for texto, tp in pl["linhas"]:
            n = len(texto.split()); ws = trecho[k:k + n]; k += n
            linhas.append({"tipo": tp, "palavras": [{"w": t, "ini": round(w["ini"] if w else pl["de"], 3)}
                                                   for t, w in zip(texto.split(), ws + [None] * (n - len(ws)))]})
        out.append(bloco(pl["de"], pl["ate"], linhas))
    return sorted(out, key=lambda g: g["ini"])


# ------------------------------------------------------------ camadas HyperFrames
def camada(nome, modulos, plano_js, pasta, w, h, fps, dur):
    proj = os.path.join(pasta, f"proj_{nome}"); os.makedirs(os.path.join(proj, "fonts"), exist_ok=True)
    for fam, f in FONTES:
        shutil.copy(os.path.join(RAIZ, "assets", "fontes", fam, f), os.path.join(proj, "fonts"))
    for f in ("nucleo.js", "fim.js"):
        shutil.copy(os.path.join(AQUI, "kit", f), proj)
    for m in modulos:
        shutil.copy(os.path.join(PRESETS, m, f"{m}.js"), proj)
    plano_js = dict(plano_js, camada=nome, modulos=modulos)
    open(os.path.join(proj, "plano.js"), "w").write("window.PLANO = " + json.dumps(plano_js, ensure_ascii=False) + ";\n")
    html = open(os.path.join(AQUI, "kit", "index.html")).read()
    for a, b in (("%W%", w), ("%H%", h), ("%FPS%", fps_txt(fps)), ("%DUR%", round(dur, 3)), ("%CAMADA%", nome),
                 ("%MODULOS%", "\n".join(f'<script src="{m}.js"></script>' for m in modulos))):
        html = html.replace(a, str(b))
    open(os.path.join(proj, "index.html"), "w").write(html)
    return proj


def fps_txt(fps):
    """24.0 -> "24"; 23.976 -> "24000/1001" (o HyperFrames cai para 30 se o data-fps não for inteiro/racional)."""
    for n in (24, 25, 30, 50, 60):
        if abs(fps - n) < .01:
            return str(n)
        if abs(fps - n * 1000 / 1001) < .01:
            return f"{n * 1000}/1001"
    return str(round(fps))


def render(proj, saida, fps):
    subprocess.run(["npx", "--yes", "hyperframes", "render", proj, "--format", "mov", "--fps", fps_txt(fps), "-o", saida], check=True)


# ------------------------------------------------------------ LENTE
def lente_filtro(lente, w, h, rampa=.14):
    zooms = (lente or {}).get("zoom") or []
    if not zooms:
        return None
    z = "1+" + "+".join(f"({x.get('escala', 1.2) - 1:.3f})*clip((t-{x['de']})/{rampa},0,1)*clip(({x['ate']}-t)/{rampa},0,1)"
                        for x in zooms)
    cy = lambda x: x.get("centro_y", .42)   # foco um pouco acima do meio (rosto)
    fy = "+".join(f"({cy(x) - .5:.3f})*clip((t-{x['de']})/{rampa},0,1)*clip(({x['ate']}-t)/{rampa},0,1)" for x in zooms)
    return (f"scale=w='trunc({w}*({z})/2)*2':h='trunc({h}*({z})/2)*2':eval=frame,"
            f"crop={w}:{h}:(in_w-{w})/2:'max(0,min(in_h-{h},(in_h-{h})/2+({fy})*in_h))'")


def luz_fundo(video, t, y0, y1, w, h):
    """Brilho médio (0-255) da faixa onde o texto do PALCO vai ficar, no meio do trecho."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", video, "-frames:v", "1", "-vf",
                        f"scale={w}:{h},crop={w}:{max(2, y1 - y0)}:0:{y0},format=gray", "-f", "rawvideo", "-"],
                       capture_output=True, check=True)
    return sum(r.stdout) / max(1, len(r.stdout))


def gerar(plano, pasta, fazer_render=True):
    os.makedirs(pasta, exist_ok=True); base = os.path.dirname(os.path.abspath(plano["_arq"]))
    absp = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
    video = absp(plano["video"]); w, h, fps, dur = sonda(video)
    comum = {"w": w, "h": h, "dur": dur, "dest": plano.get("dest", "#F2D16B")}
    projs = {}
    if plano.get("palco"):
        itens = [dict({"y": int(h * .17), "tam": 0, "estilo": "sans"}, **a) for a in plano["palco"]]
        for a in itens:   # palavra gigante que cabe em ~92% da largura
            if not a["tam"]:
                a["tam"] = int(min(w * .92 / max(1, len(a["texto"])) / (.62 if a["estilo"] == "sans" else .5), h * .2))
            if not a.get("cor"):   # fundo claro (parede branca): texto escuro, senão some
                luz = luz_fundo(video, (a["de"] + a["ate"]) / 2, a["y"], min(h, a["y"] + a["tam"]), w, h)
                a["cor"] = "#141414" if luz > 150 else "#ffffff"
                print(f"  palco '{a['texto']}': fundo {luz:.0f}/255 -> {a['cor']}")
        projs["palco"] = camada("palco", ["palco"], dict(comum, palco=itens), pasta, w, h, fps, dur)
    frente, mods = dict(comum), []
    if plano.get("destaque") is not None:
        palavras = json.load(open(absp(plano["palavras"]), encoding="utf-8"))
        frente["destaque"] = destaque(palavras, plano["destaque"], dur); mods.append("destaque")
    if plano.get("orbita"):
        cart = []
        for c in plano["orbita"]:
            c = dict({"x": 60, "y": int(h * .14), "w": int(w * .55)}, **c)
            if c["tipo"] == "checklist":
                c["itens"] = [{"t": t, "em": em} for t, em in c["itens"]]
            cart.append(c)
        frente["orbita"] = cart; mods.append("orbita")
    if mods:
        projs["frente"] = camada("frente", mods, frente, pasta, w, h, fps, dur)
    print("camadas:", ", ".join(f"{k} ({'+'.join(['palco'] if k == 'palco' else mods)})" for k in projs) or "nenhuma")
    if not fazer_render:
        return pasta
    for nome, proj in projs.items():
        render(proj, os.path.join(pasta, f"{nome}.mov"), fps)
    lf = lente_filtro(plano.get("lente"), w, h)
    rec = None
    if "palco" in projs:
        rec = absp(plano["recorte"]) if plano.get("recorte") else os.path.join(pasta, "recorte.mov")
        if not os.path.exists(rec):
            subprocess.run([sys.executable, os.path.join(AQUI, "recorte.py"), video, rec, "--w", str(w)], check=True)
    # montagem: base(+lente) -> palco -> recorte(+lente) -> frente
    ent = ["-i", video]; fc = [f"[0:v]{lf or 'null'}[v0]"]; ult = "v0"; n = 1
    for arq, lent in ((os.path.join(pasta, "palco.mov") if "palco" in projs else None, False), (rec, True),
                      (os.path.join(pasta, "frente.mov") if "frente" in projs else None, False)):
        if not arq:
            continue
        ent += ["-i", arq]
        src = f"[{n}:v]"
        if lent and lf:
            fc.append(f"{src}format=yuva444p10le,{lf}[l{n}]"); src = f"[l{n}]"
        fc.append(f"[{ult}]{src}overlay=0:0:format=auto[v{n}]"); ult = f"v{n}"; n += 1
    fc.append(f"[{ult}]format=yuv420p[vout]")
    out = os.path.join(pasta, "previa.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + ent + ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "0:a?",
                    "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-t", str(dur), out], check=True)
    if lf:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", lf, "-c:v", "libx264", "-crf", "16", "-c:a", "copy",
                        os.path.join(pasta, "base.mp4")], check=True)
        if rec:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", rec, "-vf", f"format=yuva444p10le,{lf}", "-c:v", "prores_ks",
                            "-profile:v", "4444", "-pix_fmt", "yuva444p10le", os.path.join(pasta, "recorte_lente.mov")], check=True)
    print("prévia:", out)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    p = json.load(open(a[0], encoding="utf-8")); p["_arq"] = os.path.abspath(a[0])
    gerar(p, os.path.abspath(a[1]), "--sem-render" not in a)
