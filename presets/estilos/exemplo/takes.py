"""Banco de TAKES REAIS para as prévias dos estilos: um vídeo diferente por estilo (regra do usuário, 23/10/2026).

  python3 presets/estilos/exemplo/takes.py filtrar [--brutos ~/.cache/ogab_takes/brutos] [--paralelo 6] [--apagar]
  python3 presets/estilos/exemplo/takes.py baixar ids.txt [--paralelo 4]   -> baixa+avalia+apaga um a um
  python3 presets/estilos/exemplo/takes.py folha        -> folha de contato dos aprovados (para conferir a olho)

Cada bruto (vídeo vertical do Pexels, licença livre, baixado em <brutos>/<id>.mp4) passa por:
- 1 rosto só, de frente, tamanho de apresentador (16-62% da largura), centrado, com espaço acima da cabeça;
- exposição normal: nem escuro nem estourado (rosto com luma média 85-170, quase nada queimado);
- nítido (detalhe no rosto) durante 5 s seguidos.
Aprovado vira <banco>/<id>/gravacao.mp4 (1080x1920, 24 qps, 5 s, sem som) + info.json. O fazer.py sorteia um take
diferente para cada estilo (takes.json guarda a escolha, para a prévia sair igual se refeita).
"""
import json, os, subprocess, sys, tempfile

BANCO = os.path.expanduser("~/.cache/ogab_takes")
W, H, DUR = 1080, 1920, 5.0


def sonda(arq):
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                        "-of", "json", arq], capture_output=True, text=True).stdout
    d = json.loads(o or "{}"); s = (d.get("streams") or [{}])[0]
    return s.get("width", 0), s.get("height", 0), float((d.get("format") or {}).get("duration", 0) or 0)


def rostos_vision(png):
    import Vision
    from Foundation import NSURL
    req = Vision.VNDetectFaceRectanglesRequest.alloc().init()
    hd = Vision.VNImageRequestHandler.alloc().initWithURL_options_(NSURL.fileURLWithPath_(png), None)
    ok, _ = hd.performRequests_error_([req], None)
    r = []
    for f in (req.results() or []) if ok else []:
        b = f.boundingBox(); yaw = f.yaw()
        r.append((b.origin.x, 1 - b.origin.y - b.size.height, b.size.width, b.size.height, float(yaw) if yaw is not None else 0.0))
    return r   # normalizado, y para baixo: (x, y, w, h, yaw)


def nitidez(cinza):
    a = cinza.astype("float32")
    lap = -4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:]
    return float(lap.var())


