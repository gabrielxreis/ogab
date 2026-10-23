// RITMO · círculo da marca: um círculo na cor do cliente nasce de um ponto, cobre o quadro (com o nome da próxima parte,
// se houver) e se abre de dentro para fora revelando o plano seguinte. Transição entre partes do vídeo.
ESTILO["circulo-marca"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, raio = Math.hypot(W, H) + 40;
  C.css("circulo-marca", `
    .cm{position:absolute;inset:0;background:var(--dest);--furo:0px;
        -webkit-mask:radial-gradient(circle at var(--fx) var(--fy),transparent var(--furo),#000 calc(var(--furo) + 1.5px));
        mask:radial-gradient(circle at var(--fx) var(--fy),transparent var(--furo),#000 calc(var(--furo) + 1.5px))}
    .cm-t{position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);text-align:center;font-family:"PalcoSans";
          font-weight:900;color:#111;letter-spacing:-.03em;line-height:.95;padding:0 ${C.seguro.lado + 30}px}
    .cm-t small{display:block;font-family:"PalcoSerif";font-style:italic;font-weight:600;letter-spacing:0;font-size:.42em;margin-bottom:.18em;opacity:.8}`);
  const pt = it.ponto || [.86, .78];                  // de onde o círculo nasce (0-1 do quadro)
  const px = pt[0] * W, py = pt[1] * H;
  const r = C.rostoEm(it.ate) || [W * .32, H * .32, W * .68, H * .55];
  const cm = C.el("div", "cm");
  cm.style.setProperty("--fx", ((r[0] + r[2]) / 2) + "px"); cm.style.setProperty("--fy", ((r[1] + r[3]) / 2) + "px");   // abre a partir do rosto
  let tx = null;
  if (it.texto) {
    const tam = Math.min(210, (W - 2 * C.seguro.lado - 60) / Math.max(4, String(it.texto).length) / .58);
    tx = C.el("div", "cm-t", cm, (it.linha ? `<small>${C.esc(it.linha)}</small>` : "") + C.esc(it.texto));
    tx.style.fontSize = Math.round(tam) + "px";
    const h = String(P.dest || "#F2D16B").replace("#", ""), v = i => parseInt(h.substr(i, 2), 16) || 0;
    if (h.length >= 6 && .299 * v(0) + .587 * v(2) + .114 * v(4) < 140) tx.style.color = "#fff";   // marca escura: texto branco
  }
  const tl = C.tl, d = it.de, f = it.ate, cobre = .5, abre = .55;
  tl.set(cm, {clipPath: `circle(0px at ${px}px ${py}px)`, "--furo": "0px"}, 0)
    .to(cm, {clipPath: `circle(${raio}px at ${px}px ${py}px)`, duration: cobre, ease: "power2.in"}, d);
  if (tx) tl.fromTo(tx, {scale: .82, opacity: 0}, {scale: 1, opacity: 1, duration: .35, ease: "back.out(1.6)"}, d + cobre - .08)
            .to(tx, {scale: 1.06, opacity: 0, duration: .2, ease: "power2.in"}, f - abre - .05);
  tl.to(cm, {"--furo": raio + "px", duration: abre, ease: "power3.out"}, f - abre)
    .set(cm, {display: "none"}, f);
};
