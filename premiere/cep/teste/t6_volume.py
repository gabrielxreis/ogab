"""Calibra a escala do Level (Volume) no ExtendScript: exporta WAV com valores diferentes e mede com ffmpeg."""
import json, os, re, subprocess, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import premiere2019_lib as P

M = lambda n: P._abs(os.path.join(AQUI, "midia", n))
PRE = r"C:\Program Files\Adobe\Adobe Premiere Pro CC 2019\Settings\SequencePresets\Digital SLR\1080p\DSLR 1080p30.sqpreset"
WAV = r"C:\Program Files\Adobe\Adobe Premiere Pro CC 2019\MediaIO\systempresets\3F3F3F3F_57415645\Waveform Audio 48kHz 16-bit.epr"
SAIDA = os.path.join(AQUI, "render"); os.makedirs(SAIDA, exist_ok=True)


def media_db(arq):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", arq, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True)
    return float(re.search(r"mean_volume: (-?[\d.]+) dB", r.stderr).group(1))


print("fonte:", media_db(M("musica.wav")), "dB")
P.jsx("""
  var p = GAB.proj();
  try { GAB.seq("Cal"); } catch (e) { app.enableQE(); qe.project.newSequence("Cal", args.pre); }
  var s = GAB.seq("Cal"); var it = GAB.itemPorCaminho(args.a);
  it.setInPoint(GAB.tempo(0), 4); it.setOutPoint(GAB.tempo(4), 4);
  if (!s.audioTracks[0].clips.numItems) s.audioTracks[0].overwriteClip(it, GAB.tempo(0));
  it.clearInPoint(4); it.clearOutPoint(4);
  return true;
""", a=M("musica.wav"), pre=PRE)
for v in [0.25, 2.0, 0.0, 0.5 * 10 ** (-10 / 20)]:
    arq = os.path.join(SAIDA, f"cal_{v}.wav")
    t = time.time()
    r = P.jsx("""
      var s = GAB.seq("Cal"); var c = s.audioTracks[0].clips[0];
      var nivel = c.components[0].properties[1]; nivel.setValue(args.v, true);
      var ok = s.exportAsMediaDirect(args.saida, args.pre, app.encoder.ENCODE_ENTIRE);
      return { lido: nivel.getValue(), ok: ok };
    """, v=v, saida=arq.replace("/", "\\"), pre=WAV)
    print(f"Level={v}: {r} render {time.time() - t:.2f}s -> {media_db(arq) if os.path.exists(arq) else 'sem arquivo'} dB")
