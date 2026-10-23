// PROVA · arquivo pessoal: molduras de papel claro (foto + data em itálico embaixo) entram uma a uma, em leque, fora do rosto.
// Sem foto no campo, desenha uma foto antiga ilustrada (fictícia) em tons gastos.
ESTILO["arquivo-pessoal"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, wN = 1000, hN = 400, fw = 300, fh = 350;
  C.css("arquivo-pessoal", `
    .ap{position:absolute;transform-origin:50% 0}
    .ap .fr{position:absolute;top:20px;width:${fw}px;height:${fh}px;background:#F4EFE4;border-radius:6px;padding:16px 16px 0;
        box-shadow:0 22px 50px rgba(0,0,0,.45)}
    .ap .ft{width:100%;height:${fw - 32}px;overflow:hidden;border-radius:2px;background:#9a8a70;position:relative}
    .ap .ft img{width:100%;height:100%;object-fit:cover;filter:saturate(.8) contrast(.95)}
    .ap .ft svg{position:absolute;inset:0;width:100%;height:100%}
    .ap .ft::after{content:"";position:absolute;inset:0;box-shadow:inset 0 0 40px rgba(60,40,10,.35)}
    .ap .dt{font-family:"PalcoSerif";font-style:italic;font-weight:600;font-size:34px;color:#2b2620;text-align:center;line-height:${fh - fw + 16}px}`);
  const r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const zc = [S.topo, r[1] - 36], zb = [r[3] + 36, H - S.baixo], z = (zb[1] - zb[0]) >= (zc[1] - zc[0]) ? zb : zc;
  const s = Math.min(1, (z[1] - z[0]) / hN, (W - 2 * S.lado) / wN);
  const b = C.el("div", "ap");
  Object.assign(b.style, {width: wN + "px", height: hN + "px", left: (W - wN) / 2 + "px", top: (z[0] + ((z[1] - z[0]) - hN * s) / 2) + "px",
                          transform: `scale(${s})`});
  // foto ilustrada (fictícia): céu desbotado, morros e uma pessoa pequena; muda de tom por índice
  const tons = [["#c9b48f", "#8f7b58", "#6d5c42"], ["#b9a7a0", "#7d7068", "#5a4f49"], ["#c4b98a", "#8a8a5e", "#5d6044"]];
  const ilustra = i => { const [c, m, p] = tons[i % 3];
    return `<svg viewBox="0 0 268 268" preserveAspectRatio="xMidYMid slice"><rect width="268" height="268" fill="${c}"/>
      <circle cx="${70 + i * 50}" cy="70" r="26" fill="#efe3c6" opacity=".8"/>
      <path d="M0 180 Q70 130 140 170 T268 160 V268 H0Z" fill="${m}"/><path d="M0 215 Q90 190 180 212 T268 205 V268 H0Z" fill="${p}"/>
      <circle cx="${120 + i * 15}" cy="150" r="11" fill="#3e352b"/><path d="M${108 + i * 15} 200 q12 -42 24 0z" fill="#3e352b"/></svg>`; };
  const itens = it.imagens || [], n = Math.max(1, itens.length), passo = Math.min(fw * .82, (wN - fw) / Math.max(1, n - 1));
  const x0 = (wN - (fw + passo * (n - 1))) / 2, tl = C.tl, d = it.de, f = it.ate, frs = [];
  itens.forEach((x, i) => {
    const rot = (i - (n - 1) / 2) * 5 + (i % 2 ? 1.5 : -1.5);
    const fr = C.el("div", "fr", b, `<div class="ft">${x.img ? `<img src="${C.esc(x.img)}">` : ilustra(i)}</div><div class="dt">${C.esc(x.data || "")}</div>`);
    Object.assign(fr.style, {left: (x0 + i * passo) + "px", zIndex: i + 1}); frs.push(fr);
    const em = typeof x.em === "number" ? x.em : d + i * .55;   // em = segundo do vídeo
    tl.set(fr, {y: 140, rotation: rot * 3, opacity: 0}, 0)
      .to(fr, {y: 0, rotation: rot, opacity: 1, duration: .6, ease: "expo.out"}, em);
  });
  tl.to(frs, {y: -60, opacity: 0, duration: .4, stagger: .05, ease: "power2.in"}, Math.max(d + 1.6, f - .5));
};
