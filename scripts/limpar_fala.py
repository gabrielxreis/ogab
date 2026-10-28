"""LEI da fala limpa (regra do usuário, 28/10/2026: "não pode deixar de remover repetições de fala... ele tenta falar,
dá uma pausa e vai, tem que remover essas coisas, não pode existir"). Roda ANTES de montar a timeline.

A transcrição do DaVinci esconde repetição: junta "por metro... por metro quadrado" numa palavra "metro" de 3,27 s.
Aqui a fala é transcrita LITERAL (mlx-whisper large-v3-turbo, com prompt de fala hesitante, cache ao lado da gravação)
e o detector tira:
  RETAKE / FALSO COMEÇO  a 1ª tentativa é o começo da 2ª ("você procurou no Google, quanto custa construir por... |
                         você procurou no Google, quanto custa construir por metro quadrado"): fica só a última.
  GAGUEJO                palavra repetida colada ("é, é errado", "o o pedreiro") ou palavra cortada ("constr- construir").
  SILÊNCIO               pausa maior que --pausa (0,25 s) entre palavras: fica --respiro (0,08 s) de cada lado.

  python3 limpar_fala.py <gravação> [--trechos cortes.json] [--saida limpo.json] [--pausa 0.25] [--respiro 0.08]

--trechos: {"trechos": [[ini, fim], ...]} ou [[ini, fim], ...] em segundos da gravação (o que já foi escolhido para o
vídeo); sem ele, a gravação inteira. Saída: {"trechos": [...], "removidos": [...], "texto": "..."} e o texto final
impresso, para ler antes de montar. Também grava <gravação>.literal.json (transcrição literal, formato segments/words
com "text") que serve de fonte para a legenda.
"""
import json, os, re, subprocess, sys, tempfile, unicodedata

PROMPT = ("Então, é, é... o o pedreiro, ele, ele vai, vai fazer a a obra, né? Hum, quanto, quanto custa, "
          "por metro, por metro quadrado.")


def norm(s):
    """minúscula sem pontuação, MANTENDO acento ("e" e "é" são palavras diferentes: "civil e é modelado")"""
    return re.sub(r"[^\w]+", "", unicodedata.normalize("NFC", s.lower()))


def literal(arquivo):
    cache = arquivo + ".literal.json"
    if os.path.exists(cache):
        return json.load(open(cache, encoding="utf-8"))
    import mlx_whisper
    wav = os.path.join(tempfile.mkdtemp(), "a.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", arquivo, "-ac", "1", "-ar", "16000", wav], check=True)
    r = mlx_whisper.transcribe(wav, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language="pt",
                               word_timestamps=True, condition_on_previous_text=False, initial_prompt=PROMPT)
    out = {"segments": [{"start": s["start"], "end": s["end"],
                         "words": [{"text": w["word"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)}
                                   for w in s.get("words", []) if w["word"].strip()]} for s in r["segments"]]}
    json.dump(out, open(cache, "w", encoding="utf-8"), ensure_ascii=False)
    return out


def literal_trechos(arquivo, trechos, folga=0.4):
    """Transcrição literal TRECHO A TRECHO (28/10/2026: a do arquivo inteiro desalinha os tempos no começo, depois de
    silêncio: "Por que que na parede..." caía 5 s antes da fala real e o corte comia frase). Cache por trecho."""
    import mlx_whisper
    cache = arquivo + ".trechos.json"
    c = json.load(open(cache, encoding="utf-8")) if os.path.exists(cache) else {}
    out = []
    for a, b in trechos:
        x, y = max(0.0, a - folga), b + folga; k = f"{x:.2f}-{y:.2f}"
        if k not in c:
            wav = os.path.join(tempfile.mkdtemp(), "t.wav")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{x:.3f}", "-to", f"{y:.3f}", "-i", arquivo, "-ac", "1", "-ar", "16000", wav], check=True)
            r = mlx_whisper.transcribe(wav, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language="pt",
                                       word_timestamps=True, condition_on_previous_text=False, initial_prompt=PROMPT)
            c[k] = [{"text": w["word"].strip(), "start": round(x + w["start"], 3), "end": round(x + w["end"], 3)}
                    for sg in r["segments"] for w in sg.get("words", []) if w["word"].strip()]
            json.dump(c, open(cache, "w", encoding="utf-8"), ensure_ascii=False)
        # só as palavras que caem dentro do trecho (a folga é para não cortar a 1ª/última sílaba na transcrição)
        out += [w for w in c[k] if w["end"] > a + 0.03 and w["start"] < b - 0.03 and not (out and w["start"] < out[-1]["end"] - 0.02)]
    return out


