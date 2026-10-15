"""Tira os silêncios com a ferramenta do PRÓPRIO DaVinci: Clip > Audio Operations > Ripple Delete Silence…
(regra do usuário, 15/10/2026: "somente ela", é inteligente o bastante). Não há função na API; o script prepara pela
API, aciona o menu pelo System Events e confere o resultado pela API.

  python3 silencios.py "<timeline>" [--espera 180]

1. Pela API: confere que a timeline só tem a gravação (V1 + áudio dela), guarda uma cópia "<nome> - com silencios"
   (backup; nada é apagado) e abre a timeline na página Edit.
2. Pelo menu: Edit > Select All, Clip > Audio Operations > Ripple Delete Silence…, janela "Remove Silence" com os
   padrões do DaVinci (Threshold -25 dB, Pre head 0, Post tail 0, Minimum to strip 24 frames), botão Remove.
3. Pela API: espera a duração mudar e mostra antes x depois. Se nada mudou, para com erro (não diz que cortou).

Antes de rodar: nenhuma outra sessão mexendo no DaVinci e o usuário fora dele (regra 1g; o menu age no projeto que
estiver na frente). Roda DEPOIS dos cortes e ANTES da legenda.
"""
import argparse, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MENU = '''tell application "DaVinci Resolve" to activate
delay 0.8
tell application "System Events" to tell process "Resolve"
  click menu item "Select All" of menu 1 of menu bar item "Edit" of menu bar 1
  delay 0.5
  click menu item "Ripple Delete Silence…" of menu 1 of menu item "Audio Operations" of menu 1 of menu bar item "Clip" of menu bar 1
  repeat 20 times
    if exists window "Remove Silence" then exit repeat
    delay 0.5
  end repeat
  if not (exists window "Remove Silence") then error "a janela Remove Silence não abriu"
  click button "Remove" of window "Remove Silence"
end tell'''


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("timeline"); ap.add_argument("--espera", type=float, default=180)
    a = ap.parse_args()
    import resolve_lib as R
    r = R.conectar(); p = r.GetProjectManager().GetCurrentProject(); projeto = p.GetName()
    tls = {p.GetTimelineByIndex(i).GetName(): p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)}
    t = tls.get(a.timeline)
    if not t:
        raise SystemExit(f"timeline {a.timeline!r} não existe no projeto {projeto!r}")
    backup = a.timeline + " - com silencios"
    if backup in tls:
        raise SystemExit(f"já existe {backup!r}: os silêncios já foram tirados (apague/renomeie o backup para refazer)")
    outros = [f"V{k}" for k in range(2, t.GetTrackCount("video") + 1) if t.GetItemListInTrack("video", k)]
    outros += [f"A{k}" for k in range(2, t.GetTrackCount("audio") + 1) if t.GetItemListInTrack("audio", k)]
    outros += ["legenda"] if t.GetTrackCount("subtitle") and t.GetItemListInTrack("subtitle", 1) else []
    if outros:
        raise SystemExit(f"PAROU: a timeline já tem {', '.join(outros)}. Silêncios saem ANTES de legenda/b-roll/música.")
    fps = float(t.GetSetting("timelineFrameRate"))
    dur = lambda x: (x.GetEndFrame() - x.GetStartFrame()) / fps
    antes, n_antes = dur(t), len(t.GetItemListInTrack("video", 1) or [])
    p.SetCurrentTimeline(t)
    if not t.DuplicateTimeline(backup):
        raise SystemExit("não consegui criar o backup")
    p.SetCurrentTimeline(t); r.OpenPage("edit"); time.sleep(1)
    if p.GetCurrentTimeline().GetName() != a.timeline:
        raise SystemExit("a timeline certa não ficou na frente; nada foi cortado")
    res = subprocess.run(["osascript", "-"], input=MENU, capture_output=True, text=True)
    if res.returncode:
        raise SystemExit("menu do DaVinci falhou: " + res.stderr.strip())
    t0 = time.time()
    while time.time() - t0 < a.espera:
        time.sleep(2)
        if r.GetProjectManager().GetCurrentProject().GetName() != projeto:
            raise SystemExit("o projeto do DaVinci mudou no meio (outra sessão?); conferir a timeline à mão")
        if abs(dur(t) - antes) > 0.05:
            time.sleep(2); break
    depois, n = dur(t), len(t.GetItemListInTrack("video", 1) or [])
    if abs(depois - antes) <= 0.05:
        raise SystemExit(f"Ripple Delete Silence não mudou a timeline ({antes:.1f} s, {n} clipes). Backup em {backup!r}.")
    print(f"{a.timeline!r}: {antes:.1f} s -> {depois:.1f} s ({n_antes} -> {n} clipes); original em {backup!r}")
    R.salvar(r)


if __name__ == "__main__":
    main()
