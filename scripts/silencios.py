"""Tira os silêncios pela TRANSCRIÇÃO DO DAVINCI, tudo pela API (sem clicar).

  python3 silencios.py "<timeline>" [--minimo 0.4] [--pre 0.10] [--pos 0.18] [--simular]

Decidido com o usuário em 15/10/2026: o "Remove Silent Portions" do DaVinci (transcrição > ⋯) não existe na API e o
Ripple Delete Silence por dB apagou clipe inteiro em gravação com fundo alto. Então o silêncio vem das PALAVRAS que o
próprio DaVinci reconheceu (MediaPoolItem.TranscribeAudio/GetTranscription): não depende de volume nem de barulho.

Para cada clipe LIGADO da V1, na ordem: pega as palavras dentro do trecho usado; corta o vão entre duas palavras
quando ele passa de `--minimo` s e o começo/fim do clipe sem fala; sobra `--pre` s antes da palavra e `--pos` s depois.
Clipe sem transcrição é transcrito na hora; clipe sem nenhuma palavra entra inteiro (nunca some um clipe).
Monta a timeline nova com o mesmo nome (do modelo, mesma resolução e fps) e guarda a original como
"<nome> - com silencios" (nada é apagado).

Roda DEPOIS dos cortes e ANTES de legenda/b-roll/música: se a timeline já tiver algo além da V1 e do áudio dela, para.
`--simular` mostra o que sairia sem mexer no DaVinci.
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def tc_quadros(tc, fps):
    """HH:MM:SS:FF ou HH:MM:SS;FF (drop frame) -> número do quadro."""
    drop = ";" in tc
    h, m, s, f = [int(x) for x in tc.replace(";", ":").split(":")]
    base = int(round(fps))
    n = ((h * 60 + m) * 60 + s) * base + f
    if drop:   # 29.97/59.94 DF: pula 2 (ou 4) quadros por minuto, menos nos múltiplos de 10
        d = 2 if base == 30 else 4
        mins = h * 60 + m
        n -= d * (mins - mins // 10)
    return n


def palavras(item, fps):
    tr = item.GetTranscription()
    if not tr or not tr.get("segments"):
        item.TranscribeAudio(); tr = item.GetTranscription()
    if not tr or not tr.get("segments"):
        return None
    ini = tc_quadros(item.GetClipProperty("Start TC") or "00:00:00:00", fps)
    ws = []
    for s in tr["segments"]:
        for w in s.get("words", []):
            t = (w.get("text") or "").strip()
            if t and t != "(...)":
                ws.append(((tc_quadros(w["start"], fps) - ini) / fps, (tc_quadros(w["end"], fps) - ini) / fps))
    return sorted(ws)


def trechos(ws, ini, fim, minimo, pre, pos):
    """Trechos (s do arquivo) a manter dentro de [ini, fim]: blocos de fala separados por vãos >= minimo."""
    dentro = [(max(a, ini), min(b, fim)) for a, b in ws if b > ini and a < fim]
    if not dentro:
        return [(ini, fim)]
    blocos = [list(dentro[0])]
    for a, b in dentro[1:]:
        if a - blocos[-1][1] >= minimo:
            blocos.append([a, b])
        else:
            blocos[-1][1] = max(blocos[-1][1], b)
    out = []
    for a, b in blocos:
        a, b = max(ini, a - pre), min(fim, b + pos)
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("timeline")
    ap.add_argument("--minimo", type=float, default=0.4); ap.add_argument("--pre", type=float, default=0.10)
    ap.add_argument("--pos", type=float, default=0.18); ap.add_argument("--simular", action="store_true")
    a = ap.parse_args()
    import resolve_lib as R
    r = R.conectar(); p = r.GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool()
    tls = {p.GetTimelineByIndex(i).GetName(): p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)}
    t = tls.get(a.timeline)
    if not t:
        raise SystemExit(f"timeline {a.timeline!r} não existe no projeto {p.GetName()!r}")
    backup = a.timeline + " - com silencios"
    if backup in tls and not a.simular:
        raise SystemExit(f"já existe {backup!r}: os silêncios já foram tirados (apague/renomeie o backup para refazer)")
    outros = [f"V{k}" for k in range(2, t.GetTrackCount("video") + 1) if t.GetItemListInTrack("video", k)]
    outros += [f"A{k}" for k in range(2, t.GetTrackCount("audio") + 1) if t.GetItemListInTrack("audio", k)]
    outros += ["legenda"] if t.GetTrackCount("subtitle") and t.GetItemListInTrack("subtitle", 1) else []
    if outros:
        raise SystemExit(f"PAROU: a timeline já tem {', '.join(outros)}. Silêncios saem ANTES de legenda/b-roll/música.")
    fps_tl = float(t.GetSetting("timelineFrameRate"))
    clipes = [x for x in (t.GetItemListInTrack("video", 1) or []) if x.GetMediaPoolItem() and x.GetClipEnabled()]
    if not clipes:
        raise SystemExit("V1 sem clipe ligado com mídia")
    infos, antes, depois, cortes = [], 0.0, 0.0, 0
    cache = {}
    for x in clipes:
        it = x.GetMediaPoolItem(); fps = float(it.GetClipProperty("FPS") or fps_tl)
        ini = x.GetSourceStartFrame() / fps; fim = ini + x.GetDuration() / fps_tl
        if it.GetUniqueId() not in cache:
            cache[it.GetUniqueId()] = palavras(it, fps)
        ws = cache[it.GetUniqueId()]
        ks = [(ini, fim)] if ws is None else trechos(ws, ini, fim, a.minimo, a.pre, a.pos)
        dur, fica = fim - ini, sum(b - c for c, b in ks)
        antes += dur; depois += fica; cortes += max(0, len(ks) - 1) + (ks[0][0] > ini + 0.01) + (ks[-1][1] < fim - 0.01)
        print(f"  {x.GetName()}: {dur:.1f} s -> {fica:.1f} s" + (" (sem transcrição: entra inteiro)" if ws is None else f" ({len(ks)} trechos)"))
        for c, b in ks:
            infos.append({"mediaPoolItem": it, "startFrame": int(round(c * fps)), "endFrame": int(round(b * fps)) - 1})
    print(f"total: {antes:.1f} s -> {depois:.1f} s (saem {antes - depois:.1f} s em {cortes} silêncios)")
    if a.simular:
        return
    w, h = t.GetSetting("timelineResolutionWidth"), t.GetSetting("timelineResolutionHeight")
    t.SetName(backup)
    nova = R.timeline_do_modelo(p, mp, a.timeline, w, h, t.GetSetting("timelineFrameRate")) or mp.CreateEmptyTimeline(a.timeline)
    p.SetCurrentTimeline(nova)
    nova.SetSetting("useCustomSettings", "1")
    for k, v in (("timelineResolutionWidth", w), ("timelineResolutionHeight", h), ("timelineFrameRate", t.GetSetting("timelineFrameRate"))):
        nova.SetSetting(k, str(v))
    res = mp.AppendToTimeline(infos) or []
    dur = (nova.GetEndFrame() - nova.GetStartFrame()) / fps_tl
    if len(res) != len(infos):
        print(f"AVISO: entraram {len(res)} de {len(infos)} trechos; conferir a timeline")
    print(f"timeline {a.timeline!r}: {len(res)} clipes, {dur:.1f} s; original guardada em {backup!r}")
    R.salvar(r)


if __name__ == "__main__":
    main()
