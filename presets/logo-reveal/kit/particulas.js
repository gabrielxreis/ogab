// Motor de pontos dos presets MARCO e LOGO REVEAL: milhares de pontos num campo que gira devagar e depois se juntam
// numa forma (texto ou logo). Tudo é função do tempo (render(t)) e usa semente: o mesmo quadro sai igual em todo seek.
window.Particulas = function (canvas, W, H, alvos, o = {}) {
  const ctx = canvas.getContext("2d"); canvas.width = W; canvas.height = H;
  let s = o.semente || 7; const rnd = () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const N = o.n || 3600, cx = o.cx ?? W / 2, cy = o.cy ?? H / 2, raio = o.raio || Math.max(W, H) * .55;
  const tam = o.tamanho || Math.max(2.4, W / 340);
  const P = [];
  for (let i = 0; i < N; i++) {
    const a = rnd() * Math.PI * 2, r = raio * Math.pow(rnd(), .62);            // disco mais denso no centro
    const alvo = alvos.length ? alvos[Math.floor(rnd() * alvos.length)] : [cx, cy];
    P.push({ a, r, y0: (rnd() - .5) * .5, alvo, atraso: rnd(), fase: rnd() * 6.283, cor: rnd() < (o.fracCor ?? .28), luz: .45 + rnd() * .55 });
  }
  const easeInOut = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
  // t: tempo do vídeo. junta = [início, duração] da reunião; dissolve = [início, duração] (opcional); apaga = alfa final.
  this.render = (t, { junta = [1, 2], giro = .12, apaga = 1, dissolve = null } = {}) => {
    ctx.clearRect(0, 0, W, H);
    const [j0, jd] = junta;
    for (const p of P) {
      const ang = p.a + t * giro * (1.4 - p.r / raio);
      const fx = cx + Math.cos(ang) * p.r, fy = cy + Math.sin(ang) * p.r * (.62 + p.y0);
      let k = Math.min(1, Math.max(0, (t - j0 - p.atraso * jd * .45) / (jd * .55)));
      if (dissolve) k *= 1 - Math.min(1, Math.max(0, (t - dissolve[0] - p.atraso * dissolve[1] * .5) / (dissolve[1] * .5)));
      const e = easeInOut(k), curva = Math.sin(e * Math.PI) * 60 * (p.atraso - .5);
      const brilho = .75 + .25 * Math.sin(t * 3 + p.fase);
      const x = fx + (p.alvo[0] - fx) * e + curva + (k >= 1 ? Math.sin(t * 2 + p.fase) * .6 : 0);
      const y = fy + (p.alvo[1] - fy) * e - curva * .4;
      ctx.globalAlpha = Math.min(1, p.luz * brilho * (.6 + .4 * e)) * apaga;
      ctx.fillStyle = p.cor ? (o.cor || "#C4A34F") : (o.branco || "#f5f5f7");
      const z = tam * (1 - .2 * e);
      ctx.fillRect(x - z / 2, y - z / 2, z, z);
    }
    ctx.globalAlpha = 1;
  };
};

// Pontos (x, y) de um texto desenhado num canvas escondido: só onde a letra tem tinta, numa grade de "passo" px.
window.pontosDoTexto = function (texto, fonte, tamanho, cx, cy, passo, peso = 400, espaco = 0) {
  const c = document.createElement("canvas"), g = c.getContext("2d");
  g.font = `${peso} ${tamanho}px ${fonte}`; g.letterSpacing = espaco + "px"; const w = Math.ceil(g.measureText(texto).width) + 20, h = Math.ceil(tamanho * 1.3);
  c.width = w; c.height = h; g.font = `${peso} ${tamanho}px ${fonte}`; g.letterSpacing = espaco + "px"; g.textBaseline = "middle"; g.fillStyle = "#fff"; g.fillText(texto, 10, h / 2);
  const d = g.getImageData(0, 0, w, h).data, out = [];
  for (let y = 0; y < h; y += passo) for (let x = 0; x < w; x += passo) if (d[(y * w + x) * 4 + 3] > 128) out.push([cx - w / 2 + x, cy - h / 2 + y]);
  return out;
};
