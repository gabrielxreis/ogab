"""Preset LAUNCH (filme de lançamento de produto, a partir do /brag), SEMPRE com acabamento premium: fundo preto,
uma ideia por cena, revelações longas que freiam no fim, produto flutuando em 3D, luz guiando o olhar. 12-25 s.

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4] [--gif]   (--gif: prévia saida.gif ao lado do mp4)

plano.json: { "w": 1080, "h": 1920, "fps": 60, "cor": "#C4A34F" (destaque), "cor2": "#F2E2B3" (luz do destaque),
  "letra": "apple" (padrão: Inter Tight pesada, branca, centralizada) | "editorial" (à esquerda, destaque em serifa itálica)
           | "cinema" (tudo em serifa grande, destaque em itálico),
  "fonte": "Inter Tight" (padrão; troque só se a marca exigir), "marca": { "nome", "dominio", "logo" (png/svg) }, "cenas": [ ... ] }
Campos comuns da cena: tipo, dur (s), luz (true = faixa de luz atravessa na saída da cena).
Texto: "*palavra*" = degradê metálico na cor da marca; "|" = quebra de linha. Frases curtas (2-4 palavras por linha).
Tipos:
  gancho    texto ("||" = próxima batida: a frase sai e a seguinte entra, uma ideia por vez), olho, sub, tam
  logo      nome, frase, logo (padrão: o da marca; sem logo vira monograma), tamLogo
  tela      imagem (print: desktop.png/celular.png do capturar.py), moldura navegador|celular, titulo, sub, url,
            proporcao (altura/largura do print; o gerar.py mede sozinho), foco [{y 0-1 do rolar, zoom}]
  lista     olho, itens ["Método.", {t, d}] (um de cada vez, grande; 3 é o ideal), tam
  recursos  = lista (compatível com planos antigos)
  numero    de, ate, prefixo, sufixo, decimais, texto
  cta       texto, url, botao (texto; opcional), comLogo (false = sem logo), aviso (linha pequena, ex.: risco), tam
"""
import json, os, re, shutil, struct, subprocess, sys
AQUI = os.path.dirname(os.path.abspath(__file__))


def proporcao_png(caminho):
    """altura/largura de um PNG (sem biblioteca)."""
    try:
        with open(caminho, "rb") as f:
            cab = f.read(24)
        if cab[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", cab[16:24]); return h / w
    except Exception:
        pass
    return None


def gerar(plano, pasta, base):
    os.makedirs(os.path.join(pasta, "assets"), exist_ok=True); K = os.path.join(AQUI, "kit")
    plano = json.loads(json.dumps(plano))
    for k, v in (("w", 1080), ("h", 1920), ("fps", 60), ("cor", "#C4A34F"), ("cor2", "#F2E2B3")): plano.setdefault(k, v)

    def traz(caminho):
        """Copia uma imagem do plano para assets/ e devolve o caminho relativo."""
        if not caminho or re.match(r"^(https?:|data:)", caminho): return caminho
        orig = caminho if os.path.isabs(caminho) else os.path.join(base, caminho)
        nome = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(orig))
        shutil.copy(orig, os.path.join(pasta, "assets", nome)); return "assets/" + nome

    m = plano.setdefault("marca", {})
    if m.get("logo"):
        orig = m["logo"] if os.path.isabs(m["logo"]) else os.path.join(base, m["logo"])
        m.setdefault("logoProp", proporcao_png(orig) or 1)
        m["logo"] = traz(m["logo"])
    for c in plano["cenas"]:
        c.setdefault("dur", 2.4)
        if c.get("logo"): c["logo"] = traz(c["logo"])
        if c.get("imagem"):
            orig = c["imagem"] if os.path.isabs(c["imagem"]) else os.path.join(base, c["imagem"])
            c.setdefault("proporcao", proporcao_png(orig))
            c["imagem"] = traz(c["imagem"])
    dur = round(sum(c["dur"] for c in plano["cenas"]), 3)
    open(os.path.join(pasta, "plano.js"), "w").write("window.PLANO = " + json.dumps(plano, ensure_ascii=False) + ";\n")
    shutil.copy(os.path.join(K, "launch.js"), pasta)
    css = open(os.path.join(K, "launch.css")).read()
    # Fonte da marca, só se o plano pedir (o padrão Inter já vem no index.html).
    extra, fontes = "", []
    if plano.get("fonte") and plano["fonte"] not in ("Inter", "Inter Tight"):
        fontes.append(plano["fonte"]); extra += '#root { font-family: "%s", "Inter", sans-serif; }\n' % plano["fonte"]
    open(os.path.join(pasta, "launch.css"), "w").write(css + "\n" + extra)
    html = open(os.path.join(K, "index.html")).read()
    if fontes:
        fam = "&".join("family=" + f.replace(" ", "+") + ":wght@300;400;500;600;700" for f in fontes)
        html = html.replace("<link rel=\"stylesheet\" href=\"launch.css\">",
                            '<link href="https://fonts.googleapis.com/css2?%s&display=block" rel="stylesheet">\n<link rel="stylesheet" href="launch.css">' % fam)
    for a, b2 in (("%W%", plano["w"]), ("%H%", plano["h"]), ("%FPS%", plano["fps"]), ("%DUR%", dur)): html = html.replace(a, str(b2))
    open(os.path.join(pasta, "index.html"), "w").write(html)
    json.dump({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}}, open(os.path.join(pasta, "hyperframes.json"), "w"))
    print("ok", pasta, len(plano["cenas"]), "cenas", dur, "s"); return pasta


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2: raise SystemExit(__doc__)
    arq = os.path.abspath(a[0])
    pasta = gerar(json.load(open(arq)), os.path.abspath(a[1]), os.path.dirname(arq))
    if "--render" in a:
        saida = os.path.abspath(a[a.index("--render") + 1])
        subprocess.run(["npx", "--yes", "hyperframes@0.8.151", "render", pasta, "--format", "mp4", "-q", "high", "-w", "2", "-o", saida], check=True); print("render", saida)
        if "--gif" in a:   # prévia leve (README, mandar no chat): 15 fps, paleta própria
            gif = os.path.splitext(saida)[0] + ".gif"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", saida, "-vf",
                            "fps=15,scale=270:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                            gif], check=True); print("gif", gif)
