"""Fábrica de cortes: um vídeo longo (aula, live, podcast, palestra) vira N cortes verticais, cada um numa timeline
própria no DaVinci, em ordem de força. Ideia estudada no OpenMontage (clip factory), feita do jeito da /ogab:
material bruto, corte no DaVinci, transcrição do DaVinci.

  python3 fabrica_cortes.py frases <transcricao.json> <frases.md> [--pausa 0.8]
        -> a transcrição em frases numeradas com o tempo (S1, S2...). É o que o Gab lê para escolher os cortes.
  python3 fabrica_cortes.py conferir <transcricao.json> <cortes.json> [--min 20 --max 75] [--pausa 0.8]
        (use o MESMO --pausa do comando frases, senão os S1, S2... apontam para outras frases)
        -> confere cada corte escolhido e escreve o plano de trechos (pausas encurtadas) em cortes/NN.json.
  python3 fabrica_cortes.py montar <cortes.json> "<clipe do Media Pool>" [--vertical] [--reframe] [--fps-fonte 30]
        -> uma timeline por corte ("CORTE 01 - <título>"), na ordem da nota. --vertical: 1080x1920 com o clipe
           preenchendo; --reframe: Smart Reframe do DaVinci (segue a pessoa). Original intocado.

cortes.json (escrito pelo Gab depois de ler frases.md):
[ {"titulo": "O erro de quem começa", "de": "S41", "ate": "S52",
   "notas": {"gancho": 9, "sozinho": 8, "forca": 9, "fecho": 8}, "porque": "abre com pergunta e fecha com a virada"} ]

Como escolher (nota 0-10 em cada um, média >= 7,5 para entrar; ordenar pela média):
  gancho   a 1ª frase prende sozinha em 3 s (pergunta, número, afirmação forte, contraste); nunca começa com
           "e", "mas", "então", "porque", "aí" nem com referência ao que veio antes ("como eu disse", "isso")
  sozinho  quem não viu o vídeo inteiro entende; sem "lá atrás", "aquele slide", "como vocês viram"
  forca    surpresa, emoção, número concreto, história, virada; uma ideia só
  fecho    termina numa conclusão (frase com ponto final), não no meio do raciocínio
Duração: 20-75 s (Reels rende mais entre 30 e 60). Cortes não se sobrepõem.
"""
import json, os, re, sys, tempfile, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cortes as C

CONECTORES = {"e", "mas", "entao", "porque", "ai", "que", "isso", "tipo", "ne", "pois", "so", "dai", "inclusive"}
REFERENCIA = ("como eu disse", "como eu falei", "la atras", "aquele slide", "como voces viram", "nesse slide",
              "como a gente viu", "voltando", "continuando")


def simples(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", "".join(ch for ch in s if unicodedata.category(ch) != "Mn")))


def mmss(s):
    return f"{int(s // 60):02d}:{s % 60:04.1f}"


def frases(trans, pausa=.8):
    """[(id, ini, fim, texto, palavras)] cortando no ponto final, interrogação, exclamação ou pausa longa."""
    ws = C.palavras(trans); out, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w)
        prox = ws[i + 1] if i + 1 < len(ws) else None
        if re.search(r"[.?!…]$", w["t"]) or prox is None or prox["s"] - w["e"] > pausa:
            out.append((f"S{len(out) + 1}", cur[0]["s"], cur[-1]["e"], " ".join(x["t"] for x in cur), cur))
            cur = []
    return out


def cmd_frases(trans, saida, pausa=.8):
    fs = frases(trans, pausa)
    L = [f"# Frases de {os.path.basename(trans)} ({len(fs)} frases, {mmss(fs[-1][2]) if fs else '0'})", ""]
    L += [f"[{i} {mmss(a)}] {t}" for i, a, b, t, _ in fs]
    open(saida, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"{saida}: {len(fs)} frases")


