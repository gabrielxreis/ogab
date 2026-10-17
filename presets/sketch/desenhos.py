"""Desenhos de bonequinhos para o preset SKETCH (bloco "desenho"): cenas de traço que se desenham na hora.

Cada cena é desenhada numa caixa de 600 x 400 (x para a direita, y para baixo) e o gerar.py escala para o quadro.
Uma cena devolve uma lista de traços: ("linha", d, cor) ou ("texto", x, y, txt, tam, cor). As cores são nomes
("branco", "destaque", "laranja", "azul", "verde", "roxo", "rosa", "vermelho") resolvidos pelo gerar.py.
Para criar uma cena nova: escrever a função aqui e pôr em CENAS (e na tabela do PRESET.md).
"""
import math


class T:
    """Mapeia coordenadas da caixa 600x400 para a tela (escala + deslocamento)."""
    def __init__(s, x0, y0, k):
        s.x0, s.y0, s.k = x0, y0, k

    def p(s, x, y):
        return f"{s.x0 + x * s.k:.1f},{s.y0 + y * s.k:.1f}"

    def xy(s, x, y):
        return s.x0 + x * s.k, s.y0 + y * s.k


def L(t, *pts):
    return "M" + " L".join(t.p(x, y) for x, y in pts)


def circ(t, cx, cy, r):
    x, y = t.xy(cx - r, cy); rr = r * t.k
    return f"M{x:.1f},{y:.1f} a{rr:.1f},{rr:.1f} 0 1,0 {2 * rr:.1f},0 a{rr:.1f},{rr:.1f} 0 1,0 {-2 * rr:.1f},0"


def Q(t, a, c, b):
    return f"M{t.p(*a)} Q{t.p(*c)} {t.p(*b)}"


def ret(t, x1, y1, x2, y2):
    return L(t, (x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1))


def boneco(t, x, chao, h=170, be=(-45, 55), bd=(45, 55), humor=None, sentado=False, cor="branco", cabeca=None):
    """Bonequinho de palito: be/bd = ponta do braço esquerdo/direito relativa ao ombro (dx, dy);
    humor "feliz" | "triste" | None; sentado dobra as pernas para a frente."""
    r = h * 0.11
    cx, cy = cabeca if cabeca else (x, chao - h + r)
    pesc = cy + r; omb = pesc + h * 0.07; quad = chao - h * 0.45
    out = [("linha", circ(t, cx, cy, r), cor), ("linha", L(t, (cx, pesc), (x, quad)), cor),
           ("linha", L(t, (x, omb), (x + be[0], omb + be[1])), cor), ("linha", L(t, (x, omb), (x + bd[0], omb + bd[1])), cor)]
    if sentado:
        out += [("linha", L(t, (x, quad), (x + h * 0.28, quad), (x + h * 0.28, chao)), cor),
                ("linha", L(t, (x, quad), (x + h * 0.22, quad + 6), (x + h * 0.22, chao)), cor)]
    else:
        out += [("linha", L(t, (x, quad), (x - h * 0.16, chao)), cor), ("linha", L(t, (x, quad), (x + h * 0.16, chao)), cor)]
    if humor == "feliz":
        out.append(("linha", Q(t, (cx - r * .45, cy + r * .2), (cx, cy + r * .7), (cx + r * .45, cy + r * .2)), cor))
    elif humor == "triste":
        out.append(("linha", Q(t, (cx - r * .45, cy + r * .55), (cx, cy + r * .1), (cx + r * .45, cy + r * .55)), cor))
    return out


def igreja(t, x, base, w=150, cor="branco", cruz="destaque"):
    h = w * 0.75; topo = base - h
    return [("linha", L(t, (x, base), (x, topo + h * .35), (x + w / 2, topo), (x + w, topo + h * .35), (x + w, base), (x, base)), cor),
            ("linha", L(t, (x + w / 2 - 14, base), (x + w / 2 - 14, base - 46), (x + w / 2 + 14, base - 46), (x + w / 2 + 14, base)), cor),
            ("linha", L(t, (x + w / 2, topo), (x + w / 2, topo - 48)), cruz),
            ("linha", L(t, (x + w / 2 - 17, topo - 32), (x + w / 2 + 17, topo - 32)), cruz)]


def casa(t, x, base, w=110, cor="branco"):
    h = w * 0.8
    return [("linha", L(t, (x, base), (x, base - h * .55), (x + w / 2, base - h), (x + w, base - h * .55), (x + w, base), (x, base)), cor),
            ("linha", ret(t, x + w * .4, base - h * .35, x + w * .6, base), cor)]


def pasta(t, x, y, w=90, cor="branco"):
    return [("linha", ret(t, x, y, x + w, y + w * .65), cor),
            ("linha", L(t, (x + w * .35, y), (x + w * .35, y - 12), (x + w * .65, y - 12), (x + w * .65, y)), cor)]


