// FÍSICA (Matter.js): palavras/cartões caindo, quicando e empilhando. A simulação roda inteira no carregamento
// (passo fixo de 1/60 s, determinística) e vira uma tabela de posições; o draw(t) só lê a tabela.
// EFX.fisica(tl, dur, { corpos: [{el, w, h, x, y, de, angulo, quique}], chao: 1500, paredes: [60, 1020], gravidade: 1.4 })
//   el: elemento absoluto (o centro dele vai para x,y); de: quando entra na cena (cai a partir de y).
EFX.fisica = function (tl, dur, o) {
  const M = Matter, eng = M.Engine.create({ gravity: { x: 0, y: o.gravidade || 1.4 } }), W = o.largura || 1080;
  const est = { isStatic: true, friction: .8 };
  M.Composite.add(eng.world, [M.Bodies.rectangle(W / 2, (o.chao || 1500) + 50, W * 2, 100, est),
    M.Bodies.rectangle((o.paredes || [0, W])[0] - 50, 0, 100, 6000, est), M.Bodies.rectangle((o.paredes || [0, W])[1] + 50, 0, 100, 6000, est)]);
  const cs = o.corpos.map((c, i) => Object.assign({ i, dentro: false }, c, {
    corpo: c.forma === "circulo" ? M.Bodies.circle(c.x, c.y, c.w / 2, { restitution: c.quique ?? .35, friction: .6, angle: c.angulo || 0 })
      : M.Bodies.rectangle(c.x, c.y, c.w, c.h, { restitution: c.quique ?? .3, friction: .7, chamfer: { radius: Math.min(c.h / 2, c.raio ?? 14) }, angle: c.angulo || 0 }) }));
  const fps = 60, n = Math.ceil(dur * fps) + 1, tab = cs.map(() => new Float32Array(n * 3));
  for (let f = 0; f < n; f++) {
    const t = f / fps;
    cs.forEach(c => { if (!c.dentro && t >= (c.de || 0)) { M.Composite.add(eng.world, c.corpo); c.dentro = true;
      if (c.empurrao) M.Body.setVelocity(c.corpo, { x: c.empurrao[0], y: c.empurrao[1] }); if (c.giro) M.Body.setAngularVelocity(c.corpo, c.giro); } });
    cs.forEach((c, k) => { const p = c.corpo.position; tab[k][f * 3] = p.x; tab[k][f * 3 + 1] = p.y; tab[k][f * 3 + 2] = c.corpo.angle; });
    M.Engine.update(eng, 1000 / fps);
  }
  cs.forEach(c => Object.assign(c.el.style, { position: "absolute", left: (-c.w / 2) + "px", top: (-c.h / 2) + "px", width: c.w + "px", height: c.h + "px", opacity: 0 }));
  return function draw(t) {
    const f = Math.min(n - 1, Math.max(0, Math.round(t * fps)));
    cs.forEach((c, k) => { const vis = t >= (c.de || 0) && (c.ate == null || t < c.ate);
      c.el.style.opacity = vis ? 1 : 0;
      c.el.style.transform = `translate(${tab[k][f * 3]}px, ${tab[k][f * 3 + 1]}px) rotate(${tab[k][f * 3 + 2]}rad)`; });
  };
};
