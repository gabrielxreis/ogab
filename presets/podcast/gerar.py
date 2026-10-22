"""Preset PODCAST: corte de podcast/entrevista com DUAS pessoas em tela dividida (uma em cima, outra embaixo) e
legenda karaokê com a cor de quem fala, ancorada logo abaixo do queixo de quem está falando.

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4] [--gif]

plano.json:
{ "w": 1080, "h": 1920, "fps": 30, "dur": 7,
  "cor": "#F2B33D"  (cor da marca: falante 1, emenda),  "cor2": "#4FD1C5" (cor do falante 2),
  "maxPalavras": 3  (por linha de legenda, 3 ou 4),  "maxCaracteres": 20,  "fonte": "Poppins",  "caixaAlta": true,
  "nomes": false    (etiqueta com o nome de cada um junto da emenda),  "escurece": 0.34 (quanto a metade de quem
                    está calado escurece),  "audio": "podcast.wav" (opcional: som do corte; sem ele, os vídeos ficam mudos),
  "falantes": [   (o 1º vai em cima, o 2º embaixo)
    { "nome": "Ana", "midia": "ana.mp4" ou "ana.png", "cor": "#..." (opcional, troca a cor dele),
      "trilha": "ana_trilha.json"  (opcional: saída do scripts/rastrear.py --rosto, em pixels do vídeo de origem),
      "rosto": {"alt": 280}        (altura do rosto em px da origem na escala 1.0 da trilha; sem ela o gerar mede
                                    com a detecção de rosto da Apple; para imagem/câmera parada pode ir {"x","y","alt"}
                                    e vale como trilha fixa),
      "recorte": {"x": 0.5, "y": 0.3, "zoom": 1.0}  (opcional: ponto da origem que fica na metade, 0 a 1 como
                                    object-position, e zoom extra; sem ele o rosto da trilha fica centrado a 36 %),
      "inicio": 0.0  (segundo do arquivo em que o corte começa),  "som": false (true = usa o som deste vídeo),
      "legendaY": 0.62  (sem trilha nem rosto: centro da legenda, fração da altura da metade) } ],
  "palavras": [ {"texto": "Qual", "ini": 0.25, "fim": 0.5, "falante": 0, "quebra": false (true força quebra
                depois desta palavra)}, ... ]  (tempos em segundos DO CORTE, já descontado o início) }

Legenda: grupos de até maxPalavras palavras do mesmo falante, quebra na pontuação e nas pausas, nunca termina em
palavra fraca (que, de, o, com...). Ela fica abaixo do queixo, dentro da metade de quem fala, presa às bordas; sem
espaço embaixo, sobe para cima da cabeça; nunca cobre o rosto. Sem trilha, posição fixa da metade (legendaY).
Exceção à legenda fixa da /ogab: SÓ podcast/entrevista com duas pessoas (ver PRESET.md).
"""
import json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from hf_preset import montar, renderizar, args_render, traz

AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(os.path.dirname(AQUI))
IMAGEM = (".png", ".jpg", ".jpeg", ".webp")
FRACAS = {"que", "quem", "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas", "o", "a", "os", "as", "um", "uma",
          "para", "pra", "pro", "com", "se", "e", "mas", "por", "pelo", "pela", "ao", "à", "meu", "minha", "seu", "sua",
          "teu", "tua", "nosso", "nossa", "esse", "essa", "este", "esta", "isso", "aquele", "aquela", "como", "quando", "onde"}
ROSTO_Y = .36      # sem recorte: centro do rosto fica a 36 % da altura da metade
QUEIXO = .62       # queixo = centro do rosto + 0,62 x altura do rosto (a caixa do detector corta no queixo; sobra folga)
TOPO = .80         # topo da cabeça = centro - 0,80 x altura


def sonda(arq):
    """(w, h, dur) de vídeo ou imagem."""
    if arq.lower().endswith(IMAGEM):
        from PIL import Image
        w, h = Image.open(arq).size
        return w, h, None
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:stream_tags=rotate",
                        "-show_entries", "format=duration", "-of", "json", arq], capture_output=True, text=True, check=True)
    d = json.loads(r.stdout); st = d["streams"][0]
    w, h = int(st["width"]), int(st["height"])
    if str(st.get("tags", {}).get("rotate", "0")) in ("90", "270", "-90"):
        w, h = h, w
    return w, h, float(d["format"]["duration"])


