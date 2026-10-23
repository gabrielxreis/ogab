// GANCHO · dois pesos: linha em caixa alta bem grossa sobre linha em serifa fina e estreita, centradas no topo; sobem por máscara e saem em ~3 s.
ESTILO["dois-pesos"] = (it, C) => {
  const P = C.P, W = P.w, S = C.seguro;
  C.css("dois-pesos", `
    .dp{position:absolute;left:${S.lado}px;right:${S.lado}px;text-align:center;color:#fff;text-shadow:0 6px 24px rgba(0,0,0,.45)}
    .dp .m{overflow:hidden;padding:0 .05em .1em;margin-bottom:-.06em}.dp .m span{display:inline-block}
    .dp .a{font-family:"PalcoSans";font-weight:900;letter-spacing:-.035em;line-height:.95}
    .dp .b{font-family:"PalcoSerif";font-style:italic;font-weight:400;line-height:1.05;color:var(--dest)}
    .dp .b span{transform-origin:50% 50%}`);
  const l1 = String(it.linha1 || "").toUpperCase(), l2 = String(it.linha2 || "");
  const f1 = Math.min(140, (W - 2 * S.lado - 40) / Math.max(4, l1.length) / .6), f2 = Math.min(124, (W - 2 * S.lado - 40) / Math.max(4, l2.length) / .32);
  const b = C.el("div", "dp"); b.style.top = S.topo + 10 + "px";
  b.innerHTML = `<div class="m a" style="font-size:${f1}px"><span>${C.esc(l1)}</span></div>
    <div class="m b" style="font-size:${f2}px"><span><i style="display:inline-block;font-style:inherit;transform:scaleX(.86)">${C.esc(l2)}</i></span></div>`;
  const sp = b.querySelectorAll(".m > span"), tl = C.tl, d = it.de, sai = Math.max(d + 1.2, Math.min(it.ate, d + 3) - .45);
  tl.set(sp, {yPercent: 115}, 0)
    .to(sp, {yPercent: 0, duration: .6, stagger: .14, ease: "expo.out"}, d)
    .to(sp, {yPercent: -115, duration: .4, stagger: .06, ease: "power3.in"}, sai);
};
