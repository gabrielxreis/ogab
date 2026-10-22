"""Plano de edição preso à PALAVRA, não ao segundo: motion, b-roll, lettering e SFX guardam em que palavra entram.
Quando a narração é regravada, a voz IA muda ou o roteiro troca uma frase, tudo se reposiciona sozinho na fala nova.
Ideia estudada no hypit (22/10/2026), código nosso.

  python3 ancorar.py criar <transcricao.json> --sfx sfx/plano_sfx.txt [--motions motions.json] [--saida ancoras.json]
  python3 ancorar.py criar <transcricao.json> --eventos eventos.json [--saida ancoras.json]
  python3 ancorar.py resolver <ancoras.json> <transcricao_nova.json> [--pasta <saida>]
  python3 ancorar.py ver <ancoras.json>

criar: lê um plano em segundos e grava, para cada evento, a palavra de entrada (e a de saída, se tiver duração),
       a posição dela na fala (índice e ocorrência) e o deslocamento em relação ao começo da palavra.
       --sfx    plano_sfx.txt da skill ('T.TTs Ax nome -NNdB[ D.Ds]: comentário')
       --motions [[arquivo, segundo], ...] (a lista do colocar_motions) ou [{"arquivo","em","dur"}]
       --eventos [{"tipo": "broll"|"lettering"|..., "em": s, "dur": s opcional, ...qualquer outro campo}]
resolver: alinha a fala antiga com a nova (sequência de palavras) e recalcula cada tempo. Grava na --pasta
       plano_sfx.txt, motions.json e eventos.json nos MESMOS formatos (prontos para colocar_plano_sfx/colocar_motions)
       e avisa o que perdeu a palavra (frase cortada do roteiro): esses ficam presos à palavra vizinha mais próxima.
Transcrição em segundos (transcrever.py; a do DaVinci já sai convertida pelo --clipe).
"""
import difflib, json, os, re, sys, unicodedata


def _norm(w):
    w = unicodedata.normalize("NFKD", w.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in w if not unicodedata.combining(c)))


def palavras(tr):
    return [{"t": w["text"].strip(), "n": _norm(w["text"]), "i": float(w["start"]), "f": float(w["end"])}
            for s in tr.get("segments", []) for w in s.get("words", []) if _norm(w.get("text", ""))]


def _indice(ws, t):
    """Palavra que está sendo dita em t; numa pausa, a próxima (o evento costuma entrar com a palavra seguinte)."""
    for k, w in enumerate(ws):
        if t < w["f"]:
            return k if t >= w["i"] - 0.6 or k == 0 else (k if w["i"] - t < t - ws[k - 1]["f"] else k - 1)
    return len(ws) - 1


def ancora(ws, t):
    k = _indice(ws, t)
    oc = sum(1 for w in ws[:k + 1] if w["n"] == ws[k]["n"])
    return {"palavra": ws[k]["t"], "indice": k, "ocorrencia": oc, "desloc": round(t - ws[k]["i"], 3),
            "contexto": " ".join(w["t"] for w in ws[max(0, k - 2):k + 3])}


def criar(tr, sfx=None, motions=None, eventos=None):
    ws = palavras(tr)
    if not ws:
        raise SystemExit("transcrição sem palavras")
    out = {"versao": 1, "palavras": [w["t"] for w in ws], "eventos": []}

    def add(tipo, em, dur=None, **resto):
        e = {"tipo": tipo, "entra": ancora(ws, em), **resto}
        if dur:
            e["sai"] = ancora(ws, em + dur); e["dur_original"] = dur
        out["eventos"].append(e)
    if sfx:
        for l in open(sfx, encoding="utf-8").read().splitlines():
            m = re.match(r"\s*([\d.]+)s (A\d) (\S+) (-?\d+)dB(?: ([\d.]+)s)?(.*)", l)
            if m:
                add("sfx", float(m[1]), None, trilha=m[2], nome=m[3], db=int(m[4]),
                    dmax=float(m[5]) if m[5] else None, resto=m[6])
    if motions:
        for x in json.load(open(motions, encoding="utf-8")):
            if isinstance(x, list):
                add("motion", float(x[1]), None, arquivo=x[0])
            else:
                add("motion", float(x["em"]), x.get("dur"), **{k: v for k, v in x.items() if k not in ("em", "dur")})
    if eventos:
        for x in json.load(open(eventos, encoding="utf-8")):
            add(x.get("tipo", "evento"), float(x["em"]), x.get("dur"),
                **{k: v for k, v in x.items() if k not in ("em", "dur", "tipo")})
    return out


