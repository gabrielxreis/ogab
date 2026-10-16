// Biblioteca de efeitos extras para qualquer composição HyperFrames do Gab (window.EFX).
// Regra do render: o HyperFrames salta de quadro em quadro, então todo efeito é uma função PURA do tempo
// (draw(t)), ligada à timeline por um único tween de 0 até o fim (padrão do point cloud).
window.EFX = window.EFX || {};
EFX.relogio = function (tl, dur, draw) {
  const est = { t: 0 };
  tl.to(est, { t: dur, duration: dur, ease: "none", onUpdate: () => draw(est.t) }, 0);
  draw(0);
};
EFX.rng = function (seed) { let s = seed >>> 0 || 1; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); };
EFX.lim = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
EFX.suave = p => p * p * (3 - 2 * p);
EFX.canvas = function (pai, w, h, css) {   // canvas na resolução certa, posicionado em px
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  Object.assign(c.style, { position: "absolute", width: w + "px", height: h + "px" }, css || {}); pai.appendChild(c); return c;
};
EFX.texto_canvas = function (texto, o) {   // texto renderizado num canvas (fonte de ASCII e LUPA)
  o = Object.assign({ w: 900, h: 400, fonte: "900 220px CS", cor: "#fff", fundo: null, linha: 1.05, alinhar: "center" }, o || {});
  const c = document.createElement("canvas"); c.width = o.w; c.height = o.h; const x = c.getContext("2d");
  if (o.fundo) { x.fillStyle = o.fundo; x.fillRect(0, 0, o.w, o.h); }
  x.fillStyle = o.cor; x.font = o.fonte; x.textAlign = o.alinhar; x.textBaseline = "middle";
  const linhas = String(texto).split("\n"), tam = parseFloat(o.fonte.match(/(\d+)px/)[1]);
  const pinta = () => { x.clearRect(0, 0, o.w, o.h); if (o.fundo) { x.fillStyle = o.fundo; x.fillRect(0, 0, o.w, o.h); }
    x.fillStyle = o.cor; x.font = o.fonte; x.textAlign = o.alinhar; x.textBaseline = "middle";
    linhas.forEach((l, i) => x.fillText(l, o.alinhar === "left" ? 0 : o.w / 2, o.h / 2 + (i - (linhas.length - 1) / 2) * tam * o.linha)); };
  pinta(); document.fonts.load(o.fonte).then(pinta);   // redesenha com a fonte certa (no load ela ainda não chegou)
  return c;
};
