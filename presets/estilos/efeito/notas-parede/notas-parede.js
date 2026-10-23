// EFEITO · notas na parede: bilhetes de papel (fita adesiva, leve rotação) colam em volta da cabeça, um por item, fugindo do rosto.
ESTILO["notas-parede"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, nw = 420;
  C.css("notas-parede", `
    .np{position:absolute;width:${nw}px;padding:30px 30px 34px;background:#F6F1E6;color:#1c1b19;border-radius:6px;
        box-shadow:0 18px 40px rgba(0,0,0,.35);font-family:"PalcoSans";font-weight:800;font-size:40px;line-height:1.12;overflow-wrap:anywhere}
    .np::before{content:"";position:absolute;top:-16px;left:50%;width:120px;height:34px;transform:translateX(-50%) rotate(-3deg);
        background:color-mix(in srgb, var(--dest) 55%, transparent);border-radius:3px}`);
  const itens = it.itens || [], r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55], m = 30;
  // vagas sem cobrir o rosto: faixa acima da cabeça em 2 colunas (quantas linhas couberem) + laterais quando há espaço real
  const vagas = [], alt = 150, topoMax = r[1] - 30;
  for (let y = S.topo, k = 0; y + alt <= topoMax; y += alt + 18, k++)
    [[W / 2 - nw - 20, -3 + k], [W / 2 + 20, 3 - k]].forEach(([x, rot]) => vagas.push({x: x + (k % 2 ? 40 : -20), y, rot, w: nw}));
  const esq = r[0] - m - S.lado, dir = W - S.lado - (r[2] + m);
  if (esq >= 220) vagas.push({x: S.lado, y: r[1] + 40, rot: -4, w: Math.min(nw, esq)});
  if (dir >= 220) vagas.push({x: r[2] + m, y: r[1] + 120, rot: 3.5, w: Math.min(nw, dir)});
  if (!vagas.length) vagas.push({x: (W - nw) / 2, y: S.topo, rot: -2, w: nw});
  const tl = C.tl, notas = [];
  itens.forEach((x, i) => {
    const v = vagas[i % vagas.length], n = C.el("div", "np", null, C.esc(x.texto || ""));
    Object.assign(n.style, {left: v.x + "px", top: v.y + "px", width: v.w + "px"}); notas.push(n);
    const em = typeof x.em === "number" ? x.em : it.de + .1 + i * .8;   // em = segundo do vídeo
    tl.set(n, {opacity: 0, scale: 1.25, rotation: v.rot * 3}, 0)
      .to(n, {opacity: 1, scale: 1, rotation: v.rot, duration: .45, ease: "back.out(2)"}, em);
  });
  tl.to(notas, {y: -60, opacity: 0, duration: .4, stagger: .06, ease: "power2.in"}, Math.max(it.de + 1, it.ate - .5));
};
