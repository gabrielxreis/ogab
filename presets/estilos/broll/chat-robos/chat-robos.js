// BROLL · robôs conversando: janela de grupo escura e genérica; cada mensagem entra de baixo com avatar de robô desenhado
// (cabeça, olhos e antena em SVG), nome e texto, e as @menções ficam marcadas na cor da marca. Fora do rosto.
ESTILO["chat-robos"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, wN = 960, hN = 560;
  C.css("chat-robos", `
    .cr{position:absolute;transform-origin:50% 0}
    .cr .cd{position:absolute;inset:0;border-radius:34px;background:#141518;border:1.5px solid rgba(255,255,255,.12);overflow:hidden;
        box-shadow:0 28px 70px rgba(0,0,0,.5);font-family:"PalcoSans";color:#fff}
    .cr .hd{height:76px;display:flex;align-items:center;gap:12px;padding:0 30px;border-bottom:1.5px solid rgba(255,255,255,.08);font-weight:800;font-size:28px}
    .cr .hd em{font-style:normal;color:var(--dest);font-size:34px}.cr .hd span{margin-left:auto;font-size:22px;color:#8d929a;font-weight:700}
    .cr .ms{position:absolute;left:30px;right:30px;top:100px;display:flex;flex-direction:column;gap:26px}
    .cr .m{display:flex;gap:20px;align-items:flex-start}
    .cr .av{width:72px;height:72px;border-radius:20px;flex:none;display:grid;place-items:center}
    .cr .nm{font-weight:800;font-size:26px;margin-bottom:4px}.cr .nm small{font-size:20px;color:#7d828a;font-weight:700;margin-left:10px}
    .cr .tx{font-weight:700;font-size:31px;line-height:1.3;color:#e6e7ea}
    .cr .at{color:var(--dest);background:color-mix(in srgb, var(--dest) 16%, transparent);border-radius:8px;padding:0 6px}`);
  const r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const zc = [S.topo, r[1] - 36], zb = [r[3] + 36, H - S.baixo], z = (zb[1] - zb[0]) >= (zc[1] - zc[0]) ? zb : zc;
  const s = Math.min(1, (z[1] - z[0]) / hN, (W - 2 * S.lado) / wN);
  const b = C.el("div", "cr");
  Object.assign(b.style, {width: wN + "px", height: hN + "px", left: (W - wN) / 2 + "px", top: (z[0] + ((z[1] - z[0]) - hN * s) / 2) + "px",
                          transform: `scale(${s})`});
  const robos = it.robos || [], msgs = it.mensagens || [], tons = ["var(--dest)", "#E9E9EC", "#9BA3AE", "#C9B48F"];
  const rosto = (k) => `<svg width="50" height="50" viewBox="0 0 50 50"><path d="M25 3v7" stroke="#111" stroke-width="4" stroke-linecap="round"/>
    <circle cx="25" cy="4" r="3.5" fill="#111"/><rect x="7" y="12" width="36" height="30" rx="10" fill="none" stroke="#111" stroke-width="4"/>
    ${k % 2 ? `<rect x="15" y="22" width="7" height="7" rx="2" fill="#111"/><rect x="28" y="22" width="7" height="7" rx="2" fill="#111"/>`
            : `<circle cx="18.5" cy="25.5" r="4" fill="#111"/><circle cx="31.5" cy="25.5" r="4" fill="#111"/>`}
    <path d="M19 35h12" stroke="#111" stroke-width="3.5" stroke-linecap="round"/></svg>`;
  const marca = t => C.esc(t).replace(/@[\wÀ-ÿ-]+/g, m => `<span class="at">${m}</span>`);
  const cd = C.el("div", "cd", b, `<div class="hd"><em>#</em>${C.esc(it.sala || "")}<span>${robos.length} ${P.lingua === "en" ? "bots" : "robôs"}</span></div>`);
  const ms = C.el("div", "ms", cd), tl = C.tl, d = it.de, f = it.ate, els = [];
  tl.set(cd, {y: 80, opacity: 0}, 0).to(cd, {y: 0, opacity: 1, duration: .55, ease: "expo.out"}, d);
  msgs.forEach((x, i) => {
    const k = Math.max(0, Math.min(robos.length - 1, x.de | 0)), rb = robos[k] || {};
    const m = C.el("div", "m", ms, `<div class="av" style="background:${tons[k % tons.length]}">${rosto(k)}</div>
      <div><div class="nm">${C.esc(rb.nome || "")}<small>${P.lingua === "en" ? "bot" : "robô"}</small></div><div class="tx">${marca(x.texto || "")}</div></div>`);
    els.push(m);
    const em = typeof x.em === "number" ? x.em : d + .45 + i * .8;
    tl.set(m, {y: 50, opacity: 0}, 0).to(m, {y: 0, opacity: 1, duration: .45, ease: "expo.out"}, em);
  });
  tl.to(cd, {y: -40, opacity: 0, duration: .4, ease: "power2.in"}, Math.max(d + 1.6, f - .45));
};