def _envelope(arquivo, passo=0.02):
    """nível (dB) a cada 20 ms do áudio da gravação, ou None"""
    try:
        import numpy as np
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", arquivo, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
        a = np.frombuffer(raw, np.int16).astype(float) / 32768; h = int(16000 * passo); n = len(a) // h
        rms = np.sqrt((a[:n * h].reshape(n, h) ** 2).mean(axis=1) + 1e-12)
        return list(20 * np.log10(rms)), passo
    except Exception:
        return None


def _igual(a, b):
    """mesma palavra, ou a 1ª é o pedaço cortado da 2ª ("constr" / "construir")"""
    return a == b or (len(a) >= 3 and b.startswith(a))


def detectar(ws):
    """[(ini_s, fim_s, motivo, texto)] dos trechos a tirar (retake, gaguejo)."""
    n = [norm(w["text"]) for w in ws]; tira = []; i = 0
    while i < len(ws):
        achou = None
        for j in range(i + 1, min(len(ws), i + 16)):
            if not n[i] or not _igual(n[i], n[j]) or ws[j]["start"] - ws[i]["start"] > 12: continue
            m = 0
            while j + m < len(ws) and i + m < j and _igual(n[i + m], n[j + m]): m += 1
            vao = j - i
            # retake = a 1ª tentativa INTEIRA é o começo da 2ª, ou só sobra 1 palavra CORTADA ("por...", "constr-");
            # frase paralela NÃO é retake ("tem gente dizendo que flopou, tem gente dizendo que não"; "não foi o
            # temporal, foi o projeto"): sobra palavra inteira diferente. Gaguejo = palavra repetida colada.
            sobra = ws[i + m]["text"] if m < vao else ""
            cortada = sobra.endswith(("...", "…", "-")) or (len(norm(sobra)) <= 3 and not sobra.endswith((",", ".", "?", "!")))
            gag = vao == 1 and m == 1 and not n[i].isdigit() and ws[j]["start"] - ws[i]["end"] < 1.0   # colada de verdade
            if gag or (m >= 2 and (m == vao or (vao - m == 1 and cortada))):
                achou = (j, "GAGUEJO" if vao == 1 else "RETAKE"); break
        if achou:
            j, motivo = achou
            tira.append((ws[i]["start"], ws[j]["start"], motivo, " ".join(w["text"] for w in ws[i:j])))
            i = j
        else:
            i += 1
    # palavra abandonada ("Já... já... Por que"): o whisper marca com reticências; sai, e a pausa junto
    for k, w in enumerate(ws):
        if w["text"].endswith(("...", "…")) and not any(a <= w["start"] < b for a, b, *_ in tira):
            fim = ws[k + 1]["start"] if k + 1 < len(ws) else w["end"]
            tira.append((w["start"], fim, "HESITAÇÃO", w["text"]))
    return sorted(tira)


