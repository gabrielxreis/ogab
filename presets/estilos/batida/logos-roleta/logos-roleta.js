// BATIDA · roleta de logos: um bloco branco troca de marca cada vez mais devagar (corte seco, sem giro); na última, a frase entra ao lado.
ESTILO["logos-roleta"] = (it, C) => {
  const P = C.P, W = P.w, lado = 210, logos = (it.logos || []).slice(0, 10);
  C.css("logos-roleta", `
    .lr{position:absolute;left:0;right:0;display:flex;justify-content:center;align-items:center;gap:34px;font-family:"PalcoSans"}
    .lr .bx{position:relative;width:${lado}px;height:${lado}px;border-radius:40px;background:#fff;box-shadow:0 14px 40px rgba(0,0,0,.3);flex:none}
    .lr .lg{position:absolute;inset:28px;display:grid;place-items:center}
    .lr .lg img{width:100%;height:100%;object-fit:contain}
    .lr .mk{width:100%;height:100%;border-radius:26px;display:grid;place-items:center;font-weight:900;font-size:80px;color:#fff}
    .lr .fr{font-weight:900;font-size:60px;line-height:1.05;color:#fff;text-transform:uppercase;letter-spacing:-.02em;max-width:${W - lado - 160}px;
            text-shadow:0 8px 28px rgba(0,0,0,.45);overflow:hidden;padding-bottom:.08em}
    .lr .fr span{display:inline-block}.lr .fr em{font-style:normal;color:var(--dest)}`);
  const CORES = ["#15171a", "#3a4a5c", "#6b3d2e", "#2f4a3a", "#4a3a5c", "#5c5a3a"];
  const lim = P.h - C.seguro.baixo, r = C.rostoEm(it.de), alto = lado;
  let y = lim - alto;
  if (r && r[3] + 40 + alto <= lim) y = r[3] + 40; else if (r && r[1] - 40 - alto >= C.seguro.topo) y = r[1] - 40 - alto;
  const box = C.el("div", "lr"); box.style.top = y + "px";
  const bx = C.el("div", "bx", box);
  const ls = logos.map((l, i) => C.el("div", "lg", bx, l.logo ? `<img src="${C.esc(l.logo)}">`
    : `<div class="mk" style="background:${CORES[i % CORES.length]}">${C.esc(String(l.nome || "?").slice(0, 1).toUpperCase())}</div>`));
  const ws = String(it.frase || "").split(/\s+/).filter(Boolean);
  const fr = C.el("div", "fr", box, `<span>${ws.map((w, i) => i === ws.length - 1 ? `<em>${C.esc(w)}</em>` : C.esc(w)).join(" ")}</span>`);
  const tl = C.tl, d = it.de, f = it.ate;
  tl.set(box, {opacity: 0}, 0).set(box, {opacity: 1}, d).set(ls, {opacity: 0}, 0)
    .fromTo(bx, {scale: .6, opacity: 0}, {scale: 1, opacity: 1, duration: .35, ease: "expo.out"}, d)
    .set(fr, {clipPath: "inset(0 100% 0 0)"}, 0);
  let t = d + .05;
  ls.forEach((l, i) => {   // troca a cada passo, freando: 0,09 s no começo até ~0,3 s no fim
    tl.set(ls, {opacity: 0}, t).set(l, {opacity: 1}, t);
    if (i < ls.length - 1) t += .09 + .22 * Math.pow(i / Math.max(1, ls.length - 2), 2);
  });
  tl.fromTo(bx, {scale: 1.08}, {scale: 1, duration: .3, ease: "power3.out"}, t)
    .to(fr, {clipPath: "inset(0 0% 0 0)", duration: .5, ease: "expo.out"}, t + .1)
    .fromTo(fr.firstElementChild, {yPercent: 100}, {yPercent: 0, duration: .5, ease: "expo.out"}, t + .1)
    .to(box, {y: 40, opacity: 0, duration: .35, ease: "power3.in"}, Math.max(t + .9, f - .35));
};
