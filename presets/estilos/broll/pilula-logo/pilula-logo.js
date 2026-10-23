// BROLL · pílula de produto: vidro escuro arredondado com ícone (arquivo do campo ou inicial na cor da marca), nome do produto,
// "por" e a marca; abre da esquerda para a direita e um brilho diagonal atravessa uma vez. Acima da cabeça ou abaixo do queixo.
ESTILO["pilula-logo"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, alto = 128;
  C.css("pilula-logo", `
    .pg{position:absolute;left:50%;display:flex;align-items:center;gap:22px;height:${alto}px;padding:0 44px 0 18px;border-radius:${alto / 2}px;white-space:nowrap;max-width:${W - 2 * S.lado}px;
        background:rgba(14,14,17,.74);backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px);border:1.5px solid rgba(255,255,255,.18);
        box-shadow:0 20px 50px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.12);font-family:"PalcoSans";color:#fff;overflow:hidden}
    .pg .ic{width:92px;height:92px;border-radius:50%;background:var(--dest);display:grid;place-items:center;font-weight:900;font-size:44px;color:#111;flex:none;overflow:hidden}
    .pg .ic img{width:100%;height:100%;object-fit:cover}
    .pg .nm{font-weight:800;font-size:44px;letter-spacing:-.01em}.pg .por{font-weight:700;font-size:28px;color:rgba(255,255,255,.55)}
    .pg .mc{font-weight:800;font-size:34px;color:rgba(255,255,255,.88)}.pg .mc img{height:46px;display:block}
    .pg .br{position:absolute;top:-20%;bottom:-20%;left:0;width:160px;background:linear-gradient(100deg,transparent,rgba(255,255,255,.28),transparent);
        transform:skewX(-18deg)}`);
  const r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  let y = r[3] + 50;
  if (y + alto > H - S.baixo) y = Math.max(S.topo, r[1] - 50 - alto);   // sem espaço abaixo do queixo: vai acima da cabeça
  const p = C.el("div", "pg"); p.style.top = y + "px";
  const nome = String(it.nome || "");
  p.innerHTML = `<div class="ic">${it.icone ? `<img src="${C.esc(it.icone)}">` : C.esc(nome.slice(0, 1).toUpperCase())}</div>
    <span class="nm">${C.esc(nome)}</span><span class="por">${C.esc(it.por || "")}</span>
    <span class="mc">${it.logo ? `<img src="${C.esc(it.logo)}">` : C.esc(it.marca || "")}</span><i class="br"></i>`;
  const br = p.querySelector(".br"), tx = [...p.querySelectorAll(".nm,.por,.mc")], ic = p.querySelector(".ic");
  const tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 1.2, f - .4);
  tl.set(p, {xPercent: -50, clipPath: `inset(0 100% 0 0 round ${alto / 2}px)`}, 0).set(ic, {scale: .4, rotation: -40}, 0)
    .set(tx, {x: -24, opacity: 0}, 0).set(br, {x: -200}, 0)
    .to(p, {clipPath: `inset(0 0% 0 0 round ${alto / 2}px)`, duration: .65, ease: "expo.out"}, d)
    .to(ic, {scale: 1, rotation: 0, duration: .5, ease: "expo.out"}, d + .05)
    .to(tx, {x: 0, opacity: 1, duration: .45, stagger: .08, ease: "power3.out"}, d + .2)
    .to(br, {x: 1100, duration: .9, ease: "power2.inOut"}, d + .75)
    .to(p, {y: 30, opacity: 0, duration: .35, ease: "power2.in"}, sai);
};
