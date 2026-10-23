// LEGENDA · sob o queixo: uma linha curta em caixa alta pequena colada logo abaixo do queixo, acompanhando o rosto.
ESTILO["sob-queixo"] = (it, C) => {
  const MAX = 3;
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
  C.css("sob-queixo", `
    .sq{position:absolute;white-space:nowrap;font-family:"PalcoSans";font-weight:800;font-size:44px;letter-spacing:.05em;color:#fff;
        background:rgba(12,12,14,.42);border-radius:14px;padding:6px 20px 8px;text-shadow:0 2px 10px rgba(0,0,0,.4)}
    .sq .k{color:var(--dest)}`);
  frases.forEach((f, i) => {
    const ini = f[0].ini, fim = fimDe(i), r = C.rostoEm(ini), txt = f.map(p => limpa(p.w).toUpperCase());
    const larg = txt.join(" ").length * 44 * .74 + 40, cx = r ? (r[0] + r[2]) / 2 : W / 2;
    const x = Math.max(S.lado + larg / 2, Math.min(W - S.lado - larg / 2, cx));
    let y = r ? r[3] + 22 : lugar(ini, 66);
    if (y + 66 > H - S.baixo) y = lugar(ini, 66);
    const b = C.el("div", "sq", null, f.map((p, j) => `<span class="${chaves.has(norm(p.w)) ? "k" : ""}">${C.esc(txt[j])}</span>`).join(" "));
    Object.assign(b.style, {left: x + "px", top: y + "px"});
    tl.set(b, {xPercent: -50, autoAlpha: 0}, 0).set(b, {autoAlpha: 1}, ini)
      .fromTo(b, {y: 12}, {y: 0, duration: .2, ease: "power3.out"}, ini).set(b, {autoAlpha: 0}, fim);
  });
};
