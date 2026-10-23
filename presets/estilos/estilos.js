// Despachante dos ESTILOS (presets/estilos/<grupo>/<id>/<id>.js): cada estilo registra window.ESTILO[id] = (item, C) => {...}
// e anima o que quiser na timeline C.tl a partir de item.de até item.ate. Ajudas para os estilos:
//   C.css(id, texto)       injeta o CSS do estilo uma vez
//   C.rostoEm(t)           caixa do rosto [x0, y0, x1, y1] no tempo t (ou null), para nada cair em cima dele
//   C.seguro               área segura das redes: {topo: 220, baixo: 450, lado: 35} (Reels/TikTok)
window.ESTILO = window.ESTILO || {};
(function () {
  const C = window.CENA, P = C.P, feitos = {};
  C.css = (id, txt) => { if (feitos[id]) return; feitos[id] = 1; const s = document.createElement("style"); s.textContent = txt; document.head.appendChild(s); };
  C.rostoEm = t => {
    const R = P.rostos || []; let m = null, d = 1e9;
    for (const r of R) { const k = Math.abs(r[0] - t); if (k < d) { d = k; m = r; } }
    return m && d < 1.5 ? m.slice(1) : null;
  };
  C.seguro = { topo: 220, baixo: 450, lado: 35 };
  // <video> dentro da camada (P.video = vídeo da pessoa, P.silhueta = pessoa recortada com alfa), no tempo do vídeo
  let trilha = 20;
  C.video = (src, pai, cls) => {
    const v = C.el("video", cls || null, pai);
    v.src = src; v.muted = true; v.playsInline = true; v.setAttribute("muted", ""); v.setAttribute("playsinline", "");
    v.setAttribute("data-start", "0"); v.setAttribute("data-duration", String(P.dur)); v.setAttribute("data-track-index", String(trilha++));
    return v;
  };
  C.mod.estilos = (lista, C) => (lista || []).forEach(it => {
    const f = window.ESTILO[it.id];
    if (f) f(it, C); else console.warn("estilo sem módulo:", it.id);
  });
})();
