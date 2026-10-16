"""Preset GLASS: kit de motions 16:9 (HyperFrames), estética premium. Módulo base (tipos de tela cheia e laterais).

  python gerar.py plano.json [ids...]   -> cria _hf/kit/out/<id>/index.html
Plano: lista de {"id","tipo","ini","fim", ...}; tempos ABSOLUTOS da timeline (s), já ancorados nas palavras
(ancorar.py). Tempo local = t - ini.
Com BG (tela cheia, opaco): numero, lista, frase, passos, versus
Sem BG (alfa, faixa livre da direita): callout, numero_lado, lista_lado, palavra   ("pos": "tela" = abaixo do facecam)

Linguagem visual: preto profundo com aurora violeta, grão de filme, hairlines, vidro escuro com filete de luz,
título metálico (branco -> lilás), destaque em Playfair itálico, números em Inter fina, revelações por máscara
(sobe de dentro da linha) com desfoque, eases expo, um brilho que atravessa por cartão, anel de ícone girando.
"""
import json, os, re, sys, shutil, html, random

AQUI = os.path.dirname(os.path.abspath(__file__))
FONTES = os.path.join(AQUI, "fonts")   # Inter e Playfair Display (OFL), dentro do preset
IMG_BASE = os.getcwd()
OUT = os.path.join(os.getcwd(), "motions_vidro_violeta")   # gerar.py troca pela pasta pedida                 # pasta de onde vêm as imagens citadas no plano (gerar.py usa a pasta do plano.json)
ARQ_FONTES = ["Inter-VariableFont_opsz,wght.ttf", "PlayfairDisplay-Italic.ttf"]
VERDE, VERMELHO = "#6ee7b7", "#fca5a5"

ICONES = {  # traço 24x24, se desenham com stroke-dashoffset
    "check": "M5 12.5l4.5 4.5L19 7.5",
    "dinheiro": "M12 2v20M17 6.5c-1-1.6-2.8-2.5-5-2.5-3 0-5 1.6-5 3.8 0 5.4 10 2.8 10 8.4 0 2.3-2.2 3.8-5 3.8-2.4 0-4.4-1-5.4-2.8",
    "grafico": "M3 20h18M5 16l4-5 4 3 6-8M15 6h4v4",
    "carrinho": "M3 4h2.5l2.2 11h10.6l2-8H7M9.5 20a1 1 0 1 0 0-.01M17 20a1 1 0 1 0 0-.01",
    "pagina": "M5 3h10l4 4v14H5zM15 3v4h4M8 12h8M8 16h6",
    "raio": "M13 2L4 14h7l-1 8 9-12h-7z",
    "alvo": "M12 3a9 9 0 1 0 .01 0M12 7a5 5 0 1 0 .01 0M12 11a1 1 0 1 0 .01 0",
    "foguete": "M12 15l-3-3c1.5-4.5 5-8 10-9-1 5-4.5 8.5-9 10zM9 12l-4 1-1 4 4-1M12 15l-1 4 4-1 1-4M14.5 9.5a1 1 0 1 0 .01 0",
    "pessoas": "M9 11a3.5 3.5 0 1 0 .01 0M2.5 20c.6-3.5 3.3-5.5 6.5-5.5s5.9 2 6.5 5.5M16 4.5a3.5 3.5 0 0 1 0 6.5M18 14.5c2 .7 3.2 2.6 3.5 5.5",
    "relogio": "M12 3a9 9 0 1 0 .01 0M12 7v5l3.5 2",
    "alerta": "M12 3L2 20h20zM12 9v5M12 17.2v.01",
    "celular": "M7 2h10v20H7zM11 18.5h2",
    "estrela": "M12 3l2.7 5.6 6.1.8-4.5 4.3 1.1 6.1L12 17l-5.4 2.8 1.1-6.1L3.2 9.4l6.1-.8z",
    "x": "M6 6l12 12M18 6L6 18",
}


def ic(nome, cor=None):
    st = f' style="stroke:{cor}"' if cor else ""
    return f'<svg class="ic" viewBox="0 0 24 24"{st}><path pathLength="1" d="{ICONES.get(nome, ICONES["raio"])}"/></svg>'


def medalha(cid, k, nome, tam, cor=None):
    """Ícone dentro de um anel com borda em gradiente que gira devagar."""
    return (f'<div class="med" style="width:{tam}px;height:{tam}px"><div class="anel" id="{cid}-an{k}"></div>'
            f'<div class="miolo" style="padding:{tam * .27:.0f}px">{ic(nome, cor)}</div></div>')


def esc(s):
    return html.escape(str(s))


def linha(cid, k, conteudo, estilo=""):
    """Texto que sobe de dentro da própria linha (máscara)."""
    return f'<div class="mk" style="{estilo}"><div class="mi" id="{cid}-{k}">{conteudo}</div></div>'


