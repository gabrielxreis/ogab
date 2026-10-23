// EFEITO · checklist ao lado da cabeça: cartão escuro compacto no lado com mais parede livre; cada item ganha check verde no "em".
ESTILO["checklist-lado"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, m = 34, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  C.css("checklist-lado", `
    .cl{position:absolute;background:rgba(16,17,20,.88);border:1.5px solid rgba(255,255,255,.14);border-radius:26px;padding:24px 26px 14px;
        box-shadow:0 22px 50px rgba(0,0,0,.45);color:#fff}
    .cl .t{font-weight:800;font-size:21px;letter-spacing:.24em;color:rgba(255,255,255,.62);padding-bottom:14px;margin-bottom:6px;
           border-bottom:3px solid var(--dest);display:inline-block}
    .cl .i{display:flex;align-items:center;gap:16px;font-weight:800;font-size:33px;line-height:1.1;margin:14px 0;overflow-wrap:anywhere}
    .cl .k{position:relative;flex:none;width:38px;height:38px;border-radius:50%;border:3px solid rgba(255,255,255,.3)}
    .cl .k i{position:absolute;inset:-3px;border-radius:50%;background:#22C55E;box-shadow:0 0 18px rgba(34,197,94,.55)}
    .cl .k svg{position:absolute;left:7px;top:9px;width:24px;height:20px}
    .cl .k path{fill:none;stroke:#fff;stroke-width:4;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:30;stroke-dashoffset:30}`);
  const esq = r[0] - m - S.lado, dir = W - S.lado - (r[2] + m), lado = Math.max(esq, dir);
  const c = C.el("div", "cl"), itens = it.itens || [];
  let x, y, w;
  if (lado >= 230) { w = Math.min(380, lado); x = dir >= esq ? r[2] + m : r[0] - m - w; y = Math.max(S.topo, r[1] + 20); }
  else { w = 440; x = (W - w) / 2; y = S.topo; }                    // sem parede ao lado: acima da cabeça
  Object.assign(c.style, {left: x + "px", top: y + "px", width: w + "px"});
  if (it.titulo) C.el("div", "t", c, C.esc(it.titulo));
  const tl = C.tl, d = it.de, f = it.ate, de = dir >= esq ? 50 : -50;
  tl.set(c, {opacity: 0}, 0).fromTo(c, {opacity: 0, x: de, scale: .92}, {opacity: 1, x: 0, scale: 1, duration: .45, ease: "back.out(1.6)"}, d);
  itens.forEach((o, i) => {
    const row = C.el("div", "i", c, `<span class="k"><i></i><svg viewBox="0 0 24 20"><path d="M3 10 L9 16 L21 3"/></svg></span><span>${C.esc(o.texto || "")}</span>`);
    const em = typeof o.em === "number" ? o.em : d + .5 + i * .8, txt = row.children[1];
    tl.set(row.querySelector("i"), {scale: 0, opacity: 0}, 0).set(txt, {opacity: .55}, 0)
      .to(row.querySelector("i"), {scale: 1, opacity: 1, duration: .3, ease: "back.out(2.4)"}, em)
      .to(row.querySelector("path"), {strokeDashoffset: 0, duration: .25, ease: "power2.out"}, em + .12)
      .to(txt, {opacity: 1, duration: .2}, em)
      .fromTo(row, {x: 0}, {x: 8, duration: .12, yoyo: true, repeat: 1, ease: "power1.out"}, em);
  });
  tl.to(c, {opacity: 0, y: -30, duration: .4, ease: "power2.in"}, Math.max(d + 1, f - .4));
};
