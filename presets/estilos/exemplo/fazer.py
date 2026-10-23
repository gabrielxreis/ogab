"""Prévia (exemplo.gif) de cada ESTILO sobre um TAKE REAL de pessoa (vídeo de banco com licença livre; nunca apresentador
ilustrado, regra do usuário 23/10/2026). O take fica só no cache; no repositório vai só o GIF pequeno.

  python3 presets/estilos/exemplo/fazer.py <id> [<id> ...] [--trab <pasta>] [--todos] [--faltando]

Monta uma vez a "gravação" e o "recorte" do take real (cache em --trab, padrão ~/.cache/ogab_estilos_real),
aplica o estilo com os campos de exemplo do estilo.json (tempos em "exemplo": {"de", "ate"}) pelo motor CENA
(presets/cena/gerar.py) e grava presets/estilos/<grupo>/<id>/exemplo.gif (loop, 300 px, 15 fps).
--todos refaz todos; --faltando só os que ainda não têm exemplo.gif.
"""
import glob, json, os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__)); ESTILOS = os.path.dirname(AQUI); PRESETS = os.path.dirname(ESTILOS)
CENA = os.path.join(PRESETS, "cena")
FALA = ["Olha", "esse", "estilo", "aqui", "no", "seu", "vídeo,", "funciona", "em", "qualquer", "assunto."]


TAKE = {"url": "https://www.pexels.com/download/video/7261920/", "de": 8.0,   # take real, licença livre do Pexels
        "fonte": "Pexels 7261920 (licença Pexels: uso livre, com modificação)"}
DUR = 5.0


def gravacao(trab):
    """Take REAL de pessoa (regra do usuário, 23/10/2026: nada de apresentador ilustrado): baixa uma vez do Pexels,
    corta 5 s em 1080x1920 24 qps e recorta a pessoa (recorte.py). O rosto o motor detecta sozinho (rosto.py)."""
    g, r = os.path.join(trab, "gravacao.mp4"), os.path.join(trab, "recorte.mov")
    marca = os.path.join(trab, "take_real.ok")
    if os.path.exists(g) and os.path.exists(r) and os.path.exists(marca):
        return
    os.makedirs(trab, exist_ok=True)
    bruto = os.path.join(trab, "take_bruto.mp4")
    if not os.path.exists(bruto):
        subprocess.run(["curl", "-sL", "-A", "Mozilla/5.0", "-o", bruto, TAKE["url"]], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(TAKE["de"]), "-t", str(DUR), "-i", bruto, "-vf",
                    "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=24", "-an",
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", g], check=True)
    subprocess.run([sys.executable, os.path.join(CENA, "recorte.py"), g, r, "--w", "1080"], check=True)
    t, pal = .3, []
    for w in FALA:
        d = .16 + .045 * len(w); pal.append({"w": w, "ini": round(t, 3), "fim": round(t + d, 3)}); t += d + .12
    json.dump(pal, open(os.path.join(trab, "palavras.json"), "w"), ensure_ascii=False)
    open(marca, "w").write(TAKE["fonte"])


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
    gif = os.path.join(pasta_estilo, "exemplo.gif")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(de), "-t", str(d), "-i", os.path.join(saida, "previa.mp4"), "-vf",
                    "fps=15,scale=300:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                    "-loop", "0", gif], check=True)
    print("ok:", gif)


if __name__ == "__main__":
    a = sys.argv[1:]
    trab = os.path.expanduser(a[a.index("--trab") + 1]) if "--trab" in a else os.path.expanduser("~/.cache/ogab_estilos_real")
    todos = estilos()
    ids = [x for x in a if not x.startswith("--") and x != trab]
    if "--todos" in a:
        ids = list(todos)
    if "--faltando" in a:
        ids = [i for i in todos if not os.path.exists(os.path.join(todos[i], "exemplo.gif"))]
    if not ids:
        raise SystemExit(__doc__)
    gravacao(trab)
    for i in ids:
        if i not in todos:
            raise SystemExit(f"estilo desconhecido: {i}")
        fazer(i, todos[i], trab)
