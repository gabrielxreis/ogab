// GANCHO · creme contornado: caixa alta creme com contorno marrom-escuro e sombra deslocada, mais uma linha de apoio caramelo; clima acolhedor.
ESTILO["creme-contornado"] = (it, C) => {
  const P = C.P, W = P.w, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, P.h * .32, W * .68, P.h * .55];
  C.css("creme-contornado", `
    .cc{position:absolute;left:${S.lado}px;right:${S.lado}px;text-align:center}
    .cc .t{font-family:"PalcoSans";font-weight:900;letter-spacing:-.02em;line-height:1;color:#F5E8CF;-webkit-text-stroke:10px #3A2618;paint-order:stroke fill;
        text-shadow:0 9px 0 #3A2618,0 20px 40px rgba(0,0,0,.35)}
    .cc .t div{display:block}
    .cc .ap{font-family:"PalcoSerif";font-style:italic;font-weight:600;color:#D69A55;margin-top:14px;-webkit-text-stroke:4px #3A2618;paint-order:stroke fill}`);
  const tit = String(it.titulo || "").toUpperCase(), pal = tit.split(/\s+/);
  let ls = [tit];
  if (tit.length > 11 && pal.length > 1) {
    let best = 1e9;
    for (let k = 1; k < pal.length; k++) { const a = pal.slice(0, k).join(" "), b = pal.slice(k).join(" "), m = Math.max(a.length, b.length);
      if (m < best) { best = m; ls = [a, b]; } }
  }
  const maior = Math.max(...ls.map(l => l.length)), fs = Math.min(124, (W - 2 * S.lado - 50) / Math.max(4, maior) / .72);
  const ap = String(it.apoio || ""), fa = Math.min(72, (W - 2 * S.lado - 40) / Math.max(6, ap.length) / .42);
  const alt = ls.length * fs + 14 + fa * 1.3, top = Math.max(S.topo, Math.min(S.topo + 30, r[1] - 40 - alt));
  const b = C.el("div", "cc"); b.style.top = top + "px";
  const t = C.el("div", "t", b, ls.map(l => `<div>${C.esc(l)}</div>`).join("")); t.style.fontSize = fs + "px";
  const a = C.el("div", "ap", b, C.esc(ap)); a.style.fontSize = fa + "px";
  const tl = C.tl, d = it.de, f = it.ate;
  tl.set(b, {opacity: 0}, 0).set(b, {opacity: 1}, d)
    .fromTo(t.children, {y: 46, scale: .92, opacity: 0}, {y: 0, scale: 1, opacity: 1, duration: .55, stagger: .1, ease: "expo.out"}, d)
    .fromTo(a, {y: 20, opacity: 0}, {y: 0, opacity: 1, duration: .45, ease: "power3.out"}, d + .35)
    .to(b, {y: -46, opacity: 0, duration: .4, ease: "power2.in"}, Math.max(d + 1, f - .45));
};
