// Preset APPLE DESIGN: folha de desenho técnico no estilo dos desenhos dimensionais da Apple, desenhada por uma caneta
// enquanto a câmera passeia pelo papel, e que no fim vira o produto acabado com o título do lançamento.
// Batidas: close no módulo de câmera → recua para a vista de trás → camadas sobem na vista explodida → folha inteira →
// o desenho ganha cor e acabamento e o título sobe. Tudo é função do tempo (render(t)), então o HyperFrames pula para
// qualquer quadro. Ideia da coreografia: github.com/enesozturk/dimensional-drawing (MIT). Campos: ver gerar.py.
(async function () {
  const P = window.PLANO, W = P.w, H = P.h, VERT = H > W, U = Math.min(W, H) / 1080, dur = P.dur || 13;
  try { await Promise.all([document.fonts.load("700 120px 'Inter Tight'"), document.fonts.load("600 14px 'Inter Tight'"),
    document.fonts.load("500 14px 'Inter Tight'"), document.fonts.load("400 40px 'Inter Tight'")]); await document.fonts.ready; } catch (e) {}
  const root = document.getElementById("root"), camEl = document.getElementById("cam"), palco = document.getElementById("palco");
  const COR = P.cor || "#C4A34F", NOITE = P.tema === "noite";
  root.style.setProperty("--cor", COR); root.classList.add("tema-" + (NOITE ? "noite" : "papel"));
  const EN = (P.rotulos || "en") !== "pt", T = (en, pt) => EN ? en : pt;
  const clamp01 = v => v < 0 ? 0 : v > 1 ? 1 : v, lerp = (a, b, p) => a + (b - a) * p;
  const eio = p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2, eo = p => 1 - Math.pow(1 - p, 3);
  const rgb = h => { h = h.replace("#", ""); if (h.length === 3) h = h.split("").map(c => c + c).join(""); return [0, 2, 4].map(i => parseInt(h.substr(i, 2), 16)); };
  const mix = (a, b, t) => { const A = rgb(a), B = rgb(b); return "#" + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, "0")).join(""); };

  // ---------- medidas do produto (mm) e diagramação da folha ----------
  const M = Object.assign({ largura: 71.9, altura: 150, espessura: 8.75, raio: 12 }, P.medidas || {});
  const PW = +M.largura, PH = +M.altura, D = +M.espessura, R = +M.raio;
  const k = (VERT ? 4.0 : 3.5) * U;                                   // px por mm na vista de trás
  const A = VERT ? [W * .43, H * .33] : [W * .28, H * .5];             // centro da vista de trás
  const B = VERT ? [W * .47, H * .72] : [W * .69, H * .5];             // centro da vista explodida (depois, do título)
  const PX = A[0] - PW * k / 2, PY = A[1] - PH * k / 2, X = v => PX + v * k, Y = v => PY + v * k;
  const fs = v => v * U;

  const NS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.setAttribute("width", W); svg.setAttribute("height", H); svg.setAttribute("class", "dw");
  camEl.appendChild(svg);
  // Registro: at(início, intervalo, duração) vale para tudo o que mk() criar depois. Traço cheio se desenha
  // (pathLength 1 + dashoffset); texto, tracejado e cota aparecem por opacidade.
  const REG = []; let CUR = { a: 0, s: 0, d: .6, i: 0 }, noreg = 0, sv = svg;
  const at = (a, s, d) => { CUR = { a, s: s || 0, d: d || .6, i: 0 }; };
  const SUMIR = / (tracejado|detalhe|eixo|cota|ext|lider|ponto|seta|hach) /;
  function mk(t, a, p) {
    const e = document.createElementNS(NS, t);
    for (const n in a) if (a[n] != null) e.setAttribute(n, a[n]);
    (p || sv).appendChild(e);
    if (!noreg && t !== "g") {
      const s = CUR.a + CUR.i * CUR.s; CUR.i++;
      const kd = t === "text" || SUMIR.test(" " + (a.class || "") + " ") ? "f" : "d";
      if (kd === "d") { e.setAttribute("pathLength", "1"); e.style.strokeDasharray = "1 2"; e.style.strokeDashoffset = 1; }
      e.style.opacity = 0; REG.push({ e, a: s, b: s + CUR.d, k: kd, cheio: t !== "line" && t !== "polyline" });
    }
    return e;
  }
  const g = (pai, attrs) => { noreg++; const e = mk("g", attrs || {}, pai); noreg--; return e; };
  function tx(x, y, s, c, a, p) { const e = mk("text", Object.assign({ x, y, class: c || "dt", "font-size": fs(c === "vt" ? 13 : c === "dts" ? 10.5 : 12), "stroke-width": fs(4) }, a || {}), p); e.textContent = s; return e; }

  noreg = 1;
  const defs = mk("defs", {});
  const mar = mk("marker", { id: "seta", viewBox: "0 0 10 10", refX: 10, refY: 5, markerWidth: fs(7), markerHeight: fs(7), orient: "auto-start-reverse", markerUnits: "userSpaceOnUse" }, defs);
  mk("path", { d: "M0,1.7 L10,5 L0,8.3 z", class: "seta" }, mar);
  const hat = mk("pattern", { id: "hach", width: 1.8, height: 1.8, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" }, defs);
  mk("line", { x1: 0, y1: 0, x2: 0, y2: 1.8, class: "hach" }, hat);
  // acabamento do produto no fecho: metal na cor da marca, vidro escuro nas lentes, faixa de luz
  const grad = (id, para, stops, extra) => { const gr = mk(para, Object.assign({ id }, extra || {}), defs); stops.forEach(([o, c, op]) => mk("stop", { offset: o, "stop-color": c, "stop-opacity": op == null ? 1 : op }, gr)); return gr; };
  grad("metal", "linearGradient", [[0, mix(COR, "#ffffff", .45)], [.45, COR], [1, mix(COR, "#000000", .38)]], { x1: 0, y1: 0, x2: 1, y2: 1 });
  grad("metal2", "linearGradient", [[0, mix(COR, "#ffffff", .62)], [1, mix(COR, "#000000", .2)]], { x1: 0, y1: 0, x2: 1, y2: 1 });
  grad("vidro", "radialGradient", [[0, "#3a4a66"], [.55, "#141821"], [1, "#050608"]], { cx: .38, cy: .35, r: .7 });
  grad("brilho", "linearGradient", [[0, "#ffffff", 0], [.5, "#ffffff", .55], [1, "#ffffff", 0]], { x1: 0, y1: 0, x2: 1, y2: 0 });
  const clip = mk("clipPath", { id: "corpo" }, defs); mk("rect", { x: 0, y: 0, width: PW, height: PH, rx: R }, clip);
  noreg = 0;
  const SETA = "url(#seta)";

  // ---------- cotas (coordenadas da folha) ----------
  function dimH(x1, x2, y, e1, e2, l, o) {
    o = o || {};
    [[x1, e1], [x2, e2]].forEach(([x, e]) => { if (e == null) return; const s = Math.sign(y - e) || 1; mk("line", { x1: x, y1: e + s * fs(3), x2: x, y2: y + s * fs(5), class: "ext" }); });
    if (x2 - x1 >= fs(26)) mk("line", { x1, y1: y, x2, y2: y, class: "cota", "marker-start": SETA, "marker-end": SETA });
    else { mk("line", { x1: x1 - fs(13), y1: y, x2: x1, y2: y, class: "cota", "marker-end": SETA }); mk("line", { x1: x2 + fs(13), y1: y, x2: x2, y2: y, class: "cota", "marker-end": SETA }); }
    tx((x1 + x2) / 2 + fs(o.dx || 0), (o.abaixo ? y + fs(14) : y - fs(5)), l, o.c || "dt", { "text-anchor": "middle" });
  }
  function dimV(y1, y2, x, e1, e2, l, o) {
    o = o || {};
    [[y1, e1], [y2, e2]].forEach(([y, e]) => { if (e == null) return; const s = Math.sign(x - e) || 1; mk("line", { x1: e + s * fs(3), y1: y, x2: x + s * fs(5), y2: y, class: "ext" }); });
    if (y2 - y1 >= fs(26)) mk("line", { x1: x, y1, x2: x, y2, class: "cota", "marker-start": SETA, "marker-end": SETA });
    else { mk("line", { x1: x, y1: y1 - fs(13), x2: x, y2: y1, class: "cota", "marker-end": SETA }); mk("line", { x1: x, y1: y2 + fs(13), x2: x, y2: y2, class: "cota", "marker-end": SETA }); }
    const c = (y1 + y2) / 2;
    if (o.lado) { const d = o.lado === "d"; tx(d ? x + fs(7) : x - fs(7), c + fs(4), l, o.c || "dt", { "text-anchor": d ? "start" : "end" }); }
    else tx(x - fs(5), c, l, o.c || "dt", { "text-anchor": "middle", transform: `rotate(-90 ${x - fs(5)} ${c})` });
  }
  function chamada(px, py, ex, ey, l, dir, c) {
    const s = dir || (ex >= px ? 1 : -1);
    mk("circle", { cx: px, cy: py, r: fs(2), class: "ponto" });
    mk("polyline", { points: `${px},${py} ${ex},${ey} ${ex + s * fs(12)},${ey}`, class: "lider" });
    tx(ex + s * fs(16), ey + fs(4), l, c || "dt", { "text-anchor": s > 0 ? "start" : "end" });
  }
  function detalhe(cx, cy, r, l, lx, ly) {
    mk("circle", { cx, cy, r, class: "detalhe" });
    const a = Math.atan2(ly - cy, lx - cx);
    mk("line", { x1: cx + r * Math.cos(a), y1: cy + r * Math.sin(a), x2: lx, y2: ly, class: "lider" });
    tx(lx + (lx < cx ? -fs(5) : fs(5)), ly + fs(4), l, "dts", { "text-anchor": lx < cx ? "end" : "start" });
  }
  const titulo = (x, y, t, s) => { tx(x, y, t, "vt", { "text-anchor": "middle" }); if (s) tx(x, y + fs(16), s, "dts", { "text-anchor": "middle", class: "dts tc" }); };

  const folha = g(svg, { id: "folha" }); sv = folha;
  const gPlano = g(folha, { transform: `matrix(${k},0,0,${k},${PX},${PY})` });

  // ---------- 1. close no módulo de câmera (0-2,3 s) ----------
  const bx = PW * .064, by = PW * .064, bw = PW * .47, bh = PW * .49, br = PW * .105, rl = bw * .2;
  const LENTES = [[bx + bw * .29, by + bh * .27], [bx + bw * .29, by + bh * .75], [bx + bw * .74, by + bh * .51]];
  const FLASH = [bx + bw * .74, by + bh * .19], LIDAR = [bx + bw * .74, by + bh * .83];
  const BOT_D = [[26, 33], [41, 52], [57, 68]], BOT_E = [[49, 66], [96, 112]];   // botões (mm do topo), lados na vista de trás
  sv = gPlano;
  at(-.6, 0, 2.6); mk("rect", { x: 0, y: 0, width: PW, height: PH, rx: R, class: "obj" });
  at(-.1, 0, 1.3); mk("rect", { x: bx, y: by, width: bw, height: bh, rx: br, class: "obj" });
  at(.25, .2, .85); LENTES.forEach(([x, y]) => mk("circle", { cx: x, cy: y, r: rl, class: "obj" }));
  at(.8, .12, .6); LENTES.forEach(([x, y]) => mk("circle", { cx: x, cy: y, r: rl * .6, class: "fino" }));
  at(1.35, .1, .5); mk("circle", { cx: FLASH[0], cy: FLASH[1], r: rl * .32, class: "fino" }); mk("circle", { cx: LIDAR[0], cy: LIDAR[1], r: rl * .34, class: "chapa" });
  mk("circle", { cx: bx + bw * .5, cy: by + bh * .13, r: .55, class: "fino" });
  sv = folha;
  const cy0 = Y(-7), cx0 = X(-7);
  at(1.55, .08, .45); dimH(X(0), X(bx), cy0, Y(R * .3), Y(by), "S1", { dx: -10 }); dimH(X(bx), X(bx + bw), cy0, null, Y(by), "B1");
  at(1.8, .08, .45); dimV(Y(0), Y(by), cx0, X(R * .3), X(bx), "S1", { lado: "e" }); dimV(Y(by), Y(by + bh), cx0, null, X(bx), "B2");
  at(1.95, .1, .45); chamada(X(LENTES[2][0] + rl * .71), Y(LENTES[2][1] - rl * .71), X(bx + bw + 9), Y(by - 2), "Ø L1", 1);
  chamada(X(LENTES[0][0] + rl * .6 * .71), Y(LENTES[0][1] + rl * .6 * .71), X(bx + bw + 9), Y(by + bh * .5 + 4), "Ø L2", 1);
  chamada(X(bx + bw - br * .29), Y(by + bh - br * .29), X(bx + bw + 9), Y(by + bh + 5), "R2", 1);

  // ---------- 2. recua para a vista de trás inteira (2,3-4,4 s) ----------
  sv = gPlano;
  at(2.25, 0, 1.5); mk("rect", { x: 1.4, y: 1.4, width: PW - 2.8, height: PH - 2.8, rx: R - 1.4, class: "fino" });
  at(2.45, .06, .45); BOT_D.forEach(([a, b]) => mk("rect", { x: PW, y: a, width: .9, height: b - a, rx: .45, class: "obj" }));
  BOT_E.forEach(([a, b]) => mk("rect", { x: -.9, y: a, width: .9, height: b - a, rx: .45, class: "obj" }));
  at(2.95, 0, .6); mk("circle", { cx: PW / 2, cy: PH * .47, r: PW * .1, class: "tracejado" });
  sv = folha;
  at(2.8, .12, .7); mk("line", { x1: X(PW / 2), y1: Y(-4), x2: X(PW / 2), y2: Y(PH + 6), class: "eixo" }); mk("line", { x1: X(-5), y1: Y(PH / 2), x2: X(PW + 5), y2: Y(PH / 2), class: "eixo" });
  at(3.0, 0, .5); tx(X(PW / 2), Y(PH * .47 + PW * .1 + 5), T("Mark slot", "Área da marca"), "dts", { "text-anchor": "middle" });
  at(3.1, .06, .45); dimH(X(0), X(PW), Y(-17), Y(-9), Y(-9), "W"); tx(X(PW / 2), Y(-17) - fs(19), `W = ${String(PW).replace(".", ",")} mm`, "dts", { "text-anchor": "middle", class: "dts tc" });
  at(3.3, .06, .45); dimV(Y(0), Y(PH), X(-17), X(-9), X(-9), "H"); dimV(Y(by + bh), Y(PH), cx0, null, X(R * .3), "FLEX", { c: "dts" });
  at(3.45, .05, .45); chamada(X(PW - R * .29), Y(PH - R * .29), X(PW + 7), Y(PH + 9), "R1", 1);
  at(3.55, .05, .4); chamada(X(PW + .9), Y((BOT_D[1][0] + BOT_D[1][1]) / 2), X(PW + 7), Y(BOT_D[1][0] - 6), T("Volume", "Volume"), 1, "dts");
  at(3.65, .08, .5); detalhe(X(bx + bw / 2), Y(by + bh / 2), bw * .78 * k, T("Detail A", "Detalhe A"), X(-12), Y(by + bh + 12));
  detalhe(X(PW), Y((BOT_D[0][0] + BOT_D[2][1]) / 2), 27 * k * .5, T("Detail B", "Detalhe B"), X(PW + 10), Y(BOT_D[2][1] + 14));
  // vista lateral (a traseira olha para a esquerda, o módulo de câmera salta para fora)
  const sx = X(PW + 16), sw = D * k;
  at(3.4, .06, .8); mk("rect", { x: sx, y: Y(0), width: sw, height: PH * k, rx: Math.min(sw / 2, 1.8 * k), class: "obj" });
  mk("rect", { x: sx - 2.6 * k, y: Y(by), width: 2.6 * k + 1, height: bh * k, rx: .9 * k, class: "obj" });
  at(3.75, .05, .4); BOT_D.forEach(([a, b]) => mk("rect", { x: sx + sw * .3, y: Y(a), width: sw * .4, height: (b - a) * k, rx: sw * .2, class: "fino" }));
  at(3.85, .05, .45); dimH(sx, sx + sw, Y(PH + 9), Y(PH), Y(PH), "D", { abaixo: true }); dimH(sx - 2.6 * k, sx, Y(-7), Y(by), Y(0), "P1");
  at(4.0, .1, .5); titulo(X(PW / 2), Y(PH + 22), T("Rear view", "Vista de trás"), T("Scale 1:1 · mm", "Escala 1:1 · mm"));
  titulo(sx + sw / 2, Y(PH + 22), T("Side", "Lateral"), "");

  // ---------- 3. camadas sobem na vista explodida (4,6-7,6 s) ----------
  const sc = (VERT ? 4.5 : 4.1) * U, ia = .94 * sc, ib = .17 * sc, ic = -.34 * sc, id = .47 * sc, gap = (VERT ? 84 : 74) * U, NL = 6;
  const TX = B[0] - (ia * PW + ic * PH) / 2, TY = B[1] - (ib * PW + id * PH) / 2 + gap * (NL - 1) / 2;
  const ISO = (x, y, z) => [TX + ia * x + ic * y, TY + ib * x + id * y - z];
  const flat = [k, 0, 0, k, PX, PY], iso = [ia, ib, ic, id, TX, TY];
  const gExpl = g(folha, {});
  noreg = 1;
  const MG = [];
  const camada = (i, a0) => { const e = mk("g", { class: "mg" }, gExpl); e.style.opacity = 0; MG.push({ g: e, z: gap * i, a: a0 }); return e; };
  let q = camada(0, 4.75 + .14 * 5);                                                       // L0 tela
  mk("rect", { x: 0, y: 0, width: PW, height: PH, rx: R, class: "obj" }, q); mk("rect", { x: 1.8, y: 1.8, width: PW - 3.6, height: PH - 3.6, rx: R - 1.8, class: "chapa" }, q);
  mk("rect", { x: PW / 2 - 9.5, y: 4.2, width: 19, height: 5.6, rx: 2.8, class: "obj" }, q);
  q = camada(1, 4.75 + .14 * 4);                                                           // L1 moldura
  mk("rect", { x: 0, y: 0, width: PW, height: PH, rx: R, class: "obj" }, q); mk("rect", { x: 3, y: 3, width: PW - 6, height: PH - 6, rx: R - 3, class: "fino" }, q);
  BOT_D.forEach(([a, b]) => mk("rect", { x: PW, y: a, width: 1.2, height: b - a, rx: .5, class: "obj" }, q));
  q = camada(2, 4.75 + .14 * 3);                                                           // L2 bateria
  const bat = mk("rect", { x: 7, y: by + bh + 6, width: PW - 14, height: PH - (by + bh) - 16, rx: 4, class: "obj" }, q);
  mk("rect", { x: 7, y: by + bh + 6, width: PW - 14, height: PH - (by + bh) - 16, rx: 4, fill: "url(#hach)", class: "fino" }, q);
  q = camada(3, 4.75 + .14 * 2);                                                           // L3 placa
  mk("rect", { x: PW * .5, y: 4, width: PW * .44, height: by + bh + 2, rx: 3, class: "chapa" }, q);
  [[.56, 8, .3, 12], [.56, 23, .14, 8], [.74, 23, .14, 8], [.56, 35, .32, 6]].forEach(([x, y, w, h]) => mk("rect", { x: PW * x, y, width: PW * w, height: h, rx: .8, class: "obj" }, q));
  q = camada(4, 4.75 + .14 * 1);                                                           // L4 câmeras
  mk("rect", { x: bx + 1.2, y: by + 1.2, width: bw - 2.4, height: bh - 2.4, rx: br - 1.2, class: "fino" }, q);
  LENTES.forEach(([x, y]) => { mk("circle", { cx: x, cy: y, r: rl * 1.02, class: "obj" }, q); mk("circle", { cx: x, cy: y, r: rl * .6, class: "fino" }, q); });
  q = camada(5, 4.75);                                                                     // L5 vidro traseiro
  mk("rect", { x: 0, y: 0, width: PW, height: PH, rx: R, class: "obj" }, q); mk("rect", { x: bx, y: by, width: bw, height: bh, rx: br, class: "obj" }, q);
  LENTES.forEach(([x, y]) => mk("circle", { cx: x, cy: y, r: rl, class: "fino" }, q));
  mk("circle", { cx: PW / 2, cy: PH * .47, r: PW * .1, class: "tracejado" }, q);
  noreg = 0;
  sv = gExpl;
  at(6.45, .04, .45); [[R * .3, R * .3], [PW - R * .3, R * .3], [PW - R * .3, PH - R * .3], [R * .3, PH - R * .3]].forEach(([x, y]) => {
    const p1 = ISO(x, y, 0), p2 = ISO(x, y, gap * (NL - 1)); mk("line", { x1: p1[0], y1: p1[1], x2: p2[0], y2: p2[1], class: "tracejado" }); });
  const RX = ISO(PW, 0, 0)[0] + fs(34);
  const ROT = [[T("L0 · Display", "L0 · Tela"), T("Cover glass · R1", "Vidro frontal · R1")], [T("L1 · Frame", "L1 · Moldura"), T("Band · buttons", "Aro · botões")],
    [T("L2 · Battery", "L2 · Bateria"), T("Cell · inset S1", "Célula · recuo S1")], [T("L3 · Board", "L3 · Placa"), T("Logic · stacked", "Lógica · empilhada")],
    [T("L4 · Cameras", "L4 · Câmeras"), "L1 · L2 · L3"], [T("L5 · Back glass", "L5 · Vidro traseiro"), "B1 · B2 · R2"]];
  at(6.7, .08, .45); ROT.forEach(([t1, t2], i) => {
    const p = ISO(PW, PH * .12, gap * i);
    mk("circle", { cx: p[0], cy: p[1], r: fs(2), class: "ponto" }); mk("polyline", { points: `${p[0]},${p[1]} ${RX - fs(8)},${p[1]} ${RX},${p[1]}`, class: "lider" });
    tx(RX + fs(5), p[1] - fs(2), t1, "vt"); tx(RX + fs(5), p[1] + fs(12), t2, "dts", { class: "dts tc" });
  });
  const pe = ISO(PW / 2, PH, 0);
  at(7.2, .1, .5); titulo(pe[0] - fs(30), pe[1] + fs(44), T("Exploded view", "Vista explodida"), T("Axonometric · gaps not to scale", "Axonométrica · vãos fora de escala"));

  // ---------- 4. folha inteira (7,6-9,6 s) ----------
  sv = folha;
  const m = fs(22);
  at(7.6, 0, 1.5); mk("rect", { x: m, y: m, width: W - 2 * m, height: H - 2 * m, rx: fs(14), class: "borda" });
  const NOTAS = P.notas || [T("All dimensions in millimetres unless noted.", "Medidas em milímetros, salvo indicação."),
    T("Camera plateau B1 × B2 sits S1 from both edges.", "Platô da câmera B1 × B2 a S1 das duas bordas."),
    T("Corner R1 is continuous (squircle), not circular.", "Canto R1 contínuo (squircle), não circular.")];
  const nx = m + fs(26), ny = m + fs(42);
  at(8.25, .07, .4); tx(nx, ny, T("Notes:", "Notas:"), "vt");
  NOTAS.forEach((n, i) => { const y = ny + fs(26) + i * fs(22); mk("rect", { x: nx, y: y - fs(10), width: fs(13), height: fs(13), class: "caixa" }); tx(nx + fs(6.5), y + fs(.5), String(i + 1), "dt", { "text-anchor": "middle", "font-size": fs(10) }); tx(nx + fs(22), y, n, "dt", { class: "dt tc" }); });
  // tabela das variáveis, ao lado da vista lateral
  const tbx = sx + sw + fs(VERT ? 34 : 46), tby = Y(PH * .55), cw = [fs(34), fs(64), fs(64)], rh = fs(19);
  const fmt = v => String(v).replace(".", ",");
  const LIN = [["W", T("width", "largura"), fmt(PW)], ["H", T("height", "altura"), fmt(PH)], ["D", T("depth", "espessura"), fmt(D)], ["R1", T("corner", "canto"), fmt(R)],
    ["B1", T("plateau", "platô"), fmt(+(bw).toFixed(1))], ["S1", T("inset", "recuo"), fmt(+(bx).toFixed(1))]];
  at(8.5, .015, .3); tx(tbx, tby - fs(10), T("Variables", "Variáveis"), "vt");
  [[T("Code", "Cód."), T("Name", "Nome"), "mm"]].concat(LIN).forEach((r, i) => { let c2 = tbx; r.forEach((c, j) => {
    mk("rect", { x: c2, y: tby + i * rh, width: cw[j], height: rh, class: "caixa" }); tx(c2 + (j ? cw[j] / 2 : fs(6)), tby + i * rh + fs(13), c, i ? "dt" : "vt", { "text-anchor": j ? "middle" : "start", "font-size": fs(10.5), class: (i ? "dt" : "vt") + (j === 1 ? " tc" : "") }); c2 += cw[j]; }); });
  // carimbo
  const cbw = fs(300), cbh = fs(76), cbx = W - m - fs(18) - cbw, cby = H - m - fs(18) - cbh;
  at(8.85, .03, .35); mk("rect", { x: cbx, y: cby, width: cbw, height: cbh, class: "caixa" }); mk("line", { x1: cbx, y1: cby + cbh / 2, x2: cbx + cbw, y2: cby + cbh / 2, class: "cota" });
  mk("line", { x1: cbx + cbw * .62, y1: cby, x2: cbx + cbw * .62, y2: cby + cbh, class: "cota" });
  tx(cbx + fs(10), cby + fs(24), P.produto || "Product", "vt"); tx(cbx + cbw * .62 + fs(10), cby + fs(24), P.codigo || "DWG-A01", "dt");
  tx(cbx + fs(10), cby + cbh / 2 + fs(24), "Apple Design · " + T("Dimensional drawing", "Desenho dimensional"), "dts", { class: "dts" }); tx(cbx + cbw * .62 + fs(10), cby + cbh / 2 + fs(24), T("Sheet 1/1", "Folha 1/1"), "dts");

  // ---------- 5. o desenho vira produto + título (9,8 s-fim) ----------
  const HERO = 9.8;
  noreg = 1;
  const gHero = mk("g", {}, svg), gSol = mk("g", { transform: `matrix(${k},0,0,${k},${PX},${PY})` }, gHero);
  gHero.style.opacity = 0;
  const sol = (t, a) => mk(t, a, gSol);
  sol("rect", { x: 0, y: 0, width: PW, height: PH, rx: R, fill: "url(#metal)", stroke: mix(COR, "#000000", .5), "stroke-width": .35 });
  sol("rect", { x: .9, y: .9, width: PW - 1.8, height: PH - 1.8, rx: R - .9, fill: "none", stroke: mix(COR, "#ffffff", .5), "stroke-width": .25, "stroke-opacity": .8 });
  BOT_D.forEach(([a, b]) => sol("rect", { x: PW - .1, y: a, width: 1, height: b - a, rx: .45, fill: mix(COR, "#000000", .25) }));
  BOT_E.forEach(([a, b]) => sol("rect", { x: -.9, y: a, width: 1, height: b - a, rx: .45, fill: mix(COR, "#000000", .25) }));
  sol("rect", { x: bx, y: by, width: bw, height: bh, rx: br, fill: "url(#metal2)", stroke: mix(COR, "#000000", .45), "stroke-width": .3 });
  LENTES.forEach(([x, y]) => { sol("circle", { cx: x, cy: y, r: rl, fill: mix(COR, "#000000", .55), stroke: mix(COR, "#ffffff", .35), "stroke-width": .35 });
    sol("circle", { cx: x, cy: y, r: rl * .72, fill: "#0b0c10" }); sol("circle", { cx: x, cy: y, r: rl * .52, fill: "url(#vidro)" });
    sol("circle", { cx: x - rl * .18, cy: y - rl * .2, r: rl * .1, fill: "#ffffff", "fill-opacity": .55 }); });
  sol("circle", { cx: FLASH[0], cy: FLASH[1], r: rl * .32, fill: "#f4ead2", stroke: mix(COR, "#000000", .4), "stroke-width": .2 });
  sol("circle", { cx: LIDAR[0], cy: LIDAR[1], r: rl * .34, fill: "#1a1b20" });
  const faixa = sol("rect", { x: -PW, y: -10, width: PW * .55, height: PH + 20, fill: "url(#brilho)", "clip-path": "url(#corpo)", transform: "skewX(-18)" });
  gHero.style.filter = NOITE ? "drop-shadow(0 0 40px rgba(255,255,255,.08))" : `drop-shadow(0 ${fs(28)}px ${fs(36)}px rgba(0,0,0,.18))`;
  noreg = 0;

  // texto do fecho (HTML, fora da câmera)
  const mkh = (tag, cls, pai, css) => { const e = document.createElement(tag); if (cls) e.className = cls; if (css) Object.assign(e.style, css); if (pai) pai.appendChild(e); return e; };
  const caixa = mkh("div", "", palco); caixa.id = "texto";
  Object.assign(caixa.style, { left: B[0] + "px", top: B[1] + "px", width: (VERT ? W * .86 : W * .44) + "px" });
  const olho = P.olho ? mkh("div", "olho", caixa, { fontSize: fs(26) + "px", marginBottom: fs(22) + "px" }) : null; if (olho) olho.textContent = P.olho;
  const tit = mkh("div", "titulo", caixa, { fontSize: fs(P.tamTitulo || (VERT ? 128 : 112)) + "px" });
  const linhas = String(P.titulo || "Produto").split("|").map(ln => { const L = mkh("span", "linha", tit), d = mkh("span", "", L);
    ln.split(/(\*[^*]+\*)/).filter(Boolean).forEach(p => { const c = /^\*.*\*$/.test(p), s = mkh("span", "p" + (c ? " cor" : ""), d); s.textContent = c ? p.slice(1, -1) : p; }); return d; });
  const sub = P.sub ? mkh("div", "sub", caixa, { fontSize: fs(VERT ? 40 : 34) + "px", marginTop: fs(26) + "px" }) : null; if (sub) sub.textContent = P.sub;
  const rod = P.rodape ? mkh("div", "rodape", caixa, { fontSize: fs(20) + "px", marginTop: fs(40) + "px" }) : null; if (rod) rod.textContent = P.rodape;

  // ---------- câmera ----------
  const bumpC = [X(bx + bw / 2), Y(by + bh / 2)];
  const planC = [(X(-20) + sx + sw + fs(VERT ? 160 : 40)) / 2, A[1] + fs(VERT ? 10 : 0)];
  const zc = VERT ? 3.7 : 4.1, zp = VERT ? 1.7 : 1.5, ze = VERT ? 1.12 : 1.22;
  const explC = [B[0] + fs(VERT ? 70 : 110), B[1]];
  const KEYS = [{ t: 0, c: [bumpC[0] - fs(8), bumpC[1] - fs(6)], z: zc }, { t: 2.3, c: [bumpC[0] + fs(6), bumpC[1] + fs(8)], z: zc * .93 },
    { t: 4.35, c: planC, z: zp }, { t: 4.9, c: planC, z: zp * .985 },
    { t: 7.25, c: explC, z: ze }, { t: 7.85, c: explC, z: ze * .985 },
    { t: 9.6, c: [W / 2, H / 2], z: 1 }, { t: Math.max(dur, 10), c: [W / 2, H / 2], z: 1.035 }];
  function camera(t) {
    let i = 0; while (i < KEYS.length - 2 && t > KEYS[i + 1].t) i++;
    const a = KEYS[i], b = KEYS[i + 1], p = eio(clamp01((t - a.t) / (b.t - a.t)));
    return { cx: lerp(a.c[0], b.c[0], p), cy: lerp(a.c[1], b.c[1], p), z: Math.exp(lerp(Math.log(a.z), Math.log(b.z), p)) };
  }

  // ---------- render(t): tudo a partir do tempo ----------
  function render(t) {
    const c = camera(t);
    camEl.style.transform = `translate(${W / 2 - c.cx * c.z}px, ${H / 2 - c.cy * c.z}px) scale(${c.z})`;
    svg.style.setProperty("--u", 1 / c.z); gPlano.style.setProperty("--u", 1 / (k * c.z));
    for (const r of REG) {
      const p = clamp01((t - r.a) / (r.b - r.a));
      if (r.k === "f") { r.e.style.opacity = eo(p); continue; }
      r.e.style.opacity = p > 0 ? 1 : 0; r.e.style.strokeDashoffset = 1 - eio(p);
      if (r.cheio) r.e.style.fillOpacity = clamp01((p - .55) / .45);
    }
    for (const L of MG) {
      const p = eio(clamp01((t - L.a) / 1.7)), Mx = flat.map((v, j) => lerp(v, iso[j], p)); Mx[5] -= L.z * p;
      L.g.setAttribute("transform", `matrix(${Mx.join(",")})`);
      L.g.style.opacity = clamp01((t - L.a) / .35);
      L.g.style.setProperty("--fo", .8 * clamp01((t - L.a - .5) / .7));   // 80%: as camadas de baixo aparecem por transparência
      L.g.style.setProperty("--u", 1 / (Math.sqrt(Math.abs(Mx[0] * Mx[3] - Mx[1] * Mx[2])) * c.z));
    }
    const h = clamp01((t - HERO) / 1.0);
    folha.style.opacity = 1 - .86 * eio(h); gExpl.style.opacity = 1 - eio(clamp01((t - HERO) / .6));
    gHero.style.opacity = eio(h);
    const s = lerp(.965, 1, eo(h)), dy = lerp(fs(18), 0, eo(h));
    gHero.setAttribute("transform", `translate(${A[0]} ${A[1] + dy}) scale(${s}) translate(${-A[0]} ${-A[1]})`);
    const f = eio(clamp01((t - HERO - .7) / 1.4));
    faixa.setAttribute("x", lerp(-PW * .2, PW * 1.9, f)); faixa.style.opacity = f > 0 && f < 1 ? 1 : 0;
  }

  const tl = gsap.timeline({ paused: true }), relogio = { t: 0 };
  tl.to(relogio, { t: dur, duration: dur, ease: "none", onUpdate: () => render(relogio.t) }, 0);
  const REVELA = "expo.out", aparece = (el, t0) => tl.fromTo(el, { opacity: 0, y: fs(18), filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: .9, ease: REVELA }, t0);
  if (olho) aparece(olho, HERO + .35);
  tl.fromTo(linhas, { yPercent: 115, opacity: 0 }, { yPercent: 0, opacity: 1, duration: 1.1, ease: REVELA, stagger: .12 }, HERO + .5);
  if (sub) aparece(sub, HERO + 1.05);
  if (rod) aparece(rod, HERO + 1.4);
  tl.set({}, {}, dur);
  render(0);
  window.__timelines = window.__timelines || {}; window.__timelines["apple-design"] = tl;
})();
