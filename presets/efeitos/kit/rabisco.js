// RABISCO (Rough.js): círculo, sublinhado, seta, caixa, X e preenchimento HACHURADO à mão, que se desenham e
// "fervem" (3 variações trocando a cada 0,12 s, como animação desenhada). Semente fixa: sai igual em todo render.
// EFX.rabisco(tl, svg, { forma: "circulo|sublinhado|seta|caixa|x|hachura", x, y, w, h, cor, de, desenho: .6, ate, espessura: 4,
//                       hachura: "hachure|cross-hatch|zigzag", seed }) -> desenha na timeline (sem draw(t)).
EFX.rabisco = function (tl, svg, o) {
  o = Object.assign({ cor: "#F2D16B", espessura: 4, desenho: .6, seed: 7, rugosidade: 1.6, hachura: "hachure" }, o);
  const rc = rough.svg(svg), NS = "http://www.w3.org/2000/svg", g = document.createElementNS(NS, "g"); svg.appendChild(g);
  const variacoes = [0, 1, 2].map(k => {
    const op = { stroke: o.cor, strokeWidth: o.espessura, roughness: o.rugosidade, seed: o.seed + k * 13, bowing: 1.4 };
    const { x, y, w, h } = o; let n;
    switch (o.forma) {
      case "circulo": n = rc.ellipse(x + w / 2, y + h / 2, w * 1.12, h * 1.3, op); break;
      case "sublinhado": n = rc.curve([[x, y + h], [x + w * .5, y + h + 6], [x + w, y + h - 4]], op); break;
      case "seta": { const ang = Math.atan2(h, w), ex = x + w, ey = y + h, a1 = ang + 2.6, a2 = ang - 2.6;
        n = document.createElementNS(NS, "g"); n.appendChild(rc.curve([[x, y], [x + w * .45, y + h * .2], [ex, ey]], op));
        n.appendChild(rc.linearPath([[ex + Math.cos(a1) * 34, ey + Math.sin(a1) * 34], [ex, ey], [ex + Math.cos(a2) * 34, ey + Math.sin(a2) * 34]], op)); break; }
      case "caixa": n = rc.rectangle(x, y, w, h, op); break;
      case "x": n = document.createElementNS(NS, "g"); n.appendChild(rc.line(x, y, x + w, y + h, op)); n.appendChild(rc.line(x + w, y, x, y + h, op)); break;
      case "hachura": n = rc.rectangle(x, y, w, h, Object.assign({}, op, { fill: o.cor, fillStyle: o.hachura, hachureGap: o.gap || 14, fillWeight: o.espessura * .6, hachureAngle: -41 })); break;
    }
    g.appendChild(n); return n;
  });
  const linhas = variacoes.map(v => [...v.querySelectorAll("path")]);
  linhas.flat().forEach(p => { const L = p.getTotalLength(); p.style.strokeDasharray = L; p.style.strokeDashoffset = L; p.setAttribute("stroke-linecap", "round"); });
  tl.set(variacoes, { opacity: 0 }, 0);
  // desenha a variação 0 traço a traço, depois as 3 se alternam (boil) até o fim
  const ps = linhas[0], passo = o.desenho / ps.length;
  tl.set(variacoes[0], { opacity: 1 }, o.de);
  ps.forEach((p, i) => tl.to(p, { strokeDashoffset: 0, duration: passo, ease: "power1.inOut" }, o.de + i * passo));
  linhas.slice(1).flat().forEach(p => tl.set(p, { strokeDashoffset: 0 }, o.de + o.desenho));
  const fim = o.ate ?? o.de + o.desenho + 3;
  for (let t = o.de + o.desenho, k = 0; t < fim; t += .12, k++) variacoes.forEach((v, j) => tl.set(v, { opacity: j === k % 3 ? 1 : 0 }, t));
  if (o.ate != null) tl.to(variacoes, { opacity: 0, duration: .2 }, o.ate);
  return g;
};
