"""B-roll de material real: reportagem, cena histórica/pública citada na fala (ex.: 11 de setembro), discurso,
evento, acervo de domínio público, perfil do TikTok e print de site/notícia.

Fluxo: buscar > achar o trecho > folha de quadros (olhar antes) > baixar.

  python3 baixar_video.py buscar "<termos>" [--n 5] [--fonte youtube|commons|nasa|archive|met|aic] [--tipo video|imagem]
                                  [--previa folha.jpg]
        -> lista título, canal/autor, duração, licença e link. Não baixa nada. Acervos livres, sem chave, a rota
           mais segura em direitos (serve para anúncio pago):
             commons = Wikimedia Commons (vídeo e foto, conferir a licença de cada um)
             nasa    = acervo da NASA (vídeo e foto, domínio público)
             archive = Internet Archive, só o que está em domínio público/CC0 ou na coleção Prelinger (filmes
                       antigos, cinejornal, institucional dos anos 1920-70: ótimo para história)
             met     = Metropolitan Museum (pinturas, gravuras, mapas, objetos; só domínio público, CC0)
             aic     = Art Institute of Chicago (obras em domínio público, CC0)
           --previa: grade com a miniatura de cada resultado (archive, met, aic) para escolher olhando.
  python3 baixar_video.py achar <url> "<frase ou assunto>" [--n 3]
        -> lê legendas, capítulos e tempos da descrição do vídeo (sem baixar o vídeo) e devolve as
           janelas onde o assunto aparece, com nota. Escrever a frase no idioma do vídeo.
  python3 baixar_video.py folha <url|arquivo> <saida.jpg> [--de mm:ss --ate mm:ss] [--quadros 12]
  python3 baixar_video.py folha <url|arquivo> <saida.jpg> --varrer
        -> grade de quadros com o tempo de cada um (baixa só uma cópia leve, 360p). ABRIR E OLHAR antes de
           baixar: marca d'água, legenda queimada, cena errada. --varrer cobre o vídeo inteiro (até 15 min),
           para quando o `achar` não tiver pista.
  python3 baixar_video.py baixar <url> <pasta_brolls> <nome> [--de 12.5 --ate 18] [--max 1080] [--com-audio]
        -> baixa só o trecho (ou tudo sem --de/--ate) em MP4 H.264, sem áudio por padrão, e anota a origem
           em <pasta do vídeo>/links.txt. Aceita YouTube, TikTok, Instagram etc. (yt-dlp) e também link
           de arquivo do Commons (commons.wikimedia.org/wiki/File:...), da NASA (images.nasa.gov/details/...), do
           Internet Archive (archive.org/details/...), do Met e do Art Institute (link da obra):
           foto sai como imagem, vídeo é cortado e convertido.
  python3 baixar_video.py tiktok @usuario [--n 12]
        -> lista os posts recentes de um perfil do TikTok sem login (página de incorporação).
  python3 baixar_video.py print <url> <saida.png> [--vertical] [--largura 1440 --altura 900]
        -> print da página (manchete, site, painel) pelo Chrome sem janela. Página que pede login ou
           cookie: tirar o print pelo Claude in Chrome.

Precisa do yt-dlp e do ffmpeg (install.sh instala os dois). Tempos em segundos ou mm:ss.
"""
import datetime, glob, json, math, os, re, shutil, subprocess, sys, tempfile, unicodedata
import urllib.parse, urllib.request

UA = "ogab-broll/1.0 (editor de video; uso pessoal)"
HDR = {"User-Agent": UA, "AIC-User-Agent": UA}   # o Art Institute recusa imagem sem o AIC-User-Agent


def _seg(x):
    if x is None:
        return None
    if ":" in str(x):
        p = [float(v) for v in str(x).split(":")]
        return sum(v * 60 ** i for i, v in enumerate(reversed(p)))
    return float(x)


def _mmss(s):
    s = max(0, int(round(s or 0)))
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def _ytdlp():
    exe = shutil.which("yt-dlp")
    if not exe:
        raise SystemExit("yt-dlp não encontrado: brew install yt-dlp (ou rode o install.sh)")
    return exe


def _get(url, as_json=True):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=60) as r:
        dado = r.read()
    return json.loads(dado) if as_json else dado.decode("utf-8", "replace")