def conferir(trans, cortes_json, mn=20, mx=75, pausa=.8):
    fs = {f[0]: f for f in frases(trans, pausa)}; ordem = list(fs)
    lista = json.load(open(cortes_json))
    pasta = os.path.join(os.path.dirname(os.path.abspath(cortes_json)), "cortes"); os.makedirs(pasta, exist_ok=True)
    for c in lista:
        n = c.get("notas") or {}
        c["media"] = round(sum(n.values()) / len(n), 2) if n else 0
    lista.sort(key=lambda c: -c["media"])
    usados, linhas, ok = [], [], True
    for k, c in enumerate(lista, 1):
        i0, i1 = ordem.index(c["de"]), ordem.index(c["ate"])
        sel = [fs[x] for x in ordem[i0:i1 + 1]]
        a, b = sel[0][1], sel[-1][2]; dur = b - a
        prob = []
        prim = C.norm(sel[0][4][0]["t"])
        if prim in CONECTORES: prob.append(f"começa com \"{sel[0][4][0]['t']}\" (depende do que veio antes)")
        txt = simples(" ".join(f[3] for f in sel))
        ref = [r for r in REFERENCIA if r in txt]
        if ref: prob.append("cita algo de fora do corte: " + ", ".join(ref))
        if not re.search(r"[.?!…]$", sel[-1][3].strip()): prob.append("termina sem ponto final (meio do raciocínio?)")
        if dur < mn or dur > mx: prob.append(f"{dur:.0f} s fora de {mn}-{mx} s")
        if any(a < y and b > x for x, y in usados): prob.append("sobrepõe outro corte")
        if c["media"] < 7.5: prob.append(f"média {c['media']} abaixo de 7,5")
        usados.append((a, b))
        # trechos do corte com as pausas encurtadas (cortes.plano numa transcrição só com as palavras do corte)
        d = json.load(open(trans)); fps = float(d.get("fps", 30))
        for s in d["segments"]:   # motor davinci grava timecode HH:MM:SS:FF; daqui para baixo tudo em segundos
            for w in s.get("words", []): w["start"], w["end"] = C._seg(w["start"], fps), C._seg(w["end"], fps)
        seg = {"segments": [{"words": [w for s in d["segments"] for w in s.get("words", [])
                                                                     if a - .01 <= float(w["start"]) and float(w["end"]) <= b + .01]}]}
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); json.dump(seg, tmp); tmp.close()
        plano = os.path.join(pasta, f"{k:02d}.json")
        C.plano(tmp.name, plano); os.remove(tmp.name)
        pj = json.load(open(plano)); pj["transcricao"] = os.path.abspath(trans)
        # a folga do cortes.plano não pode invadir a palavra de fora do corte (sobrava "Olha"/"Porque" no fim)
        todas = sorted((float(w["start"]), float(w["end"])) for s in d["segments"] for w in s.get("words", []))
        dentro = seg["segments"][0]["words"]
        for tr in pj.get("trechos", []):
            fins = [float(w["end"]) for w in dentro if float(w["end"]) <= tr[1] + .01]
            inis = [float(w["start"]) for w in dentro if float(w["start"]) >= tr[0] - .01]
            if fins:   # termina no começo da 1a palavra depois da última palavra do trecho
                prox = [s for s, e in todas if s >= max(fins) - .001]
                if prox: tr[1] = round(min(tr[1], prox[0]), 3)
            if inis:   # começa depois do fim da palavra anterior
                ant = [e for s, e in todas if s < min(inis) - .001]
                if ant: tr[0] = round(max(tr[0], min(max(ant), min(inis))), 3)
        pj["total"] = round(sum(y - x for x, y in pj.get("trechos", [])), 2)
        json.dump(pj, open(plano, "w"), indent=1)
        c.update({"n": k, "ini": round(a, 2), "fim": round(b, 2), "plano": plano, "problemas": prob})
        ok &= not prob
        linhas.append(f"{k:02d}  {c['media']:>4}  {mmss(a)}-{mmss(b)} ({dur:.0f} s)  {c['titulo']}"
                      + ("".join(f"\n      ! {p}" for p in prob)))
    json.dump(lista, open(cortes_json, "w"), ensure_ascii=False, indent=1)
    print("\n".join(linhas))
    print(f"\n{len(lista)} corte(s); " + ("tudo certo" if ok else "corrigir os marcados com ! (trocar o S de início/fim, ou tirar o corte fraco) e conferir de novo"))
    return ok


def montar(cortes_json, clipe, vertical=False, reframe=False, fps_fonte=30.0):
    import resolve_lib as R
    lista = json.load(open(cortes_json))
    for c in lista:
        nome = f"CORTE {c['n']:02d} - {c['titulo']}"[:80]
        C.montar(c["plano"], nome, clipe, fps_fonte)
        r = R.conectar(); p = r.GetProjectManager().GetCurrentProject(); t = p.GetCurrentTimeline()
        if vertical:
            t.SetSetting("useCustomSettings", "1")
            t.SetSetting("timelineResolutionWidth", "1080"); t.SetSetting("timelineResolutionHeight", "1920")
            itens = t.GetItemListInTrack("video", 1) or []
            for it in itens:
                it.SetProperty("Scaling", 3)   # preencher: horizontal ocupa o vertical (conferir o enquadramento)
            if reframe:
                R.reenquadrar_vertical(p, itens)
        R.salvar(r)
        print(f"ok: {nome}")


if __name__ == "__main__":
    a = sys.argv[1:]
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if len(a) < 3 or a[0] not in ("frases", "conferir", "montar"):
        raise SystemExit(__doc__)
    if a[0] == "frases":
        cmd_frases(a[1], a[2], float(op("--pausa", .8)))
    elif a[0] == "conferir":
        sys.exit(0 if conferir(a[1], a[2], float(op("--min", 20)), float(op("--max", 75)), float(op("--pausa", .8))) else 1)
    else:
        montar(a[1], a[2], "--vertical" in a, "--reframe" in a, float(op("--fps-fonte", 30)))
