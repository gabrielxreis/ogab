// Preset PAINEL: apresentação de app/fintech (estudado num reel de lançamento de app de finanças, 22/10/2026).
// Fundo navy contínuo, uma cor de destaque (verde-menta), grotesca pesada em caixa alta, linha de gráfico que se
// desenha com a ponta acesa, cartões de interface flutuando em 3D, números rolando e câmera que mergulha no cartão.
// Timeline GSAP pausada e determinística (HyperFrames renderiza quadro a quadro). Tipos e campos: ver gerar.py.
(async function () {
  try { await Promise.all([document.fonts.load("800 200px 'Inter Tight'"), document.fonts.load("600 40px 'Inter Tight'"),
    document.fonts.load("500 40px 'Inter Tight'"), document.fonts.load("700 30px 'JetBrains Mono'")]); await document.fonts.ready; } catch (e) {}
  const P = window.PLANO, W = P.w, H = P.h, CY = P.centro_y || H / 2, M = 70;
  const root = document.getElementById("root"), box = document.getElementById("cenas");
  [["--cor", P.cor], ["--cor2", P.cor2], ["--cor3", P.cor3], ["--fundo", P.fundo], ["--tinta", P.tinta]].forEach(([k, v]) => v && root.style.setProperty(k, v));
  const COR = getComputedStyle(root).getPropertyValue("--cor").trim(), COR2 = getComputedStyle(root).getPropertyValue("--cor2").trim(), COR3 = getComputedStyle(root).getPropertyValue("--cor3").trim();
  let s = P.semente || 11; const R = () => { s |= 0; s = s + 0x6D2B79F5 | 0; let q = Math.imul(s ^ s >>> 15, 1 | s); q = q + Math.imul(q ^ q >>> 7, 61 | q) ^ q; return ((q ^ q >>> 14) >>> 0) / 4294967296; };
  const tl = gsap.timeline({ paused: true });
  const NS = "http://www.w3.org/2000/svg";
  const mk = (tag, cls, pai, css) => { const e = document.createElement(tag); if (cls) e.className = cls; if (css) Object.assign(e.style, css); if (pai) pai.appendChild(e); return e; };
  const sv = (tag, pai, at) => { const e = document.createElementNS(NS, tag); for (const k in at || {}) e.setAttribute(k, at[k]); if (pai) pai.appendChild(e); return e; };
  const px = v => v + "px";

  // ---------- números pt-BR rolando ----------
  function br(v, c) { const n = Math.abs(v).toFixed(c); let [i, f] = n.split("."); i = i.replace(/\B(?=(\d{3})+(?!\d))/g, "."); return (v < 0 ? "−" : "") + i + (f ? "," + f : ""); }
  function valor(el, spec, t, d) {           // spec: "texto fixo" | {de, ate, pre, suf, casas}
    if (spec == null) return; if (typeof spec !== "object") { el.textContent = spec; return; }
    const c = spec.casas != null ? spec.casas : (Number.isInteger(spec.ate) ? 0 : 2), o = { v: spec.de || 0 };
    const pinta = () => { el.textContent = (spec.pre || "") + br(o.v, c) + (spec.suf || ""); }; pinta();
    const dc = Math.min(d, spec.dur || 1.5);
    tl.to(o, { v: spec.ate, duration: dc, ease: "power3.out", onUpdate: pinta }, t);
    tl.fromTo(el, { filter: "blur(2.5px)" }, { filter: "blur(0px)", duration: dc, ease: "power2.in" }, t);
  }

  // ---------- texto: *azul*  [destaque]  ~cinza~  ponto final na cor  "|" quebra ----------
  function marcar(l) {
    let pt = ""; if (/[.!?,]$/.test(l) && !/[\]*~]$/.test(l)) { pt = l.slice(-1); l = l.slice(0, -1); }
    l = l.replace(/\*([^*]+)\*/g, '<span class="cor2">$1</span>').replace(/\[([^\]]+)\]/g, '<span class="corA">$1</span>').replace(/~([^~]+)~/g, '<span class="mudo">$1</span>');
    return l + (pt ? `<span class="pt">${pt}</span>` : "");
  }
  function letras(el) {                      // embrulha cada letra num span .L (para espalhar/subir letra a letra)
    const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); const ns = []; while (w.nextNode()) ns.push(w.currentNode);
    ns.forEach(n => { const f = document.createDocumentFragment(); [...n.textContent].forEach(ch => { const sp = document.createElement("span"); sp.className = "L"; sp.innerHTML = ch === " " ? "&nbsp;" : ch; f.appendChild(sp); }); n.parentNode.replaceChild(f, n); });
    return [...el.querySelectorAll(".L")];
  }
  function texto(pai, linhas, o = {}) {
    linhas = [].concat(linhas).flatMap(x => String(x).split("|"));
    const el = mk("div", "T", pai, { top: px(o.y != null ? o.y : CY), textAlign: o.alinhar || "left", fontSize: px(o.tam || 170) });
    if (o.centro) el.style.transform = "translateY(-50%)";
    const sp = linhas.map(l => { const ln = mk("div", "ln", el); const s2 = mk("span", "", ln); s2.innerHTML = marcar(l); return s2; });
    const larg = Math.max(...sp.map(x => x.getBoundingClientRect().width)), max = (o.larg || 1) * (W - 2 * M);
    if (larg > max) el.style.fontSize = px((o.tam || 170) * max / larg);
    return { el, sp };
  }
  const sobe = (els, t, st = .09, d = .75) => tl.fromTo(els, { yPercent: 112, filter: "blur(8px)" }, { yPercent: 0, filter: "blur(0px)", duration: d, ease: "expo.out", stagger: st }, t);
  const sai = (els, t, d = .35) => tl.to(els, { yPercent: -112, filter: "blur(8px)", duration: d, ease: "power3.in" }, t);

  // ---------- caminhos suaves e linha que se desenha ----------
  function suave(p) { let d = `M${p[0][0]},${p[0][1]}`; for (let i = 0; i < p.length - 1; i++) { const a = p[i - 1] || p[i], b = p[i], c = p[i + 1], e = p[i + 2] || c;
    d += ` C${b[0] + (c[0] - a[0]) / 6},${b[1] + (c[1] - a[1]) / 6} ${c[0] - (e[0] - b[0]) / 6},${c[1] - (e[1] - b[1]) / 6} ${c[0]},${c[1]}`; } return d; }
  function linha(pai, pts, t, d, o = {}) {
    const svg = sv("svg", pai, { class: "fio", viewBox: `0 0 ${o.w || W} ${o.h || H}` }); if (o.w) Object.assign(svg.style, { width: px(o.w), height: px(o.h) });
    const dd = suave(pts);
    let area = null;
    if (o.area) { const g = sv("linearGradient", sv("defs", svg), { id: "ga" + t.toFixed(2).replace(".", ""), x1: 0, y1: 0, x2: 0, y2: 1 });
      sv("stop", g, { offset: 0, "stop-color": COR, "stop-opacity": .28 }); sv("stop", g, { offset: 1, "stop-color": COR, "stop-opacity": 0 });
      const last = pts[pts.length - 1]; area = sv("path", svg, { d: dd + ` L${last[0]},${o.h || H} L${pts[0][0]},${o.h || H} Z`, fill: `url(#${g.id})` }); }
    const p = sv("path", svg, { d: dd, fill: "none", stroke: COR, "stroke-width": o.esp || 6, "stroke-linecap": "round", style: `filter: drop-shadow(0 0 10px ${COR})` });
    const L = p.getTotalLength(); p.style.strokeDasharray = L; p.style.strokeDashoffset = L;
    const ponta = mk("div", "ponta", pai); const pr = { f: 0 };
    const x0 = pts[0][0], x1 = pts[pts.length - 1][0];
    const pinta = () => { p.style.strokeDashoffset = L * (1 - pr.f); const q = p.getPointAtLength(L * pr.f); ponta.style.left = px(q.x); ponta.style.top = px(q.y);
      if (area) area.style.clipPath = `inset(0 ${(1 - (q.x - x0) / (x1 - x0)) * 100}% 0 0)`; if (o.cada) o.cada(q, pr.f); };
    pinta(); tl.to(pr, { f: 1, duration: d, ease: o.ease || "power2.inOut", onUpdate: pinta }, t);
    tl.fromTo(ponta, { scale: 0 }, { scale: 1, duration: .3, ease: "expo.out" }, t);
    return { svg, p, ponta, L };
  }

  // ---------- cartões de interface ----------
  function cartao(pai, css) {               // cartão de crédito
    const c = mk("div", "cartao", pai, css);
    mk("div", "ondas", c); const m = mk("div", "mc", c); m.innerHTML = icone(34) + (P.marca || "marca");
    mk("div", "chip2", c); mk("div", "num", c).textContent = "•••• " + (P.final_cartao || "4821");
    const b = mk("div", "bola", c); mk("b", "", b); mk("b", "", b); return c;
  }
  function icone(z, cor) { return `<svg width="${z}" height="${z}" viewBox="0 0 40 40" fill="none"><polyline points="4,30 15,19 22,25 36,10" stroke="${cor || COR}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>`; }
  function rosca(pai, segs, z, t, d) {
    const svg = sv("svg", pai, { width: z, height: z, viewBox: "0 0 200 200" }); svg.style.display = "block";
    sv("circle", svg, { cx: 100, cy: 100, r: 80, fill: "none", stroke: "rgba(255,255,255,.06)", "stroke-width": 22 });
    const C = 2 * Math.PI * 80; let acc = 0;
    segs.forEach((g, k) => { const cc = sv("circle", svg, { cx: 100, cy: 100, r: 80, fill: "none", stroke: g.cor || [COR, COR2, COR3, "#D9DDEA"][k % 4], "stroke-width": 22, "stroke-linecap": "round", transform: `rotate(${-90 + acc * 360} 100 100)` });
      const len = Math.max(.001, g.frac * C - 8); cc.style.strokeDasharray = `${len} ${C}`;
      tl.fromTo(cc, { strokeDashoffset: len }, { strokeDashoffset: 0, duration: d * .8, ease: "power3.out" }, t + k * d * .12); acc += g.frac; });
    return svg;
  }
  // um cartão de painel; devolve o elemento. tipos: saldo | barras | rosca | lista | aviso | meta | cartao
  function cardUI(pai, k, css, t, d) {
    if (k.tipo === "cartao") { const e = cartao(pai, { left: css.left, top: css.top }); gsap.set(e, { scale: parseFloat(css.width || 640) / 640, transformOrigin: "0% 0%" }); return e; }
    const c = mk("div", "card" + (k.tipo === "aviso" ? " aviso" : ""), pai, css);
    if (k.chip) mk("span", "chip dir", c).textContent = k.chip;
    if (k.tipo === "aviso") { mk("div", "ico", c); const n = mk("div", "nm", c); n.innerHTML = (k.nome || "") + `<small>${k.sub || ""}</small>`; mk("div", "vl", c).textContent = k.valor || ""; return c; }
    if (k.rotulo) mk("div", "rot", c).textContent = k.rotulo;
    if (k.titulo) mk("div", "tit", c).textContent = k.titulo;
    if (k.tipo === "saldo") { valor(mk("div", "val", c), k.valor, t + .2, d * .8); if (k.sub) { const s2 = mk("div", "chip", c, { marginTop: "14px" }); s2.textContent = k.sub; }
      if (k.linha !== false) { const box2 = mk("div", "", c, { position: "relative", height: "40px", marginTop: "10px" }); const pts = []; for (let i = 0; i <= 8; i++) pts.push([i * 52, 30 - i * 2.6 - (i % 3 === 1 ? 6 : 0)]);
        const g = linha(box2, pts, t + .3, d * .7, { w: 420, h: 40, esp: 4 }); g.ponta.style.display = "none"; } }
    if (k.tipo === "barras") { if (k.valor) valor(mk("div", "val", c, { fontSize: "46px" }), k.valor, t + .2, d * .6);
      const vs = k.valores || [.45, .62, .38, .72, .95, .5, .4], on = k.destaque != null ? k.destaque : vs.indexOf(Math.max(...vs));
      const b = mk("div", "barras", c); const bs = vs.map((v, i) => mk("i", i === on ? "on" : "", b, { height: (v * 100) + "%" }));
      tl.fromTo(bs, { scaleY: 0 }, { scaleY: 1, duration: .7, ease: "expo.out", stagger: .06 }, t + .25);
      if (k.dias) { const dd = mk("div", "dias", c); k.dias.forEach(x => mk("b", "", dd).textContent = x); } }
    if (k.tipo === "rosca") { const wrap = mk("div", "", c, { position: "relative", width: px(k.tam || 300), margin: "22px auto 0" });
      rosca(wrap, k.segmentos || [{ frac: .55 }, { frac: .25 }, { frac: .12 }], k.tam || 300, t + .2, d * .8);
      const ct = mk("div", "", wrap, { position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" });
      valor(mk("div", "val", ct, { fontSize: px((k.tam || 300) * .17), marginTop: 0 }), k.valor, t + .2, d * .85);
      if (k.sub) mk("div", "rot", ct, { fontSize: "22px" }).textContent = k.sub; }
    if (k.tipo === "meta") { const wrap = mk("div", "", c, { position: "relative", width: "190px", margin: "18px auto 6px" }); const f = k.frac || .72;
      rosca(wrap, [{ frac: f, cor: COR }], 190, t + .2, d * .8);
      const ct = mk("div", "", wrap, { position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" });
      valor(mk("div", "val", ct, { fontSize: "40px", marginTop: 0 }), { de: 0, ate: Math.round(f * 100), suf: "%" }, t + .2, d * .8);
      if (k.sub) mk("div", "tit", c, { fontSize: "28px" }).textContent = k.sub; }
    if (k.tipo === "lista") { const l = mk("div", "lista", c);
      (k.itens || []).forEach((it, i) => { const r2 = mk("div", "it", l); const ic = mk("div", "ico", r2); mk("i", "", ic);
        const nm = mk("div", "nm", r2); nm.textContent = it[0]; const v = mk("div", "vl", r2); valor(v, it[1], t + .3 + i * .1, d * .6);
        if (it[2] != null) { const tr = mk("div", "tr", nm); const bi = mk("i", "", tr, { background: [COR, COR2, COR2, COR3][i % 4] });
          tl.fromTo(bi, { scaleX: 0 }, { scaleX: it[2], duration: .9, ease: "expo.out" }, t + .3 + i * .1); } }); }
    return c;
  }
  const entraCard = (els, t, st = .14) => tl.fromTo(els, { y: 90, z: -260, opacity: 0, filter: "blur(14px)" }, { y: 0, z: 0, opacity: 1, filter: "blur(0px)", duration: .95, ease: "expo.out", stagger: st }, t);
  // câmera: leva o ponto (x,y) do mundo para o centro, com escala e giro
  function mergulha(mundo, x, y, esc, t, d, extra) {
    tl.to(mundo, Object.assign({ x: W / 2 - W / 2 - esc * (x - W / 2), y: CY - H / 2 - esc * (y - H / 2), scale: esc, duration: d, ease: "power3.inOut" }, extra || {}), t);
  }

  // ---------- tipos de cena ----------
  const TIPOS = {
    // gancho: a linha de gráfico atravessa a tela e a palavra nasce em contorno e se preenche quando a ponta passa
    linha(c, el, t, d) {
      const ls = String(c.texto || "SEU|DINHEIRO").split("|"), y0 = c.y || CY - 60;
      const pts = c.pontos_linha || [[-20, y0 + 330], [150, y0 + 300], [230, y0 + 200], [300, y0 + 290], [470, y0 + 170], [560, y0 + 210], [760, y0 + 40], [880, y0 - 30], [990, y0 - 150], [1040, y0 - 120]];
      const dl = Math.min(d * .55, 1.6); const g = linha(el, pts, t, dl, { ease: "power2.inOut" });
      const ult = ls.length - 1, base = texto(el, ls[ult], { y: y0, tam: c.tam || 190, alinhar: "center" });
      const sol = base.el; const cont = sol.cloneNode(true); cont.classList.add("contorno"); el.insertBefore(cont, sol);
      tl.fromTo(sol, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: dl * .55, ease: "power2.inOut" }, t + dl * .45);
      tl.fromTo(cont, { opacity: 0 }, { opacity: 1, duration: .25, ease: "power2.out" }, t + .1);
      tl.to(cont, { opacity: 0, duration: .3, ease: "power2.out" }, t + dl);
      tl.to([g.svg, g.ponta], { opacity: 0, duration: .45, ease: "power2.out" }, t + dl + .1);
      if (ult > 0) { const top = texto(el, ls.slice(0, ult), { y: y0 - (c.tam || 190) * .92 * ult, tam: c.tam || 190, alinhar: "center" }); sobe(top.sp, t + dl * .7, .08); }
    },
    // frase empilhada: grupos de linhas sobem por máscara; o grupo anterior encolhe, fica cinza e sai por cima
    pilha(c, el, t, d) {
      const gs = c.grupos || [c.linhas || ["SUA", "FRASE", "AQUI."]]; const tam = c.tam || 175;
      const tg = gs.map((g, i) => c.em && c.em[i] != null ? c.em[i] : i * d / gs.length);
      let ant = null;
      gs.forEach((g, i) => {
        const T = texto(el, g, { y: CY, tam, centro: true }); const ti = t + tg[i];
        sobe(T.sp, ti, Math.min(.28, Math.max(.1, (d / gs.length) * .45 / g.length)));
        if (ant) { const hA = ant.el.getBoundingClientRect().height, hN = T.el.getBoundingClientRect().height;
          tl.to(ant.el, { y: -(hN / 2 + hA * .35 + 30), scale: .62, transformOrigin: "0% 100%", opacity: .3, duration: .6, ease: "expo.out" }, ti);
          tl.to(ant.el, { opacity: 0, filter: "blur(10px)", duration: .4, ease: "power2.in" }, ti + .55); }
        ant = T;
      });
    },
    // título grande no alto + cartões de interface flutuando em 3D; a câmera mergulha no cartão de foco
    painel(c, el, t, d) {
      const p3 = mk("div", "palco3d", el), mundo = mk("div", "mundo", p3);
      if (c.titulo) { const T = texto(el, c.titulo, { y: 150, tam: c.tam || 150 }); tl.fromTo(T.sp, { x: 380, filter: "blur(26px)", opacity: 0 }, { x: 0, filter: "blur(0px)", opacity: 1, duration: .8, ease: "expo.out" }, t);
        if (c.foco != null) tl.to(T.el, { y: -260, filter: "blur(12px)", opacity: 0, duration: .7, ease: "power3.in" }, t + d * .4); }
      const ks = c.cartoes || [];
      const LAY = c.posicoes || [[560, 470, 400], [140, 680, 800], [120, 1220, 560], [560, 1300, 420], [200, 1560, 640]];
      const els = ks.map((k, i) => { const [x, y, w] = (k.pos || LAY[i % LAY.length]); return cardUI(mundo, k, { left: px(x), top: px(y), width: px(w) }, t + .25 + i * .14, d - .4); });
      tl.set(mundo, { rotationY: c.giro != null ? c.giro : -12, rotationX: 7, rotationZ: 1.5 }, t);
      entraCard(els, t + .15);
      tl.to(mundo, { rotationY: (c.giro != null ? c.giro : -12) + 5, duration: d, ease: "sine.inOut" }, t);
      if (c.foco != null && els[c.foco]) { const e = els[c.foco], x = parseFloat(e.style.left) + e.offsetWidth / 2, y = parseFloat(e.style.top) + e.offsetHeight / 2;
        mergulha(mundo, x, y, c.zoom || 1.45, t + d * .42, d * .5, { rotationY: -3, rotationX: 2 });
        if (c.depois != null && els[c.depois]) { const e2 = els[c.depois], x2 = parseFloat(e2.style.left) + e2.offsetWidth / 2, y2 = parseFloat(e2.style.top) + e2.offsetHeight / 2;
          mergulha(mundo, x2, y2, c.zoom || 1.45, t + d * .72, d * .26, { rotationY: -6 }); } }
    },
    // um disco da cor cresce e cobre a tela; a palavra fecha o espaçamento; o cartão gira em 3D e assenta
    revela(c, el, t, d) {
      el.classList.remove("cor"); const ox = c.origem ? c.origem[0] : W / 2, oy = c.origem ? c.origem[1] : CY, r = Math.hypot(Math.max(ox, W - ox), Math.max(oy, H - oy)) + 40;
      const disco = mk("div", "disco", el, { width: px(2 * r), height: px(2 * r), left: px(ox - r), top: px(oy - r) });
      tl.fromTo(disco, { scale: 0 }, { scale: 1, duration: .6, ease: "expo.inOut" }, t - .3);
      const T = texto(el, c.texto || "MOVA.", { y: c.y || 520, tam: c.tam || 220, alinhar: "center" }); T.el.style.color = "var(--tinta)"; T.el.querySelectorAll(".pt").forEach(e => e.style.color = "var(--tinta)");
      tl.fromTo(T.sp, { letterSpacing: ".5em", filter: "blur(18px)", opacity: 0 }, { letterSpacing: "0em", filter: "blur(0px)", opacity: 1, duration: .9, ease: "expo.out" }, t + .1);
      if (c.objeto !== false) { const p3 = mk("div", "palco3d", el), m = mk("div", "mundo", p3);
        const k = cartao(m, { left: px(W / 2 - 320), top: px(c.y_objeto || 1080) });
        tl.fromTo(k, { rotationY: 92, rotationZ: -30, rotationX: 24, y: 420, z: -300 }, { rotationY: -10, rotationZ: -14, rotationX: 16, y: 0, z: 0, duration: 1.1, ease: "expo.out" }, t + .15);
        tl.to(k, { rotationZ: -10, y: -24, duration: d, ease: "sine.inOut" }, t + 1.2); }
    },
    // palavras trocando em fila no alto; cartão com fio até a pílula com valor contando e selo de confirmação
    troca(c, el, t, d) {
      const ps = c.palavras || ["SIMPLES.", "RÁPIDO.", "DO SEU JEITO."]; const em = ps.map((_, i) => c.em && c.em[i] != null ? c.em[i] : i * d / ps.length);
      ps.forEach((w, i) => { const T = texto(el, w, { y: c.y || 250, tam: c.tam || 130 }); sobe(T.sp, t + em[i] + (i ? .04 : 0), 0, .6); if (i < ps.length - 1) sai(T.sp, t + em[i + 1] - .22, .26); });
      const p3 = mk("div", "palco3d", el), m = mk("div", "mundo", p3);
      const k = cartao(m, { left: px(W - 560), top: px(-130) }); tl.set(k, { scale: .72, rotationZ: -12, rotationX: 18, transformOrigin: "50% 50%" }, t);
      tl.fromTo(k, { x: -500, y: 500, filter: "blur(20px)" }, { x: 0, y: 0, filter: "blur(0px)", duration: .8, ease: "expo.out" }, t);
      const pil = cardUI(m, { tipo: "saldo", rotulo: c.rotulo || "Reserva", valor: c.valor || { de: 3200, ate: 4800, pre: "R$ ", casas: 2 }, chip: c.chip || "+R$ 1.200", linha: false },
        { left: px(130), top: px(980), width: px(680), padding: "30px 38px" }, t + .35, Math.min(1.6, d * .5));
      entraCard([pil], t + .3, 0);
      linha(el, [[W - 330, 300], [W - 230, 560], [520, 760], [330, 900], [380, 975]], t + .2, .9, { esp: 5 }).ponta.style.display = "none";
      const sel = mk("div", "selo", el, { left: px(600), top: px(930) }); mk("i", "", sel); sel.appendChild(document.createTextNode(c.selo || "Enviado"));
      tl.fromTo(sel, { scale: .6, opacity: 0, filter: "blur(6px)" }, { scale: 1, opacity: 1, filter: "blur(0px)", duration: .5, ease: "expo.out" }, t + Math.min(1.9, d * .5));
      tl.to(m, { y: -40, duration: d, ease: "sine.inOut" }, t);
    },
    // a palavra nasce de uma linha no chão; a linha sobe virando gráfico, a câmera segue a ponta e no fim abre na meta
    cresce(c, el, t, d) {
      const cam = mk("div", "", el, { position: "absolute", left: 0, top: 0, width: px(W * 1.9), height: px(H) });
      const yb = c.y || 1500, T = texto(cam, c.texto || "CRESÇA", { y: yb - 150, tam: c.tam || 170 }); T.el.style.right = "auto";
      const ls = letras(T.sp[0]);
      tl.fromTo(ls, { scaleY: 0, transformOrigin: "50% 100%", opacity: 0 }, { scaleY: 1, opacity: 1, duration: .55, ease: "expo.out", stagger: .07 }, t + .1);
      const wT = T.sp[0].getBoundingClientRect().width;
      const pts = [[M - 10, yb - 175], [M + wT * .5, yb - 190], [M + wT + 40, yb - 205], [M + wT + 180, yb - 120], [M + wT + 330, yb - 330], [M + wT + 470, yb - 230], [M + wT + 640, yb - 600], [M + wT + 760, yb - 470], [M + wT + 900, yb - 900]];
      const rot = c.rotulos || ["R$ 6 mil", "R$ 9 mil", "R$ 12 mil"], idx = [3, 5, 7];
      const rs = rot.map((r2, i) => { const q = pts[idx[i]]; const e = mk("div", "rotulo", cam, { left: px(q[0] - 40), top: px(q[1] + 26) }); e.textContent = r2; tl.set(e, { opacity: 0 }, t); return e; });
      const tag = mk("div", "tag", cam); const tv = mk("div", "v", tag); mk("div", "chip", tag).textContent = c.chip || "▲ 18,4%";
      const dl = d * .62, x0 = Math.max(W * .5, M + wT + 60);
      const g = linha(cam, pts, t + .05, dl, { w: W * 1.9, h: H, area: true, ease: "power1.inOut",
        cada(q) { tag.style.left = px(Math.max(Math.max(0, q.x - x0) + M - 20, q.x - 380)); tag.style.width = "360px"; tag.style.top = px(q.y - 140);
          const camx = Math.max(0, q.x - x0); cam.style.transform = `translate(${-camx}px, ${Math.max(0, (yb - 420) - q.y) * .85}px)`;
          rs.forEach((e, i) => { if (q.x >= pts[idx[i]][0] - 5) e.style.opacity = 1; }); } });
      valor(tv, c.valor || { de: 11800, ate: 12480, pre: "R$ ", casas: 2 }, t + .1, dl);
      if (c.meta) { const last = pts[pts.length - 1]; const mt = mk("div", "meta", cam, { left: px(last[0] + 40), top: px(last[1] - 330) }); mt.innerHTML = `<small>${c.meta_rotulo || "META"}</small>${c.meta}`;
        const ms = sv("svg", cam, { class: "fio" }); const ml = sv("path", ms, { d: `M${last[0]},${last[1]} L${last[0] + 110},${last[1] - 250}`, stroke: COR2, "stroke-width": 3, "stroke-dasharray": "8 8", fill: "none" });
        tl.fromTo([mt, ml], { opacity: 0 }, { opacity: 1, duration: .5, ease: "power2.out" }, t + dl + .1);
        tl.to(el, { scale: .78, transformOrigin: "70% 40%", duration: d - dl, ease: "power3.inOut" }, t + dl); }
      tl.to(g.ponta, { scale: 1.25, duration: .3, ease: "expo.out" }, t + dl);
    },
    // mosaico de cartões inclinado deslizando; as letras se espalham e se refazem na frase nova enquanto os cartões assentam em grade
    caos(c, el, t, d) {
      const p3 = mk("div", "palco3d", el), mundo = mk("div", "mundo", p3);
      const G = [[{ tipo: "saldo", rotulo: "Patrimônio", valor: c.valor || { de: 22400, ate: 24860.42, pre: "R$ ", casas: 2 }, chip: c.chip || "▲ 18,4% este ano" }, 70, 560, 940],
        [{ tipo: "barras", rotulo: "Esta semana", valor: "R$ 486", dias: ["S", "T", "Q", "Q", "S", "S", "D"] }, 70, 900, 455],
        [{ tipo: "meta", rotulo: "Meta de economia", sub: c.meta || "Viagem ao Japão", frac: .72 }, 555, 900, 455],
        [{ tipo: "cartao" }, 70, 1330, 455],
        [{ tipo: "lista", rotulo: "Recentes", itens: c.itens || [["Salário", "+R$ 4.200"], ["Aluguel", "−R$ 1.450"], ["Café", "−R$ 6,40"]] }, 555, 1330, 455]];
      const tc = t + d * (c.virada || .45);
      const els = G.map(([k, x, y, w]) => cardUI(mundo, k, { left: px(x), top: px(y), width: px(w) }, tc + .2, d - (tc - t) - .3));
      tl.set(mundo, { rotationX: 50, rotationZ: -26, scale: .92, x: 30, y: 120 }, t);
      els.forEach((e, i) => { tl.set(e, { x: (i % 2 ? 120 : -90) + R() * 60, y: (i - 2) * 70 }, t); });
      tl.fromTo(els, { z: -260, opacity: 0, filter: "blur(14px)" }, { z: 0, opacity: 1, filter: "blur(0px)", duration: .95, ease: "expo.out", stagger: .06 }, t);
      tl.to(mundo, { x: -60, y: 40, duration: tc - t, ease: "sine.inOut" }, t);
      tl.to(mundo, { rotationX: 0, rotationZ: 0, scale: 1, x: 0, y: 0, duration: 1.1, ease: "expo.inOut" }, tc - .1);
      tl.to(els, { x: 0, y: 0, duration: 1.1, ease: "expo.inOut" }, tc - .1);
      const A = texto(el, c.antes || "MENOS *CAOS.*", { y: 200, tam: c.tam || 120 }), B = texto(el, c.depois || ["~MAIS~", "CONTROLE."], { y: 150, tam: c.tam || 130 });
      const la = letras(A.el), lb = letras(B.el);
      sobe(A.sp, t + .1, .1);
      tl.to(la, { x: () => (R() - .5) * 420, y: () => (R() - .5) * 300, rotation: () => (R() - .5) * 160, opacity: 0, filter: "blur(10px)", duration: .45, ease: "power3.in", stagger: .012 }, tc - .35);
      tl.fromTo(lb, { x: () => (R() - .5) * 420, y: () => (R() - .5) * 300, rotation: () => (R() - .5) * 160, opacity: 0, filter: "blur(10px)" }, { x: 0, y: 0, rotation: 0, opacity: 1, filter: "blur(0px)", duration: .8, ease: "expo.out", stagger: .015 }, tc);
    },
    // cartão de regras com chaves ligando uma a uma e a frase empilhada embaixo
    regras(c, el, t, d) {
      const its = c.itens || [["Arredonde cada compra", "Troco → Reserva"], ["Guarde 10% do salário", "Todo dia de pagamento"], ["Contas no automático", "6 contas, sem atraso"]];
      const card = mk("div", "card", el, { left: px(M + 20), right: px(M + 20), top: px(c.y_cartao || 520) });
      mk("div", "tit", card, { marginBottom: "22px" }).textContent = c.titulo || "Suas regras";
      const chip = mk("span", "chip dir", card); const n = { v: 0 }; const pc = () => chip.textContent = `${Math.round(n.v)}/${its.length} ativas`; pc();
      const ks = its.map(([a, b]) => { const r2 = mk("div", "regra", card); r2.innerHTML = `${a}<small>${b}</small>`; const k = mk("div", "chave", r2); return [k, mk("i", "", k)]; });
      entraCard([card], t, 0);
      ks.forEach(([k, b], i) => { const ti = t + .6 + i * Math.min(.55, d * .5 / its.length);
        tl.to(k, { backgroundColor: COR, duration: .3, ease: "power2.out" }, ti); tl.to(b, { x: 32, duration: .35, ease: "expo.out" }, ti);
        tl.to(n, { v: i + 1, duration: .01, onUpdate: pc }, ti); });
      const T = texto(el, c.texto || ["~SEU DINHEIRO,~", "SUAS REGRAS."], { y: c.y || 1180, tam: c.tam || 140 });
      sobe(T.sp, t + .35, Math.min(.6, d * .3));
    },
    // fecho: ícone se desenha, frase sobe, encolhe e dá lugar à marca com a frase dela
    fecho(c, el, t, d) {
      const ic = mk("div", "", el, { position: "absolute", left: px(W / 2 - 75), top: px((c.y || 760) - 230), width: "150px", height: "150px" });
      ic.innerHTML = `<svg width="150" height="150" viewBox="0 0 40 40" fill="none"><polyline points="4,30 15,19 22,25 34,12" stroke="${COR}" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/><circle cx="35" cy="11" r="2.6" fill="#fff" opacity="0"/></svg>`;
      tl.to(ic.querySelector("polyline"), { strokeDashoffset: 0, duration: .7, ease: "power3.inOut" }, t);
      tl.to(ic.querySelector("circle"), { opacity: 1, duration: .2 }, t + .6);
      const T = texto(el, c.linhas || ["MOVA SEU DINHEIRO.", "MOVA SEU [FUTURO]."], { y: c.y || 760, tam: c.tam || 112, alinhar: "center" });
      sobe(T.sp, t + .25, Math.min(.9, d * .25));
      const tm = t + d * (c.virada || .55);
      tl.to([T.el, ic], { scale: .55, filter: "blur(14px)", opacity: 0, duration: .5, ease: "power3.in", transformOrigin: "50% 0%" }, tm);
      const mc = mk("div", "marca", el, { top: px((c.y || 760) + 40) });
      mc.innerHTML = `<div class="nome">${icone(130)}${c.marca || P.marca || "marca"}</div><div class="frase">${c.frase || ""}</div>`;
      tl.fromTo(mc, { scale: 1.12, filter: "blur(16px)", opacity: 0 }, { scale: 1, filter: "blur(0px)", opacity: 1, duration: .9, ease: "expo.out" }, tm + .3);
    },
  };

  // ---------- montagem: cenas sobre o fundo contínuo ----------
  let t = 0, ant = null;
  P.cenas.forEach((c, i) => {
    const d = c.dur || 2, el = mk("div", "cena", box);
    (TIPOS[c.tipo] || TIPOS.pilha)(c, el, t, d);
    const tr = c.transicao || (c.tipo === "revela" ? "disco" : "desfoque");
    if (!ant) tl.set(el, { opacity: 1 }, 0);
    else if (tr === "disco") { tl.set(el, { opacity: 1 }, t - .3); tl.set(ant, { opacity: 0 }, t + .3); }
    else if (tr === "corte") { tl.set(el, { opacity: 1 }, t); tl.set(ant, { opacity: 0 }, t); }
    else if (tr === "chicote") { tl.to(ant, { x: -W * .6, filter: "blur(30px)", opacity: 0, duration: .28, ease: "power3.in" }, t - .2);
      tl.fromTo(el, { opacity: 0, x: W * .6, filter: "blur(30px)" }, { opacity: 1, x: 0, filter: "blur(0px)", duration: .45, ease: "expo.out" }, t); }
    else { tl.to(ant, { opacity: 0, scale: 1.08, filter: "blur(18px)", duration: .4, ease: "power2.in" }, t - .25);
      tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: .35, ease: "power2.out" }, t - .1); }
    ant = el; t += d;
  });
  tl.fromTo("#cam", { scale: 1 }, { scale: 1.04, duration: t, ease: "none" }, 0);
  tl.fromTo("#ceu", { x: 0, y: 0 }, { x: -60, y: 40, duration: t, ease: "none" }, 0);
  window.__timelines = window.__timelines || {}; window.__timelines["painel"] = tl;
})();