def avaliar(arq):
    """(ok, motivo, info). info tem o recorte (escala/offset) e o melhor trecho de 5 s."""
    import numpy as np
    from PIL import Image
    w, h, dur = sonda(arq)
    if not w or h < w * 1.4 or h < 1280 or dur < DUR + 1:
        return False, f"formato {w}x{h} {dur:.0f}s", None
    # escala para cobrir 1080x1920
    esc = max(W / w, H / h); sw, sh = round(w * esc / 2) * 2, round(h * esc / 2) * 2
    tmp = tempfile.mkdtemp(prefix="take_")
    fim = min(dur - .2, 24)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-t", str(fim), "-i", arq, "-vf", f"fps=2,scale={sw}:{sh}",
                    os.path.join(tmp, "q_%04d.png")], check=True)
    qs = sorted(os.listdir(tmp)); amostras = []
    for i, q in enumerate(qs):
        p = os.path.join(tmp, q)
        fs = [f for f in rostos_vision(p) if f[2] > .06]
        amostras.append((i / 2, p, fs))
    # posição do recorte: x centrado no rosto médio, y deixando a testa a ~24% da altura
    caixas = [f[0] for _, _, fs in amostras if len(fs) == 1 for f in [fs]]
    if len(caixas) < 10:
        return False, "sem rosto único", None
    mx = float(np.median([(c[0] + c[2] / 2) * sw for c in caixas])); my = float(np.median([c[1] * sh for c in caixas]))
    ox = int(min(max(0, mx - W / 2), sw - W)); oy = int(min(max(0, my - .24 * H), sh - H))
    bons = []
    for t, p, fs in amostras:
        if len(fs) != 1:
            bons.append(None); continue
        x, y, fw, fh, yaw = fs[0]
        X0, Y0, X1, Y1 = x * sw - ox, y * sh - oy, (x + fw) * sw - ox, (y + fh) * sh - oy
        larg = (X1 - X0) / W; cx = (X0 + X1) / 2 / W; topo = Y0 / H
        if not (.16 <= larg <= .62 and .3 <= cx <= .7 and .08 <= topo <= .45 and abs(yaw) < .45):
            bons.append(None); continue
        img = Image.open(p).convert("L").crop((ox, oy, ox + W, oy + H)); a = np.asarray(img)
        face = np.asarray(img.crop((int(X0), int(Y0), int(X1), int(Y1))).resize((200, int(200 * (Y1 - Y0) / max(1, X1 - X0)))))
        bons.append({"luma_rosto": float(face.mean()), "luma": float(a.mean()), "queimado": float((a >= 250).mean()),
                     "nitidez": nitidez(face), "caixa": [int(X0), int(Y0), int(X1), int(Y1)]})
    for p in os.listdir(tmp):
        os.remove(os.path.join(tmp, p))
    os.rmdir(tmp)
    n = int(DUR * 2) + 1; melhor = None
    for i in range(0, len(bons) - n + 1):
        jan = bons[i:i + n]
        if any(b is None for b in jan):
            continue
        lr = sum(b["luma_rosto"] for b in jan) / n; nt = sum(b["nitidez"] for b in jan) / n
        qm = max(b["queimado"] for b in jan); lm = sum(b["luma"] for b in jan) / n
        if not (85 <= lr <= 170 and 45 <= lm <= 175 and qm < .02):
            continue
        nota = nt - 2 * abs(lr - 125)
        if not melhor or nota > melhor["nota"]:
            melhor = {"de": i / 2, "nota": nota, "luma_rosto": round(lr), "luma": round(lm), "nitidez": round(nt, 1),
                      "rosto": jan[0]["caixa"]}
    if not melhor:
        return False, "sem 5 s bons (rosto/exposição)", None
    if melhor["nitidez"] < 25:
        return False, f"desfocado ({melhor['nitidez']})", None
    melhor.update(esc=[sw, sh], off=[ox, oy])
    return True, "ok", melhor


def preparar(arq):
    pid = os.path.splitext(os.path.basename(arq))[0]
    pasta = os.path.join(BANCO, "ok", pid)
    if os.path.exists(os.path.join(pasta, "info.json")):
        return pid, True, "já aprovado"
    ok, motivo, info = avaliar(arq)
    if not ok:
        return pid, False, motivo
    os.makedirs(pasta, exist_ok=True)
    sw, sh = info["esc"]; ox, oy = info["off"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(info["de"]), "-t", str(DUR), "-i", arq, "-vf",
                    f"scale={sw}:{sh}:flags=lanczos,crop={W}:{H}:{ox}:{oy},fps=24", "-an", "-c:v", "libx264", "-crf", "18",
                    "-pix_fmt", "yuv420p", os.path.join(pasta, "gravacao.mp4")], check=True)
    info["fonte"] = f"Pexels {pid} (licença Pexels: uso livre, com modificação)"
    json.dump(info, open(os.path.join(pasta, "info.json"), "w"))
    return pid, True, f"luma rosto {info['luma_rosto']}, nitidez {info['nitidez']}"


def garantir(pid):
    """Caminho da gravacao.mp4 do take; se o cache sumiu (limpeza de disco), baixa do Pexels e prepara de novo."""
    g = os.path.join(BANCO, "ok", str(pid), "gravacao.mp4")
    if os.path.exists(g):
        return g
    brutos = os.path.join(BANCO, "brutos"); os.makedirs(brutos, exist_ok=True)
    arq = os.path.join(brutos, f"{pid}.mp4")
    try:
        subprocess.run(["curl", "-sL", "-A", "Mozilla/5.0", "--max-time", "300", "-o", arq,
                        f"https://www.pexels.com/download/video/{pid}/"], check=True)
        _, ok, msg = preparar(arq)
    finally:
        if os.path.exists(arq):
            os.remove(arq)
    if not ok:
        raise SystemExit(f"take {pid} não passou no filtro ao baixar de novo: {msg}")
    return g


