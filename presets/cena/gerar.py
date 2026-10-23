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
  "lente":    {"zoom": [{"de": 11.0, "ate": 13.4, "escala": 1.25}]},
  "estilos":  [{"id": "titulo-atras", "de": 0.2, "ate": 3.0, "titulo": "GAB"}] }   # presets/estilos/LEIA.md
palavras.json: [{"w": "Olá", "ini": 0.0, "fim": 0.3}, ...] (transcrição com tempo por palavra).
Ênfase "marca": o grupo inteiro vira PÍLULA branca e a palavra ganha marca-texto.
"""
import glob, json, os, re, shutil, subprocess, sys, unicodedata

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
        return {"ini": round(ini, 3), "fim": round(fim, 3), "y": round(y0 - max(0, alto - 62) * .5), "alto": alto, "linhas": linhas,
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
def camada(nome, modulos, plano_js, pasta, w, h, fps, dur, extras=()):
    proj = os.path.join(pasta, f"proj_{nome}"); os.makedirs(os.path.join(proj, "fonts"), exist_ok=True)
    for fam, f in FONTES:
        shutil.copy(os.path.join(RAIZ, "assets", "fontes", fam, f), os.path.join(proj, "fonts"))
    for f in ("nucleo.js", "fim.js"):
        shutil.copy(os.path.join(AQUI, "kit", f), proj)
    for m in modulos:
        shutil.copy(os.path.join(PRESETS, m, f"{m}.js"), proj)
    for c in plano_js.get("estilos") or []:   # imagens/logos dos campos dos estilos
        for orig, nome in c.get("_copiar", []):
            os.makedirs(os.path.join(proj, "img"), exist_ok=True); shutil.copy(orig, os.path.join(proj, "img", nome))
    for x in extras:   # módulos dos ESTILOS (presets/estilos/<grupo>/<id>/<id>.js), carregados antes do despachante
        shutil.copy(x, proj)
    for c in plano_js.get("orbita") or []:
        for k in c.get("cartoes", []):
            if k.get("_orig"):
                os.makedirs(os.path.join(proj, "img"), exist_ok=True); shutil.copy(k["_orig"], os.path.join(proj, k["img"]))
    plano_js = dict(plano_js, camada=nome, modulos=modulos)
    open(os.path.join(proj, "plano.js"), "w").write("window.PLANO = " + json.dumps(plano_js, ensure_ascii=False) + ";\n")
    html = open(os.path.join(AQUI, "kit", "index.html")).read()
    for a, b in (("%W%", w), ("%H%", h), ("%FPS%", fps_txt(fps)), ("%DUR%", round(dur, 3)), ("%CAMADA%", nome),
                 ("%MODULOS%", "\n".join([f'<script src="{m}.js"></script>' for m in modulos]   # despachante dos estilos antes
                                       + [f'<script src="{os.path.basename(x)}"></script>' for x in extras]))):
        html = html.replace(a, str(b))
    open(os.path.join(proj, "index.html"), "w").write(html)
    return proj


def estilos_do_plano(itens, absp=lambda p: p):
    """Separa os ESTILOS do plano por camada lendo presets/estilos/<grupo>/<id>/estilo.json.
    Devolve (frente, atras, arquivos_js, precisa_rosto)."""
    idx = {}
    for j in glob.glob(os.path.join(PRESETS, "estilos", "*", "*", "estilo.json")):
        m = json.load(open(j, encoding="utf-8")); m["_js"] = os.path.join(os.path.dirname(j), m["id"] + ".js"); idx[m["id"]] = m
    frente, atras, js, rosto = [], [], [], False
    for it in itens or []:
        m = idx.get(it["id"])
        if not m:
            raise SystemExit(f"estilo desconhecido: {it['id']} (ver presets/estilos/LEIA.md)")
        it = dict({k: v["exemplo"] for k, v in (m.get("campos") or {}).items() if isinstance(v, dict) and "exemplo" in v}, **it)
        it["_precisa"] = m.get("precisa") or []
        for k, c in (m.get("campos") or {}).items():   # imagens/logos do estilo vão para img/ do projeto
            if not isinstance(c, dict) or c.get("tipo") not in ("imagem", "imagens", "logo") or not it.get(k):
                continue
            def traz(v):
                if not isinstance(v, str) or re.match(r"^(https?:|data:|img/)", v) or not os.path.exists(absp(v)):
                    return v
                nome = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(v))
                it.setdefault("_copiar", []).append((absp(v), nome)); return "img/" + nome
            it[k] = [traz(v) for v in it[k]] if isinstance(it[k], list) else traz(it[k])
        (atras if it.get("camada", m.get("camada", "frente")) == "atras" else frente).append(it)
        if m["_js"] not in js:
            js.append(m["_js"])
        rosto = rosto or "rosto" in (m.get("precisa") or [])
    return frente, atras, js, rosto


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


def rosto_lente(c, t, lente, w, h, rampa=.14):
    """Caixa do rosto depois do zoom da LENTE no tempo t (mesma conta do lente_filtro)."""
    if not c:
        return c
    z, fy = 1.0, 0.0
    for x in (lente or {}).get("zoom") or []:
        k = max(0, min(1, (t - x["de"]) / rampa)) * max(0, min(1, (x["ate"] - t) / rampa))
        z += (x.get("escala", 1.2) - 1) * k; fy += (x.get("centro_y", .42) - .5) * k
    ih = h * z; oy = max(0, min(ih - h, (ih - h) / 2 + fy * ih)); ox = (w * z - w) / 2
    return (c[0] * z - ox, c[1] * z - oy, c[2] * z - ox, c[3] * z - oy)


def caixas_rosto(plano, video, w, h, dur):
    """Rosto por quadro: detectado (rosto.py) ou fixo no plano ("rosto": [x0, y0, x1, y1], ex.: apresentador ilustrado)."""
    if plano.get("rosto"):
        return {round(i * .5, 3): tuple(plano["rosto"]) for i in range(int(dur * 2) + 2)}
    from rosto import rostos
    return rostos(video, w, h, dur)


def proteger_rosto(cx, w, h, lente, legenda, cartoes):
    """REGRA DO GAB: texto e animação nunca na frente do rosto. Legenda que bate no rosto desce; cartão que bate vai
    para TRÁS da pessoa (camada palco, com o recorte por cima); sem espaço embaixo, avisa para reenquadrar."""
    from rosto import no_trecho, bate
    if not cx:
        print("  rosto: nenhum rosto detectado, posições mantidas"); return [], []
    rost = lambda de, ate: no_trecho({t: rosto_lente(c, t, lente, w, h) for t, c in cx.items()}, de, ate)
    avisos, atras = [], []
    for g in legenda or []:
        r = rost(g["ini"], g["fim"])
        if bate((60, g["y"], w - 60, g["y"] + g["alto"]), r):
            novo = int(r[3] + 40)
            if novo + g["alto"] > h * .9:
                avisos.append(f"legenda {g['ini']:.1f}s: sem espaço abaixo do rosto, reenquadre (afaste/baixe a pessoa)")
                novo = int(h * .9 - g["alto"])
            g["y"] = novo
    fica = []
    for c in cartoes or []:
        alto = {"checklist": 110 + 72 * len(c.get("itens", [])), "progresso": 230, "cta": 112}.get(c["tipo"], 300)
        caixa = (70, c["y"], w - 70, c["y"] + alto) if c["tipo"] == "cta" else (c["x"], c["y"], c["x"] + c["w"], c["y"] + alto)
        r = rost(c["de"], c["ate"])
        if not bate(caixa, r):
            fica.append(c); continue
        if c["tipo"] == "cta" and r[3] + 120 + alto < h * .92:   # CTA desce em vez de ir para trás
            c["y"] = int(r[3] + 120); fica.append(c); continue
        atras.append(c); print(f"  rosto: {c['tipo']} {c['de']:.1f}s bateria no rosto -> vai para trás da pessoa")
    cartoes[:] = fica
    for a in avisos:
        print("  AVISO", a)
    return atras, avisos


def preparar_giros(giros, cx, w, h, lente, absp):
    """Cartões girando: elipse em volta da pessoa com a passagem da FRENTE abaixo do queixo (regra do rosto)."""
    from rosto import no_trecho
    for c in giros:
        c.setdefault("voltas", 1); c.setdefault("fase", 0.6)
        c.setdefault("cw", int(w * .30)); c.setdefault("ch", int(c["cw"] * (16 / 9 if any(k.get("img") for k in c["cartoes"]) else .62)))
        c.setdefault("rx", int(w * .38)); c.setdefault("cx", w // 2)
        r = no_trecho({t: rosto_lente(b, t, lente, w, h) for t, b in cx.items()}, c["de"], c["ate"]) if cx else None
        # volta inclinada: atrás passa na altura do rosto (some atrás da cabeça), na frente passa abaixo do queixo
        tras = (r[1] + r[3]) / 2 if r else h * .3
        frente_y = (r[3] if r else h * .45) + 40 + c["ch"] / 2
        c.setdefault("cy", int((tras + frente_y) / 2)); c.setdefault("ry", int((frente_y - tras) / 2))
        c["_base"] = int(c["cy"] + c["ry"] + c["ch"] / 2)   # embaixo do cartão da frente (a legenda desce para cá)
        for k in c["cartoes"]:
            if k.get("img"):
                orig = absp(k["img"]); nome = "giro_" + os.path.basename(orig)
                k["_orig"] = orig; k["img"] = "img/" + nome
        print(f"  giro {c['de']:.1f}s: {len(c['cartoes'])} cartões, atrás y {c['cy'] - c['ry']}, frente y {c['cy'] + c['ry']}")


def gerar(plano, pasta, fazer_render=True):
    os.makedirs(pasta, exist_ok=True); base = os.path.dirname(os.path.abspath(plano["_arq"]))
    absp = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
    video = absp(plano["video"]); w, h, fps, dur = sonda(video)
    comum = {"w": w, "h": h, "dur": dur, "dest": plano.get("dest", "#F2D16B")}
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
    _cx = {}
    def rosto_cx():
        if "v" not in _cx:
            _cx["v"] = caixas_rosto(plano, video, w, h, dur)
        return _cx["v"]
    giros = [c for c in frente.get("orbita", []) if c["tipo"] == "giro"]
    if giros:
        frente["orbita"] = [c for c in frente["orbita"] if c["tipo"] != "giro"]
        preparar_giros(giros, rosto_cx(), w, h, plano.get("lente"), absp)
    for c in giros:   # legenda desce para baixo dos cartões da frente durante o giro
        for g in frente.get("destaque") or []:
            if g["ini"] < c["ate"] and g["fim"] > c["de"] and g["y"] < c["_base"] + 30:
                g["y"] = int(min(c["_base"] + 30, h * .9 - g["alto"]))
    est_frente, est_atras, est_js, est_rosto = estilos_do_plano(plano.get("estilos"), absp)
    if any("palavras" in (x.get("_precisa") or []) for x in est_frente + est_atras) and plano.get("palavras"):
        comum["palavras"] = frente["palavras"] = json.load(open(absp(plano["palavras"]), encoding="utf-8"))   # legenda e batidas na fala
    if est_rosto or est_atras:   # estilos que fogem do rosto recebem a caixa dele a cada 0,5 s
        comum["rostos"] = [[t_, *map(int, b)] for t_, b in sorted(rosto_cx().items()) if b]
        frente["rostos"] = comum["rostos"]
    if est_frente:
        frente["estilos"] = est_frente; mods.append("estilos")
    atras_cart = []
    if plano.get("proteger_rosto", True) and (frente.get("destaque") or frente.get("orbita")):   # estilos fogem do rosto sozinhos
        atras_cart, _ = proteger_rosto(rosto_cx(), w, h, plano.get("lente"), frente.get("destaque"), frente.get("orbita"))
    projs = {}
    atras_cart = atras_cart + giros
    frente.setdefault("orbita", []).extend(giros)
    if giros and "orbita" not in mods:
        mods.append("orbita")
    if plano.get("palco") or atras_cart or est_atras:
        itens = [dict({"y": int(h * .17), "tam": 0, "estilo": "sans"}, **a) for a in plano.get("palco", [])]
        for a in itens:   # palavra gigante que cabe em ~92% da largura
            if not a["tam"]:
                a["tam"] = int(min(w * .92 / max(1, len(a["texto"])) / (.62 if a["estilo"] == "sans" else .5), h * .2))
            if not a.get("cor"):   # fundo claro (parede branca): texto escuro, senão some
                luz = luz_fundo(video, (a["de"] + a["ate"]) / 2, a["y"], min(h, a["y"] + a["tam"]), w, h)
                a["cor"] = "#141414" if luz > 150 else "#ffffff"
                print(f"  palco '{a['texto']}': fundo {luz:.0f}/255 -> {a['cor']}")
        projs["palco"] = camada("palco", ["palco"] + (["orbita"] if atras_cart else []) + (["estilos"] if est_atras else []),
                                dict(comum, palco=itens, orbita=atras_cart, estilos=est_atras), pasta, w, h, fps, dur,
                                extras=est_js if est_atras else ())
    if mods:
        projs["frente"] = camada("frente", mods, frente, pasta, w, h, fps, dur, extras=est_js if est_frente else ())
    print("camadas:", ", ".join(projs) or "nenhuma")
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
