"""Decupa um vídeo de REFERÊNCIA ("faz igual esse Reel") e compara o nosso export com ele.

  python3 referencia.py decupar <arquivo ou link> [--saida <pasta>] [--limiar 0.3] [--refazer]
  python3 referencia.py comparar <nosso.mp4> <referencia.json> [--saida <pasta>]

decupar: baixa o link (yt-dlp, só para análise), corta barra de interface de gravação de tela do celular e tarja preta,
e mede o que hoje se anotava à mão:
  - planos: início, fim e duração de cada um (corte de cena do ffmpeg), média, mais curto, mais longo, cortes por 10 s
  - câmera por plano, MEDIDA por fluxo óptico: aproxima, afasta, anda para um lado, sobe/desce, gira ou parada,
    com o ritmo (parada, lenta, média, rápida)
  - luz e cor por plano: brilho, contraste, % de quadro escuro, saturação e as 4 cores dominantes
  - música: BPM e grade de batidas (musica.py), média do plano em batidas, % de cortes que caem na batida
  - picos: onde o som cresce e explode (preparação, respiro, impacto), presos na batida mais perto
  - flashes: quadros brancos de impacto
Saída em <pasta> (padrão: <arquivo>_referencia/ ou ./referencia_<id>/):
  referencia.json   tudo medido (o storyboard.py e o revisor.py leem este arquivo)
  referencia.md     a FICHA DE RITMO: resumo + tabela plano a plano (coluna "o que acontece" o Gab preenche olhando)
  folha_1s.jpg      um quadro por segundo (olhar primeiro)
  folha_planos.jpg  o quadro do meio de cada plano, com número e tempo
A mesma referência já decupada na mesma pasta é reaproveitada (--refazer mede de novo).

comparar: mede o nosso vídeo com as MESMAS funções e aponta a distância da referência. Tolerância de 30% na média de
plano (fora disso é ERRO), avisos para câmera parada demais, luz diferente e cortes fora da batida. Gera
lado_a_lado.jpg (referência em cima, o nosso embaixo, nos mesmos pontos relativos do vídeo) e comparacao.md.
O revisor.py chama isto sozinho com --referencia.

No plano do motion (plano.js/plano.json), cada cena aponta para o plano da referência que ela recria:
  "cenas": [{"dur": 2.4, "ref_plano": 3, "ref_o_que": "aproxima rápido no rosto e corta no bumbo", ...}]
e "referencia": "<caminho do referencia.json>" no topo do plano (o storyboard.py confere duração e plano a plano).

Só INSPIRAÇÃO de ritmo e linguagem: nunca copiar imagem, texto, marca ou personagem da referência.
Adaptado de ReelMimic (analyze.py, compare.py) (c) 2026 ReelMimic contributors, licença MIT.
"""
import collections, hashlib, json, os, re, shutil, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

TOLERANCIA = 0.30   # média de plano e duração de cena: até 30% de diferença da referência
CAMERA = {"aproxima": "aproxima", "afasta": "afasta", "esquerda": "anda p/ esquerda", "direita": "anda p/ direita",
          "sobe": "sobe", "desce": "desce", "gira": "gira", "parada": "parada"}


def sh(cmd, **k):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **k)


def sondar(path):
    j = json.loads(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                       "-of", "json", path]).stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    fps = None
    if v and v.get("r_frame_rate") and v["r_frame_rate"] != "0/0":
        n, d = v["r_frame_rate"].split("/"); fps = round(float(n) / float(d), 3)
    return {"duracao": float(j["format"]["duration"]), "w": v and v["width"], "h": v and v["height"], "fps": fps, "audio": a is not None}


def baixar(src, out):
    if os.path.isfile(src):
        return os.path.abspath(src)
    exe = shutil.which("yt-dlp")
    if not exe:
        raise SystemExit("yt-dlp não encontrado: brew install yt-dlp (ou rode o install.sh)")
    r = sh([exe, "-f", "bv*[height<=1080]+ba/b[height<=1080]/b", "--merge-output-format", "mp4", "--no-playlist",
            "-o", os.path.join(out, "fonte.%(ext)s"), src])
    for f in sorted(os.listdir(out)):
        if f.startswith("fonte.") and not f.endswith(".part"):
            return os.path.join(out, f)
    raise SystemExit("não consegui baixar a referência (privada/bloqueada? brew upgrade yt-dlp):\n" + r.stderr[-800:])


