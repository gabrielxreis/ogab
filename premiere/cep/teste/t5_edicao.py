"""Segunda rodada: fps exato, colocar só vídeo / só áudio, TrackItem, volume."""
import json, os, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import premiere2019_lib as P

M = lambda n: P._abs(os.path.join(AQUI, "midia", n))
SEQ = "Reels 01"


def passo(nome, cod, **a):
    t = time.time()
    try:
        r = P.jsx(cod, nome, **a)
    except Exception as e:
        r = f"ERRO {e}"
    print(f"[{(time.time() - t) * 1000:6.0f} ms] {nome}: {json.dumps(r, ensure_ascii=False)[:900]}")
    return r


passo("fps 30 exato (videoFrameRate.ticks)", """
  var s = GAB.seq(args.seq); var st = s.getSettings();
  var fr = new Time(); fr.ticks = String(254016000000 / 30); st.videoFrameRate = fr;
  s.setSettings(st);
  return { timebase: s.timebase, fps: 254016000000 / Number(s.timebase) };
""", seq=SEQ)

passo("reflexão TrackItem e Component", """
  var c = GAB.seq(args.seq).videoTracks[0].clips[0];
  return { item: GAB.descrever(c), comp: GAB.descrever(c.components[0]), param: GAB.descrever(c.components[0].properties[0]) };
""", seq=SEQ)

passo("Track.overwriteClip na V2 (take_01 em 2 s): leva áudio junto?", """
  var s = GAB.seq(args.seq); var it = GAB.itemPorCaminho(args.a);
  s.videoTracks[1].overwriteClip(it, GAB.tempo(2));
  return GAB.retrato(s);
""", seq=SEQ, a=M("take_01.mp4"))

passo("subclipe só vídeo (createSubClip takeAudio=0) do take_02 e Track.overwriteClip em 8 s", """
  var s = GAB.seq(args.seq); var it = GAB.itemPorCaminho(args.a);
  var nome = it.name + " (video)";
  var sub = GAB.itemPorNome(nome);
  if (!sub) {
    var fim = it.getOutPoint(4);
    sub = it.createSubClip(nome, GAB.tempo(0), fim, 0, 1, 0);
  }
  if (!sub) sub = GAB.itemPorNome(nome);
  s.videoTracks[1].overwriteClip(sub, GAB.tempo(8));
  return GAB.retrato(s);
""", seq=SEQ, a=M("take_02.mp4"))

passo("Track.overwriteClip na A2 (música, in 10 s, 15 s de duração)", """
  var s = GAB.seq(args.seq); var it = GAB.itemPorCaminho(args.a);
  it.setInPoint(GAB.tempo(10), 4); it.setOutPoint(GAB.tempo(25), 4);
  s.audioTracks[1].overwriteClip(it, GAB.tempo(0));
  it.clearInPoint(4); it.clearOutPoint(4);
  var c = s.audioTracks[1].clips[0];
  return { inicio: c.start.seconds, fim: c.end.seconds, in_: c.inPoint.seconds };
""", seq=SEQ, a=M("musica.wav"))

passo("Track.overwriteClip na V3 (motion MOV sem áudio, 1 s)", """
  var s = GAB.seq(args.seq); var it = GAB.itemPorCaminho(args.a);
  s.videoTracks[2].overwriteClip(it, GAB.tempo(1));
  return GAB.retrato(s);
""", seq=SEQ, a=M("motion.mov"))

passo("componentes: música e take", """
  var s = GAB.seq(args.seq), r = {};
  var ver = function (c) { var l = []; for (var i = 0; i < c.components.numItems; i++) { var comp = c.components[i], ps = [];
    for (var j = 0; j < comp.properties.numItems; j++) { var pr = comp.properties[j], v = null; try { v = pr.getValue(); } catch (e) {} ps.push(pr.displayName + "=" + v); }
    l.push(comp.displayName + " [" + comp.matchName + "]: " + ps.join(", ")); } return l; };
  r.musica = ver(s.audioTracks[1].clips[0]); r.take = ver(s.videoTracks[1].clips[0]);
  return r;
""", seq=SEQ)
