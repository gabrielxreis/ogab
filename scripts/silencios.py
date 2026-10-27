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
NARRAÇÃO (voz por IA ou locução gravada, vídeo de takes): com a V1 vazia e a narração na A1, faz o mesmo nos clipes
da A1 (regra do usuário, 15/10/2026: "tirar os silêncios seria bom entrar no processo"); mantém o volume do clipe
(+5 dB da narração). Rodar logo depois de `colocar_narracao`, antes da legenda e dos takes.
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
        import time   # o resultado chega segundos depois do TranscribeAudio (relato 16/10/2026)
        item.TranscribeAudio()
        for _ in range(90):
            tr = item.GetTranscription()
            if tr and tr.get("segments"): break
            time.sleep(2)
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


def ate_voz_calar(trechos_, arquivo, ini, fim, lim=-46.0, maxs=0.6):
    """Regra do usuário (17/10/2026: "você cortou os áudios e as palavras ficam cortadas"): a transcrição do DaVinci
    marca o fim da palavra cedo (ex.: "1979," acabava 0,4 s depois). Confere no ÁUDIO: cada borda de corte anda até
    60 ms seguidos abaixo de lim dB (fim para a frente, começo para trás), sem invadir o trecho vizinho."""
    import subprocess, numpy as np
    try:
        a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", arquivo, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                                         capture_output=True).stdout, dtype=np.float32)
    except Exception:
        return trechos_
    if not len(a): return trechos_
    jan = 160; n = len(a) // jan
    db = 20 * np.log10(np.sqrt(np.mean(a[:n * jan].reshape(n, jan) ** 2, axis=1)) + 1e-9)
    def anda(t, d):
        i0 = int(t * 100); q = 0
        for k in range(int(maxs * 100)):
            i = i0 + k * d
            if i < 0 or i >= n: break
            q = q + 1 if db[i] < lim else 0
            if q >= 6: return max(0.0, (k - 5) / 100) + 0.02
        return maxs
    out = [list(x) for x in trechos_]
    for j, (c, b) in enumerate(out):
        if j + 1 < len(out) or b < fim - 0.01:
            nb = min(fim, b + anda(b, +1)); out[j][1] = min(nb, out[j + 1][0] if j + 1 < len(out) else fim)
        if j > 0 or c > ini + 0.01:
            nc = max(ini, c - anda(c, -1)); out[j][0] = max(nc, out[j - 1][1] if j > 0 else ini)
    junto = []
    for c, b in out:
        if junto and c <= junto[-1][1] + 0.02: junto[-1][1] = b
        else: junto.append([c, b])
    return [tuple(x) for x in junto]


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
    narracao = not clipes   # vídeo de narração: V1 vazia, a fala está na A1
    if narracao:
        clipes = [x for x in (t.GetItemListInTrack("audio", 1) or []) if x.GetMediaPoolItem() and x.GetClipEnabled()]
    if not clipes:
        raise SystemExit("V1 e A1 sem clipe ligado com mídia")
    tipo, rot = ("audio", "A1") if narracao else ("video", "V1")
    # velocidade alterada (speed ramp, 50%, 200%): o AppendToTimeline remonta a 100% e o trecho cairia fora da fala.
    # TimelineItem.GetSpeed (21.1) dá a %; speed ramp não aparece nela, então também compara trecho do arquivo x duração.
    lentos = []
    for x in clipes:
        it = x.GetMediaPoolItem(); fps = float(it.GetClipProperty("FPS") or fps_tl)
        src = (x.GetSourceEndFrame() - x.GetSourceStartFrame()) / fps; tl = x.GetDuration() / fps_tl
        try:
            pct = float((x.GetSpeed() or {}).get("Percentage", 100))   # API 21.1; a proporção cobre speed ramp
        except Exception:
            pct = 100.0
        if abs(pct - 100) > 0.5 or (tl > 0 and abs(src / tl - 1) > 0.03):
            lentos.append(f"{x.GetName()} ({pct:.0f}%)" if abs(pct - 100) > 0.5 else f"{x.GetName()} (~{100 * src / tl:.0f}%)")
    if lentos:
        raise SystemExit(f"PAROU: clipe com velocidade alterada na {rot}: " + ", ".join(lentos) +
                         ". Tirar os silêncios ANTES de mexer na velocidade (nada foi alterado).")
    infos, vols, antes, depois, cortes = [], [], 0.0, 0.0, 0
    cache = {}
    for x in clipes:
        it = x.GetMediaPoolItem(); fps = float(it.GetClipProperty("FPS") or fps_tl)
        ini = x.GetSourceStartFrame() / fps; fim = ini + x.GetDuration() / fps_tl
        if it.GetUniqueId() not in cache:
            cache[it.GetUniqueId()] = palavras(it, fps)
        ws = cache[it.GetUniqueId()]
        ks = [(ini, fim)] if ws is None else trechos(ws, ini, fim, a.minimo, a.pre, a.pos)
        if ws is not None: ks = ate_voz_calar(ks, it.GetClipProperty("File Path"), ini, fim)   # palavra nunca cortada
        dur, fica = fim - ini, sum(b - c for c, b in ks)
        antes += dur; depois += fica; cortes += max(0, len(ks) - 1) + (ks[0][0] > ini + 0.01) + (ks[-1][1] < fim - 0.01)
        print(f"  {x.GetName()}: {dur:.1f} s -> {fica:.1f} s" + (" (sem transcrição: entra inteiro)" if ws is None else f" ({len(ks)} trechos)"))
        vol = x.GetProperty("AudioVolume") if narracao else None
        for c, b in ks:
            info = {"mediaPoolItem": it, "startFrame": int(round(c * fps)), "endFrame": int(round(b * fps))}
            if narracao: info.update({"mediaType": 2, "trackIndex": 1})
            infos.append(info); vols.append(vol)
    print(f"total: {antes:.1f} s -> {depois:.1f} s (saem {antes - depois:.1f} s em {cortes} silêncios)")
    if a.simular:
        return
    w, h = t.GetSetting("timelineResolutionWidth"), t.GetSetting("timelineResolutionHeight")
    vi = t.GetVoiceIsolationState(1) or {}
    t.SetName(backup)
    # duplicar a PRÓPRIA timeline (mantém fps, resolução e o estilo da trilha de legenda). Recriar pelo modelo GAB USA
    # (24 fps) deixava a nova em 24 numa timeline de 30: SetSetting do fps não pega e os trechos saíam errados (relato 16/10/2026)
    p.SetCurrentTimeline(t); R.pagina_edit()
    nova = t.DuplicateTimeline(a.timeline)
    if not nova:
        t.SetName(a.timeline); raise SystemExit("DuplicateTimeline falhou; nada foi alterado")
    p.SetCurrentTimeline(nova)
    for k in ("video", "audio"):
        its = nova.GetItemListInTrack(k, 1) or []
        if its: nova.DeleteClips(its)
    if abs(float(nova.GetSetting("timelineFrameRate")) - fps_tl) > 0.01:
        raise SystemExit("a cópia mudou de fps; conferir (a original está guardada como backup)")
    if narracao:
        res = mp.AppendToTimeline(infos) or []
    else:
        # vídeo (V1) e áudio (A1) em appends SEPARADOS no mesmo quadro e depois ligados: o append junto, sem trilha,
        # cai na trilha de destino da interface (áudio foi parar na A2) e, com fps da gravação != fps da timeline
        # (30 numa de 24), dessincroniza o áudio (relato 27/10/2026)
        res, rec = [], nova.GetStartFrame()
        for info in infos:
            v = mp.AppendToTimeline([dict(info, mediaType=1, trackIndex=1, recordFrame=rec)]) or []
            au = mp.AppendToTimeline([dict(info, mediaType=2, trackIndex=1, recordFrame=rec)]) or []
            if v and au: nova.SetClipsLinked([v[0], au[0]], True)
            if v: res.append(v[0]); rec = v[0].GetEnd()
    dur = (nova.GetEndFrame() - nova.GetStartFrame()) / fps_tl
    if len(res) != len(infos):
        print(f"AVISO: entraram {len(res)} de {len(infos)} trechos; conferir a timeline")
    if narracao:   # volume do clipe (+5 dB da narração) não vem no AppendToTimeline
        for x, v in zip(res, vols):
            if isinstance(v, (int, float)): x.SetProperty("AudioVolume", v)
    else:   # regra 1d: Voice Isolation na A1 (timeline nova nasce sem); mantém a intensidade que a original tinha
        alvo_vi = vi if vi.get("isEnabled") else {"isEnabled": True, "amount": 100}
        nova.SetVoiceIsolationState(1, alvo_vi)
        print("Voice Isolation A1:", nova.GetVoiceIsolationState(1))
    R.salvar(r)
    # o salvar pode descartar clipes de um append que deu erro: conferir DEPOIS de salvar (armadilha da API)
    n = len(nova.GetItemListInTrack(tipo, 1) or [])
    if n < len(infos):
        raise SystemExit(f"ERRO: depois de salvar ficaram {n} de {len(infos)} trechos na {rot}; conferir a timeline {a.timeline!r}")
    print(f"timeline {a.timeline!r}: {n} clipes, {dur:.1f} s; original guardada em {backup!r}")


if __name__ == "__main__":
    main()
