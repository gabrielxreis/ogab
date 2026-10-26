"""Timeline inteira por XML do Final Cut 7 (xmeml): gera, importa, confere trilhas/volume/escala, tempo total."""
import json, os, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import premiere2019_lib as P

M = lambda n: os.path.join(AQUI, "midia", n)
nome = "XML %s" % time.strftime("%H%M%S")
plano = {
    "nome": nome, "w": 1080, "h": 1920, "fps": 30,
    "video": [
        [{"arquivo": M("bruto.mp4"), "inicio": 0, "ate": 10}],
        [{"arquivo": M("take_01.mp4"), "inicio": 2, "ate": 2, "escala": 177.78},
         {"arquivo": M("take_02.mp4"), "inicio": 5, "de": 1, "ate": 4, "escala": 177.78}],
        [{"arquivo": M("motion2.mov"), "inicio": 8}],
    ],
    "audio": [
        [{"arquivo": M("bruto.mp4"), "inicio": 0, "ate": 10}],
        [{"arquivo": M("musica.wav"), "inicio": 0, "de": 5, "ate": 15, "db": -10}],
    ],
}
t = time.time()
xml = P.xmeml(plano, os.path.join(AQUI, "render", "timeline.xml"))
t_xml = time.time() - t
t = time.time()
print("sequências novas:", P.importar_xml(xml), f"(gerar {t_xml:.2f} s, importar {time.time() - t:.2f} s)")
r = P.retrato(nome)
for lado in ("video", "audio"):
    for i, tr in enumerate(r[lado]):
        if tr: print(f"  {lado[0].upper()}{i + 1}:", [(c["nome"], round(c["inicio"], 2), round(c["fim"], 2), round(c["in_"], 2)) for c in tr])
print("ajustes:", P.jsx("""
  var s = GAB.seq(args.n), mu = GAB.clipeEm(s.audioTracks[1], 0), tk = GAB.clipeEm(s.videoTracks[1], 2);
  return { quadro: [s.frameSizeHorizontal, s.frameSizeVertical], fps: GAB.TICKS / Number(s.timebase),
           nivelMusica: GAB.nivel(mu).getValue(), escalaTake: tk.components[1].properties[1].getValue() };
""", n=nome))
print(P.quadro(nome, 6.0, os.path.join(AQUI, "render", "xmeml_6s.png")))
