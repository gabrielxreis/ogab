// BATIDA · logos com papel: blocos brancos com a marca entram na palavra (campo "em") e uma etiqueta na cor da marca diz o papel.
ESTILO["logos-papeis"] = (it, C) => {
  const P = C.P, W = P.w, itens = (it.itens || []).slice(0, 4), n = Math.max(1, itens.length);
  const lado = 34, gap = 30, larg = Math.min(250, (W - 2 * 70 - gap * (n - 1)) / n), alto = larg + 92;
  C.css("logos-papeis", `
    .lp{position:absolute;display:flex;justify-content:center;gap:${gap}px;left:0;right:0;font-family:"PalcoSans"}
    .lp .it{display:flex;flex-direction:column;align-items:center;gap:18px}
    .lp .bx{border-radius:34px;background:#fff;display:grid;place-items:center;overflow:hidden;box-shadow:0 14px 40px rgba(0,0,0,.28);padding:${lado}px;box-sizing:border-box}
    .lp .bx img{width:100%;height:100%;object-fit:contain}
    .lp .mk{width:100%;height:100%;border-radius:24px;display:grid;place-items:center;font-weight:900;color:#fff;letter-spacing:-.04em}
    .lp .tag{background:var(--dest);color:#111;font-weight:900;font-size:34px;text-transform:uppercase;letter-spacing:.04em;
             padding:8px 22px;border-radius:14px;white-space:nowrap}`);
  const CORES = ["#15171a", "#3a4a5c", "#6b3d2e", "#2f4a3a"];
  const marca = (l, i) => l.logo ? `<img src="${C.esc(l.logo)}">`
    : `<div class="mk" style="background:${CORES[i % 4]};font-size:${Math.round(larg * .34)}px">${C.esc(String(l.nome || "?").slice(0, 1).toUpperCase())}</div>`;
  const lim = P.h - C.seguro.baixo, r = C.rostoEm(it.de);
  let y = lim - alto;
  if (r && r[3] + 40 + alto <= lim) y = r[3] + 40; else if (r && r[3] + 40 + alto > lim && r[1] - 40 - alto >= C.seguro.topo) y = r[1] - 40 - alto;
  const box = C.el("div", "lp"); box.style.top = y + "px";
  const tl = C.tl, d = it.de, f = it.ate;
  itens.forEach((l, i) => {
    const e = C.el("div", "it", box, `<div class="bx" style="width:${larg}px;height:${larg}px">${marca(l, i)}</div>
      <div class="tag">${C.esc(l.papel || "")}</div>`);
    const t = Math.max(d, Math.min(f - .6, l.em != null ? +l.em : d + i * .6));
    tl.set(e, {opacity: 0}, 0)
      .fromTo(e.children[0], {y: 60, scale: .7, opacity: 0}, {y: 0, scale: 1, opacity: 1, duration: .5, ease: "expo.out"}, t)
      .set(e, {opacity: 1}, t)
      .fromTo(e.children[1], {y: -20, opacity: 0, clipPath: "inset(0 100% 0 0)"}, {y: 0, opacity: 1, clipPath: "inset(0 0% 0 0)", duration: .4, ease: "power3.out"}, t + .18);
  });
  tl.to(box.children, {y: 40, opacity: 0, duration: .35, ease: "power3.in", stagger: .05}, Math.max(d + 1, f - .45));
};
