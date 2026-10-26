"""Legenda no 13.1.5: (1) o que a QE deixa mudar nas Open Captions; (2) calibra o título nativo no estilo GAB USA
(Poppins Bold, caixa alta, 414 px de largura para "NÃO FOI O MOVIMENTO" no 1080x1920, centro em Y 724 de baixo)."""
import json, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import premiere2019_lib as P
from PIL import Image

R = os.path.join(AQUI, "render")
pre = """
  app.enableQE(); var it = null;
  for (var b = 0; b < qe.project.numBins; b++) { var bin = qe.project.getBinAt(b);
    for (var i = 0; i < bin.numItems; i++) if (bin.getItemAt(i).name === "legenda.srt") it = bin.getItemAt(i); }
  var st = it.clip.getCaptioningStreamAt(0), c = st.getCaptionAt(0);
"""
print("antes:", P.jsx(pre + "return [c.positionX(), c.positionY(), c.anchor(), c.alignment(), String(c.textColor()), String(c.backgroundColor())];"))
for cod in ["c.setPositionY(0.3)", "c.setTextColor(16776960)", "c.setBackgroundColor(0)"]:
    try:
        P.jsx(pre + cod + "; return true;"); print("ok", cod)
    except Exception as e:
        print("ERRO", cod, e)
print("depois:", P.jsx(pre + "return [c.positionX(), c.positionY(), c.anchor(), c.alignment(), String(c.textColor()), String(c.backgroundColor())];"))


def largura_texto(png, y_centro):
    """Largura (px) dos pixels brancos numa faixa em volta de y_centro (o fundo das barras não é branco puro)."""
    im = Image.open(png).convert("RGB"); W, H = im.size
    xs = [x for y in range(int(y_centro) - 30, int(y_centro) + 30) for x in range(W)
          if im.getpixel((x, y))[0] > 245 and im.getpixel((x, y))[1] > 245 and im.getpixel((x, y))[2] > 245]
    return (max(xs) - min(xs) + 1) if xs else 0


# Sequência limpa (fundo preto) para medir
P.criar_sequencia("Cal Legenda")
y_topo = 1920 - 724
tam = 60
for rodada in range(4):
    P.jsx("var s = GAB.seq('Cal Legenda'); for (var t = 0; t < s.videoTracks.numTracks; t++) for (var i = s.videoTracks[t].clips.numItems - 1; i >= 0; i--) s.videoTracks[t].clips[i].remove(false, false); return 1;")
    P.titulo("Cal Legenda", "NÃO FOI O MOVIMENTO", 0.0, 2.0, trilha=0, tamanho=tam, y=y_topo)
    png = P.quadro("Cal Legenda", 1.0, os.path.join(R, f"cal_legenda_{rodada}.png"))
    w = largura_texto(png, y_topo)
    print(f"tamanho {tam}: largura {w} px (alvo 414)")
    if not w or abs(w - 414) <= 3:
        break
    tam = round(tam * 414 / w, 2)
