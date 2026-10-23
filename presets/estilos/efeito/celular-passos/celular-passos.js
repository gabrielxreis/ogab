// EFEITO · celular com passo a passo: celular escuro desliza da borda ao lado da pessoa, os passos enchem a tela e um
// toque no botão (cor da marca) troca o texto para "Pronto" com check. Nunca em cima do rosto.
ESTILO["celular-passos"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, m = 30, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const esq = r[0] - m - S.lado, dir = W - S.lado - (r[2] + m), naDir = dir >= esq;
  let w = Math.min(340, Math.max(esq, dir)), x, y;
  if (w >= 240) { x = naDir ? r[2] + m : r[0] - m - w; y = Math.max(S.topo, r[1] - 30); }
  else { w = 340; x = naDir ? W - S.lado - w : S.lado; y = r[3] + 40; }   // sem lado livre: abaixo do queixo, encostado na borda
  const h = Math.min(w * 2.02, H - S.baixo - y + 160), k = w / 340;            // k: escala das letras pelo tamanho do celular
  C.css("celular-passos", `
    .cp{position:absolute;border-radius:${46 * k}px;background:#0d0e11;border:${7 * k}px solid #2a2c31;box-shadow:0 30px 70px rgba(0,0,0,.55),
        inset 0 0 0 2px rgba(255,255,255,.06);overflow:hidden;color:#fff;font-family:"PalcoSans"}
    .cp .ilha{position:absolute;top:${14 * k}px;left:50%;width:${92 * k}px;height:${26 * k}px;margin-left:${-46 * k}px;border-radius:20px;background:#000}
    .cp .tit{position:absolute;left:${24 * k}px;right:${24 * k}px;top:${62 * k}px;font-weight:800;font-size:${38 * k}px;line-height:1.05}
    .cp .sub{display:block;margin-top:${8 * k}px;height:${5 * k}px;width:${60 * k}px;border-radius:4px;background:var(--dest)}
    .cp .lst{position:absolute;left:${18 * k}px;right:${18 * k}px;top:${140 * k}px}
    .cp .ps{display:flex;align-items:center;gap:${14 * k}px;background:rgba(255,255,255,.07);border-radius:${18 * k}px;padding:${14 * k}px ${14 * k}px;
            margin-bottom:${12 * k}px;font-weight:700;font-size:${29 * k}px;line-height:1.1;overflow-wrap:anywhere}
    .cp .n{flex:none;width:${36 * k}px;height:${36 * k}px;border-radius:50%;background:rgba(255,255,255,.14);display:flex;align-items:center;
           justify-content:center;font-weight:900;font-size:${19 * k}px}
    .cp .bt{position:absolute;left:${22 * k}px;right:${22 * k}px;bottom:${30 * k}px;height:${84 * k}px;border-radius:${42 * k}px;background:var(--dest);
            color:#111;font-weight:900;font-size:${30 * k}px;display:flex;align-items:center;justify-content:center;gap:${10 * k}px}
    .cp .bt span{position:absolute}
    .cp .dedo{position:absolute;width:${70 * k}px;height:${70 * k}px;border-radius:50%;background:rgba(255,255,255,.85);border:3px solid #fff;
              box-shadow:0 6px 20px rgba(0,0,0,.4)}`);
  const ph = C.el("div", "cp");
  Object.assign(ph.style, {left: x + "px", top: y + "px", width: w + "px", height: h + "px"});
  C.el("div", "ilha", ph);
  C.el("div", "tit", ph, `${C.esc(it.titulo || "")}<span class="sub"></span>`);
  const lst = C.el("div", "lst", ph), passos = it.passos || [];
  const bt = C.el("div", "bt", ph), b1 = C.el("span", "", bt, C.esc(it.botao || "Publicar")),
        b2 = C.el("span", "", bt, `<svg width="${30 * k}" height="${24 * k}" viewBox="0 0 30 24" style="vertical-align:-2px;margin-right:${8 * k}px"><path d="M3 12 L11 20 L27 3" fill="none" stroke="#111" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>${C.esc(it.pronto || "Pronto")}`);
  const dedo = C.el("div", "dedo", ph); dedo.style.left = (w / 2 - 20 * k) + "px"; dedo.style.top = (h + 20) + "px";
  const tl = C.tl, d = it.de, f = it.ate, fora = naDir ? W - x + 40 : -(x + w + 40);
  tl.set(ph, {opacity: 0}, 0).set(b2, {opacity: 0}, 0)
    .fromTo(ph, {opacity: 1, x: fora, rotation: naDir ? 8 : -8}, {x: 0, rotation: naDir ? 3 : -3, duration: .55, ease: "power3.out"}, d);
  let ult = d + .4;
  passos.forEach((p, i) => {
    const e = C.el("div", "ps", lst, `<span class="n">${i + 1}</span><span>${C.esc(p.texto || "")}</span>`);
    const em = typeof p.em === "number" ? p.em : d + .5 + i * .55; ult = Math.max(ult, em);
    tl.set(e, {opacity: 0}, 0).fromTo(e, {opacity: 0, y: 24, scale: .96}, {opacity: 1, y: 0, scale: 1, duration: .3, ease: "back.out(1.8)"}, em)
      .to(e.querySelector(".n"), {backgroundColor: "rgba(255,255,255,.95)", color: "#111", duration: .2}, em + .1);
  });
  const toque = typeof it.toque === "number" ? it.toque : Math.min(ult + .55, f - .9);
  tl.fromTo(dedo, {y: 0, opacity: 0}, {y: -(20 * k + 100 * k + 20), opacity: 1, duration: .35, ease: "power2.out"}, toque - .35)
    .to(dedo, {scale: .8, duration: .1, yoyo: true, repeat: 1}, toque)
    .to(bt, {scale: .94, duration: .1, yoyo: true, repeat: 1}, toque)
    .to(b1, {opacity: 0, duration: .12}, toque + .1).fromTo(b2, {opacity: 0, scale: .7}, {opacity: 1, scale: 1, duration: .3, ease: "back.out(2.5)"}, toque + .12)
    .to(dedo, {opacity: 0, y: "+=40", duration: .3}, toque + .25)
    .to(ph, {x: fora, rotation: naDir ? 10 : -10, duration: .45, ease: "power3.in"}, Math.max(toque + .6, f - .45));
};
