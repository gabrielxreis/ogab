"""Cria o projeto de teste e despeja a reflexão do DOM e da QE do Premiere em teste/reflexao_<versao>.json."""
import json, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import premiere2019_lib as P

print(P.abrir_projeto(os.path.join(AQUI, "Teste Gab 2019.prproj")))
m = os.path.join(AQUI, "midia")
s = P.jsx("""
  var it = GAB.importar([args.bruto], "Footages")[0];
  var p = GAB.proj();
  // QE: nova sequência a partir de preset (createNewSequence do DOM abre diálogo)
  app.enableQE();
  for (var i = 0; i < p.sequences.numSequences; i++) if (p.sequences[i].name === "Reflexao") return "ja existe";
  p.createNewSequenceFromClips ? p.createNewSequenceFromClips("Reflexao", [it], GAB.bin("Timelines")) : null;
  return p.sequences.numSequences;
""", bruto=P._abs(os.path.join(m, "bruto.mp4")))
print("sequências:", s)

alvos = {
    "app": "app", "project": "app.project", "rootItem": "app.project.rootItem",
    "projectItem": "app.project.rootItem.children[0].children.numItems ? app.project.rootItem.children[0].children[0] : app.project.rootItem.children[0]",
    "sequence": "app.project.activeSequence", "videoTrack": "app.project.activeSequence.videoTracks[0]",
    "audioTrack": "app.project.activeSequence.audioTracks[0]", "trackItem": "app.project.activeSequence.videoTracks[0].clips[0]",
    "audioTrackItem": "app.project.activeSequence.audioTracks[0].clips[0]",
    "component": "app.project.activeSequence.videoTracks[0].clips[0].components[0]",
    "componentParam": "app.project.activeSequence.videoTracks[0].clips[0].components[1].properties[0]",
    "markers": "app.project.activeSequence.markers", "encoder": "app.encoder", "time": "new Time()",
    "qe": "(app.enableQE(), qe)", "qeProject": "(app.enableQE(), qe.project)",
    "qeSequence": "(app.enableQE(), qe.project.getActiveSequence())",
    "qeVideoTrack": "(app.enableQE(), qe.project.getActiveSequence().getVideoTrackAt(0))",
    "qeAudioTrack": "(app.enableQE(), qe.project.getActiveSequence().getAudioTrackAt(0))",
    "qeVideoClip": "(app.enableQE(), qe.project.getActiveSequence().getVideoTrackAt(0).getItemAt(0))",
    "qeAudioClip": "(app.enableQE(), qe.project.getActiveSequence().getAudioTrackAt(0).getItemAt(0))",
    "qeProjectItem": "(app.enableQE(), qe.project.getItemAt(0))",
    "qeBin": "(app.enableQE(), qe.project.getBinAt(0))",
}
saida = {}
for nome, expr in alvos.items():
    try:
        saida[nome] = P.descrever(expr)
        print(f"{nome}: {saida[nome].get('classe')} - {len(saida[nome].get('metodos', []))} métodos")
    except Exception as e:
        saida[nome] = {"erro": str(e)}
        print(f"{nome}: ERRO {e}")
v = P.versao()
json.dump(saida, open(os.path.join(AQUI, f"reflexao_{v}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
