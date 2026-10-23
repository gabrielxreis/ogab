// BATIDA · logos e setas: duas marcas em blocos brancos; a seta de ida se desenha por cima, a de volta por baixo, cada uma com rótulo.
ESTILO["logos-setas"] = (it, C) => {
  const P = C.P, W = P.w, lado = 230, alto = 330, mg = 80;
  C.css("logos-setas", `
    .ls{position:absolute;left:0;width:${W}px;height:${alto}px;font-family:"PalcoSans"}
    .ls .bx{position:absolute;top:${(alto - lado) / 2}px;width:${lado}px;height:${lado}px;border-radius:40px;background:#fff;box-shadow:0 14px 40px rgba(0,0,0,.3);
            display:grid;place-items:center;padding:30px;box-sizing:border-box}
    .ls .bx img{width:100%;height:100%;object-fit:contain}
    .ls .mk{width:100%;height:100%;border-radius:28px;display:grid;place-items:center;font-weight:900;font-size:84px;color:#fff}
    .ls svg{position:absolute;left:0;top:0;overflow:visible}
    .ls .rt{position:absolute;left:0;right:0;text-align:center;font-weight:900;font-size:38px;text-transform:uppercase;letter-spacing:.05em;color:#fff;
            text-shadow:0 3px 12px rgba(0,0,0,.55)}
    .ls .rt span{background:var(--dest);color:#111;padding:6px 20px;border-radius:12px;text-shadow:none}`);
  const marca = (l, cor) => l && l.logo ? `<img src="${C.esc(l.logo)}">`
    : `<div class="mk" style="background:${cor}">${C.esc(String((l && l.nome) || "?").slice(0, 1).toUpperCase())}</div>`;
  const lim = P.h - C.seguro.baixo, r = C.rostoEm(it.de);
  let y = lim - alto;
  if (r && r[3] + 40 + alto <= lim) y = r[3] + 40; else if (r && r[1] - 40 - alto >= C.seguro.topo) y = r[1] - 40 - alto;
  const box = C.el("div", "ls"); box.style.top = y + "px";
  const A = C.el("div", "bx", box, marca(it.a, "#15171a")), B = C.el("div", "bx", box, marca(it.b, "#3a4a5c"));
  A.style.left = mg + "px"; B.style.left = (W - mg - lado) + "px";
  const x0 = mg + lado + 30, x1 = W - mg - lado - 30, yi = alto * .36, yv = alto * .64;
  const svg = C.el("div", "", box, `<svg width="${W}" height="${alto}">
    <path d="M${x0} ${yi} Q${W / 2} ${yi - 70} ${x1} ${yi}" fill="none" stroke="var(--dest)" stroke-width="10" stroke-linecap="round"/>
    <path d="M${x1 - 24} ${yi - 22} L${x1} ${yi} L${x1 - 30} ${yi + 12}" fill="none" stroke="var(--dest)" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M${x1} ${yv} Q${W / 2} ${yv + 70} ${x0} ${yv}" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round"/>
    <path d="M${x0 + 24} ${yv + 22} L${x0} ${yv} L${x0 + 30} ${yv - 12}" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/></svg>`);
  const ps = svg.querySelectorAll("path");
  ps.forEach(p => { const L = p.getTotalLength ? p.getTotalLength() : 600; p.style.strokeDasharray = L; p.style.strokeDashoffset = L; });
  const ri = C.el("div", "rt", box, `<span>${C.esc(it.ida || "")}</span>`); ri.style.top = (yi - 120) + "px";
  const rv = C.el("div", "rt", box, it.volta ? `<span style="background:#fff">${C.esc(it.volta)}</span>` : ""); rv.style.top = (yv + 60) + "px";
  const tl = C.tl, d = it.de, f = it.ate, meio = d + (f - d) * .42;
  tl.fromTo([A, B], {scale: .6, opacity: 0}, {scale: 1, opacity: 1, duration: .5, ease: "expo.out", stagger: .12}, d)
    .to([ps[0]], {strokeDashoffset: 0, duration: .55, ease: "power2.inOut"}, d + .35).to([ps[1]], {strokeDashoffset: 0, duration: .2, ease: "power2.out"}, d + .88)
    .fromTo(ri, {y: 16, opacity: 0}, {y: 0, opacity: 1, duration: .35, ease: "power3.out"}, d + .6);
  if (it.volta)
    tl.to([ps[2]], {strokeDashoffset: 0, duration: .55, ease: "power2.inOut"}, meio).to([ps[3]], {strokeDashoffset: 0, duration: .2, ease: "power2.out"}, meio + .53)
      .fromTo(rv, {y: -16, opacity: 0}, {y: 0, opacity: 1, duration: .35, ease: "power3.out"}, meio + .25);
  else tl.set([ps[2], ps[3]], {opacity: 0}, 0);
  tl.set(box, {opacity: 0}, 0).set(box, {opacity: 1}, d)
    .to(box, {y: 40, opacity: 0, duration: .4, ease: "power3.in"}, Math.max(d + 1.2, f - .4));
};
