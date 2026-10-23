// LAYOUT · polaroid narrador (tela cheia, camada da frente): mesa escura com grade, o print/tela (campo imagem, ou uma página
// ilustrada) como cartão principal e o vídeo da própria pessoa (C.P.video) numa polaroid inclinada no canto de baixo,
// enquadrado no rosto, com legenda manuscrita na faixa branca.
ESTILO["polaroid-narrador"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  C.css("polaroid-narrador", `
    .pn{position:absolute;inset:0;background:linear-gradient(rgba(255,255,255,.045) 2px, transparent 2px) 0 0/60px 60px,
        linear-gradient(90deg, rgba(255,255,255,.045) 2px, transparent 2px) 0 0/60px 60px, radial-gradient(ellipse at 50% 30%, #2a2d35, #121317)}
    .pn-tela{position:absolute;left:${S.lado + 15}px;right:${S.lado + 15}px;border-radius:24px;background:#fff;overflow:hidden;box-shadow:0 30px 70px rgba(0,0,0,.55)}
    .pn-tela .bar{height:64px;background:#eceef1;display:flex;align-items:center;gap:10px;padding:0 22px}
    .pn-tela .bar i{width:16px;height:16px;border-radius:50%;background:#c9ccd2}
    .pn-tela .bar b{margin-left:16px;flex:1;height:40px;border-radius:20px;background:#fff;font-weight:700;font-size:24px;color:#6a6d74;line-height:40px;padding:0 18px}
    .pn-tela .co{position:absolute;left:0;right:0;top:64px;bottom:0}.pn-tela .co img{width:100%;height:100%;object-fit:cover;object-position:top}
    .pn-tela .il{padding:34px;display:grid;grid-template-columns:1fr 1fr;gap:24px}
    .pn-tela .il div{height:250px;border-radius:18px;background:#f0f1f3;border:2px solid #e2e4e8;position:relative}
    .pn-tela .il div:nth-child(2){background:color-mix(in srgb, var(--dest) 22%, #fff);border-color:var(--dest)}
    .pn-tela .il div::before{content:"";position:absolute;left:26px;right:40%;top:30px;height:22px;border-radius:11px;background:#c9ccd2}
    .pn-tela .il div::after{content:"";position:absolute;left:26px;top:80px;width:50%;height:60px;border-radius:10px;background:#9ea2aa}
    .pn-tela .il .lin{grid-column:1/3;height:26px;border-radius:13px;background:#e6e8eb;border:0}
    .pn-tela .il .lin::before,.pn-tela .il .lin::after{display:none}
    .pn-po{position:absolute;background:#fbfaf6;padding:20px 20px 0;box-shadow:0 30px 70px rgba(0,0,0,.6);border-radius:4px}
    .pn-po .ja{position:relative;overflow:hidden;background:#222}
    .pn-po .ja video{position:absolute;max-width:none}
    .pn-po .lg{height:92px;display:flex;align-items:center;justify-content:center;font-family:"PalcoHand","PalcoSerif";font-style:normal;font-size:50px;color:#1d1e22}`);
  const tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 1, f - .45), src = it.imagem || it.src;
  const pn = C.el("div", "pn"), tela = C.el("div", "pn-tela", pn);
  Object.assign(tela.style, {top: S.topo - 30 + "px", height: Math.round(H * .5) + "px"});
  tela.innerHTML = `<div class="bar"><i></i><i></i><i></i><b>${C.esc(it.titulo || "")}</b></div><div class="co">${src ? `<img src="${C.esc(src)}">`
    : `<div class="il"><div></div><div></div><div class="lin"></div><div class="lin" style="width:70%"></div><div></div><div></div></div>`}</div>`;
  // polaroid no canto de baixo à direita, por cima do canto do cartão; janela enquadra o rosto do vídeo
  const jw = 360, jh = 400, po = C.el("div", "pn-po", pn), ja = C.el("div", "ja", po);
  Object.assign(ja.style, {width: jw + "px", height: jh + "px"});
  C.el("div", "lg", po, C.esc(it.legenda || ""));
  Object.assign(po.style, {right: S.lado + 25 + "px", top: H - S.baixo - (jh + 112) + 30 + "px"});
  const fh = r[3] - r[1], esc = jh * .55 / fh, fx = (r[0] + r[2]) / 2, fy = (r[1] + r[3]) / 2;
  if (P.video) {
    const v = C.video(P.video, ja);
    Object.assign(v.style, {width: W * esc + "px", height: H * esc + "px", left: jw / 2 - fx * esc + "px", top: jh * .47 - fy * esc + "px"});
  }
  tl.set(pn, {clipPath: "inset(100% 0 0 0)"}, 0).to(pn, {clipPath: "inset(0% 0 0 0)", duration: .45, ease: "expo.out"}, d)
    .fromTo(tela, {y: -120, opacity: 0}, {y: 0, opacity: 1, duration: .55, ease: "back.out(1.3)"}, d + .05)
    .fromTo(po, {rotation: 16, scale: .6, y: 200}, {rotation: 5, scale: 1, y: 0, duration: .6, ease: "back.out(1.5)"}, d + .2)
    .to(po, {rotation: 3.5, duration: Math.max(.5, sai - d - .8), ease: "sine.inOut"}, d + .8)
    .to(pn, {clipPath: "inset(0 0 100% 0)", duration: .45, ease: "power3.in"}, sai);
};
