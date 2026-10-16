// ASCII (como o filtro do PixiJS, em canvas 2D): a fonte (texto, imagem ou canvas) vira caracteres pela luz.
// EFX.ascii(canvas, fonte, { cel: 14, cor: "#F2D16B", chars: " .:-=+*#%@", modo: "revela|dissolve|fixo" }) -> draw(p)
//   p 0->1: "revela" = ruído de caracteres -> ASCII -> imagem limpa; "dissolve" = o contrário; "fixo" = só ASCII embaralhando.
EFX.ascii = function (cv, fonte, o) {
  o = Object.assign({ cel: 14, cor: "#F2D16B", chars: " .:-=+*#%@", modo: "revela", fonteCss: "700 15px monospace" }, o);
  const ctx = cv.getContext("2d"), W = cv.width, H = cv.height, cols = Math.ceil(W / o.cel), rows = Math.ceil(H / (o.cel * 1.25));
  const amostra = document.createElement("canvas"); amostra.width = cols; amostra.height = rows; const ax = amostra.getContext("2d", { willReadFrequently: true });
  let lum = null;
  const ler = () => { ax.clearRect(0, 0, cols, rows); ax.drawImage(fonte, 0, 0, cols, rows); const d = ax.getImageData(0, 0, cols, rows).data;
    lum = new Float32Array(cols * rows); for (let i = 0; i < cols * rows; i++) lum[i] = (d[i * 4] * .3 + d[i * 4 + 1] * .59 + d[i * 4 + 2] * .11) / 255 * (d[i * 4 + 3] / 255); };
  const h = (i, k) => { const x = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x); };
  return function draw(p, t) {
    if (!lum || fonte.tagName === "VIDEO") ler();
    p = EFX.lim(p); const fase = o.modo === "dissolve" ? 1 - p : p, quadro = Math.floor((t ?? p * 6) * 12);
    ctx.clearRect(0, 0, W, H);
    const limpo = o.modo === "fixo" ? 0 : EFX.lim((fase - .65) / .35);
    if (limpo > 0) { ctx.globalAlpha = limpo; ctx.drawImage(fonte, 0, 0, W, H); ctx.globalAlpha = 1; }
    ctx.font = o.fonteCss; ctx.fillStyle = o.cor; ctx.textBaseline = "top";
    const ruido = o.modo === "fixo" ? .15 : EFX.lim(1 - fase / .45), forma = o.modo === "fixo" ? 1 : EFX.lim(fase / .35);
    ctx.globalAlpha = 1 - limpo * .9;
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      const i = r * cols + c, l = lum[i], n = h(i, quadro);
      let v = l * forma + (n < .12 ? n * 4 : 0) * ruido * (1 - l);
      if (o.modo !== "fixo" && h(i, 7) > fase * 1.4 + .1) v *= .15;
      if (v < .06) continue;
      const ch = o.chars[Math.min(o.chars.length - 1, Math.floor(v * o.chars.length + (n - .5) * ruido * 3))] || o.chars[1];
      ctx.fillText(ch, c * o.cel, r * o.cel * 1.25);
    }
    ctx.globalAlpha = 1;
  };
};