def medir_rosto(arq, t=0.0):
    """Altura do rosto (px da origem) pela detecção da Apple (presets/cena/rosto.py). None se não achar."""
    try:
        sys.path.insert(0, os.path.join(RAIZ, "presets", "cena"))
        from rosto import _caixa_vision, _caixa_opencv
        import tempfile
        png = arq
        if not arq.lower().endswith(IMAGEM):
            png = os.path.join(tempfile.mkdtemp(prefix="podcast_"), "q.png")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", arq, "-frames:v", "1", png], check=True)
        w, h, _ = sonda(png)
        cx = _caixa_vision(png, w, h) if sys.platform == "darwin" else _caixa_opencv(png)
        if cx:
            c = max(cx, key=lambda c: (c[2] - c[0]) * (c[3] - c[1]))
            return c[3] - c[1]
    except Exception as e:
        print("aviso: não medi o rosto automaticamente:", str(e)[:80])
    return None


def suavizar(pts, janela):
    """Média móvel de x, y e escala (a legenda acompanha a cabeça sem tremer)."""
    if len(pts) < 3:
        return pts
    out = []
    for i, p in enumerate(pts):
        viz = [q for q in pts if abs(q[0] - p[0]) <= janela / 2]
        out.append([p[0]] + [sum(q[k] for q in viz) / len(viz) for k in (1, 2, 3)])
    return out


def amostrar(pts, t):
    if t <= pts[0][0]:
        return pts[0][1:]
    if t >= pts[-1][0]:
        return pts[-1][1:]
    lo, hi = 0, len(pts) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        lo, hi = (m, hi) if pts[m][0] <= t else (lo, m)
    a, b = pts[lo], pts[hi]; k = (t - a[0]) / max(1e-6, b[0] - a[0])
    return [a[i] + (b[i] - a[i]) * k for i in (1, 2, 3)]


