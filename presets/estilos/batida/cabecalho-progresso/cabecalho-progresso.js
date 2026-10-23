// BATIDA · cabeçalho de progresso: faixa no topo com título pequeno e os itens em linha; a cada "em" o item atual fica cheio
// (fundo na cor da marca), os já vistos ficam marcados e a barra de baixo anda até ele. Fica até o fim do trecho.
ESTILO["cabecalho-progresso"] = (it, C) => {
  const P = C.P, W = P.w, its = (it.itens || []).slice(0, 5), n = Math.max(1, its.length), lado = 60;
  C.css("cabecalho-progresso", `
    .cp{position:absolute;left:${lado}px;right:${lado}px;font-family:"PalcoSans"}
    .cp .tt{font-weight:800;font-size:28px;letter-spacing:.14em;text-transform:uppercase;color:#fff;opacity:.9;margin:0 0 12px 4px;text-shadow:0 2px 10px rgba(0,0,0,.5)}
    .cp .ln{display:flex;gap:10px;background:rgba(14,15,18,.72);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-radius:22px;padding:10px}
    .cp .it{flex:1;min-width:0;border-radius:14px;padding:16px 8px;text-align:center;font-weight:800;color:rgba(255,255,255,.55);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
            position:relative;z-index:1}
    .cp .it b{font-weight:900;margin-right:10px;opacity:.7}
    .cp .mk{position:absolute;top:10px;bottom:10px;left:10px;border-radius:14px;background:var(--dest)}
    .cp .br{height:6px;border-radius:3px;background:rgba(255,255,255,.25);margin-top:12px;overflow:hidden}.cp .br i{display:block;height:100%;background:var(--dest);transform-origin:left}`);
  const r = C.rostoEm(it.de), y = C.seguro.topo + 6;
  const box = C.el("div", "cp"); box.style.top = (r && r[1] < y + 200 ? Math.max(y - 100, 120) : y) + "px";
  if (it.titulo) C.el("div", "tt", box, C.esc(it.titulo));
  const ln = C.el("div", "ln", box); ln.style.position = "relative";
  const mk = C.el("div", "mk", ln), tam = Math.min(36, (W - 2 * lado - 20) / n / 7);
  const els = its.map((x, i) => { const e = C.el("div", "it", ln, `<b>${i + 1}</b>${C.esc(x.texto || "")}`); e.style.fontSize = Math.round(tam) + "px"; return e; });
  const br = C.el("div", "br", box, "<i></i>").firstChild;
  const tl = C.tl, d = it.de, f = it.ate, cel = (W - 2 * lado - 20 - 10 * (n - 1)) / n;
  mk.style.width = cel + "px";
  tl.set(box, {opacity: 0}, 0).fromTo(box, {y: -40, opacity: 0}, {y: 0, opacity: 1, duration: .45, ease: "expo.out"}, d)
    .set(mk, {opacity: 0, x: 0}, 0).set(br, {scaleX: 0}, 0);
  its.forEach((x, i) => {
    const t = Math.max(d + .2, Math.min(f - .5, x.em != null ? +x.em : d + .3 + i * (f - d - .8) / n));
    tl.to(mk, {opacity: 1, x: i * (cel + 10), duration: .45, ease: "expo.out"}, t)
      .to(els[i], {color: "#111", duration: .2, ease: "power2.out"}, t + .1)
      .to(br, {scaleX: (i + 1) / n, duration: .5, ease: "expo.out"}, t);
    if (i) tl.to(els[i - 1], {color: "rgba(255,255,255,.9)", duration: .2, ease: "power2.out"}, t);
  });
  tl.to(box, {y: -30, opacity: 0, duration: .35, ease: "power3.in"}, Math.max(d + 1, f - .35));
};
