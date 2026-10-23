// LEGENDA · escada: as palavras descem em diagonal como degraus (uma por linha) no espaço vazio do quadro; a palavra-chave
// vem em serifa itálica grande e um sublinhado se desenha embaixo dela.
ESTILO["escada"] = (it, C) => {
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
  C.css("escada", `
    .ec{position:absolute;color:#fff;text-shadow:0 5px 20px rgba(0,0,0,.55)}
    .ec div{position:absolute;white-space:nowrap}
    .ec .p{font-family:"PalcoSans";font-weight:800}
    .ec .k{font-family:"PalcoSerif";font-style:italic;font-weight:600;color:var(--dest)}
    .ec .k svg{position:absolute;left:0;bottom:-.06em;width:100%;height:.16em;overflow:visible}`);
  frases.forEach((f, i) => {
    const k = chave(f), ini = f[0].ini, fim = fimDe(i), r = C.rostoEm(ini) || [W * .32, H * .32, W * .68, H * .55];
    // espaço vazio: lateral larga, ou o maior entre abaixo do queixo e acima da cabeça
    const esq = r[0] - S.lado - 30, dir = W - S.lado - 30 - r[2], base = H - S.baixo - 10;
    const vagas = [{x: S.lado + 20, y: r[3] + 30, w: W - 2 * S.lado - 40, h: base - r[3] - 30},
                   {x: S.lado + 20, y: S.topo, w: W - 2 * S.lado - 40, h: r[1] - 30 - S.topo}];
    if (Math.max(esq, dir) >= 420) vagas.push(esq >= dir ? {x: S.lado, y: r[1], w: esq, h: base - r[1], lat: 1}
                                                          : {x: r[2] + 30, y: r[1], w: dir, h: base - r[1], lat: 1});
    const v = vagas.sort((a, b) => (b.lat || 0) - (a.lat || 0) || b.h - a.h)[0];
    let fp = 52, fk = 104, lp = 64, lk = 122;
    const tot = (f.length - 1) * lp + lk, esc = Math.max(.62, Math.min(1, v.h / tot));
    fp *= esc; fk *= esc; lp *= esc; lk *= esc;
    const larg = f.map((p, j) => limpa(p.w).length * (j === k ? fk * .5 : fp * .62)), passo = Math.min(90 * esc, (v.w - Math.max(...larg)) / Math.max(1, f.length - 1));
    const totW = Math.max(...larg.map((l, j) => l + j * passo)), x0 = v.x + Math.max(0, (v.w - totW) / 2);
    const altT = (f.length - 1) * lp + lk, b = C.el("div", "ec"); Object.assign(b.style, {left: x0 + "px", top: v.y + Math.max(0, (v.h - altT) / 2) + "px"});
    let y = 0;
    f.forEach((p, j) => {
      const ek = j === k, e = C.el("div", ek ? "k" : "p", b, C.esc(limpa(p.w).toLowerCase()) + (ek ? `<svg viewBox="0 0 100 10" preserveAspectRatio="none">
        <path d="M1 6 C 30 2, 70 9, 99 4" fill="none" stroke="var(--dest)" stroke-width="${Math.round(fk * .07)}" stroke-linecap="round"
        vector-effect="non-scaling-stroke" pathLength="1"/></svg>` : ""));
      Object.assign(e.style, {left: j * passo + "px", top: y + "px", fontSize: (ek ? fk : fp) + "px", lineHeight: (ek ? lk : lp) + "px"});
      y += ek ? lk : lp;
      tl.fromTo(e, {opacity: 0, x: -30}, {opacity: 1, x: 0, duration: .28, ease: "power3.out"}, p.ini);
      if (ek) tl.fromTo(e.querySelector("path"), {strokeDasharray: 1, strokeDashoffset: 1}, {strokeDashoffset: 0, duration: .45, ease: "power2.out"}, p.ini + .2);
    });
    tl.set(b, {autoAlpha: 0}, 0).set(b, {autoAlpha: 1}, ini).set(b, {autoAlpha: 0}, fim);
  });
};
