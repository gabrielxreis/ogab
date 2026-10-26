// EFEITO · recorte de papel: a sala some atrás de uma colagem (papel kraft, pedaços rasgados, fita, rabiscos de giz) que
// entra em stop motion (12 qps); a silhueta da pessoa ganha borda branca grossa + sombra (recorte colado) e uma palavra de
// letras de bilhete aparece acima da cabeça. Camada atrás: a pessoa de verdade fica por cima do próprio "recorte".
ESTILO["recorte-papel"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const tl = C.tl, d = it.de, f = it.ate, uid = "rp" + Math.round(d * 1000);
  C.css("recorte-papel", `
    .rp{position:absolute;inset:0;overflow:hidden}
    .rp-fundo{position:absolute;inset:-20px;background:#C9A77C;
      background-image:radial-gradient(rgba(255,255,255,.12) 1px,transparent 1.5px),radial-gradient(rgba(60,35,10,.12) 1px,transparent 1.5px);
      background-size:7px 7px,11px 11px;background-position:0 0,3px 5px}
    .rp-peca{position:absolute;box-shadow:0 10px 24px rgba(0,0,0,.28)}
    .rp-fita{position:absolute;width:150px;height:44px;background:rgba(240,232,205,.78);box-shadow:0 2px 6px rgba(0,0,0,.15);
      clip-path:polygon(0 8%,4% 0,8% 10%,12% 0,100% 0,96% 12%,100% 22%,96% 34%,100% 46%,96% 58%,100% 70%,96% 84%,100% 100%,0 100%,4% 86%,0 72%,4% 58%,0 44%,4% 30%,0 18%)}
    .rp-v{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:fill}
    .rp-giz{position:absolute;left:0;top:0;overflow:visible}
    .rp-giz path{fill:none;stroke:rgba(255,255,255,.95);stroke-width:11;stroke-linecap:round;stroke-linejoin:round;filter:url(#${uid}g)}
    .rp-pal{position:absolute;left:0;right:0;text-align:center;white-space:nowrap}
    .rp-pal span{display:inline-block;margin:0 4px;padding:6px 16px 10px;line-height:1;box-shadow:0 8px 18px rgba(0,0,0,.3)}`);
  const box = C.el("div", "rp");
  C.el("div", null, box, `<svg width="0" height="0" style="position:absolute">
    <filter id="${uid}b" x="-5%" y="-5%" width="110%" height="110%"><feMorphology in="SourceAlpha" operator="dilate" radius="16" result="a"/>
      <feTurbulence type="fractalNoise" baseFrequency=".05" numOctaves="1" seed="3" result="t"/>
      <feDisplacementMap in="a" in2="t" scale="10" xChannelSelector="R" yChannelSelector="G" result="d"/>
      <feFlood flood-color="#fff"/><feComposite in2="d" operator="in" result="w"/>
      <feDropShadow in="w" dx="10" dy="14" stdDeviation="10" flood-color="#000" flood-opacity=".45"/></filter>
    <filter id="${uid}g"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="1" seed="5" result="n"/>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="5" result="x"/>
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.1 1.5" result="m"/><feComposite in="x" in2="m" operator="in"/></filter></svg>`);
  const fundo = C.el("div", "rp-fundo", box);
  // pedaços de papel rasgado (borda serrilhada própria, gerada por semente)
  const rasgo = (seed) => { const p = []; let s = seed; const rnd = () => (s = (s * 9301 + 49297) % 233280) / 233280;
    for (let i = 0; i <= 10; i++) p.push(`${i * 10}% ${rnd() * 6}%`); for (let i = 0; i <= 10; i++) p.push(`${100 - rnd() * 5}% ${i * 10}%`);
    for (let i = 10; i >= 0; i--) p.push(`${i * 10}% ${100 - rnd() * 6}%`); for (let i = 10; i >= 0; i--) p.push(`${rnd() * 5}% ${i * 10}%`);
    return `polygon(${p.join(",")})`; };
  const PECAS = [ // x, y, w, h (frações do quadro), cor, rotação
    [-.06, .04, .62, .3, "#EDE6D6", -6], [.5, .1, .6, .26, "color-mix(in srgb, var(--dest) 70%, #fff)", 5], [-.1, .42, .44, .34, "#2E3A4F", 4],
    [.62, .46, .5, .3, "#E9DCC0", -4], [.22, .7, .6, .32, "#D7CBB4", 2], [.05, .2, .3, .16, "#F3D9C9", 9]];
  const pecas = PECAS.map(([x, y, w, h, cor, rot], i) => {
    const e = C.el("div", "rp-peca", box);
    Object.assign(e.style, {left: x * W + "px", top: y * H + "px", width: w * W + "px", height: h * H + "px", background: cor, clipPath: rasgo(i * 37 + 11)});
    e.style.transform = `rotate(${rot}deg)`; e.dataset.rot = rot;
    if (i === 3) e.style.background = `repeating-linear-gradient(0deg, ${cor} 0 46px, rgba(70,110,170,.35) 46px 48px)`;   // folha pautada
    return e;
  });
  const fitas = [[.06, .06, -12], [.66, .1, 10], [.12, .46, 30], [.74, .48, -24]].map(([x, y, rot]) => {
    const e = C.el("div", "rp-fita", box); Object.assign(e.style, {left: x * W + "px", top: y * H + "px"}); e.dataset.rot = rot; e.style.transform = `rotate(${rot}deg)`; return e;
  });
  // rabiscos de giz ao redor (seta, estrelinha, sublinhado em onda, círculo)
  const gz = C.el("div", null, box, `<svg class="rp-giz" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <path pathLength="1" d="M${W * .1} ${H * .62} q 60 -80 150 -40 t 120 -30 m -30 -30 l 34 28 l -40 22"/>
    <path pathLength="1" d="M${W * .82} ${H * .3} l 14 34 l 36 4 l -28 22 l 10 36 l -32 -20 l -32 20 l 10 -36 l -28 -22 l 36 -4 z"/>
    <path pathLength="1" d="M${W * .62} ${H * .78} c 30 -24 60 24 90 0 s 60 24 90 0 s 60 24 90 0"/>
    <path pathLength="1" d="M${W * .2} ${H * .27} c -60 -10 -80 60 -20 76 c 60 14 110 -40 60 -70 c -30 -16 -70 -4 -84 10"/></svg>`).firstChild;
  // a pessoa como recorte: borda branca + sombra a partir da silhueta
  let v = null;
  if (P.silhueta) {
    v = C.video(P.silhueta, box, "rp-v"); v.style.filter = `url(#${uid}b)`;
  }
  // letras de bilhete acima da cabeça
  const pal = String(it.palavra || ""), ESTILOS = [["#111", "#fff", "PalcoSans", 900, "normal"], ["#fff", "#111", "PalcoSerif", 600, "italic"],
    ["var(--dest)", "#111", "PalcoSans", 800, "normal"], ["#F2E8D0", "#B0382C", "PalcoSerif", 400, "italic"], ["#B0382C", "#fff", "PalcoSans", 700, "normal"]];
  const tam = Math.min(150, (W - 2 * S.lado - 80) / Math.max(3, pal.length) * 1.05);
  const pw = C.el("div", "rp-pal", box); pw.style.top = Math.max(S.topo, r[1] - tam * 1.55 - 30) + "px";
  const letras = [...pal].map((c, i) => {
    const [bg, cor, fam, peso, est] = ESTILOS[(i * 3 + 1) % ESTILOS.length];
    const e = C.el("span", null, pw, c === " " ? "&nbsp;" : C.esc(c));
    Object.assign(e.style, {background: bg, color: cor, fontFamily: fam, fontWeight: peso, fontStyle: est, fontSize: Math.round(tam * (i % 2 ? .9 : 1.05)) + "px",
                            transform: `rotate(${((i * 37) % 13) - 6}deg) translateY(${((i * 17) % 5) * 6 - 12}px)`, clipPath: rasgo(i * 53 + 7)});
    return e;
  });
  // tempo: tudo em "passos" (stop motion 12 qps)
  const st = "steps(5)";
  tl.set(box, {opacity: 0}, 0).set(box, {opacity: 1}, d)
    .fromTo(fundo, {clipPath: "circle(0% at 50% 50%)"}, {clipPath: "circle(80% at 50% 50%)", duration: .4, ease: st}, d)
    .fromTo(pecas, {y: (i) => (i % 2 ? -1 : 1) * 260, rotation: (i, e) => +e.dataset.rot + (i % 2 ? 25 : -25), opacity: 0},
            {y: 0, rotation: (i, e) => +e.dataset.rot, opacity: 1, duration: .42, ease: st, stagger: .06}, d + .05)
    .fromTo(fitas, {scale: 1.6, opacity: 0, rotation: (i, e) => +e.dataset.rot}, {scale: 1, opacity: 1, rotation: (i, e) => +e.dataset.rot, duration: .25, ease: "steps(3)", stagger: .06}, d + .4)
    .fromTo(gz.querySelectorAll("path"), {strokeDasharray: 1, strokeDashoffset: 1}, {strokeDashoffset: 0, duration: .5, ease: "steps(6)", stagger: .1}, d + .5)
    .fromTo(letras, {scale: 0, opacity: 0}, {scale: 1, opacity: 1, duration: .2, ease: "steps(3)", stagger: .08}, d + .55);
  if (v) tl.fromTo(v, {opacity: 0}, {opacity: 1, duration: .15, ease: "steps(2)"}, d + .25);
  for (let t = d + 1, k = 0; t < f - .4; t += 1 / 6, k++)   // tremidinha de animação quadro a quadro nas letras
    tl.set(letras, {x: (i) => ((k + i) % 3 - 1) * 3, y: (i) => ((k * 2 + i) % 3 - 1) * 3}, t);
  tl.to(box, {clipPath: "inset(0 0 0 100%)", duration: .35, ease: "steps(5)"}, Math.max(d + 1, f - .35)).set(box, {opacity: 0, clipPath: "none"}, f);
};
