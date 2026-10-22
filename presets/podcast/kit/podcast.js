// Preset PODCAST: duas pessoas em tela dividida (1º em cima, 2º embaixo), emenda fina na cor da marca, metade de
// quem está calado escurece um pouco, legenda karaokê na cor de quem fala, ancorada abaixo do queixo dele e
// acompanhando a cabeça (trilha do rastrear.py convertida pelo gerar.py para px da metade). Campos: ver gerar.py.
(async function () {
  const P = window.PLANO, W = P.w, H = P.h, HH = H / 2, U = W / 1080, dur = P.dur;
  const F = P._falantes, G = P._grupos, T = P._turnos, fam = `'${P.fonte || "Poppins"}'`;
  try { await Promise.all([document.fonts.load(`800 66px ${fam}`), document.fonts.load(`700 26px ${fam}`)]); await document.fonts.ready; } catch (e) {}
  const root = document.getElementById("root");
  root.style.setProperty("--cor", P.cor); root.style.setProperty("--cor2", P.cor2);
  root.style.fontFamily = `${fam}, "Poppins", system-ui, sans-serif`;
  const mk = (tag, cls, pai, css) => { const e = document.createElement(tag); if (cls) e.className = cls; if (css) Object.assign(e.style, css); if (pai) pai.appendChild(e); return e; };
  const tl = gsap.timeline({ paused: true });
  const MARGEM = 44 * U, VAO = 22 * U, QUEIXO = .62, TOPO = .80, ZOOM = .035;
  const LIMITE = [HH - MARGEM, Math.min(HH - MARGEM, H * .84 - HH)];   // embaixo: fora da faixa da UI do Instagram

  // Emenda fina na cor da marca.
  Object.assign(document.getElementById("emenda").style, { top: HH - 3 * U + "px", height: 6 * U + "px" });

  // Quem está falando: a outra metade escurece um pouco (troca suave na 1ª palavra do outro).
  const sombras = F.map((_, i) => document.getElementById("sombra-" + i));
  const etiquetas = [];
  if (P.nomes) {
    const caixa = document.getElementById("etiquetas");
    F.forEach((f, i) => {
      const e = mk("div", "etiqueta", caixa, { fontSize: 26 * U + "px", left: MARGEM + "px" });
      e.style[i === 0 ? "bottom" : "top"] = (i === 0 ? H - HH + 26 * U : HH + 26 * U) + "px";
      mk("i", "", e, { background: f.cor }); mk("span", "", e).textContent = f.nome;
      etiquetas.push(e);
    });
  }
  const ativo0 = T.length ? T[0][1] : 0;
  sombras.forEach((s, i) => gsap.set(s, { opacity: i === ativo0 ? 0 : P.escurece }));
  etiquetas.forEach((e, i) => gsap.set(e, { opacity: i === ativo0 ? 1 : .5 }));
  T.slice(1).forEach(([t, a]) => {
    sombras.forEach((s, i) => tl.to(s, { opacity: i === a ? 0 : P.escurece, duration: .45, ease: "power2.inOut" }, Math.max(0, t - .12)));
    etiquetas.forEach((e, i) => tl.to(e, { opacity: i === a ? 1 : .5, duration: .45, ease: "power2.inOut" }, Math.max(0, t - .12)));
  });

  // Legendas: um bloco por grupo, palavra por palavra.
  const caixaLeg = document.getElementById("legendas");
  const legs = G.map(g => {
    const el = mk("div", "leg", caixaLeg), ln = mk("div", "linha", el, { fontSize: (P.tamLegenda || 66) * U + "px" });
    const spans = g.palavras.map(w => { const s = mk("span", "p", ln); s.textContent = P.caixaAlta === false ? w.texto : w.texto.toLocaleUpperCase("pt-BR"); return s; });
    let larg = el.offsetWidth;
    if (larg > W - 2 * MARGEM) { ln.style.fontSize = parseFloat(ln.style.fontSize) * (W - 2 * MARGEM) / larg + "px"; larg = el.offsetWidth; }
    return { g, el, ln, spans, w: larg, h: el.offsetHeight };
  });
  legs.forEach(({ g, ln, spans }) => {
    const cor = F[g.falante].cor;
    gsap.set(ln, { opacity: 0 });
    tl.fromTo(ln, { opacity: 0, y: 16 * U, scale: .96 }, { opacity: 1, y: 0, scale: 1, duration: .24, ease: "power3.out" }, g.ini);
    tl.to(ln, { opacity: 0, duration: .12, ease: "power2.in" }, Math.max(g.ini + .25, g.fim - .12));
    g.palavras.forEach((w, k) => {
      tl.to(spans[k], { color: cor, scale: 1.05, duration: .1, ease: "power2.out" }, w.ini);
      const prox = g.palavras[k + 1];
      tl.to(spans[k], { color: "#ffffff", scale: 1, duration: .14, ease: "power2.out" }, prox ? prox.ini : Math.max(w.fim, g.fim - .3));
    });
  });

  // Trilha local (px da metade, sem zoom) no tempo t.
  const naTrilha = (tr, t) => {
    if (t <= tr[0][0]) return tr[0].slice(1);
    if (t >= tr[tr.length - 1][0]) return tr[tr.length - 1].slice(1);
    let lo = 0, hi = tr.length - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (tr[m][0] <= t) lo = m; else hi = m; }
    const a = tr[lo], b = tr[hi], k = (t - a[0]) / Math.max(1e-6, b[0] - a[0]);
    return [1, 2, 3].map(i => a[i] + (b[i] - a[i]) * k);
  };
  // Onde fica o bloco: abaixo do queixo, preso às bordas da metade; sem espaço embaixo, acima da cabeça; nunca no
  // rosto. O lado (embaixo/acima) é decidido UMA vez por grupo, olhando o trecho inteiro (sem pular no meio).
  const zoomEm = t => 1 + ZOOM * t / dur;
  const rostoEm = (f, t) => {
    const z = zoomEm(t); let [x, y, e] = naTrilha(f.trilha, t);
    x = W / 2 + (x - W / 2) * z; y = HH / 2 + (y - HH / 2) * z;
    const alt = f.rostoAlt * e * z;
    return { x, queixo: y + QUEIXO * alt, cabeca: y - TOPO * alt };
  };
  legs.forEach(L => {
    const f = F[L.g.falante], i = L.g.falante;
    if (!f.trilha) { L.lado = "fixo"; return; }
    let queixoMax = -1e9, cabecaMin = 1e9;
    for (let t = L.g.ini; t <= L.g.fim + 1e-6; t += 1 / 15) { const r = rostoEm(f, t); queixoMax = Math.max(queixoMax, r.queixo); cabecaMin = Math.min(cabecaMin, r.cabeca); }
    if (queixoMax + VAO * .5 + L.h <= LIMITE[i]) L.lado = "embaixo";
    else if (cabecaMin - VAO - L.h >= MARGEM) L.lado = "acima";
    else { L.lado = "embaixo"; console.warn("podcast: sem espaço para a legenda fora do rosto", L.g.ini); }
  });
  const posicao = (L, t) => {
    const f = F[L.g.falante], i = L.g.falante;
    let cx = W / 2, top;
    if (L.lado === "fixo") top = f.legendaY * HH - L.h / 2;
    else {
      const r = rostoEm(f, t); cx = r.x;
      top = L.lado === "embaixo" ? Math.min(r.queixo + VAO, LIMITE[i] - L.h) : r.cabeca - VAO - L.h;
    }
    top = Math.max(MARGEM, Math.min(LIMITE[i] - L.h, top));
    cx = Math.max(MARGEM + L.w / 2, Math.min(W - MARGEM - L.w / 2, cx));
    return [cx - L.w / 2, i * HH + top];
  };
  const cams = F.map((_, i) => document.getElementById("cam-" + i));
  const relogio = { t: 0 };
  const quadro = () => {
    const t = relogio.t, z = zoomEm(t);   // aproximação contínua bem lenta nas duas metades
    cams.forEach(c => { c.style.transform = `scale(${z})`; });
    legs.forEach(L => {
      if (t < L.g.ini - .05 || t > L.g.fim + .05) return;
      const [x, y] = posicao(L, t);
      L.el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
    });
  };
  legs.forEach(L => { const [x, y] = posicao(L, L.g.ini); L.el.style.transform = `translate(${x}px, ${y}px)`; });
  tl.to(relogio, { t: dur, duration: dur, ease: "none", onUpdate: quadro }, 0);   // relogio: câmera contínua (linear ok)
  quadro();
  tl.set({}, {}, dur);
  window.__timelines = window.__timelines || {}; window.__timelines["podcast"] = tl;
})();
