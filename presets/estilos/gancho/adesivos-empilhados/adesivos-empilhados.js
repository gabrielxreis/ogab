// GANCHO · adesivos empilhados: pílulas brancas de borda grossa, uma sobre a outra acima da cabeça, cada uma com nome em cor e vaga de logo.
ESTILO["adesivos-empilhados"] = (it, C) => {
  const P = C.P, W = P.w, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, P.h * .32, W * .68, P.h * .55];
  const itens = (it.itens || []).slice(0, 4), n = Math.max(1, itens.length), gap = 20;
  const livre = r[1] - 40 - S.topo, alt = Math.round(Math.max(72, Math.min(116, (livre - gap * (n - 1)) / n)));
  C.css("adesivos-empilhados", `
    .ae{position:absolute;left:50%;display:flex;align-items:center;background:#fff;border:9px solid #15161a;border-radius:999px;
        font-family:"PalcoSans";font-weight:900;letter-spacing:-.02em;white-space:nowrap;box-shadow:0 9px 0 #15161a,0 22px 44px rgba(0,0,0,.35)}
    .ae .lg{border-radius:50%;flex:none;display:grid;place-items:center;overflow:hidden;color:#fff;background:#15161a}
    .ae .lg img{width:100%;height:100%;object-fit:contain;background:#fff}`);
  const tl = C.tl, d = it.de, f = it.ate, els = [];
  itens.forEach((x, i) => {
    const nome = String(x.nome || ""), cor = x.cor || "color-mix(in srgb, var(--dest) 72%, #000)", lg = alt - 30;
    const fs = Math.min(alt * .6, (W - 2 * S.lado - lg - 90) / Math.max(3, nome.length) / .62);
    const e = C.el("div", "ae", null, `<div class="lg">${x.logo ? `<img src="${C.esc(x.logo)}">` : C.esc(nome.slice(0, 1).toUpperCase())}</div>
      <span>${C.esc(nome)}</span>`);
    Object.assign(e.style, {top: (S.topo + i * (alt + gap)) + "px", height: alt + "px", fontSize: fs + "px", gap: (alt * .2) + "px",
                            padding: `0 ${alt * .42}px 0 ${(alt - 18 - lg) / 2}px`, color: cor});
    Object.assign(e.firstChild.style, {width: lg + "px", height: lg + "px", fontSize: (lg * .5) + "px", background: x.logo ? "#fff" : cor});
    const rot = i % 2 ? 2.5 : -2.5, dx = i % 2 ? 26 : -26;
    tl.set(e, {xPercent: -50, x: dx, rotation: rot, opacity: 0}, 0)
      .fromTo(e, {scale: .5, opacity: 0, rotation: rot * 4}, {scale: 1, opacity: 1, rotation: rot, duration: .5, ease: "expo.out"}, d + i * .2);
    els.push(e);
  });
  tl.to(els.slice().reverse(), {y: -50, opacity: 0, duration: .35, stagger: .05, ease: "power2.in"}, Math.max(d + 1, f - .45));
};
