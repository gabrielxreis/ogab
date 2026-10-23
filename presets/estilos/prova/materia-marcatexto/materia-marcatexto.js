// PROVA · matéria com marca-texto: cartão da matéria (print real do cliente ou página ilustrada), zoom até o trecho,
// marca-texto amarelo varrendo a frase linha a linha e pílula com fonte e data. Fica acima da cabeça ou abaixo do queixo.
ESTILO["materia-marcatexto"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, wN = 960, hC = 430, hN = hC + 90;
  C.css("materia-marcatexto", `
    .mm{position:absolute;transform-origin:50% 0}
    .mm .cd{position:absolute;left:0;top:0;width:${wN}px;height:${hC}px;border-radius:22px;overflow:hidden;background:#FBFAF7;
        box-shadow:0 26px 70px rgba(0,0,0,.45)}
    .mm .pg{position:absolute;inset:0;color:#16171a;font-family:"PalcoSans"}
    .mm .pg img{width:100%;height:100%;object-fit:cover;display:block}
    .mm .mh{position:absolute;left:48px;right:48px;top:30px;display:flex;justify-content:space-between;align-items:baseline;
        border-bottom:3px solid #16171a;padding-bottom:12px}
    .mm .mh b{font-family:"PalcoSerif";font-style:italic;font-weight:600;font-size:40px}.mm .mh span{font-weight:700;font-size:20px;color:#777;letter-spacing:.12em}
    .mm .hd{position:absolute;left:48px;right:48px;top:104px;font-weight:800;font-size:42px;line-height:1.08;letter-spacing:-.01em}
    .mm .ln{position:absolute;left:48px;height:14px;border-radius:7px;background:#e3e0d8}
    .mm .tr{position:absolute;left:48px;width:690px;top:262px;font-weight:700;font-size:33px;line-height:1.4;color:#2a2b2f}
    .mm .mk{background-image:linear-gradient(var(--mm-cor),var(--mm-cor));background-repeat:no-repeat;background-size:var(--m,0%) 100%;
        background-position:0 70%}
    .mm .rk{position:absolute;background:var(--mm-cor);mix-blend-mode:multiply;transform-origin:0 50%;border-radius:4px}
    .mm .pl{position:absolute;left:50%;top:${hC + 26}px;transform:translateX(-50%);display:flex;align-items:center;gap:14px;white-space:nowrap;
        background:rgba(14,14,16,.88);border:1.5px solid rgba(255,255,255,.18);border-radius:40px;padding:12px 28px;font-weight:700;font-size:28px;color:#fff}
    .mm .pl i{width:14px;height:14px;border-radius:50%;background:var(--dest)}.mm .pl em{font-style:normal;color:rgba(255,255,255,.6)}`);
  // zona livre do rosto: acima da cabeça ou abaixo do queixo (a maior), cartão reduzido para caber
  const r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const zc = [S.topo, r[1] - 36], zb = [r[3] + 36, H - S.baixo], z = (zb[1] - zb[0]) >= (zc[1] - zc[0]) ? zb : zc;
  const s = Math.min(1, (z[1] - z[0]) / hN, (W - 2 * S.lado) / wN);
  const b = C.el("div", "mm"); b.style.setProperty("--mm-cor", it.cor || "#FFE45C");
  Object.assign(b.style, {width: wN + "px", height: hN + "px", left: (W - wN) / 2 + "px", top: (z[0] + ((z[1] - z[0]) - hN * s) / 2) + "px",
                          transform: `scale(${s})`});
  const cd = C.el("div", "cd", b), pg = C.el("div", "pg", cd);
  let foco, alvo;
  if (it.imagem) {   // print real: zoom no ponto "foco" e retângulo amarelo em "marca"
    C.el("img", null, pg).src = it.imagem;
    const f = it.foco || [.5, .45], m = it.marca || [.08, .4, .92, .52];
    foco = `${f[0] * 100}% ${f[1] * 100}%`;
    alvo = C.el("div", "rk", pg);
    Object.assign(alvo.style, {left: m[0] * 100 + "%", top: m[1] * 100 + "%", width: (m[2] - m[0]) * 100 + "%", height: (m[3] - m[1]) * 100 + "%"});
  } else {           // página ilustrada (fictícia): cabeçalho, manchete, linhas cinza e o trecho com marca-texto
    pg.innerHTML = `<div class="mh"><b>${C.esc(it.fonte || "")}</b><span>${C.esc(String(it.data || "").toUpperCase())}</span></div>
      <div class="hd">${C.esc(it.titulo || "")}</div>
      <div class="ln" style="top:214px;width:820px"></div><div class="ln" style="top:238px;width:640px"></div>
      <div class="tr"><span class="mk">${C.esc(it.trecho || "")}</span>, segundo o levantamento feito com quem vê com o som ligado.</div>
      <div class="ln" style="top:400px;width:760px"></div>`;
    foco = "0% 290px"; alvo = pg.querySelector(".mk");
  }
  const pl = C.el("div", "pl", b, `<i></i>${C.esc(it.fonte || "")}<em>·</em><em>${C.esc(it.data || "")}</em>`);
  pg.style.transformOrigin = foco;
  const tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 1.8, f - .45);
  tl.set(cd, {y: 80, opacity: 0}, 0).set(pl, {opacity: 0, y: 20}, 0).set(pg, {scale: 1}, 0)
    .set(alvo, it.imagem ? {scaleX: 0} : {"--m": "0%"}, 0)
    .to(cd, {y: 0, opacity: 1, duration: .55, ease: "expo.out"}, d)
    .to(pg, {scale: 1.28, duration: 1, ease: "power2.inOut"}, d + .45)
    .to(alvo, it.imagem ? {scaleX: 1, duration: .8, ease: "power1.inOut"} : {"--m": "100%", duration: .8, ease: "power1.inOut"}, d + 1.15)
    .to(pl, {opacity: 1, y: 0, duration: .45, ease: "power3.out"}, d + 1.3)
    .to([cd, pl], {y: -40, opacity: 0, duration: .4, ease: "power2.in"}, sai);
};