def _sem_html(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t or "")).strip()


# ---------------------------------------------------------------- buscar

def buscar(termos, n=5, fonte="youtube", tipo="video"):
    if fonte == "commons":
        res = _buscar_commons(termos, n, tipo)
    elif fonte == "nasa":
        res = _buscar_nasa(termos, n, tipo)
    elif fonte == "archive":
        res = _buscar_archive(termos, n)
    elif fonte == "met":
        res = _buscar_met(termos, n)
    elif fonte == "aic":
        res = _buscar_aic(termos, n)
    else:
        out = subprocess.run([_ytdlp(), f"ytsearch{n}:{termos}", "--flat-playlist", "-j", "--no-warnings"],
                             capture_output=True, text=True, timeout=120).stdout
        res = []
        for linha in out.splitlines():
            d = json.loads(linha)
            res.append({"titulo": d.get("title"), "canal": d.get("channel") or d.get("uploader"),
                        "duracao": _mmss(d.get("duration")), "licenca": "",
                        "url": d.get("url") or f"https://www.youtube.com/watch?v={d.get('id')}"})
    for k, r in enumerate(res, 1):
        extra = f"  [{r['licenca']}]" if r.get("licenca") else ""
        print(f"{k:>2}. {r['duracao']:>7}  {r['canal']}  |  {r['titulo']}{extra}\n         {r['url']}")
    if not res:
        print("nada encontrado (tente termos em inglês: os acervos são quase todos em inglês)")
    return res


