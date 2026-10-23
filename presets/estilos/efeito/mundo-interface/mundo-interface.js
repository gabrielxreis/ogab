// EFEITO · você dentro do app: o fundo inteiro vira uma tela clara de chat (canvas atrás da pessoa recortada), abrindo em
// círculo a partir do peito; a barra de pergunta digita o pedido acima da cabeça e o botão enviar (cor da marca) pulsa.
// Tela recriada: é ilustração (nome de app fictício no campo "app"), não finge ser print de app real.
ESTILO["mundo-interface"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  C.css("mundo-interface", `
    .mi{position:absolute;inset:0;background:#F5F4F0;overflow:hidden;color:#1d1d1f}
    .mi .grd{position:absolute;inset:0;background-image:radial-gradient(rgba(0,0,0,.07) 2px,transparent 2px);background-size:44px 44px}
    .mi .hd{position:absolute;left:${S.lado + 20}px;right:${S.lado + 20}px;top:${S.topo}px;height:84px;display:flex;align-items:center;gap:18px;
            font-weight:800;font-size:34px;border-bottom:2px solid rgba(0,0,0,.08)}
    .mi .lg{width:46px;height:46px;border-radius:14px;background:var(--dest)}
    .mi .hd i{margin-left:auto;width:52px;height:10px;border-radius:6px;background:rgba(0,0,0,.14)}
    .mi .bl{position:absolute;border-radius:30px;background:#fff;box-shadow:0 6px 24px rgba(0,0,0,.06);padding:26px 30px}
    .mi .bl b{display:block;height:16px;border-radius:9px;background:rgba(0,0,0,.1);margin:12px 0}
    .mi-q{position:absolute;height:112px;border-radius:56px;background:#fff;border:2px solid rgba(0,0,0,.09);
          box-shadow:0 22px 60px rgba(0,0,0,.14);display:flex;align-items:center;padding:0 16px 0 40px;gap:14px;color:#1d1d1f}
    .mi-q .tx{flex:1;font-weight:700;font-size:38px;white-space:nowrap;overflow:hidden}
    .mi-q .car{display:inline-block;width:4px;height:42px;background:#1d1d1f;vertical-align:-7px;margin-left:3px}
    .mi-q .env{flex:none;width:80px;height:80px;border-radius:50%;background:var(--dest);position:relative}
    .mi-q .env svg{position:absolute;left:21px;top:20px}`);
  const fundo = C.el("div", "mi");
  C.el("div", "grd", fundo);
  C.el("div", "hd", fundo, `<span class="lg"></span>${C.esc(it.app || "Assistente")}<i></i>`);
  // balões de conversa apagados nas laterais (ficam atrás e em volta do corpo, só como ambiente)
  [[S.lado + 10, r[3] + 120, 380, 3], [W - S.lado - 400, r[3] + 360, 390, 2], [S.lado + 10, r[3] + 600, 330, 2]].forEach(([x, y, w, n]) => {
    const b = C.el("div", "bl", fundo, "<b></b>".repeat(n)); Object.assign(b.style, {left: x + "px", top: y + "px", width: w + "px"});
    [...b.children].forEach((l, i) => l.style.width = (100 - i * 22) + "%");
  });
  const ped = String(it.pedido || ""), qw = W - 2 * (S.lado + 30), qy = Math.max(S.topo, Math.min(r[1] - 112 - 70, S.topo + 150));
  const q = C.el("div", "mi-q", null, `<div class="tx"><span class="t"></span><span class="car"></span></div>
     <div class="env"><svg width="38" height="40" viewBox="0 0 38 40"><path d="M19 34 V6 M7 17 L19 5 L31 17" fill="none" stroke="#111" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>`);
  Object.assign(q.style, {left: (S.lado + 30) + "px", top: qy + "px", width: qw + "px"});
  const tx = q.querySelector(".t"), car = q.querySelector(".car"), env = q.querySelector(".env");
  const tl = C.tl, d = it.de, f = it.ate, cx = (r[0] + r[2]) / 2, cy = r[3] + 200, R = Math.hypot(Math.max(cx, W - cx), Math.max(cy, H - cy)) + 20;
  tl.set([fundo, q], {opacity: 0}, 0).set(fundo, {opacity: 1}, d)
    .fromTo(fundo, {clipPath: `circle(0px at ${cx}px ${cy}px)`}, {clipPath: `circle(${R}px at ${cx}px ${cy}px)`, duration: .5, ease: "power3.inOut"}, d)
    .fromTo(q, {opacity: 0, y: 40, scale: .9}, {opacity: 1, y: 0, scale: 1, duration: .45, ease: "back.out(1.7)"}, d + .3);
  // digitação: letra a letra, cabendo no trecho (até 60% do tempo)
  const t0 = d + .7, passo = Math.min(.06, Math.max(.025, ((f - d) * .6 - .7) / Math.max(1, ped.length)));
  for (let i = 1; i <= ped.length; i++) tl.set(tx, {textContent: ped.slice(0, i)}, t0 + i * passo);
  const fimTx = t0 + ped.length * passo;
  tl.set(car, {opacity: 1}, 0).set(car, {opacity: 0}, fimTx + .25).set(car, {opacity: 1}, fimTx + .5)
    .fromTo(env, {scale: 1}, {scale: 1.15, duration: .15, yoyo: true, repeat: 1, ease: "power2.out"}, fimTx + .2)
    .to(q, {opacity: 0, y: -30, duration: .35, ease: "power2.in"}, Math.max(fimTx + .6, f - .5))
    .to(fundo, {clipPath: `circle(0px at ${cx}px ${cy}px)`, duration: .45, ease: "power3.in"}, Math.max(fimTx + .7, f - .45));
};
