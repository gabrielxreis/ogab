"""Animações LOTTIE para site e app do cliente: arquivos .json leves (poucos KB) que o site toca em qualquer tamanho
sem perder qualidade (lottie-web, LottieFiles, Webflow, Framer, WordPress, iOS e Android).

  python3 lottie.py <modelo> <saida.json> [--cor #C4A34F] [--cor2 #F2E2B3] [--trilho #2A2A2E] [--tamanho 512] [--fps 60]
  python3 lottie.py todos <pasta> [--cor ...]          # gera todos os modelos na pasta
  python3 lottie.py previa <a.json> [b.json ...] --gif saida.gif [--fundo #0B0B0D]   # GIF de prévia (Chrome + lottie-web)

Modelos:
  carregando   arco girando sobre o trilho, em loop (1,2 s)
  sucesso      círculo se desenha, o check se traça e assenta (1,2 s, para no fim)
  curtir       coração se enche de cor com pontinhos saindo (1 s, para no fim)
  saiba-mais   botão em pílula com a seta empurrando para a direita, em loop (1,4 s)
Regras: só camadas de forma (sem imagem, fonte ou expressão), curvas que freiam no fim (nada de quique), cores da marca.
Entregar o .json + o GIF de prévia; para o site, o dev usa <lottie-player src="arquivo.json" loop autoplay>.
"""
import json, os, sys

TAM, FPS = 512, 60
SAI = {"o": {"x": [0.33], "y": [0]}, "i": {"x": [0.16], "y": [1]}}       # expo.out (freia no fim)
IO = {"o": {"x": [0.65], "y": [0]}, "i": {"x": [0.35], "y": [1]}}        # power3.inOut


def rgb(h):
    h = h.lstrip("#"); return [round(int(h[i:i + 2], 16) / 255, 4) for i in (0, 2, 4)] + [1]


def fixo(v):
    return {"a": 0, "k": v}


def anim(chaves, curva=SAI):
    """chaves: [(quadro, valor), ...] -> propriedade animada."""
    k = []
    for n, (t, v) in enumerate(chaves):
        item = {"t": t, "s": v if isinstance(v, list) else [v]}
        if n < len(chaves) - 1:
            dim = len(item["s"])
            item["o"] = {"x": curva["o"]["x"] * dim, "y": curva["o"]["y"] * dim}
            item["i"] = {"x": curva["i"]["x"] * dim, "y": curva["i"]["y"] * dim}
        k.append(item)
    return {"a": 1, "k": k}


def tr(p=(0, 0), s=100, r=0, o=100, a=(0, 0)):
    return {"ty": "tr", "p": p if isinstance(p, dict) else fixo(list(p)), "a": fixo(list(a)),
            "s": s if isinstance(s, dict) else fixo([s, s]), "r": r if isinstance(r, dict) else fixo(r),
            "o": o if isinstance(o, dict) else fixo(o)}


def traco(cor, w):
    return {"ty": "st", "c": fixo(rgb(cor)), "o": fixo(100), "w": fixo(w), "lc": 2, "lj": 2}


def tinta(cor, o=100):
    return {"ty": "fl", "c": fixo(rgb(cor)), "o": o if isinstance(o, dict) else fixo(o), "r": 1}


def caminho(v, i=None, o=None, fechado=False):
    z = [[0, 0]] * len(v)
    return {"ty": "sh", "ks": fixo({"c": fechado, "v": v, "i": i or z, "o": o or z})}


def grupo(*itens, t=None):
    return {"ty": "gr", "it": list(itens) + [t or tr()]}


def camada(nome, formas, op, ind=1, ks=None):
    return {"ddd": 0, "ind": ind, "ty": 4, "nm": nome, "sr": 1, "ao": 0, "ip": 0, "op": op, "st": 0, "bm": 0,
            "ks": ks or {"o": fixo(100), "r": fixo(0), "p": fixo([TAM / 2, TAM / 2, 0]), "a": fixo([0, 0, 0]), "s": fixo([100, 100, 100])},
            "shapes": formas}


