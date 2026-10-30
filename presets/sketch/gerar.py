"""Preset SKETCH: motion de "desenho de marcador" sobre fundo escuro (contornos que se traçam, cursor, ícones que surgem,
texto manuscrito digitado, setas que se desenham, traço tremido de animação feita à mão).

  python3 gerar.py plano.json <pasta_saida> [--render saida.mp4]

plano.json:
{ "formato": "vertical" | "horizontal", (cena "ajuste": [cx, cy, escala] = centro medido -> 540,960; ver --centrar), "base": 1110 (opcional: o conteúdo termina acima desse Y, para a legenda),          # 1080x1920 (padrão) ou 1920x1080; "w"/"h" para outro tamanho
  "fps": 30,
  "cores": {"paleta": ["#f0884a", "#4aa3f0", "#3fcf6a", "#a07cf0"], "destaque": "#ffc83d", "texto": "#f2f2f2"},   # opcional
  "cenas": [ {"blocos": [ ...blocos... ], "segurar": 1.6}, ... ] }      # "dur" fixa a duração da cena (senão: animação + segurar)

Blocos (empilhados de cima para baixo, centralizados na altura do quadro; cada um entra depois do anterior):
  {"tipo": "cabecalho", "partes": [{"icone": "github", "texto": "GitHub"}, {"seta": true},
                                   {"texto": "App Store", "cor": "destaque", "grande": true}, {"texto": "do"},
                                   {"icone": "claude", "texto": "Claude Code", "cor": "laranja"}]}
  {"tipo": "grade", "itens": [{"icones": ["video"], "rotulo": "editar vídeo", "botao": "instalar"},
                              {"icones": ["gmail", "drive"], "rotulo": "Gmail e Drive", "botao": "instalar"}], "colunas": 3}
  {"tipo": "numero", "n": "1", "linha1": "projeto 1 de 5", "linha2": "o que mais me chamou a atenção", "cor": "laranja"}
  {"tipo": "fluxo", "de": {"icone": "claude", "rotulo": "Claude Code"},
                    "painel": {"mock": "editor_video" | "grafico" | "lista" | "chat", "titulo": "editor de vídeo", "itens": [...]}}
  {"tipo": "frase", "texto": "Instala uma vez e usa pra sempre", "cor": "destaque"}
  {"tipo": "lista", "itens": ["roteiro", "edição", "legenda"], "cor": "verde"}
  {"tipo": "espaco", "altura": 60}
  {"tipo": "desenho", "cena": "camera_igreja", "altura": 440}   bonequinhos que se desenham (cenas em desenhos.py)
Em qualquer bloco, "em": segundos desde o início da cena = o bloco só entra nesse instante (sincronizar com a fala).
Na lista, "tempos": [s, s, ...] = instante de cada item (cada check entra quando o item é falado).
Cores por nome: laranja, azul, verde, roxo, rosa, amarelo, branco, destaque (ou "#hex"). Sem cor, os cartões seguem a paleta.
Ícones (kit/icones.js): video play tesoura email gmail drive instagram tiktok youtube github claude robo codigo terminal
chat doc pasta grafico subida dolar check xis pessoa grupo globo raio estrela engrenagem lupa casa calendario coracao
celular link foguete cadeado sino carrinho lampada relogio alvo ia.
"""
import json, math, os, shutil, subprocess, sys
from fontTools.ttLib import TTFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desenhos  # noqa: E402


