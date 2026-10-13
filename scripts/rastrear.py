"""Rastreia um objeto ou um rosto num vídeo e gera a trajetória (para texto/elemento que acompanha o movimento).

  python3 rastrear.py <video> --caixa X,Y,L,A [--de 2.0] [--ate 6.5] [--saida trilha.json]   # objeto (caixa no 1º quadro)
  python3 rastrear.py <video> --rosto [--de 0] [--ate 8] [--saida trilha.json]                # rosto (detecção por quadro)
  python3 rastrear.py <video> --caixa ... --previa previa.mp4                                  # vídeo com a caixa desenhada

Só usa o OpenCV que já vem instalado (sem modelos extras):
  objeto: pontos bons dentro da caixa seguidos por fluxo óptico (Lucas-Kanade); o centro anda pela mediana do
          movimento dos pontos; se os pontos se perdem, reencontra pela imagem da caixa (template).
  rosto:  detector de rosto do OpenCV a cada quadro (o maior rosto), com preenchimento nos quadros sem rosto.
Saída (JSON): {"video", "fps", "w", "h", "de", "ate", "pontos": [[t, x, y, escala], ...]} em PIXELS do vídeo e
segundos do arquivo; "escala" acompanha o tamanho (1.0 = tamanho da caixa no início). Suavizado (média móvel) para o
texto não tremer. Quem aplica: resolve_lib.texto_rastreado, premiere_lib.animar_rastreado, ae_lib (posição).
Como achar a caixa: tirar um quadro (ffmpeg -ss T -i video -frames:v 1 q.png), olhar e estimar X,Y (canto
superior esquerdo), L e A em pixels do vídeo.
"""
import json, os, sys
import cv2
import numpy as np


