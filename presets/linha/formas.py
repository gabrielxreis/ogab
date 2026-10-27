"""Geometria do preset LINHA: formas de um traço só, letra cursiva de traço único (Hershey) e utilidades de curva.

Tudo vira lista de segmentos cúbicos [(p0, p1, p2, p3), ...] em coordenadas do mundo (px na escala 1 da câmera).
As formas da biblioteca estão numa caixa 0..100 (y para baixo), com ENTRADA no canto de baixo à esquerda (0,100) e
SAÍDA no de baixo à direita (100,100), para a linha seguir de uma figura para a outra sem levantar a caneta.
Forma nova: escrever o "d" (M L H V C S Q T Z, sem arco) na caixa 0..100 começando em (0,100) e terminando em (100,100).
"""
import html, math, os, re

AQUI = os.path.dirname(os.path.abspath(__file__))
HERSHEY = os.path.join(AQUI, "fontes", "HersheyScript1.svg")

# ------------------------------------------------------------------ biblioteca (caixa 0..100, um traço, entra à esquerda)
FORMAS = {
    "casa": "M0,100 L12,100 L12,48 L50,16 L68,31.2 L68,20 L76,20 L76,37.9 L88,48 L88,100 L60,100 L60,76 "
            "C60,68 55.5,63 50,63 C44.5,63 40,68 40,76 L40,100 L100,100",
    "arvore": "M0,100 C20,100 38,99 44,95 L44,64 C30,66 17,56 22,43 C13,31 24,14 38,17 C43,4 61,2 66,14 "
              "C80,10 93,24 85,36 C95,47 86,63 72,60 C66,66 59,66 56,62 L56,95 C62,99 80,100 100,100",
    "broto": "M0,100 L40,100 C44,100 48,98 50,92 L50,60 C44,62 30,60 24,48 C36,44 46,50 50,58 L50,52 "
             "C56,54 72,50 78,36 C64,32 54,40 50,48 L50,92 C52,98 56,100 60,100 L100,100",
    "predios": "M0,100 L8,100 L8,56 L24,56 L24,100 L30,100 L30,30 L40,20 L50,30 L50,100 L56,100 L56,46 L64,46 "
               "L64,36 L72,36 L72,46 L80,46 L80,100 L86,100 L86,64 L94,64 L94,100 L100,100",
    "diamante": "M0,100 C22,100 42,97 50,92 L16,44 L30,30 L70,30 L84,44 L50,92 L36,44 L16,44 L84,44 L64,44 "
                "L50,30 L36,44 L50,92 L64,44 L50,92 C60,97 78,100 100,100",
    "coroa": "M0,100 L18,100 L18,74 L10,36 L32,58 L50,24 L68,58 L90,36 L82,74 L18,74 L18,86 L82,86 L82,100 L100,100",
    "chave": "M0,100 C10,100 18,86 24,72 C15.2,72 8,64.8 8,56 C8,47.2 15.2,40 24,40 C32.8,40 40,47.2 40,56 "
             "C40,64.8 32.8,72 24,72 C32.8,72 40,64.8 40,56 L92,56 L92,67 L85,67 L85,61 L78,61 L78,67 L71,67 "
             "L71,56 C71,80 86,100 100,100",
    "montanha": "M0,100 L18,100 L40,56 L50,70 L64,38 C56.3,38 50,31.7 50,24 C50,16.3 56.3,10 64,10 "
                "C71.7,10 78,16.3 78,24 C78,31.7 71.7,38 64,38 L80,72 L86,64 L100,100",
    "onda": "M0,100 C18,100 26,88 34,72 C44,50 64,34 82,40 C96,45 96,64 82,66 C72,67 70,55 78,53 "
            "C84,52 86,58 82,60 C76,66 70,80 76,92 C80,100 90,100 100,100",
    "relogio": "M0,100 C20,100 36,94 50,88 C31.2,88 16,72.8 16,54 C16,35.2 31.2,20 50,20 L50,54 L65,63 L50,54 "
               "L50,20 C68.8,20 84,35.2 84,54 C84,72.8 68.8,88 50,88 C64,94 80,100 100,100",
    "coracao": "M0,100 C20,100 40,96 50,86 C30,70 14,56 14,40 C14,28 24,20 34,20 C42,20 48,26 50,32 "
               "C52,26 58,20 66,20 C76,20 86,28 86,40 C86,56 70,70 50,86 C60,96 80,100 100,100",
    "anel": "M0,100 C10,100 18,90 22,62 C22,46.5 34.5,34 50,34 L42,26 L46,18 L54,18 L58,26 L50,34 L42,26 L58,26 "
            "L50,34 C65.5,34 78,46.5 78,62 C78,77.5 65.5,90 50,90 C34.5,90 22,77.5 22,62 C22,77.5 34.5,90 50,90 "
            "C66,92 84,100 100,100",
}


