"""Cria sequência pela QE (sem diálogo), ajusta para 1080x1920 e despeja a reflexão de Sequence/Track/Settings."""
import json, os, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import premiere2019_lib as P

preset = "C:/Program Files/Adobe/Adobe Premiere Pro CC 2019/Settings/SequencePresets/Digital SLR/1080p/DSLR 1080p30.sqpreset"
print(os.path.exists(preset))
t = time.time()
r = P.jsx("""
  var p = GAB.proj();
  for (var i = 0; i < p.sequences.numSequences; i++) if (p.sequences[i].name === args.nome) return "já existe";
  app.enableQE();
  qe.project.newSequence(args.nome, args.preset);
  var s = GAB.seq(args.nome);
  return { id: s.sequenceID, ativa: p.activeSequence ? p.activeSequence.name : null };
""", nome="Reels 01", preset=preset)
print(r, round(time.time() - t, 3), "s")
d = {}
for nome, expr in {"sequence": "GAB.seq('Reels 01')", "settings": "GAB.seq('Reels 01').getSettings()",
                   "videoTrack": "GAB.seq('Reels 01').videoTracks[0]", "trackCollection": "GAB.seq('Reels 01').videoTracks",
                   "qeSequence": "GAB.qeSeq(GAB.seq('Reels 01'))",
                   "qeVideoTrack": "GAB.qeSeq(GAB.seq('Reels 01')).getVideoTrackAt(0)",
                   "qeAudioTrack": "GAB.qeSeq(GAB.seq('Reels 01')).getAudioTrackAt(0)"}.items():
    try:
        d[nome] = P.descrever(expr)
    except Exception as e:
        d[nome] = {"erro": str(e)}
for k, v in d.items():
    print("##", k, v.get("classe"), v.get("erro", ""))
    print(" | ".join(v.get("metodos", [])))
    print("props:", v.get("props"))
arq = os.path.join(AQUI, "reflexao_13.1.5.json")
tudo = json.load(open(arq, encoding="utf-8")); tudo.update(d)
json.dump(tudo, open(arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
