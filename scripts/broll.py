"""B-roll em gravação de apresentador: acha a frase na transcrição (tempo da gravação), converte para o tempo
da timeline cortada (lendo GetSourceStartTime de cada corte da V1) e coloca o clipe BRUTO na trilha BROLL
com ponto de entrada/saída (nada pré-cortado: o usuário reajusta no DaVinci). Preenche o quadro vertical.

Uso (Python):
    import broll
    broll.colocar(timeline, mp, transcricao_json, [
        {"frase": "estuda, analisa o gráfico", "arquivo": ".../take.mp4", "dur": 3.0, "entrada": 0.5},
        {"frase": "o maior atentado", "arquivo": ".../yt.mp4", "dur": 3.5, "entrada": 328, "atraso": 0.4},
    ], trilha=2)
"""
import json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolve_lib as R


def _n(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z0-9]+", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def palavras(trans):
    d = json.load(open(trans))
    return [w for s in d["segments"] for w in s["words"] if _n(w["text"])]


def achar_frase(ws, frase, depois=0.0):
    alvo = [_n(x) for x in frase.split() if _n(x)]
    for i in range(len(ws) - len(alvo) + 1):
        if ws[i]["start"] >= depois and all(_n(ws[i + k]["text"]) == alvo[k] for k in range(len(alvo))):
            return ws[i]["start"]
    raise ValueError(f"frase não encontrada: {frase!r}")


def mapa_fonte(t, trilha=1):
    """[(seg_fonte_ini, seg_fonte_fim, seg_timeline_ini)] dos cortes da trilha (gravação principal)."""
    F = float(t.GetSetting("timelineFrameRate")); S = t.GetStartFrame(); out = []
    for x in t.GetItemListInTrack("video", trilha) or []:
        a = x.GetSourceStartTime(); d = (x.GetEnd() - x.GetStart()) / F
        out.append((a, a + d, (x.GetStart() - S) / F))
    return out


def fonte_para_timeline(mapa, seg):
    for a, b, tl in mapa:
        if a - 0.05 <= seg <= b + 0.05:
            return tl + max(0.0, seg - a)
    # caiu num trecho cortado: usa o próximo corte
    prox = [m for m in mapa if m[0] > seg]
    return prox[0][2] if prox else None


def _preencher(item, w, h, W=1080, H=1920):
    """O DaVinci encaixa por 'fit'; dá zoom até preencher o quadro vertical (sem barra preta)."""
    if not w or not h:
        return
    fit = min(W / w, H / h)
    z = max(W / (w * fit), H / (h * fit))
    if z > 1.001:
        item.SetProperty("ZoomX", round(z, 3)); item.SetProperty("ZoomY", round(z, 3))


def colocar(t, mp, trans, lista, trilha=2, nome_trilha="BROLL", bin_nome="BRoll"):
    F = float(t.GetSetting("timelineFrameRate")); S = t.GetStartFrame()
    while t.GetTrackCount("video") < trilha:
        t.AddTrack("video")
    t.SetTrackName("video", trilha, nome_trilha)
    ws = palavras(trans); mapa = mapa_fonte(t); feitos = []
    plano = []
    for b in lista:
        seg_t, dep = None, b.get("depois", 0.0)
        for _ in range(6):   # a mesma frase pode existir num retake cortado: usa a 1a ocorrência que ficou na timeline
            try:
                seg_f = achar_frase(ws, b["frase"], dep)
            except ValueError:
                break
            if any(a - 0.05 <= seg_f <= bb + 0.05 for a, bb, _ in mapa):
                seg_t = fonte_para_timeline(mapa, seg_f); break
            dep = seg_f + 0.01
        if seg_t is None:
            print("  pulei (frase fora da timeline):", b["frase"]); continue
        plano.append((seg_t + b.get("atraso", 0.0), dict(b)))
    plano.sort(key=lambda x: x[0])
    for k in range(len(plano) - 1):   # sem sobrepor: encurta o anterior até o próximo
        a, b = plano[k]; prox = plano[k + 1][0]
        if a + b["dur"] > prox:
            b["dur"] = max(0.8, prox - a)
    # foto (still) entra sempre com 5 s e a API não apara: colocar os vídeos antes e as fotos por último,
    # assim o DaVinci encaixa a foto no vão até o próximo clipe
    eh_foto = lambda b: os.path.splitext(b["arquivo"])[1].lower() in (".heic", ".jpg", ".jpeg", ".png")
    plano = [x for x in plano if not eh_foto(x[1])] + [x for x in plano if eh_foto(x[1])]
    for seg_t, b in plano:
        # não cabe por cima de um clipe que já está na trilha: limita ao vão livre (senão o append falha calado)
        ini_f = S + int(round(seg_t * F))
        depois_dele = [x.GetStart() for x in (t.GetItemListInTrack("video", trilha) or []) if x.GetStart() > ini_f]
        if depois_dele:
            b["dur"] = min(b["dur"], (min(depois_dele) - ini_f) / F - 0.04)
        if b["dur"] < 0.5:
            print("  sem espaço:", b["frase"]); continue
        it = R.importar(mp, b["arquivo"], bin_nome)
        pr = it.GetClipProperty()
        fps_c = float(pr.get("FPS") or F)
        foto = os.path.splitext(b["arquivo"])[1].lower() in (".heic", ".jpg", ".jpeg", ".png")
        info = {"mediaPoolItem": it, "trackIndex": trilha, "recordFrame": S + int(round(seg_t * F)), "mediaType": 1}
        if not foto:
            e = int(round(b.get("entrada", 0.0) * fps_c))
            info.update(startFrame=e, endFrame=e + int(round(b["dur"] * fps_c)) - 1)
        else:
            info.update(startFrame=0, endFrame=int(round(b["dur"] * F)) - 1)
        res = mp.AppendToTimeline([info])
        if not res:
            print("  falhou:", b["frase"], os.path.basename(b["arquivo"])); continue
        x = res[0]
        nome_arq = os.path.basename(b["arquivo"])
        if not any(y.GetName() == nome_arq and abs(y.GetStart() - ini_f) <= F for y in (t.GetItemListInTrack("video", trilha) or [])):
            print("  NÃO ENTROU (sobreposição?):", b["frase"]); continue
        try:
            w, h = [int(v) for v in (pr.get("Resolution") or "0x0").split("x")]
        except ValueError:
            w = h = 0
        _preencher(x, w, h)
        if "zoom" in b:
            x.SetProperty("ZoomX", b["zoom"]); x.SetProperty("ZoomY", b["zoom"])
        feitos.append((round(seg_t, 2), os.path.basename(b["arquivo"]), b["frase"]))
        print(f"  {seg_t:6.2f}s  {os.path.basename(b['arquivo'])}  <- {b['frase']}")
    return feitos


def transcricao_na_timeline(t, trans, saida):
    """Transcrição da gravação (tempo da fonte) -> tempo da timeline cortada, só com as palavras que ficaram.
    Base para a legenda (cortes > legenda > b-roll)."""
    mapa = mapa_fonte(t); out = []
    for w in palavras(trans):
        a, b = w["start"], w["end"]
        for fa, fb, tl in mapa:
            dentro = min(b, fb) - max(a, fa)
            if dentro > 0 and dentro >= 0.4 * max(0.01, b - a):
                out.append({"text": w["text"], "start": round(tl + max(0.0, a - fa), 3),
                            "end": round(tl + min(fb, b) - fa, 3)})
                break
    out.sort(key=lambda x: x["start"])
    json.dump({"segments": [{"words": out}]}, open(saida, "w"), ensure_ascii=False)
    return out
