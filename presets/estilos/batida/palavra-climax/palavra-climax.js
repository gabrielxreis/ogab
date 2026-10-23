// BATIDA · palavra clímax: palavra gigante em caixa alta passa da direita para a esquerda atrás da pessoa (camada atras);
// entra rápido, quase para no meio e sai rápido. Cor da marca com contorno escuro.
ESTILO["palavra-climax"] = (it, C) => {
  const P = C.P, W = P.w, pal = String(it.palavra || "").toUpperCase(), r = C.rostoEm(it.de);
  const tam = Math.min(P.h * .2, W * 1.05 / Math.max(3, pal.length) / .66);   // no meio do caminho a palavra cabe quase inteira
  C.css("palavra-climax", `
    .pcx{position:absolute;left:0;white-space:nowrap;font-family:"PalcoSans";font-weight:900;letter-spacing:-.05em;line-height:1;color:var(--dest);
         -webkit-text-stroke:8px rgba(18,16,14,.9);paint-order:stroke fill}`);
  const fh = r ? r[3] - r[1] : P.h * .2, y = Math.max(C.seguro.topo - 60, (r ? r[1] - fh * .35 : P.h * .25) - tam * .55);
  const e = C.el("div", "pcx", null, C.esc(pal)); e.style.fontSize = Math.round(tam) + "px"; e.style.top = Math.round(y) + "px";
  const larg = pal.length * tam * .66, tl = C.tl, d = it.de, f = it.ate, meio = (f - d);
  tl.set(e, {x: W + 20}, 0)
    .to(e, {x: (W - larg) / 2 + W * .06, duration: .45, ease: "expo.out"}, d)
    .to(e, {x: (W - larg) / 2 - W * .06, duration: Math.max(.3, meio - .85), ease: "none"}, d + .45)
    .to(e, {x: -larg - 40, duration: .4, ease: "power3.in"}, d + .45 + Math.max(.3, meio - .85));
};