def relogio(t, cx, cy, r=38, cor="destaque"):
    return [("linha", circ(t, cx, cy, r), cor), ("linha", L(t, (cx, cy), (cx, cy - r * .7)), cor),
            ("linha", L(t, (cx, cy), (cx + r * .5, cy + r * .2)), cor)]


# ------------------------------------------------------------------ cenas
def camera_igreja(t):
    out = igreja(t, 400, 360, 160)
    out += [("linha", ret(t, 190, 196, 272, 248), "branco"), ("linha", circ(t, 290, 222, 18), "azul"),
            ("linha", L(t, (231, 248), (196, 360)), "branco"), ("linha", L(t, (231, 248), (266, 360)), "branco"),
            ("linha", L(t, (231, 248), (231, 360)), "branco"), ("linha", circ(t, 204, 210, 5), "vermelho")]
    out += boneco(t, 120, 360, 185, be=(55, 10), bd=(70, -6))
    return out


def editando_noite(t):
    out = [("linha", "M" + t.p(505, 50) + " " + f"a{36 * t.k:.1f},{36 * t.k:.1f} 0 1,0 {32 * t.k:.1f},{58 * t.k:.1f} "
            + f"a{28 * t.k:.1f},{28 * t.k:.1f} 0 1,1 {-32 * t.k:.1f},{-58 * t.k:.1f}", "destaque")]
    for sx, sy in ((430, 40), (570, 120), (380, 100)):
        out.append(("linha", L(t, (sx - 7, sy), (sx + 7, sy)) + " " + L(t, (sx, sy - 7), (sx, sy + 7)), "destaque"))
    out += relogio(t, 80, 80, 40)
    out += [("linha", L(t, (150, 300), (520, 300)), "branco"), ("linha", L(t, (180, 300), (180, 372)), "branco"),
            ("linha", L(t, (490, 300), (490, 372)), "branco"), ("linha", ret(t, 300, 180, 470, 284), "branco"),
            ("linha", L(t, (385, 284), (385, 300)), "branco"),
            ("linha", ret(t, 318, 250, 380, 266), "laranja"), ("linha", ret(t, 386, 250, 452, 266), "azul"),
            ("linha", L(t, (330, 200), (330, 240)), "destaque")]
    out += boneco(t, 230, 372, 175, be=(80, 18), bd=(95, 22), sentado=True)
    return out


def bolso_vazio(t):
    out = boneco(t, 300, 380, 220, be=(-40, 95), bd=(40, 95), humor="triste")
    out += [("linha", "M" + t.p(255, 292) + " q" + f"{-12 * t.k:.1f},{26 * t.k:.1f} {10 * t.k:.1f},{32 * t.k:.1f} "
             + f"q{12 * t.k:.1f},{-6 * t.k:.1f} {2 * t.k:.1f},{-32 * t.k:.1f}", "branco"),
            ("linha", "M" + t.p(345, 292) + " q" + f"{12 * t.k:.1f},{26 * t.k:.1f} {-10 * t.k:.1f},{32 * t.k:.1f} "
             + f"q{-12 * t.k:.1f},{-6 * t.k:.1f} {-2 * t.k:.1f},{-32 * t.k:.1f}", "branco")]
    for cx, cy, r in ((450, 150, 30), (510, 90, 24), (130, 120, 26)):
        out += [("linha", circ(t, cx, cy, r), "destaque"), ("texto", cx, cy + 2, "R$", r * .9, "destaque")]
    out += [("linha", Q(t, (395, 200), (420, 175), (430, 170)), "destaque"), ("linha", Q(t, (190, 190), (165, 160), (150, 140)), "destaque")]
    return out


def equilibrio(t):
    out = boneco(t, 300, 390, 175, be=(-80, -70), bd=(80, -70))
    out += igreja(t, 135, 150, 95, cruz="destaque") + pasta(t, 255, 40, 90, "laranja") + casa(t, 385, 150, 95, "azul")
    out += [("linha", Q(t, (190, 165), (300, 130), (430, 165)), "branco"),
            ("texto", 182, 178, "igreja", 30, "branco"), ("texto", 300, 125, "trabalho", 30, "laranja"),
            ("texto", 432, 178, "família", 30, "azul")]
    return out


def oferta(t):
    out = boneco(t, 210, 380, 200, be=(75, -5), bd=(95, -5), humor="feliz")
    out += [("linha", ret(t, 300, 200, 380, 270), "destaque"), ("linha", L(t, (340, 200), (340, 270)), "destaque"),
            ("linha", L(t, (300, 230), (380, 230)), "destaque"),
            ("linha", Q(t, (340, 200), (312, 168), (326, 196)), "destaque"), ("linha", Q(t, (340, 200), (368, 168), (354, 196)), "destaque"),
            ("linha", "M" + t.p(340, 120) + " c" + f"{-30 * t.k:.1f},{-35 * t.k:.1f} {-70 * t.k:.1f},{5 * t.k:.1f} 0,{55 * t.k:.1f} "
             + f"c{70 * t.k:.1f},{-50 * t.k:.1f} {30 * t.k:.1f},{-90 * t.k:.1f} 0,{-55 * t.k:.1f}", "rosa")]
    return out