def doc(nome, op, camadas):
    return {"v": "5.7.4", "fr": FPS, "ip": 0, "op": op, "w": TAM, "h": TAM, "nm": nome, "ddd": 0, "assets": [],
            "layers": [dict(c, ind=i + 1) for i, c in enumerate(camadas)]}


def carregando(c):
    op = round(1.2 * FPS)
    arco = grupo({"ty": "el", "p": fixo([0, 0]), "s": fixo([300, 300])},
                 {"ty": "tm", "s": anim([(0, 0), (op * .5, 0), (op, 70)], IO), "e": anim([(0, 8), (op * .5, 78), (op, 78)], IO), "o": fixo(0), "m": 1},
                 traco(c["cor"], 30), t=tr(r={"a": 1, "k": [{"t": 0, "s": [0], "o": {"x": [.4], "y": [0]}, "i": {"x": [.6], "y": [1]}}, {"t": op, "s": [360]}]}))
    trilho = grupo({"ty": "el", "p": fixo([0, 0]), "s": fixo([300, 300])}, traco(c["trilho"], 30))
    return doc("carregando", op, [camada("arco", [arco], op), camada("trilho", [trilho], op)])


def sucesso(c):
    op = round(1.2 * FPS)
    circ = grupo({"ty": "el", "p": fixo([0, 0]), "s": fixo([300, 300])},
                 {"ty": "tm", "s": fixo(0), "e": anim([(0, 0), (34, 100)], IO), "o": fixo(0), "m": 1}, traco(c["cor"], 22),
                 t=tr(r=-90))
    fundo = grupo({"ty": "el", "p": fixo([0, 0]), "s": fixo([300, 300])}, tinta(c["cor"], anim([(28, 0), (48, 16)])))
    check = grupo(caminho([[-62, 4], [-18, 48], [70, -46]]),
                  {"ty": "tm", "s": fixo(0), "e": anim([(26, 0), (50, 100)], SAI), "o": fixo(0), "m": 1}, traco(c["cor2"], 26))
    ks = {"o": fixo(100), "r": fixo(0), "p": fixo([TAM / 2, TAM / 2, 0]), "a": fixo([0, 0, 0]),
          "s": anim([(0, [92, 92, 100]), (40, [100, 100, 100])])}
    return doc("sucesso", op, [camada("check", [check], op, ks=ks), camada("circulo", [circ, fundo], op, ks=ks)])


CORACAO = dict(v=[[0, 150], [-170, -20], [-92, -150], [0, -86], [92, -150], [170, -20]],
               i=[[62, -52], [0, 92], [-58, 0], [-14, -44], [-52, 0], [0, -84]],
               o=[[-62, -52], [0, -84], [52, 0], [14, -44], [58, 0], [0, 92]])


def curtir(c):
    op = round(1.0 * FPS)
    contorno = grupo(caminho(**CORACAO, fechado=True), traco(c["cor"], 18))
    cheio = grupo(caminho(**CORACAO, fechado=True), tinta(c["cor"]), t=tr(s=anim([(6, [0, 0]), (30, [100, 100])], SAI)))
    pontos = []
    import math
    for k in range(8):
        ang = math.radians(k * 45 - 90); d0, d1 = 170, 235
        p = anim([(14, [math.cos(ang) * d0, math.sin(ang) * d0]), (40, [math.cos(ang) * d1, math.sin(ang) * d1])], SAI)
        pontos.append(grupo({"ty": "el", "p": fixo([0, 0]), "s": fixo([20, 20])}, tinta(c["cor2"] if k % 2 else c["cor"]),
                            t=tr(p=p, s=anim([(14, [100, 100]), (40, [0, 0])], SAI), o=anim([(12, 0), (16, 100), (40, 100)], SAI))))
    ks = {"o": fixo(100), "r": fixo(0), "p": fixo([TAM / 2, TAM / 2 + 10, 0]), "a": fixo([0, 0, 0]),
          "s": anim([(0, [100, 100, 100]), (8, [90, 90, 100]), (26, [100, 100, 100])], IO)}
    return doc("curtir", op, [camada("pontos", pontos, op), camada("cheio", [cheio], op, ks=ks), camada("contorno", [contorno], op, ks=ks)])


