// BROLL · pergunta no chat: janela escura genérica (sem marca de app real). A pergunta é digitada no campo (o campo de texto é
// a cena, por isso a digitação é permitida), o botão envia, o balão sobe e a resposta chega por partes, linha a linha.
ESTILO["chat-pergunta"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, wN = 960, hN = 560;
  C.css("chat-pergunta", `
    .cp{position:absolute;transform-origin:50% 0}
    .cp .cd{position:absolute;inset:0;border-radius:34px;background:#151619;border:1.5px solid rgba(255,255,255,.12);overflow:hidden;
        box-shadow:0 28px 70px rgba(0,0,0,.5);font-family:"PalcoSans";color:#fff}
    .cp .hd{height:76px;display:flex;align-items:center;gap:16px;padding:0 30px;border-bottom:1.5px solid rgba(255,255,255,.08);font-weight:800;font-size:28px}
    .cp .hd i{width:34px;height:34px;border-radius:10px;background:var(--dest)}
    .cp .ms{position:absolute;left:30px;right:30px;top:100px;bottom:120px;display:flex;flex-direction:column;gap:18px}
    .cp .eu{align-self:flex-end;max-width:78%;background:var(--dest);color:#111;border-radius:28px 28px 8px 28px;padding:16px 26px;font-weight:700;font-size:30px;line-height:1.3}
    .cp .ia{align-self:flex-start;max-width:86%;background:#24262b;border-radius:28px 28px 28px 8px;padding:18px 28px;font-weight:700;font-size:30px;line-height:1.35}
    .cp .ia p{margin:2px 0}.cp .pt{align-self:flex-start;display:flex;gap:8px;padding:22px 26px;background:#24262b;border-radius:28px}
    .cp .pt b{width:12px;height:12px;border-radius:50%;background:#9a9ea6}
    .cp .in{position:absolute;left:24px;right:24px;bottom:24px;height:76px;border-radius:40px;background:#202227;display:flex;align-items:center;
        padding:0 12px 0 30px;font-weight:700;font-size:28px;color:#e9eaec}
    .cp .in .tx{flex:1;white-space:nowrap;overflow:hidden}.cp .in .tx span{display:none}
    .cp .car{display:inline-block;width:3px;height:32px;background:var(--dest);vertical-align:-6px;margin-left:3px}
    .cp .bt{width:56px;height:56px;border-radius:50%;background:var(--dest);display:grid;place-items:center;flex:none}`);
  const r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const zc = [S.topo, r[1] - 36], zb = [r[3] + 36, H - S.baixo], z = (zb[1] - zb[0]) >= (zc[1] - zc[0]) ? zb : zc;
  const s = Math.min(1, (z[1] - z[0]) / hN, (W - 2 * S.lado) / wN);
  const b = C.el("div", "cp");
  Object.assign(b.style, {width: wN + "px", height: hN + "px", left: (W - wN) / 2 + "px", top: (z[0] + ((z[1] - z[0]) - hN * s) / 2) + "px",
                          transform: `scale(${s})`});
  const perg = String(it.pergunta || ""), partes = [].concat(it.resposta || []);
  const cd = C.el("div", "cd", b, `<div class="hd"><i></i>${C.esc(it.nome || "")}</div>
    <div class="ms"><div class="eu">${C.esc(perg)}</div><div class="ia">${partes.map(p => `<p>${C.esc(p)}</p>`).join("")}</div></div>
    <div class="in"><div class="tx">${[...perg].map(c => `<span>${C.esc(c)}</span>`).join("")}<i class="car"></i></div>
      <div class="bt"><svg width="26" height="26" viewBox="0 0 26 26"><path d="M13 21V5M6 12l7-7 7 7" fill="none" stroke="#111" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div></div>`);
  const eu = cd.querySelector(".eu"), ia = cd.querySelector(".ia"), ps = [...ia.children], letras = [...cd.querySelectorAll(".tx span")];
  const pt = C.el("div", "pt", null, "<b></b><b></b><b></b>"); ia.before(pt); const bt = cd.querySelector(".bt");
  const tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 2.6, f - .45);
  const tDig = Math.min(1.2, letras.length * .03), tEnv = d + .35 + tDig + .15;
  tl.set(cd, {y: 80, opacity: 0}, 0).set([eu, ia], {opacity: 0}, 0).set(pt, {opacity: 0, display: "flex"}, 0).set(ps, {clipPath: "inset(0 0 100% 0)", y: 10}, 0)
    .to(cd, {y: 0, opacity: 1, duration: .55, ease: "expo.out"}, d);
  letras.forEach((l, i) => tl.set(l, {display: "inline"}, d + .35 + i * tDig / letras.length));   // digitação no campo
  tl.to(bt, {scale: .85, duration: .1, yoyo: true, repeat: 1, ease: "power1.inOut"}, tEnv)
    .set(letras, {display: "none"}, tEnv + .12)
    .fromTo(eu, {y: 70, opacity: 0}, {y: 0, opacity: 1, duration: .45, ease: "expo.out"}, tEnv + .1)
    .to(pt, {opacity: 1, duration: .2, ease: "power2.out"}, tEnv + .45)
    .to(pt.children, {y: -8, duration: .22, yoyo: true, repeat: 1, stagger: .08, ease: "sine.inOut"}, tEnv + .5)
    .set(pt, {display: "none"}, tEnv + .98)
    .to(ia, {opacity: 1, duration: .2}, tEnv + 1.0);
  ps.forEach((p, i) => tl.to(p, {clipPath: "inset(0 0 0% 0)", y: 0, duration: .4, ease: "power3.out"}, tEnv + 1.0 + i * .4));
  tl.to(cd, {y: -40, opacity: 0, duration: .4, ease: "power2.in"}, sai);
};
