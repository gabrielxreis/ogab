// LAYOUT · espaço acima da cabeça: cartão escuro (linha pequena + título + etiquetas) que cabe na faixa livre entre o topo
// seguro e a cabeça; encolhe sozinho se o espaço for curto e flutua de leve até sair para cima.
ESTILO["espaco-acima"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  C.css("espaco-acima", `
    .ea{position:absolute;left:50%;width:${W - 2 * S.lado - 60}px;border-radius:34px;background:rgba(16,17,21,.8);border:1.5px solid rgba(255,255,255,.16);
        box-shadow:0 26px 60px rgba(0,0,0,.45);padding:30px 40px 34px;color:#fff;text-align:center}
    .ea .li{font-weight:800;font-size:28px;letter-spacing:.3em;text-transform:uppercase;color:var(--dest)}
    .ea .ti{font-weight:900;font-size:88px;line-height:1;letter-spacing:-.03em;margin-top:10px}
    .ea .et{display:flex;justify-content:center;flex-wrap:wrap;gap:14px;margin-top:22px}
    .ea .et span{padding:8px 24px;border-radius:30px;background:rgba(255,255,255,.1);border:1.5px solid rgba(255,255,255,.22);font-weight:700;font-size:32px}
    .ea .et span::before{content:"";display:inline-block;width:14px;height:14px;border-radius:50%;background:var(--dest);margin-right:12px;vertical-align:3px}`);
  const itens = it.itens || [], alto = 132 + 82 + (itens.length ? 76 : 0), livre = r[1] - 34 - S.topo;
  const esc = Math.max(.55, Math.min(1, livre / alto)), topo = S.topo + Math.max(0, (livre - alto * esc) / 2);
  const e = C.el("div", "ea"); e.style.top = topo + "px";
  e.innerHTML = `${it.linha ? `<div class="li">${C.esc(it.linha)}</div>` : ""}<div class="ti">${C.esc(it.titulo || "")}</div>
    ${itens.length ? `<div class="et">${itens.map(x => `<span>${C.esc(x.texto || x)}</span>`).join("")}</div>` : ""}`;
  const tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 1, f - .45), et = e.querySelectorAll(".et span");
  tl.set(e, {xPercent: -50, scale: esc, transformOrigin: "50% 0%", opacity: 0}, 0)
    .fromTo(e, {opacity: 0, y: -50, scale: esc * .9}, {opacity: 1, y: 0, scale: esc, duration: .55, ease: "back.out(1.5)"}, d)
    .to(e, {y: 12, duration: Math.max(.5, sai - d - .55), ease: "sine.inOut"}, d + .55)
    .to(e, {opacity: 0, y: -70, duration: .4, ease: "power2.in"}, sai);
  et.forEach((s, i) => {
    const em = typeof itens[i].em === "number" ? itens[i].em : d + .5 + i * .2;
    tl.set(s, {opacity: 0}, 0).fromTo(s, {opacity: 0, scale: .5}, {opacity: 1, scale: 1, duration: .3, ease: "back.out(2.5)"}, em);
  });
};
