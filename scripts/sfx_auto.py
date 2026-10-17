"""Efeitos sonoros automáticos a partir dos tempos da timeline (regra do usuário, 12/10/2026).

  python3 sfx_auto.py "<timeline>" [--biblioteca <pasta com whoosh*.wav e pop*.wav>] [--sem-broll] [--simular]

- whoosh no início de cada MOTION (pico do som cai na entrada do motion);
- whoosh mais baixo no b-roll FORTE: o que entra depois de pelo menos 1,5 s só com o apresentador (cobertura nova);
- pop em cada LETTERING (título do Fusion, item sem arquivo, numa trilha acima da V1).
Vai tudo na A3 (cria e nomeia "SFX"); limpa só os SFX que este script colocou antes (mesmos nomes de arquivo) e não
toca em mais nada. Rodar `retrato.py antes` e `depois --alvo audio3` em volta. Biblioteca padrão: SKILL_DIR/biblioteca_sfx
(fora do git: sons licenciados do usuário, ex.: Artlist "swipe transition low whoosh").
"""
import glob, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolve_lib as R
from projeto import MOTION

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PICO = {"whoosh": 0.11, "pop": 0.03}          # segundos até o pico de cada som (medido)
DUR = {"whoosh": 1.2, "pop": 0.29}            # quanto do som entra
DB = {"motion": -12.0, "broll": -18.0, "pop": -16.0}


def eventos(t, com_broll=True, vazio_min=1.5):
    F = float(t.GetSetting("timelineFrameRate")); S = t.GetStartFrame(); sec = lambda f: (f - S) / F
    acima = sorted(((sec(x.GetStart()), sec(x.GetEnd()), x) for k in range(2, t.GetTrackCount("video") + 1)
                    for x in t.GetItemListInTrack("video", k) or []), key=lambda e: e[0])
    ev = []; fim_cob = -99.0
    for a, b, x in acima:
        nome = x.GetName(); arq = x.GetMediaPoolItem().GetClipProperty("File Path") if x.GetMediaPoolItem() else ""
        if not arq: ev.append((a, "pop", "pop", nome))                       # título/lettering do Fusion
        elif MOTION.search(nome): ev.append((a, "whoosh", "motion", nome))
        elif com_broll and a - fim_cob >= vazio_min: ev.append((a, "whoosh", "broll", nome))
        fim_cob = max(fim_cob, b)
    ev.sort(); limpo = []
    for e in ev:                                                              # um som por instante (motion ganha)
        if e[0] < 0.3 or (limpo and e[0] - limpo[-1][0] < 0.4): continue   # nada no 1º quadro
        limpo.append(e)
    return limpo


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(2)
    nome = a[0]; bib = a[a.index("--biblioteca") + 1] if "--biblioteca" in a else os.path.join(SKILL, "biblioteca_sfx")
    som = {k: (sorted(glob.glob(os.path.join(bib, f"{k}*.wav"))) or [None])[0] for k in ("whoosh", "pop")}
    if not all(som.values()): sys.exit(f"faltam whoosh*.wav e pop*.wav em {bib} (baixar do Artlist/Envato, ver navegador/downloads.md)")
    r = R.conectar(); p = r.GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool()
    t = next((p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if p.GetTimelineByIndex(i).GetName() == nome), None)
    if not t: sys.exit(f"timeline não encontrada: {nome}")
    p.SetCurrentTimeline(t); time.sleep(0.5)
    ev = eventos(t, "--sem-broll" not in a)
    for s, k, tipo, alvo in ev: print(f"  {s:6.2f}s  {k:6s} ({tipo}) <- {alvo}")
    if "--simular" in a: return
    R.garantir_trilhas_audio(t, 3); t.SetTrackName("audio", 3, "SFX")
    nomes = {os.path.basename(v) for v in som.values()}
    velhos = [x for x in t.GetItemListInTrack("audio", 3) or [] if x.GetName() in nomes]
    if velhos and not t.DeleteClips(velhos): sys.exit("não apagou os SFX antigos (timeline atual?)")
    F = float(t.GetSetting("timelineFrameRate")); S = t.GetStartFrame(); itens = {k: R.importar(mp, v, "SFX") for k, v in som.items()}
    n = 0
    for s, k, tipo, _ in ev:
        it = itens[k]; fps_c = float(it.GetClipProperty("FPS") or F)
        ini = max(0.0, s - PICO[k])
        res = mp.AppendToTimeline([{"mediaPoolItem": it, "mediaType": 2, "trackIndex": 3, "recordFrame": S + round(ini * F),
                                    "startFrame": 0, "endFrame": max(1, round(DUR[k] * fps_c))}])
        if res:
            res[0].SetProperty("AudioVolume", DB["pop" if k == "pop" else tipo]); n += 1
    print(f"{n} de {len(ev)} efeitos na A3 de '{nome}'")
    r.GetProjectManager().SaveProject()


if __name__ == "__main__":
    main()
