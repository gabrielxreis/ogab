// BATIDA · grade de resultados: duas fileiras de 3 cartões (prints do campo imagens) no maior espaço livre; a cada segundo a
// grade inteira vira para o próximo lote com um giro rápido em cascata. Sem imagens, cartões ilustrados de painel (número
// grande + gráfico) com os textos do campo valores (só prévia; prova real vem do cliente).
ESTILO["grade-resultados"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, COL = 3, GAP = 18;
  C.css("grade-resultados", `
    .gr{position:absolute;left:${S.lado}px;width:${W - 2 * S.lado}px;display:grid;grid-template-columns:repeat(${COL},1fr);gap:${GAP}px;perspective:1000px}
    .gr .cl{position:relative;transform-style:preserve-3d}
    .gr .ca{position:absolute;inset:0;border-radius:22px;overflow:hidden;background:#fff;box-shadow:0 14px 34px rgba(0,0,0,.4);backface-visibility:hidden;opacity:0}
    .gr .ca img{width:100%;height:100%;object-fit:cover;display:block}
    .gr .ca.il{padding:16px 18px;color:#111;display:flex;flex-direction:column;justify-content:space-between}
    .gr .ca.il b{font-weight:900;font-size:34px;letter-spacing:-.02em;line-height:1}
    .gr .ca.il span{font-weight:700;font-size:18px;color:#8a8f98}
    .gr .ca.il svg{width:100%;height:40%}`);
  const imgs = (it.imagens || []).filter(Boolean), vals = it.valores || [], qt = imgs.length || vals.length || 6;
  const r = C.rostoEm(it.de) || [W * .3, H * .3, W * .7, H * .55];
  const zonas = [[S.topo, r[1] - 30], [r[3] + 40, H - S.baixo]].sort((a, b) => (b[1] - b[0]) - (a[1] - a[0])), z = zonas[0];
  const cw = (W - 2 * S.lado - GAP * (COL - 1)) / COL, ch = Math.min(cw * 1.05, (z[1] - z[0] - GAP) / 2);
  const g = C.el("div", "gr"); Object.assign(g.style, {top: ((z[0] + z[1]) / 2 - ch - GAP / 2) + "px", gridAutoRows: ch + "px"});
  const lotes = Math.max(1, Math.ceil(qt / (COL * 2))), d = it.de, f = it.ate, tl = C.tl;
  const troca = Math.max(.8, Math.min(1, (f - d - .8) / lotes));   // ~1 s por lote
  const cards = [];
  for (let c = 0; c < COL * 2; c++) {
    const cel = C.el("div", "cl", g); cards.push([]);
    for (let l = 0; l < lotes; l++) {
      const k = l * COL * 2 + c, ca = C.el("div", "ca" + (imgs.length ? "" : " il"), cel);
      if (imgs.length) ca.innerHTML = `<img src="${C.esc(imgs[k % imgs.length])}">`;
      else {   // painel ilustrado: subida em linha com área clara
        const pts = [0, 1, 2, 3, 4, 5].map(j => `${j * 20},${40 - (8 + ((k * 7 + j * 13) % 11) + j * 4.5)}`).join(" ");
        ca.innerHTML = `<span>${P.lingua === "en" ? "result" : "resultado"} #${k + 1}</span><b>${C.esc(vals[k % Math.max(1, vals.length)] || "")}</b>
          <svg viewBox="0 0 100 40" preserveAspectRatio="none"><polygon points="0,40 ${pts} 100,40" fill="var(--dest)" opacity=".25"/>
          <polyline points="${pts}" fill="none" stroke="var(--dest)" stroke-width="3" stroke-linejoin="round"/></svg>`;
      }
      cards[c].push(ca);
    }
  }
  cards.forEach((pilha, c) => pilha.forEach((ca, l) => {
    const t0 = d + l * troca + c * .05;
    tl.fromTo(ca, {opacity: 0, rotationY: l ? -90 : 0, scale: l ? 1 : .7, y: l ? 0 : 40},
              {opacity: 1, rotationY: 0, scale: 1, y: 0, duration: l ? .28 : .4, ease: l ? "power2.out" : "back.out(1.6)", immediateRender: false}, t0 + (l ? .22 : 0));
    if (l < lotes - 1) tl.to(ca, {rotationY: 90, opacity: 0, duration: .22, ease: "power2.in"}, d + (l + 1) * troca + c * .05);
  }));
  tl.to(g, {opacity: 0, y: 40, duration: .4, ease: "power2.in"}, Math.max(d + 1, f - .4));
};