# ------------------------------------------------------------------ curvas
def _l(p, q):
    return (p, (p[0] + (q[0] - p[0]) / 3, p[1] + (q[1] - p[1]) / 3), (p[0] + 2 * (q[0] - p[0]) / 3, p[1] + 2 * (q[1] - p[1]) / 3), q)


def parse_d(d):
    """'d' de SVG (M L H V C S Q T Z, absoluto ou relativo, sem arco) -> lista de subcaminhos de cúbicas."""
    tok = re.findall(r"[MLHVCSQTZAmlhvcsqtza]|-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", d)
    subs, cur, i, cmd = [], [], 0, None
    p = st = (0.0, 0.0); last_c = last_q = None
    num = lambda: float(tok[i])
    while i < len(tok):
        if re.match(r"[A-Za-z]", tok[i]):
            cmd = tok[i]; i += 1
            if cmd in "Aa":
                raise SystemExit("formas: arco (A) no 'd' não é aceito; converta para curvas (Inkscape: Caminho > Objeto em caminho)")
            if cmd in "Zz":
                if p != st:
                    cur.append(_l(p, st))
                p = st; last_c = last_q = None
                continue
        rel = cmd.islower(); C = cmd.upper()
        ox, oy = (p if rel else (0.0, 0.0))
        def pt(k):
            return (float(tok[i + k]) + ox, float(tok[i + k + 1]) + oy)
        if C == "M":
            if cur:
                subs.append(cur); cur = []
            p = st = pt(0); i += 2; cmd = "l" if rel else "L"; last_c = last_q = None
        elif C == "L":
            q = pt(0); cur.append(_l(p, q)); p = q; i += 2; last_c = last_q = None
        elif C == "H":
            q = (float(tok[i]) + (p[0] if rel else 0), p[1]); cur.append(_l(p, q)); p = q; i += 1; last_c = last_q = None
        elif C == "V":
            q = (p[0], float(tok[i]) + (p[1] if rel else 0)); cur.append(_l(p, q)); p = q; i += 1; last_c = last_q = None
        elif C == "C":
            c1, c2, q = pt(0), pt(2), pt(4); cur.append((p, c1, c2, q)); last_c = c2; p = q; i += 6; last_q = None
        elif C == "S":
            c1 = (2 * p[0] - last_c[0], 2 * p[1] - last_c[1]) if last_c else p
            c2, q = pt(0), pt(2); cur.append((p, c1, c2, q)); last_c = c2; p = q; i += 4; last_q = None
        elif C in "QT":
            if C == "Q":
                c, q = pt(0), pt(2); i += 4
            else:
                c = (2 * p[0] - last_q[0], 2 * p[1] - last_q[1]) if last_q else p; q = pt(0); i += 2
            cur.append((p, (p[0] + 2 / 3 * (c[0] - p[0]), p[1] + 2 / 3 * (c[1] - p[1])),
                        (q[0] + 2 / 3 * (c[0] - q[0]), q[1] + 2 / 3 * (c[1] - q[1])), q))
            last_q = c; p = q; last_c = None
        else:
            raise SystemExit(f"formas: comando '{cmd}' não suportado")
    if cur:
        subs.append(cur)
    return subs


def bez(s, t):
    a, b, c, d = s; u = 1 - t
    return (u * u * u * a[0] + 3 * u * u * t * b[0] + 3 * u * t * t * c[0] + t * t * t * d[0],
            u * u * u * a[1] + 3 * u * u * t * b[1] + 3 * u * t * t * c[1] + t * t * t * d[1])


