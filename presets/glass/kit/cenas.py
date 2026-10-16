"""Preset GLASS: cenas de abertura que entram e saem com slide (empurrão de câmera junto com a V1 no DaVinci).

  Usado pelo gerar.py do preset (tipos print_destaque, dois_problemas, montagem, chip, blocos, foto_lado).
Tempos absolutos da timeline cortada. Cenas com BG deslizam inteiras (BG junto), por isso saem em MOV com alfa.
"""
import json, os, random, shutil
import base as G
from base import ic, medalha, linha, esc, sobe, desenha, gira

AQUI = os.path.dirname(os.path.abspath(__file__))
SL = 0.4  # duração do slide (igual ao da câmera, camera.py)


def W(t):
    """Primeira ocorrência da palavra a partir de t (tempo da transcrição da timeline cortada)."""
    return t


CENAS = []   # o plano vem do gerar.py do preset





def foto(cid, k, arq, larg, anel=None, cor="#f87171"):
    """Print/foto do usuário em moldura de vidro; anel = (x0, y0, x1, y1) em fração da imagem, desenhado depois."""
    svg = ""
    if anel:
        x0, y0, x1, y1 = anel
        svg = (f'<svg viewBox="0 0 100 100" preserveAspectRatio="none" style="position:absolute;left:{x0 * 100:.1f}%;top:{y0 * 100:.1f}%;'
               f'width:{(x1 - x0) * 100:.1f}%;height:{(y1 - y0) * 100:.1f}%;overflow:visible;filter:drop-shadow(0 0 10px {cor})">'
               f'<ellipse id="{cid}-an{k}e" cx="50" cy="50" rx="52" ry="52" pathLength="1" style="fill:none;stroke:{cor};stroke-width:1.3;'
               f'stroke-dasharray:1;stroke-dashoffset:1"/></svg>')
    return (f'<div id="{cid}-f{k}" class="vidro" style="padding:14px;border-radius:26px;width:{larg}px">'
            f'<div style="position:relative"><img src="{arq}" style="display:block;width:100%;border-radius:14px">{svg}</div>'
            f'<div class="glint" id="{cid}-g{k}"></div></div>')


def caixa_css(m):
    """Caixa vermelha piscando sobre um ponto do print: m["caixa"] = (x0, y0, x1, y1) em fração da imagem (card de 980 px)."""
    x0, y0, x1, y1 = m.get("caixa", (0, 0, 0, 0))
    w = 952; h = w * m.get("proporcao", 445 / 833); top = (640 - h - 28) / 2 + 14
    return f"left:{14 + x0 * w - 8:.0f}px;top:{top + y0 * h - 8:.0f}px;width:{(x1 - x0) * w + 16:.0f}px;height:{(y1 - y0) * h + 16:.0f}px"


def anel(cid, k, t, d=.6):
    return f'tl.fromTo("#{cid}-an{k}e",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:{d},ease:"power2.inOut"}},{t:.2f});'


