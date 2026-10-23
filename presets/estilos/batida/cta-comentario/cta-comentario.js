// BATIDA · comente a palavra: cartão branco com um anel em degradê (cor da marca girando para um tom vizinho) à esquerda;
// "Comente" digita letra a letra com cursor e a palavra-chave entra grande, em degradê, com um pulo. Segura até o fim.
// Fica abaixo do queixo (lugar natural de chamada) ou acima da cabeça se embaixo não couber.
ESTILO["cta-comentario"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, LW = W - 2 * 70, LH = 250;
  C.css("cta-comentario", `
    .ct{position:absolute;width:${LW}px;height:${LH}px;border-radius:56px;background:#fff;box-shadow:0 26px 60px rgba(0,0,0,.4);
        display:flex;align-items:center;gap:36px;padding:0 44px;color:#111;transform-origin:50% 50%;
        --dg:linear-gradient(120deg,var(--dest),#7b5cff);--dg:linear-gradient(120deg,var(--dest),hsl(from var(--dest) calc(h + 70) s l))}
    .ct .an{width:150px;height:150px;border-radius:50%;background:var(--dg);padding:9px;flex:none}
    .ct .an i{display:grid;place-items:center;width:100%;height:100%;border-radius:50%;background:#fff;border:6px solid #fff;
        background-clip:padding-box;font-style:normal}
    .ct .an svg{width:70px;height:70px}
    .ct .tx{flex:1;min-width:0}
    .ct .ac{font-weight:800;font-size:40px;color:#555a62;height:52px;white-space:nowrap}
    .ct .ac span{display:none}
    .ct .ac .cu{display:inline-block;width:4px;height:40px;background:#111;vertical-align:-6px;margin-left:3px}
    .ct .pv{font-weight:900;font-size:104px;line-height:1.02;letter-spacing:-.03em;white-space:nowrap;background:var(--dg);
        -webkit-background-clip:text;background-clip:text;color:transparent;transform-origin:0 60%;padding-right:10px}
    .ct .sb{font-weight:700;font-size:30px;color:#8a8f98;margin-top:2px}`);
  const r = C.rostoEm(it.de) || [W * .3, H * .3, W * .7, H * .55];
  const cima = r[1] - 30 - S.topo, baixo = H - S.baixo - (r[3] + 40);
  const zona = baixo >= LH * .8 || baixo >= cima ? [r[3] + 40, H - S.baixo] : [S.topo, r[1] - 30];
  const pal = String(it.palavra || ""), esc = Math.min(1, (zona[1] - zona[0]) / LH, 9.5 / Math.max(6, pal.length));
  const e = C.el("div", "ct"); Object.assign(e.style, {left: "70px", top: ((zona[0] + zona[1]) / 2 - LH / 2) + "px"});
  const ac = String(it.acao || (P.lingua === "en" ? "Comment" : "Comente"));
  e.innerHTML = `<div class="an"><i><svg viewBox="0 0 64 64"><path d="M32 10C18 10 8 19 8 30c0 6 3 11 8 15l-3 10 11-6c2 1 5 1 8 1 14 0 24-9 24-20S46 10 32 10z"
      fill="none" stroke="#111" stroke-width="5" stroke-linejoin="round"/></svg></i></div>
    <div class="tx"><div class="ac">${[...ac].map(c => `<span>${C.esc(c)}</span>`).join("")}<i class="cu"></i></div>
    <div class="pv">${C.esc(pal)}</div>${it.sub ? `<div class="sb">${C.esc(it.sub)}</div>` : ""}</div>`;
  const tl = C.tl, d = it.de, f = it.ate, ls = [...e.querySelectorAll(".ac span")], cu = e.querySelector(".cu"), pv = e.querySelector(".pv");
  const sb = e.querySelector(".sb"), an = e.querySelector(".an");
  tl.fromTo(e, {opacity: 0, scale: esc * .85, y: 50}, {opacity: 1, scale: esc, y: 0, duration: .5, ease: "back.out(1.4)"}, d)
    .fromTo(an, {rotation: -120}, {rotation: 0, duration: .9, ease: "power3.out"}, d);
  ls.forEach((l, i) => tl.to(l, {display: "inline", duration: .001}, d + .4 + i * .06));
  const tp = d + .4 + ls.length * .06 + .1;
  tl.fromTo(pv, {opacity: 0, scale: .5}, {opacity: 1, scale: 1, duration: .45, ease: "back.out(2.2)"}, tp)
    .to(cu, {opacity: 0, duration: .001}, tp);
  if (sb) tl.fromTo(sb, {opacity: 0, y: 10}, {opacity: 1, y: 0, duration: .3}, tp + .25);
  tl.to(e, {scale: esc * 1.04, duration: .15, yoyo: true, repeat: 1, ease: "power1.inOut"}, tp + .6)
    .to(e, {opacity: 0, y: 40, duration: .35, ease: "power2.in"}, Math.max(tp + 1, f - .35));
};