CSS = """
@font-face{font-family:Inter;src:url("fonts/Inter-VariableFont_opsz,wght.ttf");font-weight:100 900}
@font-face{font-family:Play;src:url(fonts/PlayfairDisplay-Italic.ttf);font-style:italic}
body{margin:0;background:transparent}
#root{position:relative;width:100%;height:100%;overflow:hidden;font-family:Inter;color:#f4f1ff}
.full{position:absolute;inset:0}
.ic{width:100%;height:100%;fill:none;stroke:#ddd6fe;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;overflow:visible;display:block}
.met{background:linear-gradient(180deg,#ffffff 0%,#f1ecff 42%,#b9a6f7 100%);-webkit-background-clip:text;background-clip:text;color:transparent;
 filter:drop-shadow(0 6px 30px rgba(139,92,246,.35))}
.ser{font-family:Play;font-style:italic;font-weight:400;letter-spacing:0;text-transform:none}
.ser.met{background:linear-gradient(180deg,#ffffff 0%,#e4dbff 50%,#a78bfa 100%);-webkit-background-clip:text;background-clip:text}
.eyebrow{display:flex;align-items:center;gap:22px;font-weight:600;font-size:22px;letter-spacing:.42em;text-transform:uppercase;color:#a78bfa}
.eyebrow i{display:block;width:70px;height:1px;background:linear-gradient(90deg,transparent,#a78bfa)}
.eyebrow i:last-child{background:linear-gradient(90deg,#a78bfa,transparent)}
.mk{overflow:hidden;padding:.08em .06em .16em}
.mi{display:block}
.vidro{position:relative;overflow:hidden;border-radius:26px;background:linear-gradient(160deg,rgba(38,28,72,.62),rgba(12,9,24,.78) 60%);
 border:1px solid rgba(255,255,255,.09);box-shadow:0 30px 80px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,255,255,.16),inset 0 0 0 1px rgba(167,139,250,.06)}
.vidro::before{content:"";position:absolute;left:0;right:0;top:0;height:1px;background:linear-gradient(90deg,transparent,rgba(221,214,254,.75),transparent)}
.lado-on .vidro{background:linear-gradient(160deg,rgba(32,22,62,.94),rgba(10,8,20,.96) 65%)}
.glint{position:absolute;top:-30%;bottom:-30%;width:22%;left:0;background:linear-gradient(100deg,transparent,rgba(255,255,255,.13),transparent);transform:skewX(-18deg)}
.med{position:relative;flex:none}
.anel{position:absolute;inset:0;border-radius:50%;padding:1.5px;background:conic-gradient(from 0deg,rgba(167,139,250,.05),#c4b5fd,rgba(167,139,250,.05) 40%,#7c3aed,rgba(167,139,250,.05));
 -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude}
.miolo{position:absolute;inset:6px;border-radius:50%;background:radial-gradient(circle at 50% 30%,rgba(139,92,246,.28),rgba(10,8,22,.9) 70%);box-sizing:border-box}
.pt{position:absolute;border-radius:50%;background:#ddd6fe}
.num{font-weight:200;letter-spacing:-.04em;line-height:.95;font-variant-numeric:tabular-nums}
"""


def bg_html(cid, rnd):
    pts = []
    for _ in range(34):
        x, y, s = rnd.uniform(0, 1920), rnd.uniform(0, 1080), rnd.uniform(1.5, 4.5)
        pts.append(f'<i class="pt" style="left:{x:.0f}px;top:{y:.0f}px;width:{s:.1f}px;height:{s:.1f}px;'
                   f'opacity:{rnd.uniform(.12, .5):.2f};filter:blur({0 if s < 3 else 1.5}px)"></i>')
    return f"""
<div class="full" style="background:#050409"></div>
<div id="{cid}-au1" class="full" style="background:radial-gradient(ellipse 60% 55% at 30% 35%,rgba(109,40,217,.42),transparent 70%)"></div>
<div id="{cid}-au2" class="full" style="background:radial-gradient(ellipse 50% 45% at 75% 70%,rgba(76,29,149,.38),transparent 70%)"></div>
<div class="full" style="perspective:800px;overflow:hidden"><div id="{cid}-grid" style="position:absolute;left:-60%;right:-60%;top:60%;height:150%;
 background-image:linear-gradient(rgba(167,139,250,.13) 1px,transparent 1px),linear-gradient(90deg,rgba(167,139,250,.13) 1px,transparent 1px);
 background-size:120px 120px;transform:rotateX(76deg);transform-origin:50% 0;-webkit-mask-image:linear-gradient(to bottom,#000,transparent 70%)"></div></div>
<div style="position:absolute;left:0;right:0;top:60%;height:1px;background:linear-gradient(90deg,transparent,rgba(196,181,253,.55),transparent);box-shadow:0 0 30px 4px rgba(139,92,246,.35)"></div>
<div id="{cid}-pts" class="full">{''.join(pts)}</div>
<div id="{cid}-ray" style="position:absolute;top:-40%;height:180%;width:340px;left:-500px;transform:rotate(20deg);
 background:linear-gradient(90deg,transparent,rgba(221,214,254,.06),transparent)"></div>
<svg class="full" style="opacity:.10;mix-blend-mode:overlay" width="1920" height="1080"><filter id="{cid}-gr"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="7"/></filter>
 <rect id="{cid}-grr" x="-40" y="-40" width="2000" height="1160" filter="url(#{cid}-gr)"/></svg>
<div class="full" style="background:radial-gradient(ellipse at center,transparent 45%,rgba(0,0,0,.78) 100%)"></div>
"""


def bg_js(cid, dur):
    n = max(1, int(dur / .08))
    return f"""
tl.fromTo("#{cid}-au1",{{x:-60,y:20,scale:1}},{{x:80,y:-30,scale:1.12,duration:{dur},ease:"sine.inOut"}},0);
tl.fromTo("#{cid}-au2",{{x:40,scale:1.1}},{{x:-70,scale:1,duration:{dur},ease:"sine.inOut"}},0);
tl.fromTo("#{cid}-grid",{{backgroundPosition:"0px 0px"}},{{backgroundPosition:"0px 240px",duration:{dur},ease:"none"}},0);
tl.fromTo("#{cid}-pts .pt",{{y:0}},{{y:(i)=>-30-(i%6)*14,duration:{dur},ease:"none"}},0);
tl.fromTo("#{cid}-ray",{{x:0}},{{x:3000,duration:{max(dur, 4)},ease:"power1.inOut"}},.2);
tl.fromTo("#{cid}-grr",{{x:0,y:0}},{{x:-30,y:-20,duration:.08,repeat:{n},ease:"steps(1)"}},0);
"""