def cena_funil(m, cid, dur):
    L = lambda t: G.L(m, t)
    H = [f"""<div class="full" style="display:flex;align-items:center;justify-content:center;gap:80px">
 <div style="position:relative;width:980px;height:640px">
  <div style="position:absolute;left:0;top:50%;transform:translateY(-50%)">{foto(cid, 0, G.nome_img(m["img"]), 980, tuple(m.get("anel", (.45, .32, .66, 1.0))))}</div>
  {f'<div id="{cid}-ag" style="position:absolute;left:190px;top:0">{foto(cid, 1, G.nome_img(m["img2"]), 600)}</div>' if m.get("img2") else f'<div id="{cid}-ag"></div>'}
  <div id="{cid}-lu" style="position:absolute;{caixa_css(m)};border-radius:12px;border:3px solid #f87171;box-shadow:0 0 30px rgba(248,113,113,.7);opacity:0"></div>
 </div>
 <div style="width:620px;display:flex;flex-direction:column;gap:20px">
  <div id="{cid}-eb" class="eyebrow">{esc(m.get("rotulo", "o seu funil"))}</div>
  {linha(cid, 't1', f'<span class="met">{esc(m.get("titulo", "Initiate Checkout"))}</span>', 'font-size:70px;font-weight:700;letter-spacing:-.02em;line-height:1.05')}
  {linha(cid, 't2', f'<span class="ser" style="color:#fca5a5;font-size:150px">{esc(m.get("destaque", "0%"))}</span>', 'line-height:1')}
  {linha(cid, 'tt', f'<span class="met">{esc(m.get("frase", "o famoso "))}</span><span class="ser met">{esc(m.get("frase_serif", "funil agulha"))}</span>', 'font-size:80px;font-weight:700;letter-spacing:-.02em;line-height:1.05')}
 </div></div>"""]
    ta = L(m["t_agulha"]) - .7   # a agulha entra no "o famoso"
    J = [f'tl.fromTo("#{cid}-eb",{{opacity:0}},{{opacity:1,duration:.5}},{SL:.2f});',
         f'tl.fromTo("#{cid}-f0",{{opacity:0,scale:.92,rotateY:-14,filter:"blur(12px)"}},{{opacity:1,scale:1,rotateY:0,filter:"blur(0px)",duration:.9,ease:"expo.out"}},{max(SL, L(m["t_conv"]) - .4):.2f});',
         f'tl.fromTo("#{cid}-g0",{{x:-300}},{{x:1300,duration:1.2,ease:"power2.inOut"}},{L(m["t_conv"]):.2f});',
         sobe(f"#{cid}-t1", L(m["t_ic"]) - .1, .7), anel(cid, 0, L(m["t_ic"]) + .1, .7),
         sobe(f"#{cid}-t2", L(m["t_assim"]) - .1, .7),
         f'tl.fromTo("#{cid}-lu",{{opacity:0,scale:1.4}},{{opacity:1,scale:1,duration:.45,ease:"back.out(2)"}},{L(m["t_assim"]) + .15:.2f});',
         f'tl.fromTo("#{cid}-lu",{{opacity:1}},{{opacity:.35,duration:.12,yoyo:true,repeat:3,immediateRender:false}},{L(m["t_assim"]) + .6:.2f});',
         # vira a agulha: o print recua e escurece, a foto da agulha cai por cima
         f'tl.to("#{cid}-f0,#{cid}-lu",{{scale:.9,opacity:.25,filter:"blur(6px)",duration:.6,ease:"power2.inOut"}},{ta:.2f});',
         f'tl.to("#{cid}-t1,#{cid}-t2",{{opacity:0,y:-20,duration:.35,ease:"power2.in"}},{ta:.2f});',
         f'tl.fromTo("#{cid}-ag",{{opacity:0,y:-120,rotate:-6,scale:1.1}},{{opacity:1,y:0,rotate:-2,scale:1,duration:.7,ease:"back.out(1.6)"}},{ta + .05:.2f});',
         sobe(f"#{cid}-tt", ta + .3, .8)]
    return "\n".join(H), "\n".join(J)


