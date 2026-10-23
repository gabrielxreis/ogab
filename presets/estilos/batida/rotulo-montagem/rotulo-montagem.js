// BATIDA · rótulo de montagem: selo no canto superior esquerdo (ponto da cor da marca + rótulo em caixa alta) com uma linha fina de
// subtítulo; abre por máscara da esquerda e fecha pelo mesmo caminho. Não cobre o rosto (fica no canto; se o rosto estiver lá, vai à direita).
ESTILO["rotulo-montagem"] = (it, C) => {
  const P = C.P, W = P.w, S = C.seguro;
  C.css("rotulo-montagem", `
    .rm{position:absolute;font-family:"PalcoSans";display:flex;flex-direction:column;gap:10px}
    .rm .sl{display:inline-flex;align-items:center;gap:18px;background:#fff;color:#111;border-radius:16px;padding:14px 26px 14px 22px;align-self:flex-start;
            font-weight:900;font-size:44px;text-transform:uppercase;letter-spacing:.03em;box-shadow:0 10px 30px rgba(0,0,0,.3)}
    .rm.dir .sl{align-self:flex-end}
    .rm .pt{width:22px;height:22px;border-radius:50%;background:var(--dest);flex:none}
    .rm .sb{font-weight:700;font-size:30px;color:#fff;text-shadow:0 3px 12px rgba(0,0,0,.6);padding-left:6px}`);
  const larg = 560, alto = 140, x = 60, y = S.topo + 20, r = C.rostoEm(it.de);
  const dir = r && r[0] < x + larg && r[1] < y + alto;   // rosto no canto: vai para a direita
  const box = C.el("div", "rm" + (dir ? " dir" : ""));
  Object.assign(box.style, dir ? {right: x + "px", top: y + "px", textAlign: "right"} : {left: x + "px", top: y + "px"});
  const sl = C.el("div", "sl", box, `<span class="pt"></span><span>${C.esc(it.rotulo || "")}</span>`);
  const sb = it.sub ? C.el("div", "sb", box, C.esc(it.sub)) : null;
  const pt = sl.firstElementChild, tl = C.tl, d = it.de, f = it.ate;
  tl.set(box, {opacity: 0}, 0).set(box, {opacity: 1}, d)
    .fromTo(sl, {clipPath: dir ? "inset(0 0 0 100%)" : "inset(0 100% 0 0)"}, {clipPath: "inset(0 0% 0 0%)", duration: .5, ease: "expo.out"}, d)
    .fromTo(pt, {scale: 0}, {scale: 1, duration: .35, ease: "expo.out"}, d + .2);
  if (sb) tl.fromTo(sb, {y: -10, opacity: 0}, {y: 0, opacity: 1, duration: .4, ease: "power3.out"}, d + .3);
  tl.to(box, {clipPath: dir ? "inset(0 0 0 100%)" : "inset(0 100% 0 0)", duration: .35, ease: "power3.in"}, Math.max(d + 1, f - .35));
};
