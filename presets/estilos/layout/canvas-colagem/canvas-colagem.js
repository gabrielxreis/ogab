// LAYOUT · canvas colagem: a sala some sob um canvas azul suave com pontinhos (abre em círculo); cartões de vídeo com borda
// branca entram inclinados em volta da pessoa recortada e adesivos colam nos cantos. Mídia: {imagem?, legenda, em}.
ESTILO["canvas-colagem"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  C.css("canvas-colagem", `
    .cc-fu{position:absolute;inset:0;background:radial-gradient(rgba(255,255,255,.55) 2.5px, transparent 3px) 0 0/40px 40px,
           linear-gradient(170deg,#DCEBFA,#B9D4F1 70%,#A9C8EC)}
    .cc-m{position:absolute;background:#fff;padding:14px 14px 58px;border-radius:10px;box-shadow:0 22px 50px rgba(30,60,100,.32)}
    .cc-m .im{width:100%;height:100%;border-radius:4px;overflow:hidden;position:relative;background:linear-gradient(150deg,#3a4256,#151922)}
    .cc-m .im img{width:100%;height:100%;object-fit:cover}
    .cc-m .im svg{position:absolute;left:50%;top:50%;width:70px;height:70px;transform:translate(-50%,-50%)}
    .cc-m .im b{position:absolute;left:0;right:0;bottom:0;height:8px;background:rgba(255,255,255,.25)}
    .cc-m .im b i{display:block;height:100%;width:38%;background:var(--dest)}
    .cc-m .lg{position:absolute;left:18px;right:18px;bottom:10px;font-family:"PalcoSerif";font-style:italic;font-weight:600;font-size:32px;color:#1d2433}
    .cc-a{position:absolute;padding:12px 28px;border-radius:40px;background:var(--dest);color:#111;font-weight:900;font-size:40px;
          border:6px solid #fff;box-shadow:0 12px 26px rgba(30,60,100,.3);white-space:nowrap}`);
  const tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 1, f - .45);
  const fu = C.el("div", "cc-fu");
  tl.set(fu, {clipPath: "circle(0% at 50% 40%)"}, 0)
    .to(fu, {clipPath: "circle(120% at 50% 40%)", duration: .6, ease: "power3.out"}, d)
    .to(fu, {clipPath: "circle(0% at 50% 40%)", duration: .45, ease: "power3.in"}, sai);
  // vagas: duas em cima (acima da cabeça) e duas nas laterais do pescoço; o corpo recortado cobre o que passar por trás
  const cima = Math.max(170, Math.min(330, r[1] - S.topo - 30)), vg = [
    {x: S.lado + 15, y: S.topo - 10, w: 430, h: cima, rot: -7}, {x: W - S.lado - 445, y: S.topo + 30, w: 430, h: cima, rot: 6},
    {x: 10, y: r[3] - 150, w: 320, h: 260, rot: 5}, {x: W - 330, y: r[3] - 90, w: 320, h: 260, rot: -6}];
  const ms = (it.midias || []).slice(0, vg.length), cards = [];
  ms.forEach((x, i) => {
    const v = vg[i], c = C.el("div", "cc-m"), src = typeof x === "string" ? x : x.imagem || x.src;
    c.innerHTML = `<div class="im">${src ? `<img src="${C.esc(src)}">` : `<svg viewBox="0 0 70 70"><circle cx="35" cy="35" r="33" fill="rgba(255,255,255,.92)"/><path d="M28 22 L50 35 L28 48Z" fill="#151922"/></svg><b><i></i></b>`}</div>
      <div class="lg">${C.esc(x.legenda || "")}</div>`;
    Object.assign(c.style, {left: v.x + "px", top: v.y + "px", width: v.w + "px", height: v.h + 72 + "px"}); cards.push(c);
    const em = typeof x.em === "number" ? x.em : d + .2 + i * .2;
    tl.set(c, {opacity: 0}, 0)
      .fromTo(c, {opacity: 0, scale: 1.3, rotation: v.rot * 3, y: 40}, {opacity: 1, scale: 1, rotation: v.rot, y: 0, duration: .5, ease: "back.out(1.5)"}, em)
      .to(c, {rotation: v.rot * .6, y: -10, duration: Math.max(.5, sai - em - .5), ease: "sine.inOut"}, em + .5);
  });
  (it.adesivos || []).slice(0, 4).forEach((x, i) => {
    const v = vg[i % vg.length], a = C.el("div", "cc-a", null, C.esc(x.texto || ""));
    Object.assign(a.style, v.x < W / 2 ? {left: Math.max(10, v.x - 10) + "px", top: v.y - 34 + "px"}   // canto de fora, no alto: longe do rosto e da legenda
                                       : {right: Math.max(10, W - v.x - v.w - 10) + "px", top: v.y - 34 + "px"});
    const em = typeof x.em === "number" ? x.em : d + 1 + i * .2, rot2 = v.x < W / 2 ? -10 : 9;
    tl.set(a, {opacity: 0}, 0).fromTo(a, {opacity: 0, scale: 2, rotation: rot2 * 2}, {opacity: 1, scale: 1, rotation: rot2, duration: .35, ease: "back.out(2.4)"}, em);
    cards.push(a);
  });
  tl.to(cards, {scale: .6, opacity: 0, duration: .35, ease: "power2.in", stagger: .03}, sai - .1);
};