def _abrir(video, de):
    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        raise SystemExit(f"não abri o vídeo: {video}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC, de * 1000)
    return cap, fps


def _suavizar(pontos, janela=5):
    if len(pontos) < janela:
        return pontos
    arr = np.array(pontos, dtype=float)
    k = np.ones(janela) / janela
    out = arr.copy()
    for c in (1, 2, 3):
        pad = np.pad(arr[:, c], (janela // 2, janela // 2), mode="edge")
        out[:, c] = np.convolve(pad, k, mode="valid")
    return [[round(a, 4), round(b, 2), round(c, 2), round(d, 4)] for a, b, c, d in out.tolist()]


def objeto(video, caixa, de=0.0, ate=None, previa=None):
    cap, fps = _abrir(video, de)
    ok, q = cap.read()
    if not ok:
        raise SystemExit("vídeo sem quadros no ponto de início")
    h, w = q.shape[:2]
    x, y, L, A = caixa
    cinza = cv2.cvtColor(q, cv2.COLOR_BGR2GRAY)
    mascara = np.zeros_like(cinza); mascara[int(y):int(y + A), int(x):int(x + L)] = 255
    pts = cv2.goodFeaturesToTrack(cinza, maxCorners=120, qualityLevel=0.01, minDistance=5, mask=mascara)
    modelo = cinza[int(y):int(y + A), int(x):int(x + L)].copy()
    cx, cy, esc = x + L / 2, y + A / 2, 1.0
    pontos, t = [[round(de, 4), cx, cy, 1.0]], de
    gravador = None
    if previa:
        gravador = cv2.VideoWriter(previa, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    anterior = cinza
    while True:
        ok, q = cap.read()
        if not ok:
            break
        t += 1.0 / fps
        if ate is not None and t > ate:
            break
        cinza = cv2.cvtColor(q, cv2.COLOR_BGR2GRAY)
        novos = None
        if pts is not None and len(pts) >= 6:
            novos, st, _ = cv2.calcOpticalFlowPyrLK(anterior, cinza, pts, None, winSize=(21, 21), maxLevel=3)
            bons_n, bons_v = novos[st == 1], pts[st == 1]
            if len(bons_n) >= 6:
                d = np.median(bons_n - bons_v, axis=0)
                # escala: razão das distâncias ao centro (mediana), para o texto crescer/encolher junto
                c0, c1 = np.median(bons_v, axis=0), np.median(bons_n, axis=0)
                r0 = np.median(np.linalg.norm(bons_v - c0, axis=1)); r1 = np.median(np.linalg.norm(bons_n - c1, axis=1))
                if r0 > 1:
                    esc *= float(np.clip(r1 / r0, 0.97, 1.03))
                cx, cy = cx + float(d[0]), cy + float(d[1])
                pts = bons_n.reshape(-1, 1, 2)
            else:
                pts = None
        if pts is None or len(pts) < 6:    # perdeu: reencontra pela imagem da caixa e recomeça os pontos
            res = cv2.matchTemplate(cinza, modelo, cv2.TM_CCOEFF_NORMED)
            _, val, _, loc = cv2.minMaxLoc(res)
            if val > 0.5:
                cx, cy = loc[0] + L / 2, loc[1] + A / 2
                m = np.zeros_like(cinza); m[loc[1]:loc[1] + int(A), loc[0]:loc[0] + int(L)] = 255
                pts = cv2.goodFeaturesToTrack(cinza, maxCorners=120, qualityLevel=0.01, minDistance=5, mask=m)
        pontos.append([round(t, 4), round(cx, 2), round(cy, 2), round(esc, 4)])
        if gravador is not None:
            l2, a2 = L * esc, A * esc
            cv2.rectangle(q, (int(cx - l2 / 2), int(cy - a2 / 2)), (int(cx + l2 / 2), int(cy + a2 / 2)), (0, 200, 255), 3)
            gravador.write(q)
        anterior = cinza
    cap.release()
    if gravador is not None:
        gravador.release()
    return {"video": os.path.abspath(video), "fps": fps, "w": w, "h": h, "de": de, "ate": round(t, 4),
            "modo": "objeto", "caixa": list(caixa), "pontos": _suavizar(pontos)}


def rosto(video, de=0.0, ate=None, previa=None):
    cap, fps = _abrir(video, de)
    det = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    pontos, t, base, w, h, gravador = [], de - 1.0 / fps, None, None, None, None
    while True:
        ok, q = cap.read()
        if not ok:
            break
        t += 1.0 / fps
        if ate is not None and t > ate:
            break
        h, w = q.shape[:2]
        if previa and gravador is None:
            gravador = cv2.VideoWriter(previa, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
        peq = cv2.resize(cv2.cvtColor(q, cv2.COLOR_BGR2GRAY), None, fx=0.5, fy=0.5)
        rs = det.detectMultiScale(peq, scaleFactor=1.1, minNeighbors=6, minSize=(40, 40))
        if len(rs):
            x, y, L, A = max(rs, key=lambda r: r[2] * r[3]) * 2
            base = base or float(L)
            pontos.append([round(t, 4), float(x + L / 2), float(y + A / 2), round(L / base, 4)])
            if gravador is not None:
                cv2.rectangle(q, (int(x), int(y)), (int(x + L), int(y + A)), (0, 200, 255), 3)
        if gravador is not None:
            gravador.write(q)
    cap.release()
    if gravador is not None:
        gravador.release()
    if not pontos:
        raise SystemExit("nenhum rosto encontrado nesse trecho")
    return {"video": os.path.abspath(video), "fps": fps, "w": w, "h": h, "de": de, "ate": round(t, 4),
            "modo": "rosto", "pontos": _suavizar(pontos, 9)}


def main(a):
    if not a:
        raise SystemExit(__doc__)
    video = a[0]
    de = float(a[a.index("--de") + 1]) if "--de" in a else 0.0
    ate = float(a[a.index("--ate") + 1]) if "--ate" in a else None
    previa = a[a.index("--previa") + 1] if "--previa" in a else None
    if "--rosto" in a:
        r = rosto(video, de, ate, previa)
    elif "--caixa" in a:
        r = objeto(video, [float(v) for v in a[a.index("--caixa") + 1].split(",")], de, ate, previa)
    else:
        raise SystemExit(__doc__)
    saida = a[a.index("--saida") + 1] if "--saida" in a else os.path.splitext(video)[0] + "_trilha.json"
    json.dump(r, open(saida, "w"), indent=0)
    xs = [p[1] for p in r["pontos"]]; ys = [p[2] for p in r["pontos"]]
    print(f"{saida}: {len(r['pontos'])} quadros ({r['modo']}), x {min(xs):.0f}-{max(xs):.0f}, y {min(ys):.0f}-{max(ys):.0f}")


if __name__ == "__main__":
    main(sys.argv[1:])
