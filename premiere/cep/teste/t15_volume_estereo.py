"""Clipe ESTÉREO no 13.1.5: Level padrão, ganho em dB e fades (P.volume) medidos no WAV renderizado pelo Premiere."""
import json, os, re, subprocess, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import premiere2019_lib as P

M = os.path.join(AQUI, "midia"); R = os.path.join(AQUI, "render")
fonte = os.path.join(M, "estereo.wav")
if not os.path.exists(fonte):   # seno 300 Hz na esquerda e 500 Hz na direita, 10 s, -20 dBFS de pico
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=300:d=10", "-f", "lavfi", "-i", "sine=f=500:d=10",
                    "-filter_complex", "[0][1]join=inputs=2:channel_layout=stereo,volume=-2dB", "-ar", "48000", fonte], check=True)
WAV = r"C:\Program Files\Adobe\Adobe Premiere Pro CC 2019\MediaIO\systempresets\3F3F3F3F_57415645\Waveform Audio 48kHz 16-bit.epr"


def rms_janelas(arq, janelas):
    """RMS (dB) de cada janela [a, b] em segundos, pelo astats do ffmpeg."""
    out = []
    for a, b in janelas:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", str(a), "-t", str(b - a), "-i", arq, "-af",
                            "astats=measure_perchannel=none:measure_overall=RMS_level", "-f", "null", "-"],
                           capture_output=True, text=True)
        m = re.findall(r"RMS level dB: (-?[\d.inf]+)", r.stderr)
        out.append(float(m[-1]) if m and m[-1] not in ("-inf", "inf") else -120.0)
    return out


janelas = [(0.0, 0.1), (0.2, 0.3), (0.6, 1.0), (3.0, 5.0), (7.6, 7.8), (8.9, 9.0)]
print("fonte:", rms_janelas(fonte, [(3, 5)]))
P.criar_sequencia("Cal Estereo")
P.jsx("var s = GAB.seq('Cal Estereo'); for (var t = 0; t < s.audioTracks.numTracks; t++) for (var i = s.audioTracks[t].clips.numItems - 1; i >= 0; i--) s.audioTracks[t].clips[i].remove(false, false); return 1;")
P.colocar("Cal Estereo", fonte, 0.0, video=None, audio=0, ate=9.0)
print("Level padrão (clipe estéreo):", P.jsx("var c = GAB.clipeEm(GAB.seq('Cal Estereo').audioTracks[0], 0); var n = GAB.nivel(c); return [n.getValue(), c.components[0].displayName, c.components[0].matchName];"))


def render(nome):
    arq = os.path.join(R, nome)
    P.jsx("GAB.seq('Cal Estereo').exportAsMediaDirect(args.s, args.p, app.encoder.ENCODE_ENTIRE); return 1;", s=arq, p=WAV)
    return arq


base = rms_janelas(render("estereo_0db.wav"), [(3, 5)])[0]
print("padrão (0 dB):", base)
P.volume("Cal Estereo", 0, 0.0, db=-10)
print("-10 dB sem fade:", rms_janelas(render("estereo_-10db.wav"), [(3, 5)])[0] - base, "(alvo -10)")
print(P.volume("Cal Estereo", 0, 0.0, db=-10, fade_in=0.5, fade_out=2.5))
v = rms_janelas(render("estereo_fades.wav"), janelas)
for (a, b), x in zip(janelas, v):
    print(f"  {a:4.1f}-{b:4.1f} s: {x - base:7.1f} dB")
print("chaves:", P.jsx("var n = GAB.nivel(GAB.clipeEm(GAB.seq('Cal Estereo').audioTracks[0], 0)), k = n.getKeys(), l = []; "
                       "for (var i = 0; i < k.length; i++) l.push([k[i].seconds, n.getValueAtKey(k[i])]); return l;"))

# Música com ponto de entrada (de=2): as chaves de fade vão em tempo da FONTE (inPoint + t).
P.criar_sequencia("Cal Estereo 2")
P.jsx("var s = GAB.seq('Cal Estereo 2'); for (var i = s.audioTracks[0].clips.numItems - 1; i >= 0; i--) s.audioTracks[0].clips[i].remove(false, false); return 1;")
P.colocar("Cal Estereo 2", fonte, 0.0, video=None, audio=0, de=2.0, ate=8.0)


def render2(nome):
    arq = os.path.join(R, nome)
    P.jsx("GAB.seq('Cal Estereo 2').exportAsMediaDirect(args.s, args.p, app.encoder.ENCODE_ENTIRE); return 1;", s=arq, p=WAV)
    return arq


base2 = rms_janelas(render2("e2_0db.wav"), [(2, 4)])[0]
print("com entrada em 2 s:", P.volume("Cal Estereo 2", 0, 0.0, db=-10, fade_in=0.5, fade_out=2.5))
jan2 = [(0.0, 0.1), (0.6, 1.0), (2.0, 3.0), (5.9, 6.0)]
for (a, b), x in zip(jan2, rms_janelas(render2("e2_fades.wav"), jan2)):
    print(f"  {a:4.1f}-{b:4.1f} s: {x - base2:7.1f} dB")
