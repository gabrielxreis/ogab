// EFEITO · capa de revista: moldura fina + título enorme em serifa ATRÁS da cabeça (silhueta da pessoa por cima, na mesma
// camada) + chamadas pequenas nos cantos e linha em serifa itálica embaixo, na frente do peito (nunca no rosto).
ESTILO["capa-revista"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  C.css("capa-revista", `
    .cr{position:absolute;inset:0;overflow:hidden}
    .cr-tom{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.35),rgba(0,0,0,0) 40%,rgba(0,0,0,0) 62%,rgba(0,0,0,.45))}
    .cr-mold{position:absolute;border:3px solid rgba(255,255,255,.9)}
    .cr-tit{position:absolute;left:0;right:0;text-align:center;font-family:"PalcoSerif";font-style:italic;font-weight:400;color:#fff;
            line-height:.8;letter-spacing:-.035em;white-space:nowrap;text-shadow:0 10px 40px rgba(0,0,0,.25)}
    .cr-tit span{display:inline-block}
    .cr-sil{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:fill}
    .cr-ed{position:absolute;font-family:"PalcoSans";font-weight:800;font-size:26px;letter-spacing:.3em;color:#fff}
    .cr-ch{position:absolute;width:300px;font-family:"PalcoSans";font-weight:800;font-size:34px;line-height:1.08;color:#fff;text-shadow:0 3px 14px rgba(0,0,0,.5)}
    .cr-ch:before{content:"";display:block;width:54px;height:6px;background:var(--dest);margin-bottom:14px}
    .cr-num{position:absolute;text-align:right;font-family:"PalcoSans";font-weight:900;color:var(--dest);line-height:.9;text-shadow:0 6px 24px rgba(0,0,0,.4)}
    .cr-num small{display:block;font-size:24px;letter-spacing:.24em;color:#fff;font-weight:800;margin-top:8px}
    .cr-linha{position:absolute;left:0;right:0;text-align:center;font-family:"PalcoSerif";font-style:italic;font-weight:600;color:#fff;
              text-shadow:0 4px 22px rgba(0,0,0,.6)}
    .cr-cod{position:absolute;width:120px;height:62px;background:repeating-linear-gradient(90deg,#111 0 3px,#fff 3px 5px,#111 5px 6px,#fff 6px 10px);
            border:6px solid #fff}`);
  const box = C.el("div", "cr"), tl = C.tl, d = it.de, f = it.ate, m = 40;
  C.el("div", "cr-tom", box);
  const mold = C.el("div", "cr-mold", box); Object.assign(mold.style, {left: m + "px", top: m + "px", right: m + "px", bottom: m + "px"});
  // título: cabe em ~90% da largura, base encostando no alto da cabeça (atrás dela)
  const tit = String(it.titulo || ""), tam = Math.min(W * .9 / Math.max(2, tit.length) / .44, H * .22);
  const t = C.el("div", "cr-tit", box, [...tit].map(c => `<span>${c === " " ? "&nbsp;" : C.esc(c)}</span>`).join(""));
  t.style.fontSize = Math.round(tam) + "px"; t.style.top = Math.max(S.topo - 40, r[1] + (r[3] - r[1]) * .34 - tam * .8) + "px";
  // silhueta da pessoa por cima do título (mesma camada); sem silhueta o título só fica acima da cabeça
  let sil = null;
  if (P.silhueta) {
    sil = C.video(P.silhueta, box, "cr-sil");
  } else t.style.top = Math.max(S.topo - 40, r[1] - tam * .85) + "px";
  const ed = C.el("div", "cr-ed", box, C.esc(it.edicao || "")); Object.assign(ed.style, {left: m + 34 + "px", top: S.topo - 70 + "px"});
  const cod = C.el("div", "cr-cod", box); Object.assign(cod.style, {right: m + 34 + "px", top: S.topo - 90 + "px"});
  // chamadas: ao LADO do rosto (fora da caixa dele) e abaixo do queixo; número grande do outro lado do rosto
  const ch = (it.chamadas || []).slice(0, 3), yCh = r[3] + 90, chs = [];
  const lE = r[0] - 40 - S.lado - 30, lD = W - S.lado - 30 - (r[2] + 40);
  const vagas = [{left: S.lado + 30, top: r[1] + 90, w: Math.max(200, Math.min(300, lE))}, {left: S.lado + 30, top: yCh, w: 300},
                 {right: S.lado + 30, top: yCh + 60, w: 300}];
  ch.forEach((x, i) => {
    const v = vagas[i], e = C.el("div", "cr-ch", box, C.esc(x));
    Object.assign(e.style, {top: v.top + "px", width: v.w + "px"}, v.right != null ? {right: v.right + "px", textAlign: "right"} : {left: v.left + "px"});
    chs.push(e);
  });
  let num = null;
  if (it.numero) {
    num = C.el("div", "cr-num", box, `${C.esc(it.numero)}<small>APROVAM</small>`);
    Object.assign(num.style, {right: S.lado + 30 + "px", top: r[1] + 120 + "px", fontSize: Math.round(Math.min(110, lD / Math.max(2, it.numero.length) * 1.6)) + "px"});
  }
  const linha = C.el("div", "cr-linha", box, C.esc(it.linha || ""));
  linha.style.fontSize = Math.round(Math.min(64, W * .86 / Math.max(8, (it.linha || "").length) * 1.9)) + "px";
  linha.style.top = H - S.baixo - 30 + "px";
  // tempo
  tl.set(box, {opacity: 0}, 0).set(box, {opacity: 1}, d).set(box, {opacity: 0}, f)
    .fromTo(mold, {scale: 1.08, opacity: 0}, {scale: 1, opacity: 1, duration: .45, ease: "power3.out"}, d)
    .fromTo(box.querySelector(".cr-tom"), {opacity: 0}, {opacity: 1, duration: .3}, d)
    .fromTo(t.children, {yPercent: -60, opacity: 0}, {yPercent: 0, opacity: 1, duration: .7, ease: "expo.out", stagger: .05}, d + .05)
    .fromTo([ed, cod], {y: -20, opacity: 0}, {y: 0, opacity: 1, duration: .4, ease: "power2.out", stagger: .06}, d + .25)
    .fromTo(chs, {x: (i) => (i % 2 ? 40 : -40), opacity: 0}, {x: 0, opacity: 1, duration: .45, ease: "power3.out", stagger: .12}, d + .4)
    .fromTo(linha, {y: 24, opacity: 0}, {y: 0, opacity: 1, duration: .5, ease: "power3.out"}, d + .6);
  if (num) tl.fromTo(num, {scale: .7, opacity: 0}, {scale: 1, opacity: 1, duration: .5, ease: "back.out(2)"}, d + .7);
  const sai = Math.max(d + 1.2, f - .4);
  tl.to([t, ed, cod, ...chs, linha, num].filter(Boolean), {opacity: 0, y: -16, duration: .3, stagger: .02, ease: "power2.in"}, sai)
    .to([mold, box.querySelector(".cr-tom")], {opacity: 0, duration: .3}, sai + .1);
};
