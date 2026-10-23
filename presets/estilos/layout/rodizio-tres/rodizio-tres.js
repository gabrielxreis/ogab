// LAYOUT · rodízio de três: lista de trechos, cada um num modo. "prova": cartão claro no espaço acima da cabeça;
// "palavra": uma palavra gigante abaixo do queixo; "tela": prova em tela cheia (fundo escuro + cartão grande).
// Trecho: {modo, de, ate, titulo, texto, imagem?, palavra}. Sem de/ate, divide o tempo do estilo em partes iguais.
ESTILO["rodizio-tres"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro;
  C.css("rodizio-tres", `
    .rt-p{position:absolute;left:${S.lado + 25}px;right:${S.lado + 25}px;border-radius:30px;background:#fff;color:#15161a;overflow:hidden;
          box-shadow:0 26px 60px rgba(0,0,0,.45);display:flex;flex-direction:column}
    .rt-p .cab{display:flex;align-items:center;gap:16px;padding:22px 28px 14px;font-weight:800;font-size:34px}
    .rt-p .cab i{width:22px;height:22px;border-radius:50%;background:var(--dest);flex:none}
    .rt-p .cab small{margin-left:auto;font-weight:700;font-size:24px;color:#7a7c82}
    .rt-p .co{flex:1;margin:0 28px 24px;border-radius:18px;overflow:hidden;background:#f1f2f4;position:relative}
    .rt-p .co img{width:100%;height:100%;object-fit:cover}
    .rt-p .co svg{position:absolute;inset:0;width:100%;height:100%}
    .rt-w{position:absolute;left:0;right:0;text-align:center;font-weight:900;letter-spacing:-.045em;line-height:.9;color:var(--dest);
          -webkit-text-stroke:6px rgba(16,14,12,.9);paint-order:stroke fill;text-shadow:0 16px 40px rgba(0,0,0,.45)}
    .rt-w span{display:inline-block}
    .rt-t{position:absolute;inset:0;background:#0f1013}
    .rt-t .rt-p{top:${S.topo + 40}px;bottom:${S.baixo + 10}px}
    .rt-t .tit{position:absolute;left:${S.lado + 30}px;right:${S.lado + 30}px;bottom:${S.baixo - 120}px;text-align:center;color:#fff;font-weight:900;
          font-size:56px;line-height:1.05}`);
  const grafico = () => `<svg viewBox="0 0 600 300" preserveAspectRatio="none"><path d="M0 260 C120 250 180 230 260 200 S420 90 600 30 L600 300 L0 300Z"
    fill="color-mix(in srgb, var(--dest) 30%, transparent)"/><path d="M0 260 C120 250 180 230 260 200 S420 90 600 30" fill="none" stroke="var(--dest)" stroke-width="8"/></svg>`;
  const cartao = (pai, x, top, alto) => {
    const p = C.el("div", "rt-p", pai), src = x.imagem || x.src;
    p.innerHTML = `<div class="cab"><i></i>${C.esc(x.titulo || "")}<small>${C.esc(x.texto || "")}</small></div>
      <div class="co">${src ? `<img src="${C.esc(src)}">` : grafico()}</div>`;
    if (top != null) Object.assign(p.style, {top: top + "px", height: alto + "px"});
    return p;
  };
  const tr = it.trechos || [], tl = C.tl, n = Math.max(1, tr.length), passo = (it.ate - it.de) / n;
  tr.forEach((x, i) => {
    const d = typeof x.de === "number" ? x.de : it.de + i * passo, f = typeof x.ate === "number" ? x.ate : d + passo;
    const r = C.rostoEm(d) || [W * .32, H * .32, W * .68, H * .55], ult = i === tr.length - 1, sai = ult ? Math.max(d + .6, f - .4) : f - .25;
    if (x.modo === "tela") {
      const t = C.el("div", "rt-t"), p = cartao(t, x);
      p.querySelector(".cab small").remove(); C.el("div", "tit", t, C.esc(x.texto || ""));
      tl.set(t, {clipPath: "inset(100% 0 0 0)"}, 0).to(t, {clipPath: "inset(0% 0 0 0)", duration: .4, ease: "expo.out"}, d)
        .fromTo(p, {y: 80, scale: .92}, {y: 0, scale: 1, duration: .5, ease: "back.out(1.4)"}, d + .05)
        .to(t, {clipPath: "inset(0 0 100% 0)", duration: .35, ease: "power3.in"}, sai);
    } else if (x.modo === "palavra") {
      const w = String(x.palavra || "").toUpperCase(), topo = r[3] + 40, livre = H - S.baixo - topo;
      const tam = Math.max(70, Math.min(W * .9 / Math.max(3, w.length) / .62, livre, 240));
      const e = C.el("div", "rt-w", null, [...w].map(c => `<span>${c === " " ? "&nbsp;" : C.esc(c)}</span>`).join(""));
      Object.assign(e.style, {top: topo + "px", fontSize: Math.round(tam) + "px"});
      tl.set(e, {opacity: 0}, 0).set(e, {opacity: 1}, d)
        .fromTo(e.children, {y: 60, scale: 1.4, opacity: 0}, {y: 0, scale: 1, opacity: 1, duration: .45, ease: "expo.out", stagger: .035}, d)
        .to(e, {scale: 1.06, duration: f - d - .7, ease: "none"}, d + .45)
        .to(e, {opacity: 0, y: 40, duration: .25, ease: "power2.in"}, sai);
    } else {
      const alto = Math.max(160, r[1] - 30 - S.topo), p = cartao(null, x, S.topo, alto);
      tl.set(p, {opacity: 0}, 0).fromTo(p, {opacity: 0, y: -60, rotation: -2}, {opacity: 1, y: 0, rotation: 0, duration: .5, ease: "back.out(1.5)"}, d)
        .to(p, {opacity: 0, y: -60, duration: .25, ease: "power2.in"}, sai);
    }
  });
};
