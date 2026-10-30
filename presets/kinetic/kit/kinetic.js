// Preset KINETIC v2: tipografia cinética estilo "Katana" (estudada em 13/10/2026). Cada cena = uma batida da fala.
// Timeline GSAP pausada e determinística (HyperFrames renderiza quadro a quadro). Tipos de cena e campos: ver gerar.py.
(async function () {
  try { await Promise.all([document.fonts.load("900 200px Archivo"), document.fonts.load("100 200px Archivo"),
    document.fonts.load("italic 900 200px Archivo"), document.fonts.load("700 60px 'JetBrains Mono'")]); await document.fonts.ready; } catch (e) {}
  const P = window.PLANO, W = P.w, H = P.h, CY = P.centro_y || 960;
  const root = document.getElementById("root"), box = document.getElementById("cenas");
  root.style.setProperty("--cor", P.cor || "#E8202A"); root.style.setProperty("--cor2", P.cor2 || "#C8FF3D");
  root.style.setProperty("--brilho", P.brilho || "rgba(232,32,42,.55)");
  let s = P.semente || 7; const R = () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const tl = gsap.timeline({ paused: true });
  const AREA = P.area || (W - 260);   // folga dentro da zona segura do Reels (x 70-1010): o zoom de entrada e o brilho passam da caixa medida

  const mk = (tag, cls, pai, css) => { const e = document.createElement(tag); if (cls) e.className = cls; if (css) Object.assign(e.style, css); if (pai) pai.appendChild(e); return e; };
  function fit(el, maxW, maxPx) { el.style.fontSize = "200px"; el.style.display = "inline-block"; const w = el.getBoundingClientRect().width || 1; el.style.display = ""; const f = Math.min(maxPx, 200 * maxW / w); el.style.fontSize = f + "px"; return f; }
  function marcar(txt, letras) {           // [caixa]  *vermelho*  ponto final na cor
    let pt = ""; if (/[.!?…]$/.test(txt) && !/[\]*]$/.test(txt)) { pt = txt.slice(-1); txt = txt.slice(0, -1); }
    const temMarca = /[\[*]/.test(txt);
    let h = temMarca || !letras ? txt : [...txt].map(c => `<span class="c">${c === " " ? "&nbsp;" : c}</span>`).join("");
    h = h.replace(/\[([^\]]+)\]/g, '<span class="caixa">$1</span>').replace(/\*([^*]+)\*/g, '<span class="verm">$1</span>');
    return h + (pt ? `<span class="pt">${pt}</span>` : "");
  }
  function linha(pai, txt, o = {}) {
    const e = mk("div", "L" + (o.cor ? " cor" : "") + (o.contorno ? " contorno" : "") + (o.brilho ? " brilho" : "") + (o.ital ? " ital" : ""), pai);
    e.innerHTML = marcar(txt, o.letras); fit(e, (o.larg || 1) * AREA, o.max || 420); return e;
  }

  // ---------- entradas de texto ----------
  function entra(tipo, els, t, d) {
    els = [].concat(els);
    const L = q => els.flatMap(e => [...e.querySelectorAll(q)]);
    switch (tipo) {
      case "blur": tl.fromTo(els, { x: W * .7, skewX: -22, filter: "blur(28px)", opacity: 0 }, { x: 0, skewX: 0, filter: "blur(0px)", opacity: 1, duration: .22, ease: "expo.out", stagger: .06 }, t); break;
      case "subir": tl.fromTo(els, { y: 140, filter: "blur(16px)", opacity: 0, scaleY: 1.5 }, { y: 0, filter: "blur(0px)", opacity: 1, scaleY: 1, duration: .2, ease: "power4.out", stagger: .08 }, t); break;
      case "queda": { const c = L(".c"); if (c.length) tl.fromTo(c, { y: -280, rotation: () => (R() - .5) * 60, opacity: 0 }, { y: 0, rotation: 0, opacity: 1, duration: .22, ease: "back.out(2.2)", stagger: .028 }, t); else entra("subir", els, t, d); break; }
      case "estica": tl.fromTo(els, { scaleX: 3.4, letterSpacing: ".35em", filter: "blur(10px)", opacity: 0 }, { scaleX: 1, letterSpacing: "-.005em", filter: "blur(0px)", opacity: 1, duration: .32, ease: "expo.out" }, t); break;
      case "digita": { const c = L(".c"); const p = Math.min(.045, d * .6 / Math.max(1, c.length)); tl.set(c, { opacity: 0 }, t); c.forEach((x, j) => tl.set(x, { opacity: 1 }, t + j * p)); break; }
      case "glitch": els.forEach(e => {
        ["#ff2a2a", "#22e0ff"].forEach((cc, j) => { const k = e.cloneNode(true); Object.assign(k.style, { position: "absolute", left: 0, right: 0, top: 0, color: cc, mixBlendMode: "screen", webkitTextStroke: "0" }); e.appendChild(k);
          tl.fromTo(k, { x: j ? 26 : -26, opacity: .95 }, { x: 0, opacity: 0, duration: .28, ease: "steps(6)" }, t); });
        tl.fromTo(e, { opacity: 0, clipPath: "inset(42% 0 38% 0)" }, { opacity: 1, clipPath: "inset(0% 0 0% 0)", duration: .2, ease: "steps(4)" }, t);
        tl.fromTo(e, { x: -34 }, { x: 0, duration: .26, ease: "steps(5)" }, t); }); break;
      case "peso": tl.fromTo(els, { fontVariationSettings: '"wdth" 62, "wght" 100', opacity: 0 }, { fontVariationSettings: '"wdth" 125, "wght" 900', opacity: 1, duration: .3, ease: "power3.out", stagger: .06 }, t); break;
      default: tl.fromTo(els, { scale: 2.3, opacity: 0, filter: "blur(18px)" }, { scale: 1, opacity: 1, filter: "blur(0px)", duration: .22, ease: "power4.out", stagger: .07 }, t);   // zoom
    }
  }
  const tremor = (el, t) => tl.fromTo(el, { x: 0 }, { x: 12, duration: .03, yoyo: true, repeat: 3, ease: "none" }, t);

  // ---------- tipos de cena ----------
  const TIPOS = {
    palavra(c, P2, t, d) {
      const ls = String(c.texto).split("|"); const um = ls.length === 1;
      const els = ls.map((x, k) => linha(P2, x, { cor: c.destaque === k, contorno: c.contorno === k, brilho: true, letras: ["queda", "digita"].includes(c.entrada), max: um ? 820 : 430, larg: c.destaque === k ? .9 : 1 }));
      entra(c.entrada || "zoom", els, t, d); tremor(P2, t + .2);
    },
    hierarquia(c, P2, t, d, el) {
      P2.classList.add(c.alinhar === "centro" ? "cen" : "esq");
      const T = { p: [.55, 95], m: [.75, 220], g: [1, 430] };
      const els = c.linhas.map(o => { const [lg, mx] = T[o.tam || "g"]; return linha(P2, o.t, { cor: o.cor, contorno: o.contorno, brilho: true, larg: (c.forma && H <= W ? .66 : 1) * lg, max: mx }); });
      const ent = ["subir", "blur", "zoom", "estica"];
      els.forEach((e, k) => { const o = c.linhas[k]; entra(o.entrada || ent[k % ent.length], e, t + (o.em != null ? o.em : k * Math.min(.28, d / (els.length + 1))), d); });
      if (c.forma) { if (H > W) { P2.style.top = (CY + 230) + "px"; forma(c.forma, el, t + .1, d, { x: W / 2, y: CY - 380, r: 250 }); } else forma(c.forma, el, t + .1, d, { x: W * .74, y: CY, r: 300 }); }
      tremor(P2, t + .2);
    },
    eco(c, P2, t, d) {
      const main = linha(P2, c.texto, { brilho: true, max: 820 });
      const h = main.getBoundingClientRect().height;
      [-2, -1, 1, 2].forEach(k => { const g = main.cloneNode(true); g.classList.add("contorno"); g.classList.remove("brilho"); Object.assign(g.style, { position: "absolute", left: 0, right: 0, top: 0 }); P2.appendChild(g);
        tl.fromTo(g, { y: 0, opacity: .9 }, { y: k * h * .92, opacity: Math.abs(k) === 1 ? .55 : .25, duration: .3, ease: "expo.out" }, t + .06);
        tl.to(g, { y: k * h * 1.05, duration: d - .36, ease: "none" }, t + .36); });
      entra("glitch", main, t, d);
    },
    faixa(c, P2, t, d, el) {
      const f = mk("div", "faixa", null); el.querySelector(".mov").insertBefore(f, P2);
      tl.fromTo(f, { scaleX: 0, transformOrigin: "0% 50%" }, { scaleX: 1, duration: .18, ease: "expo.out" }, t);
      const e = linha(P2, c.texto, { ital: true, max: 360, larg: .92 }); e.style.color = "#fff"; e.style.transform = "rotate(-9deg)";
      tl.fromTo(e, { x: W * .8, filter: "blur(24px)", opacity: 0 }, { x: 0, filter: "blur(0px)", opacity: 1, duration: .24, ease: "expo.out" }, t + .06);
      tl.to(e, { x: -40, duration: d, ease: "none" }, t + .3); tremor(f, t + .2);
    },
    caixa(c, P2, t, d) {
      P2.classList.add(c.alinhar === "centro" ? "cen" : "esq");
      const ls = String(c.texto).split("|");
      ls.forEach((x, k) => { const e = linha(P2, x, { max: k === 0 && ls.length > 1 ? 160 : 330, larg: k === 0 && ls.length > 1 ? .8 : 1 });
        const toks = x.match(/\[[^\]]+\][.!?]?|\*[^*]+\*|\S+/g) || [];
        e.innerHTML = toks.map(z => `<span class="w" style="display:inline-block">${marcar(z)}</span>`).join(" "); fit(e, (k === 0 && ls.length > 1 ? .8 : 1) * AREA, k === 0 && ls.length > 1 ? 160 : 330);
        const ws = [...e.querySelectorAll(".w")];
        ws.forEach((w, j) => { const tt = t + (k * ws.length + j) * Math.min(.14, d * .6 / (ls.length * ws.length));
          tl.fromTo(w, { y: 90, opacity: 0, filter: "blur(10px)" }, { y: 0, opacity: 1, filter: "blur(0px)", duration: .16, ease: "back.out(2)" }, tt);
          const cx = w.querySelector(".caixa"); if (cx) tl.fromTo(cx, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: .16, ease: "expo.out" }, tt + .04); }); });
    },
    prompt(c, P2, t, d, el) {
      const b = mk("div", "input mono", el.querySelector(".mov")); b.style.setProperty("--cy", CY + "px");
      const txt = mk("div", "", b); const en = mk("div", "enter", b); en.textContent = "↵";
      let h = ""; String(c.texto).split(/(\[[^\]]+\])/).forEach(part => { const tok = /^\[/.test(part); const z = tok ? part.slice(1, -1) : part;
        const cs = [...z].map(ch => `<span class="c" style="opacity:0">${ch === " " ? "&nbsp;" : ch}</span>`).join("");
        h += tok ? `<span class="tok" style="display:inline">${cs}</span>` : cs; });
      txt.innerHTML = h + '<span class="cur"></span>';
      tl.fromTo(b, { y: 160, opacity: 0, rotationX: 25 }, { y: 0, opacity: 1, rotationX: 0, duration: .25, ease: "power3.out" }, t);
      const cs = [...txt.querySelectorAll(".c")], p = Math.min(.05, (d * .62) / cs.length);
      cs.forEach((x, j) => tl.set(x, { opacity: 1 }, t + .25 + j * p));
      tl.to(txt.querySelector(".cur"), { opacity: 0, duration: .01, repeat: 9, yoyo: true, repeatDelay: .07 }, t);
      const fim = t + .25 + cs.length * p;
      tl.to(en, { backgroundColor: getComputedStyle(root).getPropertyValue("--cor"), scale: 1.2, duration: .1, yoyo: true, repeat: 1 }, fim + .05);
      tl.to(b, { scale: 1.18, duration: Math.max(.2, t + d - fim - .05), ease: "power2.in" }, fim + .05);
    },
    render(c, P2, t, d, el) {
      const e = linha(P2, c.texto || "RENDER.", { max: 300, brilho: true }); entra("glitch", e, t, d);
      const m = el.querySelector(".mov"); const y0 = CY + 120;
      const br = mk("div", "barra", m, { top: y0 + "px" }); const f = mk("i", "", br);
      const eta = mk("div", "eta", m, { top: (y0 + 50) + "px", fontSize: "92px" }); const pc = mk("div", "eta", m, { top: (y0 - 70) + "px", left: "auto", right: "90px", fontSize: "44px" });
      tl.fromTo(f, { width: "0%" }, { width: "100%", duration: d * .85, ease: "power1.inOut" }, t + .1);
      const o = { v: c.de || 0 }, ate = c.ate || 251; const fmt = v => { v = Math.max(0, Math.round(v)); return "⧗ " + [v / 3600, v / 60 % 60, v % 60].map(x => String(Math.floor(x)).padStart(2, "0")).join(":"); };
      eta.textContent = fmt(o.v); pc.textContent = "0%";
      tl.to(o, { v: ate, duration: d * .85, ease: "none", onUpdate: () => { eta.textContent = fmt(o.v); pc.textContent = Math.round(100 * (o.v - (c.de || 0)) / (ate - (c.de || 0))) + "%"; } }, t + .1);
    },
    rec(c, P2, t, d, el) {
      const m = el.querySelector(".mov"), x = W * .36, y = CY;
      const a = mk("div", "anel", m, { width: "300px", height: "300px", left: (x - 150) + "px", top: (y - 150) + "px" });
      const dt = mk("div", "dot", m, { width: "110px", height: "110px", left: (x - 55) + "px", top: (y - 55) + "px" });
      const tx = mk("div", "L", m, { position: "absolute", left: (x + 200) + "px", top: (y - 90) + "px", fontSize: "50px", fontWeight: 700, textAlign: "left", textTransform: "none", lineHeight: "1.15", whiteSpace: "normal", width: "400px", fontVariationSettings: '"wdth" 100' });
      tx.innerHTML = [...String(c.texto)].map(ch => ch === " " ? " " : `<span class="c">${ch}</span>`).join("") + '<span class="cur"></span>';
      tl.fromTo(dt, { scale: 0 }, { scale: 1, duration: .25, ease: "back.out(3)" }, t);
      tl.fromTo(dt, { opacity: 1 }, { opacity: .55, duration: .18, yoyo: true, repeat: Math.floor(d / .36), ease: "sine.inOut" }, t + .25);
      tl.fromTo(a, { scale: .4, opacity: 0, rotation: 0 }, { scale: 1, opacity: 1, rotation: 200, duration: d, ease: "power2.out" }, t + .05);
      const cs = [...tx.querySelectorAll(".c")], p = Math.min(.05, d * .55 / cs.length); tl.set(cs, { opacity: 0 }, t); cs.forEach((z, j) => tl.set(z, { opacity: 1 }, t + .3 + j * p));
    },
    visor(c, P2, t, d, el) {
      const e = linha(P2, c.texto, { brilho: true, max: 300, larg: .8 }); entra(c.entrada || "zoom", e, t, d);
      const m = el.querySelector(".mov"); const bw = 900, bh = 520, x0 = (W - bw) / 2, y0 = CY - bh / 2;
      [[0, 0, "Top", "Left"], [1, 0, "Top", "Right"], [0, 1, "Bottom", "Left"], [1, 1, "Bottom", "Right"]].forEach(([i, j, a, b]) => {
        const k = mk("div", "canto", m, { left: (x0 + i * (bw - 90)) + "px", top: (y0 + j * (bh - 90)) + "px" }); k.style["border" + a + "Width"] = "8px"; k.style["border" + b + "Width"] = "8px";
        tl.fromTo(k, { x: (i ? 1 : -1) * 120, y: (j ? 1 : -1) * 120, opacity: 0 }, { x: 0, y: 0, opacity: 1, duration: .22, ease: "back.out(2)" }, t + .05); });
      const r = mk("div", "L", m, { position: "absolute", left: (x0 + 20) + "px", top: (y0 - 80) + "px", fontSize: "40px", textAlign: "left", color: "#fff", fontVariationSettings: '"wdth" 100' }); r.innerHTML = '<span class="pt">●</span> REC';
      tl.fromTo(r, { opacity: 0 }, { opacity: 1, duration: .01, repeat: Math.floor(d / .3), yoyo: true, repeatDelay: .15 }, t + .1);
    },
    forma(c, P2, t, d, el) {
      const vert = H > W; P2.classList.add(vert ? "cen" : "esq"); if (vert) P2.style.top = (CY + 260) + "px";
      const e = linha(P2, c.texto, { larg: vert ? .9 : .5, max: 520 }); entra(c.entrada || "blur", e, t, d);
      if (c.sub) { const s2 = linha(P2, c.sub, { larg: .95, max: 150 }); entra("estica", s2, t + Math.min(.4, d * .35), d); }
      forma(c.figura || "cubo", el, t + .08, d, vert ? { x: W / 2, y: CY - 330, r: 200 } : { x: W * .72, y: CY - 40, r: 190 });
    },
    pilha_eco(c, P2, t, d, el) {
      const m = el.querySelector(".mov"); const ws = c.palavras; const n = ws.length; const passo = Math.min(.32, d * .7 / n);
      const base = CY + 260; const linhas = [];
      let alt = 170; ws.forEach((w, i) => { const e = linha(P2, w, { max: 230, larg: .95 }); alt = e.getBoundingClientRect().height * .95; Object.assign(e.style, { position: "absolute", left: "70px", right: "70px", top: base + "px" }); m.appendChild(e); linhas.push(e);
        const ti = t + i * passo; entra(i % 2 ? "blur" : "subir", e, ti, d);
        linhas.slice(0, i).forEach((p, k) => { const deg = i - k; tl.to(p, { y: -alt * (1 - Math.pow(.8, deg)) / .2 * .92, scale: Math.pow(.8, deg), opacity: Math.max(.25, 1 - deg * .22), duration: .18, ease: "power3.out" }, ti); }); });
      const fim = t + n * passo;
      [1, 2, 3].forEach(k => { linhas.forEach((p, i) => { const g = p.cloneNode(true); m.appendChild(g); g.style.opacity = 0;
        tl.fromTo(g, { y: -alt * (1 - Math.pow(.8, (n - 1 - i) + k * n)) / .2 * .92, scale: Math.pow(.8, (n - 1 - i) + k * n), opacity: 0 }, { opacity: .6 / k, duration: .12 }, fim + k * .08); }); });
    },
    explosao(c, P2, t, d, el) {
      P2.classList.add("esq");
      const els = c.linhas.map((o, k) => linha(P2, o.t || o, { cor: o.cor, larg: H > W ? .92 : .62, max: 360 }));
      els.forEach((e, k) => entra(["subir", "blur", "zoom"][k % 3], e, t + k * Math.min(.25, d * .5 / els.length), d));
      const m = el.querySelector(".mov"); const r = 360, x = W * .74, y = CY + (H > W ? 120 : 0);
      const st = mk("div", "estrela", null, { width: r * 2 + "px", height: r * 2 + "px", left: (x - r) + "px", top: (y - r) + "px" }); m.insertBefore(st, P2);
      const ci = mk("div", "forma", null, { width: r * 1.3 + "px", height: r * 1.3 + "px", left: (x - r * .65) + "px", top: (y - r * .65) + "px", borderRadius: "50%", opacity: 0 }); m.insertBefore(ci, P2);
      tl.fromTo(st, { scale: 0, rotation: -40 }, { scale: 1, rotation: 0, duration: .3, ease: "back.out(1.7)" }, t + .1);
      tl.to(st, { rotation: 25, scale: 1.08, duration: d * .6, ease: "none" }, t + .4);
      const tm = t + d * .62;
      tl.to(els, { fontVariationSettings: '"wdth" 100, "wght" 120', duration: .3, ease: "power2.inOut", stagger: .04 }, tm);
      tl.to(st, { scale: .2, opacity: 0, duration: .22 }, tm); tl.fromTo(ci, { scale: .3, opacity: 0 }, { scale: 1, opacity: 1, duration: .3, ease: "back.out(2)" }, tm + .05);
    }
  };
  function forma(tipo, el, t, d, o) {
    const m = el.querySelector(".mov"); const { x, y, r } = o;
    if (tipo === "cubo") {
      const c = mk("div", "cubo", m, { width: r * 2 + "px", height: r * 2 + "px", left: (x - r) + "px", top: (y - r) + "px" });
      [["rotateY(0deg)", 1], ["rotateY(90deg)", .78], ["rotateY(180deg)", 1], ["rotateY(-90deg)", .7], ["rotateX(90deg)", 1.15], ["rotateX(-90deg)", .6]].forEach(([tr, b]) => mk("div", "", c, { transform: tr + ` translateZ(${r}px)`, filter: `brightness(${b})` }));
      tl.fromTo(c, { scale: 0, rotationX: -20, rotationY: 30 }, { scale: 1, duration: .3, ease: "back.out(2)" }, t);
      tl.to(c, { rotationY: 30 + 160, rotationX: -32, duration: d, ease: "power1.inOut" }, t);
    } else if (tipo === "morph") {
      const f = mk("div", "forma", m, { width: r * 2 + "px", height: r * 2 + "px", left: (x - r) + "px", top: (y - r) + "px" });
      const C = "polygon(50% 0%,85% 15%,100% 50%,85% 85%,50% 100%,15% 85%,0% 50%,15% 15%)", T = "polygon(50% 0%,75% 50%,100% 100%,75% 100%,50% 100%,25% 100%,0% 100%,25% 50%)", Q = "polygon(50% 0%,100% 0%,100% 50%,100% 100%,50% 100%,0% 100%,0% 50%,0% 0%)";
      tl.fromTo(f, { scale: 0, clipPath: C, borderRadius: "50%" }, { scale: 1, duration: .25, ease: "back.out(2)" }, t);
      tl.to(f, { clipPath: T, borderRadius: "0%", rotation: 0, duration: .22, ease: "power3.inOut" }, t + d * .35);
      tl.to(f, { clipPath: Q, rotation: 12, duration: .22, ease: "power3.inOut" }, t + d * .65);
    } else if (tipo === "circulo") {
      const f = mk("div", "forma", m, { width: r * 2 + "px", height: r * 2 + "px", left: (x - r) + "px", top: (y - r) + "px", borderRadius: "50%" });
      tl.fromTo(f, { scale: 0 }, { scale: 1, duration: .35, ease: "back.out(1.8)" }, t);
    } else if (tipo === "estrela" || tipo === "interrogacao") {
      const f = mk("div", tipo === "estrela" ? "estrela" : "L cor", m, { position: "absolute", left: (x - r) + "px", top: (y - r * 1.1) + "px", width: r * 2 + "px", height: r * 2 + "px" });
      if (tipo === "interrogacao") { f.textContent = "?"; f.style.fontSize = r * 2.4 + "px"; f.style.lineHeight = "1"; }
      tl.fromTo(f, { scale: 0, rotation: -30 }, { scale: 1, rotation: tipo === "estrela" ? 0 : 8, duration: .3, ease: "back.out(2)" }, t);
      tl.to(f, { rotation: "+=14", duration: d, ease: "none" }, t + .3);
    }
  }

  // ---------- transições ----------
  const barras = document.getElementById("barras"); const BS = [];
  for (let i = 0; i < 9; i++) BS.push(mk("b", "", barras, { top: (R() * H) + "px", height: (20 + R() * 120) + "px" }));
  function transicao(tipo, ant, el, t) {
    const mv = el.querySelector(".mov"), mvA = ant && ant.querySelector(".mov");
    if (tipo === "chicote") { if (mvA) tl.to(mvA, { x: -W * .9, skewX: 18, filter: "blur(30px)", duration: .1, ease: "power3.in" }, t - .1);
      tl.fromTo(mv, { x: W * .9, skewX: -18, filter: "blur(30px)" }, { x: 0, skewX: 0, filter: "blur(0px)", duration: .16, ease: "expo.out" }, t); }
    else if (tipo === "vertical") { if (mvA) tl.to(mvA, { y: -H * .6, filter: "blur(30px)", duration: .1, ease: "power3.in" }, t - .1);
      tl.fromTo(mv, { y: H * .6, filter: "blur(30px)" }, { y: 0, filter: "blur(0px)", duration: .16, ease: "expo.out" }, t); }
    else if (tipo === "glitch") { BS.forEach((b, i) => { const cor = [getComputedStyle(root).getPropertyValue("--cor"), "#fff", "#000"][i % 3];
        tl.set(b, { opacity: 1, background: cor, x: (R() - .5) * 300 }, t); tl.set(b, { opacity: 0 }, t + .09); });
      tl.fromTo(mv, { x: -40 }, { x: 0, duration: .12, ease: "steps(4)" }, t); }
    else if (tipo === "risco") { tl.fromTo("#risco", { opacity: 1, scaleX: 0, top: CY + (R() - .5) * 400 }, { scaleX: 1, duration: .12, ease: "expo.out" }, t - .06); tl.to("#risco", { opacity: 0, duration: .12 }, t + .08);
      tl.fromTo(mv, { scaleY: .02, filter: "brightness(3)" }, { scaleY: 1, filter: "brightness(1)", duration: .16, ease: "expo.out" }, t); }
    else if (tipo === "zoom") { if (mvA) tl.to(mvA, { scale: 2.2, opacity: 0, filter: "blur(20px)", duration: .1, ease: "power2.in" }, t - .1);
      tl.fromTo(mv, { scale: .55, filter: "blur(18px)" }, { scale: 1, filter: "blur(0px)", duration: .2, ease: "expo.out" }, t); }
    else if (tipo === "flash") tl.fromTo("#flash", { opacity: .85 }, { opacity: 0, duration: .14 }, t);
  }

  // ---------- montagem ----------
  const ROD = ["chicote", "glitch", "risco", "zoom", "vertical", "flash"];
  let t = 0, ant = null;
  P.cenas.forEach((c, i) => {
    const d = c.dur || .8, tema = c.tema || ["preto", "vermelho", "branco"][i % 3];
    const el = mk("div", "cena " + tema, box); el.style.setProperty("--cy", CY + "px");
    mk("div", "fundo", el); mk("div", "pontos", el); const mv = mk("div", "mov", el, { position: "absolute", inset: 0 });
    if (tema === "preto") for (let k = 0; k < 14; k++) { const z = 10 + R() * 46; const b = mk("div", "bokeh", mv, { width: z + "px", height: z + "px", left: R() * W + "px", top: R() * H + "px", opacity: .25 + R() * .5 });
      tl.to(b, { y: -60 - R() * 140, x: (R() - .5) * 80, duration: d, ease: "none" }, t); }
    const P2 = mk("div", "palco", mv);
    tl.set(el, { opacity: 1 }, t); if (ant) tl.set(ant, { opacity: 0 }, t);
    tl.fromTo(mv, { scale: 1, rotation: 0 }, { scale: c.zoom || 1.07, rotation: (i % 2 ? .8 : -.8), duration: d, ease: "none" }, t);
    (TIPOS[c.tipo || "palavra"] || TIPOS.palavra)(c, P2, t, d, el);
    if (i > 0) transicao(c.transicao || ROD[i % ROD.length], ant, el, t);
    if (c.flash) tl.fromTo("#flash", { opacity: .6 }, { opacity: 0, duration: .12 }, t);
    ant = el; t += d;
  });
  window.__timelines = window.__timelines || {}; window.__timelines["kinetic"] = tl;
})();
