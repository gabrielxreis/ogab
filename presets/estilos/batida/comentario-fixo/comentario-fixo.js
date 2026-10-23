// BATIDA · recado fixo no topo: uma linha em letra manuscrita (branca, sombra suave) se escreve da esquerda para a direita no
// início e fica parada até o fim; um traço feito à mão na cor da marca sublinha. Palavras em CAIXA ALTA no texto ganham a cor
// da marca. Encolhe para caber acima da cabeça (de it.de a it.ate: o Gab põe o vídeo inteiro).
ESTILO["comentario-fixo"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro;
  C.css("comentario-fixo", `
    .cf{position:absolute;left:${S.lado + 20}px;right:${S.lado + 20}px;text-align:center;font-family:"PalcoHand","PalcoSans";font-weight:400;
        color:#fff;line-height:1.08;text-shadow:0 3px 14px rgba(0,0,0,.6),0 1px 2px rgba(0,0,0,.5)}
    .cf em{font-style:normal;color:var(--dest)}
    .cf svg{display:block;margin:6px auto 0;overflow:visible}`);
  const txt = String(it.texto || ""), r = C.rostoEm(it.de) || [W * .3, H * .3, W * .7, H * .55];
  const larg = W - 2 * (S.lado + 20), livre = Math.max(80, r[1] - 40 - S.topo);
  let tam = Math.min(78, larg / Math.max(8, txt.length) / .44);
  const linhas = Math.ceil(txt.length * tam * .44 / larg); if (linhas * tam * 1.08 + 30 > livre) tam = Math.max(40, (livre - 30) / 1.08 / Math.max(1, linhas));
  const e = C.el("div", "cf"); Object.assign(e.style, {top: S.topo + "px", fontSize: Math.round(tam) + "px"});
  const html = C.esc(txt).replace(/\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ]{2,})\b/g, "<em>$1</em>");
  const lw = Math.min(larg * .7, txt.length * tam * .3);
  e.innerHTML = `<div class="tx">${html}</div><svg width="${lw}" height="18"><path d="M2 12 C ${lw * .25} 4, ${lw * .5} 16, ${lw * .75} 8 S ${lw - 4} 10, ${lw - 2} 7"
    fill="none" stroke="var(--dest)" stroke-width="6" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/></svg>`;
  const tl = C.tl, d = it.de, f = it.ate, tx = e.querySelector(".tx"), sub = e.querySelector("path");
  tl.fromTo(tx, {clipPath: "inset(0 100% 0 0)", opacity: 1}, {clipPath: "inset(0 0% 0 0)", duration: Math.min(1.2, .25 + txt.length * .025), ease: "none"}, d)
    .to(sub, {attr: {"stroke-dashoffset": 0}, duration: .45, ease: "power2.out"}, d + Math.min(1.2, .25 + txt.length * .025))
    .to(e, {opacity: 0, duration: .3}, Math.max(d + 1.8, f - .3));
};