def mock(cid, k, alto, linhas, botao_y):
    ls = "".join(f'<div style="height:14px;border-radius:7px;background:rgba(221,214,254,{.10 + (i % 3) * .05});width:{60 + (i * 37) % 38}%;margin:0 0 16px"></div>' for i in range(linhas))
    return f"""<div class="vidro" style="width:620px;height:{alto}px;padding:0;overflow:hidden">
 <div style="height:44px;display:flex;align-items:center;gap:10px;padding:0 20px;border-bottom:1px solid rgba(255,255,255,.08)">
  <i style="width:12px;height:12px;border-radius:50%;background:#f87171"></i><i style="width:12px;height:12px;border-radius:50%;background:#fbbf24"></i><i style="width:12px;height:12px;border-radius:50%;background:#6ee7b7"></i>
  <div style="flex:1;height:20px;margin-left:16px;border-radius:10px;background:rgba(255,255,255,.07)"></div></div>
 <div style="position:relative;height:{alto - 44}px;overflow:hidden">
  <div id="{cid}-sc{k}" style="padding:30px 40px">
   <div style="height:34px;width:80%;border-radius:10px;background:rgba(244,241,255,.75);margin-bottom:26px"></div>{ls}
   <div style="margin-top:{botao_y}px;height:64px;width:260px;border-radius:40px;background:linear-gradient(90deg,#059669,#34d399);display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:700;color:#03140d">Comprar</div>
  </div>
  <div id="{cid}-sb{k}" style="position:absolute;right:8px;top:10px;width:6px;height:{max(30, (alto - 44) * 60 // (linhas * 30 + 400))}px;border-radius:3px;background:rgba(221,214,254,.5)"></div>
 </div></div>"""


def cena_paginas(m, cid, dur):
    L = lambda t: G.L(m, t)
    X = lambda k, txt: (f'<div id="{cid}-x{k}" style="position:absolute;right:-30px;top:-30px;width:96px;height:96px;border-radius:50%;'
                        f'background:#1a0b0b;border:2px solid #f87171;padding:22px;box-sizing:border-box;box-shadow:0 0 40px rgba(248,113,113,.5)">{ic("x", "#fca5a5")}</div>')
    H = [f"""<div id="{cid}-s1" class="full" style="display:flex;align-items:center;justify-content:center;gap:90px">
  <div style="position:relative">{mock(cid, 1, 760, 80, 900)}{X(1, '')}
   <svg id="{cid}-cur" viewBox="0 0 22 32" style="position:absolute;left:300px;top:520px;width:34px;height:48px;overflow:visible"><path d="M1 1 L1 27 L7.5 20.5 L12.5 31 L17 29 L12 18.5 L21 18.5 Z" fill="#fff" stroke="#0b0816" stroke-width="1.6"/></svg></div>
  <div style="width:560px;display:flex;flex-direction:column;gap:18px">
   <div class="eyebrow" id="{cid}-e1">{esc(m.get("rotulo1", "problema 01"))}</div>
   {linha(cid, 't1', f'<span class="met">{esc(m.get("titulo1", "Página "))}</span><span class="ser met">{esc(m.get("serif1", "longa demais"))}</span>', 'font-size:84px;font-weight:700;line-height:1.02;letter-spacing:-.02em')}
   {linha(cid, 'd1', f'<span style="color:#fca5a5">{esc(m.get("sub1", "desistiu antes do botão"))}</span>', 'font-size:40px;font-weight:500')}</div></div>
 <div id="{cid}-s2" class="full" style="display:flex;align-items:center;justify-content:center;gap:90px">
  <div style="position:relative">{mock(cid, 2, 300, 1, 10)}{X(2, '')}
   {''.join(f'<div id="{cid}-q{k}" class="ser met" style="position:absolute;font-size:{90 - k * 12}px;left:{[-70, 560, 250][k]}px;top:{[-90, 20, 250][k]}px">?</div>' for k in range(3))}</div>
  <div style="width:560px;display:flex;flex-direction:column;gap:18px">
   <div class="eyebrow" id="{cid}-e2">{esc(m.get("rotulo2", "problema 02"))}</div>
   {linha(cid, 't2', f'<span class="met">{esc(m.get("titulo2", "Página "))}</span><span class="ser met">{esc(m.get("serif2", "curta demais"))}</span>', 'font-size:84px;font-weight:700;line-height:1.02;letter-spacing:-.02em')}
   {linha(cid, 'd2', f'<span style="color:#fca5a5">{esc(m.get("sub2", "não entendeu o produto"))}</span>', 'font-size:40px;font-weight:500')}</div></div>"""]
    tr = L(m["t_troca"])
    J = [f'tl.fromTo("#{cid}-e1",{{opacity:0}},{{opacity:1,duration:.5}},{SL:.2f});', sobe(f"#{cid}-t1", L(m["t_longa"]) - .35, .8),
         f'tl.fromTo("#{cid}-sc1",{{y:0}},{{y:-900,duration:{tr - SL:.2f},ease:"none"}},{SL:.2f});',  # rola sem parar
         f'tl.fromTo("#{cid}-sb1",{{y:0}},{{y:600,duration:{tr - SL:.2f},ease:"none"}},{SL:.2f});',
         f'tl.fromTo("#{cid}-cur",{{y:0,x:0}},{{y:110,x:40,duration:{max(.5, L(m["t_desist1"]) - SL):.2f},ease:"sine.inOut"}},{SL:.2f});',
         f'tl.fromTo("#{cid}-x1",{{scale:0,rotate:-90}},{{scale:1,rotate:0,duration:.6,ease:"back.out(2.4)"}},{L(m["t_desist1"]):.2f});',
         sobe(f"#{cid}-d1", L(m["t_desist1"]) + .1, .7), desenha(f"#{cid}-x1", L(m["t_desist1"]) + .25, .5),
         f'tl.to("#{cid}-cur",{{opacity:0,x:-200,duration:.5,ease:"power2.in"}},{L(m["t_desist1"]) + .3:.2f});',
         # troca: cena 1 sai pela esquerda, cena 2 entra pela direita (empurrão)
         f'tl.fromTo("#{cid}-s1",{{x:0}},{{x:-1920,duration:{SL + .05:.2f},ease:"power3.inOut"}},{tr:.2f});',
         f'tl.fromTo("#{cid}-s2",{{x:1920}},{{x:0,duration:{SL + .05:.2f},ease:"power3.inOut"}},{tr:.2f});',
         f'tl.fromTo("#{cid}-e2",{{opacity:0}},{{opacity:1,duration:.5}},{tr + .3:.2f});', sobe(f"#{cid}-t2", L(m["t_curta"]) - .35, .8)]
    for k in range(3):
        J.append(f'tl.fromTo("#{cid}-q{k}",{{scale:0,opacity:0,rotate:-20}},{{scale:1,opacity:1,rotate:0,duration:.5,ease:"back.out(3)"}},{L(m["t_entender"]) + k * .18:.2f});')
        J.append(f'tl.to("#{cid}-q{k}",{{y:-12,duration:.9,yoyo:true,repeat:3,ease:"sine.inOut"}},{L(m["t_entender"]) + .5 + k * .18:.2f});')
    J += [f'tl.fromTo("#{cid}-x2",{{scale:0,rotate:-90}},{{scale:1,rotate:0,duration:.6,ease:"back.out(2.4)"}},{L(m["t_desist2"]):.2f});',
          sobe(f"#{cid}-d2", L(m["t_desist2"]) + .1, .7), desenha(f"#{cid}-x2", L(m["t_desist2"]) + .25, .5)]
    return "\n".join(H), "\n".join(J)


