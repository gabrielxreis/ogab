// Preset MARCO: pontos girando num campo escuro se juntam e formam o número do marco; o número nítido assenta por
// cima, os pontos ficam brilhando por trás, e a frase sobe embaixo. Valor exato do plano. Campos: ver gerar.py.
(async function () {
  const P = window.PLANO, W = P.w, H = P.h, VERT = H > W;
  const serif = P.letra === "cinema", fam = serif ? "'Instrument Serif'" : "'Inter Tight'", peso = serif ? 400 : 800;
  try { await Promise.all([document.fonts.load(`${peso} 300px ${fam}`), document.fonts.load("700 120px 'Inter Tight'"),
    document.fonts.load("500 40px 'Inter Tight'"), document.fonts.load("120px 'Instrument Serif'")]); await document.fonts.ready; } catch (e) {}
  const root = document.getElementById("root"), palco = document.getElementById("palco");
  root.style.setProperty("--cor", P.cor || "#C4A34F"); root.style.setProperty("--cor2", P.cor2 || "#F2E2B3");
  root.classList.add("letra-" + (P.letra || "apple"));
  const U = Math.min(W, H) / 1080, px = v => Math.round(v * U) + "px";
  const tl = gsap.timeline({ paused: true }), REVELA = "expo.out", dur = P.dur || 6;
  const mk = (tag, cls, pai, css) => { const e = document.createElement(tag); if (cls) e.className = cls; if (css) Object.assign(e.style, css); if (pai) pai.appendChild(e); return e; };
  const aparece = (el, t0, d = .9) => tl.fromTo(el, { opacity: 0, y: px(20), filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: d, ease: REVELA }, t0);

  // Tamanho do número: o maior que cabe em 80% da largura (máx. 420 px na base 1080).
  const num = String(P.numero), med = document.createElement("canvas").getContext("2d");
  let tam = (P.tam || 420) * U; const esp = serif ? -.015 : -.05; med.font = `${peso} ${tam}px ${fam}`; med.letterSpacing = esp * tam + "px";
  const larg = med.measureText(num).width; if (larg > W * .8) tam *= W * .8 / larg;
  // Textos primeiro (sem posição), para medir; no vertical o bloco inteiro (olho, número, texto, sub, fonte) fica
  // centrado na zona segura do Reels (y 360-1560): sub e fonte no rodapé caíam em y~1660/1770 (relato 30/10/2026).
  const n = mk("div", "numero", palco, { fontSize: tam + "px", fontWeight: peso, fontFamily: fam });
  if (P.destaqueNumero !== false) n.style.color = "var(--cor)";
  n.textContent = num;
  const o = P.olho ? mk("div", "olho legenda", palco, { fontSize: px(28) }) : null; if (o) o.textContent = P.olho;
  let t = null, ls = [];
  if (P.texto) {
    t = mk("div", "titulo legenda", palco, { fontSize: px(P.tamTexto || (VERT ? 92 : 76)) });
    ls = String(P.texto).split("|").map(ln => { const L = mk("span", "linha", t), d = mk("span", "", L);
      ln.split(/(\*[^*]+\*)/).filter(Boolean).forEach(p => { const c = /^\*.*\*$/.test(p), s = mk("span", "p" + (c ? " cor" : ""), d); s.textContent = c ? p.slice(1, -1) : p; }); return d; });
  }
  const sb = P.sub ? mk("div", "sub legenda", palco, { fontSize: px(34) }) : null; if (sb) sb.textContent = P.sub;
  const fo = P.fonte ? mk("div", "sub legenda", palco, { fontSize: px(26), opacity: .8 }) : null; if (fo) fo.textContent = P.fonte;
  // posições relativas ao centro do número (cy)
  const rel = { n: -tam * .5 }; if (o) rel.o = -tam * .5 - 110 * U;
  let fimRel = tam * .5;
  if (t) { rel.t = tam * .55 + 30 * U; fimRel = rel.t + t.offsetHeight; }
  if (VERT) {
    if (sb) { rel.sb = fimRel + 34 * U; fimRel = rel.sb + sb.offsetHeight; }
    if (fo) { rel.fo = fimRel + (sb ? 14 : 34) * U; fimRel = rel.fo + fo.offsetHeight; }
  }
  const iniRel = o ? rel.o : rel.n;
  const cy = VERT ? H * .5 - (iniRel + fimRel) / 2 : H * .45;
  for (const [k, el] of [["n", n], ["o", o], ["t", t], ["sb", sb], ["fo", fo]]) if (el && rel[k] !== undefined) el.style.top = cy + rel[k] + "px";
  if (!VERT) { if (sb) sb.style.bottom = px(90); if (fo) fo.style.bottom = px(50); }

  const alvos = window.pontosDoTexto(num, fam, tam, W / 2, cy, Math.max(3, Math.round(tam / 95)), peso, esp * tam);
  const pt = new window.Particulas(document.getElementById("pontos"), W, H, alvos, { cor: P.cor || "#C4A34F", n: P.pontos || 5200, semente: 11, cx: W / 2, cy });
  const J0 = .5, JD = 2.4, NITIDO = J0 + JD - .2;
  const relogio = { t: 0 };
  tl.to(relogio, { t: dur, duration: dur, ease: "none", onUpdate: () => pt.render(relogio.t, { junta: [J0, JD], apaga: relogio.t > NITIDO ? Math.max(.38, 1 - (relogio.t - NITIDO) / .8 * .62) : 1 }) }, 0);

  // Número nítido por cima (mesma fonte e posição que os pontos), assentando com desfoque.
  tl.fromTo(n, { opacity: 0, filter: "blur(14px)", scale: 1.04 }, { opacity: 1, filter: "blur(0px)", scale: 1, duration: 1.2, ease: REVELA }, NITIDO);
  if (o) aparece(o, .2);
  if (t) tl.fromTo(ls, { yPercent: 115, opacity: 0 }, { yPercent: 0, opacity: 1, duration: 1.1, ease: REVELA, stagger: .12 }, NITIDO + .25);
  if (sb) aparece(sb, NITIDO + .7);
  if (fo) aparece(fo, NITIDO + .9);
  tl.fromTo("#cam", { scale: 1.06 }, { scale: 1, duration: NITIDO + .8, ease: "power2.out" }, 0);
  tl.set({}, {}, dur);
  window.__timelines = window.__timelines || {}; window.__timelines["marco"] = tl;
})();
