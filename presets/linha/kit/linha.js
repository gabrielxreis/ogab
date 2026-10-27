// Preset LINHA: o filme inteiro é uma linha fina e contínua. O gerar.py já calculou tudo (traços, tempo da caneta e
// câmera quadro a quadro); aqui cada quadro é uma função pura do tempo t: render(t) desenha o estado exato daquele
// instante (sem sorteio, sem relógio). Ideias portadas do demo "02-line-art" do mg-styles-15 (MIT, Vincentwei1021):
// traço que se desenha, linhas antigas apagando para ~40%, câmera que acompanha a ponta, linha que vira superfície.
// Mudança pedida: a ponta da caneta NÃO brilha (é só um ponto nítido) e o brilho fica só nas formas, nunca no texto.
(function () {
  const P = window.PLANO, W = P.w, H = P.h, C = P.cores, Q = P.quadros, NS = "http://www.w3.org/2000/svg";
  const N = Q.S.length - 1;
  document.body.style.background = C.fundo;
  const sv = document.getElementById("sv");
  const el = (tag, at, pai) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); (pai || sv).appendChild(e); return e; };
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, t) => a + (b - a) * t;
  const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
  const expoOut = (x) => (x <= 0 ? 0 : x >= 1 ? 1 : 1 - Math.pow(2, -10 * x));
  const cubicOut = (x) => 1 - Math.pow(1 - clamp(x), 3);
  function curva(p1x, p1y, p2x, p2y) {   // cubic-bezier sem dependência
    const bx = (t) => 3 * p1x * t * (1 - t) ** 2 + 3 * p2x * t * t * (1 - t) + t ** 3;
    const by = (t) => 3 * p1y * t * (1 - t) ** 2 + 3 * p2y * t * t * (1 - t) + t ** 3;
    return (x) => { if (x <= 0) return 0; if (x >= 1) return 1; let lo = 0, hi = 1; for (let i = 0; i < 26; i++) { const m = (lo + hi) / 2; if (bx(m) < x) lo = m; else hi = m; } return by((lo + hi) / 2); };
  }
  const easeIO = curva(0.65, 0, 0.35, 1);   // a curva do estilo (desenho que freia nas quinas)
  function semente(s) { return () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const mixCor = (a, b, k) => { const A = hex(a), B = hex(b); return "rgb(" + A.map((v, i) => Math.round(v + (B[i] - v) * k)).join(",") + ")"; };

  // ---------------------------------------------------------------- fundo: azul-noite chapado, vinheta do mesmo tom, pontos de prancheta
  const defs = el("defs", {});
  const vg = el("radialGradient", { id: "vinheta", cx: "50%", cy: "46%", r: "72%" }, defs);
  el("stop", { offset: "0", "stop-color": C.centro }, vg); el("stop", { offset: ".6", "stop-color": C.fundo }, vg); el("stop", { offset: "1", "stop-color": C.borda }, vg);
  const pt = el("pattern", { id: "pontos", width: 46, height: 46, patternUnits: "userSpaceOnUse" }, defs);
  el("circle", { cx: 23, cy: 23, r: 1.25, fill: C.pontos }, pt);
  const fBrilho = el("filter", { id: "brilho", x: "-20%", y: "-20%", width: "140%", height: "140%" }, defs);
  const blur = el("feGaussianBlur", { stdDeviation: 4 }, fBrilho);
  el("rect", { x: 0, y: 0, width: W, height: H, fill: C.fundo });
  el("rect", { x: 0, y: 0, width: W, height: H, fill: "url(#vinheta)" });
  const grade = el("g", { opacity: 0.075 });
  el("rect", { x: -8000, y: -8000, width: 16000, height: 16000, fill: "url(#pontos)" }, grade);

  // ---------------------------------------------------------------- mundo (a câmera move este grupo)
  const mundo = el("g", {});
  const gBrilho = el("g", { fill: "none", stroke: C.linha, "stroke-linecap": "round", "stroke-linejoin": "round", filter: "url(#brilho)" }, mundo);
  const gLinha = el("g", { fill: "none", stroke: C.linha, "stroke-linecap": "round", "stroke-linejoin": "round" }, mundo);
  const gMoeda = el("g", {}, mundo);
  const gLetra = el("g", { fill: "none", "stroke-linecap": "round", "stroke-linejoin": "round" }, mundo);
  const gTexto = el("g", {}, mundo);
  if (P.cauda) {   // a entrada da linha vem de fora e a cauda se dissolve no fundo
    const cg = el("linearGradient", { id: "cauda", gradientUnits: "userSpaceOnUse", x1: P.cauda.x0, y1: P.cauda.y, x2: P.cauda.x1, y2: P.cauda.y }, defs);
    el("stop", { offset: "0", "stop-color": C.linha, "stop-opacity": 0 }, cg); el("stop", { offset: "1", "stop-color": C.linha, "stop-opacity": 1 }, cg);
  }
  const PISO = { forma: 0.42, ligacao: 0.32, entrada: 0.32, texto: 0.82, inicial: 1, anel: 1, regra: 1 };
  const COM_BRILHO = { forma: 1, anel: 1, ligacao: 1, entrada: 1, regra: 1 };   // texto e inicial: nunca
  const tr = P.tracos.map((t) => {
    const pai = t.tipo === "inicial" ? gLetra : gLinha;
    const at = { d: t.d, pathLength: 1, "stroke-dasharray": "1 2", "stroke-dashoffset": 1, visibility: "hidden" };
    if (t.tipo === "entrada" && P.cauda) at.stroke = "url(#cauda)";
    const p = el("path", at, pai);
    let b = null;
    if (COM_BRILHO[t.tipo]) { const ab = Object.assign({}, at); b = el("path", ab, gBrilho); }
    return Object.assign({}, t, { p, b });
  });

  // ---------------------------------------------------------------- fecho: a linha vira superfície (moeda) e a marca sobe por máscara
  const FE = P.fecho;
  let disco = null, brilhoMoeda = null, tMarca = null, tFrase = null, cMarca = null, cFrase = null;
  if (FE) {
    const og = el("linearGradient", { id: "ouro", gradientUnits: "userSpaceOnUse", x1: FE.cx - FE.R, y1: FE.cy - FE.R, x2: FE.cx + FE.R, y2: FE.cy + FE.R }, defs);
    C.ouro.forEach((c, i) => el("stop", { offset: i / (C.ouro.length - 1), "stop-color": c }, og));
    const cm = el("clipPath", { id: "cmoeda" }, defs); const cc = el("circle", { cx: FE.cx, cy: FE.cy, r: 0 }, cm);
    disco = el("path", { d: "", fill: "url(#ouro)", "fill-rule": "evenodd", visibility: "hidden" }, gMoeda);
    const sg = el("linearGradient", { id: "reflexo", x1: "0", y1: "0", x2: "1", y2: "0" }, defs);
    el("stop", { offset: "0", "stop-color": C.brilho, "stop-opacity": 0 }, sg); el("stop", { offset: ".5", "stop-color": C.brilho, "stop-opacity": 1 }, sg);
    el("stop", { offset: "1", "stop-color": C.brilho, "stop-opacity": 0 }, sg);
    const gr = el("g", { "clip-path": "url(#cmoeda)" }, gMoeda);
    brilhoMoeda = el("rect", { x: -FE.R * 0.25, y: FE.cy - FE.R * 1.6, width: FE.R * 0.5, height: FE.R * 3.2, fill: "url(#reflexo)", opacity: 0 }, gr);
    disco.cc = cc;
    const caixaTexto = (id, y, tam) => { const c = el("clipPath", { id }, defs); el("rect", { x: FE.cx - W * 4, y: y - tam * 0.95, width: W * 8, height: tam * 1.28 }, c); return c; };
    if (FE.marca) {
      cMarca = caixaTexto("cmarca", FE.y_marca, FE.tm);
      const g = el("g", { "clip-path": "url(#cmarca)" }, gTexto);
      tMarca = el("text", { x: FE.cx + FE.esp * FE.tm / 2, y: FE.y_marca, "font-size": FE.tm, "letter-spacing": FE.esp * FE.tm, "text-anchor": "middle", fill: C.texto, "font-weight": 430 }, g);
      tMarca.textContent = FE.marca;
    }
    if (FE.frase) {
      cFrase = caixaTexto("cfrase", FE.y_frase, FE.tf);
      const g = el("g", { "clip-path": "url(#cfrase)" }, gTexto);
      tFrase = el("text", { x: FE.cx + 0.06 * FE.tf / 2, y: FE.y_frase, "font-size": FE.tf, "letter-spacing": 0.06 * FE.tf, "text-anchor": "middle", fill: C.texto, opacity: 0.86, "font-style": "italic" }, g);
      tFrase.textContent = FE.frase;
    }
  }
  const ponta = el("circle", { r: 2, fill: C.ponta }, mundo);
  const T_PONTA = FE ? FE.t_ponta : P.t_ponta;

  // ---------------------------------------------------------------- grão (4 quadros de ruído com semente, trocados 12x por segundo)
  const gc = document.getElementById("grao"), GW = Math.round(W / 2), GH = Math.round(H / 2);
  gc.width = GW; gc.height = GH; const gx = gc.getContext("2d"); gc.style.opacity = P.grao;
  const graos = [0, 1, 2, 3].map((k) => {
    const c = document.createElement("canvas"); c.width = GW; c.height = GH; const x = c.getContext("2d");
    const im = x.createImageData(GW, GH), r = semente(9001 + k * 77);
    for (let i = 0; i < im.data.length; i += 4) { const v = 128 + (r() - 0.5) * 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
    x.putImageData(im, 0, 0); return c;
  });
  let grAtual = -1;

  // ---------------------------------------------------------------- o quadro no tempo t
  function render(t) {
    const f = clamp(t * P.fps, 0, N), i0 = Math.floor(f), i1 = Math.min(N, i0 + 1), a = f - i0;
    const q = (arr) => lerp(arr[i0], arr[i1], a);
    const S = q(Q.S), cx = q(Q.cx), cy = q(Q.cy), z = q(Q.z);
    mundo.setAttribute("transform", `translate(${W / 2} ${H / 2}) scale(${z}) translate(${-cx} ${-cy})`);
    const zg = 1 + (z - 1) * 0.5, gxp = lerp(P.poster.cx, cx, 0.5), gyp = lerp(P.poster.cy, cy, 0.5);
    grade.setAttribute("transform", `translate(${W / 2} ${H / 2}) scale(${zg}) translate(${-gxp} ${-gyp})`);
    gLinha.setAttribute("stroke-width", P.lw / z);
    gBrilho.setAttribute("stroke-width", (P.lw * 3.2) / z);
    blur.setAttribute("stdDeviation", 5 / z);
    const tp0 = P.poster.t0;
    for (const s of tr) {
      const fr = clamp((S - s.s0) / Math.max(s.L, 1e-6));
      if (fr <= 0) { s.p.setAttribute("visibility", "hidden"); if (s.b) s.b.setAttribute("visibility", "hidden"); continue; }
      const off = 1 - fr;
      s.p.setAttribute("visibility", "visible"); s.p.setAttribute("stroke-dashoffset", off);
      const idade = fr < 1 ? -1 : t - s.t1, piso = PISO[s.tipo] ?? 0.5;
      let b = idade <= 0 ? 1 : piso + (1 - piso) * (1 - smooth(0.25, 1.6, idade));
      if (t > tp0) {   // no pôster uma onda de luz volta pela linha (do fim para o começo) e deixa tudo legível
        const atraso = 0.9 * (1 - s.s0 / P.STOT);
        b = lerp(b, Math.max(b, 0.86), smooth(tp0 + atraso, tp0 + atraso + 0.55, t));
      }
      s.p.setAttribute("opacity", b.toFixed(3));
      if (s.b) {
        const g = idade <= 0 ? 0.5 : 0.5 * (1 - smooth(0.1, 0.9, idade));
        if (g < 0.01) s.b.setAttribute("visibility", "hidden");
        else { s.b.setAttribute("visibility", "visible"); s.b.setAttribute("stroke-dashoffset", off); s.b.setAttribute("opacity", g.toFixed(3)); }
      }
    }
    // fecho
    let carve = 0;
    if (FE) {
      const u = (t - FE.t_fill) / 0.55;
      // a superfície nasce do contorno: um anel cheio cuja borda de dentro fecha até o centro
      const rFim = FE.R + (P.lw * 0.6) / z, ri = u <= 0 ? rFim : rFim * (1 - cubicOut(u));
      const anelD = (r) => `M${FE.cx + r},${FE.cy} A${r},${r} 0 1 0 ${FE.cx - r},${FE.cy} A${r},${r} 0 1 0 ${FE.cx + r},${FE.cy}Z`;
      disco.setAttribute("visibility", u > 0 ? "visible" : "hidden");
      disco.setAttribute("d", anelD(rFim) + (ri > 0.3 ? " " + anelD(ri) : ""));
      disco.cc.setAttribute("r", (u > 0 ? rFim : 0).toFixed(2));
      carve = smooth(0.35, 0.8, u);
      const sq = (t - FE.t_fill - 0.75) / 0.9;
      if (sq > 0 && sq < 1) {
        const x = lerp(FE.cx - FE.R * 1.5, FE.cx + FE.R * 1.2, easeIO(sq));
        brilhoMoeda.setAttribute("transform", `translate(${x} 0) rotate(18 ${FE.R * 0.25} ${FE.cy})`);
        brilhoMoeda.setAttribute("opacity", (0.3 * Math.sin(Math.PI * sq)).toFixed(3));
      } else brilhoMoeda.setAttribute("opacity", 0);
      if (tMarca) { const e = expoOut((t - FE.t_marca) / 1.1); tMarca.setAttribute("y", (FE.y_marca + (1 - e) * FE.tm * 1.1).toFixed(2)); }
      if (tFrase) { const e = expoOut((t - FE.t_frase) / 1.1); tFrase.setAttribute("y", (FE.y_frase + (1 - e) * FE.tf * 1.2).toFixed(2)); }
    }
    gLetra.setAttribute("stroke", carve > 0 ? mixCor(C.linha, C.fundo, carve) : C.linha);
    gLetra.setAttribute("stroke-width", (P.lw * (1 + 0.8 * carve)) / z);
    // ponta da caneta: ponto nítido, sem halo (o brilho fica só no traço das formas)
    const vis = 1 - smooth(T_PONTA, T_PONTA + 0.3, t);
    ponta.setAttribute("opacity", vis.toFixed(3));
    ponta.setAttribute("cx", q(Q.px)); ponta.setAttribute("cy", q(Q.py)); ponta.setAttribute("r", (P.lw * 0.85) / z);
    const gi = Math.floor(t * 12) % 4;
    if (gi !== grAtual) { gx.clearRect(0, 0, GW, GH); gx.drawImage(graos[gi], 0, 0); grAtual = gi; }
  }

  const tl = gsap.timeline({ paused: true }), rel = { t: 0 };
  tl.to(rel, { t: P.dur, duration: P.dur, ease: "none", onUpdate: () => render(rel.t) }, 0);
  render(0);
  window.__timelines = window.__timelines || {}; window.__timelines["linha"] = tl;
})();