def cena_estrutura(m, cid, dur):
    L = lambda t: G.L(m, t)
    blocos = "".join(f'<div id="{cid}-k{k}" style="height:{[120, 64, 64, 64, 96, 50, 64][k]}px;border-radius:14px;margin-bottom:12px;'
                     f'background:linear-gradient(90deg,rgba(124,58,237,{.55 - k * .05}),rgba(76,29,149,{.35 - k * .03}));border:1px solid rgba(196,181,253,.3)"></div>' for k in range(7))
    H = [f"""<div class="full" style="display:flex;align-items:center;justify-content:center;gap:110px">
 <div class="vidro" style="width:520px;padding:30px">{blocos}</div>
 <div style="display:flex;flex-direction:column;gap:26px;width:640px">
  <div class="eyebrow" id="{cid}-eb">{esc(m.get("rotulo", "o que eu uso"))}</div>
  {linha(cid, 'tt', f'<span class="met">{esc(m.get("titulo", "A "))}</span><span class="ser met">{esc(m.get("titulo_serif", "estrutura"))}</span>', 'font-size:96px;font-weight:700;letter-spacing:-.02em')}
  <div id="{cid}-lt" style="align-self:flex-start;padding:14px 30px;border-radius:40px;border:1px solid rgba(196,181,253,.5);background:rgba(124,58,237,.25);font-size:34px;font-weight:600">{esc(m.get("pilula", "low ticket"))}</div>
  <div id="{cid}-fn">{foto(cid, 0, G.nome_img(m["img"]), 600, tuple(m.get("anel", (.40, .20, .60, .93))), "#6ee7b7") if m.get("img") else ""}</div></div></div>"""]
    J = [f'tl.fromTo("#{cid}-eb",{{opacity:0}},{{opacity:1,duration:.5}},{SL:.2f});', sobe(f"#{cid}-tt", L(m["t_estr"]) - .3, .8)]
    for k in range(7):
        J.append(f'tl.fromTo("#{cid}-k{k}",{{opacity:0,x:-60,scaleX:.6}},{{opacity:1,x:0,scaleX:1,duration:.45,ease:"expo.out"}},{L(m["t_estr"]) + k * .2:.2f});')
    J += [f'tl.fromTo("#{cid}-lt",{{opacity:0,scale:.6}},{{opacity:1,scale:1,duration:.5,ease:"back.out(2.5)"}},{L(m["t_lt"]):.2f});',
          f'tl.fromTo("#{cid}-fn",{{opacity:0,y:40,scale:.94,filter:"blur(12px)"}},{{opacity:1,y:0,scale:1,filter:"blur(0px)",duration:.8,ease:"expo.out"}},{L(m["t_ic"]) - .25:.2f});',
          f'tl.fromTo("#{cid}-g0",{{x:-300}},{{x:900,duration:1.1,ease:"power2.inOut"}},{L(m["t_ic"]) + .1:.2f});',
          anel(cid, 0, L(m["t_ic"]) + .15, .55)]
    return "\n".join(H), "\n".join(J)


