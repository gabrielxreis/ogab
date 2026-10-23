// BATIDA · citação no topo: aspas grandes em serifa na cor da marca; a frase (serifa itálica) entra palavra por palavra no ritmo
// da duração e o autor fecha com um traço. Faixa escura suave no topo para ler sobre qualquer fundo; fica acima da cabeça.
ESTILO["citacao-topo"] = (it, C) => {
  const P = C.P, W = P.w, ws = String(it.texto || "").split(/\s+/).filter(Boolean), r = C.rostoEm(it.de);
  const lim = r ? r[1] - 60 : P.h * .32, livre = Math.max(200, lim - C.seguro.topo);
  const tam = Math.max(46, Math.min(80, Math.sqrt((W - 180) * livre * .55 / Math.max(8, ws.join(" ").length)) / .78));
  C.css("citacao-topo", `
    .ct-bg{position:absolute;left:0;right:0;top:0;background:linear-gradient(180deg,rgba(0,0,0,.62),rgba(0,0,0,.35) 70%,rgba(0,0,0,0))}
    .ct{position:absolute;left:90px;right:90px;text-align:center;font-family:"PalcoSerif";font-style:italic;font-weight:600;color:#fff}
    .ct .aq{font-size:1.9em;line-height:.6;color:var(--dest);display:inline-block;vertical-align:-.42em;font-weight:600}
    .ct .w{display:inline-block;overflow:hidden;vertical-align:top;padding:.08em .02em .12em}.ct .w span{display:inline-block}
    .ct .au{font-family:"PalcoSans";font-style:normal;font-weight:800;font-size:30px;letter-spacing:.12em;text-transform:uppercase;color:#fff;opacity:.85;margin-top:18px}
    .ct .au:before{content:"";display:inline-block;width:46px;height:4px;background:var(--dest);vertical-align:middle;margin-right:16px;border-radius:2px}`);
  const bg = C.el("div", "ct-bg"); bg.style.height = Math.round(lim + 40) + "px";
  const box = C.el("div", "ct"); box.style.top = (C.seguro.topo + 10) + "px"; box.style.fontSize = Math.round(tam) + "px"; box.style.lineHeight = "1.18";
  const ab = C.el("span", "aq", box, "“");
  const pals = ws.map(w => { const e = C.el("span", "w", box, `<span>${C.esc(w)}</span>`); box.appendChild(document.createTextNode(" ")); return e.firstChild; });
  const fe = C.el("span", "aq", box, "”");
  const au = it.autor ? C.el("div", "au", box, C.esc(it.autor)) : null;
  const tl = C.tl, d = it.de, f = it.ate, janela = Math.max(.6, Math.min(2.2, (f - d) * .55)), passo = janela / Math.max(1, pals.length);
  tl.set([bg, box], {opacity: 0}, 0).to(bg, {opacity: 1, duration: .3, ease: "power2.out"}, d).set(box, {opacity: 1}, d)
    .fromTo(ab, {opacity: 0, scale: .5}, {opacity: 1, scale: 1, duration: .4, ease: "expo.out"}, d)
    .fromTo(pals, {yPercent: 135}, {yPercent: 0, duration: .4, ease: "expo.out", stagger: passo}, d + .15)
    .fromTo(fe, {opacity: 0, scale: .5}, {opacity: 1, scale: 1, duration: .4, ease: "expo.out"}, d + .15 + janela);
  if (au) tl.fromTo(au, {y: 14, opacity: 0}, {y: 0, opacity: .85, duration: .4, ease: "power3.out"}, d + .3 + janela);
  tl.to([box, bg], {opacity: 0, duration: .35, ease: "power2.in"}, Math.max(d + 1.2, f - .35));
};
