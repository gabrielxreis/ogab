// PROVA · post de rede social: cartão claro genérico (nenhuma rede de verdade) com avatar, nome, @, texto e a fileira de ações;
// entra inclinado de baixo, flutua devagar e o coração enche na cor da marca com o número subindo. Fora do rosto.
ESTILO["post-social"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, wN = 920, hN = 430;
  C.css("post-social", `
    .ps{position:absolute;transform-origin:50% 0}
    .ps .cd{position:absolute;inset:0;border-radius:34px;background:#fff;color:#14161a;padding:34px 40px;font-family:"PalcoSans";
        box-shadow:0 28px 70px rgba(0,0,0,.42)}
    .ps .tp{display:flex;align-items:center;gap:20px}
    .ps .av{width:84px;height:84px;border-radius:50%;background:var(--dest);display:grid;place-items:center;font-weight:900;font-size:40px;color:#111;
        overflow:hidden;flex:none}.ps .av img{width:100%;height:100%;object-fit:cover}
    .ps .nm{font-weight:800;font-size:34px}.ps .us{font-weight:700;font-size:26px;color:#80858d}
    .ps .tx{font-weight:700;font-size:37px;line-height:1.3;margin:22px 0 26px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
    .ps .ac{display:flex;gap:56px;align-items:center;font-weight:800;font-size:28px;color:#5f646c;border-top:2px solid #eef0f2;padding-top:20px}
    .ps .ac span{display:flex;align-items:center;gap:12px}.ps .ac svg{width:40px;height:40px}
    .ps .co path.ch{fill:var(--dest);transform-origin:50% 55%}.ps .co b{color:#14161a}`);
  const r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const zc = [S.topo, r[1] - 36], zb = [r[3] + 36, H - S.baixo], z = (zb[1] - zb[0]) >= (zc[1] - zc[0]) ? zb : zc;
  const s = Math.min(1, (z[1] - z[0]) / hN, (W - 2 * S.lado) / wN);
  const b = C.el("div", "ps");
  Object.assign(b.style, {width: wN + "px", height: hN + "px", left: (W - wN) / 2 + "px", top: (z[0] + ((z[1] - z[0]) - hN * s) / 2) + "px",
                          transform: `scale(${s})`});
  const nome = String(it.nome || ""), traco = 'fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"';
  const cd = C.el("div", "cd", b, `<div class="tp"><div class="av">${it.avatar ? `<img src="${C.esc(it.avatar)}">` : C.esc(nome.slice(0, 1))}</div>
    <div><div class="nm">${C.esc(nome)}</div><div class="us">${C.esc(it.usuario || "")} · ${C.esc(it.tempo || "")}</div></div></div>
    <div class="tx">${C.esc(it.texto || "")}</div>
    <div class="ac"><span><svg viewBox="0 0 40 40"><path ${traco} d="M8 10h24v15H18l-7 6v-6H8z"/></svg>${C.esc(it.comentarios || "")}</span>
      <span><svg viewBox="0 0 40 40"><path ${traco} d="M10 15l5-5 5 5M15 10v16h10M30 25l-5 5-5-5M25 30V14H15"/></svg></span>
      <span class="co"><svg viewBox="0 0 40 40"><path ${traco} d="M20 32S6 24 6 15a7 7 0 0 1 14-2 7 7 0 0 1 14 2c0 9-14 17-14 17z"/>
        <path class="ch" d="M20 32S6 24 6 15a7 7 0 0 1 14-2 7 7 0 0 1 14 2c0 9-14 17-14 17z"/></svg><b>${C.esc(it.curtidas || "")}</b></span></div>`);
  const ch = cd.querySelector(".ch"), num = cd.querySelector(".co b");
  const tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 1.6, f - .45);
  tl.set(cd, {y: 120, rotation: -5, opacity: 0}, 0).set(ch, {scale: 0}, 0).set(num, {opacity: .35}, 0)
    .to(cd, {y: 0, rotation: -1.5, opacity: 1, duration: .7, ease: "expo.out"}, d)
    .to(cd, {y: -14, rotation: -.6, duration: Math.max(.4, sai - d - .7), ease: "sine.inOut"}, d + .7)   // flutua devagar
    .to(ch, {scale: 1, duration: .35, ease: "power3.out"}, d + 1.0)
    .to(num, {opacity: 1, duration: .3, ease: "power2.out"}, d + 1.05)
    .to(cd, {y: -70, opacity: 0, duration: .4, ease: "power2.in"}, sai);
};
