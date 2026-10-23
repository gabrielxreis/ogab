// GANCHO · serifa + arredondada: linha fina em serifa itálica sobre uma palavra grossa e redonda em minúsculas, ar de capa de revista.
ESTILO["serifa-arredondada"] = (it, C) => {
  const P = C.P, W = P.w, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, P.h * .32, W * .68, P.h * .55];
  C.css("serifa-arredondada", `
    .sa{position:absolute;left:${S.lado}px;right:${S.lado}px;text-align:center;text-shadow:0 8px 30px rgba(0,0,0,.4)}
    .sa .l{font-family:"PalcoSerif";font-style:italic;font-weight:400;color:#fff;overflow:hidden;padding-bottom:.12em;line-height:1.1}
    .sa .l span{display:inline-block}
    .sa .p{font-family:"PalcoSans";font-weight:900;letter-spacing:-.05em;line-height:.9;color:var(--dest);margin-top:-.04em;
        -webkit-text-stroke:.035em var(--dest);paint-order:stroke fill}`);
  const lin = String(it.linha || "").toLowerCase(), pal = String(it.palavra || "").toLowerCase();
  const fp = Math.min(220, (W - 2 * S.lado - 60) / Math.max(3, pal.length) / .62), fl = Math.min(64, (W - 2 * S.lado - 40) / Math.max(6, lin.length) / .42);
  const alt = fl * 1.2 + fp * .95, top = Math.max(S.topo, Math.min(S.topo + 30, r[1] - 40 - alt));
  const b = C.el("div", "sa"); b.style.top = top + "px";
  const l = C.el("div", "l", b, `<span>${C.esc(lin)}</span>`); l.style.fontSize = fl + "px";
  const p = C.el("div", "p", b, C.esc(pal)); p.style.fontSize = fp + "px";
  const tl = C.tl, d = it.de, f = it.ate;
  tl.set(b, {opacity: 0}, 0).set(b, {opacity: 1}, d)
    .fromTo(l.firstChild, {yPercent: 110}, {yPercent: 0, duration: .55, ease: "expo.out"}, d)
    .fromTo(p, {y: 50, scale: .9, opacity: 0}, {y: 0, scale: 1, opacity: 1, duration: .6, ease: "expo.out"}, d + .2)
    .to(b, {y: -46, opacity: 0, duration: .4, ease: "power2.in"}, Math.max(d + 1, f - .45));
};
