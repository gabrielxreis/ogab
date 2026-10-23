"""Cortes de gravação de apresentador pela transcrição (palavra a palavra).

Tira frases inteiras (retakes, repetições) e encurta as pausas, gerando a lista
de trechos a manter. Depois monta numa timeline nova do DaVinci (a original
fica como backup "<nome> - bruto").

  python3 cortes.py plano <transcricao.json> <saida.json> [--tirar "frase 1" --tirar "frase 2"]
        [--tirar-entre INICIO FIM] [--ate SEG] [--pausa 0.35] [--pre 0.10] [--pos 0.18]
        [--audio audio.wav --silencio 0.35 --deixa 0.12 --limiar -35]  (externa com barulho: --limiar -27)   (encolhe silêncios dentro dos trechos)
  python3 cortes.py montar <saida.json> "<timeline>" "<clipe do media pool>" [--fps-fonte 30]

--tirar: sequência de palavras (sem pontuação, sem caixa) a remover; a 1a ocorrência
         (ou use "frase@SEG" para a ocorrência mais perto de SEG).
--tirar-entre: tira tudo entre dois tempos (retake inteiro).
"""
import json, re, sys, unicodedata


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", s)


def _seg(v, fps):
    """Segundos de um tempo da transcrição: número ou timecode HH:MM:SS:FF do DaVinci (motor davinci)."""
    if isinstance(v, str) and v.count(":") == 3:
        h, m, sec, fr = (int(x) for x in v.split(":"))
        return h * 3600 + m * 60 + sec + fr / fps
    return float(v)


def palavras(trans):
    d = json.load(open(trans))
    fps = float(d.get("fps", 30))
    ws = []
    for s in d["segments"]:
        for w in s.get("words", []):
            t = w.get("text", w.get("word", ""))
            if norm(t):
                ws.append({"t": t.strip(), "n": norm(t), "s": _seg(w["start"], fps), "e": _seg(w["end"], fps)})
    return ws


def achar(ws, frase, perto=None):
    alvo = [norm(x) for x in frase.split() if norm(x)]
    achados = []
    for i in range(len(ws) - len(alvo) + 1):
        if all(ws[i + k]["n"] == alvo[k] for k in range(len(alvo))):
            achados.append(i)
    if not achados:
        raise SystemExit(f"frase não encontrada: {frase!r}")
    if perto is not None:
        achados.sort(key=lambda i: abs(ws[i]["s"] - perto))
    return achados[0], achados[0] + len(alvo)


def silencios(audio, limiar=-35, minimo=0.35):
    import subprocess
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", audio, "-af",
                          f"silencedetect=n={limiar}dB:d={minimo}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    ini = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    fim = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(ini, fim))


def tirar_silencios(trechos, audio, minimo=0.35, deixa=0.12, limiar=-35, protegidas=()):
    """Dentro de cada trecho, encolhe cada silêncio > minimo para 2*deixa (respiro).
    Nunca corta dentro de uma palavra da transcrição (palavra falada baixo parece silêncio)."""
    sil = []
    for s0, s1 in silencios(audio, limiar=limiar, minimo=minimo):
        partes = [(s0, s1)]
        for w0, w1 in protegidas:
            w0, w1 = w0 - 0.06, w1 + 0.06
            novo = []
            for a, b in partes:
                if w1 <= a or w0 >= b:
                    novo.append((a, b))
                else:
                    if w0 > a: novo.append((a, w0))
                    if w1 < b: novo.append((w1, b))
            partes = novo
        sil += [x for x in partes if x[1] - x[0] >= minimo]
    out = []
    for a, b in trechos:
        cur = a
        for s0, s1 in sil:
            if s1 <= a or s0 >= b:
                continue
            c0, c1 = max(s0, a), min(s1, b)
            if c1 - c0 < minimo:
                continue
            fim_fala = c0 + deixa if c0 > a else a
            volta = c1 - deixa if c1 < b else b
            if fim_fala - cur > 0.08:
                out.append([round(cur, 3), round(fim_fala, 3)])
            cur = volta
        if b - cur > 0.08:
            out.append([round(cur, 3), round(b, 3)])
    return out


