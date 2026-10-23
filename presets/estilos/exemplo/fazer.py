"""Prévia (exemplo.mp4) de cada ESTILO sobre um TAKE REAL de pessoa (vídeo de banco com licença livre; nunca apresentador
ilustrado, regra do usuário 23/10/2026). O take fica só no cache; no repositório vai só o GIF pequeno.

  python3 presets/estilos/exemplo/fazer.py <id> [<id> ...] [--trab <pasta>] [--todos] [--faltando] [--paralelo N]

Cada estilo usa um take real DIFERENTE do banco do takes.py (~/.cache/ogab_takes/ok; escolha guardada em takes.json;
--trab <pasta> força um take só, para teste),
aplica o estilo com os campos de exemplo do estilo.json (tempos em "exemplo": {"de", "ate"}) pelo motor CENA
(presets/cena/gerar.py) e grava presets/estilos/<grupo>/<id>/exemplo.mp4 (360 px, sem som; o menu toca em loop).
--todos refaz todos; --faltando só os que ainda não têm exemplo.mp4.
"""
import glob, json, os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__)); ESTILOS = os.path.dirname(AQUI); PRESETS = os.path.dirname(ESTILOS)
CENA = os.path.join(PRESETS, "cena")
FALA = ["Olha", "esse", "estilo", "aqui", "no", "seu", "vídeo,", "funciona", "em", "qualquer", "assunto."]


DUR = 5.0
MAPA = os.path.join(AQUI, "takes.json")   # estilo -> take do Pexels (fixo, para a prévia sair igual se refeita)


def gravacao(trab):
    """Take REAL já preparado pelo takes.py (gravacao.mp4 1080x1920 24 qps). Só falta a fala de exemplo; o recorte da
    pessoa o gerar.py faz sozinho quando o estilo precisa (camada atras/silhueta), e o rosto ele detecta (rosto.py)."""
    if not os.path.exists(os.path.join(trab, "gravacao.mp4")):
        raise SystemExit(f"take sem gravacao.mp4: {trab} (rode takes.py filtrar)")
    pal_arq = os.path.join(trab, "palavras.json")
    if not os.path.exists(pal_arq):
        t, pal = .3, []
        for w in FALA:
            d = .16 + .045 * len(w); pal.append({"w": w, "ini": round(t, 3), "fim": round(t + d, 3)}); t += d + .12
        json.dump(pal, open(pal_arq, "w"), ensure_ascii=False)


def takes_por_estilo(ids):
    """Um take DIFERENTE para cada estilo (regra do usuário, 23/10/2026). Guarda a escolha em takes.json."""
    import random
    sys.path.insert(0, AQUI)
    from takes import BANCO, aprovados
    def bom(p):   # nada claro demais (regra do usuário): fundo e rosto com luz de vídeo normal
        i = json.load(open(os.path.join(BANCO, "ok", p, "info.json")))
        return i["luma"] <= 150 and i["luma_rosto"] <= 160
    ok = [p for p in aprovados() if bom(p)]; mapa = json.load(open(MAPA)) if os.path.exists(MAPA) else {}
    mapa = {e: p for e, p in mapa.items() if p in ok}
    livres = [p for p in ok if p not in set(mapa.values())]; random.Random(7).shuffle(livres)
    for e in sorted(ids):
        if e not in mapa:
            if not livres:
                raise SystemExit(f"faltam takes aprovados: {len(ok)} para {len(set(ids) | set(mapa))} estilos")
            mapa[e] = livres.pop()
    json.dump(dict(sorted(mapa.items())), open(MAPA, "w"), indent=1)
    return {e: os.path.join(BANCO, "ok", mapa[e]) for e in ids}


def estilos():
    return {json.load(open(j, encoding="utf-8"))["id"]: os.path.dirname(j)
            for j in glob.glob(os.path.join(ESTILOS, "*", "*", "estilo.json"))}


def fazer(eid, pasta_estilo, trab):
    m = json.load(open(os.path.join(pasta_estilo, "estilo.json"), encoding="utf-8"))
    ex = dict({"de": .4, "ate": 3.4}, **(m.get("exemplo") or {}))
    plano = {"video": "gravacao.mp4", "palavras": "palavras.json", "recorte": "recorte.mov", "dest": "#2BFF88",
             "estilos": [{"id": eid, "de": ex["de"], "ate": ex["ate"]}]}
    arq = os.path.join(trab, f"plano_{eid}.json"); json.dump(plano, open(arq, "w"), ensure_ascii=False)
    saida = os.path.join(trab, f"saida_{eid}")
    subprocess.run([sys.executable, os.path.join(CENA, "gerar.py"), arq, saida], check=True)
    de, d = max(0, ex["de"] - .2), ex["ate"] - ex["de"] + .5
    mp4 = os.path.join(pasta_estilo, "exemplo.mp4")   # vídeo real em GIF pesa ~1 MB; MP4 curto ~150 KB e mais nítido
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(de), "-t", str(d), "-i", os.path.join(saida, "previa.mp4"), "-vf",
                    "fps=24,scale=360:-2:flags=lanczos", "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "28",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4], check=True)
    velho = os.path.join(pasta_estilo, "exemplo.gif")
    if os.path.exists(velho):
        os.remove(velho)   # GIF antigo do apresentador ilustrado
    gif = mp4
    print("ok:", gif)


if __name__ == "__main__":
    a = sys.argv[1:]
    trab = os.path.expanduser(a[a.index("--trab") + 1]) if "--trab" in a else None
    todos = estilos()
    ids = [x for k, x in enumerate(a) if not x.startswith("--") and x != trab and not (k and a[k - 1] in ("--paralelo", "--trab"))]
    if "--todos" in a:
        ids = list(todos)
    if "--faltando" in a:
        ids = [i for i in todos if not os.path.exists(os.path.join(todos[i], "exemplo.mp4"))]
    if not ids:
        raise SystemExit(__doc__)
    for i in ids:
        if i not in todos:
            raise SystemExit(f"estilo desconhecido: {i}")
    def motor(i):
        return json.load(open(os.path.join(todos[i], "estilo.json"), encoding="utf-8")).get("motor", "cena")
    fora = [i for i in ids if motor(i) != "cena"]   # ritmo (davinci/lente) e cor (lut) têm prévia própria
    if fora:
        print("pulando (motor próprio, prévia pelo script do grupo):", " ".join(fora), flush=True)
    ids = [i for i in ids if i not in fora]
    trabs = {i: trab for i in ids} if "--trab" in a else takes_por_estilo(ids)
    for d in set(trabs.values()):
        gravacao(d)
    n = int(a[a.index("--paralelo") + 1]) if "--paralelo" in a else 1
    from concurrent.futures import ThreadPoolExecutor
    def um(i):
        try:
            fazer(i, todos[i], trabs[i]); return i, None
        except Exception as e:
            return i, str(e)[-200:]
    with ThreadPoolExecutor(n) as ex:
        for i, erro in ex.map(um, ids):
            print(("FALHOU " + i + ": " + erro) if erro else ("pronto " + i), flush=True)
