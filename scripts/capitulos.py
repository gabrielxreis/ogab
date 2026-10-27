"""Capítulos do YouTube a partir da transcrição, conferidos com as regras do próprio YouTube.

  python3 capitulos.py <transcricao.json | .srt | .vtt> [--alvo 8] [--json]

Lê o transcricao.json da /ogab (DaVinci, whisper ou vtt_transcricao.py), .srt ou .vtt. Imprime o bloco para colar na
descrição. Regras do YouTube, conferidas aqui em vez de supostas: começar em 0:00, no mínimo 3 capítulos e cada um com
10 s ou mais. Um bloco que quebra qualquer uma delas fica parado na descrição e NÃO vira capítulo.

As divisas saem das pausas que a pessoa fez, pesadas pelo tamanho da pausa e por quanto o vocabulário muda de um lado
para o outro. Os títulos impressos são as palavras do assunto: rascunho para reescrever como a promessa do trecho
(3 a 5 palavras), nunca para colar como estão.

Adaptado de youtube-agent-skill (c) 2026 Jake Schincariol, licença MIT.
"""
import json, os, re, sys, unicodedata

PARADA = set("""a o as os um uma uns umas de da do das dos em na no nas nos por pra pro para com sem sobre entre
e ou mas que se quando onde como porque porquê pois então ent tipo assim isso isto esse essa este esta aquele aquela
ele ela eles elas eu tu voce você vocês voces nos nós me te lhe meu minha seu sua nosso nossa dele dela
é e foi era ser estar esta está estão estava tem ter tinha vai vou ia já ja não nao sim muito muita mais menos bem
aqui ali lá la agora depois antes até ate ainda também tambem só so todo toda todos todas cada outro outra mesmo
coisa coisas gente aí ai né ne pode podem fazer faz fez dizer disse falar olha vamos vem veio sabe acho então
qual quais quem porque gente vez vezes dia hoje naquela naquele nessa nesse nesta neste daquela daquele dessa desse
pelo pela pelos pelas numa num""".split())


def _sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _ts(s):
    s = s.strip().replace(",", ".")
    p = s.split(":")
    return int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2]) if len(p) == 3 else int(p[0]) * 60 + float(p[1])


def trechos(caminho):
    """[(ini, fim, texto)] de transcricao.json (segments/words), .srt ou .vtt. Com tempo por palavra, reagrupa por
    pausa (>= 0,5 s), ponto final ou 15 palavras, para as pausas reais aparecerem entre os trechos."""
    bruto = open(caminho, encoding="utf-8", errors="replace").read()
    if caminho.endswith(".json"):
        d = json.loads(bruto)
        segs = d.get("segments", d if isinstance(d, list) else [])
        ws = [w for s in segs for w in s.get("words", []) if (w.get("text") or w.get("word") or "").strip()]
        if ws:
            out, cur = [], []
            for w in ws:
                txt = (w.get("text") or w.get("word")).strip()
                ini, fim = float(w["start"]), float(w["end"])
                if cur and (ini - cur[-1][1] >= 0.5 or len(cur) >= 15):
                    out.append(cur); cur = []
                cur.append((ini, fim, txt))
                if txt[-1:] in ".?!":
                    out.append(cur); cur = []
            if cur:
                out.append(cur)
            return [(c[0][0], c[-1][1], " ".join(x[2] for x in c)) for c in out]
        return [(float(s["start"]), float(s["end"]), (s.get("text") or "").strip()) for s in segs if s.get("text")]
    cues, cur = [], None
    for linha in bruto.splitlines():
        m = re.match(r"\s*(\d[\d:.,]+)\s*-->\s*(\d[\d:.,]+)", linha)
        if m:
            cur = [_ts(m.group(1)), _ts(m.group(2)), []]
            cues.append(cur)
        elif cur is not None and linha.strip() and not linha.strip().isdigit():
            cur[2].append(re.sub(r"<[^>]+>", "", linha.strip()))
    return [(a, b, " ".join(t)) for a, b, t in cues if t]


def palavras_chave(texto):
    return {w for w in re.findall(r"[a-zà-ÿ']{4,}", texto.lower()) if _sem_acento(w) not in PARADA and w not in PARADA}


def mmss(t):
    t = int(t); h, m, s = t // 3600, (t % 3600) // 60, t % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def capitulos(cues, alvo=7, minimo=10.0):
    dur = cues[-1][1]
    cand = []
    for i in range(1, len(cues)):
        pausa = cues[i][0] - cues[i - 1][1]
        kb = palavras_chave(" ".join(c[2] for c in cues[max(0, i - 12):i]))
        ka = palavras_chave(" ".join(c[2] for c in cues[i:i + 12]))
        troca = 1 - (len(kb & ka) / len(kb | ka)) if (kb | ka) else 0
        cand.append((pausa * 1.6 + troca * 3.2, cues[i][0]))
    cand.sort(reverse=True)
    marcas = [0.0]
    for _, t in cand:
        if len(marcas) >= alvo:
            break
        if all(abs(t - p) >= minimo for p in marcas) and dur - t >= minimo:
            marcas.append(t)
    marcas.sort()
    caps = []
    for n, t in enumerate(marcas):
        fim = marcas[n + 1] if n + 1 < len(marcas) else dur
        texto = " ".join(c[2] for c in cues if c[0] >= t and c[1] <= fim)
        kw = sorted(palavras_chave(texto), key=lambda w: -texto.lower().count(w))
        caps.append({"inicio": round(t, 2), "rotulo": mmss(t), "rascunho": " ".join(w.capitalize() for w in kw[:3]) or "Trecho",
                     "segundos": round(fim - t, 2)})
    ok = len(caps) >= 3 and caps[0]["inicio"] == 0 and all(c["segundos"] >= minimo for c in caps)
    return caps, ok


def main(a):
    como_json = "--json" in a
    alvo = int(a[a.index("--alvo") + 1]) if "--alvo" in a else 7
    arqs = [x for x in a if not x.startswith("--") and not x.isdigit()]
    if not arqs or not os.path.exists(arqs[0]):
        sys.exit(__doc__)
    cues = trechos(arqs[0])
    if len(cues) < 6:
        sys.exit("transcrição curta demais para capítulos (menos de 6 trechos)")
    caps, ok = capitulos(cues, alvo)
    if como_json:
        print(json.dumps({"valido": ok, "capitulos": caps}, ensure_ascii=False, indent=1)); return
    print()
    for c in caps:
        print(f"{c['rotulo']} {c['rascunho']}")
    print(f"\n{len(caps)} capítulos" + ("" if ok else "  -- INVÁLIDO: o YouTube exige 3 ou mais, o 1º em 0:00 e 10 s no mínimo cada"))
    print("Reescrever cada título (3-5 palavras, a promessa do trecho) antes de colar: estas são só as palavras do assunto.")


if __name__ == "__main__":
    main(sys.argv[1:])
