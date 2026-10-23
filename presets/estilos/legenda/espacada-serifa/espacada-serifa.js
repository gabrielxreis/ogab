// LEGENDA · espaçada + serifa: linha pequena em caixa alta bem espaçada com a fala e a palavra forte em serifa itálica grande,
// subindo de dentro de uma máscara.
ESTILO["espacada-serifa"] = (it, C) => {
  const MAX = 5;
  const P = C.P, W = P.w, H = P.h, S = C.seguro, tl = C.tl;
  const norm = s => String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]/g, "");
  const limpa = s => String(s).replace(/[,.;:]+$/, ""), chaves = new Set([].concat(it.chave || []).map(norm));
  const frases = [], pal = (P.palavras || []).filter(p => p.ini >= it.de - .05 && p.ini < it.ate);
  let g = [];   // frases curtas: quebra na pontuação ou a cada MAX palavras
  pal.forEach(p => { g.push(p); if (g.length >= MAX || /[.,!?;:]$/.test(p.w)) { frases.push(g); g = []; } });
  if (g.length) frases.push(g);
  const chave = f => { const i = f.findIndex(p => chaves.has(norm(p.w))); if (i >= 0) return i;   // sem chave pedida: a palavra mais longa
    let m = 0; f.forEach((p, k) => { if (norm(p.w).length > norm(f[m].w).length) m = k; }); return m; };
  const fimDe = i => Math.min(it.ate, i + 1 < frases.length ? frases[i + 1][0].ini : frases[i][frases[i].length - 1].fim + .5);
  const lugar = (t, alt) => {   // terço de baixo, acima da área segura; se o rosto desce até ali, logo abaixo do queixo ou acima da cabeça
    const r = C.rostoEm(t), base = H - S.baixo - 10; let y = base - alt;
    if (r && y < r[3] + 30) y = r[3] + 30 + alt <= base ? r[3] + 30 : Math.max(S.topo, r[1] - 30 - alt);
    return y; };
  C.css("espacada-serifa", `
    .es{position:absolute;text-wrap:balance;left:${S.lado + 20}px;right:${S.lado + 20}px;text-align:center;color:#fff;text-shadow:0 5px 20px rgba(0,0,0,.55)}
    .es .l{font-family:"PalcoSans";font-weight:700;font-size:32px;letter-spacing:.34em;line-height:1.4;margin-right:-.34em}
    .es .l span{display:inline-block;margin:0 .3em}
    .es .m{overflow:hidden;padding:0 .1em .16em;margin-top:2px}
    .es .w{display:inline-block;font-family:"PalcoSerif";font-style:italic;font-weight:600;line-height:1.02;color:var(--dest)}`);
  frases.forEach((f, i) => {
    const k = chave(f), ini = f[0].ini, fim = fimDe(i), w = limpa(f[k].w).toLowerCase(), resto = f.filter((p, j) => j !== k);
    const fs = Math.min(150, (W - 2 * S.lado - 80) / Math.max(3, w.length) / .5);
    const b = C.el("div", "es"); b.style.top = lugar(ini, (resto.length ? 50 : 0) + fs * 1.2) + "px";
    if (resto.length) { const l = C.el("div", "l", b);
      resto.forEach(p => { const s = C.el("span", "", l, C.esc(limpa(p.w).toUpperCase()));
        tl.fromTo(s, {opacity: 0}, {opacity: 1, duration: .25, ease: "power2.out"}, p.ini); }); }
    const m = C.el("div", "m", b), s = C.el("span", "w", m, C.esc(w)); s.style.fontSize = fs + "px";
    tl.fromTo(s, {yPercent: 110}, {yPercent: 0, duration: .5, ease: "expo.out"}, f[k].ini);
    tl.set(b, {autoAlpha: 0}, 0).set(b, {autoAlpha: 1}, ini).set(b, {autoAlpha: 0}, fim);
  });
};
