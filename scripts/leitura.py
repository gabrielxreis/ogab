"""Duas conferências que pegam erro que o olho deixa passar (ideia estudada no lemo-opuscar, 20/10/2026):

  python3 leitura.py texto <video.mp4> [--passo 0.1] [--json saida.json]
      Tempo de leitura: lê o texto de cada quadro com o OCR do macOS (Vision) e mede quanto tempo cada frase fica
      inteira na tela. Mínimo = 0,3 s por palavra + 0,5 s, nunca menos de 1,0 s; título (até 3 palavras e sozinho)
      mínimo 1,0 s. Abaixo de 60% do mínimo é ERRO; abaixo do mínimo, ou da regra folgada (letras / 15 + 1,5 s) em frase
      de mais de 3 palavras, é aviso. Fica de fora: texto miúdo de interface (linha menor que 2,2% da altura), número
      sozinho (contador) e o que aparece menos de 0,3 s (borrão de transição). Letra cursiva/manuscrita o OCR lê só em
      parte dos quadros: o tempo medido é o mínimo garantido, conferir no olho antes de mexer. O texto que ainda
      está entrando (letra a letra, palavra a palavra) não conta: só a versão completa da frase.
      Feito para motion/lettering (revisor.py chama sozinho). Em vídeo com legenda queimada a legenda também entra;
      legenda tem regra própria (legendas.py), então ler a lista com isso em mente.

  python3 leitura.py voz <audio_ou_video> <roteiro.txt> [--idioma pt]
      Voz IA transcrita de volta: passa o Whisper local no áudio final e compara palavra por palavra com o roteiro
      aprovado. Lista palavra trocada, faltando ou sobrando com o tempo. Pega pronúncia errada da voz clonada
      (nome próprio, número, sigla) antes do cliente ouvir.

Sai com código 1 se houver ERRO.
"""
import difflib, json, os, re, subprocess, sys, tempfile, unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s%$]", " ", s)).strip()


# ---------------------------------------------------------------- texto
def ocr(foto):
    """Linhas de texto da imagem pelo Vision do macOS: [(texto, altura da linha em fração do quadro)]."""
    import Vision
    from Foundation import NSURL
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    req.setRecognitionLanguages_(["pt-BR", "en-US"])
    req.setUsesLanguageCorrection_(True)   # sem ela a cursiva some em metade dos quadros
    h = Vision.VNImageRequestHandler.alloc().initWithURL_options_(NSURL.fileURLWithPath_(foto), None)
    h.performRequests_error_([req], None)
    out = []
    for r in req.results() or []:
        c = r.topCandidates_(1)
        if c and c[0].confidence() >= .5:
            out.append((c[0].string(), r.boundingBox().size.height))
    return out


def texto(video, passo=.1, altura_min=.022):
    tmp = tempfile.mkdtemp(prefix="leitura_")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-i", video, "-vf", f"fps={1 / passo:.4f},scale=720:-2",
                    os.path.join(tmp, "q%05d.png")], check=True)
    fotos = sorted(f for f in os.listdir(tmp) if f.endswith(".png"))
    quadros = []   # [(t, {frase_normalizada: frase_original})]
    for i, f in enumerate(fotos):
        p = os.path.join(tmp, f)
        linhas = ocr(p)
        os.remove(p)
        # Só texto de leitura: letra de verdade (contador e número sozinho mudam de propósito) e tamanho de lettering
        # (texto miúdo de interface/decoração não precisa ser lido inteiro).
        quadros.append((round(i * passo, 3), {norm(l): l for l, h in linhas
                                              if h >= altura_min and len(re.findall(r"[^\W\d_]", l)) >= 3}))
    os.rmdir(tmp)
    # Sequências contínuas de cada frase (tolera 1 quadro perdido pelo OCR).
    corridas, abertas = [], {}
    for t, frases in quadros:
        for k in list(abertas):
            if k not in frases and t - abertas[k]["fim"] > 1.5:   # OCR perde quadros (borrão, letra cursiva): mesma frase em até 1,5 s é a mesma
                corridas.append(abertas.pop(k))
        for k, orig in frases.items():
            if k not in abertas:   # leitura torta da mesma frase ("Palo, rumo") conta como a mesma
                k = next((o for o in abertas if difflib.SequenceMatcher(None, o, k).ratio() >= .75), k)
            if k in abertas:
                abertas[k]["fim"] = t
            else:
                abertas[k] = {"chave": k, "texto": orig, "ini": t, "fim": t}
    corridas += abertas.values()
    # Pedaço de frase entrando (prefixo/trecho de uma frase maior que aparece logo depois) não conta.
    def parcial(c):
        k = c["chave"]
        def pedaco(o):   # c é o começo (ou um trecho) de o, mesmo com o OCR errando uma letra
            ok = o["chave"]
            return k in ok or (len(ok) > len(k) and difflib.SequenceMatcher(None, k, ok[:len(k)]).ratio() >= .75)
        return any(o is not c and k != o["chave"] and pedaco(o) and o["ini"] - 1.5 <= c["fim"] <= o["fim"] + .2 for o in corridas)
    achados = []
    for c in sorted(corridas, key=lambda c: c["ini"]):
        dur = c["fim"] - c["ini"] + passo
        if parcial(c) or dur < .3:   # entrando, ou lido de passagem num quadro borrado de transição
            continue
        palavras = len(c["chave"].split()); letras = len(c["chave"].replace(" ", ""))
        minimo = max(1.0, .3 * palavras + .5)
        folgado = letras / 15 + 1.5
        nivel = ("ERRO" if dur < minimo * .6 else "aviso" if dur < minimo - passo / 2
                 or (palavras > 3 and dur < min(folgado, 4.0) - passo / 2) else None)
        achados.append({**c, "dur": round(dur, 2), "minimo": round(minimo, 2), "folgado": round(folgado, 2), "nivel": nivel})
    return achados


