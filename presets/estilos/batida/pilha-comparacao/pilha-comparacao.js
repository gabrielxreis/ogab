// BATIDA · pilha de comparação: fichas brancas (marca, nome, para quem, preço na cor da marca) caem na hora de cada "em";
// a de baixo encolhe um pouco e escurece, então só a última fica em destaque e as anteriores aparecem como borda da pilha.
ESTILO["pilha-comparacao"] = (it, C) => {
  const P = C.P, W = P.w, itens = (it.itens || []).slice(0, 5), lado = 70, alto = 170, passo = 34;
  C.css("pilha-comparacao", `
    .pc{position:absolute;left:${lado}px;width:${W - 2 * lado}px;font-family:"PalcoSans"}
    .pc .fc{position:absolute;left:0;right:0;bottom:0;height:${alto}px;border-radius:34px;background:#fff;box-shadow:0 16px 44px rgba(0,0,0,.32);
            display:flex;align-items:center;gap:26px;padding:0 34px;box-sizing:border-box;transform-origin:50% 0}
    .pc .lg{width:104px;height:104px;border-radius:24px;flex:none;display:grid;place-items:center;overflow:hidden;font-weight:900;font-size:50px;color:#fff}
    .pc .lg img{width:100%;height:100%;object-fit:contain}
    .pc .tx{flex:1;min-width:0}.pc .nm{font-weight:900;font-size:40px;color:#15171a;line-height:1.1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .pc .pa{font-weight:600;font-size:29px;color:#5d6168;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .pc .pr{font-weight:900;font-size:48px;color:#111;background:var(--dest);padding:6px 20px;border-radius:16px;white-space:nowrap}`);
  const CORES = ["#15171a", "#3a4a5c", "#6b3d2e", "#2f4a3a", "#4a3a5c"];
  const total = alto + passo * (itens.length - 1), lim = P.h - C.seguro.baixo, r = C.rostoEm(it.de);
  let y = lim - total;
  if (r && r[3] + 40 + total <= lim) y = r[3] + 40; else if (r && r[1] - 40 - total >= C.seguro.topo) y = r[1] - 40 - total;
  const box = C.el("div", "pc"); box.style.top = y + "px"; box.style.height = total + "px";
  const tl = C.tl, d = it.de, f = it.ate;
  const fs = itens.map((p, i) => C.el("div", "fc", box, `<div class="lg" style="background:${p.logo ? "#fff" : CORES[i % 5]}">${p.logo
      ? `<img src="${C.esc(p.logo)}">` : C.esc(String(p.nome || "?").slice(0, 1).toUpperCase())}</div>
    <div class="tx"><div class="nm">${C.esc(p.nome || "")}</div><div class="pa">${C.esc(p.para ? (P.lingua === "en" ? "for " : "para ") + p.para : "")}</div></div>
    <div class="pr">${C.esc(p.preco || "")}</div>`));
  fs.forEach((e, i) => {
    const t = Math.max(d, Math.min(f - .6, it.itens[i].em != null ? +it.itens[i].em : d + i * .7));
    tl.set(e, {opacity: 0}, 0)
      .fromTo(e, {y: -140, opacity: 0}, {y: 0, opacity: 1, duration: .5, ease: "expo.out"}, t);
    for (let k = 0; k < i; k++)   // as de baixo sobem um degrau, encolhem e escurecem
      tl.to(fs[k], {y: -passo * (i - k), scale: 1 - .05 * (i - k), filter: `brightness(${1 - .12 * (i - k)})`, duration: .45, ease: "expo.out"}, t);
  });
  tl.to(box, {y: 50, opacity: 0, duration: .4, ease: "power3.in"}, Math.max(d + 1.2, f - .4));
};
