// Preset RESPOSTAS: faixa no topo (entrevista de rua, "3 regras para..."). N espaços começam com "?" e cada um
// vira ícone + palavra no instante "em" em que a resposta é dita, com um flash leve da cor da marca. As respostas
// anteriores ficam; as seguintes seguem com "?". Tudo calculado por tempo (função desenha). Campos: ver gerar.py.
(async function () {
  const P = window.PLANO, W = P.w, H = P.h, dur = P.dur;
  const bebas = P.letra === "bebas";
  const FAM = bebas ? "'Bebas Neue'" : "'Inter Tight'", PESO = bebas ? 400 : 700;
  try { await Promise.all([document.fonts.load("700 80px 'Inter Tight'"), document.fonts.load("600 80px 'Inter Tight'"),
    document.fonts.load("300 80px 'Inter Tight'"), document.fonts.load("80px 'Bebas Neue'")]); await document.fonts.ready; } catch (e) {}
  const root = document.getElementById("root"), cam = document.getElementById("cam"), faixa = document.getElementById("faixa");
  root.style.setProperty("--cor", P.cor || "#C4A34F");
  root.classList.add("letra-" + (bebas ? "bebas" : "inter"));
  if (P.fundo === "transparente") { root.classList.add("transparente"); document.documentElement.classList.add("transparente"); }

  const S = Math.min(W / 1080, H / 1920), X = v => W / 2 + (v - 540) * S, Y = v => (v) * S + (H - 1920 * S) / 2, L = v => v * S;
  const mk = (tag, cls, pai, css) => { const e = document.createElement(tag); if (cls) e.className = cls; if (css) Object.assign(e.style, css); if (pai) pai.appendChild(e); return e; };

  const cl = v => Math.max(0, Math.min(1, v));
  const expoOut = p => p >= 1 ? 1 : 1 - Math.pow(2, -10 * p);
  const p2Out = p => 1 - (1 - p) * (1 - p), p3Out = p => 1 - Math.pow(1 - p, 3);
  const assenta = p => { const s = 1.3, q = p - 1; return q * q * ((s + 1) * q + s) + 1; };
  const seg = (t, t0, d, e) => e(cl((t - t0) / d));

  const med = document.createElement("canvas").getContext("2d");
  function ajusta(txt, maxW, maxH, maxLin, lh, maxS) {
    txt = bebas ? String(txt).toUpperCase() : String(txt);
    const pal = txt.split(/\s+/).filter(Boolean);
    for (let s = Math.floor(maxS || maxH); s >= 8; s -= 1) {
      med.font = `${PESO} ${s}px ${FAM}`;
      const larg = w => med.measureText(w).width * 1.05;
      if (pal.some(w => larg(w) > maxW)) continue;
      const lin = []; let at = "";
      pal.forEach(w => { const n = at ? at + " " + w : w; if (larg(n) <= maxW) at = n; else { lin.push(at); at = w; } });
      if (at) lin.push(at);
      if (lin.length <= maxLin && lin.length * s * lh <= maxH) return { s, lin };
    }
    return { s: 8, lin: [txt] };
  }

  const anima = [];
  let topo = 170;

  // Pergunta (opcional): linhas por máscara, "*palavra*" na cor da marca.
  if (String(P.pergunta || "").trim()) {
    const limpo = String(P.pergunta).replace(/\*/g, "");
    const pesoP = bebas ? 400 : 600; med.font = `${pesoP} 10px ${FAM}`;
    let tam = L(bebas ? 58 : 40);
    const r = (() => { for (let s = tam; s > L(20); s -= 1) { med.font = `${pesoP} ${s}px ${FAM}`; const pal = (bebas ? limpo.toUpperCase() : limpo).split(/\s+/); const lin = []; let at = "";
      pal.forEach(w => { const n = at ? at + " " + w : w; if (med.measureText(n).width * 1.04 <= L(900)) at = n; else { lin.push(at); at = w; } }); if (at) lin.push(at);
      if (lin.length <= 2) return { s, n: lin.length }; } return { s: L(20), n: 2 }; })();
    tam = r.s;
    const el = mk("div", "pergunta", cam, { top: Y(140) + "px", fontSize: tam + "px", fontFamily: FAM, padding: `0 ${L(90)}px` });
    const box = mk("span", "linha", el), d = mk("span", "", box);
    String(P.pergunta).split(/(\*[^*]+\*)/).filter(Boolean).forEach(p => { const c = /^\*.*\*$/.test(p), s = mk("span", "", d); s.textContent = c ? p.slice(1, -1) : p; if (c) s.style.color = "var(--cor)"; });
    anima.push(t => { const p = seg(t, .05, 1, expoOut); d.style.transform = `translateY(${(1 - p) * 112}%)`; d.style.opacity = cl(p * 1.6); });
    topo = 140 + (r.n * tam / S) * 1.12 + 26;
  }

  // Vagas.
  const itens = P.itens.map((it, i) => Object.assign({ i }, it));
  const N = itens.length, GAP = N >= 4 ? 16 : 22, VW = (900 - GAP * (N - 1)) / N, VH = N >= 4 ? 190 : 205;
  const tw = L(VW), th = L(VH), ehImg = s => /^(assets\/|https?:|data:)|\.(png|jpe?g|webp|svg|gif)$/i.test(String(s || ""));
  const corpos = itens.map(it => ajusta(it.rotulo || "", tw * .86, th * .3, 2, 1.05, L(N >= 4 ? 30 : 36)).s);
  const corpo = Math.min(...corpos);
  itens.forEach((it, i) => {
    const v = mk("div", "vaga", faixa, { left: X(90 + i * (VW + GAP)) + "px", top: Y(topo) + "px", width: tw + "px", height: th + "px", borderRadius: L(22) + "px" });
    const flash = mk("div", "flash", v), borda = mk("div", "borda", v, { borderRadius: L(22) + "px" });
    const num = mk("div", "num", v, { left: L(16) + "px", top: L(14) + "px", fontSize: L(bebas ? 30 : 24) + "px" }); num.textContent = i + 1;
    const q = mk("div", "q", v, { top: th * .5 - th * .29 + "px", fontSize: th * .58 + "px" }); q.textContent = "?";
    const ic = mk("div", "icone", v, { width: th * .42 + "px", height: th * .42 + "px", top: th * .12 + "px", marginLeft: -th * .21 + "px", fontSize: th * .36 + "px" });
    if (ehImg(it.icone)) mk("img", "", ic).src = it.icone; else ic.textContent = it.icone || "";
    const rot = mk("div", "rot", v, { top: th * .6 + "px", height: th * .34 + "px", display: "flex", alignItems: "center", justifyContent: "center", padding: `0 ${tw * .07}px` });
    const sp = mk("span", "", rot, { fontFamily: FAM });
    const r = ajusta(it.rotulo || "", tw * .86, th * .3, 2, 1.05, corpo);
    r.lin.forEach((l, k) => { if (k) sp.appendChild(document.createElement("br")); sp.appendChild(document.createTextNode(l)); });
    sp.style.fontSize = r.s + "px";
    const t0 = it.em - .05;
    anima.push(t => {
      const e = seg(t, .1 + i * .08, .85, expoOut);
      const k = cl((t - t0) / .5), pop = 1 + .045 * Math.sin(Math.PI * p3Out(k));
      v.style.opacity = cl(e * 1.5);
      v.style.transform = `translateY(${-(1 - e) * L(26)}px) scale(${pop})`;
      const resp = .32 + .12 * Math.sin(t * 2.6 + i * 1.7);   // "?" respira enquanto espera
      const sai = seg(t, t0, .28, p2Out);
      q.style.opacity = resp * (1 - sai); q.style.transform = `scale(${1 - .4 * sai})`; q.style.filter = `blur(${6 * sai}px)`;
      flash.style.opacity = .5 * seg(t, t0, .1, p2Out) * (1 - seg(t, t0 + .1, .8, expoOut)) + .12 * seg(t, t0 + .1, .8, expoOut);
      borda.style.opacity = seg(t, t0, .15, p2Out) * (1 - .45 * seg(t, t0 + .15, .8, expoOut));
      const a = seg(t, t0 + .08, .6, assenta);
      ic.style.opacity = seg(t, t0 + .08, .2, p2Out); ic.style.transform = `translateY(${(1 - a) * L(14) + Math.sin((t - t0) * 2.2) * L(3) * seg(t, t0 + .7, .6, p2Out)}px) scale(${.5 + .5 * a})`;
      const rr = seg(t, t0 + .18, .7, expoOut);
      sp.style.transform = `translateY(${(1 - rr) * 115}%)`; sp.style.opacity = cl(rr * 2);
    });
  });
  // "centro": true (só no exemplo/prévia, ou quando o vídeo não tem pessoa): pergunta + faixa no meio do quadro.
  if (P.centro) {
    const alt = topo + VH - 140, desloc = L((1920 - alt) / 2 - 140);
    [cam, faixa].filter(e => !(e !== cam && cam.contains(e))).forEach(e => { e.style.top = desloc + "px"; e.style.bottom = -desloc + "px"; });
    ["foco", "nevoa"].forEach(id => { const e = document.getElementById(id); if (e) e.style.marginTop = desloc + "px"; });
  }
  const nevoa = document.getElementById("nevoa");
  anima.push(t => {
    cam.style.transform = `scale(${1.02 - .02 * Math.min(1, t / dur)})`;   // câmera contínua bem lenta
    nevoa.style.transform = `translate(calc(-50% + ${Math.sin(t * .9) * L(60)}px), calc(-50% + ${Math.sin(t * .6 + 1) * L(30)}px)) scale(${1 + .12 * Math.sin(t * .7)})`;   // luz de fundo respirando
    nevoa.style.opacity = .8 + .2 * Math.sin(t * 1.1);
  });

  const tl = gsap.timeline({ paused: true }), relogio = { t: 0 };
  const desenha = () => anima.forEach(f => f(relogio.t));
  desenha();
  tl.to(relogio, { t: dur, duration: dur, ease: "none", onUpdate: desenha }, 0);
  tl.set({}, {}, dur);
  window.__timelines = window.__timelines || {}; window.__timelines["respostas"] = tl;
})();
