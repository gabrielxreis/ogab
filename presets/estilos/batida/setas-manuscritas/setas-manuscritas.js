// BATIDA · notas com seta à mão: nota curta em letra manuscrita CAIXA ALTA (branca, sombra) surge com leve giro e uma seta
// tremida na cor da marca se desenha até o alvo. itens: [{texto, alvo: [x, y], em}] com alvo em fração do quadro (0..1) ou
// pixels; alvo dentro do rosto é puxado para a borda dele (a seta nunca entra no rosto).
ESTILO["setas-manuscritas"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro;
  C.css("setas-manuscritas", `
    .sm{position:absolute;font-family:"PalcoHand","PalcoSans";font-weight:400;font-size:66px;line-height:1;color:#fff;text-transform:uppercase;
        white-space:nowrap;text-shadow:0 3px 14px rgba(0,0,0,.6),0 1px 2px rgba(0,0,0,.5)}
    .sm-s{position:absolute;left:0;top:0;width:${W}px;height:${H}px;overflow:visible;pointer-events:none}`);
  const r = C.rostoEm(it.de) || [W * .3, H * .3, W * .7, H * .55], m = 30, F = [r[0] - m, r[1] - m, r[2] + m, r[3] + m];
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg"); svg.setAttribute("class", "sm-s"); C.root.appendChild(svg);
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const tl = C.tl, d = it.de, f = it.ate, todos = [], itens = it.itens || [];
  const cimaLivre = F[1] - S.topo >= 140;
  itens.forEach((x, i) => {
    const txt = String(x.texto || "").toUpperCase(), tw = Math.min(W - 2 * S.lado, txt.length * 36 + 20);
    let a = x.alvo || [r[2] / W + .04, (r[1] + r[3]) / 2 / H]; a = [a[0] <= 1 ? a[0] * W : a[0], a[1] <= 1 ? a[1] * H : a[1]];
    // nota: acima da cabeça (alternando esquerda/direita) ou abaixo do queixo
    const esq = a[0] <= W / 2;   // nota do lado do alvo (alvo no meio: esquerda)
    const nx = Math.max(S.lado, Math.min(W - S.lado - tw, esq ? W * .5 - tw - 120 + (i % 2) * 40 : W * .5 + 120 - (i % 2) * 40));
    const ny = cimaLivre ? S.topo + 10 + (i % 2) * 90 : Math.min(H - S.baixo - 70, F[3] + 20 + (i % 2) * 90);
    // alvo dentro do rosto: vai para a borda mais próxima da nota
    if (a[0] > F[0] && a[0] < F[2] && a[1] > F[1] && a[1] < F[3]) a = cimaLivre ? [Math.max(F[0], Math.min(F[2], a[0])), F[1]] : [a[0], F[3]];
    const sx = nx + tw / 2, sy = ny + (cimaLivre ? 80 : -10), dx = a[0] - sx, dy = a[1] - sy, L = Math.hypot(dx, dy) || 1;
    const ex = a[0] - dx / L * 26, ey = a[1] - dy / L * 26;   // a ponta para um pouco antes do alvo
    const nxp = -dy / L, nyp = dx / L, cv = (i % 2 ? -1 : 1) * Math.min(120, L * .25);
    const cx = (sx + ex) / 2 + nxp * cv, cy = (sy + ey) / 2 + nyp * cv;
    const ang = Math.atan2(ey - cy, ex - cx), k = 34, ab = .5;   // ponta: dois traços abertos
    const p1 = [ex - k * Math.cos(ang - ab), ey - k * Math.sin(ang - ab)], p2 = [ex - k * Math.cos(ang + ab), ey - k * Math.sin(ang + ab)];
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g"); svg.appendChild(g);
    g.innerHTML = `<path d="M${sx} ${sy} Q${cx + 8} ${cy - 6} ${(cx + ex) / 2} ${(cy + ey) / 2 + 4} T${ex} ${ey}" fill="none" stroke="var(--dest)" stroke-width="8"
        stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,.5))"/>
      <path d="M${p1[0]} ${p1[1]} L${ex} ${ey} L${p2[0]} ${p2[1]}" fill="none" stroke="var(--dest)" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"
        pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>`;
    const n = C.el("div", "sm", null, C.esc(txt)); Object.assign(n.style, {left: nx + "px", top: ny + "px", width: tw + "px", textAlign: "center"});
    const em = typeof x.em === "number" ? x.em : d + .2 + i * 1.1, rot = (i % 2 ? 4 : -4), [c1, c2] = g.querySelectorAll("path");
    tl.fromTo(n, {opacity: 0, scale: 1.3, rotation: rot * 3}, {opacity: 1, scale: 1, rotation: rot, duration: .35, ease: "back.out(2.2)", immediateRender: false}, em)
      .to(c1, {attr: {"stroke-dashoffset": 0}, duration: .45, ease: "power2.inOut"}, em + .2)
      .to(c2, {attr: {"stroke-dashoffset": 0}, duration: .15, ease: "power1.out"}, em + .63);
    n.style.opacity = 0; todos.push(n, g);
  });
  tl.to(todos, {opacity: 0, duration: .35, ease: "power2.in"}, Math.max(d + 1, f - .35));
};