# ------------------------------------------------------------------ recorte (tarja e gravação de tela)
def recorte_tarja(path, dur, w, h):
    """A caixa mais comum do cropdetect no vídeo; None se a imagem já ocupa o quadro."""
    r = sh(["ffmpeg", "-hide_banner", "-i", path, "-t", str(min(dur, 60)), "-vf", "fps=2,cropdetect=limit=24:round=2:reset=1",
            "-f", "null", "-"])
    caixas = collections.Counter(re.findall(r"crop=(\d+:\d+:\d+:\d+)", r.stderr))
    if not caixas:
        return None
    cw, ch, cx, cy = map(int, caixas.most_common(1)[0][0].split(":"))
    if cw * ch > .85 * w * h:
        return None
    return {"w": cw, "h": ch, "x": cx, "y": cy, "motivo": "tarja preta / imagem dentro de um quadro maior"}


def recorte_tela_celular(path, dur, w, h):
    """Gravação de tela do celular: o vídeo fica entre duas faixas de interface que não são pretas (o cropdetect não vê).
    A faixa de linhas que MAIS muda no tempo é o vídeo tocando."""
    import numpy as np, cv2
    cap = cv2.VideoCapture(path); qs = []
    for k in range(12):
        cap.set(cv2.CAP_PROP_POS_MSEC, (k + .5) / 12 * dur * 1000)
        ok, f = cap.read()
        if ok:
            qs.append(cv2.cvtColor(cv2.resize(f, (w // 4, h // 4)), cv2.COLOR_BGR2GRAY).astype("float32"))
    cap.release()
    if len(qs) < 4:
        return None
    var = np.stack(qs).std(axis=0).mean(axis=1)
    linhas = np.where(var > max(6.0, var.max() * .35))[0]
    if not len(linhas):
        return None
    trechos, ini = [], linhas[0]
    for a, b in zip(linhas, linhas[1:]):
        if b != a + 1:
            trechos.append((ini, a)); ini = b
    trechos.append((ini, linhas[-1]))
    y0, y1 = max(trechos, key=lambda t: t[1] - t[0])
    y0, y1 = int(y0 * 4), int((y1 + 1) * 4)
    if (y1 - y0) > .85 * h or (y1 - y0) < .15 * h:
        return None
    return {"w": w, "h": (y1 - y0) // 2 * 2, "x": 0, "y": y0, "motivo": "faixa do vídeo entre a interface (gravação de tela)"}


def proxy(path, caixa, out):
    """Cópia de análise: recortada (se precisar) e com keyframe a cada 12 quadros (os saltos do fluxo óptico ficam baratos)."""
    dst = os.path.join(out, "_analise.mp4")
    vf = ["-vf", f"crop={caixa['w']}:{caixa['h']}:{caixa['x']}:{caixa['y']}"] if caixa else []
    sh(["ffmpeg", "-v", "error", "-y", "-i", path, *vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-g", "12", "-an", dst])
    return dst


# ------------------------------------------------------------------ planos, câmera e luz
def planos(path, dur, limiar=0.3, minimo=0.2):
    """Cortes pela detecção de cena do ffmpeg; plano mais curto que `minimo` (flash, quadro sujo) emenda no anterior."""
    r = sh(["ffmpeg", "-hide_banner", "-i", path, "-vf", f"select='gt(scene,{limiar})',showinfo", "-an", "-f", "null", "-"])
    cortes = [float(m) for m in re.findall(r"pts_time:([\d.]+)", r.stderr)]
    pts, ult = [0.0], 0.0
    for t in cortes:
        if t - ult >= minimo and dur - t >= minimo:
            pts.append(t); ult = t
    pts.append(dur)
    return [[round(a, 3), round(b, 3)] for a, b in zip(pts, pts[1:])]


def medir_planos(path, spans):
    """Por plano: câmera (fluxo óptico Farneback: translação, zoom e giro pela mediana dos pixels com textura) e luz
    (brilho, contraste, % escuro, saturação, 4 cores dominantes por k-means)."""
    import numpy as np, cv2
    cap = cv2.VideoCapture(path); out = []
    for i, (a, b) in enumerate(spans, 1):
        n = max(3, min(10, int((b - a) * 5))); ts = [a + (b - a) * (k + .5) / n for k in range(n)]
        cinzas, cores = [], []
        for t in ts:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read()
            if not ok:
                continue
            p = cv2.resize(f, (320, round(320 * f.shape[0] / f.shape[1])))
            cinzas.append(cv2.cvtColor(p, cv2.COLOR_BGR2GRAY)); cores.append(p)
        if len(cinzas) < 2:
            continue
        H, W = cinzas[0].shape; yy, xx = np.mgrid[0:H, 0:W]; xc, yc = xx - W / 2, yy - H / 2
        tx = ty = zoom = giro = 0.0
        for g0, g1 in zip(cinzas, cinzas[1:]):
            fl = cv2.calcOpticalFlowFarneback(g0, g1, None, .5, 3, 21, 3, 5, 1.2, 0)
            u, v = fl[..., 0], fl[..., 1]
            gx = cv2.Sobel(g0, cv2.CV_32F, 1, 0); gy = cv2.Sobel(g0, cv2.CV_32F, 0, 1)
            tex = np.hypot(gx, gy) > 40          # fundo liso e barra parada puxariam a mediana para zero
            tex[: max(1, H // 25)] = False
            if tex.sum() < 200:
                continue
            uu, vv, x_, y_ = u[tex], v[tex], xc[tex], yc[tex]
            tx += float(np.median(uu)); ty += float(np.median(vv))
            r2 = x_ ** 2 + y_ ** 2 + 1e-6
            zoom += float(np.median((uu * x_ + vv * y_) / r2)); giro += float(np.median((vv * x_ - uu * y_) / r2))
        span = ts[-1] - ts[0] or 1
        mv = {"pan_x": round(tx / W / span, 4), "tilt_y": round(ty / H / span, 4), "zoom": round(zoom / span, 4), "giro": round(giro / span, 4)}
        # cada componente em "vezes o limiar"; fica só o dominante (e o 2º se chegar a 70% dele): em plano curto e
        # câmera na mão os quatro passam do limiar juntos e a etiqueta vira ruído
        comp = [("aproxima" if mv["zoom"] > 0 else "afasta", abs(mv["zoom"]) / .006),
                ("esquerda" if mv["pan_x"] > 0 else "direita", abs(mv["pan_x"]) / .008),   # imagem p/ direita = câmera p/ esquerda
                ("sobe" if mv["tilt_y"] > 0 else "desce", abs(mv["tilt_y"]) / .008),
                ("gira", abs(mv["giro"]) / .01)]
        comp = sorted([c for c in comp if c[1] > 1], key=lambda c: -c[1])
        mv["tipo"] = [c[0] for c in comp[:2] if c[1] >= comp[0][1] * .7] if comp else ["parada"]
        vel = max(abs(mv["pan_x"]), abs(mv["tilt_y"]), abs(mv["zoom"]), abs(mv["giro"]))
        mv["ritmo"] = "parada" if vel < .006 else "lenta" if vel < .04 else "média" if vel < .12 else "rápida"
        px = np.concatenate([c.reshape(-1, 3) for c in cores]).astype(np.float32)
        lum = (.114 * px[:, 0] + .587 * px[:, 1] + .299 * px[:, 2]) / 255
        rg = px[:, 2] - px[:, 1]; yb = .5 * (px[:, 2] + px[:, 1]) - px[:, 0]
        sat = float(np.sqrt(rg.std() ** 2 + yb.std() ** 2) + .3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)) / 255
        amostra = px[:: max(1, len(px) // 4000)]
        _, lab, cen = cv2.kmeans(amostra, 4, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0), 2, cv2.KMEANS_PP_CENTERS)
        ordem = np.argsort(-np.bincount(lab.ravel(), minlength=4))
        out.append({"plano": i, "ini": round(a, 2), "fim": round(b, 2), "dur": round(b - a, 2), "camera": mv,
                    "luz": {"brilho": round(float(lum.mean()), 3), "contraste": round(float(lum.std()), 3),
                            "escuro": round(float((lum < .08).mean()), 3), "saturacao": round(sat, 3),
                            "cores": ["#%02X%02X%02X" % (int(cen[k][2]), int(cen[k][1]), int(cen[k][0])) for k in ordem]}})
    cap.release()
    return out


def flashes(path):
    """Quadros muito mais claros que os vizinhos (flash branco de impacto), a 6 qps."""
    import numpy as np
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", "fps=6,scale=64:36,format=gray", "-f", "rawvideo", "-"],
                       capture_output=True)
    a = np.frombuffer(r.stdout, np.uint8)
    if not len(a):
        return []
    lum = a[: len(a) // (64 * 36) * 64 * 36].reshape(-1, 64 * 36).mean(1) / 255
    out = []
    for i in range(2, len(lum) - 2):
        viz = np.r_[lum[i - 2:i], lum[i + 1:i + 3]]
        if lum[i] > .75 and lum[i] - viz.min() > .3:
            t = round(i / 6, 2)
            if not out or t - out[-1] > 1:
                out.append(t)
    return out


# ------------------------------------------------------------------ som
def som(path):
    """BPM e grade (musica.py) + picos: onde volume, ataques e preenchimento do espectro sobem juntos depois de um
    trecho mais baixo (o respiro antes do impacto). Os números só APONTAM: confirmar olhando os quadros."""
    import numpy as np
    import musica
    try:
        x = musica.ler(path)
    except subprocess.CalledProcessError:
        return {"presente": False}
    if len(x) < musica.SR * 2 or float(np.sqrt(np.mean(x ** 2))) < 10 ** (-45 / 20):
        return {"presente": True, "mudo": True}
    bpm, periodo, grade = musica.bpm_e_grade(x)
    hop = musica.SR // 4
    n = len(x) // hop
    if n < 24:
        return {"presente": True, "mudo": False, "bpm": round(bpm, 1), "batida_s": round(periodo, 4), "batidas": [round(t, 3) for t in grade], "picos": []}
    blocos = x[: n * hop].reshape(n, hop)
    rms = 20 * np.log10(np.sqrt((blocos ** 2).mean(1)) + 1e-9)
    S = np.abs(np.fft.rfft(blocos * np.hanning(hop), axis=1))
    fluxo = np.r_[0, np.maximum(0, np.diff(np.log1p(S), axis=0)).sum(1)]
    f = np.fft.rfftfreq(hop, 1 / musica.SR); c = (S * f).sum(1) / (S.sum(1) + 1e-9)
    larg = np.sqrt((S * (f - c[:, None]) ** 2).sum(1) / (S.sum(1) + 1e-9))
    z = lambda v: (v - v.mean()) / (v.std() + 1e-9)
    cur = np.convolve(z(rms) + z(fluxo) + z(larg), np.ones(4) / 4, mode="same")
    cand = []
    for i in range(8, n - 4):
        antes, depois = cur[i - 8:i].mean(), cur[i:i + 4].mean()
        sobe = depois - antes
        if sobe < .8:
            continue
        cand.append((sobe + .5 * max(0.0, antes - float(cur[i - 8:i].min())) + .3 * depois, i * .25, sobe))
    cand.sort(reverse=True)
    picos = []
    for _, t, sobe in cand:
        if len(grade):
            t = float(grade[np.argmin(np.abs(grade - t))])
        if any(abs(t - p["t"]) < 6 for p in picos):
            continue
        picos.append({"t": round(t, 2), "subida": round(float(sobe), 2), "tipo": "drop" if sobe >= 2.5 else "subida"})
        if len(picos) >= 3:
            break
    return {"presente": True, "mudo": False, "bpm": round(bpm, 1), "batida_s": round(periodo, 4),
            "batidas": [round(float(t), 3) for t in grade], "picos": sorted(picos, key=lambda p: p["t"])}


def na_batida(cortes, batidas, periodo):
    """% de cortes a até 1/6 de batida (ou 80 ms) de uma batida."""
    if not cortes or not batidas:
        return None
    import numpy as np
    b = np.asarray(batidas); tol = max(.08, periodo / 6)
    return round(sum(1 for t in cortes if np.abs(b - t).min() <= tol) / len(cortes), 2)


# ------------------------------------------------------------------ folhas
def _rotulo(img, txt):
    import cv2
    for cor, esp in (((0, 0, 0), 3), ((255, 255, 255), 1)):
        cv2.putText(img, txt, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, .6, cor, esp)
    return img


def _grade(tiles, colunas):
    import numpy as np, cv2
    h = tiles[0].shape[0]; tiles = [t if t.shape[0] == h else cv2.resize(t, (t.shape[1], h)) for t in tiles]
    while len(tiles) % colunas:
        tiles.append(np.zeros_like(tiles[0]))
    return np.vstack([np.hstack(tiles[r:r + colunas]) for r in range(0, len(tiles), colunas)])


def quadros(path, tempos, larg=240, rotulos=None):
    import cv2
    cap = cv2.VideoCapture(path); out = []
    for k, t in enumerate(tempos):
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read()
        if not ok:
            continue
        f = cv2.resize(f, (larg, round(larg * f.shape[0] / f.shape[1])))
        out.append(_rotulo(f, rotulos[k] if rotulos else f"{t:.1f}s"))
    cap.release()
    return out


def folhas(path, dur, sp, out):
    import cv2
    n = int(min(dur, 64)) or 1
    tiles = quadros(path, [dur * (k + .5) / n for k in range(n)], 200)
    if tiles:
        cv2.imwrite(os.path.join(out, "folha_1s.jpg"), _grade(tiles, 8), [cv2.IMWRITE_JPEG_QUALITY, 85])
    passo = max(1, len(sp) // 48); sel = sp[::passo][:48]
    tiles = quadros(path, [(p["ini"] + p["fim"]) / 2 for p in sel], 240, [f"#{p['plano']}  {p['ini']:.1f}s" for p in sel])
    if tiles:
        cv2.imwrite(os.path.join(out, "folha_planos.jpg"), _grade(tiles, 8), [cv2.IMWRITE_JPEG_QUALITY, 85])


# ------------------------------------------------------------------ medição (mesma para a referência e para o nosso)
def medir(path, out, limiar=0.3):
    info = sondar(path)
    caixa = None
    if info["w"]:
        caixa = recorte_tarja(path, info["duracao"], info["w"], info["h"]) or \
                recorte_tela_celular(path, info["duracao"], info["w"], info["h"])
    vid = proxy(path, caixa, out) if caixa or info["duracao"] > 120 else path
    dur = info["duracao"]
    spans = planos(vid, dur, limiar)
    sp = medir_planos(vid, spans)
    durs = [p["dur"] for p in sp] or [dur]
    au = som(path) if info["audio"] else {"presente": False}
    cortes = [p["ini"] for p in sp[1:]]
    ritmo = {"planos": len(sp), "media_s": round(sum(durs) / len(durs), 2), "mais_curto_s": round(min(durs), 2),
             "mais_longo_s": round(max(durs), 2), "cortes_por_10s": round(len(cortes) / dur * 10, 2) if dur else 0}
    if au.get("bpm"):
        ritmo["media_batidas"] = round(ritmo["media_s"] / au["batida_s"], 1)
        ritmo["cortes_na_batida"] = na_batida(cortes, au["batidas"], au["batida_s"])
    luz = {}
    if sp:
        luz = {"brilho": round(sum(p["luz"]["brilho"] for p in sp) / len(sp), 3),
               "saturacao": round(sum(p["luz"]["saturacao"] for p in sp) / len(sp), 3),
               "planos_escuros": round(sum(1 for p in sp if p["luz"]["escuro"] > .5) / len(sp), 2),
               "camera_em_movimento": round(sum(1 for p in sp if p["camera"]["tipo"] != ["parada"]) / len(sp), 2),
               "movimentos": sorted({k for p in sp for k in p["camera"]["tipo"]})}
    rep = {"video": info, "recorte": caixa, "ritmo": ritmo, "luz": luz, "som": au, "planos": sp,
           "flashes": flashes(vid) if info["w"] else []}
    if info["w"]:
        folhas(vid, dur, sp, out)
    if vid != path:
        os.remove(vid)
    return rep


def chave(src):
    h = hashlib.sha1(b"ref1|")
    if os.path.isfile(src):
        tam = os.path.getsize(src); h.update(str(tam).encode())
        with open(src, "rb") as f:
            h.update(f.read(4 << 20))
    else:
        h.update(src.strip().encode())
    return h.hexdigest()[:12]


def _cam(p):
    return " + ".join(CAMERA.get(k, k) for k in p["camera"]["tipo"]) + ("" if p["camera"]["ritmo"] == "parada" else f" ({p['camera']['ritmo']})")


def ficha(rep, out):
    r, l, au = rep["ritmo"], rep["luz"], rep["som"]
    v = rep["video"]
    L = ["# Ficha de ritmo da referência", "", f"Entrada: {rep['entrada']}", "",
         f"- Vídeo: {v['w']}x{v['h']}, {v['duracao']:.1f} s" + (f" (recortado: {rep['recorte']['motivo']})" if rep["recorte"] else ""),
         f"- Planos: {r['planos']}, média {r['media_s']} s (mais curto {r['mais_curto_s']} s, mais longo {r['mais_longo_s']} s), "
         f"{r['cortes_por_10s']} cortes a cada 10 s"]
    if au.get("bpm"):
        nb = r.get("cortes_na_batida")
        L.append(f"- Música: {au['bpm']} BPM (batida {au['batida_s']} s), plano médio = {r['media_batidas']} batidas"
                 + (f", {round(nb * 100)}% dos cortes na batida" if nb is not None else "")
                 + " (com fala por cima o BPM pode errar: conferir com musica.py na trilha limpa)")
    elif au.get("mudo"):
        L.append("- Som: mudo ou baixo demais para medir")
    if l:
        L.append(f"- Luz: brilho médio {l['brilho']}, saturação {l['saturacao']}, {round(l['planos_escuros'] * 100)}% planos escuros")
        L.append(f"- Câmera em movimento em {round(l['camera_em_movimento'] * 100)}% dos planos: "
                 + ", ".join(CAMERA.get(k, k) for k in l["movimentos"]))
    if au.get("picos"):
        L.append("- Picos (som cresce e explode): " + ", ".join(f"{p['t']} s ({p['tipo']})" for p in au["picos"])
                 + ". Conferir olhando a tira de quadros em volta (grade.py --de/--ate, passo 0,08)")
    if rep["flashes"]:
        L.append("- Flashes brancos de impacto: " + ", ".join(f"{t} s" for t in rep["flashes"]))
    L += ["", "Provas: `folha_1s.jpg` (1 quadro por segundo) e `folha_planos.jpg` (meio de cada plano, com número).", "",
          "## Planos (preencher \"o que acontece\" olhando a folha_planos)", "",
          "| Plano | Tempo | Dur. | Câmera | Brilho | Cor dominante | O que acontece |", "|---|---|---|---|---|---|---|"]
    for p in rep["planos"]:
        L.append(f"| {p['plano']} | {p['ini']:.1f}-{p['fim']:.1f} s | {p['dur']:.1f} s | {_cam(p)} | {p['luz']['brilho']:.2f} | {p['luz']['cores'][0]} |  |")
    L += ["", "## Como usar no plano", "",
          "Cada cena do nosso plano aponta para o plano da referência que ela recria: `\"ref_plano\": N` e `\"ref_o_que\"` "
          "(o recurso daquele plano: movimento, entrada, corte). Mesmo tipo e ritmo de câmera; duração da cena e média de plano "
          f"até {round(TOLERANCIA * 100)}% da referência. Copiar a LINGUAGEM, nunca imagem, texto, marca ou personagem.",
          f"No topo do plano: `\"referencia\": \"{os.path.join(out, 'referencia.json')}\"` (o storyboard.py confere). "
          "Depois do render: `revisor.py <mp4> --referencia <referencia.json>`."]
    open(os.path.join(out, "referencia.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")


def decupar(src, out=None, limiar=0.3, refazer=False):
    if not out:
        out = (os.path.splitext(os.path.abspath(src))[0] + "_referencia") if os.path.isfile(src) else \
              os.path.abspath(f"referencia_{chave(src)}")
    os.makedirs(out, exist_ok=True)
    arq = os.path.join(out, "referencia.json")
    if not refazer and os.path.exists(arq):
        rep = json.load(open(arq, encoding="utf-8"))
        if rep.get("chave") == chave(src):
            print("referência já decupada nesta pasta: reaproveitada (--refazer mede de novo)")
            return rep, out
    fonte = baixar(src, out)
    rep = medir(fonte, out, limiar)
    rep.update({"entrada": src, "arquivo": fonte, "chave": chave(src)})
    json.dump(rep, open(arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ficha(rep, out)
    return rep, out


# ------------------------------------------------------------------ plano (storyboard) e comparação (revisor)
def conferir_plano(cenas, ref):
    """Avisos do plano contra a referência: cena sem ref_plano, plano inexistente, duração fora da tolerância."""
    sp = {p["plano"]: p for p in ref.get("planos", [])}
    avisos = []
    for c in cenas:
        n = c.get("ref_plano")
        if n in (None, ""):
            avisos.append(f"cena {c['n']}: sem ref_plano (a qual plano da referência ela corresponde?)")
            continue
        p = sp.get(int(n))
        if not p:
            avisos.append(f"cena {c['n']}: ref_plano {n} não existe (a referência tem {len(sp)} planos)")
            continue
        dif = (c["dur"] - p["dur"]) / p["dur"] if p["dur"] else 0
        if abs(dif) > TOLERANCIA:
            avisos.append(f"cena {c['n']}: {c['dur']:.1f} s, plano {n} da referência tem {p['dur']:.1f} s ({dif:+.0%})")
    if cenas:
        media = sum(c["dur"] for c in cenas) / len(cenas); alvo = ref["ritmo"]["media_s"]
        if alvo and abs(media - alvo) / alvo > TOLERANCIA:
            avisos.append(f"média de cena {media:.1f} s, referência {alvo:.1f} s ({(media - alvo) / alvo:+.0%}): "
                          + ("dividir cenas" if media > alvo else "juntar cenas"))
    return avisos


def comparar(video, ref_json, out):
    """Mede o nosso vídeo com as mesmas funções e devolve (erros, avisos, tabela_md) em relação à referência."""
    ref = json.load(open(ref_json, encoding="utf-8")) if isinstance(ref_json, str) else ref_json
    os.makedirs(out, exist_ok=True)
    tmp = os.path.join(out, "_nosso"); os.makedirs(tmp, exist_ok=True)
    nos = medir(video, tmp)
    erros, avisos = [], []
    rr, nr = ref["ritmo"], nos["ritmo"]
    dif = (nr["media_s"] - rr["media_s"]) / rr["media_s"] if rr["media_s"] else 0
    if abs(dif) > TOLERANCIA:
        erros.append(("todo", f"ritmo: plano médio {nr['media_s']} s contra {rr['media_s']} s da referência ({dif:+.0%}, "
                              f"tolerância {round(TOLERANCIA * 100)}%): " + ("cortar mais" if dif > 0 else "segurar mais os planos")))
    rl, nl = ref.get("luz") or {}, nos.get("luz") or {}
    if rl and nl:
        if rl["camera_em_movimento"] - nl["camera_em_movimento"] > .25:
            avisos.append(("todo", f"câmera viva em {round(nl['camera_em_movimento'] * 100)}% dos planos, referência "
                                   f"{round(rl['camera_em_movimento'] * 100)}%: faltam planos com movimento"))
        if abs(rl["brilho"] - nl["brilho"]) > .15:
            avisos.append(("todo", f"brilho médio {nl['brilho']} contra {rl['brilho']} da referência"))
    nb = None
    if rr.get("cortes_na_batida") is not None:
        b = nos["som"].get("batidas") or ref["som"].get("batidas")
        per = nos["som"].get("batida_s") or ref["som"].get("batida_s")
        nb = na_batida([p["ini"] for p in nos["planos"][1:]], b, per)
        if nb is not None and rr["cortes_na_batida"] >= .6 and nb < rr["cortes_na_batida"] - .25:
            avisos.append(("todo", f"{round(nb * 100)}% dos cortes na batida, referência {round(rr['cortes_na_batida'] * 100)}%"))
    lado_a_lado(ref, video, nos["video"]["duracao"], out)
    linha = lambda nome, a, b: f"| {nome} | {a} | {b} |"
    T = ["| Medida | Referência | Nosso |", "|---|---|---|",
         linha("Duração", f"{ref['video']['duracao']:.1f} s", f"{nos['video']['duracao']:.1f} s"),
         linha("Planos", rr["planos"], nr["planos"]),
         linha("Plano médio", f"{rr['media_s']} s", f"{nr['media_s']} s ({dif:+.0%})"),
         linha("Cortes a cada 10 s", rr["cortes_por_10s"], nr["cortes_por_10s"])]
    if rl and nl:
        T += [linha("Câmera em movimento", f"{round(rl['camera_em_movimento'] * 100)}%", f"{round(nl['camera_em_movimento'] * 100)}%"),
              linha("Brilho médio", rl["brilho"], nl["brilho"]), linha("Saturação", rl["saturacao"], nl["saturacao"])]
    if rr.get("cortes_na_batida") is not None:
        T.append(linha("Cortes na batida", f"{round(rr['cortes_na_batida'] * 100)}%", f"{round(nb * 100)}%" if nb is not None else "sem corte"))
    json.dump({"referencia": ref_json if isinstance(ref_json, str) else None, "nosso": nos, "erros": erros, "avisos": avisos},
              open(os.path.join(out, "comparacao.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    shutil.rmtree(tmp, ignore_errors=True)
    return erros, avisos, T


def lado_a_lado(ref, video, dur_nosso, out, n=8):
    """Referência em cima, o nosso embaixo, nos mesmos pontos relativos (10%, 21%... 90% de cada vídeo)."""
    import numpy as np, cv2
    fr = [.1 + .8 * k / (n - 1) for k in range(n)]
    dr = ref["video"]["duracao"]
    vazio = [""] * n
    cima = quadros(ref["arquivo"], [dr * f for f in fr], 400, vazio) if os.path.exists(ref.get("arquivo", "")) else []
    baixo = quadros(video, [dur_nosso * f for f in fr], 400, vazio)
    if not baixo:
        return None
    W, H = 200, 356   # célula 9:16; formato diferente (16:9 contra 9:16) entra com tarja, nunca esticado

    def caber(img, txt):
        s = min(W / img.shape[1], H / img.shape[0])
        r = cv2.resize(img, (max(1, round(img.shape[1] * s)), max(1, round(img.shape[0] * s))))
        cel = np.full((H, W, 3), 18, np.uint8)
        y, x = (H - r.shape[0]) // 2, (W - r.shape[1]) // 2
        cel[y:y + r.shape[0], x:x + r.shape[1]] = r
        return _rotulo(cel, txt)
    baixo = [caber(t, f"nosso {dur_nosso * f:.1f}s") for t, f in zip(baixo, fr)]
    linhas = [np.hstack(baixo)]
    if cima and len(cima) == len(baixo):
        linhas = [np.hstack([caber(t, f"ref {dr * f:.1f}s") for t, f in zip(cima, fr)]), linhas[0]]
    saida = os.path.join(out, "lado_a_lado.jpg")
    cv2.imwrite(saida, np.vstack(linhas), [cv2.IMWRITE_JPEG_QUALITY, 85])
    return saida


def main(a):
    if len(a) < 2 or a[0] not in ("decupar", "comparar"):
        raise SystemExit(__doc__)
    op = lambda k: a[a.index(k) + 1] if k in a else None
    if a[0] == "decupar":
        rep, out = decupar(a[1], op("--saida"), float(op("--limiar") or .3), "--refazer" in a)
        r = rep["ritmo"]
        print(f"{r['planos']} planos, média {r['media_s']} s, {r['cortes_por_10s']} cortes/10 s"
              + (f", {rep['som']['bpm']} BPM" if rep["som"].get("bpm") else ""))
        for f in ("referencia.md", "folha_1s.jpg", "folha_planos.jpg", "referencia.json"):
            print(os.path.join(out, f))
        return
    if len(a) < 3:
        raise SystemExit(__doc__)
    v = os.path.abspath(a[1])
    out = os.path.abspath(op("--saida") or os.path.join(os.path.dirname(v), f"comparacao_{os.path.splitext(os.path.basename(v))[0]}"))
    erros, avisos, T = comparar(v, os.path.abspath(a[2]), out)
    L = ["# Ritmo vs referência", ""] + T + [""] + [f"- **ERRO** [{t}] {m}" for t, m in erros] + \
        [f"- aviso [{t}] {m}" for t, m in avisos] + ["", "Prova: `lado_a_lado.jpg` (referência em cima, o nosso embaixo)."]
    open(os.path.join(out, "comparacao.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(T)); print(os.path.join(out, "comparacao.md")); print(os.path.join(out, "lado_a_lado.jpg"))
    print(f"{len(erros)} erro(s), {len(avisos)} aviso(s)")
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
