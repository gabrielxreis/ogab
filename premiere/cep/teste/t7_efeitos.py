"""Terceira rodada: escala/preencher, QE (efeito, transição, velocidade), MOGRT, quadro PNG, render H.264."""
import json, os, subprocess, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import premiere2019_lib as P

SEQ = "Reels 01"
R = os.path.join(AQUI, "render")
H264 = r"C:\Program Files\Adobe\Adobe Premiere Pro CC 2019\MediaIO\systempresets\4E49434B_48323634\01 - Match Source - High bitrate.epr"
MOGRT = os.path.expanduser(r"~\.claude\skills\ogab\premiere\assets\mogrt\frase-duas-linhas.mogrt")
MOGRT_NATIVO = r"C:\Program Files\Adobe\Adobe Premiere Pro CC 2019\Essential Graphics\Basic Title.mogrt"


def passo(nome, cod, **a):
    t = time.time()
    try:
        r = P.jsx(cod, nome, **a)
    except Exception as e:
        r = f"ERRO {e}"
    print(f"[{(time.time() - t) * 1000:6.0f} ms] {nome}: {json.dumps(r, ensure_ascii=False)[:900]}")
    return r


passo("escala para preencher 1080x1920 (Motion > Scale) no take_01 da V2", """
  var s = GAB.seq(args.seq), c = s.videoTracks[1].clips[0];
  var w = 1920, h = 1080;   // tamanho da fonte (o 2019 não expõe direto no TrackItem; ver metadata no doc)
  var esc = Math.max(s.frameSizeHorizontal / w, s.frameSizeVertical / h) * 100;
  var motion = c.components[1]; motion.properties[1].setValue(esc, true);
  return { escala: motion.properties[1].getValue() };
""", seq=SEQ)

passo("tamanho da fonte pela metadata do projeto (Column.Intrinsic.VideoInfo)", """
  var it = GAB.seq(args.seq).videoTracks[1].clips[0].projectItem;
  var md = it.getProjectMetadata();
  var m = md.match(/<premierePrivateProjectMetaData:Column\\.Intrinsic\\.VideoInfo>([^<]*)</);
  return m ? m[1] : md.substr(0, 300);
""", seq=SEQ)

passo("QE: Lumetri Color no take_01 (V2)", """
  var q = GAB.qeSeq(GAB.seq(args.seq));
  var clipeQE = q.getVideoTrackAt(1).getItemAt(0);
  clipeQE.addVideoEffect(qe.project.getVideoEffectByName("Lumetri Color"));
  var c = GAB.seq(args.seq).videoTracks[1].clips[0], l = [];
  for (var i = 0; i < c.components.numItems; i++) l.push(c.components[i].displayName);
  var lum = c.components[c.components.numItems - 1], ps = [];
  for (var j = 0; j < lum.properties.numItems && j < 12; j++) { var v = null; try { v = lum.properties[j].getValue(); } catch (e) {} ps.push(j + ":" + lum.properties[j].displayName + "=" + v); }
  return { componentes: l, lumetri: ps, clipeQE: GAB.descrever(clipeQE).metodos.join(" | ") };
""", seq=SEQ)

passo("QE: Cross Dissolve no fim do take_01", """
  var q = GAB.qeSeq(GAB.seq(args.seq));
  var clipeQE = q.getVideoTrackAt(1).getItemAt(0);
  clipeQE.addTransition(qe.project.getVideoTransitionByName("Cross Dissolve"), false, "00;00;00;15");
  var s = GAB.seq(args.seq);
  return { transicoesV2: s.videoTracks[1].transitions.numItems };
""", seq=SEQ)

passo("QE: velocidade 200% no take_02 (video)", """
  var q = GAB.qeSeq(GAB.seq(args.seq));
  var item = null, tr = q.getVideoTrackAt(1);
  for (var i = 0; i < tr.numItems; i++) { var x = tr.getItemAt(i); if (x.name && x.name.indexOf("take_02") === 0) item = x; }
  if (!item) return "não achou";
  item.setSpeed(200, "", false, false, false);
  return GAB.retrato(GAB.seq(args.seq)).video[1];
""", seq=SEQ)

passo("MOGRT do Gab (frase-duas-linhas) em 12 s na V4", """
  var s = GAB.seq(args.seq);
  var ti = s.importMGT(args.m, GAB.ticks(12), 3, 3);
  if (!ti) return "importMGT devolveu nada";
  var comp = ti.getMGTComponent(), ps = [];
  for (var i = 0; i < comp.properties.numItems; i++) { var v = null; try { v = comp.properties[i].getValue(); } catch (e) {} ps.push(comp.properties[i].displayName + "=" + String(v).substr(0, 80)); }
  return { nome: ti.name, inicio: ti.start.seconds, fim: ti.end.seconds, params: ps };
""", seq=SEQ, m=MOGRT.replace("/", "\\"))

passo("MOGRT nativo (Basic Title) em 15 s, trocar texto", """
  var s = GAB.seq(args.seq);
  var ti = s.importMGT(args.m, GAB.ticks(15), 3, 3);
  if (!ti) return "importMGT devolveu nada";
  var comp = ti.getMGTComponent(), ps = [];
  for (var i = 0; i < comp.properties.numItems; i++) { var v = null; try { v = comp.properties[i].getValue(); } catch (e) {} ps.push(i + ":" + comp.properties[i].displayName + "=" + String(v).substr(0, 200)); }
  return { nome: ti.name, params: ps };
""", seq=SEQ, m=MOGRT_NATIVO)

passo("QE: exportar quadro PNG em 3 s (conferência visual sem tela)", """
  var q = GAB.qeSeq(GAB.seq(args.seq));
  q.exportFramePNG("00;00;03;00", args.png);
  return new File(args.png).exists;
""", seq=SEQ, png=os.path.join(R, "quadro_3s.png"))

t = time.time()
passo("render H.264 Match Source (exportAsMediaDirect, síncrono)", """
  var s = GAB.seq(args.seq);
  var r = s.exportAsMediaDirect(args.saida, args.pre, app.encoder.ENCODE_ENTIRE);
  return { r: r, existe: new File(args.saida).exists };
""", seq=SEQ, saida=os.path.join(R, "reels01.mp4"), pre=H264)
arq = os.path.join(R, "reels01.mp4")
if os.path.exists(arq):
    print(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height,r_frame_rate:format=duration",
                          "-of", "compact", arq], capture_output=True, text=True).stdout)
print(os.listdir(R))
