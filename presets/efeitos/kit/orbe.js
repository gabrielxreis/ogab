// ORBE de "IA pensando" (inspirado no thinking-orbs, MIT): esfera de pontos em canvas 2D, 6 estados.
// EFX.orbe(canvas, { estado: "pensando|buscando|resolvendo|ouvindo|escrevendo|moldando", cor: "#fff", pontos: 420 }) -> draw(t)
EFX.orbe = function (cv, o) {
  o = Object.assign({ estado: "pensando", cor: "#ffffff", pontos: 420, ponto: 3.2, vel: 1 }, o);
  const ctx = cv.getContext("2d"), W = cv.width, H = cv.height, R = Math.min(W, H) * .38, N = o.pontos, G = Math.PI * (3 - Math.sqrt(5));
  const base = Array.from({ length: N }, (_, i) => { const y = 1 - (i / (N - 1)) * 2, r = Math.sqrt(1 - y * y), a = G * i; return [Math.cos(a) * r, y, Math.sin(a) * r]; });
  const cubo = base.map(([x, y, z]) => { const m = Math.max(Math.abs(x), Math.abs(y), Math.abs(z)); return [x / m * .8, y / m * .8, z / m * .8]; });
  const toro = base.map((_, i) => { const u = (i / N) * Math.PI * 2 * 13, v = (i / N) * Math.PI * 2; return [(1 + .38 * Math.cos(u)) * Math.cos(v) * .78, .38 * Math.sin(u) * .78, (1 + .38 * Math.cos(u)) * Math.sin(v) * .78]; });
  const rot = (p, ay, ax) => { let [x, y, z] = p; const c = Math.cos(ay), s = Math.sin(ay); [x, z] = [x * c - z * s, x * s + z * c];
    const c2 = Math.cos(ax), s2 = Math.sin(ax); [y, z] = [y * c2 - z * s2, y * s2 + z * c2]; return [x, y, z]; };
  const mix = (a, b, k) => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
  return function draw(t, alfa = 1) {
    t *= o.vel; ctx.clearRect(0, 0, W, H); if (alfa <= 0) return;
    const pts = base.map((p, i) => {
      let q = p, brilho = 1, esc = 1;
      switch (o.estado) {
        case "buscando": { q = rot(p, t * .9, .35); const faixa = Math.sin(t * 2.2) * .9; brilho = .25 + 1.2 * Math.exp(-Math.pow((q[0] - faixa) * 4.5, 2)); break; }
        case "resolvendo": { const tw = Math.sin(t * 1.4) * 1.2 * p[1]; q = rot(p, t * .7 + tw, .5); esc = 1 + .12 * Math.sin(t * 2.8 + p[1] * 3); break; }
        case "ouvindo": { q = rot(p, t * .4, .25); const d = Math.acos(EFX.lim(q[2], -1, 1)); esc = 1 + .1 * Math.sin(d * 7 - t * 6); brilho = .5 + .5 * Math.sin(d * 7 - t * 6); break; }
        case "escrevendo": { q = rot(p, t * .8, .45 + .2 * Math.sin(t)); const fio = (i / N + t * .18) % 1; brilho = .25 + (fio < .35 ? 1.1 * (1 - fio / .35) : 0); break; }
        case "moldando": { const fase = (t * .35) % 3, k = EFX.suave(EFX.lim((fase % 1) * 1.6 - .3)), alvo = [base, cubo, toro], a = alvo[Math.floor(fase)], b = alvo[(Math.floor(fase) + 1) % 3];
          q = rot(mix(a[i], b[i], k), t * .6, .5); break; }
        default: { q = rot(p, t * .6, .4); brilho = .55 + .45 * Math.sin(t * 3 + p[1] * 5 + p[0] * 3); }
      }
      return [q[0] * esc, q[1] * esc, q[2] * esc, brilho];
    }).sort((a, b) => a[2] - b[2]);
    ctx.fillStyle = o.cor;
    pts.forEach(([x, y, z, b]) => { const prof = (z + 1) / 2, s = 1.4 / (2.4 - z);
      ctx.globalAlpha = alfa * EFX.lim((.15 + .85 * prof) * b, 0, 1);
      ctx.beginPath(); ctx.arc(W / 2 + x * R * s, H / 2 + y * R * s, o.ponto * (.55 + .7 * prof), 0, Math.PI * 2); ctx.fill(); });
    ctx.globalAlpha = 1;
  };
};
