// LEGENDA · linha e soco: uma linha branca pequena com a fala e, embaixo, as palavras de impacto maiores na cor da marca,
// entrando do desfoque para o foco.
ESTILO["linha-e-soco"] = (it, C) => {
  const MAX = 6;
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
  C.css("linha-e-soco", `
    .ls{position:absolute;text-wrap:balance;left:${S.lado + 20}px;right:${S.lado + 20}px;text-align:center;font-family:"PalcoSans";color:#fff;text-shadow:0 5px 20px rgba(0,0,0,.5)}
    .ls .l{font-weight:700;font-size:48px;line-height:1.2}.ls .l span{display:inline-block;margin:0 .13em}
    .ls .s{font-weight:900;letter-spacing:-.03em;line-height:1.02;color:var(--dest);margin-top:6px}.ls .s span{display:inline-block;margin:0 .1em}`);
  frases.forEach((f, i) => {
    const k = chave(f), soco = f.slice(k, Math.min(f.length, k + 2)), resto = f.filter(p => !soco.includes(p)), ini = f[0].ini, fim = fimDe(i);
    const txt = soco.map(p => limpa(p.w).toUpperCase()).join(" "), fs = Math.min(124, (W - 2 * S.lado - 60) / Math.max(4, txt.length) / .7);
    const b = C.el("div", "ls"); b.style.top = lugar(ini, (resto.length ? 64 : 0) + fs * 1.05) + "px";
    if (resto.length) { const l = C.el("div", "l", b);
      resto.forEach(p => { const s = C.el("span", "", l, C.esc(limpa(p.w))); l.append(" ");
        tl.fromTo(s, {opacity: 0, y: 12}, {opacity: 1, y: 0, duration: .18, ease: "power3.out"}, p.ini); }); }
    const sl = C.el("div", "s", b); sl.style.fontSize = fs + "px";
    soco.forEach(p => { const s = C.el("span", "", sl, C.esc(limpa(p.w).toUpperCase())); sl.append(" ");
      tl.fromTo(s, {opacity: 0, scale: 1.12, filter: "blur(18px)"}, {opacity: 1, scale: 1, filter: "blur(0px)", duration: .35, ease: "expo.out"}, p.ini); });
    tl.set(b, {autoAlpha: 0}, 0).set(b, {autoAlpha: 1}, ini).set(b, {autoAlpha: 0}, fim);
  });
};
