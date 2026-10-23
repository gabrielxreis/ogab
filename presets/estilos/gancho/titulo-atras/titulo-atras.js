// GANCHO · título atrás da cabeça: linha pequena em itálico + palavra gigante (cor da marca, contorno escuro) atrás da pessoa.
ESTILO["titulo-atras"] = (it, C) => {
  const P = C.P, W = P.w, r = C.rostoEm(it.de) || [W * .32, P.h * .32, W * .68, P.h * .55];
  C.css("titulo-atras", `
    .ta-box{position:absolute;left:0;right:0;text-align:center}
    .ta-l{font-family:"PalcoSerif";font-style:italic;font-weight:600;color:#fff;text-shadow:0 4px 18px rgba(0,0,0,.5)}
    .ta-t{font-weight:900;letter-spacing:-.045em;line-height:.86;color:var(--dest);-webkit-text-stroke:6px rgba(20,16,12,.85);paint-order:stroke fill;
          text-shadow:0 18px 50px rgba(0,0,0,.45)}
    .ta-t span{display:inline-block}`);
  const tit = String(it.titulo || "").toUpperCase(), tam = Math.min(W * .94 / Math.max(3, tit.length) / .82, P.h * .17);
  const fh = r[3] - r[1], topo = Math.max(C.seguro.topo, r[1] - fh * .55);
  const box = C.el("div", "ta-box"); box.style.top = topo + "px";
  const l = C.el("div", "ta-l", box, C.esc(it.linha || "")); l.style.fontSize = Math.round(tam * .3) + "px";
  const t = C.el("div", "ta-t", box, [...tit].map(c => `<span>${c === " " ? "&nbsp;" : C.esc(c)}</span>`).join(""));
  t.style.fontSize = Math.round(tam) + "px";
  const tl = C.tl, d = it.de, f = it.ate;
  tl.set(box, {opacity: 0}, 0).set(box, {opacity: 1}, d)
    .fromTo(l, {y: 30, opacity: 0}, {y: 0, opacity: 1, duration: .45, ease: "power3.out"}, d)
    .fromTo(t.children, {y: 70, scale: 1.25, opacity: 0, filter: "blur(14px)"},
            {y: 0, scale: 1, opacity: 1, filter: "blur(0px)", duration: .6, ease: "expo.out", stagger: .045}, d + .12)
    .to(box, {y: -40, opacity: 0, duration: .4, ease: "power2.in"}, Math.max(d + 1, f - .4));
};
