"""legenda_gab: 3 falas (uma com duas linhas) e conferência do centro do bloco em Y 724 (1196 px do topo)."""
import os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import premiere2019_lib as P
from PIL import Image

srt = os.path.join(AQUI, "midia", "legenda_gab.srt")
with open(srt, "w", encoding="utf-8") as f:
    f.write("1\n00:00:00,500 --> 00:00:02,000\nnão foi o movimento\n\n2\n00:00:02,000 --> 00:00:03,500\nfoi o processo\n\n"
            "3\n00:00:03,500 --> 00:00:05,000\nque você repetiu\ntodo dia\n\n")
P.criar_sequencia("Legenda GAB 01")
if not P.retrato("Legenda GAB 01")["video"][0]:
    P.colocar("Legenda GAB 01", os.path.join(AQUI, "midia", "bruto.mp4"), 0)
P.jsx("var s = GAB.seq('Legenda GAB 01'); if (s.videoTracks.numTracks > 3) { var tr = s.videoTracks[3]; "
      "for (var i = tr.clips.numItems - 1; i >= 0; i--) tr.clips[i].remove(false, false); } return 1;")
print(P.legenda_gab("Legenda GAB 01", srt, trilha=3))
for t in (1.0, 4.0):
    png = P.quadro("Legenda GAB 01", t, os.path.join(AQUI, "render", f"legenda_gab_{t}.png"))
    im = Image.open(png).convert("RGB")
    ys = [y for y in range(1050, 1350) for x in range(300, 780, 2) if min(im.getpixel((x, y))) > 245]
    print(f"{t} s: bloco {min(ys)}-{max(ys)}, centro {(min(ys) + max(ys)) / 2} (alvo 1196)")
