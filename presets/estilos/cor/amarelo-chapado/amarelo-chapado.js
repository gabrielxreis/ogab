// COR · amarelo chapado: a sala some e o vídeo inteiro fica sobre um fundo amarelo-manteiga liso; atrás da pessoa, um
// cartão creme de borda branca grossa e sombra curta, e etiquetas pequenas (também de borda branca) longe do rosto.
ESTILO["amarelo-chapado"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro;
  C.css("amarelo-chapado", `
    .ac{position:absolute;inset:0;background:${it.fundo || "#F4D97E"}}
    .ac-c{position:absolute;border-radius:46px;background:#FBEFC6;border:14px solid #fff;box-shadow:0 14px 0 rgba(120,90,20,.18)}
    .ac-e{position:absolute;padding:20px 34px;border-radius:26px;background:#fff8e2;border:8px solid #fff;font-family:"PalcoSans";
          font-weight:800;font-size:44px;color:#2b2414;box-shadow:0 8px 0 rgba(120,90,20,.16);white-space:nowrap}
    .ac-e i{display:inline-block;width:22px;height:22px;border-radius:50%;background:var(--dest);margin-right:16px;vertical-align:middle}`);
  const r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .57];
  const fw = r[2] - r[0], cx = (r[0] + r[2]) / 2;
  const ac = C.el("div", "ac");
  // cartão atrás da pessoa: da altura da testa até o pé do quadro, mais largo que os ombros
  const cw = Math.min(W - 2 * S.lado - 40, fw * 2.6), ct = Math.max(S.topo - 40, r[1] - fh(r) * .35);
  const card = C.el("div", "ac-c", ac); Object.assign(card.style, {left: (cx - cw / 2) + "px", width: cw + "px", top: ct + "px", height: (H - ct + 80) + "px"});
  function fh(b) { return b[3] - b[1]; }
  const etq = (it.etiquetas || []).slice(0, 2), els = [];
  etq.forEach((t, i) => {   // etiquetas acima da cabeça, alternando os lados, sem tocar no rosto
    const e = C.el("div", "ac-e", ac, `<i></i>${C.esc(t)}`);
    const y = Math.max(S.topo, ct - 150 + i * 0) ;
    Object.assign(e.style, i % 2 ? {right: (S.lado + 30) + "px", top: (y + 70) + "px", transform: "rotate(3deg)"}
                                 : {left: (S.lado + 30) + "px", top: y + "px", transform: "rotate(-3deg)"});
    els.push(e);
  });
  const tl = C.tl, d = it.de, f = it.ate;
  tl.set(ac, {opacity: 0}, 0).set(ac, {opacity: 1}, d)
    .fromTo(card, {y: 160, scale: .94}, {y: 0, scale: 1, duration: .55, ease: "back.out(1.3)"}, d);
  els.forEach((e, i) => tl.fromTo(e, {y: -30, opacity: 0, scale: .85}, {y: 0, opacity: 1, scale: 1, duration: .4, ease: "back.out(2)"}, d + .35 + i * .18));
  if (f < P.dur - .05) tl.set(ac, {opacity: 0}, f);
};
