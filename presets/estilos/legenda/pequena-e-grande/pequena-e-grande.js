// LEGENDA · pequena e grande: palavras pequenas em minúsculas e, na linha do meio, a palavra-chave grande na cor da marca.
ESTILO["pequena-e-grande"] = (it, C) => {
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
  C.css("pequena-e-grande", `
    .pg{position:absolute;text-wrap:balance;left:${S.lado + 20}px;right:${S.lado + 20}px;text-align:center;font-family:"PalcoSans";color:#fff;text-shadow:0 5px 20px rgba(0,0,0,.5)}
    .pg .s{font-weight:700;font-size:48px;line-height:1.2}.pg .s span{display:inline-block;margin:0 .14em}
    .pg .g{font-weight:900;letter-spacing:-.04em;line-height:.98;color:var(--dest)}.pg .g span{display:inline-block}`);
  frases.forEach((f, i) => {
    const k = chave(f), ini = f[0].ini, fim = fimDe(i), w = limpa(f[k].w).toLowerCase();
    const fg = Math.min(150, (W - 2 * S.lado - 60) / Math.max(3, w.length) / .62);
    const antes = f.slice(0, k), depois = f.slice(k + 1), alt = (antes.length ? 60 : 0) + fg + (depois.length ? 60 : 0);
    const b = C.el("div", "pg"); b.style.top = lugar(ini, alt) + "px";
    const linha = (ps, cls) => { if (!ps.length) return; const l = C.el("div", cls, b);
      ps.forEach(p => { const s = C.el("span", "", l, C.esc(limpa(p.w).toLowerCase())); l.append(" ");
        tl.fromTo(s, {opacity: 0, y: 14}, {opacity: 1, y: 0, duration: .18, ease: "power3.out"}, p.ini); }); };
    linha(antes, "s");
    const gl = C.el("div", "g", b); gl.style.fontSize = fg + "px"; const gs = C.el("span", "", gl, C.esc(w));
    tl.fromTo(gs, {opacity: 0, y: 30, scale: .9}, {opacity: 1, y: 0, scale: 1, duration: .3, ease: "expo.out"}, f[k].ini);
    linha(depois, "s");
    tl.set(b, {autoAlpha: 0}, 0).set(b, {autoAlpha: 1}, ini).set(b, {autoAlpha: 0}, fim);
  });
};
