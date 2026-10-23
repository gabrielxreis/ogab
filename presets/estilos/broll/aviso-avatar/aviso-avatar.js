// BROLL · aviso do personagem: avatar redondo (imagem do campo ou um personagem desenhado) entra no canto de cima, dá um toque
// (inclina e volta) e um balão claro com o nome na cor da marca abre a partir dele. Acima da cabeça (ou abaixo do queixo).
ESTILO["aviso-avatar"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, av = 140, alto = 230;
  C.css("aviso-avatar", `
    .aa-a{position:absolute;width:${av}px;height:${av}px;border-radius:50%;background:var(--dest);overflow:hidden;
        box-shadow:0 14px 36px rgba(0,0,0,.4),0 0 0 6px rgba(255,255,255,.9)}
    .aa-a img,.aa-a svg{width:100%;height:100%;object-fit:cover;display:block}
    .aa-b{position:absolute;max-width:${W - 2 * S.lado - av - 40}px;background:#fff;color:#17191d;border-radius:34px;padding:22px 30px 26px;
        font-family:"PalcoSans";box-shadow:0 18px 44px rgba(0,0,0,.38)}
    .aa-b::before{content:"";position:absolute;left:-14px;top:38px;border:16px solid transparent;border-right-color:#fff;border-left:0}
    .aa-b b{display:block;font-weight:800;font-size:24px;letter-spacing:.14em;color:#17191d;opacity:.55}
    .aa-b b i{display:inline-block;width:12px;height:12px;border-radius:50%;background:var(--dest);margin-right:10px;vertical-align:1px}
    .aa-b p{font-weight:800;font-size:38px;line-height:1.22;margin-top:6px}`);
  const r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  let y = S.topo + 20;
  if (r[1] - 30 < y + alto) y = Math.min(H - S.baixo - alto, r[3] + 40);   // sem espaço acima da cabeça: vai para baixo do queixo
  const x = S.lado + 20;
  const a = C.el("div", "aa-a", null, it.avatar ? `<img src="${C.esc(it.avatar)}">` :
    `<svg viewBox="0 0 140 140"><circle cx="70" cy="86" r="40" fill="#F4E3CF"/><path d="M30 80 Q32 40 70 40 Q108 40 110 80 Q96 58 70 60 Q44 58 30 80Z" fill="#2B2420"/>
     <circle cx="56" cy="88" r="5" fill="#2B2420"/><circle cx="84" cy="88" r="5" fill="#2B2420"/><path d="M58 104 Q70 113 82 104" fill="none" stroke="#2B2420" stroke-width="4" stroke-linecap="round"/>
     <path d="M20 140 Q30 122 70 122 Q110 122 120 140Z" fill="#2B2420"/></svg>`);
  Object.assign(a.style, {left: x + "px", top: y + "px"});
  const bo = C.el("div", "aa-b", null, `<b><i></i>${C.esc(String(it.nome || "").toUpperCase())}</b><p>${C.esc(it.texto || "")}</p>`);
  Object.assign(bo.style, {left: (x + av + 30) + "px", top: (y + 4) + "px"});
  const tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 1.4, f - .45);
  tl.set(a, {scale: 0, opacity: 0}, 0).set(bo, {scale: .3, opacity: 0, transformOrigin: "0% 30%"}, 0)
    .to(a, {scale: 1, opacity: 1, duration: .45, ease: "back.out(1.6)"}, d)
    .to(a, {rotation: -10, duration: .12, ease: "power2.out"}, d + .45).to(a, {rotation: 6, duration: .12, ease: "power2.inOut"}, d + .57)
    .to(a, {rotation: 0, duration: .16, ease: "power2.out"}, d + .69)   // o toque
    .to(bo, {scale: 1, opacity: 1, duration: .45, ease: "expo.out"}, d + .6)
    .to(bo, {scale: .8, opacity: 0, duration: .3, ease: "power2.in"}, sai)
    .to(a, {scale: 0, opacity: 0, duration: .3, ease: "power2.in"}, sai + .1);
};