# ---------------------------------------------------------------- voz
U = "zero um dois tres quatro cinco seis sete oito nove dez onze doze treze catorze quinze dezesseis dezessete dezoito dezenove".split()
D = "_ _ vinte trinta quarenta cinquenta sessenta setenta oitenta noventa".split()
C = "_ cento duzentos trezentos quatrocentos quinhentos seiscentos setecentos oitocentos novecentos".split()


def extenso(n):
    """Número por extenso em português (0 a 999.999), para '33' e 'trinta e três' contarem igual."""
    if n < 20: return U[n]
    if n < 100: return D[n // 10] + ("" if n % 10 == 0 else " e " + U[n % 10])
    if n == 100: return "cem"
    if n < 1000: return C[n // 100] + ("" if n % 100 == 0 else " e " + extenso(n % 100))
    m, r = divmod(n, 1000)
    return ("mil" if m == 1 else extenso(m) + " mil") + ("" if r == 0 else (" e " if r < 100 or r % 100 == 0 else " ") + extenso(r))


def palavras(s):
    s = re.sub(r"(?<=\d)\.(?=\d{3})", "", s)
    s = re.sub(r"\d+", lambda m: extenso(int(m.group())) if int(m.group()) < 10 ** 6 else m.group(), s)
    return norm(s).split()

def voz(midia, roteiro, idioma="pt"):
    from transcrever import via_whisper
    tmp = tempfile.mkdtemp(prefix="voz_")
    wav = os.path.join(tmp, "a.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", midia, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
    tr = via_whisper(wav, idioma)
    ouvidas = [(p, w["start"]) for s in tr["segments"] for w in s["words"] for p in palavras(w["text"])]
    esperadas = palavras(open(roteiro, encoding="utf-8").read())
    a, b = esperadas, [p for p, _ in ouvidas]
    difs = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        t = ouvidas[min(j1, len(ouvidas) - 1)][1] if ouvidas else 0
        difs.append({"t": t, "tipo": {"replace": "trocada", "delete": "faltando", "insert": "sobrando"}[op],
                     "roteiro": " ".join(a[i1:i2]), "ouvido": " ".join(b[j1:j2])})
    return difs, len(esperadas)


def main(a):
    if len(a) < 2 or a[0] not in ("texto", "voz"):
        raise SystemExit(__doc__)
    op = lambda k: a[a.index(k) + 1] if k in a else None
    if a[0] == "texto":
        r = texto(a[1], float(op("--passo") or .1), float(op("--altura-min") or .022))
        if op("--json"):
            json.dump(r, open(op("--json"), "w"), ensure_ascii=False, indent=1)
        ruins = [x for x in r if x["nivel"]]
        for x in ruins:
            print(f"{x['nivel']} [{x['ini']:.2f} s] \"{x['texto']}\" fica {x['dur']:.2f} s na tela "
                  f"(mínimo {x['minimo']:.1f} s, confortável {x['folgado']:.1f} s)")
        print(f"{len(r)} frase(s) lida(s), {sum(x['nivel'] == 'ERRO' for x in r)} erro(s), {sum(x['nivel'] == 'aviso' for x in r)} aviso(s)")
        sys.exit(1 if any(x["nivel"] == "ERRO" for x in r) else 0)
    difs, n = voz(a[1], a[2], op("--idioma") or "pt")
    for d in difs:
        print(f"[{d['t']:.1f} s] {d['tipo']}: roteiro \"{d['roteiro']}\" / ouvido \"{d['ouvido']}\"")
    taxa = 100 * (1 - sum(len(d["roteiro"].split()) or len(d["ouvido"].split()) for d in difs) / max(n, 1))
    print(f"{n} palavras no roteiro, {len(difs)} diferença(s), {taxa:.0f}% igual. Ouvir cada trecho listado: "
          "nome próprio, número e sigla trocados são ERRO; vírgula e contração são normais.")
    sys.exit(1 if difs else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