def achar_bruto(nome):
    """Imagem citada no plano: caminho absoluto ou relativo a IMG_BASE (acentos em NFC ou NFD)."""
    import unicodedata
    if os.path.isabs(nome) and os.path.exists(nome):
        return nome
    cand = os.path.join(IMG_BASE, nome)
    if os.path.exists(cand):
        return cand
    pasta, alvo = os.path.dirname(cand), unicodedata.normalize("NFC", os.path.basename(nome))
    return next(os.path.join(pasta, f) for f in os.listdir(pasta) if unicodedata.normalize("NFC", f) == alvo)


def nome_img(nome):
    import hashlib
    return "img_" + hashlib.md5(nome.encode("utf-8")).hexdigest()[:8] + os.path.splitext(nome)[1]


def paleta(doc, cor=None):
    """Troca o violeta do kit pela cor da marca: gira o matiz de todo hex/rgba violeta (240-300 graus) para o da cor."""
    if not cor:
        return doc
    import colorsys
    alvo = colorsys.rgb_to_hls(*[int(cor.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)])[0]
    base = colorsys.rgb_to_hls(0x8b / 255, 0x5c / 255, 0xf6 / 255)[0]

    def gira(r, g, b):
        h, l, s_ = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if not (240 / 360 <= h <= 300 / 360) or s_ < .2:
            return r, g, b
        return [round(x * 255) for x in colorsys.hls_to_rgb((h + alvo - base) % 1, l, s_)]
    doc = re.sub(r"#([0-9a-fA-F]{6})\b", lambda m_: "#%02x%02x%02x" % tuple(gira(*[int(m_[1][i:i + 2], 16) for i in (0, 2, 4)])), doc)
    return re.sub(r"rgba\((\d+),(\d+),(\d+),", lambda m_: "rgba(%d,%d,%d," % tuple(gira(int(m_[1]), int(m_[2]), int(m_[3]))), doc)


def tem_bg(tipo):
    return tipo in ("numero", "lista", "frase", "passos", "versus")


def L(m, t):
    return round(max(0.05, t - m["ini"]), 3)


def sobe(sel, t, d=.9):
    return f'tl.fromTo("{sel}",{{yPercent:110,opacity:0,filter:"blur(8px)"}},{{yPercent:0,opacity:1,filter:"blur(0px)",duration:{d},ease:"expo.out"}},{t:.2f});'


def desenha(sel, t, d=.9):
    return f'tl.fromTo("{sel} .ic",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:{d},ease:"power2.inOut"}},{t:.2f});'


def gira(cid, k, t, dur):
    return f'tl.fromTo("#{cid}-an{k}",{{rotate:0,opacity:0}},{{rotate:{int(dur * 40)},opacity:1,duration:{max(dur - t, .5):.2f},ease:"none"}},{t:.2f});'


def contador(cid, m, t0, t1, el):
    pre, suf = m.get("prefixo", ""), m.get("sufixo", "")
    return (f'const o{cid}={{v:0}};tl.to(o{cid},{{v:{m["valor"]},duration:{max(.3, t1 - t0):.2f},ease:"expo.out",'
            f'onUpdate:()=>{{document.getElementById("{el}").textContent="{pre}"+Math.round(o{cid}.v).toLocaleString("pt-BR")+"{suf}"}}}},{t0:.2f});')