def amostrar(segs, passo=2.0):
    """Polilinha densa [(x, y, s)] com o comprimento acumulado s (mesma medida do getTotalLength do navegador)."""
    out = [(segs[0][0][0], segs[0][0][1], 0.0)]; s = 0.0
    for sg in segs:
        corda = math.dist(sg[0], sg[1]) + math.dist(sg[1], sg[2]) + math.dist(sg[2], sg[3])
        n = max(4, int(corda / passo) + 1)
        px, py = out[-1][0], out[-1][1]
        for k in range(1, n + 1):
            x, y = bez(sg, k / n); s += math.hypot(x - px, y - py); out.append((x, y, s)); px, py = x, y
    return out


def transformar(segs, k, dx, dy):
    return [tuple((p[0] * k + dx, p[1] * k + dy) for p in sg) for sg in segs]


def d_de(segs):
    f = lambda v: f"{v:.1f}".rstrip("0").rstrip(".")
    out = [f"M{f(segs[0][0][0])},{f(segs[0][0][1])}"]
    for a, b, c, d in segs:
        out.append(f"C{f(b[0])},{f(b[1])} {f(c[0])},{f(c[1])} {f(d[0])},{f(d[1])}")
    return " ".join(out)


def caixa(segs_lista):
    xs, ys = [], []
    for segs in segs_lista:
        for x, y, _ in amostrar(segs, 6):
            xs.append(x); ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def direcao(segs, fim=False):
    """Direção unitária no começo (ou no fim) do traço."""
    if fim:
        a, b = bez(segs[-1], 0.97), segs[-1][3]
    else:
        a, b = segs[0][0], bez(segs[0], 0.03)
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1
    return dx / L, dy / L


def ligacao(p0, d0, p3, d3, folga=0.42):
    """Cúbica que sai de p0 na direção d0 e chega em p3 na direção d3 (continuidade G1: a linha não quebra)."""
    h = math.dist(p0, p3) * folga
    return [(p0, (p0[0] + d0[0] * h, p0[1] + d0[1] * h), (p3[0] - d3[0] * h, p3[1] - d3[1] * h), p3)]


def suavizar(pts, canto=105):
    """Polilinha -> cúbicas Catmull-Rom; ângulo maior que `canto` graus vira quina (sem laço na volta da letra)."""
    q = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, q[-1]) > 1e-6:
            q.append(p)
    if len(q) < 2:
        x, y = q[0]; q = [(x - .5, y), (x + .5, y)]
    n = len(q); m_in, m_out = [None] * n, [None] * n
    for i in range(n):
        if i == 0:
            m = (q[1][0] - q[0][0], q[1][1] - q[0][1]); m_in[i] = m_out[i] = m; continue
        if i == n - 1:
            m = (q[i][0] - q[i - 1][0], q[i][1] - q[i - 1][1]); m_in[i] = m_out[i] = m; continue
        a = (q[i][0] - q[i - 1][0], q[i][1] - q[i - 1][1]); b = (q[i + 1][0] - q[i][0], q[i + 1][1] - q[i][1])
        la, lb = math.hypot(*a) or 1, math.hypot(*b) or 1
        cosang = (a[0] * b[0] + a[1] * b[1]) / (la * lb)
        if math.degrees(math.acos(max(-1, min(1, cosang)))) > canto:
            m_in[i] = (a[0] * .6, a[1] * .6); m_out[i] = (b[0] * .6, b[1] * .6)
        else:
            m = ((q[i + 1][0] - q[i - 1][0]) / 2, (q[i + 1][1] - q[i - 1][1]) / 2); m_in[i] = m_out[i] = m
    return [(q[i], (q[i][0] + m_out[i][0] / 3, q[i][1] + m_out[i][1] / 3),
             (q[i + 1][0] - m_in[i + 1][0] / 3, q[i + 1][1] - m_in[i + 1][1] / 3), q[i + 1]) for i in range(n - 1)]


def forma(nome_ou_d, cx, cy, lado, espelhar=False):
    """Forma da biblioteca (ou {"d": ...} do cliente) centrada em (cx, cy) dentro de um quadrado de `lado` px.
    espelhar=True: desenhada da direita para a esquerda (entra embaixo à direita, sai embaixo à esquerda)."""
    if isinstance(nome_ou_d, dict):
        subs = parse_d(nome_ou_d["d"]); segs = [s for sub in subs for s in sub]
        x0, y0, x1, y1 = caixa([segs]); k = lado / max(x1 - x0, y1 - y0, 1e-6)
        segs = transformar(segs, k, cx - (x0 + x1) / 2 * k, cy - (y0 + y1) / 2 * k)
    else:
        if nome_ou_d not in FORMAS:
            raise SystemExit(f"forma desconhecida: {nome_ou_d}. Formas: {', '.join(sorted(FORMAS))}")
        segs = transformar(parse_d(FORMAS[nome_ou_d])[0], lado / 100, cx - lado / 2, cy - lado / 2)
    if espelhar:
        segs = [tuple((2 * cx - p[0], p[1]) for p in sg) for sg in segs]
    return segs