def saiba_mais(c):
    op = round(1.4 * FPS)
    pilula = grupo({"ty": "rc", "p": fixo([0, 0]), "s": fixo([420, 150]), "r": fixo(75)}, tinta(c["cor"]))
    seta = grupo(caminho([[-40, 0], [36, 0]]), caminho([[8, -30], [38, 0], [8, 30]]), traco(c["tinta"], 16),
                 t=tr(p=anim([(0, [0, 0]), (op * .45, [26, 0]), (op, [0, 0])], IO)))
    ks = {"o": fixo(100), "r": fixo(0), "p": fixo([TAM / 2, TAM / 2, 0]), "a": fixo([0, 0, 0]),
          "s": anim([(0, [100, 100, 100]), (op * .45, [103, 103, 100]), (op, [100, 100, 100])], IO)}
    return doc("saiba-mais", op, [camada("seta", [seta], op, ks=ks), camada("pilula", [pilula], op, ks=ks)])


MODELOS = {"carregando": carregando, "sucesso": sucesso, "curtir": curtir, "saiba-mais": saiba_mais}


def previa(jsons, gif, fundo="#0B0B0D"):
    """GIF lado a lado: cada Lottie tocado no Chrome (lottie-web), quadro a quadro, 15 fps."""
    import shutil, subprocess, tempfile
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
    from navegador import rodar
    tmp = tempfile.mkdtemp(prefix="lottie_")
    pastas = []
    for k, j in enumerate(jsons):
        p = os.path.join(tmp, str(k)); os.makedirs(p)
        rodar("previa.mjs", [os.path.abspath(j), p, fundo, 15], origem=os.path.dirname(os.path.abspath(__file__)))
        pastas.append(p)
    n = max(len(os.listdir(p)) for p in pastas)
    for p in pastas:   # completa as mais curtas repetindo o último quadro (as de loop recomeçam)
        fs = sorted(os.listdir(p))
        for i in range(len(fs), n):
            shutil.copy(os.path.join(p, fs[i % len(fs)] if "loop" in p else fs[-1]), os.path.join(p, f"f{i:04d}.png"))
    entradas = sum([["-framerate", "15", "-i", os.path.join(p, "f%04d.png")] for p in pastas], [])
    filtro = "".join(f"[{i}]scale=200:200[v{i}];" for i in range(len(pastas))) + "".join(f"[v{i}]" for i in range(len(pastas))) + \
        (f"hstack={len(pastas)}" if len(pastas) > 1 else "null") + ",split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y"] + entradas + ["-filter_complex", filtro, gif], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print("gif", gif)


def main(a):
    global TAM, FPS
    if len(a) < 2:
        raise SystemExit(__doc__)
    op = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if a[0] == "previa":
        js = [x for x in a[1:] if x.endswith(".json")]
        return previa(js, op("--gif", "previa.gif"), op("--fundo", "#0B0B0D"))
    TAM, FPS = int(op("--tamanho", 512)), int(op("--fps", 60))
    c = {"cor": op("--cor", "#C4A34F"), "cor2": op("--cor2", "#F2E2B3"), "trilho": op("--trilho", "#2A2A2E"), "tinta": op("--tinta", "#0B0B0D")}
    alvos = MODELOS if a[0] == "todos" else {a[0]: MODELOS[a[0]]}
    for nome, f in alvos.items():
        saida = os.path.join(a[1], nome + ".json") if a[0] == "todos" else a[1]
        os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
        json.dump(f(c), open(saida, "w"), separators=(",", ":"))
        print(saida, os.path.getsize(saida), "bytes")


if __name__ == "__main__":
    main(sys.argv[1:])
