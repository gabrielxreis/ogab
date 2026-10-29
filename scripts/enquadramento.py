"""Confere se a PESSOA está inteira e centralizada em cada take do vídeo pronto (regra do usuário, 17/10/2026:
"precisa centralizar o personagem, os vídeos o personagem tá cortado, isso tem que ser verificado na skill").

  python3 enquadramento.py <video.mp4> "<timeline>" [--trilhas 1,2] [--folha saida.jpg]

Para cada take das trilhas (padrão V1 e V2, sem motions), pega o quadro do meio NO VÍDEO RENDERIZADO (prévia ou export),
acha os rostos (Vision da Apple; fora do Mac, OpenCV) e reprova quando o rosto principal:
  - encosta na borda esquerda/direita/topo (cortado),
  - ocupa mais de 80% da largura (apertado demais: a cabeça e o queixo saem do quadro),
  - tem o centro a mais de 15% da largura fora do meio (pessoa sobrando de lado).
Sai com código 1 se algum take reprovar e imprime a correção: material 4:3 / baixa resolução / close apertado ->
MOLDURA (fundo na V1 e o take em Fit com zoom leve, ver takes.md); 16:9 com pessoa de lado -> Pan para o centro.
Take sem rosto não é avaliado (conferir na folha). --folha grava os quadros com a caixa do rosto para olhar.
"""
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BORDA, LARG_MAX, DESVIO = 6, 0.80, 0.30   # desvio: só reprova pessoa encostando no canto (composição de lado é ok)


def rostos(png, w, h):
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "presets", "cena"))
        from rosto import _caixa_vision
        return _caixa_vision(png, w, h)
    except Exception:
        import cv2
        g = cv2.cvtColor(cv2.imread(png), cv2.COLOR_BGR2GRAY)
        cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        return [(x, y, x + a, y + b) for x, y, a, b in cas.detectMultiScale(g, 1.1, 6, minSize=(int(w * .12),) * 2)]


def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); sys.exit(2)
    video, nome = a[0], a[1]
    trilhas = [int(x) for x in a[a.index("--trilhas") + 1].split(",")] if "--trilhas" in a else [1, 2]
    folha = a[a.index("--folha") + 1] if "--folha" in a else None
    import resolve_lib as L
    r = L.conectar(abrir=False); p = r.GetProjectManager().GetCurrentProject()
    t = next(p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if p.GetTimelineByIndex(i).GetName() == nome)
    F, S = L.fps_tl(t), t.GetStartFrame()
    # o que está NO TOPO em cada instante: take da trilha mais alta (motions fora)
    pedacos = []
    for k in trilhas:
        for x in t.GetItemListInTrack("video", k) or []:
            m = x.GetMediaPoolItem(); fp = (m.GetClipProperty("File Path") if m else "") or ""
            if not m or "/motions/" in fp or not x.GetClipEnabled(): continue
            pedacos.append((k, (x.GetStart() - S) / F, (x.GetEnd() - S) / F, x.GetName()))
    mot = [((x.GetStart() - S) / F, (x.GetEnd() - S) / F) for k in range(1, t.GetTrackCount("video") + 1)
           if "MOTION" in (t.GetTrackName("video", k) or "").upper() for x in t.GetItemListInTrack("video", k) or []]
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", video], capture_output=True, text=True).stdout
    w, h = [int(v) for v in __import__("re").findall(r"\d+", out)[:2]]   # ffprobe repete linha ou quebra "1920\n\n1080" (MP4 do DaVinci 21)
    tmp = tempfile.mkdtemp(); ruins = []; imgs = []
    for k, ini, fim, nm in sorted(pedacos, key=lambda z: z[1]):
        meio = (ini + fim) / 2
        if any(a0 <= meio < a1 for a0, a1 in mot): continue                              # coberto por motion
        if any(k2 > k and i2 <= meio < f2 for k2, i2, f2, _ in pedacos): continue        # coberto por take acima
        png = os.path.join(tmp, f"{meio:07.2f}.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{meio:.3f}", "-i", video, "-frames:v", "1", png])
        if not os.path.exists(png): continue
        cx = rostos(png, w, h)
        imgs.append((png, cx, nm, meio))
        if not cx: continue
        x0, y0, x1, y1 = max(cx, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
        motivo = []
        if x0 <= BORDA or x1 >= w - BORDA or y0 <= BORDA: motivo.append("rosto cortado na borda")
        if (x1 - x0) > LARG_MAX * w: motivo.append(f"apertado ({(x1 - x0) / w:.0%} da largura)")
        if abs((x0 + x1) / 2 - w / 2) > DESVIO * w: motivo.append(f"fora do centro ({(x0 + x1) / 2 - w / 2:+.0f} px)")
        if motivo: ruins.append((round(meio, 2), f"V{k}", nm, ", ".join(motivo)))
    if folha and imgs:
        from PIL import Image, ImageDraw
        th = []
        for png, cx, nm, meio in imgs:
            im = Image.open(png).convert("RGB"); d = ImageDraw.Draw(im)
            for b in cx: d.rectangle(b, outline="red", width=8)
            d.rectangle([0, 0, 360, 60], fill="black"); d.text((10, 10), f"{meio:.1f}s {nm[:24]}", fill="yellow")
            th.append(im.resize((216, int(216 * h / w))))
        n = 8; o = Image.new("RGB", (216 * n, th[0].size[1] * ((len(th) + n - 1) // n)))
        for i, im in enumerate(th): o.paste(im, ((i % n) * 216, (i // n) * th[0].size[1]))
        o.save(folha, quality=80); print("folha:", folha)
    for z in ruins: print("REPROVADO", *z)
    print(f"{nome}: {len(imgs)} takes conferidos, {len(ruins)} reprovados")
    if ruins:
        print("Correção: 4:3/baixa resolução/close -> moldura (fundo na V1, take em Fit + zoom leve); 16:9 de lado -> Pan para o centro.")
    sys.exit(1 if ruins else 0)


if __name__ == "__main__":
    main()
