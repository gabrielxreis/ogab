"""Preset LINHA: o filme inteiro é UMA linha fina e contínua (dourada sobre azul-noite no tema padrão). A câmera segue a
ponta da caneta enquanto ela desenha formas e escreve palavras em cursiva de traço único; no fim a linha fecha um
monograma que se enche de cor (linha vira superfície), a câmera recua e o filme assenta como um pôster com a marca.

  python3 gerar.py plano.json <pasta_saida> [--tema padrao|<marca>|caminho/tema.json] [--render saida.mp4 --gif]

plano.json:
{ "formato": "vertical" | "horizontal",        # 1080x1920 (padrão) ou 1920x1080; "w"/"h" para outro tamanho
  "fps": 30,
  "cores": {"fundo": "#0B1320", "linha": "#E9D7A5", "texto": "#EFE3C2"},   # opcional: sobrescreve o tema
  "cenas": [
    {"forma": "broto", "palavra": "um traço", "dur": 2.5},      # estação: forma de um traço + palavra escrita embaixo
    {"forma": "casa",  "palavra": "uma casa", "em": 2.5},       # "em" = segundo em que a estação começa (fala)
    {"palavra": "só a palavra"},                                  # forma ou palavra podem faltar
    {"forma": {"d": "M0,100 C..."}, "palavra": "..."},           # forma própria: um "d" de SVG (sem arco)
    {"tipo": "fecho", "inicial": "A", "marca": "AURUM", "frase": "arquitetura que atravessa gerações", "dur": 4.8}
  ] }
Formas (formas.py, um traço só, entram à esquerda e saem à direita): casa arvore broto predios diamante coroa chave
montanha onda relogio coracao anel. "dur" padrão: 2,4 s por estação e 4,8 s no fecho (inclui ~1 s de pôster parado).
O fecho é opcional (sem ele o filme termina no pôster das estações). Tudo é calculado aqui: posição de cada traço,
o tempo da caneta (spline monótona, freia nas quinas das estações) e a câmera quadro a quadro; o kit só desenha.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
import formas as F  # noqa: E402
from hf_preset import montar, renderizar, args_render  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
FONTE_SERIFA = os.path.join(RAIZ, "assets", "fontes", "EBGaramond", "EBGaramond-var.ttf")


# ------------------------------------------------------------------ cores
def _rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(c):
    return "#" + "".join(f"{max(0, min(255, round(v))):02x}" for v in c)


def mistura(a, b, k):
    a, b = _rgb(a), _rgb(b); return _hex([a[i] + (b[i] - a[i]) * k for i in range(3)])


def cores_do(tema, plano):
    c = dict(tema.get("cores", {})); c.update(plano.get("cores", {}))
    fundo, linha = c.get("fundo", "#0B1320"), c.get("linha", "#E9D7A5")
    return {"fundo": fundo, "linha": linha, "texto": c.get("texto", mistura(linha, "#ffffff", .25)),
            "ponta": mistura(linha, "#ffffff", .55), "centro": mistura(fundo, linha, .07), "borda": mistura(fundo, "#000000", .45),
            "ouro": [mistura(linha, "#ffffff", .35), linha, mistura(linha, "#000000", .18), mistura(linha, "#000000", .38)],
            "brilho": mistura(linha, "#ffffff", .6), "pontos": mistura(fundo, linha, .5)}


# ------------------------------------------------------------------ medidas da serifa (marca e frase do fecho)
_SER = None


def largura_serifa(txt, tam, espaco):
    global _SER
    if _SER is None:
        from fontTools.ttLib import TTFont
        f = TTFont(FONTE_SERIFA); _SER = (f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm)
    cmap, hm, upm = _SER; w = 0
    for ch in txt:
        g = cmap.get(ord(ch)) or cmap.get(ord("o")); w += hm[g][0]
    return w * tam / upm + espaco * tam * max(0, len(txt) - 1)


# ------------------------------------------------------------------ montagem dos traços
class Filme:
    def __init__(s, plano):
        s.p = plano
        vert = plano.get("formato", "vertical") != "horizontal"
        s.W = plano.get("w", 1080 if vert else 1920); s.H = plano.get("h", 1920 if vert else 1080); s.vert = vert
        s.u = min(s.W, s.H) / 1080
        s.fps = plano.get("fps", 30)
        s.SW, s.SH = (900 * s.u, 1200 * s.u) if vert else (1500 * s.u, 860 * s.u)   # área segura (Instagram corta as bordas)
        s.tracos = []          # {"segs", "tipo", "est"}
        s.estacoes = []        # {"tracos": [i...], "chaves": [(frac_do_tempo, indice_do_marco)], "caixa"}

    def add(s, segs, tipo, est):
        s.tracos.append({"segs": segs, "tipo": tipo, "est": est}); return len(s.tracos) - 1

    def fim(s):
        t = s.tracos[s._ultimo_principal]["segs"]; return t[-1][3], F.direcao(t, fim=True)

    def montar(s):
        """Estações em "cobra": a palavra é escrita da esquerda para a direita, a linha desce pela margem direita e a
        forma é desenhada espelhada (da direita para a esquerda); a volta seguinte acontece na margem esquerda.
        Assim nenhuma ligação cruza uma palavra ou uma forma."""
        u = s.u; lado = 340 * u; desvio = 60 * u
        cenas = s.p["cenas"]; y = 0.0; k_est = 0
        for i, c in enumerate(cenas):
            if c.get("tipo") == "fecho":
                s.fecho(c, y + 40 * u, i); continue
            cxk = s.W / 2 + (-desvio if k_est % 2 == 0 else desvio); k_est += 1
            est = {"tracos": [], "marcos": {}, "cena": c}; s.estacoes.append(est); ei = len(s.estacoes) - 1
            if c.get("palavra"):
                em = 210 * u
                tr, si, larg, xh, asc, desc = F.palavra(c["palavra"], em)
                lim = 640 * u
                if larg > lim:
                    em *= lim / larg; tr, si, larg, xh, asc, desc = F.palavra(c["palavra"], em)
                x0 = cxk - larg / 2; base = y + asc
                tr = [F.transformar(t, 1, x0, base) for t in tr]; si = [F.transformar(t, 1, x0, base) for t in si]
                s._entrar(tr[0], ei, est, "palavra")
                for t in tr[1:]:
                    est["tracos"].append(s.add(t, "texto", ei)); s._ultimo_principal = len(s.tracos) - 1
                for t in si:
                    est["tracos"].append(s.add(t, "texto", ei))
                est["marcos"]["palavra_fim"] = len(s.tracos)
                y = base - desc + 50 * u
            if c.get("forma"):
                seg = F.forma(c["forma"], cxk, y + lado / 2, lado, espelhar=bool(c.get("palavra")))
                s._entrar(seg, ei, est, "forma")
                y += lado
            y += 130 * u

    def _entrar(s, segs, ei, est, tipo):
        """Liga o traço novo ao fim do anterior (sem levantar a caneta) ou cria a entrada pela esquerda."""
        p3, d3 = segs[0][0], F.direcao(segs)
        if not s.tracos:
            p0 = (p3[0] - 560 * s.u, p3[1] + 70 * s.u)
            est["marcos"]["entrada"] = s.add(F.ligacao(p0, (1, 0), p3, d3), "entrada", ei)
        else:
            p0, d0 = s.fim()
            est["marcos"].setdefault("ligacao", len(s.tracos))
            est["tracos"].append(s.add(F.ligacao(p0, d0, p3, d3), "ligacao", ei))
        est["marcos"][tipo] = len(s.tracos)
        idx = s.add(segs, {"palavra": "texto"}.get(tipo, tipo), ei); est["tracos"].append(idx); s._ultimo_principal = idx
        est["marcos"][tipo + "_fim"] = len(s.tracos)

    def fecho(s, c, topo, i):
        u = s.u; R = 165 * u; cx, cy = s.W / 2, topo + R
        est = {"tracos": [], "marcos": {}, "cena": c, "fecho": True}; s.estacoes.append(est); ei = len(s.estacoes) - 1
        anel = F.circulo(cx, cy, R, inicio=270)
        s._entrar(anel, ei, est, "anel")
        # inicial em cursiva de traço único, centrada no anel
        tr, si, larg, xh, asc, desc = F.palavra(c.get("inicial", "A")[:1], 100)
        x0, y0, x1, y1 = F.caixa(tr + si); k = 1.15 * R / max(y1 - y0, 1e-6)
        k = min(k, 1.25 * R / max(x1 - x0, 1e-6))
        dx, dy = cx - (x0 + x1) / 2 * k, cy - (y0 + y1) / 2 * k
        tr = [F.transformar(t, k, dx, dy) for t in tr]; si = [F.transformar(t, k, dx, dy) for t in si]
        s._entrar(tr[0], ei, est, "inicial")
        for t in tr[1:] + si:
            est["tracos"].append(s.add(t, "inicial", ei))
        est["marcos"]["inicial_fim"] = len(s.tracos)
        est.update(cx=cx, cy=cy, R=R, marca=c.get("marca", ""), frase=c.get("frase", ""))

    def textos_fecho(s, zP):
        """Marca, fio e frase embaixo do anel, medidos para o tamanho que terão no pôster (zP = zoom final)."""
        est = s.estacoes[-1]; u = s.u; g = 1 / zP
        tm = 74 * u * g; tf = 42 * u * g; esp = .3
        marca, frase = est["marca"].upper(), est["frase"]
        wm = largura_serifa(marca, tm, esp) if marca else 0
        if wm > s.SW * .92 * g:
            tm *= s.SW * .92 * g / wm; wm = largura_serifa(marca, tm, esp)
        wf = largura_serifa(frase, tf, .06) if frase else 0
        if wf > s.SW * .92 * g:
            tf *= s.SW * .92 * g / wf; wf = largura_serifa(frase, tf, .06)
        y_marca = est["cy"] + est["R"] + 70 * u * g + .66 * tm
        y_fio = y_marca + 40 * u * g
        y_frase = y_fio + 34 * u * g + .7 * tf
        meia = max(wm, wf, 2 * est["R"]) / 2 + 40 * u * g
        est["textos"] = {"marca": marca, "tm": tm, "wm": wm, "esp": esp, "y_marca": y_marca, "frase": frase, "tf": tf,
                         "wf": wf, "y_frase": y_frase, "y_fio": y_fio, "fio": (est["cx"] - meia, est["cx"] + meia)}
        return (est["cx"] - meia, est["cy"] - est["R"], est["cx"] + meia, y_frase + .3 * tf)

    def fio(s):
        """A caneta sai da inicial, contorna a marca pela esquerda e risca o fio entre a marca e a frase."""
        est = s.estacoes[-1]; T = est["textos"]; ei = len(s.estacoes) - 1
        x0, x1 = T["fio"]; y = T["y_fio"]
        p0, d0 = s.fim()
        est["marcos"]["ligacao_fio"] = len(s.tracos)
        lig = [(p0, (p0[0] + d0[0] * 60 * s.u, p0[1] + d0[1] * 60 * s.u), (x0 - 260 * s.u, y - 40 * s.u), (x0, y))]
        est["tracos"].append(s.add(lig, "ligacao", ei))
        est["marcos"]["regra"] = len(s.tracos)
        est["tracos"].append(s.add([F._l((x0, y), (x1, y))], "regra", ei)); s._ultimo_principal = len(s.tracos) - 1
        est["marcos"]["regra_fim"] = len(s.tracos)


# ------------------------------------------------------------------ tempo da caneta e câmera
def monotona(xs, ys, m0=None):
    n = len(xs); d = [(ys[i + 1] - ys[i]) / max(xs[i + 1] - xs[i], 1e-9) for i in range(n - 1)]; m = [0.0] * n
    m[0] = d[0] if m0 is None else m0; m[-1] = 0.0
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            h0, h1 = xs[i] - xs[i - 1], xs[i + 1] - xs[i]; w1, w2 = 2 * h1 + h0, h1 + 2 * h0
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])

    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        k = 0
        while x > xs[k + 1]:
            k += 1
        h = xs[k + 1] - xs[k]; t = (x - xs[k]) / h; t2, t3 = t * t, t * t * t
        return ((2 * t3 - 3 * t2 + 1) * ys[k] + (t3 - 2 * t2 + t) * h * m[k] + (-2 * t3 + 3 * t2) * ys[k + 1] + (t3 - t2) * h * m[k + 1])
    return f


def suave(a, b, x):
    t = min(1, max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


def easeio(x):   # cubic-bezier(0.65, 0, 0.35, 1), a curva do estilo
    x = min(1, max(0, x)); lo, hi = 0.0, 1.0
    bx = lambda t: 3 * .65 * t * (1 - t) ** 2 + 3 * .35 * t * t * (1 - t) + t ** 3
    by = lambda t: 3 * t * t * (1 - t) + t ** 3
    for _ in range(30):
        m = (lo + hi) / 2
        if bx(m) < x:
            lo = m
        else:
            hi = m
    return by((lo + hi) / 2)


def gerar_plano(plano, tema):
    fm = Filme(plano); fm.montar(); u = fm.u
    cenas = plano["cenas"]; tem_fecho = bool(fm.estacoes) and fm.estacoes[-1].get("fecho")
    # durações / inícios
    t = 0.0; inicios = []
    for est in fm.estacoes:
        c = est["cena"]; d = c.get("dur", 4.8 if est.get("fecho") else 2.4)
        if c.get("em") is not None:
            t = max(t, float(c["em"]))
        inicios.append(t); est["t0"] = t; est["D"] = d; t += d
    dur = round(t + (0 if tem_fecho else 1.2), 3)
    # zoom do pôster (o fecho mede marca e frase para esse tamanho)
    def caixa_estacao(est, todos=False):
        idx = [i for i in est["tracos"] if todos or fm.tracos[i]["tipo"] not in ("ligacao", "entrada")]
        return F.caixa([fm.tracos[i]["segs"] for i in idx])
    caixas = [caixa_estacao(e) for e in fm.estacoes]
    zP = 0.5
    for _ in range(4):
        cx = [b for b in caixas]
        if tem_fecho:
            cx[-1] = fm.textos_fecho(zP)
        X0 = min(b[0] for b in cx); Y0 = min(b[1] for b in cx); X1 = max(b[2] for b in cx); Y1 = max(b[3] for b in cx)
        zP = min(fm.SW / (X1 - X0), fm.SH / (Y1 - Y0))
    poster = ((X0 + X1) / 2, (Y0 + Y1) / 2, zP)
    if tem_fecho:
        fm.textos_fecho(zP); fm.fio()
    # comprimento acumulado (a caneta levantada não soma: a ponta pula)
    amostras = []; S = 0.0
    for tr in fm.tracos:
        a = F.amostrar(tr["segs"], 2.0 * u); tr["s0"] = S; tr["L"] = a[-1][2]; S += tr["L"]; amostras.append(a)
    STOT = S
    # chaves de tempo: [t, S] por estação (marco repetido = pausa: a spline freia e para)
    s_de = lambda i: fm.tracos[i]["s0"] if i < len(fm.tracos) else STOT
    xs, ys = [], []

    def chave(tt, ss):
        if xs and tt <= xs[-1] + 1e-3:
            tt = xs[-1] + 1e-3
        if ys and ss < ys[-1]:
            ss = ys[-1]
        xs.append(tt); ys.append(ss)
    for est in fm.estacoes:
        M, t0, D = est["marcos"], est["t0"], est["D"]
        if est.get("fecho"):
            T = [("ligacao", 0), ("anel", .08), ("anel_fim", .24), ("inicial", .27), ("inicial_fim", .42),
                 ("regra", .63), ("regra_fim", .73)]
            for nome, f in T:
                if nome in M:
                    chave(t0 + f * D, s_de(M[nome]))
            est["t_fill"] = t0 + .42 * D + .04
            continue
        if "entrada" in M:
            chave(t0, fm.tracos[M["entrada"]]["s0"] + .55 * fm.tracos[M["entrada"]]["L"])
        elif "ligacao" in M:
            chave(t0, s_de(M["ligacao"]))
        tem_f, tem_p = "forma" in M, "palavra" in M
        if tem_p:
            chave(t0 + .12 * D, s_de(M["palavra"])); chave(t0 + (.46 if tem_f else .9) * D, s_de(M["palavra_fim"]))
        if tem_f:
            chave(t0 + (.56 if tem_p else .17) * D, s_de(M["forma"])); chave(t0 + .93 * D, s_de(M["forma_fim"]))
        chave(t0 + D, ys[-1])
    if xs[-1] < dur:
        chave(dur, ys[-1])
    v0 = (ys[1] - ys[0]) / (xs[1] - xs[0]) * 1.2
    Sf = monotona(xs, ys, m0=v0)
    N = int(round(dur * fm.fps)); dt = 1.0 / fm.fps
    Sfr = [Sf(i * dt) for i in range(N + 1)]
    # quando cada traço começa e termina (amostragem fina)
    fino = [(i / 600.0, Sf(i / 600.0)) for i in range(int(dur * 600) + 1)]
    j = 0
    for tr in fm.tracos:
        while j < len(fino) - 1 and fino[j][1] < tr["s0"] + 1e-6:
            j += 1
        tr["t0"] = fino[j][0]
    j = 0
    for tr in fm.tracos:
        while j < len(fino) - 1 and fino[j][1] < tr["s0"] + tr["L"] - 1e-3:
            j += 1
        tr["t1"] = fino[j][0] if fino[j][1] >= tr["s0"] + tr["L"] - 1e-3 else dur + 1

    def ponta(Sv):
        k = 0
        for i, tr in enumerate(fm.tracos):
            if tr["s0"] <= Sv + 1e-9:
                k = i
        a = amostras[k]; s = Sv - fm.tracos[k]["s0"]
        lo, hi = 0, len(a) - 1
        while hi - lo > 1:
            m = (lo + hi) // 2
            if a[m][2] <= s:
                lo = m
            else:
                hi = m
        f = 0 if a[hi][2] == a[lo][2] else min(1, max(0, (s - a[lo][2]) / (a[hi][2] - a[lo][2])))
        return (a[lo][0] + (a[hi][0] - a[lo][0]) * f, a[lo][1] + (a[hi][1] - a[lo][1]) * f)
    pontas = [ponta(v) for v in Sfr]
    # câmera: alvo = caixa da estação (com um pouco da ponta), zoom que cabe na área segura; depois suavização gaussiana
    alvo = []
    for i in range(N + 1):
        tt = i * dt; k = max(e for e in range(len(fm.estacoes)) if fm.estacoes[e]["t0"] <= tt + 1e-9)
        b = caixas[k]; pad = 70 * u
        bw, bh = b[2] - b[0] + 2 * pad, b[3] - b[1] + 2 * pad
        z = min(fm.SW / bw, fm.SH / bh, 1.55)
        cxb, cyb = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2; px, py = pontas[i]
        alvo.append((cxb * .7 + px * .3, cyb * .7 + py * .3, math.log(z)))
    sig = .26 * fm.fps; R = int(3 * sig); ker = [math.exp(-k * k / (2 * sig * sig)) for k in range(-R, R + 1)]; ks = sum(ker)
    cam = []
    for i in range(N + 1):
        acc = [0, 0, 0]
        for k in range(-R, R + 1):
            a = alvo[min(N, max(0, i + k))]; w = ker[k + R]
            acc[0] += a[0] * w; acc[1] += a[1] * w; acc[2] += a[2] * w
        cam.append([acc[0] / ks, acc[1] / ks, acc[2] / ks])
    # gancho: no começo a câmera está colada na ponta, bem perto, e solta até o enquadramento da estação
    for i in range(N + 1):
        tt = i * dt; w = 1 - suave(.1, 1.0, tt)
        if w > 0:
            px, py = pontas[i]
            cam[i] = [cam[i][0] + (px - cam[i][0]) * w, cam[i][1] + (py - cam[i][1]) * w, cam[i][2] + (math.log(2.3) - cam[i][2]) * w]
    # pôster: recuo com a curva do estilo depois que o monograma enche; depois um empurrão contínuo e lento
    if tem_fecho:
        tp0 = fm.estacoes[-1]["t_fill"] + .1
    else:
        tp0 = max(0, dur - 1.6)
    tp1 = min(dur - .6, tp0 + 1.3)
    for i in range(N + 1):
        tt = i * dt; e = easeio((tt - tp0) / max(tp1 - tp0, 1e-6))
        if e > 0:
            cam[i] = [cam[i][0] + (poster[0] - cam[i][0]) * e, cam[i][1] + (poster[1] - cam[i][1]) * e,
                      cam[i][2] + (math.log(poster[2]) - cam[i][2]) * e]
        q = max(0, tt - tp1)
        if q > 0:
            rest = max(dur - tp1, 1e-6); push = (q * q / (2 * .35) if q < .35 else q - .175) / rest
            cam[i][2] += math.log(1 + .03 * push)
    cores = cores_do(tema, plano)
    tr_out = [{"d": F.d_de(tr["segs"]), "tipo": tr["tipo"], "s0": round(tr["s0"], 2), "L": round(tr["L"], 2),
               "t0": round(tr["t0"], 3), "t1": round(tr["t1"], 3)} for tr in fm.tracos]
    out = {"w": fm.W, "h": fm.H, "fps": fm.fps, "dur": dur, "lw": round(3.2 * u, 2), "cores": cores, "STOT": round(STOT, 1),
           "tracos": tr_out, "poster": {"t0": round(tp0, 3), "t1": round(tp1, 3), "cx": round(poster[0], 1), "cy": round(poster[1], 1)},
           "quadros": {"S": [round(v, 1) for v in Sfr], "cx": [round(c[0], 2) for c in cam], "cy": [round(c[1], 2) for c in cam],
                       "z": [round(math.exp(c[2]), 5) for c in cam], "px": [round(p[0], 1) for p in pontas], "py": [round(p[1], 1) for p in pontas]},
           "grao": tema.get("grao", .07)}
    ent = [tr for tr in fm.tracos if tr["tipo"] == "entrada"]
    if ent:
        a = ent[0]["segs"][0]; out["cauda"] = {"x0": a[0][0], "y": a[0][1], "x1": a[0][0] + 300 * u}
    if tem_fecho:
        est = fm.estacoes[-1]; T = est["textos"]
        # a marca só sobe quando a câmera já recuou quase tudo (antes disso ela estaria enorme e cortada)
        t_marca = max(fm.tracos[est["marcos"]["regra"]]["t0"] + .05, tp0 + .8 * (tp1 - tp0))
        out["fecho"] = {"cx": est["cx"], "cy": est["cy"], "R": est["R"], "t_fill": round(est["t_fill"], 3),
                        "marca": T["marca"], "tm": round(T["tm"], 2), "esp": T["esp"], "y_marca": round(T["y_marca"], 1),
                        "frase": T["frase"], "tf": round(T["tf"], 2), "y_frase": round(T["y_frase"], 1),
                        "t_marca": round(t_marca, 3), "t_frase": round(t_marca + .35, 3),
                        "t_ponta": round(fm.tracos[est["marcos"]["regra_fim"] - 1]["t1"], 3)}
    else:
        out["t_ponta"] = round(fm.tracos[-1]["t1"], 3)
    return out


def gerar(plano, pasta, tema):
    pr = gerar_plano(plano, tema)
    montar(os.path.join(AQUI, "kit"), pr, pasta, pr["dur"])
    os.makedirs(os.path.join(pasta, "fonts"), exist_ok=True)
    import shutil
    shutil.copy(FONTE_SERIFA, os.path.join(pasta, "fonts", "EBGaramond-var.ttf"))
    print("ok", pasta, len(pr["tracos"]), "traços", pr["dur"], "s")
    return pasta


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    nome_tema = a[a.index("--tema") + 1] if "--tema" in a else "padrao"
    arq_tema = nome_tema if nome_tema.endswith(".json") else os.path.join(AQUI, "temas", nome_tema + ".json")
    tema = json.load(open(arq_tema, encoding="utf-8"))
    plano = json.load(open(os.path.abspath(a[0]), encoding="utf-8"))
    pasta = gerar(plano, os.path.abspath(a[1]), tema)
    saida, gif = args_render(a)
    if saida:
        renderizar(pasta, saida, gif)
