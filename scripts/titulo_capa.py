"""Confere título + texto da capa do YouTube como UM par, antes de mostrar as opções ao usuário.

  python3 titulo_capa.py --titulo "..." --capa "3 PALAVRAS"
  python3 titulo_capa.py titulos.txt [--capa "..."]     # um título por linha, em ordem de nota
  python3 titulo_capa.py --titulo "..." --json
  python3 titulo_capa.py buscas "busca 1" "busca 2" "busca 3" [--titulo "..."] [--n 10]

`buscas`: os N primeiros vídeos do YouTube para cada busca que o vídeo deveria ganhar (yt-dlp, sem chave de API):
views, canal, duração, a mediana de views e as palavras que mais se repetem nos títulos de quem está ganhando. Serve
para ver se dá para disputar a busca e para conferir se o título (--titulo) traz as palavras dela.

O par é a unidade, não o título: capa que repete o título desperdiça metade da área de clique (o erro mais comum).
Tamanho: a busca no computador corta perto de 60 caracteres e o feed do celular perto de 40. Os dois são avisados
porque falham diferente: no computador some o fim, no celular pode sumir o assunto.
Regras: capa com 1 a 3 palavras (regra das capas da /ogab), no máximo 2 palavras em CAIXA ALTA no título, número,
nome ou data vale mais que qualquer adjetivo. É uma checagem, não uma previsão de CTR: nota baixa = olhar de novo.

Adaptado de youtube-agent-skill (c) 2026 Jake Schincariol, licença MIT.
"""
import json, os, re, sys, unicodedata

COMPUTADOR, CELULAR, LIMITE = 60, 40, 100
VAGAS = {"incrivel", "insano", "insana", "chocante", "absurdo", "absurda", "surreal", "inacreditavel", "bizarro",
         "impressionante", "enorme", "gigante", "melhor", "melhores", "pior", "segredo", "segredos", "definitivo",
         "definitiva", "epico", "epica", "perfeito", "perfeita", "completo", "completa", "tudo", "top", "revolucionario",
         "poderoso", "poderosa", "louco", "louca", "brabo", "brutal", "ultimo", "unico"}
PARADA = {"a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos", "por",
          "pra", "pro", "para", "com", "e", "ou", "que", "se", "seu", "sua", "voce", "eu", "meu", "minha", "isso",
          "esse", "essa", "este", "esta", "como", "porque", "por que", "quando", "qual", "e", "foi", "nao", "ja"}


