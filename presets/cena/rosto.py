"""Onde está o rosto em cada momento do vídeo (regra do Gab: texto e animação NUNCA na frente do rosto).

  python3 rosto.py video.mp4 [--passo 0.5]      -> imprime as caixas

Mac: detecção de rosto da Apple (Vision, VNDetectFaceRectanglesRequest), local e grátis. Fora do Mac: OpenCV Haar.
Caixas em pixels do vídeo: (x0, y0, x1, y1) com y para baixo, já com folga em volta (cabelo e queixo).
"""
import os, subprocess, sys, tempfile


def _caixa_vision(png, w, h):
    import Vision
    from Foundation import NSURL
    req = Vision.VNDetectFaceRectanglesRequest.alloc().init()
    hd = Vision.VNImageRequestHandler.alloc().initWithURL_options_(NSURL.fileURLWithPath_(png), None)
    ok, _ = hd.performRequests_error_([req], None)
    caixas = []
    for r in (req.results() or []) if ok else []:
        b = r.boundingBox()   # normalizado, origem embaixo à esquerda
        x0, x1 = b.origin.x * w, (b.origin.x + b.size.width) * w
        y1 = (1 - b.origin.y) * h; y0 = y1 - b.size.height * h
        caixas.append((x0, y0, x1, y1))
    return caixas


def _caixa_opencv(png):
    import cv2
    img = cv2.imread(png, cv2.IMREAD_GRAYSCALE)
    if not hasattr(cv2, "CascadeClassifier"):   # OpenCV sem detecção (relato 16/10/2026): avisa em vez de quebrar
        print("AVISO: OpenCV sem detecção de rosto; rode /ogab doctor --corrigir")
        return []
    cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    return [(x, y, x + fw, y + fh) for x, y, fw, fh in cas.detectMultiScale(img, 1.1, 5, minSize=(80, 80))]


def rostos(video, w, h, dur, passo=0.5):
    """{t: (x0,y0,x1,y1)} com a maior face de cada amostra, folga de 25% em cima (cabelo) e 15% nos lados/embaixo."""
    tmp = tempfile.mkdtemp(prefix="rosto_")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"fps={1 / passo},scale={w}:{h}",
                    os.path.join(tmp, "f_%05d.png")], check=True)
    out = {}
    for i, f in enumerate(sorted(os.listdir(tmp))):
        p = os.path.join(tmp, f); t = round(i * passo, 3)
        try:
            cx = _caixa_vision(p, w, h) if sys.platform == "darwin" else _caixa_opencv(p)
        except Exception:
            cx = _caixa_opencv(p)
        os.remove(p)
        if cx:
            x0, y0, x1, y1 = max(cx, key=lambda c: (c[2] - c[0]) * (c[3] - c[1]))
            fw, fh = x1 - x0, y1 - y0
            out[t] = (max(0, x0 - .15 * fw), max(0, y0 - .25 * fh), min(w, x1 + .15 * fw), min(h, y1 + .15 * fh))
    os.rmdir(tmp)
    return out


def no_trecho(caixas, de, ate):
    """União das caixas do rosto entre `de` e `ate` (o rosto se mexe; o elemento não pode cobrir nenhuma posição)."""
    sel = [c for t, c in caixas.items() if de - .25 <= t <= ate + .25]
    if not sel:
        return None
    return (min(c[0] for c in sel), min(c[1] for c in sel), max(c[2] for c in sel), max(c[3] for c in sel))


def bate(a, b, folga=20):
    return a and b and a[0] < b[2] + folga and b[0] < a[2] + folga and a[1] < b[3] + folga and b[1] < a[3] + folga


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from gerar import sonda
    w, h, fps, dur = sonda(a[0])
    for t, c in rostos(a[0], w, h, dur, float(a[a.index("--passo") + 1]) if "--passo" in a else .5).items():
        print(t, [round(v) for v in c])
