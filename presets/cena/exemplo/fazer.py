"""Exemplo dos presets da família CENA com pessoas REAIS de banco gratuito (Pexels e Mixkit; CREDITOS.md).

  python3 presets/cena/exemplo/fazer.py <pasta_trabalho> [destaque palco orbita lente]

Cada preset ganha o SEU take (pedido do usuário, 23/10/2026: um vídeo diferente por preset, exposição normal, nada
claro demais; nunca cortar a cabeça nem o rosto). Para cada um: baixa o take, faz a "gravação" vertical 1080x1920 só
do trecho da fala que mostra o efeito, roda o gerar.py (que recorta a pessoa e acha o rosto sozinho) com a legenda
DESTAQUE + o preset e grava o exemplo.gif dele. O cena/exemplo.gif junta os quatro.
"""
import json, os, subprocess, sys, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__)); CENA = os.path.dirname(AQUI); PRESETS = os.path.dirname(CENA)
# Take de cada preset: vídeo de banco (o original nunca vai para o git), "de" = segundo do clipe em que começa,
# "y" = onde fica o corte 9:16 em clipe deitado ou mais alto que 9:16 (0 topo, .5 meio).
TAKES = {   # banco aprovado pelo takes.py (presets/estilos/exemplo); pessoas escolhidas pelo Gabriel em 23/10/2026
    "destaque": {"banco": "7644020", "de": 0},
    "palco": {"banco": "7580433", "de": 0, "palco_y": 270},   # palavra no alto: a cabeça cobre só o meio dela
    "orbita": {"banco": "7600045", "de": 0},
    "lente": {"banco": "8048476", "de": 0},
}
LUMA_ALVO = 118   # exposição média do take (0-255); acima de ~140 fica claro demais

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


def baixar(url, dest):
    if not os.path.exists(dest):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as fh:
            fh.write(r.read())
    return dest


def luma(video, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", video, "-frames:v", "1", "-vf",
                          "scale=64:-2,format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return sum(raw) / max(1, len(raw))


def gravacao(take, orig, dest, dur):
    """9:16 1080x1920 a partir do segundo "de", ida e volta se o clipe acabar, exposição puxada para LUMA_ALVO."""
    w, h = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                                    "stream=width,height", "-of", "csv=p=0", orig], capture_output=True, text=True,
                                   check=True).stdout.strip().split(",")[:2])
    if w / h > 9 / 16:
        corte = f"crop=ih*9/16:ih:(iw-ih*9/16)/2:0"
    else:
        corte = f"crop=iw:iw*16/9:0:(ih-iw*16/9)*{take.get('y', .5)}"
    ajuste = max(-.12, min(.12, (LUMA_ALVO - luma(orig, take["de"] + 1)) / 255))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(take["de"]), "-i", orig, "-filter_complex",
                    f"[0:v]{corte},scale=1080:1920:flags=lanczos,fps=30,eq=brightness={ajuste:.3f},split[a][b];"
                    "[b]reverse[r];[a][r]concat=n=2:v=1,format=yuv420p[v]", "-map", "[v]", "-t", str(dur),
                    "-c:v", "libx264", "-crf", "16", dest], check=True)