def aprovados():
    d = os.path.join(BANCO, "ok")
    return sorted(p for p in os.listdir(d) if os.path.exists(os.path.join(d, p, "info.json"))) if os.path.isdir(d) else []


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["filtrar"]:
        brutos = os.path.expanduser(a[a.index("--brutos") + 1]) if "--brutos" in a else os.path.join(BANCO, "brutos")
        n = int(a[a.index("--paralelo") + 1]) if "--paralelo" in a else 6
        from concurrent.futures import ThreadPoolExecutor
        arqs = sorted(os.path.join(brutos, f) for f in os.listdir(brutos) if f.endswith(".mp4"))
        def um(f):
            try:
                return preparar(f)
            except Exception as e:
                return os.path.basename(f), False, "erro: " + str(e)[-120:]
        with ThreadPoolExecutor(n) as ex:
            for pid, ok, msg in ex.map(um, arqs):
                print(("OK   " if ok else "fora ") + pid + ": " + msg, flush=True)
                if "--apagar" in a and not msg.startswith("erro"):   # bruto já avaliado: libera o disco (4K pesa)
                    try:
                        os.remove(os.path.join(brutos, pid + ".mp4"))
                    except OSError:
                        pass
        print(len(aprovados()), "aprovados")
    elif a[:1] == ["baixar"]:   # lista de ids do Pexels: baixa, avalia e apaga o bruto um a um (não lota o disco)
        ids = [l.strip() for l in open(a[1]) if l.strip()]
        n = int(a[a.index("--paralelo") + 1]) if "--paralelo" in a else 4
        brutos = os.path.join(BANCO, "brutos"); os.makedirs(brutos, exist_ok=True)
        from concurrent.futures import ThreadPoolExecutor
        def um(pid):
            if os.path.exists(os.path.join(BANCO, "ok", pid, "info.json")):
                return pid, True, "já aprovado"
            arq = os.path.join(brutos, pid + ".mp4")
            try:
                subprocess.run(["curl", "-sL", "-A", "Mozilla/5.0", "--max-time", "300", "-o", arq,
                                f"https://www.pexels.com/download/video/{pid}/"], check=True)
                return preparar(arq)
            except Exception as e:
                return pid, False, "erro: " + str(e)[-120:]
            finally:
                if os.path.exists(arq):
                    os.remove(arq)
        with ThreadPoolExecutor(n) as ex:
            for pid, ok, msg in ex.map(um, ids):
                print(("OK   " if ok else "fora ") + pid + ": " + msg, flush=True)
        print(len(aprovados()), "aprovados")
    elif a[:1] == ["folha"]:
        from PIL import Image, ImageDraw
        ids = aprovados(); d = os.path.join(BANCO, "ok"); saida = os.path.join(BANCO, "folha.png")
        col = 10; tw, th = 135, 240; lin = max(1, (len(ids) + col - 1) // col)
        folha = Image.new("RGB", (col * tw, lin * th), "black"); dr = ImageDraw.Draw(folha)
        for k, pid in enumerate(ids):
            q = os.path.join(d, pid, "quadro.png")
            if not os.path.exists(q):
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "2", "-i", os.path.join(d, pid, "gravacao.mp4"),
                                "-frames:v", "1", "-vf", f"scale={tw}:{th}", q], check=True)
            x, y = (k % col) * tw, (k // col) * th
            folha.paste(Image.open(q), (x, y)); dr.rectangle((x, y, x + 34, y + 16), fill="black"); dr.text((x + 3, y + 2), str(k), fill="white")
        folha.save(saida); print(saida); print(" ".join(f"{k}={v}" for k, v in enumerate(ids)))
    else:
        raise SystemExit(__doc__)
