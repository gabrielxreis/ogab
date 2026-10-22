"""Estima quanto tempo um texto leva para ser FALADO, antes de existir a voz (roteiro, storyboard, duração de motion).
Conta sílabas do português (números viram extenso), soma as pausas da pontuação e divide pelo ritmo da voz.
Ideia estudada no hypit (22/10/2026, que só faz inglês e chinês); código nosso, para português.

  python3 estimar.py "O primeiro passo é parar de esperar."                 # segundos do texto
  python3 estimar.py --arquivo roteiro.md [--ritmo normal] [--voz gabriel]  # tabela trecho a trecho + total
  python3 estimar.py calibrar <transcricao.json> --voz <nome>               # mede o ritmo REAL de uma voz e guarda

Ritmos (sílabas por segundo, sem contar as pausas): calmo 4.8, normal 5.8, rapido 7.0, ou um número (--ritmo 6.2).
--voz usa o ritmo calibrado daquela voz (config.json > "fala_ritmo"); calibrar depois do primeiro vídeo de cada voz
(ElevenLabs, clone, apresentador) deixa a estimativa bem mais certa. É aproximação: serve para decidir duração de
cena, de motion e cortar roteiro grande, não substitui medir a fala real (regra: motion com a duração da fala).
No --arquivo, cada linha não vazia é um trecho; linhas de título (#) e marcações [entre colchetes] não contam.
"""
import json, os, re, sys, unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(RAIZ, "config.json")
RITMOS = {"calmo": 4.8, "normal": 5.8, "rapido": 7.0, "rápido": 7.0}
PAUSAS = {",": 0.15, ";": 0.25, ":": 0.25, ".": 0.35, "!": 0.35, "?": 0.35, "…": 0.5, "...": 0.5, "\n": 0.35}
VOGAIS = "aeiouáéíóúâêôãõàü"

UNID = "zero um dois três quatro cinco seis sete oito nove dez onze doze treze catorze quinze dezesseis dezessete dezoito dezenove".split()
DEZ = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"]
CEM = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"]


