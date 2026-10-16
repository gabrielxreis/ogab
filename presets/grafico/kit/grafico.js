// Preset GRÁFICO: barras, linha, rosca ou comparação com o VALOR EXATO do plano (nada arredondado para "ficar bonito"),
// fonte do dado sempre na tela. Acabamento do launch: preto, uma cor de destaque, revelações que freiam no fim.
// Timeline GSAP pausada e determinística (HyperFrames). Campos: ver gerar.py.
(async function () {
  const P = window.PLANO, W = P.w, H = P.h, VERT = H > W;
  try { await Promise.all([document.fonts.load("700 120px 'Inter Tight'"), document.fonts.load("200 120px 'Inter Tight'"),
    document.fonts.load("500 40px 'Inter Tight'"), document.fonts.load("120px 'Instrument Serif'")]); await document.fonts.ready; } catch (e) {}
  const root = document.getElementById("root"), palco = document.getElementById("palco");
  root.style.setProperty("--cor", P.cor || "#C4A34F"); root.style.setProperty("--cor2", P.cor2 || "#F2E2B3");
  root.classList.add("letra-" + (P.letra || "apple"));
  const U = Math.min(W, H) / 1080, px = v => Math.round(v * U) + "px", NS = "http://www.w3.org/2000/svg";
  const tl = gsap.timeline({ paused: true }), REVELA = "expo.out", dur = P.dur || 7;
  const mk = (tag, cls, pai, css) => { const e = document.createElement(tag); if (cls) e.className = cls; if (css) Object.assign(e.style, css); if (pai) pai.appendChild(e); return e; };
  const sv = (tag, at, pai) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); if (pai) pai.appendChild(e); return e; };
  const dec = P.decimais || 0;
  const fmt = v => (P.prefixo || "") + Number(v).toLocaleString("pt-BR", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + (P.sufixo || "");
  // Conta de 0 até o valor exato; no fim grava o texto exato (sem resto de arredondamento do tween).
  const conta = (el, ate, t0, d, attr) => { const o = { v: 0 }, pinta = () => { el.textContent = fmt(o.v); };
    pinta(); tl.to(o, { v: ate, duration: d, ease: "expo.out", onUpdate: pinta, onComplete: () => { el.textContent = fmt(ate); } }, t0); tl.call(() => { el.textContent = fmt(ate); }, null, t0 + d); };
  function titulo(pai, txt, tam) {
    const el = mk("div", "titulo", pai, { fontSize: px(tam) });
    const ls = String(txt).split("|").map(ln => { const L = mk("span", "linha", el), d = mk("span", "", L);
      ln.split(/(\*[^*]+\*)/).filter(Boolean).forEach(p => { const c = /^\*.*\*$/.test(p), s = mk("span", "p" + (c ? " cor" : ""), d); s.textContent = c ? p.slice(1, -1) : p; }); return d; });
    tl.fromTo(ls, { yPercent: 115, opacity: 0 }, { yPercent: 0, opacity: 1, duration: 1.1, ease: REVELA, stagger: .12 }, .2);
    return el;
  }
  const aparece = (el, t0, d = .9) => tl.fromTo(el, { opacity: 0, y: px(20), filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: d, ease: REVELA }, t0);
  const dados = P.dados || [], n = dados.length, dest = P.destaque ?? n - 1;
  const cinzas = ["#5a5a60", "#47474c", "#38383c", "#2c2c30", "#232326"];

  if (P.olho) { const o = mk("div", "olho", palco, { fontSize: px(26), marginBottom: px(30) }); o.textContent = P.olho; aparece(o, .1); }
  if (P.titulo) titulo(palco, P.titulo, P.tam || (VERT ? 104 : 84));
  if (P.sub) { const s = mk("div", "sub", palco, { fontSize: px(34), marginTop: px(24) }); s.textContent = P.sub; aparece(s, .7); }
  const cw = (VERT ? 920 : 1300) * U, ch = (VERT ? 980 : 540) * U;
  const caixa = mk("div", "grafico", palco, { width: cw + "px", height: ch + "px", marginTop: px(VERT ? 90 : 50) });
  const svg = sv("svg", { width: cw, height: ch, viewBox: `0 0 ${cw} ${ch}` }, caixa);
  const T0 = 1.0;   // o gráfico começa depois do título assentar

  const tipos = {
    barras() {
      const max = Math.max(...dados.map(d => d.valor)), base = ch - 70 * U, topo = 90 * U, gap = cw / n, bw = Math.min(150 * U, gap * .58);
      const linha = sv("line", { x1: 0, x2: cw, y1: base, y2: base, stroke: "#3a3a3f", "stroke-width": 2 * U }, svg);
      tl.fromTo(linha, { attr: { x2: 0 } }, { attr: { x2: cw }, duration: 1.0, ease: "power3.inOut" }, T0 - .3);
      dados.forEach((d, i) => {
        const x = gap * i + (gap - bw) / 2, h = (base - topo) * d.valor / max, eDest = i === dest;
        const r = sv("rect", { x, y: base - h, width: bw, height: h, rx: 12 * U, fill: eDest ? "var(--cor)" : cinzas[Math.min(i, 2)] }, svg);
                const t0 = T0 + i * .14, dd = 1.3 + (eDest ? .25 : 0);
        tl.fromTo(r, { scaleY: 0, transformOrigin: "50% 100%" }, { scaleY: 1, duration: dd, ease: REVELA }, t0);
        const v = sv("text", { x: x + bw / 2, y: base - h - 22 * U, "text-anchor": "middle", class: "valor" + (eDest ? " dest" : ""), "font-size": (eDest ? 58 : 44) * U }, svg);
        conta(v, d.valor, t0, dd); tl.fromTo(v, { opacity: 0 }, { opacity: 1, duration: .35 }, t0);
        const ob = { p: 0 }; tl.to(ob, { p: 1, duration: dd, ease: REVELA, onUpdate: () => v.setAttribute("y", base - h * ob.p - 22 * U) }, t0);
        const rt = sv("text", { x: x + bw / 2, y: base + 46 * U, "text-anchor": "middle", class: "rotulo", "font-size": 36 * U }, svg); rt.textContent = d.rotulo;
        tl.fromTo(rt, { opacity: 0 }, { opacity: 1, duration: .7 }, t0 + .2);
      });
    },
    linha() {
      const vs = dados.map(d => d.valor), max = Math.max(...vs), min = P.zero === false ? Math.min(...vs) * .85 : 0;
      const topo = 110 * U, base = ch - 70 * U, X = i => 30 * U + (cw - 60 * U) * i / Math.max(1, n - 1), Y = v => base - (base - topo) * (v - min) / (max - min || 1);
      const pts = dados.map((d, i) => [X(i), Y(d.valor)]);
      const dPath = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
      const defs = sv("defs", {}, svg), g = sv("linearGradient", { id: "area", x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
      sv("stop", { offset: "0", "stop-color": "var(--cor)", "stop-opacity": .28 }, g); sv("stop", { offset: "1", "stop-color": "var(--cor)", "stop-opacity": 0 }, g);
      const area = sv("path", { d: dPath + ` L${pts[n - 1][0]} ${base} L${pts[0][0]} ${base} Z`, fill: "url(#area)" }, svg);
      const ln = sv("path", { d: dPath, fill: "none", stroke: "var(--cor)", "stroke-width": 6 * U, "stroke-linecap": "round", "stroke-linejoin": "round" }, svg);
      const L = ln.getTotalLength(); ln.style.strokeDasharray = L;
      const dd = 2.2; tl.fromTo(ln, { strokeDashoffset: L }, { strokeDashoffset: 0, duration: dd, ease: "power2.inOut" }, T0);
      tl.fromTo(area, { opacity: 0 }, { opacity: 1, duration: 1.2, ease: "power1.out" }, T0 + dd * .6);
      dados.forEach((d, i) => {
        const [x, y] = pts[i], eDest = i === dest, t0 = T0 + dd * (n > 1 ? i / (n - 1) : 1) * .92;
        const c = sv("circle", { cx: x, cy: y, r: (eDest ? 16 : 9) * U, fill: eDest ? "var(--cor)" : "#0b0b0d", stroke: "var(--cor)", "stroke-width": 4 * U }, svg);
                tl.fromTo(c, { scale: 0, transformOrigin: "50% 50%" }, { scale: 1, duration: .6, ease: "power3.out" }, t0);
        const rt = sv("text", { x, y: base + 50 * U, "text-anchor": "middle", class: "rotulo", "font-size": 34 * U }, svg); rt.textContent = d.rotulo;
        tl.fromTo(rt, { opacity: 0 }, { opacity: 1, duration: .6 }, t0);
        if (eDest || P.valores === "todos") {
          const v = sv("text", { x, y: y - 36 * U, "text-anchor": i === n - 1 ? "end" : "middle", class: "valor" + (eDest ? " dest" : ""), "font-size": (eDest ? 64 : 34) * U }, svg);
          conta(v, d.valor, t0, 1.2); tl.fromTo(v, { opacity: 0 }, { opacity: 1, duration: .35 }, t0);
        }
      });
      tl.fromTo(svg, { y: 0 }, { y: -10 * U, duration: dur, ease: "sine.inOut" }, 0);
    },
    rosca() {
      const tot = dados.reduce((s, d) => s + d.valor, 0), R = Math.min(cw, ch) * .36, cx = cw / 2, cy = ch * .42, sw = 54 * U, C = 2 * Math.PI * R;
      sv("circle", { cx, cy, r: R, fill: "none", stroke: "#18181b", "stroke-width": sw }, svg);
      let acc = 0, t0 = T0;
      dados.forEach((d, i) => {
        const frac = d.valor / tot, eDest = i === dest, len = C * frac - (n > 1 ? 6 * U : 0);
        const c = sv("circle", { cx, cy, r: R, fill: "none", stroke: eDest ? "var(--cor)" : cinzas[Math.min(i, 4)], "stroke-width": sw,
          "stroke-dasharray": `0 ${C}`, transform: `rotate(${-90 + 360 * acc} ${cx} ${cy})` }, svg);
        const dd = .5 + 1.1 * frac; const o = { l: 0 };
        tl.to(o, { l: len, duration: dd, ease: "power3.inOut", onUpdate: () => c.setAttribute("stroke-dasharray", `${o.l} ${C}`) }, t0);
        acc += frac; t0 += dd * .75;
      });
      const centro = mk("div", "centro", caixa, { height: ch * .84 + "px" });
      const g = mk("div", "grande dest", centro, { fontSize: px(150) }); conta(g, dados[dest].valor, T0 + .2, 2.0);
      const r = mk("div", "sub", centro, { fontSize: px(30), marginTop: px(6) }); r.textContent = dados[dest].rotulo; aparece(r, T0 + .8);
      const leg = mk("div", "", caixa, { position: "absolute", left: 0, right: 0, top: (cy + R + sw) + 30 * U + "px", display: "flex", justifyContent: "center", gap: px(40), flexWrap: "wrap" });
      dados.forEach((d, i) => { const it = mk("div", "sub", leg, { fontSize: px(32), padding: 0, display: "flex", alignItems: "center", gap: px(12) });
        mk("i", "", it, { width: px(16), height: px(16), borderRadius: "50%", display: "inline-block", background: i === dest ? "var(--cor)" : cinzas[Math.min(i, 4)] });
        it.append(d.rotulo + " " + fmt(d.valor)); aparece(it, T0 + 1.2 + i * .08, .7); });
    },
    comparacao() {
      const max = Math.max(...dados.map(d => d.valor)), lh = ch / n, bh = Math.min(64 * U, lh * .3);
      dados.forEach((d, i) => {
        const y = lh * i + lh * .5, eDest = i === dest, t0 = T0 + i * .35;
        const rt = sv("text", { x: 0, y: y - bh * .9, class: "rotulo", "font-size": 38 * U }, svg); rt.textContent = d.rotulo;
        tl.fromTo(rt, { opacity: 0 }, { opacity: 1, duration: .6 }, t0);
        sv("rect", { x: 0, y, width: cw, height: bh, rx: bh / 2, fill: "#151518" }, svg);
        const b = sv("rect", { x: 0, y, width: cw * d.valor / max, height: bh, rx: bh / 2, fill: eDest ? "var(--cor)" : cinzas[0] }, svg);
                tl.fromTo(b, { scaleX: 0, transformOrigin: "0% 50%" }, { scaleX: 1, duration: 1.5, ease: REVELA }, t0);
        const v = sv("text", { x: cw, y: y - bh * .9, "text-anchor": "end", class: "valor" + (eDest ? " dest" : ""), "font-size": (eDest ? 62 : 46) * U }, svg);
        conta(v, d.valor, t0, 1.5); tl.fromTo(v, { opacity: 0 }, { opacity: 1, duration: .4 }, t0);
      });
    },
  };
  (tipos[P.tipo] || tipos.barras)();
  const f = mk("div", "fonte", document.getElementById("root"), { fontSize: px(27), bottom: px(VERT ? 150 : 60) }); f.textContent = P.fonte;
  aparece(f, T0 + .8);
  tl.fromTo("#cam", { scale: 1 }, { scale: 1.03, duration: dur, ease: "none" }, 0)
    .fromTo("#palco", { opacity: 0 }, { opacity: 1, duration: .5 }, 0);
  tl.set({}, {}, dur);
  window.__timelines = window.__timelines || {}; window.__timelines["grafico"] = tl;
})();