def cena_chip(m, cid, dur):
    L = lambda t: G.L(m, t)
    H, J = ['<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px">'], []
    for k, x in enumerate(m["itens"]):
        cor = "#fca5a5" if x.get("ruim") else "#6ee7b7"
        H.append(f"""<div id="{cid}-c{k}" class="vidro" style="display:flex;align-items:center;gap:24px;padding:22px 34px 22px 22px;border-radius:80px;width:600px">
 {medalha(cid, k, x["icone"], 92, cor if x["icone"] in ("x", "check") else None)}
 <div><div style="font-size:44px;font-weight:700;{'text-decoration:line-through;text-decoration-color:#f87171;color:#c9c2e6' if x.get('ruim') else ''}">{esc(x['txt'])}</div>
 {f'<div class="ser" style="font-size:32px;color:#c4b5fd">{esc(x["sub"])}</div>' if x.get('sub') else ''}</div></div>""")
        lt = L(x["t"])
        J += [f'tl.fromTo("#{cid}-c{k}",{{opacity:0,x:80,filter:"blur(12px)"}},{{opacity:1,x:0,filter:"blur(0px)",duration:.55,ease:"expo.out"}},{lt:.2f});',
              desenha(f"#{cid}-c{k}", lt + .15, .5), gira(cid, k, lt, dur)]
    H.append("</div>")
    J.append(f'tl.to("#{cid}-cont .vidro",{{opacity:0,x:60,filter:"blur(10px)",duration:.3,stagger:.05,ease:"power2.in"}},{dur - .4:.2f});')
    return "\n".join(H), "\n".join(J)


