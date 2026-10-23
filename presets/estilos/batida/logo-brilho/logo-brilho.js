// BATIDA · logo com brilho: logo + nome nascem de um clarão branco desfocado, um ponto de luz cruza a base e um reflexo corre
// pelas letras e pelo logo. Sem cartão, fora do rosto (acima da cabeça ou abaixo do queixo, onde couber mais).
ESTILO["logo-brilho"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, LG = 150;
  C.css("logo-brilho", `
    .lb{position:absolute;left:0;width:${W}px;display:flex;justify-content:center;pointer-events:none}
    .lb .in{display:flex;align-items:center;gap:34px;position:relative}
    .lb .lo{width:${LG}px;height:${LG}px;border-radius:38px;position:relative;overflow:hidden;flex:none;filter:drop-shadow(0 0 26px rgba(255,255,255,.45))}
    .lb .lo.mono{background:var(--dest);display:grid;place-items:center;font-weight:900;font-size:92px;color:#111}
    .lb .lo img{width:100%;height:100%;object-fit:contain}
    .lb .lo .rf{position:absolute;inset:-40%;background:linear-gradient(105deg,transparent 42%,rgba(255,255,255,.85) 50%,transparent 58%)}
    .lb .nm{position:relative;font-weight:900;font-size:118px;letter-spacing:-.03em;line-height:1;white-space:nowrap;
        background:linear-gradient(180deg,#fff 30%,#d4d8df);-webkit-background-clip:text;background-clip:text;color:transparent;
        filter:drop-shadow(0 0 22px rgba(255,255,255,.5)) drop-shadow(0 4px 14px rgba(0,0,0,.4))}
    .lb .nm2{position:absolute;inset:0;background:linear-gradient(105deg,transparent 40%,#fff 50%,transparent 60%) no-repeat;background-size:300% 100%;
        -webkit-background-clip:text;background-clip:text;color:transparent}
    .lb .pt{position:absolute;bottom:-26px;width:14px;height:14px;border-radius:50%;background:#fff;box-shadow:0 0 18px 6px rgba(255,255,255,.8)}`);
  const r = C.rostoEm(it.de) || [W * .3, H * .3, W * .7, H * .55];
  const cima = r[1] - 40 - S.topo, baixo = H - S.baixo - (r[3] + 50), alto = LG + 40;
  const y = cima >= alto || cima >= baixo ? S.topo + Math.max(0, (cima - alto) / 2) : r[3] + 50 + Math.max(0, (baixo - alto) / 2);
  const box = C.el("div", "lb"); box.style.top = y + "px";
  const nome = String(it.nome || ""), img = typeof it.logo === "string" && it.logo.trim();
  const inn = C.el("div", "in", box);
  inn.innerHTML = `<div class="lo${img ? "" : " mono"}">${img ? `<img src="${C.esc(img)}">` : C.esc(nome.slice(0, 1).toUpperCase())}<i class="rf"></i></div>
    <div class="nm">${C.esc(nome)}<span class="nm2">${C.esc(nome)}</span></div><i class="pt"></i>`;
  const nm = inn.querySelector(".nm"), larg = LG + 34 + nome.length * 70;   // estimativa: nome longo encolhe para caber
  if (larg > W - 2 * S.lado - 40) inn.style.transform = `scale(${(W - 2 * S.lado - 40) / larg})`;
  const lo = inn.querySelector(".lo"), rf = inn.querySelector(".rf"), nm2 = inn.querySelector(".nm2"), pt = inn.querySelector(".pt");
  const tl = C.tl, d = it.de, f = it.ate;
  tl.set([lo, nm], {opacity: 0}, 0).set(pt, {opacity: 0, left: -20}, 0).set(rf, {xPercent: -70}, 0).set(nm2, {backgroundPosition: "100% 0"}, 0)
    .fromTo(lo, {opacity: 0, scale: .82, filter: "blur(18px) brightness(3)"}, {opacity: 1, scale: 1, filter: "blur(0px) brightness(1)", duration: .8, ease: "power3.out"}, d)
    .fromTo(nm, {opacity: 0, y: 16, filter: "blur(16px) brightness(2.5) drop-shadow(0 0 40px rgba(255,255,255,.9))"},
            {opacity: 1, y: 0, filter: "blur(0px) brightness(1) drop-shadow(0 0 22px rgba(255,255,255,.5))", duration: .9, ease: "power3.out"}, d + .12)
    .to(pt, {opacity: 1, duration: .15}, d + .55)
    .to(pt, {left: () => inn.offsetWidth + 10, duration: .7, ease: "power2.inOut"}, d + .55)
    .to(pt, {opacity: 0, duration: .2}, d + 1.1)
    .to(rf, {xPercent: 70, duration: .7, ease: "power2.inOut"}, d + 1.05)
    .to(nm2, {backgroundPosition: "0% 0", duration: .9, ease: "power2.inOut"}, d + 1.1)
    .to([lo, nm], {opacity: 0, filter: "blur(14px) brightness(2)", duration: .4, ease: "power2.in"}, Math.max(d + 1.9, f - .4));
};
