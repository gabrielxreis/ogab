"""Conferência OBRIGATÓRIA das emendas de corte de fala (regra do usuário, 25/10/2026: "você cortou frases e não se
conectavam, isso jamais pode acontecer"; "logo no início eu dou boas-vindas 2x").

Para cada emenda mostra o fim do trecho anterior | o começo do seguinte (as palavras REAIS da transcrição) e marca:
  FRASE CORTADA   o trecho anterior não termina em fim de frase, ou o seguinte começa no meio de uma
  REPETE          a emenda junta a mesma palavra/expressão dos dois lados ("vamos lá | vamos lá")
  DUPLICADO       a mesma fala (5+ palavras) aparece duas vezes no corte final (ex.: duas boas-vindas, dois retakes)
Sai com código 1 se houver qualquer marca: resolver TODAS (mover o corte para o fim/começo da frase inteira, tirar o
retake inteiro) antes de montar ou mostrar. Depois, ouvir cada emenda marcada como OK no DaVinci.

  python3 emendas.py <cortes.json> <pasta_transcricoes> [--contexto 10]

cortes.json: [[clipe, ini_s, fim_s], ...] ou {"cortes": [...]} na ordem da timeline (um clipe só também serve).
<pasta_transcricoes>/<clipe>.json no formato do transcrever.py ({"segments": [{"words": [{"text"|"word", "start", "end"}]}]}).
A transcrição TEM que ser a do DaVinci (transcrever.py --clipe): o Whisper limpa a fala e some com repetições e
falsos começos, então a duplicata nem aparece no texto (foi o que deixou passar as duas boas-vindas).
"""
import json, os, re, sys, unicodedata

FIM_FRASE = re.compile(r"[.!?…]$")
CONECTIVOS = {"e", "mas", "que", "porque", "pra", "para", "de", "do", "da", "dos", "das", "no", "na", "o", "a", "os", "as",
              "um", "uma", "com", "por", "se", "em", "ou", "nem", "quando", "como", "então", "entao", "aí", "ai", "tipo"}


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z0-9]+", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def _seg(v, fps=30.0):
    if isinstance(v, str) and v.count(":") == 3:
        h, m, s, f = (int(x) for x in v.split(":")); return h * 3600 + m * 60 + s + f / fps
    return float(v)


def palavras(arq):
    d = json.load(open(arq, encoding="utf-8")); fps = float(d.get("fps", 30)); ws = []
    if "whisper" in str(d.get("motor", "")).lower() or ("motor" not in d and "text" in d and "language" in d):
        print(f"AVISO: {os.path.basename(arq)} parece Whisper: ele apaga repetições e falsos começos. Para cortar fala, "
              "transcrever no DaVinci (transcrever.py --clipe).")
    for s in d["segments"]:
        for w in s.get("words", []):
            t = (w.get("text") or w.get("word") or "").strip()
            if norm(t): ws.append((_seg(w["start"], fps), _seg(w["end"], fps), t))
    return ws


def main(a):
    cortes = json.load(open(a[0], encoding="utf-8")); cortes = cortes.get("cortes", cortes) if isinstance(cortes, dict) else cortes
    pasta = a[1]; ctx = int(a[a.index("--contexto") + 1]) if "--contexto" in a else 10
    cache, trechos = {}, []
    for c, ini, fim in cortes:
        if c not in cache: cache[c] = palavras(os.path.join(pasta, c + ".json"))
        trechos.append([w for w in cache[c] if w[0] >= ini - 0.05 and w[1] <= fim + 0.15])
    marcas = 0
    for k in range(1, len(trechos)):
        antes, depois = trechos[k - 1], trechos[k]
        if not antes or not depois: continue
        fa = " ".join(w[2] for w in antes[-ctx:]); fd = " ".join(w[2] for w in depois[:ctx]); m = []
        ultima, primeira = antes[-1][2], depois[0][2]
        if not FIM_FRASE.search(ultima) or norm(ultima) in CONECTIVOS: m.append("FRASE CORTADA (antes não fecha a frase)")
        if norm(primeira) in CONECTIVOS or (primeira[:1].islower() and not FIM_FRASE.search(ultima)): m.append("FRASE CORTADA (depois começa no meio)")
        na, nd = [norm(w[2]) for w in antes[-4:]], [norm(w[2]) for w in depois[:4]]
        if any(na[-n:] == nd[:n] for n in (1, 2, 3, 4) if len(na) >= n and len(nd) >= n): m.append("REPETE na emenda")
        marcas += bool(m)
        print(f"{k:3d} {'!!' if m else 'ok'}  ...{fa}  ||  {fd}...")
        for x in m: print(f"       -> {x}")
    tudo = [norm(w[2]) for t in trechos for w in t]; vistos = {}
    for i in range(len(tudo) - 5):
        g = " ".join(tudo[i:i + 6])
        if g in vistos and 6 < i - vistos[g] < 90:   # retake = a mesma fala de novo logo em seguida (~30 s)
            print(f"DUPLICADO: '{g}' aparece duas vezes (palavras {vistos[g]} e {i}): tirar um dos retakes inteiro"); marcas += 1
        vistos[g] = i
    print(f"\n{len(trechos) - 1} emendas, {marcas} com problema." + (" Resolver TODAS antes de montar." if marcas else " Ouvir as emendas no DaVinci antes de entregar."))
    sys.exit(1 if marcas else 0)


if __name__ == "__main__":
    if len(sys.argv) < 3: print(__doc__); sys.exit(2)
    main(sys.argv[1:])
