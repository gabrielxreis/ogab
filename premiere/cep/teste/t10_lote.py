"""Montagem de uma timeline inteira num comando só (lote)."""
import json, os, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import premiere2019_lib as P

SEQ = "Reels 01"
M = lambda n: P._abs(os.path.join(AQUI, "midia", n))
PRE = r"C:\Program Files\Adobe\Adobe Premiere Pro CC 2019\Settings\SequencePresets\Digital SLR\1080p\DSLR 1080p30.sqpreset"


def passo(nome, cod, **a):
    t = time.time()
    try:
        r = P.jsx(cod, nome, **a)
    except Exception as e:
        r = f"ERRO {e}"
    print(f"[{(time.time() - t) * 1000:6.0f} ms] {nome}: {json.dumps(r, ensure_ascii=False)[:1500]}")
    return r


# Montagem de uma timeline inteira em UM comando (o jeito rápido): sequência nova, ajustes, 6 clipes, volume, marcador.
plano = dict(
    seqnome="Lote 01", pre=PRE,
    v1=M("bruto.mp4"), musica=M("musica.wav"), motion=M("motion.mov"),
    takes=[[M("take_01.mp4"), 2.0, 4.0], [M("take_02.mp4"), 6.0, 8.5], [M("take_01.mp4"), 12.0, 14.0]],
    db_musica=-10, marcadores=[[0, "GANCHO"], [17, "CTA"]],
)
t = time.time()
passo("LOTE: timeline inteira num comando", """
  var p = GAB.proj();
  try { GAB.seq(args.seqnome); return "já existe"; } catch (e) {}
  app.enableQE(); qe.project.newSequence(args.seqnome, args.pre);
  var s = GAB.seq(args.seqnome), st = s.getSettings();
  st.videoFrameWidth = 1080; st.videoFrameHeight = 1920;
  var fr = new Time(); fr.ticks = String(254016000000 / 30); st.videoFrameRate = fr; s.setSettings(st);
  GAB.garantirTrilhas(s, 3, 2);
  var bruto = GAB.importar([args.v1], "Footages")[0];
  s.overwriteClip(bruto, GAB.tempo(0), 0, 0);
  // takes só vídeo na V2: subclipe sem áudio, escala para preencher
  for (var i = 0; i < args.takes.length; i++) {
    var tk = args.takes[i], it = GAB.importar([tk[0]], "BRoll")[0];
    it.clearInPoint(4); it.clearOutPoint(4);
    var nome = it.name + " (video)", sub = GAB.itemPorNome(nome);
    if (!sub) { it.createSubClip(nome, GAB.tempo(0), it.getOutPoint(4), 0, 1, 0); sub = GAB.itemPorNome(nome); }
    sub.setInPoint(GAB.tempo(0), 4); sub.setOutPoint(GAB.tempo(tk[2] - tk[1]), 4);
    s.videoTracks[1].overwriteClip(sub, GAB.tempo(tk[1]));
    sub.clearInPoint(4); sub.clearOutPoint(4);
    var c = GAB.clipeEm(s.videoTracks[1], tk[1]);
    c.components[1].properties[1].setValue(Math.max(1080 / 1920, 1920 / 1080) * 100, true);
  }
  // música na A2 com -10 dB (escala do 2019: 0,5 = 0 dB)
  var mu = GAB.importar([args.musica], "Musicas")[0];
  mu.setInPoint(GAB.tempo(0), 4); mu.setOutPoint(GAB.tempo(20), 4);
  s.audioTracks[1].overwriteClip(mu, GAB.tempo(0)); mu.clearInPoint(4); mu.clearOutPoint(4);
  GAB.clipeEm(s.audioTracks[1], 0).components[0].properties[1].setValue(0.5 * Math.pow(10, args.db_musica / 20), true);
  // motion na V3
  var mo = GAB.importar([args.motion], "Motions")[0];
  s.videoTracks[2].overwriteClip(mo, GAB.tempo(0.5));
  for (var m = 0; m < args.marcadores.length; m++) { var mk = s.markers.createMarker(args.marcadores[m][0]); mk.name = args.marcadores[m][1]; }
  p.save();
  return GAB.retrato(s);
""", **plano)
print(f"lote total: {time.time() - t:.2f} s")
