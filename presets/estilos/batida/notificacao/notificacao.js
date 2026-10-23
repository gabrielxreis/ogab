// BATIDA · notificação do celular: cartão claro com desfoque, ícone do app na cor da marca, desce do topo com mola e sobe ao sair.
ESTILO["notificacao"] = (it, C) => {
  const P = C.P, W = P.w, lado = 60, alto = 196;
  C.css("notificacao", `
    .nt{position:absolute;border-radius:44px;background:rgba(245,246,248,.86);backdrop-filter:blur(30px);-webkit-backdrop-filter:blur(30px);
        box-shadow:0 22px 60px rgba(0,0,0,.35);display:flex;gap:26px;align-items:center;padding:30px 34px;color:#111;font-family:"PalcoSans"}
    .nt .ic{width:92px;height:92px;border-radius:22px;background:var(--dest);display:grid;place-items:center;font-weight:900;font-size:46px;color:#111;flex:none}
    .nt .tx{flex:1;min-width:0}.nt .cab{display:flex;justify-content:space-between;font-weight:700;font-size:26px;color:#6b6f76;letter-spacing:.02em}
    .nt .ti{font-weight:800;font-size:36px;margin-top:4px}.nt .co{font-weight:600;font-size:31px;color:#2a2d33;line-height:1.25;margin-top:2px;
        display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}`);
  let y = C.seguro.topo + 10;
  const r = C.rostoEm(it.de);
  if (r && r[1] < y + alto + 20) y = Math.min(P.h - C.seguro.baixo - alto, r[3] + 40);   // rosto alto: o aviso vai para baixo do queixo
  const n = C.el("div", "nt"); Object.assign(n.style, {left: lado + "px", width: (W - 2 * lado) + "px", top: y + "px"});
  n.innerHTML = `<div class="ic">${C.esc(String(it.app || "").slice(0, 1).toUpperCase())}</div><div class="tx">
    <div class="cab"><span>${C.esc(String(it.app || "").toUpperCase())}</span><span>${P.lingua === "en" ? "now" : "agora"}</span></div>
    <div class="ti">${C.esc(it.titulo || "")}</div><div class="co">${C.esc(it.texto || "")}</div></div>`;
  const tl = C.tl, d = it.de, f = it.ate;
  tl.set(n, {y: -(y + alto + 40)}, 0)
    .to(n, {y: 0, duration: .7, ease: "back.out(1.4)"}, d)
    .to(n, {scale: 1.02, duration: .12, yoyo: true, repeat: 1, ease: "power1.inOut"}, d + .7)
    .to(n, {y: -(y + alto + 40), duration: .45, ease: "power3.in"}, Math.max(d + 1.2, f - .45));
};
