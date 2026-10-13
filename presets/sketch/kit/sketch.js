// Preset SKETCH: desenho de marcador sobre fundo escuro. O layout vem pronto do gerar.py (coordenadas e tempos);
// aqui só se desenha: contorno que se traça, cursor, ícone que surge, texto digitado, seta que se desenha e o traço
// "tremido" (line boil) de animação desenhada à mão.
(function () {
  const P = window.PLANO, W = P.w, H = P.h, IC = window.ICONES, NS = "http://www.w3.org/2000/svg";
  const sv = document.getElementById("sv");
  const el = (tag, at, pai) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); (pai || sv).appendChild(e); return e; };
  const tl = gsap.timeline({ paused: true });

  // ---- fundo: preto com luz suave no centro e grão leve
  const defs = el("defs", {});
  const rg = el("radialGradient", { id: "luz", cx: "50%", cy: "45%", r: "70%" }, defs);
  el("stop", { offset: "0", "stop-color": P.cores.luz }, rg); el("stop", { offset: "1", "stop-color": P.cores.fundo }, rg);
  const gr = el("filter", { id: "grao", x: "0", y: "0", width: "100%", height: "100%" }, defs);
  el("feTurbulence", { type: "fractalNoise", baseFrequency: "0.9", numOctaves: "2", seed: "3" }, gr);
  el("feColorMatrix", { values: "0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .06 0" }, gr);
  // traço de marcador: borda irregular (deslocamento por ruído); 3 sementes trocadas 8x/s = traço "vivo"
  const BOIL = 3;
  for (let i = 0; i < BOIL; i++) {
    const f = el("filter", { id: "r" + i, x: "-5%", y: "-5%", width: "110%", height: "110%" }, defs);
    el("feTurbulence", { type: "fractalNoise", baseFrequency: P.aspereza.freq, numOctaves: "2", seed: String(7 + i * 13), result: "n" }, f);
    el("feDisplacementMap", { in: "SourceGraphic", in2: "n", scale: P.aspereza.escala, xChannelSelector: "R", yChannelSelector: "G" }, f);
  }
  el("rect", { x: 0, y: 0, width: W, height: H, fill: "url(#luz)" });
  el("rect", { x: 0, y: 0, width: W, height: H, filter: "url(#grao)", opacity: .5 });

  const tracos = [];
  const desenhar = (path, t, dur, ease) => {   // contorno que se traça (pathLength 1 = 0..1 independente do tamanho)
    path.setAttribute("pathLength", "1"); path.setAttribute("stroke-dasharray", "1"); path.setAttribute("stroke-dashoffset", "1");
    tl.to(path, { attr: { "stroke-dashoffset": 0 }, duration: dur, ease: ease || "power1.inOut" }, t);
  };
  const traco = (pai, d, cor, lw) => el("path", { d, fill: "none", stroke: cor, "stroke-width": lw, "stroke-linecap": "round", "stroke-linejoin": "round" }, pai);

  function digitar(pai, it, t0) {   // texto letra a letra (cada letra um tspan que acende)
    const tx = el("text", { x: it.x, y: it.y, "font-size": it.tam, fill: it.cor, "text-anchor": it.ancora || "start",
                            "dominant-baseline": "middle", "letter-spacing": it.espaco || 0 }, pai);
    const letras = [...it.txt];
    letras.forEach((ch, i) => {
      const s = el("tspan", { opacity: 0 }, tx); s.textContent = ch;
      if (it.modo === "surgir") return;
      tl.set(s, { attr: { opacity: 1 } }, t0 + i * (it.cps || P.cps));
    });
    if (it.modo === "surgir") {
      tx.querySelectorAll("tspan").forEach(s => s.setAttribute("opacity", 1));
      gsap.set(tx, { opacity: 0, y: 14 }); tl.to(tx, { opacity: 1, y: 0, duration: .45, ease: "power2.out" }, t0);
    }
    return tx;
  }

  function item(cena, it, base) {
    const t = base + it.t, tr = cena.tr, tx = cena.tx;
    if (it.k === "caixa") {
      const g = el("g", {}, tr);
      const fundo = el("path", { d: it.d, fill: it.cor, "fill-opacity": 0, stroke: "none" }, g);
      const p = traco(g, it.d, it.cor, it.lw || P.lw); desenhar(p, t, it.dur || .5);
      tl.to(fundo, { attr: { "fill-opacity": it.preench ?? P.preench }, duration: .35, ease: "power1.out" }, t + (it.dur || .5) * .7);
      if (it.cursor) {   // cursor de terminal piscando antes do conteúdo entrar
        const c = el("text", { x: it.cx, y: it.cy, "font-size": it.ctam, fill: it.cor, opacity: 0 }, tx); c.textContent = "_";
        const t1 = t + (it.dur || .5);
        for (let k = 0; k < it.piscas; k++) { tl.set(c, { attr: { opacity: 1 } }, t1 + k * .24); tl.set(c, { attr: { opacity: 0 } }, t1 + k * .24 + .14); }
      }
    } else if (it.k === "icone") {
      const s = it.s / 24, g = el("g", {}, tr), gi = el("g", { transform: `translate(${it.x - it.s / 2},${it.y - it.s / 2}) scale(${s})` }, g);
      (IC[it.nome] || IC.estrela).forEach(d => traco(gi, d, it.cor, (it.lw || P.lw) / s * .85));
      gsap.set(g, { opacity: 0, scale: .4, svgOrigin: `${it.x} ${it.y}` });   // svgOrigin = centro em coordenadas da tela (transformOrigin no SVG é relativo ao elemento)
      tl.to(g, { opacity: 1, scale: 1, duration: .38, ease: "back.out(2.2)" }, t);
    } else if (it.k === "texto") {
      digitar(tx, it, t);
    } else if (it.k === "linha") {
      const p = traco(tr, it.d, it.cor, it.lw || P.lw); desenhar(p, t, it.dur || .4, it.ease);
      if (it.preench) { const f = el("path", { d: it.d, fill: it.cor, "fill-opacity": 0, stroke: "none" }, tr); tl.to(f, { attr: { "fill-opacity": it.preench }, duration: .3 }, t + (it.dur || .4)); }
    } else if (it.k === "seta") {
      const p = traco(tr, it.d, it.cor, it.lw || P.lw); desenhar(p, t, it.dur || .45, "power2.out");
      const h = traco(tr, it.ponta, it.cor, it.lw || P.lw); desenhar(h, t + (it.dur || .45) * .85, .18, "power1.out");
    }
  }

  P.cenas.forEach((c, i) => {
    const g = el("g", { opacity: 0 });
    const tr = el("g", { filter: "url(#r0)" }, g), tx = el("g", { filter: "url(#r0)" }, g);
    tracos.push(tr, tx);
    const cena = { tr, tx };
    c.itens.forEach(it => item(cena, it, c.inicio));
    tl.set(g, { attr: { opacity: 1 } }, c.inicio);
    if (i < P.cenas.length - 1 || P.fade_final) tl.to(g, { attr: { opacity: 0 }, duration: .3, ease: "power1.in" }, c.inicio + c.dur - .3);
  });

  // line boil: troca a semente do traço 8 vezes por segundo (determinístico pelo tempo: o render pode pular quadros)
  const st = { t: 0 };
  tl.to(st, { t: P.dur, duration: P.dur, ease: "none", onUpdate: () => {
    const f = "url(#r" + (Math.floor(st.t * P.boil) % BOIL) + ")"; tracos.forEach(g => g.setAttribute("filter", f));
  } }, 0);

  window.__timelines = window.__timelines || {}; window.__timelines["sketch"] = tl;
})();
