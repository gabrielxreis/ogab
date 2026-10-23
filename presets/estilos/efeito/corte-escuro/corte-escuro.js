// EFEITO · corte pelo escuro: íris preta de borda macia se fecha rápido num ponto escuro do quadro ("ponto" [x, y]; sem
// ele, o canto de cima mais longe do rosto), fica preto 2 quadros no "corte" e abre do mesmo ponto na cena seguinte.
// O empurrão de câmera de verdade fica com a LENTE (zoom no mesmo trecho), se quiser.
ESTILO["corte-escuro"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  C.css("corte-escuro", `
    .ce{position:absolute;border-radius:50%;box-shadow:0 0 0 ${Math.max(W, H) * 3}px #000,inset 0 0 90px 50px #000}
    .ce-v{position:absolute;inset:0;background:radial-gradient(circle at var(--x) var(--y), transparent 20%, rgba(0,0,0,.75) 75%)}`);
  const lado = (r[0] + r[2]) / 2 > W / 2 ? W * .16 : W * .84;
  const [px, py] = Array.isArray(it.ponto) ? it.ponto : [lado, S.topo + 140];
  const D = Math.hypot(Math.max(px, W - px), Math.max(py, H - py)) * 2 + 400;
  const v = C.el("div", "ce-v"), ir = C.el("div", "ce");
  v.style.setProperty("--x", px + "px"); v.style.setProperty("--y", py + "px");
  const d = it.de, corte = typeof it.corte === "number" ? it.corte : d + .45, fecha = Math.max(.25, corte - d), abre = .5;
  const tam = s => ({width: s, height: s, left: px - s / 2, top: py - s / 2});
  C.tl.set([v, ir], {opacity: 0}, 0).set(ir, Object.assign({opacity: 1}, tam(D)), d).set(v, {opacity: 0}, d)
    .to(v, {opacity: 1, duration: fecha, ease: "power2.in"}, d)
    .to(ir, Object.assign({duration: fecha, ease: "power3.in"}, tam(0)), d)
    .set(v, {opacity: 0}, corte + 2 / 24)
    .to(ir, Object.assign({duration: abre, ease: "power3.out"}, tam(D)), corte + 2 / 24)
    .set(ir, {opacity: 0}, corte + 2 / 24 + abre);
};
