"""Legenda na ordem do usuário (12/10/2026): 1) Create Subtitles from Audio da timeline ATUAL; 2) métrica; 3) preset.

  python3 legenda_auto.py "<timeline>" <pasta_legendas> [--cliente clientes/<empresa>] [--gerar]

--gerar   apaga as legendas da trilha 1 e roda o Create Subtitles from Audio (pt, 1 linha, 25 caracteres).
Depois lê as legendas da timeline, distribui o tempo de cada uma pelas palavras (proporcional às letras),
refaz o corte com a métrica da skill (legendas.py rascunho/sincronizar/metrica, grafia do cliente) e recoloca
na MESMA trilha (o estilo/preset da trilha fica). Se a trilha veio do modelo GAB USA, o preset já está aplicado.
"""
import json, os, subprocess, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import resolve_lib as R


def gerar(r, t, espera=120):
    """Roda o Create Subtitles from Audio e ESPERA as legendas aparecerem (15/10/2026: com o DaVinci recém-aberto fora da
    página Edit o comando devolve True e a trilha fica com 0 itens; ler logo depois quebrava com IndexError)."""
    r.OpenPage("edit"); time.sleep(1)
    old = t.GetItemListInTrack("subtitle", 1) or []
    if old: t.DeleteClips(old)
    cfg = {r.SUBTITLE_LANGUAGE: r.AUTO_CAPTION_PORTUGUESE, r.SUBTITLE_CAPTION_PRESET: r.AUTO_CAPTION_SUBTITLE_DEFAULT,
           r.SUBTITLE_CHARS_PER_LINE: 25, r.SUBTITLE_LINE_BREAK: r.AUTO_CAPTION_LINE_SINGLE, r.SUBTITLE_GAP: 0}
    if not t.CreateSubtitlesFromAudio(cfg):
        raise SystemExit("Create Subtitles from Audio falhou")
    fim, antes = time.time() + espera, -1
    while time.time() < fim:
        n = len(t.GetItemListInTrack("subtitle", 1) or [])
        if n and n == antes:   # parou de crescer
            return n
        antes = n; time.sleep(3)
    raise SystemExit(f"Create Subtitles from Audio não gerou legenda em {espera} s: confira se o DaVinci está na página "
                     "Edit, se a timeline tem áudio com fala e se a transcrição (Workspace > Transcribe) funciona à mão")


def palavras_da_timeline(t):
    F = float(t.GetSetting("timelineFrameRate")); S = t.GetStartFrame(); ws = []
    for x in t.GetItemListInTrack("subtitle", 1) or []:
        txt = " ".join(x.GetName().split()); a = (x.GetStart() - S) / F; b = (x.GetEnd() - S) / F
        ps = txt.split()
        if not ps: continue
        tot = sum(len(p) + 1 for p in ps); cur = a
        for p in ps:
            d = (b - a) * (len(p) + 1) / tot
            ws.append({"text": p, "start": round(cur, 3), "end": round(cur + d, 3)}); cur += d
    return ws


def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); sys.exit(1)
    nome, pasta = a[0], a[1]
    cli = a[a.index("--cliente") + 1] if "--cliente" in a else None
    r = R.conectar(); p = r.GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool()
    t = next(p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if p.GetTimelineByIndex(i).GetName() == nome)
    p.SetCurrentTimeline(t); time.sleep(0.5)
    if "--gerar" in a: gerar(r, t)
    ws = palavras_da_timeline(t)
    if not ws:
        raise SystemExit("a trilha de legenda 1 está vazia: rode com --gerar (ou crie as legendas) antes")
    os.makedirs(pasta, exist_ok=True)
    trans = os.path.join(pasta, "subtitles_from_audio.json")
    json.dump({"segments": [{"words": ws}]}, open(trans, "w"), ensure_ascii=False)
    n = 1
    while os.path.exists(os.path.join(pasta, f"legendas_auto_v{n}.srt")): n += 1
    frases = os.path.join(pasta, "frases_auto.txt"); srt = os.path.join(pasta, f"legendas_auto_v{n}.srt")
    L = os.path.join(AQUI, "legendas.py"); cl = ["--cliente", cli] if cli else []
    subprocess.run([sys.executable, L, "rascunho", trans, frases] + cl, check=True)
    subprocess.run([sys.executable, L, "sincronizar", trans, frases, srt], check=True)
    ok = subprocess.run([sys.executable, L, "metrica", srt]).returncode == 0
    if not ok:
        subprocess.run([sys.executable, L, "reflow", trans, frases] + cl, check=True)
        subprocess.run([sys.executable, L, "sincronizar", trans, frases, srt], check=True)
        ok = subprocess.run([sys.executable, L, "metrica", srt]).returncode == 0
    print("métrica:", "OK" if ok else "AINDA COM PROBLEMA: revisar frases_auto.txt e rodar sincronizar de novo")
    R.colocar_legendas(t, mp, srt, p=p)
    its = t.GetItemListInTrack("subtitle", 1) or []
    print(f"{nome}: {len(its)} legendas na trilha 1 ({srt})")
    r.GetProjectManager().SaveProject()


if __name__ == "__main__":
    main()
