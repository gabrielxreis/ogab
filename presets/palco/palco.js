// PALCO: palavra gigante ATRÁS da pessoa (o recorte dela vai por cima desta camada), com subtítulo espaçado opcional.
CENA.mod.palco = function (itens, C) {
  const { tl, el, esc } = C;
  itens.forEach(a => {
    const t = el("div", "atras" + (a.estilo === "serifa" ? " serif" : ""), null, esc(a.texto));
    t.style.top = a.y + "px"; t.style.fontSize = a.tam + "px"; t.style.color = a.cor || "#fff";
    if (/^#(1|2|3)/.test(a.cor || "")) { t.style.textShadow = "none"; }
    if (a.desfocado) t.style.filter = "blur(3px)";
    tl.fromTo(t, { opacity: 0, scale: .84, filter: "blur(16px)" }, { opacity: 1, scale: 1, filter: a.desfocado ? "blur(3px)" : "blur(0px)", duration: .5, ease: "power3.out" }, a.de);
    tl.to(t, { scale: 1.06, duration: a.ate - a.de, ease: "none" }, a.de);
    tl.to(t, { opacity: 0, filter: "blur(12px)", duration: .3, ease: "power2.in" }, a.ate - .3);
    if (a.sub) {
      const s = el("div", "sub", null, esc(a.sub)); s.style.top = (a.y + a.tam * .98) + "px"; s.style.color = a.cor || "#fff";
      tl.fromTo(s, { opacity: 0, letterSpacing: "1.1em" }, { opacity: 1, letterSpacing: ".5em", duration: .6, ease: "power3.out" }, a.de + .25);
      tl.to(s, { opacity: 0, duration: .25 }, a.ate - .3);
    }
  });
};