def plano(trans, saida, tirar=(), entre=(), ate=None, pausa=0.35, pre=0.10, pos=0.18,
          audio=None, silencio=0.35, deixa=0.12, limiar=-35):
    ws = palavras(trans)
    fora = set()
    for f in tirar:
        perto = None
        if "@" in f:
            f, perto = f.rsplit("@", 1); perto = float(perto)
        a, b = achar(ws, f, perto)
        fora.update(range(a, b))
        print(f"  tira {ws[a]['s']:6.2f}-{ws[b-1]['e']:6.2f}  {' '.join(w['t'] for w in ws[a:b])}")
    for a, b in entre:
        idx = [i for i, w in enumerate(ws) if w["s"] >= a and w["e"] <= b]
        fora.update(idx)
        print(f"  tira {a:6.2f}-{b:6.2f}  ({len(idx)} palavras) {' '.join(ws[i]['t'] for i in idx)[:90]}")
    manter = [w for i, w in enumerate(ws) if i not in fora and (ate is None or w["s"] < ate)]
    trechos, ini, fim, prev_i, i0 = [], None, None, None, None
    idx_de = {id(w): i for i, w in enumerate(ws)}
    for w in manter:
        i = idx_de[id(w)]
        continua = ini is not None and prev_i == i - 1 and w["s"] - fim <= pausa
        if continua:
            fim = w["e"]
        else:
            if ini is not None:
                trechos.append([ini, fim, i0, prev_i])
            ini, fim, i0 = w["s"], w["e"], i
        prev_i = i
    if ini is not None:
        trechos.append([ini, fim, i0, prev_i])
    # margem sem sobrepor trechos vizinhos e sem entrar numa palavra removida
    out = []
    for a, b, ia, ib in trechos:
        a2 = max(0.0, a - pre); b2 = b + pos
        if ia > 0 and (ia - 1) in fora:
            a2 = max(a2, ws[ia - 1]["e"] + 0.02)
        if ib + 1 < len(ws) and (ib + 1) in fora:
            b2 = min(b2, ws[ib + 1]["s"] - 0.02)
        a2 = min(a2, a); b2 = max(b2, b)
        if out and a2 < out[-1][1]:
            meio = (out[-1][1] - pos + a) / 2 if out[-1][1] > a else a2
            out[-1][1] = min(out[-1][1], max(meio, out[-1][0] + 0.05)); a2 = out[-1][1]
        out.append([round(a2, 3), round(b2, 3)])
    if audio:
        out = tirar_silencios(out, audio, silencio, deixa, limiar, [(w['s'], w['e']) for w in manter])
    perdidas = [w["t"] + f"@{w['s']:.1f}" for w in manter
                if not any(a - 0.01 <= (w["s"] + w["e"]) / 2 <= b + 0.01 for a, b in out)]
    if perdidas:
        print("AVISO palavras fora dos cortes:", " ".join(perdidas))
    total = sum(b - a for a, b in out)
    json.dump({"trechos": out, "total": round(total, 2), "transcricao": trans}, open(saida, "w"), indent=1)
    print(f"{len(out)} trechos, {total:.1f} s ({int(total//60)}:{total%60:04.1f})")
    return out


def montar(plano_json, nome_tl, clipe, fps_fonte=30.0):
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    import resolve_lib as R
    r = R.conectar(); p = r.GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool()
    d = json.load(open(plano_json))
    item = None
    def busca(f):
        nonlocal item
        for c in f.GetClipList() or []:
            if c.GetName() == clipe: item = item or c
        for s in f.GetSubFolderList() or []: busca(s)
    busca(mp.GetRootFolder())
    if not item:
        raise SystemExit(f"clipe {clipe!r} não está no media pool")
    tls = {p.GetTimelineByIndex(i).GetName(): p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)}
    velha = tls.get(nome_tl)
    vazia = velha and not (velha.GetItemListInTrack("video", 1) or [])
    if velha and not vazia:
        if nome_tl + " - bruto" in tls:
            raise SystemExit(f"já existe {nome_tl!r} com conteúdo e o backup '- bruto': apague/renomeie um antes")
        velha.SetName(nome_tl + " - bruto")
    base = velha if (velha and not vazia) else tls.get(nome_tl + " - bruto")
    t = velha if vazia else None
    if t is None:   # nasce do modelo: legenda já com o preset GAB USA (sem interface)
        t = R.timeline_do_modelo(p, mp, nome_tl, base.GetSetting("timelineResolutionWidth") if base else None,
                                 base.GetSetting("timelineResolutionHeight") if base else None,
                                 base.GetSetting("timelineFrameRate") if base else None) or mp.CreateEmptyTimeline(nome_tl)
    p.SetCurrentTimeline(t)
    # mesma resolução/fps da gravação original (o padrão do projeto pode ser horizontal)
    if base:
        t.SetSetting("useCustomSettings", "1")
        for k in ("timelineResolutionWidth", "timelineResolutionHeight", "timelineFrameRate"):
            t.SetSetting(k, base.GetSetting(k))
    print("formato:", t.GetSetting("timelineResolutionWidth"), "x", t.GetSetting("timelineResolutionHeight"), t.GetSetting("timelineFrameRate"), "fps")
    infos = [{"mediaPoolItem": item, "startFrame": int(round(a * fps_fonte)),
              "endFrame": int(round(b * fps_fonte))} for a, b in d["trechos"]]
    res = mp.AppendToTimeline(infos)
    n = len(t.GetItemListInTrack("video", 1) or [])
    fps = float(t.GetSetting("timelineFrameRate"))
    dur = (t.GetEndFrame() - t.GetStartFrame()) / fps
    R.salvar(r); n = len(t.GetItemListInTrack("video", 1) or [])   # conferir depois de salvar (append com erro some no save)
    if n < len(infos):
        print(f"AVISO: depois de salvar ficaram {n} de {len(infos)} trechos; conferir a timeline")
    print(f"timeline {nome_tl!r}: {n} cortes, {dur:.1f} s (plano {d['total']} s), appended={len(res or [])}")
    return t


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("plano", "montar"):
        print(__doc__); sys.exit(1)
    if a[0] == "plano":
        tirar, entre, ate, kw = [], [], None, {}
        rest = a[3:]; i = 0
        while i < len(rest):
            k = rest[i]
            if k == "--tirar": tirar.append(rest[i + 1]); i += 2
            elif k == "--tirar-entre": entre.append((float(rest[i + 1]), float(rest[i + 2]))); i += 3
            elif k == "--ate": ate = float(rest[i + 1]); i += 2
            elif k in ("--pausa", "--pre", "--pos", "--silencio", "--deixa", "--limiar"): kw[k[2:]] = float(rest[i + 1]); i += 2
            elif k == "--audio": kw["audio"] = rest[i + 1]; i += 2
            else: raise SystemExit(f"opção desconhecida {k}")
        plano(a[1], a[2], tirar, entre, ate, **kw)
    else:
        fps = 30.0
        if "--fps-fonte" in a: fps = float(a[a.index("--fps-fonte") + 1])
        montar(a[1], a[2], a[3], fps)