def extenso(n):
    n = int(n)
    if n < 20:
        return UNID[n]
    if n < 100:
        return DEZ[n // 10] + ("" if n % 10 == 0 else " e " + UNID[n % 10])
    if n == 100:
        return "cem"
    if n < 1000:
        return CEM[n // 100] + ("" if n % 100 == 0 else " e " + extenso(n % 100))
    for valor, sing, plur in ((10 ** 9, "bilhão", "bilhões"), (10 ** 6, "milhão", "milhões"), (1000, "mil", "mil")):
        if n >= valor:
            q, r = divmod(n, valor)
            cab = ("mil" if valor == 1000 and q == 1 else extenso(q) + " " + (sing if q == 1 else plur))
            return cab + ("" if r == 0 else (" e " if r < 100 or r % 100 == 0 and r < 1000 else " ") + extenso(r))
    return str(n)


def _numeros(txt):
    txt = re.sub(r"R\$\s*([\d.]+)(?:,(\d{2}))?", lambda m: m.group(1) + " reais" + (" e " + m.group(2) + " centavos" if m.group(2) and int(m.group(2)) else ""), txt)
    txt = re.sub(r"(\d+)\s*%", r"\1 por cento", txt)
    txt = re.sub(r"(\d+),(\d+)", lambda m: m.group(1) + " vírgula " + m.group(2), txt)
    txt = re.sub(r"(\d+)\s*(mil|milhões|milhão|bilhões|bilhão|k)\b", lambda m: m.group(1) + " " + ("mil" if m.group(2) == "k" else m.group(2)), txt)
    return re.sub(r"\d[\d.]*", lambda m: extenso(m.group(0).replace(".", "")) if m.group(0).replace(".", "").isdigit() else m.group(0), txt)


def silabas(palavra):
    """Sílabas de uma palavra em português (heurística: núcleos vocálicos, ditongos e 'qu'/'gu' mudos)."""
    p = palavra.lower()
    p = re.sub(r"[^a-záéíóúâêôãõàüç]", "", p)
    if not p:
        return 0
    p = re.sub(r"(q|g)u(?=[eiéí])", r"\1", p)             # que, gue, qui, gui: u mudo
    p = re.sub(r"q(u)(?=[aoáó])", "qw", p)                  # quando, qual: u semivogal
    p = re.sub(r"ão|ãe|õe|ãos|ões", "Ã", p)                 # nasais: uma sílaba
    p = re.sub(r"(?<=[aeoáéóâêô])[iu](?![aeiouáéíóú]|[mnrlz]\b|nh)", "", p)   # ditongo decrescente: ai, ei, oi, au, eu, ou
    p = re.sub(r"(?<=[iu])u|(?<=u)i(?![mn]\b)", "", p)     # iu, ui (fui, partiu); ruim é hiato
    n = 0; antes = False
    for c in p:
        v = c in VOGAIS or c == "Ã"
        if v and not antes:
            n += 1
        elif v and antes:
            n += 1                                           # hiato (saúde, poeta, dia)
        antes = v
    return max(1, n)


def _limpar(txt):
    txt = unicodedata.normalize("NFC", txt)
    txt = re.sub(r"\[[^\]]*\]", " ", txt)                   # marcações [pausa], [risos]
    txt = re.sub(r"[*_#>`]", " ", txt)
    return _numeros(txt)


def _ritmo(ritmo=None, voz=None):
    if voz:
        try:
            r = json.load(open(CONFIG, encoding="utf-8")).get("fala_ritmo", {}).get(voz)
            if r:
                return float(r)
        except Exception:
            pass
    if ritmo is None:
        return RITMOS["normal"]
    return RITMOS.get(str(ritmo).lower()) or float(ritmo)


def estimar(texto, ritmo=None, voz=None):
    """{"segundos", "fala", "pausas", "silabas", "palavras"} do texto."""
    t = _limpar(texto)
    sil = sum(silabas(w) for w in re.findall(r"[A-Za-zÀ-ÿ]+", t))
    pausa = sum(PAUSAS[p] for p in re.findall(r"\.\.\.|…|[,;:.!?]|\n", t.strip()))
    fala = sil / _ritmo(ritmo, voz)
    return {"segundos": round(fala + pausa, 2), "fala": round(fala, 2), "pausas": round(pausa, 2), "silabas": sil,
            "palavras": len(re.findall(r"[A-Za-zÀ-ÿ]+", t))}


def calibrar(transcricao, voz):
    """Ritmo real (sílabas/s sem as pausas) de uma transcrição com tempo por palavra; grava em config.json."""
    tr = json.load(open(transcricao, encoding="utf-8"))
    sil, tempo = 0, 0.0
    for s in tr.get("segments", []):
        for w in s.get("words", []):
            try:
                i, f = float(w["start"]), float(w["end"])
            except (TypeError, ValueError):
                raise SystemExit("transcrição com timecode: gerar em segundos (transcrever.py)")
            if 0 < f - i < 2.0:
                sil += sum(silabas(x) for x in re.findall(r"[A-Za-zÀ-ÿ]+", _limpar(w.get("text", ""))))
                tempo += f - i
    if tempo < 3:
        raise SystemExit("fala curta demais para calibrar (precisa de pelo menos ~3 s de palavras)")
    r = round(sil / tempo, 2)
    cfg = json.load(open(CONFIG, encoding="utf-8")) if os.path.exists(CONFIG) else {}
    cfg.setdefault("fala_ritmo", {})[voz] = r
    json.dump(cfg, open(CONFIG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return r


def main(a):
    if not a:
        raise SystemExit(__doc__)

    def arg(n, pad=None):
        return a[a.index(n) + 1] if n in a else pad
    if a[0] == "calibrar" and len(a) >= 2 and "--voz" in a:
        print(f"ritmo da voz {arg('--voz')}: {calibrar(a[1], arg('--voz'))} sílabas/s (guardado no config.json)")
        return
    ritmo, voz = arg("--ritmo"), arg("--voz")
    if "--arquivo" in a:
        tot = 0.0
        print(f"ritmo: {_ritmo(ritmo, voz)} sílabas/s\n")
        for n, linha in enumerate(open(arg("--arquivo"), encoding="utf-8").read().splitlines(), 1):
            if not linha.strip() or linha.lstrip().startswith("#"):
                continue
            e = estimar(linha + "\n", ritmo, voz); tot += e["segundos"]
            print(f"{n:>4}  {e['segundos']:>5.1f} s  (acumulado {tot:>5.1f} s)  {linha.strip()[:70]}")
        print(f"\nTOTAL: {tot:.1f} s")
        return
    e = estimar(" ".join(x for x in a if not x.startswith("--") and x not in (ritmo, voz)), ritmo, voz)
    print(f"{e['segundos']} s  (fala {e['fala']} s + pausas {e['pausas']} s; {e['silabas']} sílabas, {e['palavras']} palavras)")


if __name__ == "__main__":
    main(sys.argv[1:])
