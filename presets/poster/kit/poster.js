// Preset POSTER: pôster editorial em movimento. Cada cena = um pôster (fundo claro com vinheta ou preto), recorte P&B,
// forma vermelha chapada, microtipografia e texto palavra a palavra. Timeline GSAP pausada e determinística
// (HyperFrames renderiza quadro a quadro). Campos do plano: ver gerar.py.
(async function () {
  try { await Promise.all([document.fonts.load("500 46px 'Inter Tight'"), document.fonts.load("800 120px 'Inter Tight'")]); await document.fonts.ready; } catch (e) {}
  const P = window.PLANO, T = P.tema, W = P.w, H = P.h, CX = W / 2, CY = H / 2;
  const root = document.getElementById("root"), box = document.getElementById("cenas");
  for (const k of ["claro", "borda", "escuro", "tinta", "branco", "acento", "acento2"]) root.style.setProperty("--" + k, T[k]);
  let s = P.semente || 11; const R = () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const tl = gsap.timeline({ paused: true });
  const mk = (tag, cls, pai, css, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (css) Object.assign(e.style, css); if (html != null) e.innerHTML = html; if (pai) pai.appendChild(e); return e; };
  const px = v => v + "px";
  const M = T.micro || {};

  // ---------- câmera sempre viva ----------
  const AMP = { lenta: .6, media: 1, rapida: 1.7 };
  function camera(cam, c, S) {
    const a = AMP[c.ritmo || "media"] || 1, de = { scale: 1, x: 0, y: 0, rotation: 0 }, ate = { scale: 1, x: 0, y: 0, rotation: 0 };
    for (const m of c.camera) {
      if (m === "afasta") { de.scale += .11 * a; }
      if (m === "aproxima") { ate.scale += .11 * a; }
      if (m === "direita") { de.x += 34 * a; ate.x -= 34 * a; }
      if (m === "esquerda") { de.x -= 34 * a; ate.x += 34 * a; }
      if (m === "sobe") { de.y += 34 * a; ate.y -= 34 * a; }
      if (m === "desce") { de.y -= 34 * a; ate.y += 34 * a; }
      if (m === "gira") { de.rotation -= 2.2 * a; ate.rotation += 1.4 * a; }
    }
    tl.fromTo(cam, de, { ...ate, duration: c.dur, ease: c.ritmo === "rapida" ? "power2.out" : "sine.inOut" }, S);
    return de;
  }

  // ---------- pedaços ----------
  function forma(pai, f, S, claro) {
    const x = CX + (f.x || 0), y = CY + (f.y || 0);
    if (f.tipo === "disco") {
      const r = f.raio || 330;
      if (f.orbita !== false) {
        const o = mk("div", "orbita", pai, { left: px(x - r * 1.22), top: px(y - r * 1.22), width: px(r * 2.44), height: px(r * 2.44) });
        tl.fromTo(o, { rotation: -20, opacity: 0 }, { rotation: 25, opacity: .85, duration: 3.2, ease: "none" }, S);
        const p = mk("div", "ponto", pai, { left: px(x + r * .78 - 26), top: px(y + r * 1.02 - 26), width: "52px", height: "52px" });
        tl.fromTo(p, { scale: 0 }, { scale: 1, duration: .3, ease: "back.out(2)" }, S + .2);
      }
      const d = mk("div", "abs disco", pai, { left: px(x - r), top: px(y - r), width: px(2 * r), height: px(2 * r) });
      tl.fromTo(d, { scale: .82, opacity: .3 }, { scale: 1, opacity: 1, duration: .38, ease: "expo.out" }, S);
    } else if (f.tipo === "quadro") {
      const w = f.larg || 420, h = f.alt || 540;
      const fr = mk("div", "quadro-moldura", pai, { left: px(x - w / 2 - 34), top: px(y - h / 2 - 34), width: px(w + 68), height: px(h + 68) });
      const q = mk("div", "quadro", pai, { left: px(x - w / 2), top: px(y - h / 2), width: px(w), height: px(h) });
      tl.fromTo(fr, { clipPath: "inset(0 100% 100% 0)" }, { clipPath: "inset(0 0% 0% 0)", duration: .45, ease: "power3.out" }, S);
      tl.fromTo(q, { clipPath: "inset(100% 0 0 0)" }, { clipPath: "inset(0% 0 0 0)", duration: .36, ease: "expo.out" }, S + .04);
    } else if (f.tipo === "pedestal") {
      const w = f.larg || 300, h = f.alt || 900, topo = 46;
      mk("div", "ped-topo", pai, { left: px(x - w / 2 - 6), top: px(y), width: px(w + 12), height: px(topo) });
      mk("div", "ped-corpo", pai, { left: px(x - w / 2), top: px(y + topo), width: px(w), height: px(h) });
    }
  }

  function foto(pai, f, c, S) {
    let x = CX + (f.x || 0), y = CY + (f.y || 0);
    if (c.forma && c.forma.tipo === "pedestal" && f.y == null) y = CY + (c.forma.y || 0) + 22 - f.h / 2;
    const e = mk("div", "foto", pai, { left: px(x - f.w / 2), top: px(y - f.h / 2), width: px(f.w), height: px(f.h), zIndex: f.frente ? 6 : 3 });
    mk("img", "", e).src = f.src;
    const par = (c.camera.includes("direita") ? -1 : c.camera.includes("esquerda") ? 1 : 0) * 26;
    tl.fromTo(e, { y: 34, x: -par, opacity: S === 0 ? .55 : 0, rotation: (f.rot || 0) - .8 }, { y: 0, x: 0, opacity: 1, rotation: f.rot || 0, duration: .34, ease: "power3.out" }, S);
    tl.to(e, { x: par, scale: 1.035, duration: c.dur - .34, ease: "sine.inOut" }, S + .34);   // paralaxe: o assunto anda mais que o fundo
  }

  function texto(pai, t, c, S) {
    const e = mk("div", "texto" + (t.alinhar === "esquerda" ? " esq" : "") + (t.cor === "branco" ? " branco" : ""), pai, { left: px(CX + (t.x || 0) - 450), top: px(CY + (t.y || 0)), zIndex: 8 });
    const gi = t.grande == null ? t.linhas.length - 1 : t.grande;
    const ws = [];
    t.linhas.forEach((ln, i) => {
      const L = mk("div", "linha " + (i === gi ? "gde" : "peq"), e);
      ln.split(" ").forEach((w, j, arr) => ws.push(mk("span", "w", L, null, w + (j < arr.length - 1 ? " " : ""))));
      if (i === gi) { L.style.display = "inline-block"; const lw = L.getBoundingClientRect().width; if (lw > 900) L.style.fontSize = px(120 * 900 / lw); L.style.display = ""; }
    });
    const passo = (t.ate - t.em) / Math.max(1, ws.length);
    tl.set(ws, { opacity: 0 }, 0);
    ws.forEach((w, k) => {
      const q = S + t.em + k * passo;
      tl.fromTo(w, { opacity: .22, filter: "blur(7px)", y: 8 }, { opacity: .22, filter: "blur(7px)", y: 8, duration: .001, immediateRender: false }, q);
      tl.to(w, { opacity: 1, filter: "blur(0px)", y: 0, duration: .24, ease: "power2.out" }, q + Math.min(.16, passo * .8));
    });
  }

  function gigante(pai, g, c, S, claro) {
    const n = g.linhas || 1;
    for (let i = 0; i < n; i++) {
      const e = mk("div", "gigante", pai, { top: px(CY + (g.y || 520) + i * 430 - 260), zIndex: g.frente ? 7 : 2,
        filter: g.frente ? "blur(8px)" : (claro ? "blur(2px)" : "none"), opacity: claro ? .92 : 1 }, (g.texto + " ").repeat(3));
      const dir = i % 2 ? 1 : -1, x0 = i % 2 ? -W * 1.1 : W * .05;
      tl.fromTo(e, { x: x0 }, { x: x0 + dir * W * (.55 + .1 * i), duration: c.dur, ease: "none" }, S);
    }
  }

  function micro(pai, c, claro) {
    const topo = mk("div", "micro", pai, { left: "70px", top: "64px" }, (M.topo || []).join("<br>") + (claro ? "<br><br>" + (M.marca || []).map(x => `<b>${x}</b>`).join("") : ""));
    if (claro) {
      mk("div", "num", pai, { right: "70px", top: "70px", color: T.tinta }, M.numero || "1");
      mk("div", "micro", pai, { left: "70px", top: px(H * .37) }, (M.lado || []).join("<br>"));
      mk("div", "micro", pai, { right: "70px", top: "150px", textAlign: "right" }, (M.rodape || [])[0] || "");
      const rod = mk("div", "micro", pai, { left: "70px", right: "70px", bottom: "120px", display: "flex", justifyContent: "space-between" }, (M.rodape || []).map(x => `<span>${x}</span>`).join(""));
      mk("div", "fio", pai, { left: "70px", right: "70px", bottom: "150px", color: T.tinta });
      const b = mk("div", "barras", pai, { right: "92px", bottom: "190px" });
      for (let i = 0; i < 26; i++) mk("i", "", b, { width: px(1 + Math.floor(R() * 4)) });
      const q = mk("div", "qr", pai, { right: "86px", top: px(H * .40) });
      for (let i = 0; i < 49; i++) { const r = Math.floor(i / 7), k = i % 7, ancora = (r < 2 && k < 2) || (r < 2 && k > 4) || (r > 4 && k < 2); mk("i", ancora || R() > .45 ? "" : "v", q); }
    } else {
      mk("div", "pontos3", pai, { right: "70px", top: "50px" }, "•••");
      mk("div", "fio", pai, { right: "130px", top: "70px", width: "300px", color: T.branco });
    }
  }

  function hud(pai, S) {
    const a = mk("div", "canto", pai, { right: "60px", top: "120px", width: "220px", height: "240px", borderTopWidth: "2px", borderRightWidth: "2px" });
    const b = mk("div", "canto", pai, { left: "60px", bottom: "330px", width: "200px", height: "220px", borderBottomWidth: "2px", borderLeftWidth: "2px" });
    const ch = mk("div", "chip", pai, { left: px(CX - 90), top: "100px" }, `<div class="globo"></div><div>${M.chip || ""}<br><span class="tag">${M.numero || "01"} ▸</span></div>`);
    tl.fromTo([a, b], { scale: .9, opacity: 0 }, { scale: 1, opacity: .9, duration: .3, ease: "power3.out", stagger: .06 }, S + .05);
    tl.fromTo(ch, { y: -16, opacity: 0 }, { y: 0, opacity: 1, duration: .3, ease: "power3.out" }, S + .1);
  }

  function quadradinhos(pai, S) {   // 2 quadradinhos brancos piscando no corte (tique de pôster digital)
    for (let i = 0; i < 2; i++) {
      const q = mk("div", "quad-branco", pai, { left: px(CX - 260 + R() * 520), top: px(CY - 260 + R() * 520), width: "46px", height: "46px", opacity: 0, zIndex: 9 });
      tl.set(q, { opacity: 1 }, S + .03 + i * .1); tl.set(q, { opacity: 0 }, S + .03 + i * .1 + .1);
    }
  }

  // ---------- cenas ----------
  P.cenas.forEach((c, k) => {
    const claro = c.fundo !== "escuro", S = c.S;
    const cena = mk("div", "cena " + (claro ? "claro" : "escuro"), box);
    mk("div", "fundo", cena);
    const cam = mk("div", "cam", cena);
    tl.set(cena, { visibility: "visible" }, S); tl.set(cena, { visibility: "hidden" }, S + c.dur);
    if (c.fecho) {
      const b = mk("div", "marca b", cam, { top: px(CY - 40) }, c.fecho), l = mk("div", "marca l", cam, { top: px(CY - 40), opacity: 0 }, c.fecho);
      tl.fromTo(cam, { scale: 1.16 }, { scale: 1, duration: c.dur, ease: "power2.out" }, S);
      tl.fromTo(b, { opacity: 0, filter: "blur(10px)" }, { opacity: 1, filter: "blur(0px)", duration: .2, ease: "power2.out" }, S);
      tl.to(b, { opacity: 0, duration: .16 }, S + .34); tl.to(l, { opacity: 1, duration: .16 }, S + .34);
      return;
    }
    if (claro && c.grade) {
      mk("div", "grade-o", cam, { left: "60px", right: "60px", top: px(H * .08), height: px(H * .42) });
      mk("div", "grade-o", cam, { left: "60px", right: "60px", top: px(H * .55), height: px(H * .42) });
    }
    if (c.micro !== false) micro(cam, c, claro);
    if (c.gigante && !c.gigante.frente) gigante(cam, c.gigante, c, S, claro);
    if (c.forma) forma(cam, c.forma, S, claro);
    if (c.foto) foto(cam, c.foto, c, S);
    if (c.gigante && c.gigante.frente) gigante(cam, c.gigante, c, S, claro);
    if (claro && (c.forma || {}).tipo === "disco") mk("div", "x", cam, { right: "120px", top: px(H * .25) });
    if (c.texto) texto(cam, c.texto, c, S);
    if (c.hud) hud(cena, S);
    if (k > 0 && claro) quadradinhos(cena, S);
    camera(cam, c, S);
  });

  window.__timelines = window.__timelines || {}; window.__timelines["poster"] = tl;
})();
