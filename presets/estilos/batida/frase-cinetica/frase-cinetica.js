// BATIDA · frase cinética: corte para tela cheia (fundo liso cobre o quadro todo, então não há rosto para proteger); a frase se monta
// palavra a palavra no centro, em blocos que sobem por máscara; palavra com "icone" ganha um ícone desenhado (SVG) num círculo da cor da marca.
ESTILO["frase-cinetica"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro;
  const ICO = {
    tempo: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', video: '<rect x="3" y="6" width="13" height="12" rx="2"/><path d="M16 10l5-3v10l-5-3"/>',
    dinheiro: '<path d="M12 3v18M16.5 7.5c-1-1.3-2.6-2-4.5-2-2.5 0-4.2 1.3-4.2 3.2 0 4.6 9 2.4 9 7 0 1.9-1.9 3.3-4.8 3.3-2 0-3.8-.8-4.8-2.2"/>',
    coracao: '<path d="M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0 1 12 7.3 4.3 4.3 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10z"/>',
    raio: '<path d="M13 3L5 13.5h6L10 21l8-10.5h-6z"/>', olho: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
    check: '<path d="M4.5 12.5l5 5 10-11"/>', seta: '<path d="M4 12h15M13 6l6 6-6 6"/>'};
  C.css("frase-cinetica", `
    .fk-bg{position:absolute;inset:0}
    .fk{position:absolute;left:${S.lado + 50}px;right:${S.lado + 50}px;display:flex;flex-wrap:wrap;justify-content:center;align-items:center;column-gap:26px;row-gap:4px;font-family:"PalcoSans"}
    .fk .w{display:inline-flex;align-items:center;gap:20px;overflow:hidden;padding:.1em 0 .1em}
    .fk .w span{display:inline-block;font-weight:900;color:#fff;text-transform:uppercase;letter-spacing:-.03em;line-height:1}
    .fk .w.d span{color:var(--dest)}
    .fk .ic{flex:none;border-radius:50%;background:var(--dest);display:grid;place-items:center}
    .fk .ic svg{width:62%;height:62%;fill:none;stroke:#111;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}`);
  const ws = it.palavras || [], n = ws.length, letras = ws.reduce((a, p) => a + String(p.w || "").length + (p.icone ? 2 : 0), 0);
  const tam = Math.round(Math.max(80, Math.min(150, Math.sqrt((W - 2 * S.lado - 100) * (H - S.topo - S.baixo) * .35 / Math.max(10, letras)) / .7)));
  const bg = C.el("div", "fk-bg"); bg.style.background = it.fundo || "#111317";
  const box = C.el("div", "fk"); box.style.top = (S.topo + (H - S.topo - S.baixo) / 2) + "px"; box.style.transform = "translateY(-50%)";
  const tl = C.tl, d = it.de, f = it.ate;
  tl.set(bg, {opacity: 0}, 0).set(bg, {opacity: 1}, d).fromTo(bg, {clipPath: "inset(100% 0 0 0)"}, {clipPath: "inset(0% 0 0 0)", duration: .35, ease: "expo.out"}, d);
  ws.forEach((p, i) => {
    const e = C.el("div", "w" + (p.destaque ? " d" : ""), box), t = Math.max(d + .15, Math.min(f - .5, p.em != null ? +p.em : d + .2 + i * (f - d - .9) / Math.max(1, n)));
    let ic = null;
    if (p.icone && ICO[p.icone]) { ic = C.el("div", "ic", e, `<svg viewBox="0 0 24 24">${ICO[p.icone]}</svg>`); ic.style.width = ic.style.height = Math.round(tam * .9) + "px"; }
    const s = C.el("span", "", e, C.esc(p.w || "")); s.style.fontSize = tam + "px";
    tl.set(e, {opacity: 0}, 0).set(e, {opacity: 1}, t).fromTo(s, {yPercent: 120}, {yPercent: 0, duration: .45, ease: "expo.out"}, t);
    if (ic) tl.fromTo(ic, {scale: 0, rotate: -40}, {scale: 1, rotate: 0, duration: .45, ease: "expo.out"}, t + .05);
  });
  tl.to(box, {opacity: 0, y: -30, duration: .3, ease: "power3.in"}, Math.max(d + 1, f - .4))
    .to(bg, {clipPath: "inset(0 0 100% 0)", duration: .35, ease: "power3.in"}, Math.max(d + 1, f - .35));
};
