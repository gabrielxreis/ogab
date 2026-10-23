"""Exemplo dos presets da família CENA com uma pessoa REAL de banco gratuito (Mixkit, licença Free; CREDITOS.md).

  python3 presets/cena/exemplo/fazer.py <pasta_trabalho>

Gera a fala (tempos por palavra), baixa o vídeo da pessoa, faz a "gravação" vertical, roda o gerar.py (que recorta a
pessoa e acha o rosto sozinho) com DESTAQUE + PALCO + ÓRBITA + LENTE e corta um exemplo.gif para cada preset.
"""
import json, os, shutil, subprocess, sys, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__)); CENA = os.path.dirname(AQUI); PRESETS = os.path.dirname(CENA)
VIDEO = "https://assets.mixkit.co/videos/4834/4834-720.mp4"   # pessoa falando para a câmera (Mixkit, licença Free)
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
    # pessoa REAL de banco gratuito (regra do usuário, 23/10/2026: nada de personagem ilustrado nos exemplos).
    # Mixkit 4834 (licença Free, CREDITOS.md): o arquivo original não vai para o repositório, é baixado aqui.
    orig = os.path.join(trab, "mixkit_4834.mp4")
    if not os.path.exists(orig):
        req = urllib.request.Request(VIDEO, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(orig, "wb") as fh:
            fh.write(r.read())
    # vertical 9:16 do meio do quadro; ida e volta (o clipe tem 15 s e a fala ~25 s); escala para 1080x1920 no fim
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", orig, "-filter_complex",
                    "[0:v]crop=405:720:(iw-405)/2:0,fps=30,split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1[c];"
                    "[c]scale=1080:1920:flags=lanczos,format=yuv420p[v]", "-map", "[v]", "-t", str(dur),
                    "-c:v", "libx264", "-crf", "16", os.path.join(trab, "gravacao.mp4")], check=True)
    q = lambda w, n=1: quando(pal, w, n)
    plano = {
        "video": "gravacao.mp4", "palavras": "palavras.json",   # recorte e rosto: o gerar.py faz (recorte.py, rosto.py)
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
    # trecho que mostra o efeito INTEIRO de cada preset (entrada, momento cheio e saída)
    gifs = {"palco": (q("Esse")["ini"] - .25, q("Gab")["fim"] + .9 - q("Esse")["ini"] + .25),
            "destaque": (q("Sempre")["ini"] - .25, q("frente")["fim"] + 1.0 - q("Sempre")["ini"] + .25),
            "orbita": (q("Ele")["ini"] - .2, q("órbita")["fim"] + 1.2 - q("Ele")["ini"] + .2),
            "lente": (q("zoom")["ini"] - .7, q("certa")["fim"] + 1.0 - q("zoom")["ini"] + .7)}
    # vídeo real pesa muito em GIF: tira o ruído, 12 qps e 320 px (cada GIF fica em ~3-5 MB)
    filtro = ("hqdn3d=3:3:5:5,fps=12,scale=320:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=112[p];"
              "[b][p]paletteuse=dither=bayer:bayer_scale=4")
    for preset, (de, d) in gifs.items():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(max(0, de)), "-t", str(d), "-i", prev, "-vf", filtro,
                        os.path.join(PRESETS, preset, "exemplo.gif")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0", "-i", prev, "-vf",
                    "hqdn3d=3:3:5:5,fps=10,scale=220:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                    os.path.join(CENA, "exemplo.gif")], check=True)
    print("ok:", prev)


if __name__ == "__main__":
    main(os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "cena_exemplo"))