def _mapa(antigas, novas):
    """índice antigo -> índice novo pelas palavras que continuam iguais (difflib sobre as palavras normalizadas)."""
    a, b = [_norm(w) for w in antigas], [w["n"] for w in novas]
    m = {}
    for bloco in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for j in range(bloco.size):
            m[bloco.a + j] = bloco.b + j
    return m


def _tempo(anc, mapa, novas, n_antigas):
    k = anc["indice"]
    if k in mapa:
        return novas[mapa[k]]["i"] + anc["desloc"], None
    for d in range(1, n_antigas):   # palavra sumiu: vizinha mais próxima que ficou
        for kk in (k + d, k - d):
            if kk in mapa:
                w = novas[mapa[kk]]
                return (w["i"] if kk > k else w["f"]), f"'{anc['palavra']}' saiu da fala; preso a '{w['t']}'"
    return None, f"'{anc['palavra']}' sem nenhuma palavra em comum"


def resolver(anc, tr_nova):
    novas = palavras(tr_nova)
    mapa = _mapa(anc["palavras"], novas)
    res, avisos = [], []
    for e in anc["eventos"]:
        t, av = _tempo(e["entra"], mapa, novas, len(anc["palavras"]))
        if t is None:
            avisos.append(f"{e['tipo']} {e.get('nome') or e.get('arquivo') or ''}: {av} (fica de fora)"); continue
        if av:
            avisos.append(f"{e['tipo']} {e.get('nome') or e.get('arquivo') or ''}: {av}")
        r = dict(e, em=round(max(0.0, t), 3))
        if "sai" in e:
            t2, av2 = _tempo(e["sai"], mapa, novas, len(anc["palavras"]))
            r["dur"] = round(t2 - t, 3) if t2 and t2 > t else e.get("dur_original")
        res.append(r)
    return res, avisos, len(mapa) / max(1, len(anc["palavras"]))


def gravar(res, pasta):
    os.makedirs(pasta, exist_ok=True)
    feitos = []
    sfx = sorted((e for e in res if e["tipo"] == "sfx"), key=lambda e: e["em"])
    if sfx:
        f = os.path.join(pasta, "plano_sfx.txt")
        open(f, "w", encoding="utf-8").write("".join(
            f"{e['em']:.2f}s {e['trilha']} {e['nome']} {e['db']}dB" + (f" {e['dmax']}s" if e.get("dmax") else "")
            + (e.get("resto") or "") + "\n" for e in sfx))
        feitos.append(f)
    mot = [e for e in res if e["tipo"] == "motion"]
    if mot:
        f = os.path.join(pasta, "motions.json")
        json.dump([[e["arquivo"], e["em"]] if "dur" not in e else
                   {k: v for k, v in e.items() if k not in ("tipo", "entra", "sai", "dur_original")} for e in mot],
                  open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        feitos.append(f)
    outros = [{k: v for k, v in e.items() if k not in ("entra", "sai", "dur_original")} for e in res
              if e["tipo"] not in ("sfx", "motion")]
    if outros:
        f = os.path.join(pasta, "eventos.json")
        json.dump(outros, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        feitos.append(f)
    return feitos


def main(a):
    if len(a) < 2:
        raise SystemExit(__doc__)

    def arg(n, pad=None):
        return a[a.index(n) + 1] if n in a else pad
    if a[0] == "criar":
        anc = criar(json.load(open(a[1], encoding="utf-8")), arg("--sfx"), arg("--motions"), arg("--eventos"))
        saida = arg("--saida", "ancoras.json")
        json.dump(anc, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{len(anc['eventos'])} evento(s) presos à palavra em {saida}")
    elif a[0] == "resolver" and len(a) >= 3:
        res, avisos, igual = resolver(json.load(open(a[1], encoding="utf-8")), json.load(open(a[2], encoding="utf-8")))
        pasta = arg("--pasta", os.path.dirname(os.path.abspath(a[1])))
        for f in gravar(res, pasta):
            print(f)
        print(f"{len(res)} evento(s) reposicionados; {igual:.0%} das palavras continuam iguais")
        for av in avisos:
            print("  AVISO:", av)
    elif a[0] == "ver":
        anc = json.load(open(a[1], encoding="utf-8"))
        for e in anc["eventos"]:
            s = f" até '{e['sai']['palavra']}'" if "sai" in e else ""
            print(f"- {e['tipo']:<9} {e.get('nome') or e.get('arquivo') or e.get('texto') or ''}: "
                  f"entra em '{e['entra']['palavra']}' ({e['entra']['contexto']}){s}")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
