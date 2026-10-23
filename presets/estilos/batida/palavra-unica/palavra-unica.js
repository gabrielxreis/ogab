// BATIDA · palavra única: palavra grande em caixa alta acima da cabeça, sublinhado na cor da marca que se desenha; "?" opcional na cor da marca.
ESTILO["palavra-unica"] = (it, C) => {
  const P = C.P, W = P.w, pal = String(it.palavra || "").toUpperCase(), q = it.pergunta ? "?" : "";
  const tam = Math.min(W * .86 / Math.max(3, pal.length + q.length) / .64, 230);
  C.css("palavra-unica", `
    .pu{position:absolute;left:0;right:0;text-align:center;font-family:"PalcoSans"}
    .pu .w{display:inline-block;font-weight:900;letter-spacing:-.04em;line-height:1.12;color:#fff;text-shadow:0 10px 36px rgba(0,0,0,.45);overflow:hidden;padding:.12em .04em .06em}
    .pu .w i{font-style:normal;display:inline-block}.pu .w b{color:var(--dest);font-weight:900;display:inline-block}
    .pu .ln{height:14px;border-radius:7px;background:var(--dest);margin:10px auto 0;transform-origin:left center}`);
  const r = C.rostoEm(it.de), alto = tam * 1.3 + 30;
  let y = C.seguro.topo + 10;
  if (r && r[1] - 50 - alto > C.seguro.topo) y = Math.max(C.seguro.topo, r[1] - 50 - alto - 20);
  else if (r && r[1] - 50 - alto < C.seguro.topo) y = Math.min(P.h - C.seguro.baixo - alto, Math.max(y, r[3] + 40));
  const box = C.el("div", "pu"); box.style.top = y + "px";
  const w = C.el("div", "w", box, `<i>${C.esc(pal)}</i>${q ? `<b>${q}</b>` : ""}`); w.style.fontSize = Math.round(tam) + "px";
  const ln = C.el("div", "ln", box); ln.style.width = Math.round(Math.min(W * .5, tam * .64 * pal.length * .55)) + "px";
  const tl = C.tl, d = it.de, f = it.ate;
  tl.set(box, {opacity: 0}, 0).set(box, {opacity: 1}, d)
    .fromTo(w.querySelector("i"), {yPercent: 105}, {yPercent: 0, duration: .5, ease: "expo.out"}, d)
    .fromTo(ln, {scaleX: 0}, {scaleX: 1, duration: .45, ease: "power3.out"}, d + .25);
  if (q) tl.fromTo(w.querySelector("b"), {yPercent: 105, rotate: 12}, {yPercent: 0, rotate: 0, duration: .45, ease: "expo.out"}, d + .3);
  tl.to(box, {y: -30, opacity: 0, duration: .35, ease: "power3.in"}, Math.max(d + .9, f - .35));
};