def corpo(m, cid, dur):
    tipo, H, J = m["tipo"], [], []
    if tipo == "numero":
        t1 = L(m, m["t"]); t0 = max(.15, t1 - 1.1)
        H.append(f"""<div class="full" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:30px">
 <div id="{cid}-eb" class="eyebrow"><i></i>{esc(m.get('rotulo', 'em números'))}<i></i></div>
 <div class="mk"><div class="mi num met" id="{cid}-num" style="font-size:{m.get('tam', 260)}px">{esc(m.get('prefixo', ''))}0{esc(m.get('sufixo', ''))}</div></div>
 <div id="{cid}-hl" style="width:620px;height:1px;background:linear-gradient(90deg,transparent,#c4b5fd,transparent)"></div>
 {linha(cid, 'leg', esc(m['legenda']), 'font-size:44px;font-weight:300;color:#e9e4ff;letter-spacing:.01em')}</div>""")
        J += [f'tl.fromTo("#{cid}-eb",{{opacity:0,y:10}},{{opacity:1,y:0,duration:.8,ease:"power3.out"}},.1);',
              sobe(f"#{cid}-num", t0, 1.0), contador(cid, m, t0, t1, f"{cid}-num"),
              f'tl.fromTo("#{cid}-num",{{scale:1}},{{scale:1.04,duration:.25,yoyo:true,repeat:1,ease:"power2.out"}},{t1:.2f});',
              f'tl.fromTo("#{cid}-hl",{{scaleX:0}},{{scaleX:1,duration:1.1,ease:"expo.out"}},{t1:.2f});',
              sobe(f"#{cid}-leg", L(m, m.get("t_leg", m["t"])) + .1, .9)]
    elif tipo == "frase":
        pal = "".join(
            f'<span class="mk" style="display:inline-block;vertical-align:bottom;margin:0 .16em"><span class="mi {"ser met" if p.get("d") else "met"}" id="{cid}-w{i}">{esc(p["p"])}</span></span>'
            for i, p in enumerate(m["palavras"]))
        H.append(f"""<div class="full" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:44px">
 <div id="{cid}-icw">{medalha(cid, 0, m.get('icone', 'raio'), 104)}</div>
 <div style="font-weight:700;font-size:{m.get('tam', 100)}px;line-height:1.08;letter-spacing:-.02em;text-align:center;max-width:1560px">{pal}</div>
 <div id="{cid}-hl" style="width:420px;height:1px;background:linear-gradient(90deg,transparent,#c4b5fd,transparent)"></div></div>""")
        J += [f'tl.fromTo("#{cid}-icw",{{opacity:0,scale:.8}},{{opacity:1,scale:1,duration:.9,ease:"expo.out"}},.05);',
              desenha(f"#{cid}-icw", .25), gira(cid, 0, .05, dur)]
        for i, p in enumerate(m["palavras"]):
            J.append(sobe(f"#{cid}-w{i}", L(m, p["t"]), .85))
            if p.get("d"):
                J.append(f'tl.fromTo("#{cid}-w{i}",{{scale:1.12}},{{scale:1,duration:1.2,ease:"expo.out"}},{L(m, p["t"]):.2f});')
        J.append(f'tl.fromTo("#{cid}-hl",{{scaleX:0}},{{scaleX:1,duration:1.2,ease:"expo.out"}},{L(m, m["palavras"][-1]["t"]) + .2:.2f});')
    elif tipo == "lista":
        it = m["itens"]; alto = len(it) > 5
        linhas = "".join(f"""<div class="vidro" id="{cid}-i{i}" style="display:flex;align-items:center;gap:26px;padding:{16 if alto else 22}px 34px;width:900px">
 <div style="font-weight:200;font-size:{34 if alto else 40}px;color:#a78bfa;width:54px;font-variant-numeric:tabular-nums">{i + 1:02d}</div>
 <div style="width:1px;align-self:stretch;background:rgba(196,181,253,.25)"></div>
 <div style="font-size:{38 if alto else 44}px;font-weight:500;flex:1">{esc(x['txt'])}</div>
 <div style="width:{40 if alto else 46}px;height:{40 if alto else 46}px">{ic('check', VERDE)}</div><div class="glint" id="{cid}-g{i}"></div></div>""" for i, x in enumerate(it))
        H.append(f"""<div class="full" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:{12 if alto else 18}px">
 <div id="{cid}-eb" class="eyebrow" style="margin-bottom:6px"><i></i>{esc(m.get('rotulo', 'a oferta'))}<i></i></div>
 {linha(cid, 'tit', esc(m['titulo']), 'font-size:72px;font-weight:700;letter-spacing:-.02em;margin-bottom:18px')}{linhas}</div>""")
        J += [f'tl.fromTo("#{cid}-eb",{{opacity:0}},{{opacity:1,duration:.8}},.05);', sobe(f"#{cid}-tit", .1, 1.0)]
        for i, x in enumerate(it):
            lt = L(m, x["t"])
            J += [f'tl.fromTo("#{cid}-i{i}",{{opacity:0,y:30,filter:"blur(10px)"}},{{opacity:1,y:0,filter:"blur(0px)",duration:.8,ease:"expo.out"}},{lt:.2f});',
                  desenha(f"#{cid}-i{i}", lt + .25, .6),
                  f'tl.fromTo("#{cid}-g{i}",{{x:-250}},{{x:1200,duration:1.1,ease:"power2.inOut"}},{lt + .3:.2f});']
    elif tipo == "passos":
        it = m["itens"]; q = len(it)
        w, h = (380, 400) if q < 4 else (330, 380)
        cx = []
        for i, x in enumerate(it):
            cx.append(f"""<div class="vidro" id="{cid}-i{i}" style="width:{w}px;height:{h}px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px">
 <div style="font-weight:200;font-size:30px;letter-spacing:.3em;color:#a78bfa">{i + 1:02d}</div>{medalha(cid, i, x.get('icone', 'raio'), 118)}
 <div style="font-size:{40 if q < 4 else 34}px;font-weight:600;text-align:center;padding:0 22px;line-height:1.15">{esc(x['txt'])}</div><div class="glint" id="{cid}-g{i}"></div></div>""")
            if i < q - 1:
                cx.append(f'<div id="{cid}-a{i}" style="width:{60 if q < 4 else 44}px;height:1px;background:linear-gradient(90deg,rgba(196,181,253,.2),#c4b5fd);transform-origin:0 50%"></div>')
        H.append(f"""<div class="full" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:50px">
 <div style="display:flex;flex-direction:column;align-items:center;gap:16px"><div id="{cid}-eb" class="eyebrow"><i></i>{esc(m.get('rotulo', 'na prática'))}<i></i></div>
 {linha(cid, 'tit', esc(m['titulo']), 'font-size:72px;font-weight:700;letter-spacing:-.02em')}</div>
 <div style="display:flex;align-items:center;gap:22px">{''.join(cx)}</div></div>""")
        J += [f'tl.fromTo("#{cid}-eb",{{opacity:0}},{{opacity:1,duration:.8}},.05);', sobe(f"#{cid}-tit", .1, 1.0)]
        for i, x in enumerate(it):
            lt = L(m, x["t"])
            J += [f'tl.fromTo("#{cid}-i{i}",{{opacity:0,y:50,filter:"blur(12px)"}},{{opacity:1,y:0,filter:"blur(0px)",duration:.9,ease:"expo.out"}},{lt:.2f});',
                  desenha(f"#{cid}-i{i}", lt + .25, .8), gira(cid, i, lt, dur),
                  f'tl.fromTo("#{cid}-g{i}",{{x:-200}},{{x:600,duration:1.1,ease:"power2.inOut"}},{lt + .4:.2f});']
            if i > 0:
                J.append(f'tl.fromTo("#{cid}-a{i - 1}",{{scaleX:0}},{{scaleX:1,duration:.5,ease:"power2.out"}},{max(.1, lt - .3):.2f});')
    elif tipo == "versus":
        a, b = m["a"], m["b"]

        def lado(k, d, cor, icone):
            if d.get("img"):
                arq = nome_img(d["img"])
                vis = (f'<div style="position:relative"><img src="{arq}" style="display:block;height:230px;border-radius:14px;box-shadow:0 12px 40px rgba(0,0,0,.5)">'
                       f'<div id="{cid}-{k}x" style="position:absolute;right:-26px;top:-26px;width:84px;height:84px;border-radius:50%;background:#1a0b0b;border:2px solid {cor};'
                       f'padding:20px;box-sizing:border-box;box-shadow:0 0 34px rgba(248,113,113,.55)">{ic(icone, cor)}</div></div>')
            else:
                vis = medalha(cid, k, icone, 130, cor)
            return f"""<div class="vidro" id="{cid}-{k}" style="width:620px;height:{560 if d.get('img') else 500}px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:{24 if d.get('img') else 30}px">
 <div style="font-weight:600;font-size:22px;letter-spacing:.38em;color:{cor}">{esc(d['rot'])}</div>{vis}
 <div style="font-size:46px;font-weight:500;text-align:center;padding:0 46px;line-height:1.2">{esc(d['txt'])}</div>
 <div style="position:absolute;left:20%;right:20%;bottom:0;height:2px;background:linear-gradient(90deg,transparent,{cor},transparent)"></div></div>"""
        H.append(f"""<div class="full" style="display:flex;align-items:center;justify-content:center;gap:56px">
 {lado('a', a, a.get('cor', VERMELHO), a.get('icone', 'x'))}
 <div id="{cid}-vs" class="ser met" style="font-size:96px;padding:0 .1em .1em">vs</div>
 {lado('b', b, b.get('cor', VERDE), b.get('icone', 'check'))}</div>""")
        ta, tb = L(m, a["t"]), L(m, b["t"])
        J += [f'tl.fromTo("#{cid}-a",{{opacity:0,x:-80,filter:"blur(14px)"}},{{opacity:1,x:0,filter:"blur(0px)",duration:1,ease:"expo.out"}},{ta:.2f});',
              desenha(f"#{cid}-a", ta + .3), gira(cid, "a", ta, dur),
              f'tl.fromTo("#{cid}-vs",{{opacity:0,scale:.6}},{{opacity:1,scale:1,duration:.9,ease:"expo.out"}},{max(ta + .4, tb - .35):.2f});',
              f'tl.fromTo("#{cid}-b",{{opacity:0,x:80,filter:"blur(14px)"}},{{opacity:1,x:0,filter:"blur(0px)",duration:1,ease:"expo.out"}},{tb:.2f});',
              desenha(f"#{cid}-b", tb + .3), gira(cid, "b", tb, dur),
              f'tl.to("#{cid}-a",{{opacity:.45,scale:.97,duration:.8,ease:"power2.out"}},{tb + .2:.2f});']
    # ---------- sem BG (alfa) ----------
    elif tipo == "callout":
        t = L(m, m["t"])
        H.append(f"""<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center">
 <div class="vidro" id="{cid}-card" style="width:700px;padding:42px 46px;display:flex;gap:34px;align-items:center">
  <div id="{cid}-icw">{medalha(cid, 0, m.get('icone', 'raio'), 128)}</div>
  <div style="flex:1"><div class="eyebrow" id="{cid}-eb" style="font-size:18px;gap:14px;margin-bottom:10px">{esc(m.get('rotulo', 'estrutura'))}</div>
  {linha(cid, 'tit', esc(m['titulo']), 'font-size:58px;font-weight:700;letter-spacing:-.02em;line-height:1.02')}
  {linha(cid, 'sub', f'<span class="ser" style="color:#ddd6fe">{esc(m.get("sub", ""))}</span>', 'font-size:40px;margin-top:6px')}</div>
  <div class="glint" id="{cid}-g"></div></div></div>""")
        J += [f'tl.fromTo("#{cid}-card",{{opacity:0,x:70,filter:"blur(16px)"}},{{opacity:1,x:0,filter:"blur(0px)",duration:1,ease:"expo.out"}},{t:.2f});',
              f'tl.fromTo("#{cid}-eb",{{opacity:0}},{{opacity:1,duration:.6}},{t + .2:.2f});',
              sobe(f"#{cid}-tit", t + .15, .9), desenha(f"#{cid}-icw", t + .3), gira(cid, 0, t, dur),
              sobe(f"#{cid}-sub", max(t + .45, L(m, m.get("t_sub", m["t"]))), .9),
              f'tl.fromTo("#{cid}-g",{{x:-220}},{{x:900,duration:1.2,ease:"power2.inOut"}},{t + .5:.2f});',
              f'tl.to("#{cid}-card",{{opacity:0,x:40,filter:"blur(14px)",duration:.5,ease:"power2.in"}},{dur - .55:.2f});']
    elif tipo == "numero_lado":
        t1 = L(m, m["t"]); t0 = max(.1, t1 - .9)
        H.append(f"""<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center">
 <div class="vidro" id="{cid}-card" style="width:640px;padding:48px 40px;display:flex;flex-direction:column;align-items:center;gap:14px">
 <div class="eyebrow" id="{cid}-eb" style="font-size:18px"><i></i>{esc(m.get('rotulo', 'resultado'))}<i></i></div>
 <div class="mk"><div class="mi num met" id="{cid}-num" style="font-size:{m.get('tam', 170)}px">{esc(m.get('prefixo', ''))}0{esc(m.get('sufixo', ''))}</div></div>
 <div id="{cid}-hl" style="width:360px;height:1px;background:linear-gradient(90deg,transparent,#c4b5fd,transparent)"></div>
 {linha(cid, 'leg', f'<span class="ser">{esc(m["legenda"])}</span>', 'font-size:40px;color:#e9e4ff;text-align:center')}
 <div class="glint" id="{cid}-g"></div></div></div>""")
        J += [f'tl.fromTo("#{cid}-card",{{opacity:0,y:30,filter:"blur(16px)"}},{{opacity:1,y:0,filter:"blur(0px)",duration:1,ease:"expo.out"}},{max(.05, t0 - .3):.2f});',
              f'tl.fromTo("#{cid}-eb",{{opacity:0}},{{opacity:1,duration:.6}},{t0:.2f});',
              sobe(f"#{cid}-num", t0, .9), contador(cid, m, t0, t1, f"{cid}-num"),
              f'tl.fromTo("#{cid}-hl",{{scaleX:0}},{{scaleX:1,duration:1,ease:"expo.out"}},{t1:.2f});',
              sobe(f"#{cid}-leg", max(t1 + .1, L(m, m.get("t_leg", m["t"]))), .9),
              f'tl.fromTo("#{cid}-g",{{x:-220}},{{x:900,duration:1.2,ease:"power2.inOut"}},{t1 + .2:.2f});',
              f'tl.to("#{cid}-card",{{opacity:0,y:-20,filter:"blur(14px)",duration:.5,ease:"power2.in"}},{dur - .55:.2f});']
    elif tipo == "lista_lado":
        it = m["itens"]; alto = len(it) > 4
        linhas = "".join(f"""<div id="{cid}-i{i}" style="display:flex;align-items:center;gap:22px;padding:{12 if alto else 18}px 0;border-top:1px solid rgba(196,181,253,.14)">
 <div style="font-weight:200;font-size:30px;color:#a78bfa;width:44px;font-variant-numeric:tabular-nums">{i + 1:02d}</div>
 <div style="font-size:{34 if alto else 38}px;font-weight:500;flex:1">{esc(x['txt'])}</div><div style="width:36px;height:36px">{ic('check', VERDE)}</div></div>""" for i, x in enumerate(it))
        H.append(f"""<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center">
 <div class="vidro" id="{cid}-card" style="width:660px;padding:40px 44px 26px">
 <div class="eyebrow" id="{cid}-eb" style="font-size:18px;margin-bottom:10px">{esc(m.get('rotulo', 'checklist'))}</div>
 {linha(cid, 'tit', esc(m['titulo']), 'font-size:52px;font-weight:700;letter-spacing:-.02em;margin-bottom:16px')}{linhas}</div></div>""")
        tt = L(m, m.get("t_tit", m["ini"] + .1))
        J += [f'tl.fromTo("#{cid}-card",{{opacity:0,x:60,filter:"blur(16px)"}},{{opacity:1,x:0,filter:"blur(0px)",duration:1,ease:"expo.out"}},{tt:.2f});',
              f'tl.fromTo("#{cid}-eb",{{opacity:0}},{{opacity:1,duration:.6}},{tt + .2:.2f});', sobe(f"#{cid}-tit", tt + .15, .9)]
        for i, x in enumerate(it):
            lt = max(tt + .5, L(m, x["t"]))
            J += [f'tl.fromTo("#{cid}-i{i}",{{opacity:0,x:40,filter:"blur(8px)"}},{{opacity:1,x:0,filter:"blur(0px)",duration:.8,ease:"expo.out"}},{lt:.2f});',
                  desenha(f"#{cid}-i{i}", lt + .2, .5)]
        J.append(f'tl.to("#{cid}-card",{{opacity:0,x:40,filter:"blur(14px)",duration:.5,ease:"power2.in"}},{dur - .55:.2f});')
    elif tipo == "palavra":
        t = L(m, m["t"])
        H.append(f"""<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center">
 <div id="{cid}-wrap" style="display:flex;flex-direction:column;align-items:center;gap:18px;padding:50px 60px;border-radius:30px;
  background:radial-gradient(ellipse at center,rgba(8,6,18,.85) 0%,rgba(8,6,18,.6) 55%,transparent 75%)">
 <div class="eyebrow" id="{cid}-eb" style="font-size:18px"><i></i>{esc(m.get('rotulo', 'anota aí'))}<i></i></div>
 {linha(cid, 'p', f'<span class="ser met">{esc(m["texto"])}</span>', f'font-size:{m.get("tam", 104)}px;line-height:1.05;text-align:center')}
 <div id="{cid}-hl" style="width:420px;height:1px;background:linear-gradient(90deg,transparent,#c4b5fd,transparent)"></div></div></div>""")
        J += [f'tl.fromTo("#{cid}-wrap",{{opacity:0}},{{opacity:1,duration:.5}},{t:.2f});',
              f'tl.fromTo("#{cid}-eb",{{opacity:0,y:8}},{{opacity:1,y:0,duration:.7,ease:"power3.out"}},{t + .05:.2f});',
              sobe(f"#{cid}-p", t + .1, 1.0),
              f'tl.fromTo("#{cid}-hl",{{scaleX:0}},{{scaleX:1,duration:1.1,ease:"expo.out"}},{t + .4:.2f});',
              f'tl.to("#{cid}-wrap",{{opacity:0,filter:"blur(12px)",duration:.45,ease:"power2.in"}},{dur - .5:.2f});']
    elif tipo == "stinger":  # transição de momento: painéis diagonais cobrem, nome do momento, revelam
        cores = ["#07050f", "linear-gradient(90deg,#1e0b4b,#5b21b6 60%,#7c3aed)", "#0d0a1c"]
        pain = "".join(f'<div id="{cid}-p{k}" style="position:absolute;top:-20%;bottom:-20%;left:-400px;width:2700px;'
                       f'transform:skewX(-14deg);background:{c};box-shadow:-30px 0 80px rgba(0,0,0,.6)">'
                       f'<div style="position:absolute;left:0;top:0;bottom:0;width:2px;background:linear-gradient(180deg,transparent,#ddd6fe,transparent);'
                       f'box-shadow:0 0 24px 6px rgba(167,139,250,.55)"></div></div>' for k, c in enumerate(cores))
        H.append(f"""{pain}
 <div id="{cid}-lb" class="full" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px">
  <div id="{cid}-eb" class="eyebrow"><i></i>{esc(m.get('rotulo', 'próximo'))}<i></i></div>
  {linha(cid, 'tx', f'<span class="ser met">{esc(m["texto"])}</span>', 'font-size:150px;line-height:1.05')}
  <div id="{cid}-hl" style="width:380px;height:1px;background:linear-gradient(90deg,transparent,#c4b5fd,transparent)"></div></div>""")
        for k in range(3):  # entra pela direita, cobre, sai pela esquerda
            J += [f'tl.fromTo("#{cid}-p{k}",{{x:2500}},{{x:0,duration:.42,ease:"expo.out"}},{.02 + k * .07:.2f});',
                  f'tl.to("#{cid}-p{k}",{{x:-3000,duration:.38,ease:"expo.in"}},{dur - .48 - k * .05:.2f});']
        J += [f'tl.fromTo("#{cid}-eb",{{opacity:0}},{{opacity:1,duration:.25}},.3);', sobe(f"#{cid}-tx", .28, .45),
              f'tl.fromTo("#{cid}-hl",{{scaleX:0}},{{scaleX:1,duration:.5,ease:"expo.out"}},.4);',
              f'tl.to("#{cid}-lb",{{opacity:0,x:-120,filter:"blur(10px)",duration:.22,ease:"power2.in"}},{dur - .62:.2f});']
    elif tipo == "inscreva":  # cartão do canal: foto, nome, cursor clica no like e no Inscrever-se, sino balança
        tl_, ti_ = L(m, m.get("t_like", m["ini"] + 1.5)), L(m, m.get("t_insc", m["ini"] + 2.7))
        ti_ = max(ti_, tl_ + .9)
        polegar = "M7 10v11H3V10zM7 10l4-8c1.7 0 2.8 1.3 2.5 3L13 9h6.2c1.2 0 2.1 1.1 1.9 2.3l-1.4 8c-.2 1-1 1.7-2 1.7H7"
        sino = "M6 16V11a6 6 0 0 1 12 0v5l2 2H4zM10 20a2 2 0 0 0 4 0"
        faisca = "".join(f'<i id="{cid}-f{k}" style="position:absolute;left:50%;top:50%;width:8px;height:8px;margin:-4px;border-radius:50%;background:#c4b5fd;opacity:0"></i>' for k in range(8))
        H.append(f"""<div id="{cid}-card" class="vidro" style="position:absolute;right:70px;bottom:78px;display:flex;align-items:center;gap:26px;padding:24px 30px 24px 24px;border-radius:120px">
 <div class="med" style="width:118px;height:118px"><div class="anel" id="{cid}-an0"></div>
  <img src="avatar.jpg" style="position:absolute;inset:6px;width:106px;height:106px;border-radius:50%;object-fit:cover"></div>
 <div style="display:flex;flex-direction:column;gap:12px">
  <div style="display:flex;align-items:baseline;gap:14px">{linha(cid, 'nm', f'<span style="font-size:38px;font-weight:700;letter-spacing:-.01em">{esc(m.get("canal", "@seucanal"))}</span>')}
   {linha(cid, 'sb', f'<span class="ser" style="font-size:28px;color:#c4b5fd">{esc(m.get("sub", "seu nicho aqui"))}</span>')}</div>
  <div style="display:flex;align-items:center;gap:14px">
   <div id="{cid}-lk" style="position:relative;display:flex;align-items:center;gap:12px;height:62px;padding:0 26px;border-radius:40px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14)">
    <svg viewBox="0 0 24 24" style="width:30px;height:30px;overflow:visible"><path id="{cid}-th" d="{polegar}" style="fill:rgba(167,139,250,0);stroke:#f4f1ff;stroke-width:1.7;stroke-linejoin:round"/></svg>
    <span style="font-size:28px;font-weight:600">{esc(m.get("txt_like", "Gostei"))}</span>{faisca}</div>
   <div id="{cid}-ib" style="position:relative;height:62px;width:250px;border-radius:40px;overflow:hidden">
    <div id="{cid}-i1" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:#f4f1ff;color:#0b0816;font-size:28px;font-weight:700;border-radius:40px">{esc(m.get("txt_inscrever", "Inscrever-se"))}</div>
    <div id="{cid}-i2" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:12px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.16);border-radius:40px;font-size:28px;font-weight:600;opacity:0">
     <svg id="{cid}-bell" viewBox="0 0 24 24" style="width:28px;height:28px;fill:none;stroke:#f4f1ff;stroke-width:1.7;stroke-linejoin:round;transform-origin:50% 10%"><path d="{sino}"/></svg>{esc(m.get("txt_inscrito", "Inscrito"))}</div></div>
  </div></div><div class="glint" id="{cid}-g"></div></div>
<svg id="{cid}-cur" viewBox="0 0 22 32" style="position:absolute;left:0;top:0;width:34px;height:48px;overflow:visible;filter:drop-shadow(0 6px 12px rgba(0,0,0,.6))">
 <path d="M1 1 L1 27 L7.5 20.5 L12.5 31 L17 29 L12 18.5 L21 18.5 Z" fill="#fff" stroke="#0b0816" stroke-width="1.6" stroke-linejoin="round"/></svg>""")
        # posições do cursor (canto do cartão: right 70 / bottom 78; cartão ~ 900 x 166)
        J.append(f'const _c=(id)=>{{const b=document.getElementById(id).getBoundingClientRect();return [b.left+b.width*.45,b.top+b.height*.55]}};'
                 f'const [lkx,lky]=_c("{cid}-lk"),[ibx,iby]=_c("{cid}-ib");')
        lkx, lky, ibx, iby = "lkx", "lky", "ibx", "iby"
        J += [f'tl.fromTo("#{cid}-card",{{opacity:0,y:60,filter:"blur(16px)"}},{{opacity:1,y:0,filter:"blur(0px)",duration:.9,ease:"expo.out"}},.05);',
              gira(cid, 0, .05, dur), sobe(f"#{cid}-nm", .25, .8), sobe(f"#{cid}-sb", .4, .8),
              f'tl.fromTo("#{cid}-g",{{x:-250}},{{x:1100,duration:1.3,ease:"power2.inOut"}},.5);',
              f'tl.fromTo("#{cid}-cur",{{x:1980,y:1150,opacity:1}},{{x:{lkx},y:{lky},duration:{max(.4, tl_ - .55):.2f},ease:"power3.inOut"}},.45);',
              f'tl.to("#{cid}-cur",{{scale:.82,duration:.08,yoyo:true,repeat:1,transformOrigin:"0 0"}},{tl_ - .08:.2f});',
              f'tl.fromTo("#{cid}-lk",{{scale:1}},{{scale:1.1,duration:.14,yoyo:true,repeat:1,ease:"power2.out"}},{tl_:.2f});',
              f'tl.to("#{cid}-lk",{{background:"linear-gradient(90deg,#5b21b6,#7c3aed)",borderColor:"rgba(196,181,253,.6)",duration:.2}},{tl_:.2f});',
              f'tl.to("#{cid}-th",{{fill:"#f4f1ff",duration:.2}},{tl_:.2f});',
              f'tl.fromTo("#{cid}-th",{{rotate:0,transformOrigin:"20% 80%"}},{{rotate:-18,duration:.18,yoyo:true,repeat:1,ease:"power2.out"}},{tl_:.2f});']
        for k in range(8):
            import math
            ang = k * math.pi / 4
            J.append(f'tl.fromTo("#{cid}-f{k}",{{x:0,y:0,opacity:1,scale:1}},{{x:{70 * math.cos(ang):.0f},y:{50 * math.sin(ang):.0f},opacity:0,scale:.3,duration:.6,ease:"expo.out",immediateRender:false}},{tl_:.2f});')
        J += [f'tl.to("#{cid}-cur",{{x:{ibx},y:{iby},duration:{max(.35, ti_ - tl_ - .3):.2f},ease:"power3.inOut"}},{tl_ + .2:.2f});',
              f'tl.to("#{cid}-cur",{{scale:.82,duration:.08,yoyo:true,repeat:1,transformOrigin:"0 0"}},{ti_ - .08:.2f});',
              f'tl.fromTo("#{cid}-ib",{{scale:1}},{{scale:.94,duration:.1,yoyo:true,repeat:1}},{ti_:.2f});',
              f'tl.to("#{cid}-i1",{{opacity:0,duration:.25}},{ti_ + .05:.2f});',
              f'tl.fromTo("#{cid}-i2",{{opacity:0}},{{opacity:1,duration:.25}},{ti_ + .05:.2f});',
              f'tl.fromTo("#{cid}-bell",{{rotate:0}},{{rotate:18,duration:.09,yoyo:true,repeat:7,ease:"sine.inOut"}},{ti_ + .3:.2f});',
              f'tl.to("#{cid}-cur",{{x:1980,y:1150,duration:.6,ease:"power3.in"}},{min(dur - .7, ti_ + .9):.2f});',
              f'tl.to("#{cid}-card",{{opacity:0,y:40,filter:"blur(14px)",duration:.5,ease:"power2.in"}},{dur - .55:.2f});']
    return "\n".join(H), "\n".join(J)


