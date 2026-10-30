// Preset POSTER: pôster editorial em movimento. Cada cena = um pôster (fundo claro com vinheta ou preto), recorte P&B,
// forma vermelha chapada, microtipografia e texto palavra a palavra. Timeline GSAP pausada e determinística
// (HyperFrames renderiza quadro a quadro). Campos do plano: ver gerar.py.
(async function () {
  try { await Promise.all([document.fonts.load("500 46px 'Inter Tight'"), document.fonts.load("800 120px 'Inter Tight'")]); await document.fonts.ready; } catch (e) {}
  const P = window.PLANO, T = P.tema, W = P.w, H = P.h, CX = W / 2, CY = H / 2;
  const root = document.getElementById("root"), box = document.getElementById("cenas");
  for (const k of ["claro", "borda", "escuro", "tinta", "branco", "acento", "acento2"]) root.style.setProperty("--" + k, T[k]);
  if (T.acento_texto) root.style.setProperty("--acento-texto", T.acento_texto);   // texto sobre a cor da marca (dourado pede escuro)
  if (T.fonte && T.fonte !== "Inter Tight") root.style.setProperty("--fonte", `"${T.fonte}"`);   // fontes da marca (tema)
  if (T.fonte_gde) root.style.setProperty("--fonte-gde", `"${T.fonte_gde}"`);
  if (T.track_gde != null) root.style.setProperty("--track-gde", T.track_gde + "em");
  if (T.tam_gde) root.style.setProperty("--tam-gde", T.tam_gde + "px");
  try { await Promise.all([T.fonte, T.fonte_gde].filter(Boolean).map(f => document.fonts.load(`800 120px "${f}"`))); await document.fonts.ready; } catch (e) {}
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
      if (i === gi) { L.style.display = "inline-block"; const lw = L.getBoundingClientRect().width; if (lw > 900) L.style.fontSize = px((T.tam_gde || 120) * 900 / lw); L.style.display = ""; }
    });
    const passo = (t.ate - t.em) / Math.max(1, ws.length);
    tl.set(ws, { opacity: 0 }, 0);
    ws.forEach((w, k) => {
      if (t.tempos && t.tempos[k] != null) {   // palavra presa à fala: acende no instante em que é dita
        const q = S + t.tempos[k];
        tl.fromTo(w, { opacity: .22, filter: "blur(7px)", y: 8 }, { opacity: .22, filter: "blur(7px)", y: 8, duration: .001, immediateRender: false }, Math.max(S, q - .2));
        tl.to(w, { opacity: 1, filter: "blur(0px)", y: 0, duration: .2, ease: "power2.out" }, Math.max(S, q - .06));
        return;
      }
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

  // ---------- velas (candles) que nascem uma a uma: mercado subindo, caindo ou volátil ----------
  function velas(pai, v, c, S, claro) {
    const n = v.n || 12, w = v.larg || 780, h = v.alt || 640, x0 = CX - w / 2 + (v.x || 0), y0 = CY + (v.y || 150) - h / 2;
    const caixa = mk("div", "velas", pai, { left: px(x0), top: px(y0), width: px(w), height: px(h), zIndex: 4 });
    for (let i = 1; i < 4; i++) mk("div", "velas-grade", caixa, { top: px(h * i / 4) });
    const modo = v.modo || "volatil";
    let p = .5; const pts = [];
    for (let i = 0; i < n; i++) {   // série determinística (semente do plano): sobe, cai ou balança forte
      const tend = modo === "sobe" ? .045 : modo === "cai" ? -.045 : modo === "lateral" ? 0 : (i % 4 < 2 ? .13 : -.13);
      const ab = p, fe = Math.min(.9, Math.max(.1, p + tend + (R() - .5) * (modo === "volatil" ? .22 : .1)));
      pts.push([ab, fe, Math.max(ab, fe) + R() * .08, Math.min(ab, fe) - R() * .08]); p = fe;
    }
    const lo0 = Math.min(...pts.map(x => x[3])), hi0 = Math.max(...pts.map(x => x[2]));   // usa a altura toda da caixa
    pts.forEach(x => x.forEach((y, i) => { x[i] = .04 + .92 * (y - lo0) / Math.max(.01, hi0 - lo0); }));
    const cw = w / n, ini = S + (v.em ?? .3), passo = ((v.ate ?? c.dur * .75) - (v.em ?? .3)) / n;
    pts.forEach(([ab, fe, hi, lo], i) => {
      const alta = fe >= ab, top = h * (1 - Math.max(ab, fe)), alt = Math.max(10, h * Math.abs(fe - ab));
      const g = mk("div", "vela " + (alta ? "alta" : "baixa"), caixa, { left: px(i * cw + cw * .2), width: px(cw * .6), top: "0", height: px(h) });
      mk("i", "pavio", g, { top: px(h * (1 - hi)), height: px(h * (hi - lo)) });
      const corpo = mk("b", "corpo", g, { top: px(top), height: px(alt) });
      const q = ini + i * passo;
      tl.fromTo(g, { opacity: 0 }, { opacity: 1, duration: .08 }, q);
      tl.fromTo(corpo, { scaleY: 0, transformOrigin: alta ? "50% 100%" : "50% 0%" }, { scaleY: 1, duration: .28, ease: "back.out(2.2)" }, q);
    });
    if (v.linha !== false) {   // linha do preço passando pelos fechamentos (desenha junto)
      const ns = "http://www.w3.org/2000/svg", svg = document.createElementNS(ns, "svg");
      svg.setAttribute("width", w); svg.setAttribute("height", h); svg.setAttribute("class", "velas-linha"); caixa.appendChild(svg);
      const path = document.createElementNS(ns, "path");
      path.setAttribute("d", pts.map(([, fe], i) => (i ? "L" : "M") + (i * cw + cw / 2).toFixed(1) + " " + (h * (1 - fe)).toFixed(1)).join(" "));
      svg.appendChild(path); const L = path.getTotalLength();
      tl.fromTo(path, { strokeDasharray: L, strokeDashoffset: L }, { strokeDashoffset: 0, duration: passo * n + .2, ease: "none" }, ini);
    }
  }

  // ---------- celular 3D com o perfil do Instagram (CTA de seguir): o dedo toca em Seguir e vira Seguindo ----------
  function celular(pai, k, c, S) {
    const p = k.perfil || {}, w = k.larg || 600, h = Math.round(w * 2.05), x = CX + (k.x || 0), y = CY + (k.y || 170);
    const palco = mk("div", "cel-palco", pai, { left: px(x - w / 2), top: px(y - h / 2), width: px(w), height: px(h), zIndex: 5 });
    const cel = mk("div", "cel", palco);
    mk("div", "cel-lado", cel);
    const tela = mk("div", "cel-tela", cel);
    mk("div", "cel-ilha", tela);
    const n = v => `<b>${v}</b>`;
    const ig = mk("div", "ig", tela, null,
      `<div class="bar"><span>9:41</span><span>▮▮▮ ◔ ▬</span></div>` +
      `<div class="user"><span>${p.user || ""} ⌄</span><span>⊕ ≡</span></div>` +
      `<div class="topo"><div class="anel"><img src="${p.foto || ""}"></div><div class="nums">` +
      `<div>${n(p.posts ?? "")}<span>posts</span></div><div>${n(p.seguidores ?? "")}<span>seguidores</span></div><div>${n(p.seguindo ?? "")}<span>seguindo</span></div></div></div>` +
      `<div class="nome">${p.nome || ""}</div><div class="bio">${(p.bio || []).join("<br>")}</div><div class="link">🔗 ${p.link || ""}</div>` +
      `<div class="botoes"><div class="bt seguir">Seguir<div class="seguindo">Seguindo ⌄</div></div><div class="bt">Mensagem</div><div class="bt" style="flex:none;width:58px">⌄</div></div>` +
      `<div class="dest">${(p.destaques || []).slice(0, 4).map((d, i) => `<div><i style="background-image:url('${(p.capas || [])[i] || ""}')"></i>${d}</div>`).join("")}</div>` +
      `<div class="abas"><b>▦</b><span>▷</span><span>◫</span></div>` +
      `<div class="grade">${(p.capas || []).slice(0, 9).map(u => `<i style="background-image:url('${u}')"></i>`).join("")}</div>`);
    mk("div", "cel-reflexo", tela);
    // entrada 3D: vem inclinado de baixo e assenta quase de frente, sempre girando um pouco (câmera viva)
    tl.fromTo(cel, { rotationY: -32, rotationX: 14, y: 260, z: -200, opacity: S === 0 ? 1 : 0 },
      { rotationY: -9, rotationX: 5, y: 0, z: 0, opacity: 1, duration: .7, ease: "expo.out" }, S);
    tl.to(cel, { rotationY: 7, rotationX: 2, duration: c.dur - .7, ease: "sine.inOut" }, S + .7);
    // o dedo: o alvo é o botão Seguir, dentro da tela (gira junto com o celular)
    const bt = tela.querySelector(".bt.seguir"), sg = bt.querySelector(".seguindo");
    const bx = bt.offsetLeft + ig.offsetLeft + bt.offsetWidth * .5, by = bt.offsetTop + ig.offsetTop + bt.offsetHeight * .5;
    const dedo = mk("div", "dedo", tela, { left: px(bx - 48), top: px(by - 30) }, `<div class="ponta"></div><div class="unha"></div>`);
    const toque = mk("div", "toque", tela, { left: px(bx - 55), top: px(by - 55) });
    const em = k.em ?? 1.4;
    tl.fromTo(dedo, { x: 260, y: 520, rotation: -18, opacity: 0 }, { x: 0, y: 0, rotation: -8, opacity: 1, duration: .5, ease: "power3.out" }, S + em - .55);
    tl.to(dedo, { scale: .9, y: 8, duration: .08, ease: "power2.in" }, S + em - .05);
    tl.to(bt, { scale: .95, duration: .08, ease: "power2.in" }, S + em - .05);
    tl.set(sg, { opacity: 1 }, S + em + .03);
    tl.to([dedo, bt], { scale: 1, y: 0, duration: .18, ease: "back.out(3)" }, S + em + .03);
    tl.fromTo(toque, { scale: .3, opacity: 1 }, { scale: 2.2, opacity: 0, duration: .55, ease: "power2.out" }, S + em + .03);
    tl.to(dedo, { x: 300, y: 560, rotation: -22, opacity: 0, duration: .5, ease: "power2.in" }, S + em + .5);
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
    if (c.celular) celular(cam, c.celular, c, S);
    if (c.velas) velas(cam, c.velas, c, S, claro);
    if (c.gigante && c.gigante.frente) gigante(cam, c.gigante, c, S, claro);
    if (claro && (c.forma || {}).tipo === "disco") mk("div", "x", cam, { right: "96px", top: px(H * .32) });   // abaixo da faixa do texto (texto é intocável)
    if (c.texto) texto(cam, c.texto, c, S);
    if (c.hud) hud(cena, S);
    if (k > 0 && claro) quadradinhos(cena, S);
    camera(cam, c, S);
  });

  window.__timelines = window.__timelines || {}; window.__timelines["poster"] = tl;
})();
