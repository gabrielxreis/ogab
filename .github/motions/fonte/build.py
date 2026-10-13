"""Motions de exemplo do README (1080x1920, fundo opaco, dados fictícios).

Refazer: python3 build.py (cria uma pasta por motion aqui), npx hyperframes render <motion> -o out/<motion>.mp4
para cada um e bash gifs.sh (grava os GIFs em .github/motions/)."""
import glob, os, shutil
from pathlib import Path

AQUI = Path(__file__).parent
FONTES = Path(os.path.expanduser("~/.claude/skills/ogab/assets/fontes/Poppins"))

HEAD = """<!doctype html>
<html lang="pt-BR"><head><meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
@font-face { font-family: "Poppins"; src: url("fonts/Poppins-Medium.ttf"); font-weight: 500; }
@font-face { font-family: "Poppins"; src: url("fonts/Poppins-SemiBold.ttf"); font-weight: 600; }
@font-face { font-family: "Poppins"; src: url("fonts/Poppins-Bold.ttf"); font-weight: 700; }
@font-face { font-family: "Poppins"; src: url("fonts/Poppins-ExtraBold.ttf"); font-weight: 800; }
@font-face { font-family: "Poppins"; src: url("fonts/Poppins-Black.ttf"); font-weight: 900; }
:root { --o1:#ff7a3d; --o2:#ffb36b; --bg1:#0d1117; --bg2:#1b2433; --line:#2a3446; --tx:#f3f5f8; --mut:#8b96a8; }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:var(--bg1); }
#root { position:relative; width:100%; height:100%; font-family:"Poppins",sans-serif; color:var(--tx);
  background: radial-gradient(1200px 900px at 50% 45%, #22304a 0%, var(--bg2) 45%, var(--bg1) 100%); }
.grid { position:absolute; inset:-200px; background-image: linear-gradient(var(--line) 1px, transparent 1px),
  linear-gradient(90deg, var(--line) 1px, transparent 1px); background-size: 90px 90px; opacity:.35; }
.glow { position:absolute; width:900px; height:900px; left:90px; top:510px; border-radius:50%;
  background: radial-gradient(circle, rgba(255,122,61,.22), rgba(255,122,61,0) 65%); }
.tag { position:absolute; display:inline-flex; align-items:center; gap:16px; padding:16px 30px; border-radius:999px;
  background:rgba(13,17,23,.85); border:2px solid var(--line); font-weight:700; font-size:30px; letter-spacing:.1em; }
.tag i { width:16px; height:16px; border-radius:50%; background:var(--o1); display:block; }
.grad { background:linear-gradient(90deg,var(--o1),var(--o2)); -webkit-background-clip:text; background-clip:text; color:transparent; }
.card { position:absolute; background:rgba(22,30,44,.92); border:2px solid #34405a; border-radius:34px;
  box-shadow:0 30px 80px rgba(0,0,0,.45); }
%CSS%
</style></head><body>
<div id="root" data-composition-id="%ID%" data-start="0" data-duration="%DUR%" data-width="1080" data-height="1920" data-fps="30">
<div class="grid" id="%ID%-grid"></div><div class="glow" id="%ID%-glow"></div>
%HTML%
</div>
<script>
const tl = gsap.timeline({ paused: true });
tl.fromTo("#%ID%-grid", { y: 0 }, { y: 90, duration: %DUR%, ease: "none" }, 0);
tl.fromTo("#%ID%-glow", { scale: .85, opacity: .6 }, { scale: 1.1, opacity: 1, duration: %DUR%, ease: "sine.inOut" }, 0);
%JS%
window.__timelines["%ID%"] = tl;
</script></body></html>
"""