def _barra():
    """Render com a barra do progresso.py (LEI do usuário, 30/10/2026: todo render de motion com link para acompanhar)."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
    import progresso
    return progresso

AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(os.path.dirname(AQUI))
FONTE = os.path.join(RAIZ, "assets", "fontes", "PatrickHand", "PatrickHand-Regular.ttf")
NOMES = {"laranja": "#f0884a", "azul": "#4aa3f0", "verde": "#3fcf6a", "roxo": "#a07cf0", "rosa": "#f05a7e",
         "amarelo": "#ffc83d", "branco": "#f2f2f2", "vermelho": "#ef5350"}
_F = TTFont(FONTE); _CMAP = _F.getBestCmap(); _HM = _F["hmtx"]; _UPM = _F["head"].unitsPerEm


def largura(txt, tam):
    w = 0
    for ch in txt:
        g = _CMAP.get(ord(ch)) or _CMAP.get(ord("o"))
        w += _HM[g][0]
    return w * tam / _UPM


def rret(x, y, w, h, r):
    """Retângulo arredondado começando no canto de cima à esquerda (o traço "anda" para a direita, como na referência)."""
    r = min(r, w / 2, h / 2)
    return (f"M{x + r:.1f},{y:.1f} H{x + w - r:.1f} A{r:.1f},{r:.1f} 0 0 1 {x + w:.1f},{y + r:.1f} V{y + h - r:.1f} "
            f"A{r:.1f},{r:.1f} 0 0 1 {x + w - r:.1f},{y + h:.1f} H{x + r:.1f} A{r:.1f},{r:.1f} 0 0 1 {x:.1f},{y + h - r:.1f} "
            f"V{y + r:.1f} A{r:.1f},{r:.1f} 0 0 1 {x + r:.1f},{y:.1f}")


def seta(x1, y1, x2, y2, u):
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 6 * u
    ang = math.atan2(y2 - my, x2 - mx); L = 22 * u
    a1, a2 = ang + math.radians(150), ang - math.radians(150)
    return (f"M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}",
            f"M{x2 + L * math.cos(a1):.1f},{y2 + L * math.sin(a1):.1f} L{x2:.1f},{y2:.1f} L{x2 + L * math.cos(a2):.1f},{y2 + L * math.sin(a2):.1f}")


class Cena:
    def __init__(s, g):
        s.g, s.itens, s.t = g, [], 0.25

    def add(_c, **it):
        _c.itens.append(it); return it

    def texto(s, x, y, txt, tam, cor, t, ancora="start", modo="digitar"):
        s.add(k="texto", x=round(x, 1), y=round(y, 1), txt=txt, tam=round(tam, 1), cor=cor, t=round(t, 3), ancora=ancora, modo=modo)
        return t + (0.45 if modo == "surgir" else len(txt) * s.g.cps)

    def caixa(s, x, y, w, h, cor, t, r=None, cursor=False, dur=0.42, preench=None, lw=None):
        u = s.g.u; r = 26 * u if r is None else r
        it = dict(k="caixa", d=rret(x, y, w, h, r), cor=cor, t=round(t, 3), dur=dur)
        if preench is not None:
            it["preench"] = preench
        if lw:
            it["lw"] = lw
        if cursor:
            it.update(cursor=True, cx=round(x + 22 * u, 1), cy=round(y + 40 * u, 1), ctam=round(34 * u, 1), piscas=1)
        s.itens.append(it)
        return t + dur + (0.28 if cursor else 0)

    def icone(s, nome, cx, cy, tam, cor, t):
        s.add(k="icone", nome=nome, x=round(cx, 1), y=round(cy, 1), s=round(tam, 1), cor=cor, t=round(t, 3))
        return t + 0.3

    def linha(s, d, cor, t, dur=0.4, preench=None, lw=None):
        it = dict(k="linha", d=d, cor=cor, t=round(t, 3), dur=dur)
        if preench:
            it["preench"] = preench
        if lw:
            it["lw"] = lw
        s.itens.append(it); return t + dur

    def seta(s, x1, y1, x2, y2, cor, t):
        d, ponta = seta(x1, y1, x2, y2, s.g.u)
        s.add(k="seta", d=d, ponta=ponta, cor=cor, t=round(t, 3), dur=0.45); return t + 0.6


class Gerador:
    def __init__(s, plano):
        s.p = plano
        vert = plano.get("formato", "vertical") != "horizontal"
        s.W = plano.get("w", 1080 if vert else 1920); s.H = plano.get("h", 1920 if vert else 1080); s.vert = vert
        s.u = min(s.W, s.H) / 1080 * (1.25 if vert else 1.0)   # vertical: tudo 25% maior (ocupa o quadro como no Reels)
        s.m = (60 if vert else 120) * min(s.W, s.H) / 1080
        c = plano.get("cores", {})
        s.paleta = [s.cor(x) for x in c.get("paleta", ["laranja", "azul", "verde", "roxo"])]
        s.destaque = s.cor(c.get("destaque", "amarelo")); s.branco = s.cor(c.get("texto", "branco"))
        s.cps = plano.get("cps", 0.03); s.k = 0

    def cor(s, x, padrao=None):
        if not x:
            return padrao
        if x == "destaque":
            return s.destaque
        return NOMES.get(x, x)

    def proxima(s):
        c = s.paleta[s.k % len(s.paleta)]; s.k += 1; return c

    # ------------------------------------------------------------ blocos: medir (altura) e montar (itens a partir de y)
    def altura(s, b):
        u, t = s.u, b["tipo"]
        if t == "cabecalho":
            return 120 * u
        if t == "grade":
            n = len(b["itens"]); col = b.get("colunas") or (min(n, 3) if s.vert else min(n, 4)); lin = math.ceil(n / col)
            c = s._lado_cartao(col)
            return lin * (c + 160 * u) - 30 * u
        if t == "numero":
            return 200 * u
        if t == "fluxo":
            return (180 + 60 + 130 + 300) * u if s.vert else 330 * u
        if t == "frase":
            return len(s._quebrar(b["texto"], b.get("tam", 84) * u, s.W - 2 * s.m)) * b.get("tam", 84) * u * 1.15 + 30 * u
        if t == "lista":
            return len(b["itens"]) * 92 * u
        if t == "espaco":
            return b.get("altura", 60) * u
        if t == "desenho":
            return b.get("altura", 440) * u
        raise SystemExit(f"bloco desconhecido: {t}")

    def _lado_cartao(s, col):
        u = s.u; util = s.W - 2 * s.m; gap = 50 * u
        return min((util - (col - 1) * gap) / col, 290 * u)

    def _quebrar(s, txt, tam, maxw):
        linhas, cur = [], ""
        for p in txt.split():
            tente = (cur + " " + p).strip()
            if largura(tente, tam) > maxw and cur:
                linhas.append(cur); cur = p
            else:
                cur = tente
        return linhas + ([cur] if cur else [])

    def montar(s, cn, b, y, t):
        u, tp = s.u, b["tipo"]
        if tp == "cabecalho":
            partes = b["partes"]; ts = b.get("tam", 64) * u; gap = 22 * u; lado = ts * 1.5
            def wpart(p):
                if p.get("seta"):
                    return 90 * u
                tam = ts * (1.3 if p.get("grande") else (0.75 if len(p.get("texto", "")) <= 3 and not p.get("icone") else 1))
                return (lado + gap if p.get("icone") else 0) + (largura(p.get("texto", ""), tam) if p.get("texto") else -gap)
            tot = sum(wpart(p) for p in partes) + gap * (len(partes) - 1)
            esc = min(1.0, (s.W - 2 * s.m) / tot); ts *= esc; lado *= esc; gap *= esc
            tot = sum(wpart(p) * esc for p in partes) + gap * (len(partes) - 1)
            x = (s.W - tot) / 2; cy = y + 60 * u
            for p in partes:
                cor = s.cor(p.get("cor"), s.branco)
                if p.get("seta"):
                    t = cn.seta(x + 6 * u, cy, x + 84 * u * esc, cy, s.cor(p.get("cor"), s.destaque), t); x += 90 * u * esc + gap; continue
                if p.get("icone"):
                    t2 = cn.caixa(x, cy - lado / 2, lado, lado, cor if p.get("cor") else s.branco, t, r=18 * u, dur=0.4, preench=0.0)
                    cn.icone(p["icone"], x + lado / 2, cy, lado * 0.68, cor if p.get("cor") else s.branco, t + 0.3)
                    t = t2 - 0.05; x += lado + gap
                if p.get("texto"):
                    tam = ts * (1.3 if p.get("grande") else (0.75 if len(p["texto"]) <= 3 and not p.get("icone") else 1))
                    t = cn.texto(x, cy, p["texto"], tam, cor, t); x += largura(p["texto"], tam) + gap
            return t
        if tp == "grade":
            itens = b["itens"]; n = len(itens); col = b.get("colunas") or (min(n, 3) if s.vert else min(n, 4))
            c = s._lado_cartao(col); gap = 50 * u; fim = t
            for i, it in enumerate(itens):
                li, co = divmod(i, col); nlin = min(col, n - li * col)
                x0 = (s.W - (nlin * c + (nlin - 1) * gap)) / 2 + co * (c + gap); y0 = y + li * (c + 160 * u)
                cor = s.cor(it.get("cor")) or s.proxima()
                t1 = cn.caixa(x0, y0, c, c, cor, t, cursor=True)
                ics = it.get("icones") or ([it["icone"]] if it.get("icone") else [])
                if len(ics) == 1:
                    cn.icone(ics[0], x0 + c / 2, y0 + c / 2, c * 0.56, cor, t1)
                elif ics:
                    k = len(ics); mini = min((c - 40 * u - (k - 1) * 14 * u) / k, c * 0.42)
                    xs = x0 + (c - (k * mini + (k - 1) * 14 * u)) / 2
                    for j, nome in enumerate(ics):
                        mx = xs + j * (mini + 14 * u); my = y0 + (c - mini) / 2
                        cn.caixa(mx, my, mini, mini, cor, t1 + j * 0.15, r=14 * u, dur=0.3, preench=0.0)
                        cn.icone(nome, mx + mini / 2, my + mini / 2, mini * 0.7, cor, t1 + j * 0.15 + 0.2)
                t2 = t1 + 0.35 + 0.15 * max(0, len(ics) - 1)
                if it.get("rotulo"):
                    t2 = cn.texto(x0 + c / 2, y0 + c + 40 * u, it["rotulo"], 40 * u, s.branco, t2, ancora="middle")
                if it.get("botao"):
                    bt = 32 * u; bw = largura(it["botao"], bt) + 56 * u; bh = 54 * u
                    bx = x0 + (c - bw) / 2; by = y0 + c + 76 * u
                    cn.caixa(bx, by, bw, bh, cor, t2 - 0.1, r=bh / 2, dur=0.3, preench=0.0)
                    t2 = cn.texto(bx + bw / 2, by + bh / 2, it["botao"], bt, cor, t2 + 0.1, ancora="middle")
                fim = max(fim, t2); t = t1 + 0.35   # próximo cartão já começa (cascata, como no reel)
            return fim
        if tp == "numero":
            cor = s.cor(b.get("cor")) or s.proxima(); lado = 190 * u; x0 = s.m
            t1 = cn.caixa(x0, y, lado, lado, cor, t)
            cn.texto(x0 + lado / 2, y + lado / 2 + 6 * u, str(b["n"]), 150 * u, cor, t1 - 0.1, ancora="middle", modo="surgir")
            tx = x0 + lado + 40 * u; maxw = s.W - s.m - tx
            t2 = t1 + 0.3
            if b.get("linha1"):
                t2 = cn.texto(tx, y + 30 * u, b["linha1"], 40 * u, s.branco, t2)
            if b.get("linha2"):
                tam = 52 * u
                for i, ln in enumerate(s._quebrar(b["linha2"], tam, maxw)[:2]):
                    t2 = cn.texto(tx, y + 110 * u + i * tam * 1.15, ln, tam, s.branco, t2 + 0.1)
            return t2
        if tp == "fluxo":
            de, pn = b.get("de", {}), b.get("painel", {})
            cor_de = s.cor(de.get("cor")) or s.proxima(); cor_p = s.cor(pn.get("cor"), cor_de)
            lado = 180 * u
            if s.vert:   # vertical: ícone em cima, seta para baixo, painel na largura toda
                x0 = (s.W - lado) / 2; t1 = cn.caixa(x0, y, lado, lado, cor_de, t)
                cn.icone(de.get("icone", "robo"), x0 + lado / 2, y + lado / 2, lado * 0.62, cor_de, t1); t1 += 0.3
                if de.get("rotulo"):
                    t1 = cn.texto(s.W / 2, y + lado + 34 * u, de["rotulo"], 40 * u, cor_de, t1, ancora="middle")
                ya = y + lado + 70 * u
                t1 = cn.seta(s.W / 2, ya, s.W / 2 + 4 * u, ya + 100 * u, cor_de, t1)
                px, py, pw, ph = s.m, ya + 130 * u, s.W - 2 * s.m, 300 * u
                t1 = cn.caixa(px, py, pw, ph, cor_p, t1, dur=0.6, preench=0.10)
                return s.mock(cn, pn, px, py, pw, ph, cor_p, t1)
            x0 = s.m; cy = y + 120 * u
            t1 = cn.caixa(x0, cy - lado / 2, lado, lado, cor_de, t)
            cn.icone(de.get("icone", "robo"), x0 + lado / 2, cy, lado * 0.62, cor_de, t1)
            t1 += 0.3
            if de.get("rotulo"):
                t1 = cn.texto(x0 + lado / 2, cy + lado / 2 + 38 * u, de["rotulo"], 40 * u, cor_de, t1, ancora="middle")
            px = x0 + lado + 120 * u; pw = s.W - s.m - px; ph = 320 * u; py = y
            t1 = cn.seta(x0 + lado + 22 * u, cy, px - 22 * u, cy, cor_de, t1)
            t1 = cn.caixa(px, py, pw, ph, cor_p, t1, dur=0.6, preench=0.10)
            return s.mock(cn, pn, px, py, pw, ph, cor_p, t1)
        if tp == "frase":
            tam = b.get("tam", 84) * u; cor = s.cor(b.get("cor"), s.branco)
            linhas = s._quebrar(b["texto"], tam, s.W - 2 * s.m)
            for i, ln in enumerate(linhas):
                t = cn.texto(s.W / 2, y + tam * 0.6 + i * tam * 1.15, ln, tam, cor, t, ancora="middle") + 0.08
            wl = largura(linhas[-1], tam); yb = y + tam * 0.6 + (len(linhas) - 1) * tam * 1.15 + tam * 0.62
            x1 = (s.W - wl) / 2; x2 = x1 + wl
            onda = f"M{x1:.1f},{yb:.1f} C{x1 + wl * .3:.1f},{yb - 10 * u:.1f} {x1 + wl * .6:.1f},{yb + 10 * u:.1f} {x2:.1f},{yb - 4 * u:.1f}"
            return cn.linha(onda, s.cor(b.get("sublinhado"), s.destaque), t, dur=0.45)
        if tp == "lista":
            cor = s.cor(b.get("cor")) or s.proxima(); tam = 48 * u
            for i, txt in enumerate(b["itens"]):
                if b.get("tempos") and i < len(b["tempos"]):
                    t = max(t, b["tempos"][i])
                yy = y + i * 92 * u; q = 54 * u
                t1 = cn.caixa(s.m, yy, q, q, cor, t, r=12 * u, dur=0.3, preench=0.0)
                t1 = cn.texto(s.m + q + 30 * u, yy + q / 2, txt, tam, s.branco, t1)
                t = cn.icone("check", s.m + q / 2, yy + q / 2, q * 0.9, cor, t1) + 0.1
            return t
        if tp == "espaco":
            return t
        if tp == "desenho":
            alt = b.get("altura", 440) * u; larg = s.W - 2 * s.m
            k = min(larg / 600, alt / 400); tr = desenhos.T((s.W - 600 * k) / 2, y + (alt - 400 * k) / 2, k)
            passo = b.get("passo", 0.11)
            for tr_ in desenhos.CENAS[b["cena"]](tr):
                if tr_[0] == "linha":
                    cn.linha(tr_[1], s.cor(tr_[2], s.branco), t, dur=0.3); t += passo
                else:
                    _, x, yy, txt, tam, cor = tr_; X, Y = tr.xy(x, yy)
                    cn.texto(X, Y, txt, tam * k, s.cor(cor, s.branco), t, ancora="middle", modo="surgir"); t += passo
            return t + 0.3
        raise SystemExit(f"bloco desconhecido: {tp}")

    def mock(s, cn, pn, x, y, w, h, cor, t):
        u, m = s.u, pn.get("mock", "editor_video"); pad = 24 * u
        titulo = pn.get("titulo", "")
        if m == "editor_video":
            vw, vh = w * 0.5, h * 0.56; vx, vy = x + pad, y + pad
            t1 = cn.caixa(vx, vy, vw, vh, s.branco, t, r=10 * u, dur=0.45, preench=0.0, lw=4 * u)
            cn.icone("play", vx + vw / 2, vy + vh / 2, vh * 0.45, cor, t1)
            by = vy + vh + 26 * u; bh = 30 * u; ws = [0.36, 0.56, 0.4]; bx = vx
            for j, f in enumerate(ws):
                bw = vw * f * 0.7 if j < 2 else w * 0.2
                cc = cor if j != 1 else s.branco
                cn.caixa(bx, by, bw, bh, cc, t1 + 0.15 * j, r=8 * u, dur=0.3, preench=0.35 if j == 0 else 0.0, lw=4 * u)
                bx += bw + 14 * u
            tx = vx + vw + 30 * u; livre = x + w - pad - tx
            tt = min(50 * u, livre / max(1, largura(titulo, 1)) * 0.95) if titulo else 0
            t2 = cn.texto(tx + livre / 2, y + 80 * u, titulo, tt, cor, t1 + 0.4, ancora="middle") if titulo else t1 + 0.4
            cn.icone("tesoura", tx + livre / 2, y + 170 * u, 72 * u, s.branco, t2)
            return t2 + 0.5
        if m == "grafico":
            vals = pn.get("valores", [3, 5, 4, 8]); n = len(vals); bw = (w - 2 * pad - (n - 1) * 24 * u) / n
            base = y + h - pad; hmax = h - 2 * pad - 70 * u
            t1 = cn.texto(x + pad, y + 50 * u, titulo, 44 * u, cor, t) if titulo else t
            for j, v in enumerate(vals):
                bh = hmax * v / max(vals); bx = x + pad + j * (bw + 24 * u)
                cn.caixa(bx, base - bh, bw, bh, cor if j == n - 1 else s.branco, t1 + 0.18 * j, r=8 * u, dur=0.35,
                         preench=0.35 if j == n - 1 else 0.0, lw=4 * u)
            return t1 + 0.18 * n + 0.4
        if m == "lista":
            itens = pn.get("itens", ["item 1", "item 2", "item 3"]); t1 = t
            if titulo:
                t1 = cn.texto(x + pad, y + 46 * u, titulo, 44 * u, cor, t1)
            yy = y + (96 if titulo else 40) * u; q = 40 * u
            for txt in itens[:4]:
                cn.caixa(x + pad, yy, q, q, cor, t1, r=8 * u, dur=0.25, preench=0.0, lw=4 * u)
                t1 = cn.texto(x + pad + q + 20 * u, yy + q / 2, txt, 38 * u, s.branco, t1 + 0.2)
                t1 = cn.icone("check", x + pad + q / 2, yy + q / 2, q * 0.95, cor, t1) + 0.05; yy += 64 * u
            return t1
        if m == "chat":
            msgs = pn.get("itens", ["oi! pode me ajudar?", "claro, já resolvo"]); t1 = t; yy = y + pad
            for j, txt in enumerate(msgs[:3]):
                tam = 34 * u; bw = min(largura(txt, tam) + 44 * u, w - 2 * pad); bh = 64 * u
                bx = x + pad if j % 2 == 0 else x + w - pad - bw; cc = s.branco if j % 2 == 0 else cor
                t1 = cn.caixa(bx, yy, bw, bh, cc, t1, r=bh / 2, dur=0.3, preench=0.12, lw=4 * u)
                t1 = cn.texto(bx + bw / 2, yy + bh / 2, txt, tam, cc, t1, ancora="middle") + 0.15; yy += bh + 22 * u
            return t1
        raise SystemExit(f"mock desconhecido: {m}")

    def gerar(s):
        cenas, inicio = [], 0.0
        for c in s.p["cenas"]:
            cn = Cena(s); blocos = c["blocos"]; gap = c.get("espaco", 70) * s.u
            alts = [s.altura(b) for b in blocos]; tot = sum(alts) + gap * (len(blocos) - 1)
            y = max(s.H / 2 - tot / 2, 140 * s.u)          # centralizado na altura (regra do Gab: motion no centro)
            if s.p.get("base"): y = max(min(y, s.p["base"] - tot), 100 * s.u)   # "base": px onde o bloco termina (legenda livre embaixo)
            t = 0.25
            for b, a in zip(blocos, alts):
                if b.get("em") is not None:
                    t = max(t, b["em"])
                t = s.montar(cn, b, y, t) + 0.15; y += a + gap
            dur = c.get("dur") or round(t + c.get("segurar", 1.6), 2)
            cenas.append({"inicio": round(inicio, 3), "dur": dur, "itens": cn.itens, "ajuste": c.get("ajuste")}); inicio += dur
        return {"w": s.W, "h": s.H, "fps": s.p.get("fps", 30), "dur": round(inicio, 3), "cenas": cenas, "cps": s.cps,
                "lw": round(5.5 * s.u, 2), "preench": 0.22, "boil": 8, "fade_final": s.p.get("fade_final", False),
                "aspereza": {"freq": "0.035", "escala": str(round(2.6 * s.u, 2))},
                "cores": {"fundo": s.p.get("cores", {}).get("fundo", "#070707"), "luz": s.p.get("cores", {}).get("luz", "#1b1b1d")}}


def gerar(plano, pasta):
    os.makedirs(os.path.join(pasta, "fonts"), exist_ok=True); K = os.path.join(AQUI, "kit")
    pr = Gerador(plano).gerar()
    open(os.path.join(pasta, "plano.js"), "w").write("window.PLANO = " + json.dumps(pr, ensure_ascii=False) + ";\n")
    for f in ("sketch.js", "icones.js"):
        shutil.copy(os.path.join(K, f), pasta)
    shutil.copy(FONTE, os.path.join(pasta, "fonts"))
    html = open(os.path.join(K, "index.html")).read()
    for a, b in (("%W%", pr["w"]), ("%H%", pr["h"]), ("%FPS%", pr["fps"]), ("%DUR%", pr["dur"]), ("%FUNDO%", pr["cores"]["fundo"])):
        html = html.replace(a, str(b))
    open(os.path.join(pasta, "index.html"), "w").write(html)
    json.dump({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}},
              open(os.path.join(pasta, "hyperframes.json"), "w"))
    print("  ▸", os.path.basename(os.path.normpath(pasta)) + " ·", len(pr["cenas"]), "cenas", pr["dur"], "s"); return pasta


def centrar(plano_json, pasta):
    """Mede cada cena (centro.py) e grava "ajuste" para o conteúdo ficar no centro (540, 960) e dentro de 900x1200."""
    sys.path.insert(0, os.path.join(AQUI, "..", "..", "scripts")); import centro
    p = json.load(open(plano_json)); [c.pop("ajuste", None) for c in p["cenas"]]; gerar(p, pasta); ini = 0
    for c in p["cenas"]:
        m = centro.medir(pasta, [round(ini + c["dur"] - .4, 2)]); ini += c["dur"]
        k = min(1.0, centro.ALTURA_MAX / max(m["h"], 1), centro.LARGURA_MAX / max(m["w"], 1))
        if not m["ok"]: c["ajuste"] = [m["cx"], m["cy"], round(k, 4)]
    json.dump(p, open(plano_json, "w"), ensure_ascii=False, indent=1); gerar(p, pasta)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--centrar" in a:
        centrar(a[0], os.path.abspath(a[1])); a = [x for x in a if x != "--centrar"]
    if len(a) < 2:
        raise SystemExit(__doc__)
    pasta = gerar(json.load(open(a[0])), os.path.abspath(a[1]))
    if "--render" in a:
        saida = os.path.abspath(a[a.index("--render") + 1])
        _barra().hf(["npx", "--yes", "hyperframes@0.8.151", "render", pasta, "--format", "mp4", "-q", "delivery", "--workers", "1", "-o", saida], os.path.basename(os.path.dirname(os.path.abspath(__file__))))
        print("    →", os.path.basename(saida))