def gerar(m):
    cid = "m" + m["id"].replace("-", "")
    dur = round(m["fim"] - m["ini"], 3)
    pasta = os.path.join(OUT, m["id"])
    os.makedirs(os.path.join(pasta, "fonts"), exist_ok=True)
    for f in ARQ_FONTES:
        d = os.path.join(pasta, "fonts", f)
        if not os.path.exists(d):
            shutil.copy(os.path.join(FONTES, f), d)
    if m["tipo"] == "inscreva":
        shutil.copy(achar_bruto(m["avatar"]), os.path.join(pasta, "avatar.jpg"))
    h, j = corpo(m, cid, dur)
    bg = tem_bg(m["tipo"])
    if m["tipo"] in ("callout", "numero_lado", "lista_lado", "palavra"):  # faixa livre da direita: webcam (rosto à esquerda) ou tela (abaixo do facecam)
        Lx, sc, cy = (1290, .72, 720) if m.get("pos") == "tela" else (1235, .82, 540)
        h = (f'<div style="position:absolute;left:{Lx}px;top:{cy - 540 * sc:.0f}px;width:760px;height:1080px;'
             f'transform:scale({sc});transform-origin:0 0">{h}</div>')
    slide_js, bordas = "", ""
    if m.get("slide"):
        import cenas
        slide_js, bordas = cenas.slide_js(cid, dur, m.get("dir", 1))
    for img in [x.get("img") for x in (m.get("a", {}), m.get("b", {})) if x.get("img")]:
        shutil.copy(achar_bruto(img), os.path.join(pasta, nome_img(img)))
    doc = f"""<!doctype html><html lang="pt"><head><meta charset="UTF-8"><meta name="viewport" content="width=1920, height=1080">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head><body>
<div id="root" data-composition-id="{cid}" data-start="0" data-width="1920" data-height="1080" data-duration="{dur}">
<section id="{cid}-clip" class="full clip" data-start="0" data-duration="{dur}">
{bg_html(cid, random.Random(m["id"])) if bg and not m.get("slide") else ''}
<div id="{cid}-sl" class="full" style="overflow:hidden">
{bg_html(cid, random.Random(m["id"])) if bg and m.get("slide") else ''}
<div id="{cid}-cont" class="full{'' if bg else ' lado-on'}">{h}</div>
{bordas}
</div>
</section></div>
<script>
document.fonts.ready.then(()=>{{
const tl=gsap.timeline({{paused:true}});
{bg_js(cid, dur) if bg else ''}
{j}
{f'tl.to("#{cid}-cont",{{opacity:0,scale:.97,filter:"blur(12px)",duration:.5,ease:"power2.in"}},{dur - .55:.2f});' if bg and not m.get("slide") else ''}
{slide_js}
window.__timelines["{cid}"]=tl;
}});
</script></body></html>"""
    open(os.path.join(pasta, "index.html"), "w", encoding="utf-8").write(paleta(doc, m.get("_cor")))
    return pasta


if __name__ == "__main__":
    plano = json.load(open(sys.argv[1], encoding="utf-8"))
    so = set(sys.argv[2:])
    for m in plano:
        if not so or m["id"] in so:
            print(gerar(m))