def cena_blocos(m, cid, dur):
    L = lambda t: G.L(m, t)
    H = [f"""<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:24px">
 <div class="eyebrow" id="{cid}-eb" style="font-size:20px"><i></i>{esc(m.get("rotulo", "bloco por bloco"))}<i></i></div>
 <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:16px;width:620px">
 {''.join(f'<div id="{cid}-n{k}" class="vidro" style="width:130px;height:130px;border-radius:50%;display:flex;align-items:center;justify-content:center"><span class="ser met" style="font-size:62px">{k + 1:02d}</span></div>' for k in range(7))}
 </div></div>"""]
    J = [f'tl.fromTo("#{cid}-eb",{{opacity:0,y:10}},{{opacity:1,y:0,duration:.5}},{L(m["t"]) - .1:.2f});']
    for k in range(7):
        J.append(f'tl.fromTo("#{cid}-n{k}",{{opacity:0,scale:.3,y:30}},{{opacity:1,scale:1,y:0,duration:.45,ease:"back.out(2.6)"}},{L(m["t"]) + k * .2:.2f});')
    J.append(f'tl.to("#{cid}-n0,#{cid}-n1,#{cid}-n2,#{cid}-n3,#{cid}-n4,#{cid}-n5,#{cid}-n6,#{cid}-eb",{{opacity:0,scale:.8,filter:"blur(8px)",duration:.3,stagger:.03,ease:"power2.in"}},{dur - .45:.2f});')
    return "\n".join(H), "\n".join(J)


def cena_foto_lado(m, cid, dur):
    L = lambda t: G.L(m, t)
    H = [f"""<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px">
 <div class="eyebrow" id="{cid}-eb" style="font-size:20px"><i></i>{esc(m.get("rotulo", "lembra dele?"))}<i></i></div>
 {foto(cid, 0, G.nome_img(m["img"]), 700, tuple(m["anel"]) if m.get("anel") else None, m.get("cor_anel", "#6ee7b7"))}</div>"""]
    J = [f'tl.fromTo("#{cid}-f0",{{opacity:0,x:80,filter:"blur(14px)"}},{{opacity:1,x:0,filter:"blur(0px)",duration:.8,ease:"expo.out"}},{L(m["t"]) - .1:.2f});',
         f'tl.fromTo("#{cid}-eb",{{opacity:0,y:10}},{{opacity:1,y:0,duration:.5}},{L(m["t"]):.2f});',
         f'tl.fromTo("#{cid}-g0",{{x:-300}},{{x:1000,duration:1.1,ease:"power2.inOut"}},{L(m["t"]) + .3:.2f});',
         anel(cid, 0, L(m["t_anel"]), .55),
         f'tl.to("#{cid}-f0,#{cid}-eb",{{opacity:0,x:50,filter:"blur(12px)",duration:.45,ease:"power2.in"}},{dur - .5:.2f});']
    return "\n".join(H), "\n".join(J)


FUNCS = {"print_destaque": cena_funil, "funil": cena_funil, "montagem": cena_estrutura, "dois_problemas": cena_paginas, "foto_lado": cena_foto_lado, "paginas": cena_paginas, "estrutura": cena_estrutura, "chip": cena_chip, "blocos": cena_blocos}
COM_BG = ("funil", "paginas", "estrutura", "print_destaque", "montagem", "dois_problemas")