def peso(t):
    out = [("linha", circ(t, 215, 200, 20), "branco"), ("linha", L(t, (232, 214), (300, 268)), "branco"),
           ("linha", L(t, (300, 268), (276, 380)), "branco"), ("linha", L(t, (300, 268), (334, 380)), "branco"),
           ("linha", L(t, (255, 232), (290, 196)), "branco"), ("linha", L(t, (270, 244), (318, 214)), "branco"),
           ("linha", Q(t, (230, 215), (220, 225), (205, 222)), "branco"),
           ("linha", "M" + t.p(285, 200) + " c" + f"{-10 * t.k:.1f},{-90 * t.k:.1f} {150 * t.k:.1f},{-90 * t.k:.1f} {140 * t.k:.1f},{0:.1f} "
            + f"c{-5 * t.k:.1f},{45 * t.k:.1f} {-130 * t.k:.1f},{45 * t.k:.1f} {-140 * t.k:.1f},0", "vermelho"),
           ("texto", 356, 168, "culpa", 34, "vermelho")]
    out += [("linha", "M" + t.p(380, 70) + " a" + f"{28 * t.k:.1f},{24 * t.k:.1f} 0 0,1 {50 * t.k:.1f},{-18 * t.k:.1f} "
             + f"a{30 * t.k:.1f},{26 * t.k:.1f} 0 0,1 {55 * t.k:.1f},{14 * t.k:.1f} a{22 * t.k:.1f},{20 * t.k:.1f} 0 0,1 {-8 * t.k:.1f},{40 * t.k:.1f} "
             + f"H{t.x0 + 372 * t.k:.1f} a{20 * t.k:.1f},{20 * t.k:.1f} 0 0,1 {8 * t.k:.1f},{-36 * t.k:.1f}", "azul")]
    for rx in (395, 425, 455):
        out.append(("linha", L(t, (rx, 120), (rx - 8, 140)), "azul"))
    out += relogio(t, 110, 110, 36, "laranja") + [("texto", 110, 172, "prazo", 30, "laranja")]
    return out


def mesa_numeros(t):
    out = [("linha", L(t, (110, 300), (490, 300)), "branco"), ("linha", L(t, (140, 300), (140, 380)), "branco"),
           ("linha", L(t, (460, 300), (460, 380)), "branco"), ("linha", ret(t, 215, 150, 385, 290), "destaque"),
           ("texto", 300, 190, "47 h/mês", 30, "branco"), ("texto", 300, 230, "R$ 720", 30, "branco"),
           ("texto", 300, 268, "= ?", 34, "destaque")]
    out += boneco(t, 80, 380, 170, be=(-30, 60), bd=(100, -20)) + boneco(t, 540, 380, 170, be=(-50, 40), bd=(30, 60))
    return out


def apresentando(t):
    out = [("linha", ret(t, 300, 70, 545, 270), "branco"), ("linha", L(t, (360, 270), (340, 370)), "branco"),
           ("linha", L(t, (485, 270), (505, 370)), "branco"),
           ("linha", ret(t, 330, 200, 365, 250), "laranja"), ("linha", ret(t, 385, 170, 420, 250), "azul"),
           ("linha", ret(t, 440, 120, 475, 250), "verde"), ("linha", L(t, (325, 110), (500, 110)), "destaque")]
    out += boneco(t, 190, 380, 190, be=(-40, 60), bd=(105, -60))
    return out


def calculadora(t):
    out = boneco(t, 200, 380, 200, be=(-35, 70), bd=(100, 10), humor="feliz")
    out += [("linha", ret(t, 300, 170, 380, 290), "destaque"), ("linha", ret(t, 312, 182, 368, 212), "destaque")]
    for i in range(3):
        for j in range(3):
            out.append(("linha", ret(t, 314 + j * 19, 224 + i * 21, 328 + j * 19, 238 + i * 21), "branco"))
    out += [("linha", ret(t, 430, 120, 560, 300), "branco")]
    for k, yy in enumerate((160, 195, 230, 265)):
        out.append(("linha", L(t, (450, yy), (540 - (k % 2) * 30, yy)), "azul" if k < 3 else "destaque"))
    out += [("texto", 300, 110, "?", 70, "destaque")]
    return out


CENAS = {"camera_igreja": camera_igreja, "editando_noite": editando_noite, "bolso_vazio": bolso_vazio,
         "equilibrio": equilibrio, "oferta": oferta, "peso": peso, "mesa_numeros": mesa_numeros,
         "apresentando": apresentando, "calculadora": calculadora}
