// Preset CARTÕES: cada cartão de prova (número, depoimento, print/foto) entra pela frente com um pop que assenta em
// perspectiva; os anteriores recuam (menores, mais escuros, um pouco acima). No máximo 4 visíveis; o resto sai pelo
// fundo. No fim, opcional, a pilha inteira volta e se abre em leque ou grade. Timeline GSAP pausada: determinístico.
(async function () {
  const P = window.PLANO, W = P.w, H = P.h, dur = P.dur || 12;
  try { await Promise.all(["500 40px", "600 56px", "700 68px", "800 200px"].map(f => document.fonts.load(f + " 'Inter Tight'"))); await document.fonts.ready; } catch (e) {}
  const root = document.getElementById("root"), palco = document.getElementById("palco");
  const U = Math.min(W, H) / 1080;
  root.style.setProperty("--cor", P.cor || "#FF8B3D"); root.style.setProperty("--u", U + "px");
  if (P.fundo === "transparente") root.classList.add("sem-fundo");
  const LW = Math.min(780 * U, W * .74), LH = 540 * U, cy = H * .43;
  const tl = gsap.timeline({ paused: true });
  // Chegada com overshoot pequeno (passa ~3% e assenta). Função própria, sem curvas de quique.
  const assenta = p => { const s = 1.0, q = p - 1; return q * q * ((s + 1) * q + s) + 1; };
  const mk = (tag, cls, pai, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; if (pai) pai.appendChild(e); return e; };

  // Número que conta: separa prefixo, valor e sufixo ("+3.200", "4,9", "98%"); conta no mesmo formato.
  const contador = s => {
    const m = String(s).match(/^(\D*?)(\d[\d.,]*)(.*)$/); if (!m) return null;
    const bruto = m[2], virg = bruto.includes(","), dec = virg ? bruto.split(",")[1].length : 0;
    const v = parseFloat(bruto.replace(/\./g, "").replace(",", ".")), agrupa = /\d\.\d{3}/.test(bruto);
    if (!isFinite(v)) return null;
    return { v, txt: x => m[1] + x.toLocaleString("pt-BR", { minimumFractionDigits: dec, maximumFractionDigits: dec, useGrouping: agrupa }) + m[3] };
  };

  const lista = (P.cartoes || []).map((c, i) => Object.assign({ em: .3 + i * 2.1 }, c));
  const cards = lista.map((c, i) => {
    const tipo = ["numero", "imagem"].includes(c.tipo) ? c.tipo : "texto";
    const el = mk("div", "cartao tipo-" + tipo, palco);
    Object.assign(el.style, { width: LW + "px", height: LH + "px", top: cy + "px" });
    mk("div", "filete", el);
    const k = { c, el };
    if (tipo === "numero") {
      if (c.titulo) mk("div", "olho", el, c.titulo);
      k.num = mk("div", "num", el, String(c.numero ?? ""));
      if (c.texto) mk("div", "sub", el, c.texto);
      k.conta = contador(c.numero);
    } else if (tipo === "imagem") {
      const f = mk("div", "foto", el); if (c.imagem) { const im = mk("img", "", f); im.src = c.imagem; im.alt = ""; }
      const leg = mk("div", "leg", el); if (c.titulo) mk("b", "", leg, c.titulo); if (c.texto) mk("span", "", leg, c.texto);
    } else {
      el.insertAdjacentHTML("beforeend", '<svg viewBox="0 0 64 52"><path d="M0 52V30C0 13 8 3 24 0l3 7C18 10 14 16 14 24h12v28zm36 0V30c0-17 8-27 24-30l3 7c-9 3-13 9-13 17h12v28z"/></svg>');
      k.fala = mk("div", "fala", el, c.texto || "");
      if (c.titulo) { const a = mk("div", "autor", el); mk("i", "", a); mk("span", "", a, c.titulo); }
    }
    k.escuro = mk("div", "escuro", el);
    k.giro = i % 2 ? 2.5 : -2.5;
    return k;
  });
  await Promise.all([...palco.querySelectorAll("img")].map(im => im.decode ? im.decode().catch(() => {}) : null));
  // Ajustes de tamanho: número que não cabe na largura e depoimento longo encolhem.
  cards.forEach(k => {
    if (k.num) { const largo = k.conta ? k.conta.txt(k.conta.v) : k.num.textContent; k.num.textContent = largo;
      let fs = parseFloat(getComputedStyle(k.num).fontSize); while (k.num.scrollWidth > LW * .86 && fs > 60) { fs -= 4; k.num.style.fontSize = fs + "px"; } }
    if (k.fala) { let fs = parseFloat(getComputedStyle(k.fala).fontSize); while (k.el.scrollHeight > LH + 1 && fs > 30) { fs -= 2; k.fala.style.fontSize = fs + "px"; } }
  });

  // Profundidade na pilha: 0 = frente; 1-3 recuam; 4+ saem pelo fundo.
  const PROF = [{ y: 0, s: 1, e: 0 }, { y: -96, s: .9, e: .38 }, { y: -176, s: .81, e: .6 }, { y: -242, s: .73, e: .76 }, { y: -290, s: .66, e: .9 }];
  const estado = d => { const p = PROF[Math.min(d, 4)];
    return { y: p.y * U, scale: p.s, rotationX: d ? 4 + d : 0, rotation: 0, opacity: d >= 4 ? 0 : 1 }; };
  cards.forEach((k, i) => {
    gsap.set(k.el, { xPercent: -50, yPercent: -50, x: 0, y: 360 * U, scale: 1.1, rotationX: -12, rotation: k.giro, opacity: 0, zIndex: 10 + i, transformOrigin: "50% 40%" });
  });
  cards.forEach((k, i) => {
    const t0 = k.c.em;
    for (let j = 0; j < i; j++) {
      const d = i - j; if (d > 4) continue;
      tl.to(cards[j].el, Object.assign({ duration: .9, ease: "power3.inOut" }, estado(d)), t0 - .06);
      tl.to(cards[j].escuro, { opacity: PROF[Math.min(d, 4)].e, duration: .9, ease: "power3.inOut" }, t0 - .06);
    }
    tl.to(k.el, { opacity: 1, duration: .4, ease: "power2.out" }, t0);
    tl.to(k.el, Object.assign({ duration: 1.05, ease: assenta }, estado(0)), t0);
    // Respiro: o cartão da frente recua bem devagar até o próximo evento (nunca fica congelado).
    const prox = i + 1 < cards.length ? cards[i + 1].c.em - .06 : (P.final && P.final !== "nenhum" && cards.length > 1 ? (P.emFinal ?? t0 + 2.3) : dur);
    if (prox - (t0 + 1.05) > .3) tl.to(k.el, { scale: .975, y: -10 * U, duration: prox - (t0 + 1.05), ease: "sine.inOut" }, t0 + 1.05);
    if (k.conta) { const o = { v: 0 };
      tl.fromTo(o, { v: 0 }, { v: k.conta.v, duration: 1.4, ease: "power2.out", immediateRender: true, onUpdate: () => { k.num.textContent = k.conta.txt(o.v); } }, t0 + .15); }
  });

  // Final: a pilha toda volta e se reorganiza (leque ou grade) para o "olha quanta prova".
  const n = cards.length, final = n > 1 ? (P.final || "nenhum") : "nenhum";
  const tF = P.emFinal ?? (lista.length ? lista[n - 1].em + 2.3 : 1);
  let topoFrase = cy - 400 * U;
  if (final === "leque") {
    const s = .5, R = 800 * U, amax = Math.min(18, 6 * (n - 1)) * Math.PI / 180;
    const meio = R * (1 - Math.cos(amax)) / 2;
    cards.forEach((k, i) => { const a = n > 1 ? -amax + 2 * amax * i / (n - 1) : 0;
      k.alvo = { x: R * Math.sin(a), y: R * (1 - Math.cos(a)) - meio, scale: s, rotation: a * 180 / Math.PI, rotationX: 0, opacity: 1 }; });
    topoFrase = cy - LH * s / 2 - 230 * U;
  } else if (final === "grade") {
    const gap = 36 * U, opcao = cols => { const rows = Math.ceil(n / cols);
      return { cols, rows, s: Math.min((W * .86 - (cols - 1) * gap) / (cols * LW), (H * .56 - (rows - 1) * gap) / (rows * LH)) }; };
    const g = [opcao(2), opcao(3)].sort((a, b) => b.s - a.s)[0], cw = LW * g.s, ch = LH * g.s;
    const alturaTotal = g.rows * ch + (g.rows - 1) * gap, topo = cy - alturaTotal / 2;
    cards.forEach((k, i) => { const r = Math.floor(i / g.cols), c = i % g.cols, naLinha = Math.min(g.cols, n - r * g.cols);
      const x0 = -(naLinha * cw + (naLinha - 1) * gap) / 2 + cw / 2;
      k.alvo = { x: x0 + c * (cw + gap), y: topo + r * (ch + gap) + ch / 2 - cy, scale: g.s, rotation: 0, rotationX: 0, opacity: 1 }; });
    topoFrase = Math.max(H * .06, topo - 170 * U);
  }
  if (final !== "nenhum") {
    cards.forEach((k, i) => {
      tl.to(k.el, Object.assign({ duration: 1.3, ease: "expo.inOut" }, k.alvo), tF + i * .04);
      tl.to(k.escuro, { opacity: 0, duration: 1.0, ease: "power2.inOut" }, tF + i * .04);
    });
    if (P.frase) {
      const f = mk("div", "frase", palco); f.style.top = topoFrase + "px";
      const ls = String(P.frase).split("|").map(t => { const L = mk("span", "linha", f); return mk("span", "", L, t); });
      tl.fromTo(ls, { yPercent: 115, opacity: 0 }, { yPercent: 0, opacity: 1, duration: 1.0, ease: "expo.out", stagger: .1 }, tF + .95);
    }
  }
  tl.fromTo("#cam", { scale: 1.03 }, { scale: 1, duration: dur, ease: "sine.out" }, 0);
  tl.set({}, {}, dur);
  window.__timelines = window.__timelines || {}; window.__timelines["cartoes"] = tl;
})();
