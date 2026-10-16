// DESTAQUE: legenda palavra por palavra. Linhas: base (branca pequena), grande (amarela black), serifa (itálica amarela
// com brilhinhos), pequena, pilula (pílula branca; palavras com "marca" ganham marca-texto amarelo).
CENA.mod.destaque = function (grupos, C) {
  const { tl, el, esc } = C;
  grupos.forEach(g => {
    const box = el("div", "leg"); box.style.top = g.y + "px"; box.style.opacity = 0;
    tl.set(box, { opacity: 1 }, g.ini); tl.set(box, { opacity: 0 }, g.fim);
    g.linhas.forEach(l => {
      const ln = el("div", l.tipo, box);
      const alvo = l.tipo === "pilula" ? el("span", "pil", ln) : ln;
      if (l.tipo === "pilula") tl.fromTo(alvo, { opacity: 0, scale: .85 }, { opacity: 1, scale: 1, duration: .25, ease: "back.out(2)" }, l.palavras[0].ini - .05);
      l.palavras.forEach(p => {
        const w = el("span", "w" + (p.marca ? " marca" : ""), alvo, esc(p.w));
        if (l.tipo === "grande") tl.fromTo(w, { opacity: 0, scale: 1.35, y: 10 }, { opacity: 1, scale: 1, y: 0, duration: .32, ease: "back.out(2.4)" }, p.ini);
        else if (l.tipo === "serifa") tl.fromTo(w, { opacity: 0, filter: "blur(12px)", y: 14 }, { opacity: 1, filter: "blur(0px)", y: 0, duration: .4, ease: "power3.out" }, p.ini);
        else tl.fromTo(w, { opacity: 0, y: 16, scale: .94 }, { opacity: 1, y: 0, scale: 1, duration: .16, ease: "power2.out" }, p.ini);
        if (p.marca) tl.fromTo(w, { "--m": "0%" }, { "--m": "100%", duration: .3, ease: "power2.out" }, p.ini + .1);
      });
      if (l.tipo === "serifa" && g.brilho) {
        ln.style.position = "relative";
        [[-0.06, .1, 1], [1.02, -.15, .7], [.92, .95, .55]].forEach(([fx, fy, s], i) => {
          const b = el("span", "brilho", ln, "✦"); b.style.left = (fx * 100) + "%"; b.style.top = (fy * 100) + "%";
          tl.fromTo(b, { opacity: 0, scale: 0, rotation: -40 }, { opacity: 1, scale: s, rotation: 0, duration: .35, ease: "back.out(3)" }, l.palavras[0].ini + .15 + i * .08);
          tl.to(b, { rotation: 25, duration: Math.max(.1, g.fim - l.palavras[0].ini - .5), ease: "none" }, l.palavras[0].ini + .5);
        });
      }
    });
  });
};
