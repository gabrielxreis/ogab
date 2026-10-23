// LEGENDA · pílula na palavra-chave: frases curtas em até 2 linhas; a palavra-chave fica dentro de uma pílula branca que abre quando é dita.
ESTILO["pilula-chave"] = (it, C) => {
  const MAX = 4;
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
  C.css("pilula-chave", `
    .pk{position:absolute;text-wrap:balance;left:${S.lado + 50}px;right:${S.lado + 50}px;text-align:center;font-family:"PalcoSans";font-weight:800;font-size:68px;
        line-height:1.28;color:#fff;text-shadow:0 5px 22px rgba(0,0,0,.5)}
    .pk span{display:inline-block;margin:0 .1em}
    .pk .k{background:#fff;color:#111214;border-radius:999px;padding:0 .34em .04em;text-shadow:none;box-shadow:0 10px 26px rgba(0,0,0,.3)}`);
  frases.forEach((f, i) => {
    const k = chave(f), ini = f[0].ini, fim = fimDe(i), b = C.el("div", "pk");
    b.style.top = lugar(ini, 185) + "px";
    f.forEach((p, j) => {
      const s = C.el("span", j === k ? "k" : "", b, C.esc(limpa(p.w))); b.append(" ");
      if (j === k) tl.fromTo(s, {opacity: 0, scale: .6}, {opacity: 1, scale: 1, duration: .3, ease: "expo.out"}, p.ini);
      else tl.fromTo(s, {opacity: 0, y: 16}, {opacity: 1, y: 0, duration: .2, ease: "power3.out"}, p.ini);
    });
    tl.set(b, {autoAlpha: 0}, 0).set(b, {autoAlpha: 1}, ini).set(b, {autoAlpha: 0}, fim);
  });
};
