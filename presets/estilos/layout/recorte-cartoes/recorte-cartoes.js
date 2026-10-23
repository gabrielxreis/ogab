// LAYOUT · recorte com cartões: sala desfocada e escurecida pelo motor ("base" no estilo.json) + vinheta e bolhas de luz; título, cartões (imagem opcional) e selos de marca
// flutuam ATRÁS da pessoa recortada. Cartão: {texto, imagem?, em}; selo: {texto, imagem?, em} (imagem = arquivo oficial).
ESTILO["recorte-cartoes"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  C.css("recorte-cartoes", `
    .rc-veu{position:absolute;inset:0;background:radial-gradient(ellipse 75% 55% at 50% 42%, rgba(10,12,16,.15), rgba(6,7,10,.75))}
    .rc-bo{position:absolute;border-radius:50%;filter:blur(22px)}
    .rc-tit{position:absolute;left:${S.lado + 20}px;right:${S.lado + 20}px;text-align:center;font-weight:900;color:#fff;letter-spacing:-.035em;
            line-height:.98;text-shadow:0 12px 40px rgba(0,0,0,.55)}
    .rc-tit span{display:inline-block;margin:0 .12em}.rc-tit .d{color:var(--dest)}
    .rc-c{position:absolute;width:300px;border-radius:26px;background:rgba(255,255,255,.09);border:1.5px solid rgba(255,255,255,.24);
          box-shadow:0 26px 60px rgba(0,0,0,.55);padding:14px;color:#fff}
    .rc-c .im{height:170px;border-radius:16px;overflow:hidden;position:relative;
          background:linear-gradient(140deg, color-mix(in srgb, var(--dest) 75%, #0d0f14), #1a1e29 75%)}
    .rc-c .im img{width:100%;height:100%;object-fit:cover}
    .rc-c .im svg{position:absolute;left:50%;top:50%;width:64px;height:64px;transform:translate(-50%,-50%)}
    .rc-c .tx{font-weight:800;font-size:30px;line-height:1.15;margin:14px 6px 4px}
    .rc-l{position:absolute;height:82px;padding:0 30px 0 18px;border-radius:41px;background:#fff;color:#14161b;display:flex;align-items:center;
          gap:14px;font-weight:900;font-size:34px;box-shadow:0 18px 40px rgba(0,0,0,.45);white-space:nowrap}
    .rc-l i{width:46px;height:46px;border-radius:14px;background:var(--dest);flex:none}.rc-l img{height:46px}`);
  const tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 1, f - .45), mid = s => (typeof s === "string" ? s : s && (s.imagem || s.src)) || "";
  const veu = C.el("div", "rc-veu");
  [[.12, .2, 260, .35], [.85, .16, 200, .3], [.08, .62, 320, .22], [.9, .58, 240, .28], [.5, .08, 180, .2], [.72, .86, 300, .18]]
    .forEach(([x, y, t, o], i) => { const b = C.el("div", "rc-bo", veu); Object.assign(b.style, {left: x * W - t / 2 + "px", top: y * H - t / 2 + "px",
      width: t + "px", height: t + "px", opacity: o, background: i % 2 ? "var(--dest)" : "#ffcf9a"}); });
  tl.set(veu, {opacity: 0}, 0).to(veu, {opacity: 1, duration: .5, ease: "power2.out"}, d).to(veu, {opacity: 0, duration: .45, ease: "power2.in"}, sai);
  tl.to(veu.children, {x: "+=30", y: "-=20", duration: f - d, ease: "sine.inOut", stagger: .1}, d);
  // título no espaço acima da cabeça (pode passar atrás do cabelo: a pessoa fica por cima)
  const tit = String(it.titulo || ""), dq = String(it.destaque || "").toLowerCase(), alto = r[1] + 30 - S.topo;
  const tam = Math.max(56, Math.min(128, (W - 2 * S.lado - 40) * 2 / Math.max(6, tit.length) / .56, alto / 2 / 1.02));
  const t = C.el("div", "rc-tit", null, tit.split(/\s+/).filter(Boolean).map(w =>
    `<span class="${dq && w.toLowerCase().replace(/[^\p{L}\p{N}]/gu, "") === dq ? "d" : ""}">${C.esc(w)}</span>`).join(" "));
  Object.assign(t.style, {top: S.topo + 10 + "px", fontSize: Math.round(tam) + "px"});
  tl.fromTo(t.children, {y: 50, opacity: 0, filter: "blur(10px)"}, {y: 0, opacity: 1, filter: "blur(0px)", duration: .5, ease: "expo.out", stagger: .06}, d + .1)
    .to(t, {y: -50, opacity: 0, duration: .4, ease: "power2.in"}, sai);
  // cartões nas laterais da cabeça e selos mais abaixo, alternando lados; cada um flutua devagar
  const vc = [{x: S.lado + 10, y: r[1] + 40, rot: -6}, {x: W - S.lado - 310, y: r[1] + 170, rot: 5}];
  const vl = [{x: W - S.lado - 20, y: r[1] - 20, al: "dir", rot: 4}, {x: S.lado + 20, y: r[3] + 20, al: "esq", rot: -3},
              {x: W - S.lado - 20, y: r[3] + 70, al: "dir", rot: 3}];
  const pop = (el, rot, em, k) => {
    const flu = gsap.utils.wrap([12, -10, 14])(k);
    tl.set(el, {opacity: 0}, 0)
      .fromTo(el, {opacity: 0, y: 90, scale: .7, rotation: rot * 3}, {opacity: 1, y: 0, scale: 1, rotation: rot, duration: .55, ease: "back.out(1.6)"}, em)
      .to(el, {y: flu, duration: Math.max(.6, sai - em - .55), ease: "sine.inOut"}, em + .55)
      .to(el, {opacity: 0, y: flu - 60, duration: .4, ease: "power2.in"}, sai + k * .04);
  };
  (it.cartoes || []).slice(0, vc.length).forEach((x, i) => {
    const v = vc[i], c = C.el("div", "rc-c"), src = mid(x);
    c.innerHTML = `<div class="im">${src ? `<img src="${C.esc(src)}">` : `<svg viewBox="0 0 64 64"><circle cx="32" cy="32" r="30" fill="rgba(255,255,255,.9)"/><path d="M26 20 L46 32 L26 44Z" fill="#14161b"/></svg>`}</div><div class="tx">${C.esc(x.texto || "")}</div>`;
    Object.assign(c.style, {left: v.x + "px", top: v.y + "px"});
    pop(c, v.rot, typeof x.em === "number" ? x.em : d + .3 + i * .3, i);
  });
  (it.logos || []).slice(0, vl.length).forEach((x, i) => {
    const v = vl[i], l = C.el("div", "rc-l"), src = mid(x);
    l.innerHTML = (src ? `<img src="${C.esc(src)}">` : "<i></i>") + C.esc(x.texto || "");
    Object.assign(l.style, v.al === "dir" ? {right: W - v.x + "px", top: v.y + "px"} : {left: v.x + "px", top: v.y + "px"});
    pop(l, v.rot, typeof x.em === "number" ? x.em : d + .9 + i * .2, i + 2);
  });
};
