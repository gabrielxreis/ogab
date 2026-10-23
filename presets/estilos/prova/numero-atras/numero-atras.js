// PROVA · número atrás da cabeça: valor gigante na cor da marca (contorno escuro) com dígitos em rolo que giram e param no
// número falado (sinais como . , % R$ ficam fixos); linha pequena em itálico por cima. Camada atrás: a pessoa fica na frente.
ESTILO["numero-atras"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  C.css("numero-atras", `
    .na{position:absolute;left:0;right:0;text-align:center}
    .na-l{font-family:"PalcoSerif";font-style:italic;font-weight:600;color:#fff;text-shadow:0 4px 18px rgba(0,0,0,.5)}
    .na-n{font-weight:900;line-height:1;letter-spacing:-.03em;color:var(--dest);white-space:nowrap;
          -webkit-text-stroke:6px rgba(20,16,12,.85);paint-order:stroke fill;font-variant-numeric:tabular-nums}
    .na-n .dg{display:inline-block;height:1em;overflow:hidden;vertical-align:top;width:.64em;
          -webkit-mask-image:linear-gradient(transparent,#000 12%,#000 88%,transparent);mask-image:linear-gradient(transparent,#000 12%,#000 88%,transparent)}
    .na-n .dg b{display:block;font-weight:900}.na-n .dg b span{display:block;height:1em}
    .na-n .fx{display:inline-block;vertical-align:top}`);
  const num = String(it.numero || "0"), nd = [...num].filter(c => /\d/.test(c)).length;
  const larg = [...num].reduce((a, c) => a + (/\d/.test(c) ? .64 : (/[.,]/.test(c) ? .3 : .62)), 0);
  const tam = Math.min(W * .94 / Math.max(2, larg), H * .19);
  const fh = r[3] - r[1], topo = Math.max(C.seguro.topo, r[1] - fh * .62);
  const box = C.el("div", "na"); box.style.top = topo + "px";
  const l = C.el("div", "na-l", box, C.esc(it.legenda || "")); l.style.fontSize = Math.round(Math.min(64, tam * .32)) + "px";
  const n = C.el("div", "na-n", box); n.style.fontSize = Math.round(tam) + "px";
  const rolos = []; let k = 0;
  for (const c of num) {
    if (/\d/.test(c)) {   // rolo: 0-9 duas vezes; para em 10 + dígito (os da esquerda giram mais tempo)
      const dg = C.el("span", "dg", n, `<b>${[...Array(20)].map((_, i) => `<span>${i % 10}</span>`).join("")}</b>`);
      rolos.push({col: dg.firstChild, alvo: 10 + Number(c), i: k++});
    } else C.el("span", "fx", n, C.esc(c));
  }
  const tl = C.tl, d = it.de, f = it.ate;
  tl.set(box, {opacity: 0}, 0).set(box, {opacity: 1}, d)
    .fromTo(l, {y: 30, opacity: 0}, {y: 0, opacity: 1, duration: .45, ease: "power3.out"}, d)
    .fromTo(n, {y: 60, opacity: 0}, {y: 0, opacity: 1, duration: .5, ease: "expo.out"}, d + .05);
  rolos.forEach(o => {
    tl.set(o.col, {yPercent: 0}, 0)
      .to(o.col, {yPercent: -o.alvo * 5, duration: 1.1 + (nd - o.i) * .08, ease: "power3.out"}, d + .1);
  });
  tl.to(box, {y: -40, opacity: 0, duration: .4, ease: "power2.in"}, Math.max(d + 1.6, f - .4));
};
