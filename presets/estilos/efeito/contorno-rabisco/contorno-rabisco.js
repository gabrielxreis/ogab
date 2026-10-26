// EFEITO · contorno rabiscado: a silhueta da pessoa (P.silhueta) vira dois traços brancos tremidos (dilata o alfa, desloca com
// ruído e fica só o anel), "fervendo" 8x por segundo como desenho à mão; rabiscos (corações, brilhos) ao lado da cabeça.
// Camada atrás: a pessoa recortada fica por cima e esconde o miolo, sobra só a linha em volta.
ESTILO["contorno-rabisco"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const tl = C.tl, d = it.de, f = it.ate, uid = "cr" + Math.round(d * 1000);
  C.css("contorno-rabisco", `
    .cb{position:absolute;inset:0}
    .cb-v{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:fill}
    .cb-svg{position:absolute;left:0;top:0;overflow:visible}
    .cb-svg path{fill:none;stroke:#fff;stroke-width:9;stroke-linecap:round;stroke-linejoin:round;filter:drop-shadow(0 3px 6px rgba(0,0,0,.35))}
    .cb-svg path.d{stroke:var(--dest)}`);
  const box = C.el("div", "cb");
  // filtro: anel = (alfa dilatado R) menos (alfa dilatado R-6), com deslocamento por ruído; duas linhas com sementes diferentes
  const anel = (k, R, esc) => `
      <feMorphology in="SourceAlpha" operator="dilate" radius="${R}" result="a${k}"/>
      <feMorphology in="SourceAlpha" operator="dilate" radius="${R - 9}" result="b${k}"/>
      <feComposite in="a${k}" in2="b${k}" operator="out" result="c${k}"/>
      <feTurbulence class="cb-t" type="fractalNoise" baseFrequency="0.018" numOctaves="2" seed="${k * 7}" result="t${k}"/>
      <feDisplacementMap in="c${k}" in2="t${k}" scale="${esc}" xChannelSelector="R" yChannelSelector="G" result="d${k}"/>`;
  const defs = C.el("div", null, box, `<svg width="0" height="0" style="position:absolute"><filter id="${uid}" x="-10%" y="-10%" width="120%" height="120%">
      ${anel(1, 18, 20)}${anel(2, 30, 28)}
      <feMerge result="m"><feMergeNode in="d1"/><feMergeNode in="d2"/></feMerge>
      <feFlood flood-color="#fff"/><feComposite in2="m" operator="in"/></filter></svg>`);
  let v = null;
  if (P.silhueta) {
    v = C.video(P.silhueta, box, "cb-v"); v.style.filter = `url(#${uid})`;
  }
  // rabiscos ao lado e acima da cabeça (fora da caixa do rosto)
  const FORMA = {
    coracao: `M0 18 C -26 -2 -22 -26 -6 -24 C 0 -23 0 -16 0 -12 C 0 -16 2 -24 8 -24 C 24 -26 26 -2 0 18 Z`,
    brilho: `M0 -26 C 3 -6 6 -3 26 0 C 6 3 3 6 0 26 C -3 6 -6 3 -26 0 C -6 -3 -3 -6 0 -26 Z`,
    estrela: `M0 -24 L7 -7 L24 -6 L10 5 L15 23 L0 12 L-15 23 L-10 5 L-24 -6 L-7 -7 Z`,
    espiral: `M0 0 C 6 -6 14 2 8 10 C 0 20 -16 10 -14 -4 C -12 -20 12 -24 20 -10 C 26 2 22 18 8 24`,
  };
  const fw = r[2] - r[0], fh = r[3] - r[1];
  const vagas = [[r[0] - fw * .38, r[1] + fh * .15, 1.6, -12], [r[2] + fw * .3, r[1] - fh * .05, 1.2, 10], [r[0] - fw * .15, r[1] - fh * .28, 1, 0],
                 [r[2] + fw * .12, r[1] - fh * .32, 1.3, 14], [r[2] + fw * .42, r[1] + fh * .4, 1, -8], [r[0] - fw * .45, r[1] - fh * .1, .9, 0]];
  const svg = C.el("div", null, box, `<svg class="cb-svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"></svg>`).firstChild, rb = [];
  (it.rabiscos || []).slice(0, vagas.length).forEach((nome, i) => {
    const [x, y, s, rot] = vagas[i], px = Math.min(W - S.lado - 40, Math.max(S.lado + 40, x)), py = Math.max(S.topo, y);
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("transform", `translate(${px} ${py}) rotate(${rot}) scale(${s * 2.8})`);   // posição fixa; o tremor vai no <g> de dentro
    g.innerHTML = `<g><path class="${i % 2 ? "" : "d"}" pathLength="1" d="${FORMA[nome] || FORMA.brilho}" style="stroke-width:${3.8 / s}"/></g>`;
    svg.appendChild(g); rb.push(g.querySelector("path"));
  });
  // tempo: contorno desenha de cima para baixo; tudo "ferve" (troca a semente do ruído e o tremor dos rabiscos) a 8 qps
  tl.set(box, {opacity: 0}, 0).set(box, {opacity: 1}, d);
  if (v) tl.fromTo(v, {clipPath: "inset(0 0 100% 0)"}, {clipPath: "inset(0 0 0% 0)", duration: .55, ease: "power2.inOut"}, d);
  rb.forEach((p, i) => tl.fromTo(p, {strokeDasharray: 1, strokeDashoffset: 1}, {strokeDashoffset: 0, duration: .4, ease: "power1.inOut"}, d + .25 + i * .1));
  const turbs = box.querySelectorAll(".cb-t");
  for (let t = d, k = 0; t < f; t += 1 / 8, k++) {
    turbs.forEach((tb, j) => tl.set(tb, {attr: {seed: (k * 13 + j * 7) % 97 + 1}}, t));
    rb.forEach((p, i) => tl.set(p.parentNode, {x: ((k + i) % 3 - 1) * 2, y: ((k * 2 + i) % 3 - 1) * 2}, t));
  }
  tl.to(box, {opacity: 0, duration: .25, ease: "power1.in"}, Math.max(d + .8, f - .25));
};
