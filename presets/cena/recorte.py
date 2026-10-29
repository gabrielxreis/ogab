"""Recorte da pessoa (para texto ATRÁS dela, órbita, tela verde): vídeo -> MOV ProRes 4444 só com a pessoa (alfa).

  python3 recorte.py video.mp4 saida_recorte.mov [--de 0 --ate 30] [--w 1080] [--qualidade precisa|equilibrada|rapida]

Mac: segmentação de pessoas da Apple (Vision, VNGeneratePersonSegmentationRequest), local e grátis.
Windows/sem Vision: rembg (pip install rembg; mais lento).
A máscara é suavizada (borda macia) e estabilizada no tempo (média com o quadro anterior) para não "ferver".
"""
import os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageFilter


def _mascara_vision(caminho_png, qualidade):
    import Quartz, Vision
    from Foundation import NSURL
    url = NSURL.fileURLWithPath_(caminho_png)
    req = Vision.VNGeneratePersonSegmentationRequest.alloc().initWithCompletionHandler_(None)
    req.setQualityLevel_({"precisa": 0, "equilibrada": 1, "rapida": 2}[qualidade])   # accurate/balanced/fast
    req.setOutputPixelFormat_(1278226488)   # kCVPixelFormatType_OneComponent8 ('L008')
    h = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, None)
    ok, err = h.performRequests_error_([req], None)
    if not ok:
        raise RuntimeError(f"Vision falhou: {err}")
    buf = req.results()[0].pixelBuffer()
    Quartz.CVPixelBufferLockBaseAddress(buf, 1)
    w, hh = Quartz.CVPixelBufferGetWidth(buf), Quartz.CVPixelBufferGetHeight(buf)
    linha = Quartz.CVPixelBufferGetBytesPerRow(buf)
    base = Quartz.CVPixelBufferGetBaseAddress(buf)
    dados = np.frombuffer(base.as_buffer(linha * hh), dtype=np.uint8).reshape(hh, linha)[:, :w].copy()
    Quartz.CVPixelBufferUnlockBaseAddress(buf, 1)
    return Image.fromarray(dados, "L")


def _mascara_rembg(img):
    from rembg import remove, new_session
    global _SESS
    _SESS = globals().get("_SESS") or new_session("u2net_human_seg")
    return remove(img, session=_SESS, only_mask=True)


def recortar(video, saida, de=0.0, ate=None, w=1080, qualidade="equilibrada", fps=None):
    tmp = tempfile.mkdtemp(prefix="recorte_")
    try:
        corte = ["-ss", str(de)] + (["-to", str(ate)] if ate else [])
        vf = f"scale={w}:-2" + (f",fps={fps}" if fps else "")
        subprocess.run(["ffmpeg", "-v", "error", "-y"] + corte + ["-i", video, "-vf", vf, os.path.join(tmp, "q_%05d.png")], check=True)
        quadros = sorted(f for f in os.listdir(tmp) if f.startswith("q_"))
        usa_vision = sys.platform == "darwin"
        anterior = None
        for i, f in enumerate(quadros):
            p = os.path.join(tmp, f); img = Image.open(p).convert("RGB")
            m = _mascara_vision(p, qualidade) if usa_vision else _mascara_rembg(img)
            m = m.resize(img.size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(1.2))
            a = np.asarray(m, dtype=np.float32)
            if anterior is not None:
                a = 0.65 * a + 0.35 * anterior        # estabiliza no tempo (borda não ferve)
            anterior = a
            rgba = img.copy(); rgba.putalpha(Image.fromarray(a.clip(0, 255).astype(np.uint8)))
            rgba.save(os.path.join(tmp, f"r_{i:05d}.png"))
            if i % 100 == 0:
                print(f"  recorte {i}/{len(quadros)}", flush=True)
        from fractions import Fraction
        r = fps or float(Fraction(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                                 "stream=r_frame_rate", "-of", "csv=p=0", video], capture_output=True, text=True).stdout.strip().strip(",").split(",")[0]))
        # bt709 na conversão e na marcação: sem isso o ffmpeg converte em BT.601 e o DaVinci lê como 709 (rosto mais quente que o take, relato 24/10/2026)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(r), "-i", os.path.join(tmp, "r_%05d.png"),
                        "-vf", "scale=out_color_matrix=bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                        "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16", saida], check=True)
        return saida, len(quadros), r
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    arg = lambda n, p=None: a[a.index(n) + 1] if n in a else p
    print(recortar(a[0], a[1], float(arg("--de", 0)), float(arg("--ate")) if arg("--ate") else None, int(arg("--w", 1080)),
                   arg("--qualidade", "equilibrada")))
