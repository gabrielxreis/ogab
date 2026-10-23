// EFEITO · salta do celular (motion puro, sem pessoa): fundo escuro próprio, celular entra inclinado em 3D e o cartão
// (titulo/sub ou imagem) sai da tela, passa por cima da borda de cima e fica flutuando na frente do aparelho.
ESTILO["celular-salta"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, cw = Math.round(W * .56), chh = Math.round(cw * 2.04);
  C.css("celular-salta", `
    .cs{position:absolute;inset:0;perspective:1800px;background:radial-gradient(120% 80% at 50% 35%,#1b2a22 0%,#0b100d 55%,#050706 100%)}
    .cs-g{position:absolute;left:50%;top:58%;width:${W * .9}px;height:${W * .9}px;margin:${-W * .45}px 0 0 ${-W * .45}px;border-radius:50%;
          background:radial-gradient(circle,color-mix(in srgb,var(--dest) 32%,transparent) 0%,transparent 62%);filter:blur(30px)}
    .cs-p{position:absolute;left:50%;top:50%;width:${cw}px;height:${chh}px;margin:${-chh * .42}px 0 0 ${-cw / 2}px;border-radius:${cw * .16}px;
          background:#0d0e10;box-shadow:0 0 0 3px #2a2c31,0 0 0 9px #0d0e10,0 60px 140px rgba(0,0,0,.7);transform-style:preserve-3d}
    .cs-s{position:absolute;inset:16px;border-radius:${cw * .13}px;overflow:hidden;background:linear-gradient(170deg,#1d2b24,#0f1512)}
    .cs-s i{position:absolute;left:8%;right:8%;height:${chh * .1}px;border-radius:22px;background:rgba(255,255,255,.07)}
    .cs-n{position:absolute;top:28px;left:50%;width:${cw * .3}px;height:34px;margin-left:${-cw * .15}px;border-radius:20px;background:#050506;z-index:2}
    .cs-c{position:absolute;left:50%;top:50%;width:${cw * 1.0}px;margin-left:${-cw * .5}px;padding:40px 30px;border-radius:40px;text-align:center;
          background:linear-gradient(160deg,rgba(255,255,255,.96),rgba(236,242,238,.92));box-shadow:0 30px 80px rgba(0,0,0,.55);color:#0b0f0d}
    .cs-c b{display:block;font-family:"PalcoSans";font-weight:900;font-size:${Math.min(cw * .3, cw * .92 / Math.max(3, String(it.titulo || '').length) / .62)}px;line-height:.9;white-space:nowrap;letter-spacing:-.04em;color:#0b0f0d}
    .cs-c b em{font-style:normal;color:var(--dest);-webkit-text-stroke:3px #0b0f0d;paint-order:stroke fill}
    .cs-c span{display:block;margin-top:14px;font-family:"PalcoSans";font-weight:700;font-size:${cw * .068}px;color:#36403b}
    .cs-c img{display:block;max-width:100%;max-height:${chh * .35}px;margin:0 auto;border-radius:20px}`);
  const fundo = C.el("div", "cs"), luz = C.el("div", "cs-g", fundo), cel = C.el("div", "cs-p", fundo);
  const tela = C.el("div", "cs-s", cel); C.el("div", "cs-n", cel);
  [.12, .27, .42, .57, .72].forEach(y => { const b = C.el("i", "", tela); b.style.top = (y * 100) + "%"; });
  const tit = C.esc(it.titulo || ""), m = tit.match(/^([+\-]?)(.*)$/);
  const card = C.el("div", "cs-c", fundo, it.imagem ? `<img src="${C.esc(it.imagem)}">` :
    `<b>${m[1] ? `<em>${m[1]}</em>` : ""}${m[2]}</b>${it.sub ? `<span>${C.esc(it.sub)}</span>` : ""}`);
  const tl = C.tl, d = it.de, f = it.ate, topoCel = H * .5 - chh * .42;
  tl.set(fundo, {opacity: 0}, 0).set(fundo, {opacity: 1}, d)
    .fromTo(luz, {opacity: 0, scale: .6}, {opacity: 1, scale: 1, duration: .8, ease: "power2.out"}, d)
    .fromTo(cel, {y: H * .35, rotationX: 38, rotationZ: -8, scale: .9}, {y: 0, rotationX: 14, rotationZ: -3, scale: 1, duration: .75, ease: "expo.out"}, d)
    // o cartão nasce DENTRO da tela (pequeno, achatado) e salta para fora por cima da borda de cima
    .fromTo(card, {y: chh * .1, scale: .55, rotationX: 14, opacity: 0, boxShadow: "0 0 0 rgba(0,0,0,0)"},
            {opacity: 1, duration: .2}, d + .55)
    .to(card, {y: topoCel - H * .5 + chh * .02, scale: 1.12, rotationX: -6, rotationZ: 3, duration: .6, ease: "back.out(1.6)",
               boxShadow: "0 60px 120px rgba(0,0,0,.6)"}, d + .7)
    .to(card, {y: "+=18", rotationZ: 1, duration: Math.max(.3, f - d - 1.8), ease: "sine.inOut"}, d + 1.3)
    .to(cel, {rotationX: 8, duration: Math.max(.3, f - d - 1.4), ease: "sine.inOut"}, d + .75)
    .to([card, cel, luz], {opacity: 0, y: "-=40", duration: .35, ease: "power2.in"}, f - .35)
    .set(fundo, {opacity: 0}, f);
};
