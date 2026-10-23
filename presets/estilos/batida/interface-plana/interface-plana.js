// BATIDA · interface plana: um cartão por passo (comentário, mensagem, e-mail), branco liso com borda fina, sem sombra nem brilho.
// O novo empurra o anterior para a esquerda; embaixo, pontos numerados mostram em que passo está. Ilustração, não finge ser print.
ESTILO["interface-plana"] = (it, C) => {
  const P = C.P, W = P.w, ps = (it.passos || []).slice(0, 5), lado = 80, larg = W - 2 * lado, alto = 220, en = P.lingua === "en";
  const ICO = {comentario: '<path d="M4 5h16v11H9l-5 4z"/>', mensagem: '<path d="M21 12a8.5 8.5 0 0 1-12.6 7.4L3 21l1.6-5.2A8.5 8.5 0 1 1 21 12z"/>',
               email: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 6l8.5 7 8.5-7"/>'};
  const NOME = {comentario: en ? "Comment" : "Comentário", mensagem: en ? "Message" : "Mensagem", email: "E-mail"};
  C.css("interface-plana", `
    .ip{position:absolute;left:0;width:${W}px;height:${alto + 60}px;font-family:"PalcoSans";overflow:hidden}
    .ip .cd{position:absolute;left:${lado}px;top:0;width:${larg}px;height:${alto}px;box-sizing:border-box;background:#fff;border:3px solid #e3e5e8;border-radius:30px;
            display:flex;gap:26px;align-items:center;padding:0 34px}
    .ip .ic{width:96px;height:96px;border-radius:24px;background:var(--dest);display:grid;place-items:center;flex:none}
    .ip .ic svg{width:54px;height:54px;fill:none;stroke:#111;stroke-width:2.2;stroke-linejoin:round;stroke-linecap:round}
    .ip .tx{flex:1;min-width:0}.ip .tp{font-weight:700;font-size:26px;color:#7a7f87;text-transform:uppercase;letter-spacing:.08em}
    .ip .qm{font-weight:800;font-size:32px;color:#15171a;margin-top:2px}
    .ip .ms{font-weight:600;font-size:36px;color:#2a2d33;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .ip .ds{position:absolute;left:0;right:0;top:${alto + 22}px;display:flex;justify-content:center;gap:14px}
    .ip .dt{width:16px;height:16px;border-radius:8px;background:rgba(255,255,255,.45)}`);
  const lim = P.h - C.seguro.baixo, r = C.rostoEm(it.de), h = alto + 60;
  let y = lim - h;
  if (r && r[3] + 40 + h <= lim) y = r[3] + 40; else if (r && r[1] - 40 - h >= C.seguro.topo) y = r[1] - 40 - h;
  const box = C.el("div", "ip"); box.style.top = y + "px";
  const cds = ps.map(p => C.el("div", "cd", box, `<div class="ic"><svg viewBox="0 0 24 24">${ICO[p.tipo] || ICO.mensagem}</svg></div>
    <div class="tx"><div class="tp">${C.esc(NOME[p.tipo] || p.tipo || "")}</div><div class="qm">${C.esc(p.quem || "")}</div><div class="ms">${C.esc(p.texto || "")}</div></div>`));
  const ds = C.el("div", "ds", box), dts = ps.map(() => C.el("div", "dt", ds));
  const tl = C.tl, d = it.de, f = it.ate;
  tl.set(box, {opacity: 0}, 0).set(box, {opacity: 1}, d).set(cds, {x: W}, 0);
  cds.forEach((c, i) => {
    const t = Math.max(d, Math.min(f - .6, ps[i].em != null ? +ps[i].em : d + i * .9));
    tl.to(c, {x: 0, duration: .5, ease: "expo.out"}, t)
      .to(dts[i], {width: 44, backgroundColor: "var(--dest)", duration: .35, ease: "power3.out"}, t);
    if (i) tl.to(cds[i - 1], {x: -W, duration: .5, ease: "expo.out"}, t).to(dts[i - 1], {width: 16, backgroundColor: "#fff", duration: .35, ease: "power3.out"}, t);
  });
  tl.to(box, {y: 40, opacity: 0, duration: .35, ease: "power3.in"}, Math.max(d + 1, f - .35));
};
