"""Experimentos de edição no Premiere 2019 pela ponte: cada bloco testa um comportamento e imprime o resultado."""
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
    print(f"[{(time.time() - t) * 1000:6.0f} ms] {nome}: {json.dumps(r, ensure_ascii=False)[:600]}")
    return r


passo("ajustar 1080x1920 30fps", """
  var s = GAB.seq(args.seq); var st = s.getSettings();
  st.videoFrameWidth = 1080; st.videoFrameHeight = 1920;
  s.setSettings(st);
  var st2 = s.getSettings();
  return { w: s.frameSizeHorizontal, h: s.frameSizeVertical, fps: st2.videoFrameRate.seconds ? 1 / st2.videoFrameRate.seconds : null, timebase: s.timebase };
""", seq=SEQ)

passo("importar tudo", """
  var r = GAB.importar(args.arqs, "Footages"); var n = []; for (var i = 0; i < r.length; i++) n.push(r[i].name); return n;
""", arqs=[M("bruto.mp4"), M("take_01.mp4"), M("take_02.mp4"), M("musica.wav"), M("motion.mov")])

passo("V1/A1: bruto em 0 (overwriteClip da Sequence)", """
  var s = GAB.seq(args.seq); var it = GAB.itemPorCaminho(args.a);
  s.overwriteClip(it, GAB.tempo(0), 0, 0);
  return GAB.retrato(s);
""", seq=SEQ, a=M("bruto.mp4"))

passo("V2 só vídeo: take_01 em 2 s com audioTrackIndex -1", """
  var s = GAB.seq(args.seq); var it = GAB.itemPorCaminho(args.a);
  s.overwriteClip(it, GAB.tempo(2), 1, -1);
  return GAB.retrato(s);
""", seq=SEQ, a=M("take_01.mp4"))

passo("V2 take_02 em 8 s, só 1,5 s a partir de 2 s da fonte (in/out no item)", """
  var s = GAB.seq(args.seq); var it = GAB.itemPorCaminho(args.a);
  it.setInPoint(GAB.tempo(2), 4); it.setOutPoint(GAB.tempo(3.5), 4);
  s.overwriteClip(it, GAB.tempo(8), 1, -1);
  it.clearInPoint(4); it.clearOutPoint(4);
  return GAB.retrato(s);
""", seq=SEQ, a=M("take_02.mp4"))

passo("A2 música com entrada em 10 s da faixa, de 0 a 15 s", """
  var s = GAB.seq(args.seq); var it = GAB.itemPorCaminho(args.a);
  it.setInPoint(GAB.tempo(10), 4); it.setOutPoint(GAB.tempo(25), 4);
  s.overwriteClip(it, GAB.tempo(0), -1, 1);
  it.clearInPoint(4); it.clearOutPoint(4);
  var c = s.audioTracks[1].clips[0];
  return { inicio: c.start.seconds, fim: c.end.seconds, in_: c.inPoint.seconds, trilhasA: s.audioTracks.numTracks };
""", seq=SEQ, a=M("musica.wav"))

passo("V3 motion MOV (sem áudio) em 1 s: trilha que não existe", """
  var s = GAB.seq(args.seq); var it = GAB.itemPorCaminho(args.a);
  var antes = s.videoTracks.numTracks;
  s.overwriteClip(it, GAB.tempo(1), 2, -1);
  return { antes: antes, depois: s.videoTracks.numTracks, v3: s.videoTracks.numTracks > 2 ? s.videoTracks[2].clips.numItems : null };
""", seq=SEQ, a=M("motion.mov"))

passo("componentes do clipe de música (volume)", """
  var c = GAB.seq(args.seq).audioTracks[1].clips[0]; var r = [];
  for (var i = 0; i < c.components.numItems; i++) {
    var comp = c.components[i], ps = [];
    for (var j = 0; j < comp.properties.numItems; j++) { var pr = comp.properties[j]; var v = null; try { v = pr.getValue(); } catch (e) {} ps.push(pr.displayName + "=" + v); }
    r.push(comp.displayName + " [" + comp.matchName + "]: " + ps.join(", "));
  }
  return r;
""", seq=SEQ)

passo("componentes do take (Motion, Opacity)", """
  var c = GAB.seq(args.seq).videoTracks[1].clips[0]; var r = [];
  for (var i = 0; i < c.components.numItems; i++) {
    var comp = c.components[i], ps = [];
    for (var j = 0; j < comp.properties.numItems; j++) { var pr = comp.properties[j]; var v = null; try { v = pr.getValue(); } catch (e) {} ps.push(pr.displayName + "=" + v); }
    r.push(comp.displayName + " [" + comp.matchName + "]: " + ps.join(", "));
  }
  return r;
""", seq=SEQ)

passo("volume -10 dB com fade in 0,5 e fade out 2,5 (keyframes)", """
  var c = GAB.seq(args.seq).audioTracks[1].clips[0];
  var nivel = c.components[0].properties[1];   // Volume > Level (conferido no passo anterior)
  var lin = Math.min(1, Math.pow(10, (args.db - 15) / 20));
  var dur = c.end.seconds - c.start.seconds, ini = c.inPoint.seconds;   // keyframe em tempo da FONTE
  nivel.setTimeVarying(true);
  var pts = [[ini, 0], [ini + 0.5, lin], [ini + dur - 2.5, lin], [ini + dur, 0]];
  for (var i = 0; i < pts.length; i++) { nivel.addKey(pts[i][0]); nivel.setValueAtKey(pts[i][0], pts[i][1], true); }
  var ks = nivel.getKeys(), l = [];
  for (var k = 0; k < ks.length; k++) l.push([ks[k].seconds, nivel.getValueAtKey(ks[k])]);
  return { linear: lin, chaves: l };
""", seq=SEQ, db=-10)

passo("marcador em 3 s", """
  var m = GAB.seq(args.seq).markers.createMarker(3); m.name = "GANCHO"; m.comments = "teste Gab"; return GAB.seq(args.seq).markers.numMarkers;
""", seq=SEQ)

passo("QE: razor na V1 em 5 s", """
  var q = GAB.qeSeq(GAB.seq(args.seq));
  var tb = GAB.seq(args.seq).getSettings().videoFrameRate;
  q.getVideoTrackAt(0).razor("00;00;05;00");
  return GAB.retrato(GAB.seq(args.seq)).video[0];
""", seq=SEQ)

passo("QE: lista de efeitos e transições (amostra)", """
  app.enableQE();
  var v = qe.project.getVideoEffectList(), t = qe.project.getVideoTransitionList();
  return { efeitos: v.length, transicoes: t.length, amostraEf: v.slice(0, 8), amostraTr: t.slice(0, 8), lumetri: v.join("|").indexOf("Lumetri") >= 0 };
""")

passo("retrato final", "return GAB.retrato(GAB.seq(args.seq));", seq=SEQ)
