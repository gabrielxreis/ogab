"""Motions de exemplo do README (1080x1920, fundo opaco, dados fictícios).

Refazer: python3 build.py (cria uma pasta por motion aqui), npx hyperframes render <motion> -o out/<motion>.mp4
para cada um e bash gifs.sh (grava os GIFs em .github/motions/)."""
import glob, os, random, shutil
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
:root { --o1:#ff6a2b; --o2:#ffb36b; --v1:#7c5cff; --bg:#070a12; --tx:#f5f7fb; --mut:#9aa6bb; }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:var(--bg); }
#root { position:relative; width:100%; height:100%; font-family:"Poppins",sans-serif; color:var(--tx); overflow:hidden; background:var(--bg); }
.aur { position:absolute; border-radius:50%; filter:blur(120px); opacity:.55; }
#a1 { width:900px; height:900px; left:-250px; top:300px; background:radial-gradient(circle,#ff6a2b,transparent 65%); }
#a2 { width:1000px; height:1000px; left:420px; top:900px; background:radial-gradient(circle,#6d4cff,transparent 65%); opacity:.45; }
#a3 { width:700px; height:700px; left:300px; top:-150px; background:radial-gradient(circle,#ff2f7a,transparent 65%); opacity:.25; }
.grid { position:absolute; inset:-300px; background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),
  linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px); background-size:72px 72px;
  -webkit-mask-image:radial-gradient(circle at 50% 50%,#000 20%,transparent 70%); }
.vig { position:absolute; inset:0; background:radial-gradient(ellipse at 50% 50%,transparent 45%,rgba(0,0,0,.65) 100%); }
.pt { position:absolute; border-radius:50%; background:#fff; }
.stage { position:absolute; inset:0; perspective:1800px; }
.glass { position:absolute; border-radius:40px; background:linear-gradient(160deg,rgba(255,255,255,.10),rgba(255,255,255,.03));
  border:1.5px solid rgba(255,255,255,.16); box-shadow:0 40px 120px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.25);
  backdrop-filter:blur(24px); overflow:hidden; transform-style:preserve-3d; }
.sweep { position:absolute; top:-50%; left:-60%; width:40%; height:200%; transform:rotate(18deg);
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.22),transparent); }
.grad { background:linear-gradient(100deg,var(--o1),var(--o2) 55%,#ffd9a8); -webkit-background-clip:text; background-clip:text; color:transparent; }
.chip { position:absolute; display:inline-flex; align-items:center; gap:14px; padding:14px 28px; border-radius:999px;
  background:rgba(255,255,255,.07); border:1.5px solid rgba(255,255,255,.18); font-weight:700; font-size:28px; letter-spacing:.14em; }
.chip i { width:14px; height:14px; border-radius:50%; background:var(--o1); box-shadow:0 0 18px var(--o1); display:block; }
%CSS%
</style></head><body>
<div id="root" data-composition-id="%ID%" data-start="0" data-duration="%DUR%" data-width="1080" data-height="1920" data-fps="30">
<div class="aur" id="a1"></div><div class="aur" id="a2"></div><div class="aur" id="a3"></div>
<div class="grid" id="grid"></div>
%PTS%
<div class="stage" id="stage">
%HTML%
</div>
<div class="vig"></div>
</div>
<script>
const tl = gsap.timeline({ paused: true });
const D = %DUR%;
tl.to("#a1", { x: 260, y: -140, duration: D, ease: "sine.inOut" }, 0);
tl.to("#a2", { x: -240, y: -220, duration: D, ease: "sine.inOut" }, 0);
tl.to("#a3", { x: 120, y: 160, duration: D, ease: "sine.inOut" }, 0);
tl.fromTo("#grid", { y: 0, rotation: 0 }, { y: 72, rotation: 2, duration: D, ease: "none" }, 0);
document.querySelectorAll(".pt").forEach(p => {
  tl.fromTo(p, { y: 0, opacity: 0 }, { y: -(+p.dataset.v), opacity: +p.dataset.o, duration: D * .35, ease: "sine.out" }, 0);
  tl.to(p, { y: -(+p.dataset.v) * 2.6, opacity: 0, duration: D * .65, ease: "sine.in" }, D * .35);
});
%JS%
window.__timelines["%ID%"] = tl;
</script></body></html>
"""


def particulas(semente, n=34):
    r = random.Random(semente); out = []
    for k in range(n):
        s = r.uniform(3, 9)
        out.append(f'<div class="pt" style="left:{r.uniform(40,1040):.0f}px;top:{r.uniform(200,1800):.0f}px;'
                   f'width:{s:.1f}px;height:{s:.1f}px;filter:blur({r.uniform(0,2.5):.1f}px)" '
                   f'data-v="{r.uniform(60,220):.0f}" data-o="{r.uniform(.25,.8):.2f}"></div>')
    return "\n".join(out)


CHECK = '<svg viewBox="0 0 40 40"><path d="M9 21 L17 29 L32 12"/></svg>'

MOTIONS = {
# ------------------------------------------------------------------ contador com anel medidor
"contador": dict(dur=4.4, css="""
#ring { position:absolute; left:190px; top:560px; width:700px; height:700px; }
#ring svg { width:100%; height:100%; overflow:visible; }
#trilho { fill:none; stroke:rgba(255,255,255,.08); stroke-width:26; }
#arco { fill:none; stroke:url(#gr); stroke-width:26; stroke-linecap:round; filter:drop-shadow(0 0 22px rgba(255,106,43,.75)); }
.tick { stroke:rgba(255,255,255,.22); stroke-width:3; }
#dot { fill:#fff; filter:drop-shadow(0 0 16px #ffb36b) drop-shadow(0 0 30px #ff6a2b); }
#num { position:absolute; left:0; right:0; top:820px; text-align:center; font-weight:900; font-size:116px; line-height:1; letter-spacing:-.02em; }
#suf { position:absolute; left:0; right:0; top:960px; text-align:center; font-weight:700; font-size:46px; }
#leg { position:absolute; left:0; right:0; top:1330px; text-align:center; font-weight:500; font-size:40px; color:var(--mut); }
#chip { left:50%; top:470px; transform:translateX(-50%); }
""", html="""
<div class="chip" id="chip"><i></i>DADO DO VÍDEO</div>
<div id="ring"><svg viewBox="0 0 700 700">
  <defs><linearGradient id="gr" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffd9a8"/><stop offset=".5" stop-color="#ff8a3d"/><stop offset="1" stop-color="#ff3d6e"/></linearGradient></defs>
  <g id="ticks"></g>
  <circle id="trilho" cx="350" cy="350" r="300"/>
  <circle id="arco" cx="350" cy="350" r="300" transform="rotate(-90 350 350)" stroke-dasharray="1885" stroke-dashoffset="1885"/>
  <circle id="dot" cx="350" cy="50" r="17"/>
</svg></div>
<div id="num" class="grad">0</div>
<div id="suf">médicos</div>
<div id="leg">faltam nos EUA até 2038</div>
""", js="""
const tk = document.querySelector("#ticks");
for (let k = 0; k < 60; k++) { const a = k * 6 * Math.PI / 180, r1 = 340, r2 = k % 5 ? 352 : 364;
  tk.insertAdjacentHTML("beforeend", `<line class="tick" x1="${350 + r1 * Math.sin(a)}" y1="${350 - r1 * Math.cos(a)}" x2="${350 + r2 * Math.sin(a)}" y2="${350 - r2 * Math.cos(a)}"/>`); }
tl.fromTo("#ring", { opacity:0, scale:.6, rotationX:55 }, { opacity:1, scale:1, rotationX:0, duration:.9, ease:"expo.out" }, .05);
tl.fromTo(".tick", { opacity:0 }, { opacity:1, duration:.02, stagger:.012 }, .2);
tl.fromTo("#chip", { opacity:0, y:-30 }, { opacity:1, y:0, duration:.5, ease:"power3.out" }, .3);
const n = { v: 0, a: 0 };
tl.to(n, { v: 141000, a: .82, duration: 2.1, ease: "power3.out", onUpdate: () => {
  document.querySelector("#num").textContent = Math.round(n.v).toLocaleString("pt-BR");
  document.querySelector("#arco").setAttribute("stroke-dashoffset", 1885 * (1 - n.a));
  const ang = n.a * 2 * Math.PI; const d = document.querySelector("#dot");
  d.setAttribute("cx", 350 + 300 * Math.sin(ang)); d.setAttribute("cy", 350 - 300 * Math.cos(ang)); } }, .45);
tl.fromTo("#num", { opacity:0, scale:.7, filter:"blur(16px)" }, { opacity:1, scale:1, filter:"blur(0px)", duration:.6, ease:"power3.out" }, .45);
tl.fromTo("#suf", { opacity:0, y:24 }, { opacity:1, y:0, duration:.5, ease:"power3.out" }, .8);
tl.fromTo("#leg", { opacity:0, y:24 }, { opacity:1, y:0, duration:.5, ease:"power3.out" }, 1.0);
tl.to("#num", { scale:1.07, duration:.22, yoyo:true, repeat:1, ease:"sine.inOut" }, 2.55);
tl.to("#stage", { scale:1.04, duration:D, ease:"none" }, 0);
tl.to(["#chip","#ring","#num","#suf","#leg"], { opacity:0, y:-40, filter:"blur(10px)", duration:.4, stagger:.03, ease:"power2.in" }, D - .55);
"""),

# ------------------------------------------------------------------ lista em cartão de vidro 3D
"lista": dict(dur=4.8, css="""
#card { left:110px; width:860px; top:560px; height:800px; }
#tit { position:absolute; left:64px; top:64px; font-weight:800; font-size:62px; line-height:1.12; }
#bar { position:absolute; left:64px; top:236px; width:150px; height:7px; border-radius:4px; background:linear-gradient(90deg,var(--o1),var(--o2)); transform-origin:left; box-shadow:0 0 18px rgba(255,106,43,.7); }
.it { position:absolute; left:64px; right:64px; height:120px; display:flex; align-items:center; gap:30px;
  border-radius:26px; padding:0 26px; background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.08); }
.it span { font-weight:600; font-size:44px; }
.it small { margin-left:auto; font-weight:700; font-size:26px; color:var(--mut); letter-spacing:.1em; }
.ck { width:76px; height:76px; border-radius:50%; flex:none; background:linear-gradient(135deg,var(--o2),var(--o1));
  display:flex; align-items:center; justify-content:center; box-shadow:0 0 0 8px rgba(255,106,43,.12), 0 10px 30px rgba(255,106,43,.5); }
.ck svg { width:42px; height:42px; }
.ck path { fill:none; stroke:#120b06; stroke-width:6; stroke-linecap:round; stroke-linejoin:round; stroke-dasharray:60; stroke-dashoffset:60; }
""", html=f"""
<div class="glass" id="card">
  <div class="sweep" id="sw"></div>
  <div id="tit">3 passos para<br><span class="grad">tirar do papel</span></div>
  <div id="bar"></div>
  <div class="it" id="i1" style="top:300px"><div class="ck">{CHECK}</div><span>Defina o objetivo</span><small>01</small></div>
  <div class="it" id="i2" style="top:450px"><div class="ck">{CHECK}</div><span>Monte o plano</span><small>02</small></div>
  <div class="it" id="i3" style="top:600px"><div class="ck">{CHECK}</div><span>Comece hoje</span><small>03</small></div>
</div>
""", js="""
tl.fromTo("#card", { opacity:0, rotationX:38, rotationY:-18, y:220, z:-400 }, { opacity:1, rotationX:0, rotationY:0, y:0, z:0, duration:1.1, ease:"expo.out" }, .05);
tl.to("#card", { rotationY:5, rotationX:-3, duration:D - 1.2, ease:"sine.inOut" }, 1.15);
tl.fromTo("#tit", { opacity:0, y:40, filter:"blur(12px)" }, { opacity:1, y:0, filter:"blur(0px)", duration:.6, ease:"power3.out" }, .4);
tl.fromTo("#bar", { scaleX:0 }, { scaleX:1, duration:.55, ease:"expo.out" }, .75);
["#i1","#i2","#i3"].forEach((s, k) => { const t = 1.05 + k * .5;
  tl.fromTo(s, { opacity:0, x:-80, rotationY:-30 }, { opacity:1, x:0, rotationY:0, duration:.6, ease:"expo.out" }, t);
  tl.fromTo(s + " .ck", { scale:0, rotation:-120 }, { scale:1, rotation:0, duration:.5, ease:"back.out(2.4)" }, t + .1);
  tl.to(s + " path", { strokeDashoffset:0, duration:.35, ease:"power2.out" }, t + .3);
  tl.fromTo(s, { backgroundColor:"rgba(255,106,43,.22)" }, { backgroundColor:"rgba(255,255,255,.04)", duration:.6 }, t + .3); });
tl.fromTo("#sw", { left:"-60%" }, { left:"140%", duration:1.1, ease:"power2.inOut" }, 2.6);
tl.to("#card", { opacity:0, y:-60, rotationX:-20, filter:"blur(10px)", duration:.45, ease:"power2.in" }, D - .55);
"""),

# ------------------------------------------------------------------ tipografia cinética
"frase": dict(dur=4.4, css="""
#box { position:absolute; left:0; right:0; top:700px; text-align:center; white-space:nowrap; transform-style:preserve-3d; }
.l { display:block; font-weight:900; font-size:100px; line-height:1.08; letter-spacing:-.01em; }
.ch { display:inline-block; transform-origin:50% 100%; }
#hl { position:absolute; left:0; top:0; width:10px; height:10px; border-radius:18px;
  background:linear-gradient(100deg,var(--o1),var(--o2)); transform-origin:left center; box-shadow:0 20px 60px rgba(255,106,43,.45); }
#l2b .ch { color:#140904; }
#l2a { margin-right:26px; }
#sub { position:absolute; left:0; right:0; top:1040px; text-align:center; font-weight:600; font-size:34px; color:var(--mut); letter-spacing:.32em; }
#q1, #q2 { position:absolute; font-weight:900; font-size:260px; line-height:1; color:rgba(255,255,255,.06); }
#q1 { left:70px; top:520px; } #q2 { right:70px; top:960px; }
""", html="""
<div id="q1">“</div><div id="q2">”</div>
<div id="hl"></div>
<div id="box">
  <span class="l" id="l1">O SEGREDO</span>
  <span class="l"><span id="l2a">É </span><span id="l2b">CONSTÂNCIA</span></span>
</div>
<div id="sub">LETTERING ANIMADO</div>
""", js="""
["#l1","#l2a","#l2b"].forEach(s => { const el = document.querySelector(s);
  el.innerHTML = [...el.textContent].map(c => c === " " ? " " : `<span class="ch">${c}</span>`).join(""); });
{ const r = document.querySelector("#l2b").getBoundingClientRect(), hl = document.querySelector("#hl");
  hl.style.left = (r.left - 16) + "px"; hl.style.top = (r.top + 6) + "px"; hl.style.width = (r.width + 32) + "px"; hl.style.height = (r.height - 6) + "px"; }
tl.fromTo("#l1 .ch, #l2a .ch", { opacity:0, y:120, rotationX:-90, filter:"blur(10px)" },
  { opacity:1, y:0, rotationX:0, filter:"blur(0px)", duration:.7, stagger:.035, ease:"expo.out" }, .1);
tl.fromTo("#hl", { scaleX:0 }, { scaleX:1, duration:.55, ease:"expo.inOut" }, .85);
tl.fromTo("#l2b .ch", { opacity:0, y:60, scale:.4 }, { opacity:1, y:0, scale:1, duration:.55, stagger:.03, ease:"back.out(2.2)" }, 1.15);
tl.fromTo("#sub", { opacity:0, letterSpacing:"0.8em" }, { opacity:1, letterSpacing:"0.32em", duration:.9, ease:"expo.out" }, 1.5);
tl.fromTo(["#q1","#q2"], { opacity:0, scale:.6 }, { opacity:1, scale:1, duration:.8, stagger:.1, ease:"expo.out" }, .3);
tl.fromTo("#stage", { scale:.96 }, { scale:1.06, duration:D, ease:"none" }, 0);
tl.to("#hl", { scaleX:1.03, duration:.25, yoyo:true, repeat:1, ease:"sine.inOut" }, 2.4);
tl.to(".ch", { opacity:0, y:-80, filter:"blur(12px)", duration:.35, stagger:.012, ease:"power2.in" }, D - .75);
tl.to(["#hl","#sub","#q1","#q2"], { opacity:0, duration:.35 }, D - .45);
"""),

# ------------------------------------------------------------------ gráfico de linha com área
"grafico": dict(dur=4.6, css="""
#card { left:90px; width:900px; top:540px; height:840px; }
#tit { position:absolute; left:60px; top:56px; font-weight:800; font-size:52px; }
#sub { position:absolute; left:60px; top:126px; font-weight:500; font-size:30px; color:var(--mut); }
#pill { position:absolute; right:56px; top:60px; padding:12px 26px; border-radius:999px; font-weight:800; font-size:40px;
  background:rgba(255,106,43,.16); border:1.5px solid rgba(255,138,61,.6); color:var(--o2); box-shadow:0 0 30px rgba(255,106,43,.35); }
