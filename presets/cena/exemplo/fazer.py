"""Exemplo dos presets da família CENA com um apresentador ILUSTRADO (ninguém real no repositório público).

  python3 presets/cena/exemplo/fazer.py <pasta_trabalho>

Gera a fala (tempos por palavra), renderiza o apresentador com fundo (a "gravação") e sozinho com alfa (o "recorte",
direto do desenho), roda o gerar.py com DESTAQUE + PALCO + ÓRBITA + LENTE e corta um exemplo.gif para cada preset.
"""
import json, os, shutil, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__)); CENA = os.path.dirname(AQUI); PRESETS = os.path.dirname(CENA)
FALA = ["Esse é o Gab.", "Ele edita o seu vídeo", "com destaque, palco e órbita.", "Cartões girando em volta de você,",
        "barra de progresso pronta,", "e zoom na palavra certa.", "Sempre um passo à frente.", "Comenta GAB."]
PAUSA = {"Gab.": .55, "órbita.": 1.3, "você,": .9, "pronta,": 1.2, "certa.": .7, "frente.": .9}


def palavras():
    t, out = .4, []
    for frase in FALA:
        for w in frase.split():
            d = .16 + .045 * len(w)
            out.append({"w": w, "ini": round(t, 3), "fim": round(t + d, 3)}); t += d + .07
            t += PAUSA.get(w, 0)
        t += .25
    return out, round(t + 1.6, 2)


def quando(pal, palavra, n=1):
    k = 0
    for p in pal:
        if p["w"].strip(".,").lower() == palavra.lower():
            k += 1
            if k == n:
                return p
    raise KeyError(palavra)


def main(trab):
    os.makedirs(trab, exist_ok=True)
    pal, dur = palavras()
    json.dump(pal, open(os.path.join(trab, "palavras.json"), "w"), ensure_ascii=False)
    html = open(os.path.join(AQUI, "apresentador", "index.html")).read()
    for modo, fundo, fmt, saida in (("base", "block", "mp4", "gravacao.mp4"), ("pessoa", "none", "mov", "recorte.mov")):
        proj = os.path.join(trab, f"ap_{modo}"); os.makedirs(proj, exist_ok=True)
        open(os.path.join(proj, "index.html"), "w").write(
            html.replace("%FUNDO%", fundo).replace("%DUR%", str(dur)).replace("%PALAVRAS%", json.dumps(pal)))
        subprocess.run(["npx", "--yes", "hyperframes", "render", proj, "--format", fmt, "--fps", "24",
                        "-o", os.path.join(trab, saida)], check=True)
    q = lambda w, n=1: quando(pal, w, n)
    plano = {
        "video": "gravacao.mp4", "palavras": "palavras.json", "recorte": "recorte.mov", "rosto": [340, 610, 740, 1100],
        "destaque": {"y": 1180, "enfase": {"gab": "grande", "órbita": "serifa", "palavra certa": "marca"},
                     "empilhadas": [{"de": q("Sempre")["ini"] - .05, "ate": q("frente")["fim"] + .8,
                                     "linhas": [["Sempre", "pequena"], ["um passo", "grande"], ["à frente.", "serifa"]]}]},
        "palco": [{"texto": "GAB", "de": q("Esse")["ini"], "ate": q("Gab")["fim"] + .5, "sub": "EDITOR COM IA"},
                  {"texto": "GAB", "de": q("Comenta")["ini"], "ate": dur, "estilo": "serifa"}],
        "orbita": [
            {"tipo": "checklist", "de": q("Ele")["ini"], "ate": q("órbita")["fim"] + 1.1, "titulo": "PRESETS",
             "itens": [["Destaque", q("destaque")["ini"]], ["Palco", q("palco")["ini"]], ["Órbita", q("órbita")["ini"]]]},
            {"tipo": "giro", "de": q("Cartões")["ini"], "ate": q("você")["fim"] + .8, "voltas": .8,
             "cartoes": [{"texto": "DESTAQUE", "sub": "LEGENDA"}, {"texto": "PALCO", "sub": "ATRÁS"},
                         {"texto": "ÓRBITA", "sub": "CARTÕES"}, {"texto": "LENTE", "sub": "ZOOM"}]},
            {"tipo": "progresso", "de": q("barra")["ini"], "ate": q("pronta")["fim"] + 1.1, "titulo": "Seu reel está pronto",
             "itens": ["Cortes", "Legenda", "Motion"]},
            {"tipo": "cta", "de": q("Comenta")["ini"], "ate": dur, "texto": "GAB", "rotulo": "comenta", "y": 1560}],
        "lente": {"zoom": [{"de": q("zoom")["ini"], "ate": q("certa")["fim"] + .5, "escala": 1.22}]}}
    json.dump(plano, open(os.path.join(trab, "plano.json"), "w"), ensure_ascii=False, indent=1)
    subprocess.run([sys.executable, os.path.join(CENA, "gerar.py"), os.path.join(trab, "plano.json"), os.path.join(trab, "saida")], check=True)
    prev = os.path.join(trab, "saida", "previa.mp4")
    gifs = {"palco": (q("Esse")["ini"] - .3, 2.6), "destaque": (q("Sempre")["ini"] - .2, 2.8),
            "orbita": (q("Cartões")["ini"] - .1, q("você")["fim"] + .8 - q("Cartões")["ini"]),
            "lente": (q("zoom")["ini"] - .6, 2.4)}
    for preset, (de, d) in gifs.items():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(max(0, de)), "-t", str(d), "-i", prev, "-vf",
                        "fps=15,scale=300:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                        os.path.join(PRESETS, preset, "exemplo.gif")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0", "-i", prev, "-vf",
                    "fps=12,scale=240:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                    os.path.join(CENA, "exemplo.gif")], check=True)
    print("ok:", prev)


if __name__ == "__main__":
    main(os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "cena_exemplo"))
