// BATIDA · contador de série: no topo, pílula escura fixa com o título da série e o contador "01/10" na cor da marca; abaixo,
// um rótulo grande por item (entra de baixo, sai para cima quando chega o próximo, o número do contador rola junto).
// itens: [{texto, em}] (em = segundo do vídeo; sem ele, divide o trecho por igual). inicio = número do primeiro item.
ESTILO["contador-serie"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro;
  C.css("contador-serie", `
    .cs{position:absolute;left:0;width:${W}px;display:flex;justify-content:center}
    .cs .pl{display:flex;align-items:center;gap:22px;background:rgba(16,17,20,.72);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
        border:1.5px solid rgba(255,255,255,.14);border-radius:50px;padding:14px 18px 14px 34px;box-shadow:0 16px 40px rgba(0,0,0,.35)}
    .cs .ti{font-weight:800;font-size:38px;letter-spacing:.01em;white-space:nowrap}
    .cs .nn{position:relative;height:58px;min-width:150px;border-radius:34px;background:var(--dest);color:#111;font-weight:900;font-size:34px;overflow:hidden}
    .cs .nn b{position:absolute;left:0;right:0;top:9px;text-align:center;opacity:0}
    .cs-r{position:absolute;left:${S.lado}px;right:${S.lado}px;text-align:center;font-weight:900;letter-spacing:-.03em;line-height:1;color:#fff;
        text-shadow:0 6px 30px rgba(0,0,0,.5);opacity:0;white-space:nowrap}`);
  const itens = (it.itens || []).map(x => typeof x === "string" ? {texto: x} : x), n = itens.length;
  const tot = Math.max(n, Math.round(Number(it.total) || n)), ini = Math.round(Number(it.inicio) || 1), z = s => String(s).padStart(2, "0");
  itens.forEach((x, i) => { if (typeof x.em !== "number") x.em = it.de + .3 + i * (it.ate - it.de - .8) / Math.max(1, n); });
  const r = C.rostoEm(it.de) || [W * .3, H * .3, W * .7, H * .55];
  const topo = S.topo, rot0 = topo + 110, espaco = r[1] - 30 - rot0;   // rótulo entre a pílula e a cabeça; sem espaço, abaixo do queixo
  const lugar = espaco >= 90 ? [rot0, r[1] - 30] : [r[3] + 40, H - S.baixo];
  const bar = C.el("div", "cs"); bar.style.top = topo + "px";
  bar.innerHTML = `<div class="pl"><span class="ti">${C.esc(it.titulo || "")}</span><span class="nn">${itens.map((_, i) => `<b>${z(ini + i)}/${z(tot)}</b>`).join("")}</span></div>`;
  const tl = C.tl, d = it.de, f = it.ate, bs = [...bar.querySelectorAll(".nn b")], fim = Math.max(d + .6, f - .4);
  tl.fromTo(bar, {opacity: 0, y: -40}, {opacity: 1, y: 0, duration: .45, ease: "back.out(1.5)"}, d);
  itens.forEach((x, i) => {
    const txt = String(x.texto || ""), alto = Math.min(150, lugar[1] - lugar[0], (W - 2 * S.lado) / Math.max(4, txt.length) / .6);
    const e = C.el("div", "cs-r", null, C.esc(txt)); e.style.fontSize = Math.round(alto) + "px";
    e.style.top = Math.round((lugar[0] + lugar[1]) / 2 - alto / 2) + "px";
    const sai = i < n - 1 ? itens[i + 1].em : fim;
    tl.fromTo(e, {opacity: 0, y: 50, scale: .9}, {opacity: 1, y: 0, scale: 1, duration: .4, ease: "back.out(1.8)", immediateRender: false}, x.em)
      .fromTo(bs[i], {opacity: 0, y: 40}, {opacity: 1, y: 0, duration: .3, ease: "power3.out", immediateRender: false}, x.em)
      .to(e, {opacity: 0, y: -50, duration: .3, ease: "power2.in"}, sai - .05);
    if (i < n - 1) tl.to(bs[i], {opacity: 0, y: -40, duration: .3, ease: "power2.in"}, sai);
  });
  tl.to(bar, {opacity: 0, y: -40, duration: .4, ease: "power2.in"}, fim);
};