#ch { position:absolute; left:40px; top:210px; width:820px; height:560px; }
#ch svg { width:100%; height:100%; overflow:visible; }
.gl { stroke:rgba(255,255,255,.08); stroke-width:2; }
.lb { fill:var(--mut); font:600 26px Poppins; }
#ln { fill:none; stroke:url(#lg); stroke-width:9; stroke-linecap:round; stroke-linejoin:round; filter:drop-shadow(0 0 14px rgba(255,106,43,.8)); }
#ar { fill:url(#ag); }
#pt { fill:#fff; filter:drop-shadow(0 0 14px #ffb36b) drop-shadow(0 0 26px #ff6a2b); }
#tip { position:absolute; padding:10px 20px; border-radius:16px; background:#fff; color:#120b06; font-weight:800; font-size:30px; white-space:nowrap; }
""", html="""
<div class="glass" id="card">
  <div class="sweep" id="sw"></div>
  <div id="tit">Alcance mensal</div>
  <div id="sub">depois dos Reels editados</div>
  <div id="pill">+212%</div>
  <div id="ch"><svg viewBox="0 0 820 560">
    <defs>
      <linearGradient id="lg" x1="0" x2="1"><stop offset="0" stop-color="#ffb36b"/><stop offset="1" stop-color="#ff3d6e"/></linearGradient>
      <linearGradient id="ag" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="rgba(255,106,43,.45)"/><stop offset="1" stop-color="rgba(255,106,43,0)"/></linearGradient>
      <clipPath id="cp"><rect id="cr" x="0" y="0" width="0" height="560"/></clipPath>
    </defs>
    <line class="gl" x1="20" y1="80" x2="800" y2="80"/><line class="gl" x1="20" y1="200" x2="800" y2="200"/>
    <line class="gl" x1="20" y1="320" x2="800" y2="320"/><line class="gl" x1="20" y1="440" x2="800" y2="440"/>
    <path id="ar" clip-path="url(#cp)" d="M40 430 C140 420 180 380 260 370 C350 358 380 300 470 280 C560 260 600 170 680 130 C720 110 760 90 790 70 L790 470 L40 470 Z"/>
    <path id="ln" d="M40 430 C140 420 180 380 260 370 C350 358 380 300 470 280 C560 260 600 170 680 130 C720 110 760 90 790 70"/>
    <circle id="pt" cx="40" cy="430" r="15"/>
    <text class="lb" x="40" y="530">JAN</text><text class="lb" x="270" y="530">FEV</text><text class="lb" x="500" y="530">MAR</text><text class="lb" x="720" y="530">ABR</text>
  </svg></div>
  <div id="tip">0 mil</div>
