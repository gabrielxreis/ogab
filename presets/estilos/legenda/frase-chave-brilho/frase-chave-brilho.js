// LEGENDA · frase com palavra-chave que brilha: frases em caixa normal revelando palavra por palavra; a palavra-chave
// de cada frase entra na cor da marca e recebe um reflexo de luz que passa por ela (degradê da própria cor, sem glow).
ESTILO["frase-chave-brilho"] = (it, C) => {
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
  C.css("frase-chave-brilho", `
    .fb{position:absolute;text-wrap:balance;left:${S.lado + 30}px;right:${S.lado + 30}px;text-align:center;font-family:"PalcoSans";font-weight:800;font-size:70px;
        line-height:1.16;color:#fff;text-shadow:0 5px 22px rgba(0,0,0,.5)}
    .fb span{display:inline-block;margin:0 .12em}
    .fb .k{background:linear-gradient(100deg,var(--dest) 0 36%,color-mix(in srgb,var(--dest) 30%,#fff) 50%,var(--dest) 64% 100%);background-size:320% 100%;
        background-position:100% 0;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;text-shadow:none;
        padding:.04em .04em .16em;margin-bottom:-.16em;filter:drop-shadow(0 5px 14px rgba(0,0,0,.45))}`);
  frases.forEach((f, i) => {
    const k = chave(f), ini = f[0].ini, fim = fimDe(i), b = C.el("div", "fb");
    b.style.top = lugar(ini, 175) + "px";
    f.forEach((p, j) => {
      const s = C.el("span", j === k ? "k" : "", b, C.esc(limpa(p.w))); b.append(" ");
      tl.fromTo(s, {opacity: 0, y: 18}, {opacity: 1, y: 0, duration: .2, ease: "power3.out"}, p.ini);
      if (j === k) tl.to(s, {backgroundPosition: "0% 0", duration: .8, ease: "power2.inOut"}, p.ini + .12);
    });
    tl.set(b, {autoAlpha: 0}, 0).set(b, {autoAlpha: 1}, ini).set(b, {autoAlpha: 0}, fim);
  });
};