def limpar(arquivo, trechos=None, pausa=0.25, respiro=0.08):
    if trechos is None:
        d = literal(arquivo); ws0 = [w for s in d["segments"] for w in s["words"]]
        trechos = [[0.0, ws0[-1]["end"] + 0.5]] if ws0 else []
    ws = literal_trechos(arquivo, trechos)
    # palavra conta se ENCOSTA no trecho (o tempo do whisper é impreciso: "Por" do começo caía fora pelo meio)
    dentro = lambda w: any(w["end"] > a + 0.05 and w["start"] < b - 0.05 for a, b in trechos)
    ws = [w for w in ws if dentro(w)]
    tira = detectar(ws)
    fora = lambda w: any(a - 0.01 <= w["start"] < b - 0.01 for a, b, *_ in tira)
    fica = [w for w in ws if not fora(w)]
    # trechos de fala: palavra com respiro, juntando quando a pausa é curta; nunca fora dos trechos escolhidos
    blocos = []
    for w in fica:
        a, b = w["start"] - respiro, w["end"] + respiro
        if blocos and a - blocos[-1][1] <= max(0.0, pausa - 2 * respiro) and not any(blocos[-1][1] <= x < a for x, *_ in tira):
            blocos[-1][1] = max(blocos[-1][1], b)
        else:
            blocos.append([a, b])
    final = []
    for a, b in blocos:
        for ta, tb in trechos:
            x, y = max(a, ta), min(b, tb)
            if y - x > 0.05: final.append([round(x, 3), round(y, 3)])
    # nada de um retake pode sobrar dentro de um bloco
    limpo = []
    for a, b in final:
        cortes = sorted([(x, y) for x, y, *_ in tira if x < b and y > a])
        cur = a
        for x, y in cortes:
            if x - cur > 0.05: limpo.append([round(cur, 3), round(x, 3)])
            cur = max(cur, y)
        if b - cur > 0.05: limpo.append([round(cur, 3), round(b, 3)])
    # silêncio pelo ÁUDIO: o whisper estica o fim da palavra para dentro da pausa; trecho sem voz > pausa é cortado
    # (fica o respiro), independente da transcrição (28/10/2026: vídeo saía MAIS longo que o do silencios.py)
    env = _envelope(arquivo)
    if env is not None:
        db, passo = env
        topo = sorted(db)[int(len(db) * 0.6):]
        ref = topo[len(topo) // 2] if topo else -20
        voz = [x > ref - 16 for x in db]
        refinado = []
        for a, b in limpo:
            i0, i1 = int(a / passo), min(len(voz), int(b / passo)); cur = a; k = i0
            while k < i1:
                if not voz[k]:
                    j = k
                    while j < i1 and not voz[j]: j += 1
                    if (j - k) * passo > pausa and k > i0 and j < i1:
                        x, y = k * passo + respiro, j * passo - respiro
                        if x - cur > 0.05: refinado.append([round(cur, 3), round(x, 3)])
                        cur = y
                    k = j
                else:
                    k += 1
            if b - cur > 0.05: refinado.append([round(cur, 3), round(b, 3)])
        limpo = refinado
    texto = " ".join(w["text"] for w in fica)
    json.dump({"segments": [{"start": fica[0]["start"] if fica else 0, "end": fica[-1]["end"] if fica else 0, "words": fica}]},
              open(arquivo + ".literal.json", "w", encoding="utf-8"), ensure_ascii=False)
    return {"trechos": limpo, "removidos": [{"ini": round(a, 2), "fim": round(b, 2), "motivo": m, "texto": t} for a, b, m, t in tira],
            "texto": texto, "total": round(sum(b - a for a, b in limpo), 2)}


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: raise SystemExit(__doc__)
    arq = a[0]
    tr = None
    if "--trechos" in a:
        t = json.load(open(a[a.index("--trechos") + 1], encoding="utf-8")); tr = t["trechos"] if isinstance(t, dict) else t
    pausa = float(a[a.index("--pausa") + 1]) if "--pausa" in a else 0.25
    resp = float(a[a.index("--respiro") + 1]) if "--respiro" in a else 0.08
    r = limpar(arq, tr, pausa, resp)
    if "--saida" in a:
        json.dump(r, open(a[a.index("--saida") + 1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for x in r["removidos"]: print(f"  - {x['motivo']:8s} {x['ini']:7.2f}-{x['fim']:7.2f}  {x['texto']}")
    print(f"{len(r['trechos'])} trechos, {r['total']} s de fala")
    print(r["texto"])
