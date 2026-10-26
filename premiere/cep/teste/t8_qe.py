"""Quarta rodada: itens da QE (vãos), efeito/transição/velocidade, MOGRT em trilha existente, addTracks."""
import json, os, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import premiere2019_lib as P

SEQ = "Reels 01"
MOGRT_NATIVO = r"C:\Program Files\Adobe\Adobe Premiere Pro CC 2019\Essential Graphics\Basic Title.mogrt"


def passo(nome, cod, **a):
    t = time.time()
    try:
        r = P.jsx(cod, nome, **a)
    except Exception as e:
        r = f"ERRO {e}"
    print(f"[{(time.time() - t) * 1000:6.0f} ms] {nome}: {json.dumps(r, ensure_ascii=False)[:1200]}")
    return r


passo("itens da V2 na QE (vãos contam?)", """
  var tr = GAB.qeSeq(GAB.seq(args.seq)).getVideoTrackAt(1), l = [];
  for (var i = 0; i < tr.numItems; i++) { var x = tr.getItemAt(i); l.push({ i: i, nome: x.name, tipo: x.type, ini: x.start ? x.start.secs : null, fim: x.end ? x.end.secs : null }); }
  return l;
""", seq=SEQ)

passo("reflexão do clipe QE (não vão)", """
  var tr = GAB.qeSeq(GAB.seq(args.seq)).getVideoTrackAt(1);
  for (var i = 0; i < tr.numItems; i++) { var x = tr.getItemAt(i); if (x.type === "Clip") return GAB.descrever(x); }
  return null;
""", seq=SEQ)

passo("Lumetri no take_01 via QE (clipe certo)", """
  var tr = GAB.qeSeq(GAB.seq(args.seq)).getVideoTrackAt(1), alvo = null;
  for (var i = 0; i < tr.numItems; i++) { var x = tr.getItemAt(i); if (x.type === "Clip" && x.name === "take_01.mp4") alvo = x; }
  alvo.addVideoEffect(qe.project.getVideoEffectByName("Lumetri Color"));
  var c = GAB.seq(args.seq).videoTracks[1].clips[0], l = [];
  for (var k = 0; k < c.components.numItems; k++) l.push(c.components[k].displayName + " [" + c.components[k].matchName + "]");
  var lum = c.components[c.components.numItems - 1], ps = [];
  for (var j = 0; j < lum.properties.numItems; j++) { var v = null; try { v = lum.properties[j].getValue(); } catch (e) {} if (j < 20) ps.push(j + ":" + lum.properties[j].displayName + "=" + String(v).substr(0, 60)); }
  return { componentes: l, n: lum.properties.numItems, lumetri: ps };
""", seq=SEQ)

passo("Cross Dissolve 15 quadros no fim do take_01", """
  var tr = GAB.qeSeq(GAB.seq(args.seq)).getVideoTrackAt(1), alvo = null;
  for (var i = 0; i < tr.numItems; i++) { var x = tr.getItemAt(i); if (x.type === "Clip" && x.name === "take_01.mp4") alvo = x; }
  alvo.addTransition(qe.project.getVideoTransitionByName("Cross Dissolve"), false, "00;00;00;15");
  var t = GAB.seq(args.seq).videoTracks[1].transitions;
  return { n: t.numItems, primeira: t.numItems ? [t[0].start.seconds, t[0].end.seconds] : null };
""", seq=SEQ)

passo("velocidade: desfaz (1x) e põe 2x no take_02 (video)", """
  var tr = GAB.qeSeq(GAB.seq(args.seq)).getVideoTrackAt(1), alvo = null;
  for (var i = 0; i < tr.numItems; i++) { var x = tr.getItemAt(i); if (x.type === "Clip" && x.name.indexOf("take_02") === 0) alvo = x; }
  alvo.setSpeed(1, "", false, false, false);
  var r1 = GAB.retrato(GAB.seq(args.seq)).video[1];
  alvo.setSpeed(2, "", false, false, false);
  return { em1x: r1, em2x: GAB.retrato(GAB.seq(args.seq)).video[1], speed: GAB.seq(args.seq).videoTracks[1].clips[1].getSpeed() };
""", seq=SEQ)

passo("addTracks: +2 vídeo +1 áudio", """
  var s = GAB.seq(args.seq); var a = [s.videoTracks.numTracks, s.audioTracks.numTracks];
  GAB.garantirTrilhas(s, a[0] + 2, a[1] + 1);
  return { antes: a, depois: [s.videoTracks.numTracks, s.audioTracks.numTracks] };
""", seq=SEQ)

passo("MOGRT nativo em 15 s na V4 (agora existe)", """
  var s = GAB.seq(args.seq);
  var ti = s.importMGT(args.m, GAB.ticks(15), 3, 0);
  if (!ti) return "nada";
  var comp = ti.getMGTComponent();
  if (!comp) return { nome: ti.name, mgt: ti.isMGT(), semComponente: true };
  var ps = [];
  for (var i = 0; i < comp.properties.numItems; i++) { var v = null; try { v = comp.properties[i].getValue(); } catch (e) {} ps.push(i + ":" + comp.properties[i].displayName + "=" + String(v).substr(0, 300)); }
  return { nome: ti.name, inicio: ti.start.seconds, fim: ti.end.seconds, params: ps };
""", seq=SEQ, m=MOGRT_NATIVO)

passo("retrato", "return GAB.retrato(GAB.seq(args.seq));", seq=SEQ)