def preparar_falante(f, i, plano, base, pasta):
    W, HH, dur = plano["w"], plano["h"] / 2, plano["dur"]
    orig = f["midia"] if os.path.isabs(f["midia"]) else os.path.join(base, f["midia"])
    if not os.path.exists(orig):
        raise SystemExit(f"falante {i + 1}: mídia não encontrada: {orig}")
    sw, sh, sdur = sonda(orig)
    imagem = sdur is None
    ini = float(f.get("inicio", 0))
    if not imagem and sdur - ini < dur - .05:
        print(f"aviso: o vídeo do falante {i + 1} tem {sdur - ini:.2f} s a partir do início e o corte pede {dur} s")
    # Trilha (rastrear.py --rosto) ou rosto fixo, sempre em px da origem.
    pts, rosto = None, dict(f.get("rosto") or {})
    if f.get("trilha"):
        tr = json.load(open(f["trilha"] if os.path.isabs(f["trilha"]) else os.path.join(base, f["trilha"]), encoding="utf-8"))
        if (tr.get("w"), tr.get("h")) != (sw, sh):
            print(f"aviso: trilha do falante {i + 1} feita em {tr.get('w')}x{tr.get('h')}, mídia é {sw}x{sh} (reescalando)")
            kx, ky = sw / tr["w"], sh / tr["h"]
            tr["pontos"] = [[p[0], p[1] * kx, p[2] * ky, p[3]] for p in tr["pontos"]]
        # tempo do arquivo -> tempo do corte
        pts = [[p[0] - ini, p[1], p[2], p[3]] for p in tr["pontos"]]
        pts = suavizar(pts, .6)
        if not rosto.get("alt"):
            alt = medir_rosto(orig, tr["pontos"][0][0])
            rosto["alt"] = alt or .2 * min(sw, sh)
            print(f"falante {i + 1}: altura do rosto {'medida' if alt else 'estimada'} = {rosto['alt']:.0f} px (passe rosto.alt para fixar)")
    elif rosto.get("x") is not None and rosto.get("y") is not None:
        pts = [[0, float(rosto["x"]), float(rosto["y"]), 1.0]]
        rosto.setdefault("alt", .2 * min(sw, sh))
    # Recorte "cover" na metade W x HH.
    rec = f.get("recorte") or {}
    s = max(W / sw, HH / sh) * float(rec.get("zoom", 1))
    dw, dh = sw * s, sh * s
    if "x" in rec or "y" in rec or not pts:
        ox = (W - dw) * float(rec.get("x", .5)); oy = (HH - dh) * float(rec.get("y", .3))
    else:   # rosto mediano centrado na horizontal e a 36 % da altura
        xs = sorted(p[1] for p in pts); ys = sorted(p[2] for p in pts)
        ox = W / 2 - xs[len(xs) // 2] * s; oy = HH * ROSTO_Y - ys[len(ys) // 2] * s
    ox = min(0, max(W - dw, ox)); oy = min(0, max(HH - dh, oy))
    # Trilha local da metade, reamostrada a 15 por segundo.
    local = None
    if pts:
        local = []
        n = max(1, int(dur * 15))
        for k in range(n + 1):
            t = dur * k / n
            x, y, e = amostrar(pts, t)
            local.append([round(t, 3), round(ox + x * s, 1), round(oy + y * s, 1), round(e, 4)])
    pasta_rel = traz(orig, base, pasta)
    return {"nome": f.get("nome", f"Falante {i + 1}"), "src": pasta_rel, "imagem": imagem, "inicio": ini,
            "som": bool(f.get("som")) and not plano.get("audio"), "cor": f.get("cor") or (plano["cor"] if i == 0 else plano["cor2"]),
            "x": round(ox, 1), "y": round(oy, 1), "dw": round(dw, 1), "dh": round(dh, 1),
            "trilha": local, "rostoAlt": round(rosto["alt"] * s, 1) if pts else None,
            "legendaY": float(f.get("legendaY", .62))}


def limpa(w):
    return re.sub(r"[^\wà-ú]", "", w.lower())


def agrupar(palavras, maxp, maxc):
    """Grupos de legenda: mesmo falante, até maxp palavras e maxc caracteres, quebra em pontuação/pausa,
    nunca terminando em palavra fraca."""
    grupos, atual = [], []

    def fecha():
        if atual:
            grupos.append(list(atual)); atual.clear()

    for i, p in enumerate(palavras):
        if atual and (p["falante"] != atual[-1]["falante"] or p["ini"] - atual[-1]["fim"] > .6):
            fecha()
        if atual and (len(atual) >= maxp or len(" ".join(x["texto"] for x in atual + [p])) > maxc):
            # não deixa a linha terminar em palavra fraca: leva as fracas para a próxima
            sobra = []
            while len(atual) > 1 and limpa(atual[-1]["texto"]) in FRACAS:
                sobra.insert(0, atual.pop())
            fecha(); atual.extend(sobra)
        atual.append(p)
        if p.get("quebra") or re.search(r"[.!?,;:]$", p["texto"]):
            fecha()
    fecha()
    out = []
    for k, g in enumerate(grupos):
        nx = grupos[k + 1] if k + 1 < len(grupos) else None
        fim = g[-1]["fim"] + .35
        if nx and (nx[0]["ini"] - g[-1]["fim"] < 1.2 or nx[0]["falante"] != g[0]["falante"]):
            fim = nx[0]["ini"]   # contínua: emenda na próxima (troca de falante também emenda)
        out.append({"falante": g[0]["falante"], "ini": round(g[0]["ini"], 3), "fim": round(fim, 3),
                    "palavras": [{"texto": x["texto"], "ini": round(x["ini"], 3), "fim": round(x["fim"], 3)} for x in g]})
        if limpa(g[-1]["texto"]) in FRACAS:
            print(f"aviso: legenda termina em palavra fraca: \"{' '.join(x['texto'] for x in g)}\" (usar \"quebra\" à mão)")
    return out


def turnos(palavras):
    """[[t, falante], ...]: quem está falando a partir de t (a troca acontece na 1ª palavra do outro)."""
    out = []
    for p in palavras:
        if not out or out[-1][1] != p["falante"]:
            out.append([round(p["ini"], 3), p["falante"]])
    if out:
        out[0][0] = 0
    return out


def conferir_espaco(plano):
    """Mesma conta do podcast.js (aproximada pela altura da linha): avisa quando a legenda não cabe nem abaixo do
    queixo nem acima da cabeça (aí ela cairia no rosto: reenquadrar com "recorte" ou baixar "tamLegenda")."""
    W, H = plano["w"], plano["h"]; HH, U, dur = H / 2, plano["w"] / 1080, plano["dur"]
    alt_leg = 1.32 * plano.get("tamLegenda", 66) * U; margem, vao = 44 * U, 22 * U
    limite = [HH - margem, min(HH - margem, H * .84 - HH)]
    problemas = 0
    for g in plano["_grupos"]:
        f = plano["_falantes"][g["falante"]]
        if not f["trilha"]:
            continue
        qmax, cmin, t = -1e9, 1e9, g["ini"]
        while t <= g["fim"] + 1e-6:
            z = 1 + .035 * t / dur; x, y, e = amostrar([[p[0], p[1], p[2], p[3]] for p in f["trilha"]], t)
            y = HH / 2 + (y - HH / 2) * z; alt = f["rostoAlt"] * e * z
            qmax, cmin = max(qmax, y + .62 * alt), min(cmin, y - .80 * alt); t += 1 / 15
        i = g["falante"]
        if qmax + vao * .5 + alt_leg > limite[i] and cmin - vao - alt_leg < margem:
            problemas += 1
            print(f'AVISO: {g["ini"]:.2f}-{g["fim"]:.2f} s ({f["nome"]}): sem espaço fora do rosto para a legenda; '
                  'reenquadrar (recorte.zoom menor / recorte.y) ou baixar tamLegenda')
    return problemas


def fonte_css(plano, pasta):
    nome = plano.get("fonte", "Poppins")
    pasta_f = os.path.join(RAIZ, "assets", "fontes", nome.replace(" ", ""))
    if os.path.isdir(pasta_f):
        css = []
        os.makedirs(os.path.join(pasta, "fonts"), exist_ok=True)
        for peso, suf in ((700, "Bold"), (800, "ExtraBold")):
            arq = os.path.join(pasta_f, f"{nome.replace(' ', '')}-{suf}.ttf")
            if os.path.exists(arq):
                shutil.copy(arq, os.path.join(pasta, "fonts"))
                css.append(f"@font-face {{ font-family: '{nome}'; font-weight: {peso}; src: url('fonts/{os.path.basename(arq)}'); }}")
        return "<style>" + "\n".join(css) + "</style>"
    fam = nome.replace(" ", "+")
    return f'<link href="https://fonts.googleapis.com/css2?family={fam}:wght@700;800&display=block" rel="stylesheet">'


def midias_html(fal, plano):
    """<video>/<img> de cada metade (fixos; o movimento fica no invólucro .cam). Precisam estar no HTML para o
    HyperFrames achar e extrair os quadros."""
    dur = plano["dur"]; out = []
    for i, f in enumerate(fal):
        css = f'left:{f["x"]}px;top:{f["y"]}px;width:{f["dw"]}px;height:{f["dh"]}px'
        if f["imagem"]:
            el = f'<img id="midia-{i}" class="midia" src="{f["src"]}" style="{css}">'
        else:
            som = 'data-has-audio="true" data-volume="1"' if f["som"] else "muted"
            el = (f'<video id="midia-{i}" class="clip midia" src="{f["src"]}" playsinline {som} data-start="0" '
                  f'data-duration="{dur}" data-media-start="{f["inicio"]}" data-track-index="{i}" style="{css}"></video>')
        out.append(f'<div class="metade" id="metade-{i}"><div class="cam" id="cam-{i}">{el}</div><div class="sombra" id="sombra-{i}"></div></div>')
    if plano.get("audio"):
        out.append(f'<audio id="som" src="{plano["audio"]}" data-start="0" data-duration="{dur}" data-track-index="5" data-volume="1"></audio>')
    return "\n".join(out)


def gerar(plano, pasta, base="."):
    plano = json.loads(json.dumps(plano))
    for k, v in (("w", 1080), ("h", 1920), ("fps", 30), ("cor", "#F2B33D"), ("cor2", "#4FD1C5"), ("maxPalavras", 3),
                 ("maxCaracteres", 20), ("fonte", "Poppins"), ("caixaAlta", True), ("nomes", False), ("escurece", .34)):
        plano.setdefault(k, v)
    if len(plano.get("falantes") or []) != 2:
        raise SystemExit('O preset podcast pede exatamente 2 "falantes" (o 1º em cima, o 2º embaixo).')
    pal = sorted(plano.get("palavras") or [], key=lambda p: p["ini"])
    if not pal:
        raise SystemExit('Falta "palavras" (transcrição palavra por palavra com "falante" 0 ou 1).')
    for p in pal:
        p["texto"] = str(p.get("texto", p.get("w", ""))).strip()
        p["falante"] = int(p.get("falante", 0))
    plano.setdefault("dur", round(pal[-1]["fim"] + .8, 2))
    os.makedirs(pasta, exist_ok=True)
    if plano.get("audio"):
        plano["audio"] = traz(plano["audio"], base, pasta)
    fal = [preparar_falante(f, i, plano, base, pasta) for i, f in enumerate(plano["falantes"])]
    plano["_falantes"] = fal
    plano["_grupos"] = agrupar(pal, int(plano["maxPalavras"]), int(plano["maxCaracteres"]))
    plano["_turnos"] = turnos(pal)
    conferir_espaco(plano)
    montar(os.path.join(AQUI, "kit"), plano, pasta, plano["dur"])
    ix = os.path.join(pasta, "index.html")
    html = open(ix, encoding="utf-8").read().replace("<!--MIDIAS-->", midias_html(fal, plano)).replace("<!--FONTE-->", fonte_css(plano, pasta))
    open(ix, "w", encoding="utf-8").write(html)
    print("ok", pasta, f'{len(plano["_grupos"])} legendas, {len(plano["_turnos"])} turnos, {plano["dur"]} s')
    for g in plano["_grupos"]:
        print(f'  {g["ini"]:5.2f}-{g["fim"]:5.2f}  [{fal[g["falante"]]["nome"]}] ' + " ".join(x["texto"] for x in g["palavras"]))
    return pasta


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    pasta = gerar(json.load(open(a[0], encoding="utf-8")), os.path.abspath(a[1]), os.path.dirname(os.path.abspath(a[0])))
    saida, gif = args_render(a)
    if saida:
        renderizar(pasta, saida, gif)