def _buscar_commons(termos, n, tipo):
    filtro = "filetype:video" if tipo == "video" else "filetype:bitmap"
    q = urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
                                "gsrsearch": f"{termos} {filtro}", "gsrlimit": n, "prop": "imageinfo",
                                "iiprop": "url|size|mime|extmetadata"})
    d = _get("https://commons.wikimedia.org/w/api.php?" + q)
    paginas = sorted((d.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    res = []
    for p in paginas:
        ii = (p.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata") or {}
        dur = ii.get("duration")
        res.append({"titulo": p["title"].replace("File:", ""),
                    "canal": _sem_html((meta.get("Artist") or {}).get("value"))[:60] or "?",
                    "duracao": _mmss(dur) if dur else f"{ii.get('width')}x{ii.get('height')}",
                    "licenca": (meta.get("LicenseShortName") or {}).get("value", "?"),
                    "url": ii.get("descriptionurl") or "https://commons.wikimedia.org/wiki/" + p["title"].replace(" ", "_")})
    return res


def _buscar_archive(termos, n):
    """Internet Archive: filmes em domínio público/CC0 ou da coleção Prelinger (cinejornal, institucional antigo)."""
    q = urllib.parse.urlencode({"q": f"({termos}) AND mediatype:movies AND (licenseurl:*publicdomain* OR collection:prelinger)",
                                "fl[]": ["identifier", "title", "licenseurl", "creator", "runtime", "year"],
                                "rows": n, "output": "json", "sort[]": "downloads desc"}, doseq=True)
    docs = _get("https://archive.org/advancedsearch.php?" + q)["response"]["docs"]
    lic = lambda d: "domínio público" if "publicdomain" in str(d.get("licenseurl", "")) else (d.get("licenseurl") or "Prelinger (domínio público)")
    return [{"titulo": d.get("title"), "canal": str(d.get("creator") or d.get("year") or "?")[:60],
             "duracao": d.get("runtime") or str(d.get("year") or ""), "licenca": lic(d),
             "thumb": f"https://archive.org/services/img/{d['identifier']}",
             "url": f"https://archive.org/details/{d['identifier']}"} for d in docs]


def _buscar_met(termos, n):
    """Metropolitan Museum: só obras em domínio público (Open Access, CC0)."""
    q = urllib.parse.urlencode({"q": termos, "hasImages": "true", "isPublicDomain": "true", "limit": n * 2})
    ids = (_get("https://collectionapi.metmuseum.org/public/collection/v1.1/search?" + q).get("objectIDs") or [])[:n * 2]
    res = []
    for i in ids:
        o = _get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{i}")
        if not (o.get("isPublicDomain") and o.get("primaryImage")):
            continue
        res.append({"titulo": o.get("title"), "canal": (o.get("artistDisplayName") or o.get("culture") or "The Met")[:60],
                    "duracao": o.get("objectDate") or "", "licenca": "CC0 (Met Open Access)",
                    "thumb": o.get("primaryImageSmall"), "url": o.get("objectURL") or f"https://www.metmuseum.org/art/collection/search/{i}"})
        if len(res) >= n:
            break
    return res


def _buscar_aic(termos, n):
    """Art Institute of Chicago: só obras em domínio público (CC0)."""
    q = urllib.parse.urlencode({"q": termos, "query[term][is_public_domain]": "true", "limit": n,
                                "fields": "id,title,artist_display,date_display,image_id"})
    d = _get("https://api.artic.edu/api/v1/artworks/search?" + q)
    return [{"titulo": o.get("title"), "canal": (o.get("artist_display") or "?").split("\n")[0][:60],
             "duracao": o.get("date_display") or "", "licenca": "CC0 (Art Institute of Chicago)",
             "thumb": f"https://www.artic.edu/iiif/2/{o['image_id']}/full/400,/0/default.jpg",
             "url": f"https://www.artic.edu/artworks/{o['id']}"} for o in d.get("data", []) if o.get("image_id")]


def previa(res, saida):
    """Grade com a miniatura de cada resultado, numerada na ordem da lista."""
    from PIL import Image, ImageDraw
    ims = []
    for r in res:
        try:
            req = urllib.request.Request(r["thumb"], headers=HDR)
            with urllib.request.urlopen(req, timeout=30) as f:
                im = Image.open(__import__("io").BytesIO(f.read())).convert("RGB")
            im.thumbnail((360, 360)); ims.append(im)
        except Exception:
            ims.append(Image.new("RGB", (360, 360), (40, 40, 40)))
    if not ims:
        return
    col = min(4, len(ims)); lin = (len(ims) + col - 1) // col
    g = Image.new("RGB", (col * 370, lin * 370), (18, 18, 20)); d = ImageDraw.Draw(g)
    for k, im in enumerate(ims):
        x, y = (k % col) * 370 + 5, (k // col) * 370 + 5
        g.paste(im, (x + (360 - im.width) // 2, y + (360 - im.height) // 2))
        d.rectangle((x, y, x + 34, y + 30), fill=(0, 0, 0)); d.text((x + 9, y + 8), str(k + 1), fill=(255, 255, 255))
    g.save(saida, quality=88)
    print(f"prévia: {saida}")


def _buscar_nasa(termos, n, tipo):
    q = urllib.parse.urlencode({"q": termos, "media_type": "video" if tipo == "video" else "image"})
    itens = (_get("https://images-api.nasa.gov/search?" + q).get("collection") or {}).get("items", [])[:n]
    res = []
    for it in itens:
        dd = (it.get("data") or [{}])[0]
        res.append({"titulo": dd.get("title"), "canal": dd.get("center") or "NASA",
                    "duracao": (dd.get("date_created") or "")[:10], "licenca": "NASA, domínio público",
                    "url": "https://images.nasa.gov/details/" + urllib.parse.quote(dd.get("nasa_id", ""))})
    return res


# ---------------------------------------------------------------- achar o trecho

_VAZIAS = set("""a o as os um uma uns umas de da do das dos e em no na nos nas por para pra com sem que se ao aos
 the a an of and or to in on at for with by from is are was were be it this that as he she they we you i""".split())


def _chave(t):
    t = unicodedata.normalize("NFD", (t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _termos(t):
    return [w for w in re.findall(r"[a-z0-9]+", _chave(t)) if w not in _VAZIAS and len(w) > 1]


def _nota(frase, texto):
    """0..1: quanto dos termos da frase aparece no texto (prefixo de 5 letras pega plural/conjugação),
    com bônus se a frase inteira aparece em sequência."""
    alvo = _termos(frase)
    if not alvo:
        return 0.0
    tem = set(_termos(texto))
    raizes = {w[:5] for w in tem}
    acerto = sum(1 for w in alvo if w in tem or (len(w) >= 5 and w[:5] in raizes))
    nota = acerto / len(alvo)
    if " ".join(alvo) in " ".join(_termos(texto)):
        nota += 0.5
    return round(min(nota, 1.5), 2)


def _tempo_vtt(s):
    p = s.replace(",", ".").split(":")
    return sum(float(v) * 60 ** i for i, v in enumerate(reversed(p)))


def ler_vtt(caminho):
    """Falas [(ini, fim, texto)]. A legenda automática do YouTube repete a linha anterior em cada bloco
    novo (efeito de rolagem): guarda só o pedaço novo de cada bloco."""
    falas, ultimo = [], ""
    blocos = re.split(r"\n\s*\n", open(caminho, encoding="utf-8", errors="replace").read().replace("\r", ""))
    for b in blocos:
        linhas = b.strip().split("\n")
        idx = next((i for i, l in enumerate(linhas) if "-->" in l), None)
        if idx is None:
            continue
        m = re.match(r"\s*([\d:.,]+)\s*-->\s*([\d:.,]+)", linhas[idx])
        if not m:
            continue
        texto = " ".join(_sem_html(l) for l in linhas[idx + 1:] if _sem_html(l))
        if not texto:
            continue
        if ultimo and texto.startswith(ultimo):
            texto = texto[len(ultimo):].strip()
        elif ultimo and texto == ultimo:
            continue
        for linha in [_sem_html(l) for l in linhas[idx + 1:] if _sem_html(l)][-1:]:
            ultimo = linha
        if texto:
            falas.append((_tempo_vtt(m.group(1)), _tempo_vtt(m.group(2)), texto))
    return falas


def _janelas_legenda(falas, teto=10.0, folga=1.5):
    """Junta falas vizinhas em janelas de até `teto` s (cortes de 2-6 s cabem com margem)."""
    jan, atual = [], None
    for ini, fim, txt in falas:
        if atual and ini - atual[1] <= folga and fim - atual[0] <= teto:
            atual = [atual[0], fim, atual[2] + " " + txt]
        else:
            if atual:
                jan.append(tuple(atual))
            atual = [ini, fim, txt]
    if atual:
        jan.append(tuple(atual))
    return jan


def _tempos_descricao(desc, dur):
    marcas = []
    for linha in (desc or "").splitlines():
        m = re.match(r"\s*[\[(]?((?:\d{1,2}:)?\d{1,2}:\d{2})[\])]?\s*[-–:|.]?\s*(.+)", linha)
        if m:
            marcas.append((_tempo_vtt(m.group(1)), m.group(2).strip()))
    marcas.sort()
    return [(t, (marcas[i + 1][0] if i + 1 < len(marcas) else (dur or t + 12)), txt)
            for i, (t, txt) in enumerate(marcas)]


def achar(url, frase, n=3):
    tmp = tempfile.mkdtemp(prefix="ogab_achar_")
    try:
        info = json.loads(subprocess.run([_ytdlp(), url, "-J", "--no-warnings", "--no-playlist"],
                                         capture_output=True, text=True, timeout=180).stdout or "{}")
        if not info:
            raise SystemExit("não consegui ler o vídeo (privado/bloqueado? brew upgrade yt-dlp)")
        dur = info.get("duration") or 0
        idioma = (info.get("language") or "").split("-")[0]
        langs = ",".join(x for x in dict.fromkeys([idioma, "pt", "en", "es"]) if x)
        subprocess.run([_ytdlp(), url, "--skip-download", "--no-playlist", "--no-warnings", "--write-subs",
                        "--write-auto-subs", "--sub-langs", langs, "--sub-format", "vtt",
                        "-o", os.path.join(tmp, "s.%(ext)s")], capture_output=True, timeout=180)
        vtts = sorted(glob.glob(os.path.join(tmp, "*.vtt")),
                      key=lambda p: (f".{idioma}" not in p, ".orig" in p))   # idioma do vídeo primeiro
        janelas = []
        if vtts:
            janelas += [(a, b, t, "legenda " + os.path.basename(vtts[0]).split(".")[1])
                        for a, b, t in _janelas_legenda(ler_vtt(vtts[0]))]
        caps = info.get("chapters") or []
        janelas += [(c["start_time"], c.get("end_time") or c["start_time"] + 12, c.get("title", ""), "capítulo") for c in caps]
        janelas += [(a, b, t, "descrição") for a, b, t in _tempos_descricao(info.get("description"), dur)]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"{info.get('title')}  |  {info.get('channel') or info.get('uploader')}  |  {_mmss(dur)}")
    print(f"pistas: {'legenda' if vtts else 'SEM legenda'}, {len(caps)} capítulos, "
          f"{sum(1 for j in janelas if j[3] == 'descrição')} tempos na descrição")
    notas = sorted(((_nota(frase, j[2]), j) for j in janelas), key=lambda x: -x[0])
    boas = [x for x in notas if x[0] > 0][:n]
    if not boas:
        passo = (dur or 60) / (n + 1)
        print(f"nenhuma janela casa com {frase!r}. Pontos de partida espaçados (confirmar na folha, "
              f"ou usar `folha --varrer`):")
        for k in range(1, n + 1):
            print(f"  {_mmss(passo * k)} - {_mmss(passo * k + 10)}")
        if idioma and idioma != "pt":
            print(f"  (o vídeo está em '{idioma}': escreva a frase nesse idioma)")
        return []
    for nota, (a, b, txt, origem) in boas:
        print(f"  nota {nota:.2f}  {_mmss(a)} - {_mmss(b)}  [{origem}]  {txt[:140]}")
    print("próximo: folha com --de/--ate de uma janela, olhar os quadros e só então baixar")
    return [{"nota": nt, "de": a, "ate": b, "texto": t, "origem": o} for nt, (a, b, t, o) in boas]


# ---------------------------------------------------------------- folha de quadros

def _duracao(arq):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", arq],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def folha(origem, saida, de=None, ate=None, quadros=12, varrer=False):
    from PIL import Image, ImageDraw, ImageFont
    de, ate = _seg(de), _seg(ate)
    tmp = tempfile.mkdtemp(prefix="ogab_folha_")
    try:
        deslocamento = 0.0
        if os.path.exists(origem):
            arq = origem
            if varrer:
                de = ate = None
        else:
            cmd = [_ytdlp(), origem, "--no-playlist", "--no-warnings", "-f",
                   "bv*[height<=360]/b[height<=360]/wv*/w", "-o", os.path.join(tmp, "v.%(ext)s")]
            if varrer:
                de, ate = None, None
                cmd += ["--download-sections", "*0-900"]
            elif de is not None or ate is not None:
                cmd += ["--download-sections", f"*{de or 0}-{ate if ate is not None else 'inf'}",
                        "--force-keyframes-at-cuts"]   # sem isso o corte cai no keyframe e o rótulo atrasa
                deslocamento = de or 0
            for tentativa in range(3):   # o YouTube às vezes recusa de primeira
                r = subprocess.run(cmd + ["--retries", "5"], capture_output=True, text=True)
                if r.returncode == 0:
                    break
            else:
                raise SystemExit("yt-dlp falhou ao baixar a cópia leve (brew upgrade yt-dlp):\n" + r.stderr[-400:])
            arq = next(p for p in glob.glob(os.path.join(tmp, "v.*")) if not p.endswith(".part"))
            de = ate = None   # a cópia leve já é só o trecho; o rótulo soma o deslocamento
        total = _duracao(arq)
        ini = de or 0.0
        fim = min(ate, total) if ate else total
        if fim <= ini:
            raise SystemExit("intervalo vazio")
        q = max(4, min(int(quadros), 24))
        tempos = [ini + (fim - ini) * (k + 0.5) / q for k in range(q)]
        fotos = []
        for k, t in enumerate(tempos):
            p = os.path.join(tmp, f"q{k:02d}.jpg")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", arq, "-frames:v", "1",
                            "-vf", "scale=360:-2", p])
            if os.path.exists(p):
                fotos.append((t + deslocamento, Image.open(p).convert("RGB")))
        if not fotos:
            raise SystemExit("não consegui tirar quadros do vídeo")
        w, h = fotos[0][1].size
        cols = 4 if w >= h else 6
        lins = math.ceil(len(fotos) / cols)
        grade = Image.new("RGB", (cols * w, lins * h), "black")
        try:
            fonte = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", max(14, h // 12))
        except OSError:
            fonte = ImageFont.load_default()
        d = ImageDraw.Draw(grade)
        for k, (t, img) in enumerate(fotos):
            x, y = (k % cols) * w, (k // cols) * h
            grade.paste(img.resize((w, h)), (x, y))
            rot = _mmss(t) + f".{int((t % 1) * 10)}"
            d.rectangle([x, y, x + fonte.getlength(rot) + 12, y + fonte.size + 8], fill="black")
            d.text((x + 6, y + 3), rot, fill="yellow", font=fonte)
        os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
        grade.save(saida, quality=85)
        print(f"ok: {saida}  ({len(fotos)} quadros, {_mmss(fotos[0][0])} a {_mmss(fotos[-1][0])})")
        if varrer and total >= 899:
            print("  aviso: varri só os primeiros 15 min")
        return saida
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------- baixar

def _acervo(url):
    """Commons/NASA: (link direto do arquivo, título, autor, licença) ou None."""
    m = re.search(r"commons\.wikimedia\.org/wiki/(File:[^?#]+)", url)
    if m:
        titulo = urllib.parse.unquote(m.group(1)).replace("_", " ")
        q = urllib.parse.urlencode({"action": "query", "format": "json", "titles": titulo, "prop": "imageinfo",
                                    "iiprop": "url|extmetadata"})
        p = next(iter(_get("https://commons.wikimedia.org/w/api.php?" + q)["query"]["pages"].values()))
        ii = p["imageinfo"][0]; meta = ii.get("extmetadata") or {}
        return (ii["url"], titulo.replace("File:", ""), _sem_html((meta.get("Artist") or {}).get("value"))[:80],
                (meta.get("LicenseShortName") or {}).get("value", "?"))
    m = re.search(r"images\.nasa\.gov/details/?([^?#/]+)", url)
    if m:
        nid = urllib.parse.unquote(m.group(1))
        hrefs = [i["href"] for i in _get("https://images-api.nasa.gov/asset/" + urllib.parse.quote(nid))["collection"]["items"]]
        pref = ["~orig.mp4", "~large.mp4", "~medium.mp4", "~orig.jpg", "~orig.png", "~large.jpg"]
        href = next((h for s in pref for h in hrefs if h.endswith(s)), hrefs[0])
        return href.replace("http://", "https://").replace(" ", "%20"), nid, "NASA", "NASA, domínio público"
    m = re.search(r"archive\.org/details/([^?#/]+)", url)
    if m:
        ident = m.group(1); md = _get(f"https://archive.org/metadata/{ident}")
        vids = [f for f in md.get("files", []) if f.get("name", "").lower().endswith((".mp4", ".m4v", ".mpeg", ".mpg", ".ogv"))]
        if not vids:
            raise SystemExit(f"{ident}: nenhum arquivo de vídeo no item")
        # maior resolução; empate: H.264 (.mp4) antes de MPEG2/Ogg, e o arquivo menor (o servidor do Archive é lento)
        alt = lambda f: int(float(f.get("height") or 0))
        ordem = lambda f: (alt(f), f["name"].lower().endswith(".mp4"), -int(f.get("size") or 0))
        f = max(vids, key=ordem); meta = md.get("metadata", {})
        lic = "domínio público" if "publicdomain" in str(meta.get("licenseurl", "")) else (meta.get("licenseurl") or "Prelinger (domínio público)")
        return (f"https://archive.org/download/{ident}/{urllib.parse.quote(f['name'])}", meta.get("title", ident),
                str(meta.get("creator", "?"))[:80], lic)
    m = re.search(r"metmuseum\.org/art/collection/search/(\d+)", url)
    if m:
        o = _get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{m.group(1)}")
        if not o.get("isPublicDomain"):
            raise SystemExit("obra do Met fora do domínio público: não usar")
        return o["primaryImage"], o.get("title", "?"), o.get("artistDisplayName") or "The Met", "CC0 (Met Open Access)"
    m = re.search(r"artic\.edu/artworks/(\d+)", url)
    if m:
        o = _get(f"https://api.artic.edu/api/v1/artworks/{m.group(1)}?fields=id,title,artist_display,image_id,is_public_domain")["data"]
        if not o.get("is_public_domain"):
            raise SystemExit("obra do Art Institute fora do domínio público: não usar")
        return (f"https://www.artic.edu/iiif/2/{o['image_id']}/full/1686,/0/default.jpg", o.get("title", "?"),
                (o.get("artist_display") or "?").split("\n")[0], "CC0 (Art Institute of Chicago)")
    return None


def _anotar(pasta, linha):
    links = os.path.join(os.path.dirname(os.path.abspath(pasta.rstrip("/"))), "links.txt")
    with open(links, "a") as f:
        f.write(f"{datetime.date.today()}  {linha}\n")


def baixar(url, pasta, nome, de=None, ate=None, maxh=1080, com_audio=False):
    os.makedirs(pasta, exist_ok=True)
    de, ate = _seg(de), _seg(ate)
    destino = os.path.join(pasta, nome + ".mp4")
    trecho = f"trecho {de or 0}-{ate if ate is not None else 'fim'} s"
    acervo = _acervo(url)
    if acervo:
        direto, titulo, autor, lic = acervo
        ext = os.path.splitext(urllib.parse.urlparse(direto).path)[1].lower() or ".bin"
        bruto = os.path.join(pasta, f"_tmp_{nome}{ext}")
        with open(bruto, "wb") as f:
            req = urllib.request.Request(direto, headers=HDR)
            with urllib.request.urlopen(req, timeout=600) as r:
                shutil.copyfileobj(r, f)
        if ext in (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"):
            destino = os.path.join(pasta, nome + (".png" if ext in (".png", ".tif", ".tiff", ".webp") else ".jpg"))
            if ext in (".tif", ".tiff", ".webp"):
                from PIL import Image
                Image.open(bruto).convert("RGB").save(destino); os.remove(bruto)
            else:
                os.replace(bruto, destino)
            trecho = "foto"
        else:
            corte = (["-ss", str(de)] if de else []) + (["-to", str(ate)] if ate is not None else [])
            sv = (json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                             "stream=codec_name,pix_fmt,height", "-of", "json", bruto],
                                            capture_output=True, text=True).stdout or "{}").get("streams") or [{}])[0]
            # já em H.264 yuv420p, inteiro e dentro da altura: só copia (recodificar em crf 16 quase dobrava o arquivo)
            copia = (not corte and sv.get("codec_name") == "h264" and sv.get("pix_fmt") == "yuv420p"
                     and int(sv.get("height") or 0) <= maxh)
            enc = ["ffmpeg", "-y", "-loglevel", "error", "-i", bruto] + corte + (["-c:v", "copy"] if copia else [
                "-vf", f"scale=-2:'min({maxh},ih)'", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                "-pix_fmt", "yuv420p"]) + (["-c:a", "aac", "-b:a", "192k"] if com_audio else ["-an"])
            subprocess.run(enc + [destino], check=True)
            os.remove(bruto)
        _anotar(pasta, f"{os.path.basename(destino)}  <-  {titulo} | {autor} | licença: {lic} | {url}  {trecho}")
        print(f"ok: {destino}  (licença: {lic}; autor: {autor})")
        return destino

    tmp = os.path.join(pasta, f"_tmp_{nome}.%(ext)s")
    cmd = [_ytdlp(), url, "--no-playlist", "--no-warnings", "-f",
           f"bv*[height<={maxh}][vcodec^=avc1]+ba/bv*[height<={maxh}]+ba/b[height<={maxh}]/b",
           "--merge-output-format", "mp4", "-o", tmp]
    if de is not None or ate is not None:
        cmd += ["--download-sections", f"*{de or 0}-{ate if ate is not None else 'inf'}", "--force-keyframes-at-cuts"]
    for tentativa in range(3):
        if subprocess.run(cmd + ["--retries", "5"]).returncode == 0:
            break
    else:
        raise SystemExit("yt-dlp falhou 3 vezes (vídeo privado/bloqueado? atualize: brew upgrade yt-dlp)")
    baixado = next(os.path.join(pasta, f) for f in os.listdir(pasta) if f.startswith(f"_tmp_{nome}."))
    # normaliza para o DaVinci: H.264, yuv420p, sem áudio (a não ser que peça). Já em H.264 yuv420p = remux sem
    # re-encode. Download INTEIRO leva a marca "ogab:download-integral" (montar_takes aceita: não é take cortado).
    sv = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,pix_fmt",
                         "-of", "csv=p=0", baixado], capture_output=True, text=True).stdout.strip()
    copia = sv.startswith("h264,yuv420p")
    enc = ["ffmpeg", "-y", "-loglevel", "error", "-i", baixado] + (["-c:v", "copy"] if copia else
          ["-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p"])
    if de is None and ate is None: enc += ["-metadata", "comment=ogab:download-integral"]
    enc += ["-c:a", "aac", "-b:a", "192k"] if com_audio else ["-an"]
    subprocess.run(enc + [destino], check=True)
    os.remove(baixado)
    info = json.loads(subprocess.run([_ytdlp(), url, "-j", "--no-warnings", "--no-playlist"],
                                     capture_output=True, text=True).stdout or "{}")
    _anotar(pasta, f"{nome}.mp4  <-  {info.get('title', '?')} | {info.get('channel') or info.get('uploader', '?')} | "
                   f"{url}  {trecho}")
    print(f"ok: {destino}")
    return destino


# ---------------------------------------------------------------- tiktok e print

def tiktok(usuario, n=12):
    """A grade do perfil não abre sem login; a página de incorporação traz os ids dos posts recentes."""
    u = usuario.lstrip("@").strip("/")
    html = _get(f"https://www.tiktok.com/embed/@{u}", as_json=False)
    ids = list(dict.fromkeys(re.findall(r"\b(7\d{17,19})\b", html)))[:n]
    if not ids:
        print("não achei posts (perfil privado, nome errado ou o TikTok mudou a página): abrir pelo Claude in Chrome")
    for i in ids:
        print(f"https://www.tiktok.com/@{u}/video/{i}")
    return ids


def _chrome():
    for p in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]:
        if os.path.exists(p):
            return p
    return shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chrome")


def print_pagina(url, saida, largura=1440, altura=900, vertical=False):
    chrome = _chrome()
    if not chrome:
        raise SystemExit("Chrome não encontrado: tirar o print pelo Claude in Chrome")
    if vertical:
        largura, altura = 540, 960   # proporção 9:16; escala 2x = 1080x1920
    saida = os.path.abspath(saida)
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    perfil = tempfile.mkdtemp(prefix="ogab_print_")
    try:
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={perfil}",
                        f"--window-size={largura},{altura}", "--force-device-scale-factor=2", "--run-all-compositor-stages-before-draw",
                        "--virtual-time-budget=8000", f"--screenshot={saida}", url],
                       capture_output=True, timeout=90)
    finally:
        shutil.rmtree(perfil, ignore_errors=True)
    if not os.path.exists(saida):
        raise SystemExit("o print não saiu: tirar pelo Claude in Chrome")
    print(f"ok: {saida}  (abrir e conferir: banner de cookie ou paywall cobrindo a manchete = refazer pelo Claude in Chrome)")
    return saida


if __name__ == "__main__":
    a = sys.argv[1:]
    cmds = ("buscar", "achar", "folha", "baixar", "tiktok", "print")
    if not a or a[0] not in cmds:
        print(__doc__); sys.exit(1)

    def opt(k, d=None):
        return a[a.index(k) + 1] if k in a else d

    if a[0] == "buscar":
        res = buscar(a[1], int(opt("--n", 5)), opt("--fonte", "youtube"), opt("--tipo", "video"))
        if opt("--previa") and any(r.get("thumb") for r in res):
            previa([r for r in res if r.get("thumb")], opt("--previa"))
    elif a[0] == "achar":
        achar(a[1], a[2], int(opt("--n", 3)))
    elif a[0] == "folha":
        folha(a[1], a[2], opt("--de"), opt("--ate"), int(opt("--quadros", 12)), "--varrer" in a)
    elif a[0] == "tiktok":
        tiktok(a[1], int(opt("--n", 12)))
    elif a[0] == "print":
        print_pagina(a[1], a[2], int(opt("--largura", 1440)), int(opt("--altura", 900)), "--vertical" in a)
    else:
        baixar(a[1], a[2], a[3], opt("--de"), opt("--ate"), int(opt("--max", 1080)), "--com-audio" in a)
