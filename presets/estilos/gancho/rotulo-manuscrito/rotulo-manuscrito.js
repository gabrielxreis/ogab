// GANCHO · rótulo manuscrito: o fundo vira uma cor chapada (atrás da pessoa) com rótulo pequeno à mão + título grande em minúsculas;
// a sala fica num cartão arredondado embaixo do título.
ESTILO["rotulo-manuscrito"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const fundo = it.fundo || P.dest || "#F2D16B", hex = String(fundo).replace("#", "");
  const rgb = [0, 2, 4].map(i => parseInt(hex.substr(i, 2), 16) / 255);
  const tinta = hex.length === 6 && (.2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2]) < .45 ? "#fff" : "#141210";
  C.css("rotulo-manuscrito", `
    .rm-c{position:absolute;overflow:hidden}
    .rm-t{position:absolute;left:0;right:0;text-align:center;z-index:2}
    .rm-r{display:inline-block;font-family:"PalcoSerif";font-style:italic;font-weight:600;font-size:46px;letter-spacing:.08em;transform:rotate(-3deg)}
    .rm-r svg{display:block;width:100%;height:16px;margin-top:-2px}
    .rm-g{font-family:"PalcoSans";font-weight:900;letter-spacing:-.045em;line-height:.92;margin-top:18px}
    .rm-g div{overflow:hidden;padding-bottom:.08em}.rm-g span{display:inline-block}`);
  const tit = String(it.titulo || "").toLowerCase(), pal = tit.split(/\s+/);
  let l1 = tit, l2 = "";
  if (tit.length > 12 && pal.length > 1) {   // duas linhas equilibradas
    let best = 1e9;
    for (let k = 1; k < pal.length; k++) { const a = pal.slice(0, k).join(" "), b = pal.slice(k).join(" "), m = Math.max(a.length, b.length);
      if (m < best) { best = m; l1 = a; l2 = b; } }
  }
  const maior = Math.max(l1.length, l2.length), tam = Math.min(150, W * .88 / Math.max(5, maior) / .58);
  const box = C.el("div", "rm-t"); Object.assign(box.style, {top: S.topo + "px", color: tinta});
  const rot = C.el("div", "rm-r", box, `${C.esc(String(it.rotulo || "").toUpperCase())}<svg viewBox="0 0 100 10" preserveAspectRatio="none">
    <path d="M2 7 C 30 3, 60 9, 98 4" fill="none" stroke="${tinta}" stroke-width="3" stroke-linecap="round" vector-effect="non-scaling-stroke" pathLength="1"/></svg>`);
  const g = C.el("div", "rm-g", box, [l1, l2].filter(Boolean).map(l => `<div><span>${C.esc(l)}</span></div>`).join(""));
  g.style.fontSize = tam + "px";
  const linhas = l2 ? 2 : 1, topoCartao = S.topo + 46 + 34 + linhas * tam * 1.0 + 44;
  const cart = C.el("div", "rm-c"); cart.style.boxShadow = `0 0 0 3000px ${fundo}`;
  const alvo = {left: 54, top: topoCartao, width: W - 108, height: H - 230 - topoCartao, borderRadius: 54};
  const tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 1.2, f - .5), traco = rot.querySelector("path");
  tl.set(cart, {left: 0, top: 0, width: W, height: H, borderRadius: 0, opacity: 0}, 0).set(cart, {opacity: 1}, d)
    .to(cart, Object.assign({duration: .7, ease: "expo.out"}, alvo), d)
    .set(box, {opacity: 0}, 0).set(box, {opacity: 1}, d)
    .fromTo(rot, {y: 24, opacity: 0}, {y: 0, opacity: 1, duration: .45, ease: "power3.out"}, d + .15)
    .fromTo(traco, {strokeDasharray: 1, strokeDashoffset: 1}, {strokeDashoffset: 0, duration: .4, ease: "power2.out"}, d + .45)
    .fromTo(g.querySelectorAll("span"), {yPercent: 110}, {yPercent: 0, duration: .6, stagger: .1, ease: "expo.out"}, d + .25)
    .to(box, {y: -60, opacity: 0, duration: .4, ease: "power2.in"}, sai)
    .to(cart, {left: 0, top: 0, width: W, height: H, borderRadius: 0, duration: .5, ease: "power3.inOut"}, sai)
    .set(cart, {opacity: 0}, sai + .5);
};
