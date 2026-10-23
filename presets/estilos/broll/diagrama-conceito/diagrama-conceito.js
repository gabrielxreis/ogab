// BROLL · diagrama do conceito: a nuvem do centro se desenha (traço e depois preenchimento), os itens em volta entram como
// cartões, as linhas se desenham até a nuvem com a ponta da seta na cor da marca e um ponto corre por cada linha. Fora do rosto.
ESTILO["diagrama-conceito"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, wN = 1000, hN = 360;
  C.css("diagrama-conceito", `
    .dc{position:absolute;transform-origin:50% 0}
    .dc svg{position:absolute;inset:0;overflow:visible;font-family:"PalcoSans"}
    .dc .no rect{fill:rgba(16,16,19,.86);stroke:rgba(255,255,255,.2);stroke-width:2}
    .dc .no text{fill:#fff;font-weight:800;font-size:30px}.dc .nu text{fill:#111;font-weight:900;font-size:40px}
    .dc .li{fill:none;stroke:rgba(255,255,255,.85);stroke-width:4;stroke-linecap:round}`);
  const r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const zc = [S.topo, r[1] - 36], zb = [r[3] + 36, H - S.baixo], z = (zb[1] - zb[0]) >= (zc[1] - zc[0]) ? zb : zc;
  const s = Math.min(1, (z[1] - z[0]) / hN, (W - 2 * S.lado) / wN);
  const b = C.el("div", "dc");
  Object.assign(b.style, {width: wN + "px", height: hN + "px", left: (W - wN) / 2 + "px", top: (z[0] + ((z[1] - z[0]) - hN * s) / 2) + "px",
                          transform: `scale(${s})`});
  const nos = (it.nos || []).slice(0, 4), cx = 500, cy = 180;
  const pos = [[150, 70], [150, 290], [850, 70], [850, 290]].slice(0, nos.length);
  const nuvem = "M392 238 Q340 238 340 196 Q340 154 384 150 Q392 100 446 102 Q474 66 522 78 Q566 70 584 114 Q640 110 650 160 Q668 204 620 238 Z";
  // linha: da borda do cartão até perto da nuvem, levemente curva
  const linhas = pos.map(([x, y]) => { const ex = x < cx ? 350 : 650, ey = cy + (y < cy ? -24 : 24), sx = x < cx ? x + 120 : x - 120;
    return {d: `M${sx} ${y} Q${(sx + ex) / 2} ${y} ${ex} ${ey}`, ex, ey, ang: Math.atan2(ey - y, ex - (sx + ex) / 2) * 180 / Math.PI}; });
  const svg = `<svg viewBox="0 0 ${wN} ${hN}" width="${wN}" height="${hN}">
    ${linhas.map(l => `<path class="li" d="${l.d}" pathLength="1"/>
      <path class="sp" d="M-18 -11 L0 0 L-18 11 Z" fill="var(--dest)" transform="translate(${l.ex} ${l.ey}) rotate(${l.ang.toFixed(1)})"/>
      <circle class="pn" r="9" fill="var(--dest)"/>`).join("")}
    <g class="nu"><path class="nf" d="${nuvem}" fill="var(--dest)"/><path class="nt" d="${nuvem}" fill="none" stroke="#fff" stroke-width="5" pathLength="1"/>
      <text x="${cx}" y="${cy + 14}" text-anchor="middle">${C.esc(it.centro || "")}</text></g>
    ${pos.map(([x, y], i) => `<g class="no" transform="translate(${x} ${y})"><rect x="-120" y="-40" width="240" height="80" rx="24"/>
      <circle cx="-82" cy="0" r="14" fill="var(--dest)"/><text x="-56" y="10">${C.esc(nos[i])}</text></g>`).join("")}</svg>`;
  b.innerHTML = svg;
  const q = sel => [...b.querySelectorAll(sel)], li = q(".li"), sp = q(".sp"), pn = q(".pn"), no = q(".no");
  const nf = b.querySelector(".nf"), nt = b.querySelector(".nt"), tx = b.querySelector(".nu text");
  const tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 2, f - .45);
  tl.set(nt, {strokeDasharray: 1, strokeDashoffset: 1}, 0).set([nf, tx], {opacity: 0}, 0).set(li, {strokeDasharray: 1, strokeDashoffset: 1}, 0)
    .set(sp, {opacity: 0}, 0).set(pn, {opacity: 0}, 0).set(no, {opacity: 0, y: 30}, 0)
    .to(nt, {strokeDashoffset: 0, duration: .7, ease: "power2.inOut"}, d)
    .to(nf, {opacity: 1, duration: .35, ease: "power2.out"}, d + .55).to(tx, {opacity: 1, duration: .3}, d + .65)
    .to(no, {opacity: 1, y: 0, duration: .45, stagger: .12, ease: "expo.out"}, d + .5)
    .to(li, {strokeDashoffset: 0, duration: .55, stagger: .12, ease: "power2.inOut"}, d + .9)
    .to(sp, {opacity: 1, duration: .2, stagger: .12}, d + 1.35);
  // ponto correndo pela linha (do cartão até a nuvem), duas passadas; pontos calculados antes (render por seek, sem onUpdate)
  linhas.forEach((l, i) => { const el = li[i], c = pn[i], L = el.getTotalLength(), t0 = d + 1.5 + i * .12, n = 14;
    const pts = [...Array(n + 1)].map((_, k) => el.getPointAtLength(L * k / n));
    tl.set(c, {attr: {cx: pts[0].x, cy: pts[0].y}}, 0);
    [0, 1].forEach(v => { const t = t0 + v * .75; tl.set(c, {opacity: 1, attr: {cx: pts[0].x, cy: pts[0].y}}, t)
      .to(c, {keyframes: pts.slice(1).map(p => ({attr: {cx: p.x, cy: p.y}, duration: .6 / n})), ease: "none"}, t)
      .to(c, {opacity: 0, duration: .12}, t + .55); }); });
  tl.to(b.querySelector("svg"), {y: -40, opacity: 0, duration: .4, ease: "power2.in"}, sai);
};
