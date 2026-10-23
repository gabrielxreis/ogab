// EFEITO · gráfico neon atrás: grade apagada + linha brilhante (cor da marca) que se desenha da base esquerda até o alto
// direito passando atrás da pessoa; no fim um estouro de luz e o número acende acima da cabeça.
ESTILO["grafico-neon"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  C.css("grafico-neon", `
    .gn{position:absolute;left:0;top:0}
    .gn .grade{stroke:rgba(255,255,255,.09);stroke-width:2}
    .gn .lz{fill:none;stroke:var(--dest);stroke-width:26;stroke-linecap:round;stroke-linejoin:round;opacity:.35;filter:blur(14px)}
    .gn .ln{fill:none;stroke:var(--dest);stroke-width:9;stroke-linecap:round;stroke-linejoin:round}
    .gn .nu{fill:none;stroke:#fff;stroke-width:3;stroke-linecap:round;stroke-linejoin:round;opacity:.8}
    .gn-n{position:absolute;text-align:right;color:#fff;font-weight:900;letter-spacing:-.04em;line-height:.9;
          text-shadow:0 0 18px var(--dest),0 0 42px var(--dest),0 0 90px var(--dest)}
    .gn-r{position:absolute;text-align:right;font-family:"PalcoSerif";font-style:italic;font-weight:600;color:#fff;opacity:.9;
          text-shadow:0 4px 18px rgba(0,0,0,.5)}`);
  // pontos da curva: começa embaixo à esquerda, oscila, sobe forte e termina no alto à direita (acima da cabeça)
  const topoN = S.topo + 40, fim = [W - S.lado - 70, Math.min(r[1] - 120, topoN + 170)];
  const base = Math.min(H - S.baixo, r[3] - (r[3] - r[1]) * .15), pts = [[-30, base], [W * .18, base - 70], [W * .33, base - 30], [W * .5, base - 190],
    [W * .62, base - 150], [W * .76, (base + fim[1]) / 2 + 40], fim];
  let dpath = `M${pts[0]}`;
  for (let i = 1; i < pts.length; i++) { const a = pts[i - 1], b = pts[i], mx = (a[0] + b[0]) / 2; dpath += ` C${mx},${a[1]} ${mx},${b[1]} ${b[0]},${b[1]}`; }
  let grade = "";
  for (let y = S.topo; y < H - 300; y += 160) grade += `<line class="grade" x1="0" y1="${y}" x2="${W}" y2="${y}"/>`;
  for (let x = 90; x < W; x += 180) grade += `<line class="grade" x1="${x}" y1="${S.topo}" x2="${x}" y2="${H - 300}"/>`;
  const svg = C.el("div", "gn", null, `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><g class="g">${grade}</g>
     <path class="lz" d="${dpath}"/><path class="ln" d="${dpath}"/><path class="nu" d="${dpath}"/>
     <circle class="pt" cx="${fim[0]}" cy="${fim[1]}" r="20" fill="#fff"/>
     <circle class="an" cx="${fim[0]}" cy="${fim[1]}" r="20" fill="none" stroke="var(--dest)" stroke-width="6"/></svg>`);
  const s = svg.querySelector("svg"), linhas = s.querySelectorAll(".lz,.ln,.nu"), len = s.querySelector(".ln").getTotalLength() + 4;
  linhas.forEach(l => { l.style.strokeDasharray = len; l.style.strokeDashoffset = len; });
  const num = String(it.numero || ""), tam = Math.min(190, (W * .62) / Math.max(3, num.length) / .58);
  const n = C.el("div", "gn-n", null, C.esc(num)), rot = C.el("div", "gn-r", null, C.esc(it.rotulo || ""));
  Object.assign(n.style, {right: (W - fim[0] + 50) + "px", top: (fim[1] - tam * .5) + "px", fontSize: Math.round(tam) + "px"});
  Object.assign(rot.style, {right: (W - fim[0] + 54) + "px", top: (fim[1] + tam * .5) + "px", fontSize: Math.round(tam * .3) + "px"});
  const tl = C.tl, d = it.de, f = it.ate, des = Math.min(1.1, Math.max(.6, (f - d) * .4)), pico = d + .15 + des;
  tl.set([svg, n, rot, s.querySelector(".pt"), s.querySelector(".an")], {opacity: 0}, 0).set(svg, {opacity: 1}, d)
    .fromTo(s.querySelector(".g"), {opacity: 0}, {opacity: 1, duration: .35}, d)
    .to(linhas, {strokeDashoffset: 0, duration: des, ease: "power2.in"}, d + .15)
    .fromTo(s.querySelector(".pt"), {scale: 0, opacity: 1, transformOrigin: "50% 50%"}, {scale: 1, duration: .3, ease: "back.out(3)"}, pico - .05)
    .fromTo(s.querySelector(".an"), {scale: 1, opacity: 1, transformOrigin: "50% 50%"}, {scale: 5, opacity: 0, duration: .6, ease: "power2.out"}, pico)
    .fromTo(n, {opacity: 0, scale: .6, filter: "blur(10px)"}, {opacity: 1, scale: 1, filter: "blur(0px)", duration: .4, ease: "back.out(2)"}, pico)
    .fromTo(rot, {opacity: 0, y: 16}, {opacity: 1, y: 0, duration: .35, ease: "power3.out"}, pico + .15)
    .to([svg, n, rot], {opacity: 0, duration: .4, ease: "power2.in"}, Math.max(pico + .8, f - .4));
};
