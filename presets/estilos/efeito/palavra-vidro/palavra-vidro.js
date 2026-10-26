// EFEITO · palavra de vidro: atrás da pessoa, uma cópia do vídeo (P.video) recortada no formato das letras, ampliada (refração),
// desfocada e clareada = vidro fosco; por cima, a mesma palavra só com reflexo em gradiente, borda de luz e um brilho que corre.
ESTILO["palavra-vidro"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const tl = C.tl, d = it.de, f = it.ate, uid = "pv" + Math.round(d * 1000);
  const pal = String(it.palavra || "").toUpperCase(), tam = Math.round(Math.min(W * .9 / Math.max(3, pal.length) / .6, H * .24));
  const base = Math.max(S.topo + tam * .8, r[1] + (r[3] - r[1]) * .38), cx = W / 2;   // linha de base na altura da testa (atrás da cabeça)
  C.css("palavra-vidro", `
    .pv{position:absolute;inset:0}
    .pv-sombra,.pv-luz{position:absolute;left:0;top:0;overflow:visible}
    .pv-vid{position:absolute;inset:0}
    .pv-vid video{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:fill;filter:blur(9px) brightness(.92) contrast(1.15) saturate(1.3)}
    .pv text{font-family:"PalcoSans";font-weight:900;letter-spacing:-.02em}`);
  const box = C.el("div", "pv");
  const txt = (attrs) => `<text x="${cx}" y="${base}" text-anchor="middle" font-size="${tam}" ${attrs}>${C.esc(pal)}</text>`;
  // sombra suave sob o vidro (dá volume) + definição do recorte em forma de texto
  C.el("div", null, box, `<svg class="pv-sombra" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <defs><clipPath id="${uid}c" clipPathUnits="userSpaceOnUse">${txt("")}</clipPath>
      <filter id="${uid}s" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur stdDeviation="18"/></filter></defs>
    <g class="pv-som">${txt(`fill="rgba(0,0,0,.35)" filter="url(#${uid}s)" transform="translate(0 22)"`)}</g></svg>`);
  const vb = C.el("div", "pv-vid", box); vb.style.clipPath = `url(#${uid}c)`;
  if (P.video) {
    const v = C.video(P.video, vb);
    v.style.transformOrigin = `${cx}px ${base - tam * .35}px`; v.style.transform = "scale(1.3) translateY(14%)";   // refração: sala ampliada dentro da letra
  }
  const luz = C.el("div", null, box, `<svg class="pv-luz" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><defs>
      <linearGradient id="${uid}g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".42"/>
        <stop offset=".45" stop-color="#fff" stop-opacity=".02"/><stop offset="1" stop-color="color-mix(in srgb, var(--dest) 60%, #fff)" stop-opacity=".22"/></linearGradient>
      <linearGradient id="${uid}b" x1="0" y1="0" x2="1" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
        <stop offset=".5" stop-color="#fff" stop-opacity=".85"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
    ${txt(`fill="none" stroke="rgba(10,14,22,.45)" stroke-width="9"`)}${txt(`fill="url(#${uid}g)" stroke="rgba(255,255,255,.9)" stroke-width="3"`)}
    <g clip-path="url(#${uid}c)"><rect class="pv-brilho" x="${-W * .4}" y="0" width="${W * .3}" height="${H}" fill="url(#${uid}b)" transform="skewX(-20)"/></g></svg>`).firstChild;
  const brilho = luz.querySelector(".pv-brilho"), som = box.querySelector(".pv-som");
  tl.set(box, {opacity: 0}, 0).set(box, {opacity: 1}, d)
    .fromTo([vb, luz, som], {y: 120, opacity: 0, filter: "blur(10px)"}, {y: 0, opacity: 1, filter: "blur(0px)", duration: .8, ease: "expo.out"}, d)
    .fromTo(brilho, {x: 0}, {x: W * 1.6, duration: 1.1, ease: "power2.inOut"}, d + .5)
    .to([vb, luz, som], {y: -50, opacity: 0, duration: .4, ease: "power2.in"}, Math.max(d + 1, f - .4));
};
