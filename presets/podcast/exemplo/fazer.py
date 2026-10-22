"""Mídia do exemplo do preset PODCAST: duas pessoas ILUSTRADAS (ninguém real no repositório público).

  python3 presets/podcast/exemplo/fazer.py

Grava em exemplo/midia/:
  falante_a.png         foto parada 1080x1350 (testa imagem + legenda em posição fixa da metade)
  falante_b.mp4         "câmera" 1920x1080 horizontal, 7 s, cabeça balançando devagar e boca mexendo na fala
                        (testa vídeo + recorte cover + legenda acompanhando a cabeça)
  falante_b_trilha.json trilha sintética no MESMO formato do scripts/rastrear.py --rosto (pixels do vídeo de origem)
Os tempos da boca do B vêm das palavras do plano.json, então rodar de novo se mudar a fala.
"""
import json, math, os, subprocess
from PIL import Image, ImageDraw, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__)); MIDIA = os.path.join(AQUI, "midia")
SS = 2   # supersample: desenha em 2x e reduz (borda lisa)


def fundo(w, h, topo, base, luz):
    """Estúdio: degradê vertical, luz suave atrás e dois painéis acústicos."""
    im = Image.new("RGB", (w, h))
    px = ImageDraw.Draw(im)
    for y in range(h):
        k = y / (h - 1)
        px.line((0, y, w, y), fill=tuple(round(topo[i] + (base[i] - topo[i]) * k) for i in range(3)))
    brilho = Image.new("L", (w, h), 0)
    ImageDraw.Draw(brilho).ellipse((w * .2, -h * .1, w * .8, h * .7), fill=70)
    brilho = brilho.filter(ImageFilter.GaussianBlur(w * .08))
    im = Image.composite(Image.new("RGB", (w, h), luz), im, brilho)
    d = ImageDraw.Draw(im)
    for x0 in (.06, .78):
        for j in range(3):
            d.rounded_rectangle((w * x0, h * (.12 + j * .17), w * (x0 + .16), h * (.12 + j * .17) + h * .14), radius=w * .01,
                                fill=tuple(min(255, c + 14) for c in base), outline=tuple(min(255, c + 26) for c in base), width=max(2, w // 400))
    return im


def pessoa(d, cx, cy, r, pele, cabelo, roupa, boca=0.0, fone=(40, 40, 46)):
    """Busto simples: ombros, pescoço, cabeça, cabelo, fone e microfone. cy = centro da cabeça, r = raio."""
    d.rounded_rectangle((cx - r * 2.3, cy + r * 1.45, cx + r * 2.3, cy + r * 5), radius=r * .9, fill=roupa)       # ombros
    d.rectangle((cx - r * .38, cy + r * .7, cx + r * .38, cy + r * 1.6), fill=tuple(max(0, c - 18) for c in pele))  # pescoço
    d.ellipse((cx - r * .9, cy - r * 1.1, cx + r * .9, cy + r * 1.05), fill=pele)                                   # rosto
    d.chord((cx - r * .98, cy - r * 1.22, cx + r * .98, cy + r * .5), 180, 360, fill=cabelo)                         # cabelo
    for s in (-1, 1):                                                                                               # olhos
        d.ellipse((cx + s * r * .33 - r * .07, cy - r * .02, cx + s * r * .33 + r * .07, cy + r * .12), fill=(34, 30, 30))
    a = r * (.05 + .16 * boca)                                                                                      # boca
    d.rounded_rectangle((cx - r * .2, cy + r * .48 - a / 2, cx + r * .2, cy + r * .48 + a / 2), radius=a / 2, fill=(120, 48, 52))
    d.arc((cx - r * 1.08, cy - r * 1.35, cx + r * 1.08, cy + r * .6), 190, 350, fill=fone, width=round(r * .16))     # fone
    for s in (-1, 1):
        d.rounded_rectangle((cx + s * r * .98 - r * .16, cy - r * .2, cx + s * r * .98 + r * .16, cy + r * .45), radius=r * .1, fill=fone)


def microfone(d, x, y, r, lado=1):
    d.line((x + lado * r * 2.6, y + r * .2, x + lado * r * .5, y + r * .95), fill=(70, 70, 78), width=round(r * .12))
    d.rounded_rectangle((x - r * .3, y + r * .55, x + r * .62, y + r * 1.35), radius=r * .4, fill=(28, 28, 32))


def falante_a():
    w, h = 1080, 1350
    im = fundo(w * SS, h * SS, (52, 40, 34), (22, 18, 16), (150, 104, 62))
    d = ImageDraw.Draw(im)
    pessoa(d, 540 * SS, 470 * SS, 118 * SS, (224, 178, 142), (58, 36, 26), (52, 62, 80))
    microfone(d, 380 * SS, 470 * SS, 118 * SS, -1)
    im.resize((w, h), Image.LANCZOS).save(os.path.join(MIDIA, "falante_a.png"))


def falante_b(palavras, dur=7.0, fps=30):
    w, h = 1920, 1080
    base = fundo(w * SS, h * SS, (24, 40, 44), (10, 18, 20), (60, 120, 120))
    fala = [p for p in palavras if p["falante"] == 1]
    r0, pts = 130, []
    out = os.path.join(MIDIA, "falante_b.mp4")
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                           "-r", str(fps), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "26", "-preset", "slow", out],
                          stdin=subprocess.PIPE)
    for i in range(int(dur * fps)):
        t = i / fps
        cx = 960 + 70 * math.sin(t * .75) + 18 * math.sin(t * 1.9)        # balanço calmo de cabeça
        cy = 420 + 14 * math.sin(t * 1.1 + .6)
        r = r0 * (1 + .025 * math.sin(t * .5))                             # chega um pouco mais perto e volta
        boca = 0.0
        for p in fala:
            if p["ini"] <= t <= p["fim"]:
                boca = abs(math.sin((t - p["ini"]) / max(.08, p["fim"] - p["ini"]) * math.pi * 2)) * .9 + .1
        im = base.copy(); d = ImageDraw.Draw(im)
        pessoa(d, cx * SS, cy * SS, r * SS, (176, 124, 92), (24, 22, 24), (96, 90, 84), boca)
        microfone(d, (cx + 170) * SS, cy * SS, r * SS)
        ff.stdin.write(im.resize((w, h), Image.LANCZOS).tobytes())
        # trilha: centro da caixa do rosto (como o detector entrega) e escala relativa ao 1º quadro
        pts.append([round(t, 4), round(cx, 2), round(cy + r * .05, 2), round(r / r0, 4)])
    ff.stdin.close(); ff.wait()
    json.dump({"video": "falante_b.mp4", "fps": fps, "w": w, "h": h, "de": 0.0, "ate": round(dur, 4), "modo": "rosto",
               "sintetica": True, "pontos": pts}, open(os.path.join(MIDIA, "falante_b_trilha.json"), "w"), indent=0)


if __name__ == "__main__":
    os.makedirs(MIDIA, exist_ok=True)
    plano = json.load(open(os.path.join(AQUI, "plano.json"), encoding="utf-8"))
    falante_a(); falante_b(plano["palavras"], plano.get("dur", 7.0))
    print("ok", MIDIA, sorted(os.listdir(MIDIA)))
