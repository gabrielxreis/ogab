// GANCHO · riscado vs novo: dois ícones lado a lado acima da cabeça; o antigo leva um X vermelho desenhado e apaga, o novo ganha o anel da marca.
ESTILO["riscado-vs-novo"] = (it, C) => {
  const P = C.P, W = P.w, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, P.h * .32, W * .68, P.h * .55];
  const lado = Math.round(Math.max(120, Math.min(210, r[1] - 40 - S.topo - 74))), gap = Math.min(200, W * .17);
  C.css("riscado-vs-novo", `
    .rv{position:absolute;display:flex;flex-direction:column;align-items:center;gap:16px;font-family:"PalcoSans";font-weight:800;
        font-size:40px;color:#fff;text-shadow:0 4px 16px rgba(0,0,0,.55);white-space:nowrap}
    .rv .ic{position:relative;border-radius:26%;display:grid;place-items:center;font-weight:900;box-shadow:0 18px 44px rgba(0,0,0,.4);text-shadow:none}
    .rv .ic img{width:76%;height:76%;object-fit:contain}
    .rv .x{position:absolute;overflow:visible;pointer-events:none}
    .rv-s{position:absolute;overflow:visible}`);
  const mk = (nome, logo, x, novo) => {
    const e = C.el("div", "rv"); Object.assign(e.style, {left: x + "px", top: S.topo + 10 + "px", width: lado + "px"});
    e.innerHTML = `<div class="ic">${logo ? `<img src="${C.esc(logo)}">` : C.esc(String(nome).slice(0, 1).toUpperCase())}</div><div>${C.esc(nome)}</div>`;
    Object.assign(e.firstChild.style, {width: lado + "px", height: lado + "px", fontSize: lado * .48 + "px",
      background: novo ? "var(--dest)" : "#E9E9EC", color: novo ? "#111214" : "#5b5d63"});
    if (logo) e.firstChild.style.background = "#fff";
    return e;
  };
  const xa = W / 2 - gap / 2 - lado, xn = W / 2 + gap / 2;
  const a = mk(it.antigo || "", it.logo_antigo, xa, false), n = mk(it.novo || "", it.logo_novo, xn, true);
  a.insertAdjacentHTML("beforeend", `<svg class="x" viewBox="0 0 100 100" style="left:${-lado * .08}px;top:${-lado * .08}px;width:${lado * 1.16}px;height:${lado * 1.16}px"><g fill="none" stroke="#E5372E" stroke-width="12" stroke-linecap="round">
    <path d="M14 14 L86 86" pathLength="1"/><path d="M86 14 L14 86" pathLength="1"/></g></svg>`);
  const s = C.el("div", "rv-s"); Object.assign(s.style, {left: W / 2 - 40 + "px", top: S.topo + 10 + lado / 2 - 30 + "px", width: "80px", height: "60px"});
  s.innerHTML = `<svg viewBox="0 0 80 60" width="80" height="60"><path d="M8 30 H66 M48 12 L68 30 L48 48" fill="none" stroke="#fff" stroke-width="8"
    stroke-linecap="round" stroke-linejoin="round" pathLength="1"/></svg>`;
  const tl = C.tl, d = it.de, f = it.ate, xs = a.querySelectorAll(".x path");
  tl.set([a, n, s], {opacity: 0}, 0)
    .fromTo(a, {y: 40, opacity: 0}, {y: 0, opacity: 1, duration: .45, ease: "expo.out"}, d)
    .fromTo(n, {y: 40, opacity: 0}, {y: 0, opacity: 1, duration: .45, ease: "expo.out"}, d + .12)
    .set(s, {opacity: 1}, d + .3).fromTo(s.querySelector("path"), {strokeDasharray: 1, strokeDashoffset: 1}, {strokeDashoffset: 0, duration: .35, ease: "power2.out"}, d + .3)
    .set(xs, {strokeDasharray: 1, strokeDashoffset: 1}, 0)
    .to(xs[0], {strokeDashoffset: 0, duration: .22, ease: "power2.out"}, d + .75)
    .to(xs[1], {strokeDashoffset: 0, duration: .22, ease: "power2.out"}, d + .97)
    .to([a.children[0], a.children[1]], {opacity: .45, duration: .3, ease: "power2.out"}, d + 1.1)
    .to(n.firstChild, {scale: 1.08, boxShadow: "0 0 0 10px #fff, 0 18px 44px rgba(0,0,0,.4)", duration: .35, ease: "power3.out"}, d + 1.2)
    .to([a, s, n], {y: -50, opacity: 0, duration: .35, stagger: .05, ease: "power2.in"}, Math.max(d + 1.7, f - .45));
};