# ------------------------------------------------------------------ letra cursiva de traço único (Hershey Script 1-stroke)
_GLIFOS = None


def glifos():
    global _GLIFOS
    if _GLIFOS is None:
        s = open(HERSHEY, encoding="utf-8").read(); _GLIFOS = {}
        for m in re.finditer(r"<glyph([^>]*)/>", s, re.S):
            a = m.group(1); u = re.search(r'unicode="([^"]*)"', a)
            if not u:
                continue
            w = re.search(r'horiz-adv-x="([^"]*)"', a); d = re.search(r'\sd="([^"]*)"', a)
            _GLIFOS[html.unescape(u.group(1))] = (float(w.group(1)) if w else 378.0, d.group(1) if d else "")
    return _GLIFOS


def _poli(d):
    """Glifo (y para cima) -> polilinhas (curvas do glifo viram pontos a cada ~12 unidades)."""
    out = []
    for sub in parse_d(d):
        pts = [sub[0][0]]
        for sg in sub:
            reta = sg[1] == _l(sg[0], sg[3])[1] and sg[2] == _l(sg[0], sg[3])[2]
            if reta:
                pts.append(sg[3])
            else:
                n = max(2, int(math.dist(sg[0], sg[3]) / 12))
                pts += [bez(sg, k / n) for k in range(1, n + 1)]
        out.append(pts)
    return out


def palavra(texto, em):
    """Texto em cursiva de traço único com corpo `em` (px). Devolve (traços, sinais, largura, x_alt, asc, desc):
    traços = polilinhas na ordem da escrita (letras emendadas quando a caneta quase não levanta), sinais = pingos,
    acentos e cedilha (escritos no fim da palavra, como à mão). Origem: x=0 na esquerda, y=0 na linha de base."""
    G = glifos(); k = em / 1000.0; x = 0.0; brutos = []
    for ch in texto:
        adv, d = G.get(ch) or G.get(ch.lower()) or (378.0, "")
        for pl in (_poli(d) if d else []):
            brutos.append([(x + px, py) for px, py in pl])
        x += adv
    tracos, sinais = [], []
    for pl in brutos:
        xs = [p[0] for p in pl]; ys = [p[1] for p in pl]
        pequeno = max(max(xs) - min(xs), max(ys) - min(ys)) < 200
        if pequeno and (min(ys) > 330 or max(ys) < 12):
            sinais.append(pl); continue
        if tracos and math.dist(tracos[-1][-1], pl[0]) < 130:
            tracos[-1] = tracos[-1] + pl
        else:
            tracos.append(pl)
    sinais.sort(key=lambda pl: min(p[0] for p in pl))
    conv = lambda pl: [(px * k, -py * k) for px, py in pl]
    tudo = [p for pl in brutos for p in pl] or [(0, 0)]
    return ([suavizar(conv(pl)) for pl in tracos], [suavizar(conv(pl)) for pl in sinais], x * k,
            300 * k, max(p[1] for p in tudo) * k, min(p[1] for p in tudo) * k)


def circulo(cx, cy, r, inicio=90):
    """Círculo em 4 cúbicas, começando no ângulo `inicio` (graus, 90 = embaixo) no sentido horário da tela."""
    K = 0.5523 * r; segs = []
    for j in range(4):
        a0 = math.radians(inicio + 90 * j); a1 = a0 + math.pi / 2
        p0 = (cx + r * math.cos(a0), cy + r * math.sin(a0)); p3 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
        t0 = (-math.sin(a0), math.cos(a0)); t1 = (-math.sin(a1), math.cos(a1))
        segs.append((p0, (p0[0] + K * t0[0], p0[1] + K * t0[1]), (p3[0] - K * t1[0], p3[1] - K * t1[1]), p3))
    return segs