def _base(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def palavras(t):
    return re.findall(r"[a-z0-9']+", _base(t))


def _raiz(w):
    return w[:5] if len(w) > 5 else w      # "milionário"/"milionários" contam como repetição


def conferir(titulo, capa=None):
    t = titulo.strip()
    n = len(t)
    prob, bom = [], []
    if n > LIMITE: prob.append(("tamanho", f"{n} caracteres: o limite do YouTube é {LIMITE}"))
    elif n > COMPUTADOR: prob.append(("tamanho", f"{n} caracteres: a busca no computador corta perto de {COMPUTADOR}"))
    else: bom.append(f"{n} caracteres, dentro do corte de {COMPUTADOR} do computador")
    if n > CELULAR:
        cabeca = t[:CELULAR].rsplit(" ", 1)[0]
        prob.append(("celular", f'o feed do celular mostra mais ou menos "{cabeca}...": o assunto sobrevive?'))
    caixa = [w for w in t.split() if len(w) > 2 and w.isupper()]
    if len(caixa) > 2: prob.append(("gritando", f"{len(caixa)} palavras em CAIXA ALTA: duas é o teto antes de parecer spam"))
    elif caixa: bom.append(f"{len(caixa)} palavra{'s' if len(caixa) > 1 else ''} em caixa alta para ênfase")
    v = sorted({w for w in palavras(t) if w in VAGAS})
    if v: prob.append(("vago", f"{', '.join(v)}: trocar por um número, um nome ou uma data"))
    nums = re.findall(r"\d[\d.,]*%?", t)
    nomes = [w for w in t.split()[1:] if w[:1].isupper() and not w.isupper()]
    if nums: bom.append(f"tem um dado concreto ({', '.join(nums[:3])})")
    elif nomes: bom.append(f"tem um nome ({', '.join(nomes[:3])})")
    else: prob.append(("sem-dado", "sem número, data ou nome: o conserto que mais funciona sozinho"))
    if t.endswith("?"): bom.append("pergunta aberta no título")
    if not [w for w in palavras(t)[:3] if w not in PARADA]:
        prob.append(("comeco", "as três primeiras palavras são enchimento: trazer o assunto para a frente"))
    if capa:
        tw = {_raiz(w) for w in palavras(t) if w not in PARADA}
        cw = {_raiz(w) for w in palavras(capa) if w not in PARADA}
        if tw & cw:
            rep = sorted(w for w in palavras(capa) if _raiz(w) in tw & cw)
            prob.append(("repete", f"a capa repete o título em {', '.join(rep)}: a capa diz o que o título não diz"))
        else:
            bom.append("capa e título com palavras diferentes")
        if len(palavras(capa)) > 3:
            prob.append(("capa-longa", f"{len(palavras(capa))} palavras na capa: 3 é o teto no tamanho do feed"))
    nota = max(0, min(100, 100 - 14 * len(prob) + 4 * len(bom)))
    return {"titulo": t, "caracteres": n, "nota": nota, "problemas": prob, "ok": bom}


def mostrar(r):
    print(f'\n"{r["titulo"]}"')
    print(f"{r['caracteres']} caracteres   nota {r['nota']}/100")
    for k, m in r["problemas"]: print(f"  x  {k:<11} {m}")
    for m in r["ok"]:          print(f"  ok             {m}")


def _views(n):
    if n is None:
        return "?"
    return f"{n / 1e6:.1f} mi" if n >= 1e6 else f"{n / 1e3:.0f} mil" if n >= 1e3 else str(n)


def buscas(qs, titulo=None, n=10):
    import statistics, subprocess
    from collections import Counter
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from baixar_video import _ytdlp, _mmss
    tw = {_raiz(w) for w in palavras(titulo or "") if w not in PARADA}
    saida = []
    for q in qs:
        out = subprocess.run([_ytdlp(), f"ytsearch{n}:{q}", "--flat-playlist", "-j", "--no-warnings",
                              "--extractor-args", "youtube:lang=pt"],   # sem isso os títulos vêm traduzidos para inglês
                             capture_output=True, text=True, timeout=120).stdout
        vs = [json.loads(l) for l in out.splitlines() if l.strip()]
        views = [v.get("view_count") for v in vs if v.get("view_count") is not None]
        en = {"the", "and", "how", "why", "what", "with", "for", "full", "this", "that", "from", "you", "your"}
        termos = Counter(w for v in vs for w in set(palavras(v.get("title") or ""))
                         if w not in PARADA and w not in en and len(w) > 2)
        qw = [w for w in palavras(q) if w not in PARADA]
        falta = [w for w in qw if _raiz(w) not in tw] if titulo else None
        r = {"busca": q, "mediana_views": statistics.median(views) if views else None,
             "termos_frequentes": [w for w, k in termos.most_common(8) if k >= 2],
             "faltam_no_titulo": falta,
             "videos": [{"titulo": v.get("title"), "canal": v.get("channel") or v.get("uploader"),
                         "views": v.get("view_count"), "duracao": _mmss(v.get("duration")),
                         "url": v.get("url") or f"https://www.youtube.com/watch?v={v.get('id')}"} for v in vs]}
        saida.append(r)
    return saida


def mostrar_buscas(rs):
    for r in rs:
        print(f'\nBUSCA "{r["busca"]}"   mediana {_views(r["mediana_views"])} views')
        for k, v in enumerate(r["videos"], 1):
            print(f"  {k:>2}. {_views(v['views']):>8}  {v['duracao']:>7}  {(v['canal'] or '')[:22]:<22}  {v['titulo']}")
        if r["termos_frequentes"]:
            print(f"  palavras de quem ganha: {', '.join(r['termos_frequentes'])}")
        if r["faltam_no_titulo"]:
            print(f"  x  o título não traz: {', '.join(r['faltam_no_titulo'])}")
        elif r["faltam_no_titulo"] == []:
            print("  ok o título traz as palavras da busca")
    print()


def main(a):
    como_json = "--json" in a
    if a and a[0] == "buscas":
        op = lambda k: a[a.index(k) + 1] if k in a else None
        usados = {op("--titulo"), op("--n")}
        qs = [x for x in a[1:] if not x.startswith("--") and x not in usados]
        if not qs:
            sys.exit(__doc__)
        rs = buscas(qs, op("--titulo"), int(op("--n") or 10))
        print(json.dumps(rs, ensure_ascii=False, indent=1)) if como_json else mostrar_buscas(rs)
        return
    capa = a[a.index("--capa") + 1] if "--capa" in a else None
    if "--titulo" in a:
        rs = [conferir(a[a.index("--titulo") + 1], capa)]
    else:
        arqs = [x for x in a if not x.startswith("--") and x != capa]
        if not arqs or not os.path.exists(arqs[0]):
            sys.exit(__doc__)
        rs = [conferir(l, capa) for l in open(arqs[0], encoding="utf-8").read().splitlines() if l.strip()]
    rs.sort(key=lambda r: -r["nota"])
    if como_json:
        print(json.dumps(rs, ensure_ascii=False, indent=1)); return
    for r in rs:
        mostrar(r)
    print()


if __name__ == "__main__":
    main(sys.argv[1:])