def main(trab, quais):
    os.makedirs(trab, exist_ok=True)
    pal_todo, _ = palavras()
    Q = lambda w, n=1: quando(pal_todo, w, n)
    # trecho da fala que mostra o efeito INTEIRO de cada preset (entrada, momento cheio e saída)
    janelas = {"palco": (Q("Esse")["ini"] - .25, Q("Gab")["fim"] + .9),
               "destaque": (Q("Sempre")["ini"] - .25, Q("frente")["fim"] + 1.0),
               "orbita": (Q("Cartões")["ini"] - .3, Q("pronta")["fim"] + .6),   # cartões girando EM VOLTA da pessoa
               "lente": (Q("zoom")["ini"] - .7, Q("certa")["fim"] + 1.0)}
    filtro = ("hqdn3d=3:3:5:5,fps=12,scale=320:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=112[p];"
              "[b][p]paletteuse=dither=bayer:bayer_scale=4")
    previas = []
    for preset in quais:
        t0, t1 = janelas[preset]; t0 = max(0, t0); dur = round(t1 - t0, 3)
        pasta = os.path.join(trab, preset); os.makedirs(pasta, exist_ok=True)
        pal = [dict(p, ini=round(p["ini"] - t0, 3), fim=round(p["fim"] - t0, 3)) for p in pal_todo
               if p["ini"] >= t0 - 1e-6 and p["fim"] <= t1 + 1e-6]
        json.dump(pal, open(os.path.join(pasta, "palavras.json"), "w"), ensure_ascii=False)
        take = TAKES[preset]
        orig = (os.path.expanduser(f"~/.cache/ogab_takes/ok/{take['banco']}/gravacao.mp4") if take.get("banco")
                else baixar(take["url"], os.path.join(trab, f"take_{preset}.mp4")))
        gravacao(take, orig, os.path.join(pasta, "gravacao.mp4"), dur)
        q = lambda w, n=1: quando(pal, w, n)
        plano = {"video": "gravacao.mp4", "palavras": "palavras.json",   # recorte e rosto: o gerar.py faz
                 "destaque": {"y": 1180, "enfase": {"gab": "grande", "órbita": "serifa", "palavra certa": "marca"}}}
        if preset == "destaque":
            plano["destaque"]["empilhadas"] = [{"de": q("Sempre")["ini"] - .05, "ate": q("frente")["fim"] + .8,
                                                "linhas": [["Sempre", "pequena"], ["um passo", "grande"], ["à frente.", "serifa"]]}]
        elif preset == "palco":
            plano["palco"] = [{"texto": "EDITOR", "de": q("Esse")["ini"], "ate": q("Gab")["fim"] + .5, "sub": "COM IA",
                               "y": TAKES["palco"].get("palco_y", int(1920 * .17))}]   # alto: a cabeça cobre só um pedaço
        elif preset == "orbita":
            plano["orbita"] = [{"tipo": "giro", "de": max(0, q("Cartões")["ini"] - .1), "ate": dur - .1, "voltas": 1.25,
                                "cartoes": [{"texto": "DESTAQUE", "sub": "LEGENDA"}, {"texto": "PALCO", "sub": "ATRÁS"},
                                            {"texto": "ÓRBITA", "sub": "CARTÕES"}, {"texto": "LENTE", "sub": "ZOOM"}]}]
        elif preset == "lente":
            de, ate = q("zoom")["ini"], q("certa")["fim"] + .5
            plano["lente"] = {"zoom": [{"de": de, "ate": ate, "escala": 1.3}]}   # o gerar centra o zoom no rosto
        json.dump(plano, open(os.path.join(pasta, "plano.json"), "w"), ensure_ascii=False, indent=1)
        subprocess.run([sys.executable, os.path.join(CENA, "gerar.py"), os.path.join(pasta, "plano.json"),
                        os.path.join(pasta, "saida")], check=True)
        prev = os.path.join(pasta, "saida", "previa.mp4"); previas.append(prev)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", prev, "-vf", filtro,
                        os.path.join(PRESETS, preset, "exemplo.gif")], check=True)
        print("ok:", preset, prev)
    if len(previas) == len(TAKES):   # visão geral da família: os quatro em sequência
        lista = os.path.join(trab, "previas.txt")
        open(lista, "w").write("".join(f"file '{p}'\n" for p in previas))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista, "-vf",
                        "hqdn3d=3:3:5:5,fps=10,scale=220:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];"
                        "[b][p]paletteuse=dither=bayer:bayer_scale=4", os.path.join(CENA, "exemplo.gif")], check=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(os.path.abspath(a[0] if a else "cena_exemplo"), [p for p in a[1:] if p in TAKES] or list(TAKES))
