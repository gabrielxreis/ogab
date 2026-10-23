// LEGENDA · uma palavra por vez: cada palavra sozinha, grande, em caixa alta e sombra suave; palavra-chave na cor da marca.
ESTILO["uma-palavra"] = (it, C) => {
  const MAX = 1;
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
  C.css("uma-palavra", `
    .up{position:absolute;left:${S.lado}px;right:${S.lado}px;text-align:center;font-family:"PalcoSans";font-weight:900;letter-spacing:-.025em;
        line-height:1;color:#fff;text-shadow:0 10px 34px rgba(0,0,0,.5),0 2px 6px rgba(0,0,0,.35)}
    .up.k{color:var(--dest)}`);
  pal.forEach((p, i) => {
    const w = limpa(p.w).toUpperCase(), fs = Math.min(170, (W - 2 * S.lado - 60) / Math.max(2, w.length) / .72);
    const prox = i + 1 < pal.length ? pal[i + 1].ini : it.ate, fim = Math.min(it.ate, prox, p.fim + .35);
    const e = C.el("div", "up" + (chaves.has(norm(p.w)) ? " k" : ""), null, C.esc(w));
    Object.assign(e.style, {fontSize: fs + "px", top: lugar(p.ini, fs * 1.05) + "px"});
    tl.set(e, {autoAlpha: 0}, 0).set(e, {autoAlpha: 1}, p.ini)
      .fromTo(e, {scale: 1.14}, {scale: 1, duration: .16, ease: "power3.out"}, p.ini).set(e, {autoAlpha: 0}, fim);
  });
};
