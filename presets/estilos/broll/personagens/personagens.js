// BROLL · fila de personagens: círculos com foto (campo) ou avatar ilustrado entram um a um de baixo, em fila centralizada,
// com etiqueta escura de nome e papel (o papel na cor da marca). Acima da cabeça ou abaixo do queixo.
ESTILO["personagens"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, wN = 1000, hN = 330, av = 200;
  C.css("personagens", `
    .pe{position:absolute;transform-origin:50% 0}
    .pe .p{position:absolute;top:0;width:250px;display:flex;flex-direction:column;align-items:center}
    .pe .c{width:${av}px;height:${av}px;border-radius:50%;overflow:hidden;background:#3a3d44;box-shadow:0 16px 40px rgba(0,0,0,.45),0 0 0 6px rgba(255,255,255,.92)}
    .pe .c img,.pe .c svg{width:100%;height:100%;object-fit:cover;display:block}
    .pe .et{margin-top:-18px;position:relative;background:rgba(14,14,17,.86);border:1.5px solid rgba(255,255,255,.16);border-radius:22px;padding:10px 22px;
        text-align:center;font-family:"PalcoSans";color:#fff;white-space:nowrap;box-shadow:0 10px 26px rgba(0,0,0,.35)}
    .pe .et b{display:block;font-weight:800;font-size:32px;line-height:1.1}.pe .et small{display:block;font-weight:700;font-size:21px;letter-spacing:.14em;color:var(--dest)}`);
  const r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const zc = [S.topo, r[1] - 36], zb = [r[3] + 36, H - S.baixo], z = (zb[1] - zb[0]) >= (zc[1] - zc[0]) ? zb : zc;
  const s = Math.min(1, (z[1] - z[0]) / hN, (W - 2 * S.lado) / wN);
  const b = C.el("div", "pe");
  Object.assign(b.style, {width: wN + "px", height: hN + "px", left: (W - wN) / 2 + "px", top: (z[0] + ((z[1] - z[0]) - hN * s) / 2) + "px",
                          transform: `scale(${s})`});
  // avatar ilustrado (fictício): pele, cabelo e roupa variam por índice
  const pele = ["#E8C4A0", "#B07A52", "#F2D6BE", "#8A5A3C"], cab = ["#2B2420", "#5A3A22", "#C9A15A", "#151515"], roupa = ["#3F5E7A", "#7A3F4E", "#4E6B45", "#6A5A86"];
  const ilustra = i => `<svg viewBox="0 0 200 200"><rect width="200" height="200" fill="${i % 2 ? "#2E3036" : "#3A3D44"}"/>
    <path d="M30 200 Q40 150 100 150 Q160 150 170 200Z" fill="${roupa[i % 4]}"/><rect x="86" y="120" width="28" height="36" fill="${pele[i % 4]}"/>
    <ellipse cx="100" cy="98" rx="42" ry="48" fill="${pele[i % 4]}"/>
    <path d="${i % 3 === 1 ? "M54 104 Q50 44 100 44 Q150 44 146 104 Q148 160 136 150 L134 84 Q100 70 66 84 L64 150 Q52 160 54 104Z" : "M56 92 Q58 46 100 46 Q142 46 144 92 Q128 70 100 72 Q72 70 56 92Z"}" fill="${cab[i % 4]}"/>
    <circle cx="85" cy="102" r="4.5" fill="#222"/><circle cx="115" cy="102" r="4.5" fill="#222"/>
    <path d="M88 124 Q100 132 112 124" fill="none" stroke="#5a2e22" stroke-width="3.5" stroke-linecap="round"/></svg>`;
  const ps = it.pessoas || [], n = Math.max(1, ps.length), passo = Math.min(260, (wN - 250) / Math.max(1, n - 1)), x0 = (wN - 250 - passo * (n - 1)) / 2;
  const tl = C.tl, d = it.de, f = it.ate, els = [];
  ps.forEach((x, i) => {
    const p = C.el("div", "p", b, `<div class="c">${x.img ? `<img src="${C.esc(x.img)}">` : ilustra(i)}</div>
      <div class="et"><b>${C.esc(x.nome || "")}</b>${x.papel ? `<small>${C.esc(String(x.papel).toUpperCase())}</small>` : ""}</div>`);
    p.style.left = (x0 + i * passo) + "px"; els.push(p);
    const c = p.querySelector(".c"), et = p.querySelector(".et"), em = typeof x.em === "number" ? x.em : d + i * .35;
    tl.set(c, {y: 90, scale: .7, opacity: 0}, 0).set(et, {y: 20, opacity: 0}, 0)
      .to(c, {y: 0, scale: 1, opacity: 1, duration: .55, ease: "expo.out"}, em)
      .to(et, {y: 0, opacity: 1, duration: .35, ease: "power3.out"}, em + .2);
  });
  tl.to(els, {y: -50, opacity: 0, duration: .4, stagger: .05, ease: "power2.in"}, Math.max(d + 1.6, f - .5));
};
