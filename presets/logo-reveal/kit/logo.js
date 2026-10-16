// Preset LOGO REVEAL: abertura de marca de 5-8 s com acabamento premium. Três estilos:
//   luz     um fio de luz se abre no centro e revela o logo de dentro para fora, com contraluz e brilho atravessando
//   linhas  fios finos entram das bordas e desenham a moldura do logo; o logo assenta e os fios se afastam
//   pontos  pontos girando se juntam no desenho do logo (amostrado pelo gerar.py) e o logo nítido assenta por cima
// Depois: nome e frase sobem por máscara. Timeline GSAP pausada e determinística. Campos: ver gerar.py.
(async function () {
  const P = window.PLANO, W = P.w, H = P.h, VERT = H > W, M = P.marca || {};
  try { await Promise.all([document.fonts.load("700 120px 'Inter Tight'"), document.fonts.load("500 40px 'Inter Tight'"),
    document.fonts.load("120px 'Instrument Serif'")]); await document.fonts.ready; } catch (e) {}
  const root = document.getElementById("root"), palco = document.getElementById("palco");
  root.style.setProperty("--cor", P.cor || "#C4A34F"); root.style.setProperty("--cor2", P.cor2 || "#F2E2B3");
  root.classList.add("letra-" + (P.letra || "apple"));
  const U = Math.min(W, H) / 1080, px = v => Math.round(v * U) + "px";
  const tl = gsap.timeline({ paused: true }), REVELA = "expo.out", dur = P.dur || 6, estilo = P.estilo || "luz";
  const mk = (tag, cls, pai, css) => { const e = document.createElement(tag); if (cls) e.className = cls; if (css) Object.assign(e.style, css); if (pai) pai.appendChild(e); return e; };
  const aparece = (el, t0, d = .9) => tl.fromTo(el, { opacity: 0, y: px(20), filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: d, ease: REVELA }, t0);

  // Caixa do logo: largo (wordmark) ocupa ~66% da largura; quadrado ~36%.
  const prop = M.logoProp || 1, largo = prop < .75, lw = (P.tamLogo || (largo ? 720 : 460)) * U, lh = largo ? lw * prop : lw;
  const cy = H * (VERT ? .44 : .45), x0 = (W - lw) / 2, y0 = cy - lh / 2;
  const caixa = mk("div", "logo-caixa", palco, { left: x0 + "px", top: y0 + "px", width: lw + "px", height: lh + "px" });
  const luz = mk("div", "contraluz", caixa);
  let lg;
  if (M.logo) { lg = mk("img", "logo-img", caixa); lg.src = M.logo; }
  else { lg = mk("div", "monograma", caixa, { fontSize: lw * .5 + "px" }); lg.textContent = (M.nome || "?").trim()[0].toUpperCase(); }
  let brilho = null;
  if (M.logo) brilho = mk("div", "brilho", caixa, { webkitMaskImage: `url(${M.logo})`, maskImage: `url(${M.logo})`, webkitMaskSize: "contain", maskSize: "contain",
    webkitMaskRepeat: "no-repeat", maskRepeat: "no-repeat", webkitMaskPosition: "center", maskPosition: "center" });
  let fim = 2.2;   // quando o logo está assentado (nome e frase entram depois)

  if (estilo === "linhas") {
    const m = 34 * U, f = 1.5 * U, fios = [
      [{ left: 0, top: y0 - m + "px", width: W + "px", height: f + "px" }, "scaleX", "0% 50%", { y: -50 * U }],
      [{ left: 0, top: y0 + lh + m + "px", width: W + "px", height: f + "px" }, "scaleX", "100% 50%", { y: 50 * U }],
      [{ left: x0 - m + "px", top: 0, width: f + "px", height: H + "px" }, "scaleY", "50% 100%", { x: -50 * U }],
      [{ left: x0 + lw + m + "px", top: 0, width: f + "px", height: H + "px" }, "scaleY", "50% 0%", { x: 50 * U }]];
    fios.forEach(([css, eixo, origem, sai], i) => { const el = mk("div", "fio", palco, css);
      tl.fromTo(el, { [eixo]: 0, transformOrigin: origem }, { [eixo]: 1, duration: 1.1, ease: "power3.inOut" }, .15 + i * .12);
      tl.to(el, { ...sai, opacity: 0, duration: .9, ease: "power2.in" }, 1.7); });
    tl.fromTo(lg, { opacity: 0, scale: 1.1, filter: "blur(16px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 1.4, ease: REVELA }, 1.3);
    tl.fromTo(luz, { opacity: 0 }, { opacity: 1, duration: 1.4 }, 1.3);
    fim = 2.4;
  } else if (estilo === "pontos" && (P.pontosLogo || []).length) {
    const cv = document.getElementById("pontos");
    const alvos = P.pontosLogo.map(([a, b]) => [x0 + a * lw, y0 + b * lh]);
    const pt = new window.Particulas(cv, W, H, alvos, { cor: P.cor || "#C4A34F", n: P.pontos || 4800, semente: 5, cx: W / 2, cy, fracCor: .35 });
    const J0 = .4, JD = 2.2, NIT = J0 + JD - .1, rel = { t: 0 };
    tl.to(rel, { t: dur, duration: dur, ease: "none", onUpdate: () => pt.render(rel.t, { junta: [J0, JD], apaga: rel.t > NIT ? Math.max(.3, 1 - (rel.t - NIT) / .8 * .7) : 1 }) }, 0);
    tl.fromTo(lg, { opacity: 0, filter: "blur(14px)", scale: 1.03 }, { opacity: 1, filter: "blur(0px)", scale: 1, duration: 1.2, ease: REVELA }, NIT);
    tl.fromTo(luz, { opacity: 0 }, { opacity: 1, duration: 1.2 }, NIT);
    fim = NIT + .6;
  } else {   // luz
    const r = mk("div", "risco", palco, { left: (W - lw * 1.4) / 2 + "px", width: lw * 1.4 + "px", top: cy + "px", height: Math.max(2, 3 * U) + "px" });
    tl.fromTo(r, { scaleX: 0, opacity: 0 }, { scaleX: 1, opacity: 1, duration: 1.0, ease: REVELA }, .2);
    tl.to(r, { scaleX: 1.6, opacity: 0, duration: 1.0, ease: "power2.out" }, 1.0);
    tl.fromTo(lg, { clipPath: "inset(50% 0% 50% 0%)", filter: "blur(6px) brightness(2)" },
      { clipPath: "inset(0% 0% 0% 0%)", filter: "blur(0px) brightness(1)", duration: 1.3, ease: REVELA }, .85);
    tl.fromTo(luz, { opacity: 0, scale: .5 }, { opacity: 1, scale: 1, duration: 1.6, ease: "power2.out" }, .8);
  }
  if (brilho) tl.fromTo(brilho, { backgroundPosition: "120% 0" }, { backgroundPosition: "-20% 0", duration: 1.4, ease: "power2.inOut" }, fim - .2);
  // Nome (quando o logo não traz o nome escrito) e frase.
  let yTexto = y0 + lh + 70 * U;
  if (P.nome) { const n = mk("div", "titulo nome", palco, { fontSize: px(P.tamNome || 104), top: yTexto + "px" });
    const L = mk("span", "linha", n), d = mk("span", "", L); d.textContent = P.nome;
    tl.fromTo(d, { yPercent: 115, opacity: 0 }, { yPercent: 0, opacity: 1, duration: 1.1, ease: REVELA }, fim + .1); yTexto += (P.tamNome || 104) * U * 1.15; }
  if (P.frase) { const f = mk("div", "sub legenda", palco, { fontSize: px(VERT ? 44 : 36), top: yTexto + 10 * U + "px" }); f.textContent = P.frase; aparece(f, fim + .45); }
  tl.fromTo("#cam", { scale: 1.05 }, { scale: 1, duration: dur, ease: "power2.out" }, 0);
  tl.set({}, {}, dur);
  window.__timelines = window.__timelines || {}; window.__timelines["logo"] = tl;
})();