</div>
""", js="""
const ln = document.querySelector("#ln"); const L = ln.getTotalLength();
ln.style.strokeDasharray = L; ln.style.strokeDashoffset = L;
tl.fromTo("#card", { opacity:0, rotationX:30, y:200, z:-300 }, { opacity:1, rotationX:0, y:0, z:0, duration:1.0, ease:"expo.out" }, .05);
tl.to("#card", { rotationY:-4, rotationX:3, duration:D - 1.1, ease:"sine.inOut" }, 1.05);
tl.fromTo(["#tit","#sub"], { opacity:0, y:24 }, { opacity:1, y:0, duration:.5, stagger:.1, ease:"power3.out" }, .4);
tl.fromTo(".gl", { scaleX:0, transformOrigin:"left" }, { scaleX:1, duration:.6, stagger:.06, ease:"expo.out" }, .5);
tl.fromTo(".lb", { opacity:0, y:14 }, { opacity:1, y:0, duration:.3, stagger:.08 }, .7);
const st = { p: 0 };
tl.to(st, { p: 1, duration: 1.8, ease: "power2.inOut", onUpdate: () => {
  ln.style.strokeDashoffset = L * (1 - st.p);
  const q = ln.getPointAtLength(L * st.p); const pt = document.querySelector("#pt");
  pt.setAttribute("cx", q.x); pt.setAttribute("cy", q.y);
  document.querySelector("#cr").setAttribute("width", q.x);
  const tip = document.querySelector("#tip"); tip.style.left = Math.min(40 + q.x - 30, 900 - 40 - tip.offsetWidth) + "px"; tip.style.top = (210 + q.y - 90) + "px";
  tip.textContent = Math.round(12 + st.p * 238) + " mil"; } }, .85);
