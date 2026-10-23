// BATIDA · botões do celular desligando: painel de vidro escuro com botões redondos ligados (cor da marca); cada um desliga
// na sua palavra (aperta, fica cinza, ganha um risco). Ícones desenhados aqui: wifi, telefone, sinal, aviao, som, sino.
// itens: [{icone, rotulo, palavra}] (palavra = gatilho na transcrição; sem ela, um a cada 0,7 s; "em" força o segundo).
ESTILO["central-controle"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, B = 170;
  const ICO = {
    wifi: `<path d="M8 22a34 34 0 0 1 48 0M16 31a22 22 0 0 1 32 0M24 40a10 10 0 0 1 16 0" fill="none" stroke-width="6" stroke-linecap="round"/><circle cx="32" cy="49" r="5" stroke="none"/>`,
    telefone: `<path d="M20 10c3 0 5 6 6 10s-3 6-4 8c3 6 8 11 14 14 2-1 4-5 8-4s10 3 10 6-4 9-9 9C27 53 11 37 11 19c0-5 5-9 9-9z" stroke="none"/>`,
    sinal: `<rect x="10" y="40" width="8" height="14" rx="2" stroke="none"/><rect x="23" y="31" width="8" height="23" rx="2" stroke="none"/><rect x="36" y="21" width="8" height="33" rx="2" stroke="none"/><rect x="49" y="11" width="8" height="43" rx="2" stroke="none"/>`,
    aviao: `<path d="M30 8c2-2 6-2 6 2v15l18 10v6l-18-5v11l6 5v5l-9-3-9 3v-5l6-5V31L12 36v-6l18-10V10z" stroke="none"/>`,
    som: `<path d="M10 25h10l13-11v36L20 39H10z" stroke="none"/><path d="M42 22c4 5 4 15 0 20M49 15c8 9 8 25 0 34" fill="none" stroke-width="5" stroke-linecap="round"/>`,
    sino: `<path d="M32 9c-10 0-16 8-16 18v10l-5 7h42l-5-7V27c0-10-6-18-16-18z" stroke="none"/><path d="M26 50a6 6 0 0 0 12 0z" stroke="none"/>`};
  C.css("central-controle", `
    .cc{position:absolute;border-radius:60px;background:rgba(30,31,36,.55);backdrop-filter:blur(30px);-webkit-backdrop-filter:blur(30px);
        border:1.5px solid rgba(255,255,255,.14);box-shadow:0 26px 60px rgba(0,0,0,.4);padding:40px 46px 30px;display:flex;gap:46px;transform-origin:50% 50%}
    .cc .bt{display:flex;flex-direction:column;align-items:center;gap:16px}
    .cc .ci{width:${B}px;height:${B}px;border-radius:50%;background:var(--dest);display:grid;place-items:center;position:relative}
    .cc .ci .of{position:absolute;inset:0;border-radius:50%;background:rgba(120,122,130,.55);opacity:0}
    .cc .ci svg{position:relative;width:84px;height:84px}
    .cc .ci .ic{fill:#111;stroke:#111}
    .cc .ci .ic2{fill:#fff;stroke:#fff;position:absolute;left:43px;top:43px;opacity:0}
    .cc .ci .rs{position:absolute;inset:0;width:100%;height:100%}
    .cc .rt{font-weight:800;font-size:30px;color:#fff;letter-spacing:.02em}
    .cc .rt small{display:block;text-align:center;font-weight:700;font-size:22px;color:rgba(255,255,255,.6);margin-top:2px}`);
  const itens = (it.itens || []).slice(0, 4), n = Math.max(1, itens.length), larg = n * B + (n - 1) * 46 + 92, alto = B + 160;
  const r = C.rostoEm(it.de) || [W * .3, H * .3, W * .7, H * .55];
  const cima = r[1] - 30 - S.topo, baixo = H - S.baixo - (r[3] + 40);
  const zona = cima >= baixo ? [S.topo, r[1] - 30] : [r[3] + 40, H - S.baixo];
  const esc = Math.min(1, (zona[1] - zona[0]) / alto, (W - 2 * S.lado) / larg);
  const p = C.el("div", "cc"); Object.assign(p.style, {left: (W - larg) / 2 + "px", top: ((zona[0] + zona[1]) / 2 - alto / 2) + "px", width: larg + "px"});
  const on = P.lingua === "en" ? "On" : "Ligado", off = P.lingua === "en" ? "Off" : "Desligado";
  const norm = s => String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]/g, "");
  const pals = (P.palavras || []).filter(w => w.ini >= it.de - .1 && w.ini < it.ate);
  let usado = -1;
  const bts = itens.map((x, i) => {
    let em = typeof x.em === "number" ? x.em : null;
    if (em == null && x.palavra) {   // primeira ocorrência da palavra depois da anterior
      const k = pals.findIndex((w, j) => j > usado && norm(w.w).startsWith(norm(x.palavra)));
      if (k >= 0) { usado = k; em = pals[k].ini; }
    }
    if (em == null) em = it.de + .8 + i * .7;
    const ic = ICO[x.icone] || ICO.wifi, b = C.el("div", "bt", p);
    b.innerHTML = `<div class="ci"><i class="of"></i><svg viewBox="0 0 64 64" class="ic">${ic}</svg><svg viewBox="0 0 64 64" class="ic2">${ic}</svg>
      <svg class="rs" viewBox="0 0 ${B} ${B}"><line x1="${B * .27}" y1="${B * .27}" x2="${B * .73}" y2="${B * .73}" stroke="#fff" stroke-width="9" stroke-linecap="round"
        stroke-dasharray="${B * .66}" stroke-dashoffset="${B * .66}"/></svg></div>
      <div class="rt">${C.esc(x.rotulo || "")}<small><span class="lg">${on}</span></small></div>`;
    return {b, em};
  });
  const tl = C.tl, d = it.de, f = it.ate;
  tl.fromTo(p, {opacity: 0, scale: esc * .8, y: 30}, {opacity: 1, scale: esc, y: 0, duration: .5, ease: "back.out(1.5)"}, d);
  bts.forEach(({b, em}) => {   // aperta, apaga a cor, troca o ícone para branco, risca e muda o texto
    const ci = b.querySelector(".ci"), lg = b.querySelector(".lg");
    tl.to(ci, {scale: .88, duration: .1, ease: "power2.in"}, em)
      .to(ci, {scale: 1, duration: .35, ease: "back.out(3)"}, em + .1)
      .to(ci, {backgroundColor: "rgba(60,62,70,.9)", duration: .2}, em + .05)
      .to(b.querySelector(".ic"), {opacity: 0, duration: .15}, em + .05)
      .to(b.querySelector(".ic2"), {opacity: 1, duration: .15}, em + .05)
      .to(b.querySelector(".rs line"), {attr: {"stroke-dashoffset": 0}, duration: .25, ease: "power2.out"}, em + .12)
      .to(lg, {opacity: 0, duration: .08}, em + .05);
    // texto ligado/desligado sem callback (o render salta de quadro em quadro): segundo span por cima
    lg.insertAdjacentHTML("afterend", `<span class="lg2" style="position:absolute;opacity:0">${off}</span>`);
    const lg2 = b.querySelector(".lg2"); lg.parentNode.style.position = "relative"; lg2.style.left = "0"; lg2.style.right = "0";
    tl.to(lg2, {opacity: 1, duration: .1}, em + .12);
  });
  tl.to(p, {opacity: 0, y: -30, duration: .4, ease: "power2.in"}, Math.max(d + 1, f - .4));
};
