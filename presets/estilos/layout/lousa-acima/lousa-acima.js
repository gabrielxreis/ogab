// LAYOUT · lousa acima da cabeça: frases grandes na parede livre acima da pessoa (camada atrás: a base do texto pode passar
// atrás do cabelo), uma por vez, palavra a palavra; *palavra* sai na cor da marca. Nada desce até o corpo.
ESTILO["lousa-acima"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  C.css("lousa-acima", `
    .la{position:absolute;left:${S.lado + 20}px;right:${S.lado + 20}px;text-align:center;font-weight:900;letter-spacing:-.035em;line-height:.98;
        text-shadow:0 8px 34px rgba(0,0,0,.45)}
    .la span{display:inline-block;margin:0 .11em}.la .d{color:var(--dest);font-family:"PalcoSerif";font-style:italic;font-weight:600;letter-spacing:-.01em}`);
  const fr = it.frases || [], topo = S.topo, fundo = r[1] + (r[3] - r[1]) * .12, alto = fundo - topo, larg = W - 2 * S.lado - 40;
  const tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 1, f - .45);
  fr.forEach((x, i) => {
    const txt = String(x.texto || x), tam = Math.max(60, Math.min(150, larg * 2 / Math.max(5, txt.replace(/\*/g, "").length) / .55, alto / 2.1));
    const e = C.el("div", "la", null, txt.split(/\s+/).filter(Boolean).map(w => /^\*.+\*[.,!?]?$/.test(w)
      ? `<span class="d">${C.esc(w.replace(/\*/g, ""))}</span>` : `<span>${C.esc(w)}</span>`).join(" "));
    Object.assign(e.style, {fontSize: Math.round(tam) + "px", color: it.cor || "#fff", top: topo + Math.max(0, (alto - tam * 2.05) / 2) + "px"});
    const em = typeof x.em === "number" ? x.em : d + .1 + i * (f - d) / Math.max(1, fr.length);
    tl.set(e.children, {opacity: 0}, 0)
      .fromTo(e.children, {opacity: 0, y: 40, filter: "blur(12px)"}, {opacity: 1, y: 0, filter: "blur(0px)", duration: .45, ease: "expo.out", stagger: .07}, em);
    const prox = fr[i + 1] ? (typeof fr[i + 1].em === "number" ? fr[i + 1].em : em + (f - d) / fr.length) - .3 : sai;
    tl.to(e, {opacity: 0, y: -50, duration: .3, ease: "power2.in"}, prox);
  });
};