tl.fromTo("#tip", { opacity:0, scale:.6 }, { opacity:1, scale:1, duration:.35, ease:"back.out(2)" }, .9);
tl.fromTo("#pill", { opacity:0, scale:.4 }, { opacity:1, scale:1, duration:.5, ease:"back.out(2.4)" }, 2.6);
tl.fromTo("#sw", { left:"-60%" }, { left:"140%", duration:1.0, ease:"power2.inOut" }, 2.8);
tl.to("#card", { opacity:0, y:-60, filter:"blur(10px)", duration:.45, ease:"power2.in" }, D - .55);
"""),

# ------------------------------------------------------------------ CTA com cursor e clique
"cta": dict(dur=4.6, css="""
#logo { position:absolute; left:430px; top:540px; width:220px; height:220px; border-radius:56px;
  background:linear-gradient(140deg,#ffd9a8,var(--o1) 55%,#ff3d6e); display:flex; align-items:center; justify-content:center;
  font-weight:900; font-size:120px; color:#120b06; box-shadow:0 30px 90px rgba(255,106,43,.55), inset 0 2px 0 rgba(255,255,255,.6); }
.orb { position:absolute; left:540px; top:650px; border-radius:50%; border:2px solid rgba(255,179,107,.35); transform:translate(-50%,-50%); }
#o1 { width:340px; height:340px; } #o2 { width:470px; height:470px; border-color:rgba(124,92,255,.3); }
.sat { position:absolute; width:16px; height:16px; border-radius:50%; background:#fff; box-shadow:0 0 18px #ffb36b; }
#tit { position:absolute; left:0; right:0; top:860px; text-align:center; font-weight:900; font-size:100px; line-height:1.04; }
#btn { position:absolute; left:220px; width:640px; top:1130px; height:132px; border-radius:999px; overflow:hidden;
  background:linear-gradient(180deg,#fff,#e8ecf4); color:#120b06; display:flex; align-items:center; justify-content:center; gap:22px;
  font-weight:800; font-size:48px; box-shadow:0 24px 70px rgba(255,255,255,.18); }
#btn svg { width:46px; height:46px; }
#bsw { position:absolute; top:0; left:-40%; width:30%; height:100%; background:linear-gradient(90deg,transparent,rgba(255,106,43,.35),transparent); transform:skewX(-20deg); }
#rip { position:absolute; left:805px; top:1196px; width:40px; height:40px; border-radius:50%; border:4px solid #ffb36b; transform:translate(-50%,-50%); opacity:0; }
#cur { position:absolute; left:760px; top:1360px; width:92px; height:92px; filter:drop-shadow(0 10px 20px rgba(0,0,0,.5)); }
#site { position:absolute; left:0; right:0; top:1300px; text-align:center; font-weight:600; font-size:34px; color:var(--mut); letter-spacing:.08em; }
""", html="""
<div class="orb" id="o1"><div class="sat" style="left:-8px;top:162px"></div></div>
<div class="orb" id="o2"><div class="sat" style="left:227px;top:-8px;background:#b9a8ff;box-shadow:0 0 18px #7c5cff"></div></div>
<div id="logo">G</div>
<div id="tit">Quer o seu<br><span class="grad">vídeo assim?</span></div>
<div id="btn"><div id="bsw"></div>Link na bio <svg viewBox="0 0 46 46"><path d="M10 23 H34 M25 13 L35 23 L25 33" fill="none" stroke="#120b06" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
<div id="rip"></div>
<div id="site">seusite.com.br</div>
<svg id="cur" viewBox="0 0 92 92"><path d="M22 8 L22 70 L37 56 L48 82 L60 77 L49 52 L70 52 Z" fill="#fff" stroke="#120b06" stroke-width="4" stroke-linejoin="round"/></svg>
""", js="""
tl.fromTo("#logo", { opacity:0, scale:.2, rotationY:180, rotationX:30 }, { opacity:1, scale:1, rotationY:0, rotationX:0, duration:1.0, ease:"expo.out" }, .05);
tl.fromTo([".orb"], { opacity:0, scale:.5 }, { opacity:1, scale:1, duration:.9, stagger:.12, ease:"expo.out" }, .3);
tl.fromTo("#o1", { rotation:0 }, { rotation:200, duration:D, ease:"none" }, 0);
tl.fromTo("#o2", { rotation:0 }, { rotation:-140, duration:D, ease:"none" }, 0);
tl.fromTo("#tit", { opacity:0, y:60, filter:"blur(14px)" }, { opacity:1, y:0, filter:"blur(0px)", duration:.7, ease:"expo.out" }, .55);
tl.fromTo("#btn", { opacity:0, y:50, scale:.8 }, { opacity:1, y:0, scale:1, duration:.6, ease:"back.out(2)" }, .95);
tl.fromTo("#site", { opacity:0 }, { opacity:1, duration:.5 }, 1.25);
tl.fromTo("#bsw", { left:"-40%" }, { left:"130%", duration:.9, ease:"power2.inOut" }, 1.3);
tl.fromTo("#cur", { opacity:0, x:160, y:200 }, { opacity:1, x:0, y:0, duration:.8, ease:"power3.out" }, 1.5);
tl.to("#cur", { x:24, y:-168, duration:.6, ease:"power3.inOut" }, 2.3);
tl.to("#cur", { scale:.82, duration:.1, yoyo:true, repeat:1 }, 2.9);
tl.to("#btn", { scale:.95, duration:.1, yoyo:true, repeat:1 }, 2.9);
tl.fromTo("#rip", { opacity:1, width:40, height:40 }, { opacity:0, width:520, height:520, duration:.8, ease:"expo.out" }, 2.95);
tl.to("#logo", { scale:1.08, duration:.2, yoyo:true, repeat:1, ease:"sine.inOut" }, 3.0);
tl.to(["#logo",".orb","#tit","#btn","#site","#cur"], { opacity:0, y:-40, filter:"blur(10px)", duration:.4, stagger:.03, ease:"power2.in" }, D - .55);
"""),
}

if __name__ == "__main__":
    for k, (nome, m) in enumerate(MOTIONS.items()):
        d = AQUI / nome
        (d / "fonts").mkdir(parents=True, exist_ok=True)
        for f in glob.glob(str(FONTES / "**" / "Poppins-*.ttf"), recursive=True):
            shutil.copy(f, d / "fonts")
        html = (HEAD.replace("%CSS%", m["css"]).replace("%HTML%", m["html"]).replace("%JS%", m["js"])
                .replace("%PTS%", particulas(k + 7)).replace("%ID%", nome).replace("%DUR%", str(m["dur"])))
        (d / "index.html").write_text(html)
        (d / "hyperframes.json").write_text('{"paths":{"blocks":"compositions","components":"compositions/components","assets":"assets"}}')
        print("ok", nome)