def slide_js(cid, dur, d=1):
    """Empurrão de câmera: a cena entra por um lado (d=1: pela direita) e sai pelo outro, com escala, desfoque,
    filete de luz nas bordas enquanto desliza, brilho atravessando e acomodação ao pousar. Mesmo ease do camera.py."""
    bordas = (f'<div id="{cid}-bd" class="full" style="pointer-events:none">'
              f'<i style="position:absolute;left:0;top:0;bottom:0;width:3px;background:linear-gradient(180deg,transparent,#ddd6fe 30%,#a78bfa 70%,transparent);box-shadow:0 0 40px 10px rgba(167,139,250,.65)"></i>'
              f'<i style="position:absolute;right:0;top:0;bottom:0;width:3px;background:linear-gradient(180deg,transparent,#ddd6fe 30%,#a78bfa 70%,transparent);box-shadow:0 0 40px 10px rgba(167,139,250,.65)"></i>'
              f'<i id="{cid}-fl" style="position:absolute;top:-20%;bottom:-20%;width:420px;left:-500px;transform:skewX(-16deg);background:linear-gradient(90deg,transparent,rgba(237,233,254,.22),transparent)"></i></div>')
    js = (f'tl.fromTo("#{cid}-sl",{{x:{d * 1920},scale:1.05,filter:"blur(22px)"}},{{x:0,scale:1,filter:"blur(0px)",duration:{SL},ease:"power3.inOut"}},0);'
          f'tl.fromTo("#{cid}-cont",{{scale:1.035}},{{scale:1,duration:.9,ease:"expo.out"}},{SL * .85:.3f});'
          f'tl.fromTo("#{cid}-bd i:not(#{cid}-fl)",{{opacity:1}},{{opacity:0,duration:.3,ease:"power2.out"}},{SL - .05:.3f});'
          f'tl.fromTo("#{cid}-fl",{{x:{0 if d > 0 else 2600}}},{{x:{2600 if d > 0 else 0},duration:{SL + .25:.2f},ease:"power2.out"}},.05);'
          f'tl.fromTo("#{cid}-bd i:not(#{cid}-fl)",{{opacity:0}},{{opacity:1,duration:.12}},{dur - SL:.3f});'
          f'tl.to("#{cid}-sl",{{x:{-d * 1920},scale:1.05,filter:"blur(22px)",duration:{SL},ease:"power3.inOut"}},{dur - SL:.3f});')
    return js, bordas


def montar(m):
    cid = "m" + m["id"].replace("-", "")
    dur = round(m["fim"] - m["ini"], 3)
    pasta = os.path.join(G.OUT, m["id"])
    os.makedirs(os.path.join(pasta, "fonts"), exist_ok=True)
    for f in G.ARQ_FONTES:
        if not os.path.exists(os.path.join(pasta, "fonts", f)):
            shutil.copy(os.path.join(G.FONTES, f), os.path.join(pasta, "fonts", f))
    for chave in ("img", "img2"):
        if m.get(chave):
            shutil.copy(G.achar_bruto(m[chave]), os.path.join(pasta, G.nome_img(m[chave])))
    h, j = FUNCS[m["tipo"]](m, cid, dur)
    bg = m["tipo"] in COM_BG
    if not bg:  # faixa livre da direita, longe do rosto
        lx, sc = m.get("pos", (1235, .82))
        h = (f'<div style="position:absolute;left:{lx}px;top:{540 - 540 * sc:.0f}px;width:760px;height:1080px;'
             f'transform:scale({sc});transform-origin:0 0">{h}</div>')
    slide, bordas = "", ""
    if bg:
        slide, bordas = slide_js(cid, dur, m.get("dir", 1))
    doc = f"""<!doctype html><html lang="pt"><head><meta charset="UTF-8"><meta name="viewport" content="width=1920, height=1080">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{G.CSS}</style></head><body>
<div id="root" data-composition-id="{cid}" data-start="0" data-width="1920" data-height="1080" data-duration="{dur}">
<section id="{cid}-clip" class="full clip" data-start="0" data-duration="{dur}">
<div id="{cid}-sl" class="full" style="overflow:hidden">
{G.bg_html(cid, random.Random(m["id"])) if bg else ''}
<div id="{cid}-cont" class="full{'' if bg else ' lado-on'}">{h}</div>
{bordas}
</div></section></div>
<script>
document.fonts.ready.then(()=>{{
const tl=gsap.timeline({{paused:true}});
{G.bg_js(cid, dur) if bg else ''}
{j}
{slide}
window.__timelines["{cid}"]=tl;
}});
</script></body></html>"""
    open(os.path.join(pasta, "index.html"), "w", encoding="utf-8").write(G.paleta(doc, m.get("_cor")))
    return pasta


