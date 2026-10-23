// BATIDA · calendário voltando no tempo: widget branco arredondado (mês pequeno, ano grande) vira o ano para trás em saltos que
// aceleram até o ano alvo; no fim uma pílula na cor da marca diz "há X anos". Fora do rosto, no maior espaço livre.
ESTILO["calendario-ano"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, LW = 420, LH = 330;
  C.css("calendario-ano", `
    .ca{position:absolute;width:${LW}px;height:${LH}px;transform-origin:50% 50%;perspective:900px}
    .ca .wd{position:absolute;inset:0;border-radius:64px;background:#fff;box-shadow:0 26px 60px rgba(0,0,0,.4);overflow:hidden;color:#111}
    .ca .ms{position:absolute;left:46px;top:40px;font-weight:800;font-size:30px;letter-spacing:.14em;color:#8a8f98;text-transform:uppercase}
    .ca .ms i{display:inline-block;width:14px;height:14px;border-radius:50%;background:var(--dest);margin-right:12px;vertical-align:2px}
    .ca .an{position:absolute;left:0;right:0;top:88px;height:150px;transform-style:preserve-3d}
    .ca .an b{position:absolute;left:44px;top:0;font-weight:900;font-size:148px;line-height:1;letter-spacing:-.05em;opacity:0;backface-visibility:hidden;
        transform-origin:50% 60%}
    .ca .ln{position:absolute;left:46px;right:46px;bottom:52px;height:8px;border-radius:6px;background:#eceef1;overflow:hidden}
    .ca .ln i{position:absolute;inset:0;background:var(--dest);transform-origin:100% 50%}
    .ca .pl{position:absolute;left:50%;top:${LH - 34}px;transform:translateX(-50%);white-space:nowrap;background:var(--dest);color:#111;border-radius:40px;
        padding:12px 30px;font-weight:900;font-size:40px;box-shadow:0 14px 34px rgba(0,0,0,.35);opacity:0}`);
  const fim = Math.round(Number(it.ano) || new Date().getFullYear()), qt = Math.max(1, Math.round(Number(it.anos) || 10)), alvo = fim - qt;
  const r = C.rostoEm(it.de) || [W * .3, H * .3, W * .7, H * .55];
  const cima = r[1] - 30 - S.topo, baixo = H - S.baixo - (r[3] + 40), tot = LH + 50;
  const zona = cima >= baixo ? [S.topo, r[1] - 30] : [r[3] + 40, H - S.baixo], esc = Math.min(1, (zona[1] - zona[0]) / tot);
  const e = C.el("div", "ca");
  Object.assign(e.style, {left: (W - LW) / 2 + "px", top: (zona[0] + (zona[1] - zona[0] - tot * esc) / 2 - LH * (1 - esc) / 2) + "px"});
  // saltos: no máximo 7 anos mostrados, sempre começando no ano de hoje e terminando no alvo
  const k = Math.min(qt, 6), anos = []; for (let i = 0; i <= k; i++) anos.push(Math.round(fim - qt * i / k));
  e.innerHTML = `<div class="wd"><div class="ms"><i></i>${C.esc(it.mes || "")}</div><div class="an">${anos.map(a => `<b>${a}</b>`).join("")}</div>
    <div class="ln"><i></i></div></div><div class="pl">${C.esc(it.rotulo || (P.lingua === "en" ? qt + " years ago" : "há " + qt + " anos"))}</div>`;
  const tl = C.tl, d = it.de, f = it.ate, bs = [...e.querySelectorAll(".an b")], ln = e.querySelector(".ln i"), pl = e.querySelector(".pl");
  tl.fromTo(e, {opacity: 0, scale: esc * .7, y: 40}, {opacity: 1, scale: esc, y: 0, duration: .55, ease: "back.out(1.5)"}, d)
    .to(bs[0], {opacity: 1, duration: .001}, d);
  let t = d + .75;
  bs.forEach((b, i) => {   // cada salto: o ano atual tomba para cima, o anterior chega de baixo; os saltos ficam mais curtos
    if (!i) return;
    const dd = Math.max(.14, .34 - i * .04);
    tl.to(bs[i - 1], {rotationX: 90, opacity: 0, duration: dd, ease: "power2.in"}, t)
      .fromTo(b, {rotationX: -90, opacity: 0}, {rotationX: 0, opacity: 1, duration: dd, ease: "power2.out", immediateRender: false}, t + dd * .6);
    t += dd * 1.25;
  });
  tl.fromTo(ln, {scaleX: 0}, {scaleX: 1, duration: t - d - .75, ease: "power1.in"}, d + .75)
    .to(e, {scale: esc * 1.05, duration: .12, yoyo: true, repeat: 1}, t)
    .fromTo(pl, {opacity: 0, y: 20, scale: .8}, {opacity: 1, y: 0, scale: 1, duration: .4, ease: "back.out(2)", immediateRender: false}, t + .05)
    .to(e, {opacity: 0, y: -30, duration: .4, ease: "power2.in"}, Math.max(t + .8, f - .4));
};