MOTIONS = {
"contador": dict(dur=4.2, css="""
#c-tag { left:50%; top:700px; transform:translateX(-50%); }
#c-num { position:absolute; left:0; right:0; top:800px; text-align:center; font-weight:900; font-size:190px; line-height:1; }
#c-suf { position:absolute; left:0; right:0; top:1010px; text-align:center; font-weight:700; font-size:52px; }
#c-bar { position:absolute; left:190px; width:700px; top:1110px; height:18px; border-radius:9px; background:#2a3446; overflow:hidden; }
#c-fill { width:100%; height:100%; background:linear-gradient(90deg,var(--o1),var(--o2)); transform-origin:left center; }
#c-leg { position:absolute; left:0; right:0; top:1160px; text-align:center; font-weight:500; font-size:38px; color:var(--mut); }
""", html="""
<div class="tag" id="c-tag"><i></i>DADO DO VÍDEO</div>
<div id="c-num" class="grad">0</div>
<div id="c-suf">médicos</div>
<div id="c-bar"><div id="c-fill"></div></div>
<div id="c-leg">faltam nos EUA até 2038</div>
""", js="""
tl.fromTo("#c-tag", { opacity:0, y:-30 }, { opacity:1, y:0, duration:.5, ease:"power3.out" }, .1);
const n = { v: 0 };
tl.fromTo("#c-num", { opacity:0, y:60 }, { opacity:1, y:0, duration:.5, ease:"power3.out" }, .25);
tl.to(n, { v: 141000, duration: 1.9, ease: "power2.out",
  onUpdate: () => { document.querySelector("#c-num").textContent = Math.round(n.v).toLocaleString("pt-BR"); } }, .3);
tl.fromTo("#c-fill", { scaleX:0 }, { scaleX:.82, duration:1.9, ease:"power2.out" }, .3);
tl.fromTo("#c-suf", { opacity:0, y:30 }, { opacity:1, y:0, duration:.45, ease:"power3.out" }, .6);
tl.fromTo("#c-leg", { opacity:0, y:30 }, { opacity:1, y:0, duration:.45, ease:"power3.out" }, .85);
tl.fromTo("#c-num", { scale:1 }, { scale:1.06, duration:.25, yoyo:true, repeat:1, ease:"sine.inOut" }, 2.2);
tl.to(["#c-tag","#c-num","#c-suf","#c-bar","#c-leg"], { opacity:0, y:-30, duration:.35, stagger:.04, ease:"power2.in" }, 3.7);
"""),

"lista": dict(dur=4.6, css="""
#l-card { left:110px; width:860px; top:600px; height:720px; }
#l-tit { position:absolute; left:60px; top:56px; font-weight:800; font-size:56px; line-height:1.15; }
.l-it { position:absolute; left:60px; display:flex; align-items:center; gap:28px; font-weight:600; font-size:44px; }
.l-ck { width:74px; height:74px; border-radius:50%; background:linear-gradient(135deg,var(--o1),var(--o2));
  display:flex; align-items:center; justify-content:center; box-shadow:0 10px 30px rgba(255,122,61,.4); }
.l-ck svg { width:40px; height:40px; }
.l-ck path { fill:none; stroke:#0d1117; stroke-width:7; stroke-linecap:round; stroke-linejoin:round; stroke-dasharray:60; stroke-dashoffset:60; }
#l-div { position:absolute; left:60px; top:210px; width:120px; height:6px; border-radius:3px; background:var(--o1); transform-origin:left; }
""", html="""
<div class="card" id="l-card">
  <div id="l-tit">3 passos para<br><span class="grad">tirar do papel</span></div>
  <div id="l-div"></div>
  <div class="l-it" id="l-i1" style="top:270px"><div class="l-ck"><svg viewBox="0 0 40 40"><path d="M8 21 L17 30 L33 11"/></svg></div>Defina o objetivo</div>
  <div class="l-it" id="l-i2" style="top:410px"><div class="l-ck"><svg viewBox="0 0 40 40"><path d="M8 21 L17 30 L33 11"/></svg></div>Monte o plano</div>
  <div class="l-it" id="l-i3" style="top:550px"><div class="l-ck"><svg viewBox="0 0 40 40"><path d="M8 21 L17 30 L33 11"/></svg></div>Comece hoje</div>
</div>
""", js="""
tl.fromTo("#l-card", { opacity:0, y:80, scale:.94 }, { opacity:1, y:0, scale:1, duration:.6, ease:"power3.out" }, .1);
tl.fromTo("#l-tit", { opacity:0, y:30 }, { opacity:1, y:0, duration:.5, ease:"power3.out" }, .35);
tl.fromTo("#l-div", { scaleX:0 }, { scaleX:1, duration:.5, ease:"power2.out" }, .6);
["#l-i1","#l-i2","#l-i3"].forEach((s, k) => {
  const t = .95 + k * .55;
  tl.fromTo(s, { opacity:0, x:-50 }, { opacity:1, x:0, duration:.45, ease:"back.out(1.6)" }, t);
  tl.fromTo(s + " .l-ck", { scale:0, rotation:-90 }, { scale:1, rotation:0, duration:.45, ease:"back.out(2)" }, t);
  tl.to(s + " path", { strokeDashoffset:0, duration:.35, ease:"power2.out" }, t + .2);
});
tl.to("#l-card", { opacity:0, y:-40, duration:.4, ease:"power2.in" }, 4.1);
"""),

"frase": dict(dur=4.0, css="""
#f-box { position:absolute; left:0; right:0; top:760px; text-align:center; white-space:nowrap; }
.f-l { display:block; font-weight:900; font-size:108px; line-height:1.05; letter-spacing:-.01em; }
.f-w { display:inline-block; margin:0 12px; }
#f-sub { position:absolute; left:0; right:0; top:1060px; text-align:center; font-weight:600; font-size:40px; color:var(--mut); letter-spacing:.2em; }
#f-ln { position:absolute; left:440px; top:1025px; width:200px; height:6px; border-radius:3px; background:var(--o1); transform-origin:center; }
""", html="""
<div id="f-box">
  <span class="f-l"><span class="f-w">O</span><span class="f-w">SEGREDO</span></span>
  <span class="f-l"><span class="f-w">É</span><span class="f-w grad">CONSTÂNCIA</span></span>
</div>
<div id="f-ln"></div>
<div id="f-sub">LETTERING ANIMADO</div>
""", js="""
tl.fromTo(".f-w", { opacity:0, y:70, filter:"blur(14px)" }, { opacity:1, y:0, filter:"blur(0px)", duration:.5, stagger:.22, ease:"power3.out" }, .15);
tl.fromTo("#f-ln", { scaleX:0 }, { scaleX:1, duration:.5, ease:"power2.out" }, 1.15);
tl.fromTo("#f-sub", { opacity:0 }, { opacity:1, duration:.5 }, 1.3);
tl.fromTo(".f-w.grad", { scale:1 }, { scale:1.08, duration:.3, yoyo:true, repeat:1, ease:"sine.inOut" }, 1.6);
tl.to([".f-w","#f-ln","#f-sub"], { opacity:0, y:-40, filter:"blur(10px)", duration:.4, stagger:.03, ease:"power2.in" }, 3.4);
"""),

"grafico": dict(dur=4.4, css="""
#g-card { left:110px; width:860px; top:560px; height:800px; }
#g-tit { position:absolute; left:60px; top:52px; font-weight:800; font-size:50px; }
#g-sub { position:absolute; left:60px; top:120px; font-weight:500; font-size:32px; color:var(--mut); }
.g-col { position:absolute; bottom:120px; width:120px; border-radius:18px 18px 6px 6px; background:#34405a; transform-origin:bottom; }
.g-col.hi { background:linear-gradient(180deg,var(--o2),var(--o1)); box-shadow:0 0 40px rgba(255,122,61,.45); }
.g-lb { position:absolute; bottom:60px; width:120px; text-align:center; font-weight:600; font-size:30px; color:var(--mut); }
#g-pill { position:absolute; right:60px; top:60px; padding:12px 26px; border-radius:999px; background:rgba(255,122,61,.15);
  color:var(--o2); font-weight:800; font-size:38px; border:2px solid rgba(255,122,61,.5); }
""", html="""
<div class="card" id="g-card">
  <div id="g-tit">Alcance mensal</div>
  <div id="g-sub">depois dos Reels editados</div>
  <div id="g-pill">+212%</div>
  <div class="g-col" id="g-c1" style="left:90px;height:150px"></div><div class="g-lb" style="left:90px">JAN</div>
  <div class="g-col" id="g-c2" style="left:280px;height:230px"></div><div class="g-lb" style="left:280px">FEV</div>
  <div class="g-col" id="g-c3" style="left:470px;height:330px"></div><div class="g-lb" style="left:470px">MAR</div>
  <div class="g-col hi" id="g-c4" style="left:660px;height:470px"></div><div class="g-lb" style="left:660px;color:var(--o2)">ABR</div>
</div>
""", js="""
tl.fromTo("#g-card", { opacity:0, y:80, scale:.94 }, { opacity:1, y:0, scale:1, duration:.6, ease:"power3.out" }, .1);
tl.fromTo(["#g-tit","#g-sub"], { opacity:0, y:24 }, { opacity:1, y:0, duration:.45, stagger:.1, ease:"power3.out" }, .35);
tl.fromTo(".g-col", { scaleY:0 }, { scaleY:1, duration:.7, stagger:.18, ease:"back.out(1.3)" }, .7);
tl.fromTo(".g-lb", { opacity:0 }, { opacity:1, duration:.3, stagger:.18 }, .8);
tl.fromTo("#g-pill", { opacity:0, scale:.6 }, { opacity:1, scale:1, duration:.45, ease:"back.out(2.2)" }, 1.75);
tl.to("#g-pill", { scale:1.08, duration:.25, yoyo:true, repeat:1, ease:"sine.inOut" }, 2.3);
tl.to("#g-card", { opacity:0, y:-40, duration:.4, ease:"power2.in" }, 3.9);
"""),

"cta": dict(dur=4.2, css="""
#k-logo { position:absolute; left:440px; top:600px; width:200px; height:200px; border-radius:48px;
  background:linear-gradient(135deg,var(--o1),var(--o2)); display:flex; align-items:center; justify-content:center;
  box-shadow:0 30px 80px rgba(255,122,61,.45); font-weight:900; font-size:96px; color:#0d1117; }
#k-tit { position:absolute; left:0; right:0; top:860px; text-align:center; font-weight:900; font-size:96px; line-height:1.05; }
#k-btn { position:absolute; left:240px; width:600px; top:1110px; height:120px; border-radius:999px; background:var(--tx); color:#0d1117;
  display:flex; align-items:center; justify-content:center; gap:20px; font-weight:800; font-size:44px; }
#k-btn svg { width:44px; height:44px; }
#k-site { position:absolute; left:0; right:0; top:1270px; text-align:center; font-weight:600; font-size:34px; color:var(--mut); letter-spacing:.06em; }
#k-ring { position:absolute; left:440px; top:600px; width:200px; height:200px; border-radius:48px; border:4px solid var(--o1); }
""", html="""
<div id="k-ring"></div>
<div id="k-logo">G</div>
<div id="k-tit">Quer o seu<br><span class="grad">vídeo assim?</span></div>
<div id="k-btn">Link na bio <svg viewBox="0 0 44 44"><path d="M10 22 H32 M24 13 L33 22 L24 31" fill="none" stroke="#0d1117" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
<div id="k-site">seusite.com.br</div>
""", js="""
tl.fromTo("#k-logo", { opacity:0, scale:.3, rotation:-25 }, { opacity:1, scale:1, rotation:0, duration:.7, ease:"back.out(1.8)" }, .1);
tl.fromTo("#k-ring", { opacity:.9, scale:1 }, { opacity:0, scale:1.8, duration:1.1, ease:"power2.out" }, .55);
tl.fromTo("#k-tit", { opacity:0, y:50 }, { opacity:1, y:0, duration:.55, ease:"power3.out" }, .55);
tl.fromTo("#k-btn", { opacity:0, y:40, scale:.85 }, { opacity:1, y:0, scale:1, duration:.5, ease:"back.out(2)" }, .95);
tl.fromTo("#k-site", { opacity:0 }, { opacity:1, duration:.4 }, 1.25);
tl.to("#k-btn", { scale:1.06, duration:.3, yoyo:true, repeat:3, ease:"sine.inOut" }, 1.7);
tl.to("#k-btn svg", { x:10, duration:.3, yoyo:true, repeat:3, ease:"sine.inOut" }, 1.7);
tl.to(["#k-logo","#k-tit","#k-btn","#k-site"], { opacity:0, y:-30, duration:.35, stagger:.04, ease:"power2.in" }, 3.7);
"""),
}

for nome, m in MOTIONS.items():
    d = AQUI / nome
    (d / "fonts").mkdir(parents=True, exist_ok=True)
    for f in glob.glob(str(FONTES / "**" / "Poppins-*.ttf"), recursive=True):
        shutil.copy(f, d / "fonts")
    html = (HEAD.replace("%CSS%", m["css"]).replace("%HTML%", m["html"]).replace("%JS%", m["js"])
            .replace("%ID%", nome).replace("%DUR%", str(m["dur"])))
    (d / "index.html").write_text(html)
    (d / "hyperframes.json").write_text('{"paths":{"blocks":"compositions","components":"compositions/components","assets":"assets"}}')
    print("ok", nome)
