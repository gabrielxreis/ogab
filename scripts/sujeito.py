#!/usr/bin/env python3
"""Cliques do Magic Mask a partir do recorte de sujeito da Apple (pessoa + cabelo + objetos que ela segura).

  python3 sujeito.py quadro.png [saida.json]

Mac 14+: Vision VNGenerateForegroundInstanceMaskRequest (o mesmo "copiar sujeito" do Fotos), local e grátis.
Devolve {"pos": [[x, y], ...], "neg": [...]} em coordenadas do Fusion (0-1, y de baixo para cima):
positivos em grade por DENTRO do sujeito (encolhido, longe da borda) + 1 no topo da cabeça (cabelo);
negativos em grade no fundo, longe da pessoa. Cada ponto vira um clique (traço de 1 ponto) no Magic Mask,
igual ao que o usuário faz na tela.
"""
import json, sys


def mascara_sujeito(png):
    """Máscara booleana (altura x largura) de todos os sujeitos do quadro."""
    import numpy as np
    import Quartz, Vision
    from Foundation import NSURL
    src = Quartz.CGImageSourceCreateWithURL(NSURL.fileURLWithPath_(png), None)
    cg = Quartz.CGImageSourceCreateImageAtIndex(src, 0, None)
    req = Vision.VNGenerateForegroundInstanceMaskRequest.alloc().init()
    h = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg, None)
    ok, _ = h.performRequests_error_([req], None)
    if not ok or not req.results():
        raise RuntimeError("a Apple não achou sujeito no quadro (pessoa fora do quadro ou desfocada)")
    res = req.results()[0]
    buf, _ = res.generateScaledMaskForImageForInstances_fromRequestHandler_error_(res.allInstances(), h, None)
    Quartz.CVPixelBufferLockBaseAddress(buf, 0)
    try:
        w, hh = Quartz.CVPixelBufferGetWidth(buf), Quartz.CVPixelBufferGetHeight(buf)
        bpr = Quartz.CVPixelBufferGetBytesPerRow(buf)
        raw = Quartz.CVPixelBufferGetBaseAddress(buf).as_buffer(bpr * hh)
        return np.frombuffer(raw, dtype=np.float32).reshape(hh, bpr // 4)[:, :w] > 0.5
    finally:
        Quartz.CVPixelBufferUnlockBaseAddress(buf, 0)


def pontos(png, passo_pos=(120, 140), passo_neg=150):
    import numpy as np
    from PIL import Image, ImageFilter
    m = mascara_sujeito(png); H, W = m.shape
    img = Image.fromarray((m * 255).astype("uint8"))
    dentro = np.array(img.filter(ImageFilter.MinFilter(29))) > 127      # ~14 px para dentro da borda
    fora = np.array(img.filter(ImageFilter.MaxFilter(81))) < 128        # ~40 px longe da pessoa
    pos = [(x, y) for y in range(40, H, passo_pos[1]) for x in range(40, W, passo_pos[0]) if dentro[y, x]]
    neg = [(x, y) for y in range(40, H, passo_neg) for x in range(40, W, passo_neg) if fora[y, x]]
    ys, xs = np.nonzero(dentro)
    if len(ys):   # cabelo: ponto no alto da cabeça
        topo = ys.min(); pos.append((int(np.median(xs[ys < topo + 25])), int(topo) + 8))
    n = lambda p: [round(p[0] / W, 4), round(1 - p[1] / H, 4)]
    return {"pos": [n(p) for p in pos], "neg": [n(p) for p in neg], "cobertura": round(float(m.mean()), 3)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    d = pontos(sys.argv[1])
    txt = json.dumps(d)
    if len(sys.argv) > 2: open(sys.argv[2], "w").write(txt)
    print(f"{len(d['pos'])} positivos, {len(d['neg'])} negativos, sujeito {d['cobertura']:.0%} do quadro")
