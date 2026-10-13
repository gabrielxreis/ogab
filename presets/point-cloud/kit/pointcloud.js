// Motor do preset POINT CLOUD (Gab /ogab). Pontos migram entre alvos (foto, texto 3D, formas) com câmera 3D.
// Tudo é função do tempo t (determinístico): o HyperFrames busca qualquer quadro.
(function () {
  const D = window.PONTOS, N = D.n, W = D.w, H = D.h, C = D.cenas;
  const A = D.alvos.map(a => Float32Array.from(a));
  const FASE = Float32Array.from(D.fase), ATR = Float32Array.from(D.atraso);
  // nuvem de abertura: os pontos chegam espalhados e se juntam na 1ª figura
  const NUVEM = new Float32Array(N * 4);
  for (let i = 0; i < N; i++) { NUVEM[i*4] = (FASE[i]-.5)*3.2; NUVEM[i*4+1] = (ATR[i]-.5)*5; NUVEM[i*4+2] = (FASE[(i*7)%N]-.5)*3; NUVEM[i*4+3] = .3; }
  const S = []; let acc = 0; for (const c of C) { S.push(acc); acc += c.dur; } const DUR = acc;
  const cv = document.getElementById("cv"), cx = cv.getContext("2d");
  const ease = p => p < .5 ? 4*p*p*p : 1 - Math.pow(-2*p+2, 3)/2;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const rad = d => d * Math.PI / 180;
  const ang = (k, local) => rad(-C[k].giro/2 + C[k].giro * clamp(local / C[k].dur, 0, 1));
  const zoomDe = (k, local) => C[k].zoom[0] + (C[k].zoom[1] - C[k].zoom[0]) * clamp(local / C[k].dur, 0, 1);

  function draw(t) {
    let k = 0; while (k < C.length - 1 && t >= S[k+1]) k++;
    const local = t - S[k], tr = C[k].transicao, de = k ? A[k-1] : NUVEM, para = A[k];
    const g = ease(clamp(local / tr, 0, 1));
    const aPrev = k ? ang(k-1, C[k-1].dur) : ang(0, 0);
    const a = aPrev + (ang(k, local) - aPrev) * g;
    const tilt = rad((k ? C[k-1].inclinacao : C[0].inclinacao) + (C[k].inclinacao - (k ? C[k-1].inclinacao : C[0].inclinacao)) * g);
    const zm = (k ? zoomDe(k-1, C[k-1].dur) : C[0].zoom[0]) * (1-g) + zoomDe(k, local) * g;
    const ca = Math.cos(a), sa = Math.sin(a), ct = Math.cos(tilt), st = Math.sin(tilt);
    const f = 2.6, esc = W * D.largura / 2 * zm, cxp = W / 2, cyp = D.cy;
    cx.fillStyle = D.fundo; cx.fillRect(0, 0, W, H); cx.fillStyle = D.cor;
    for (let i = 0; i < N; i++) {
      const o = i * 4;
      const p = ease(clamp((local - ATR[i] * tr * .35) / (tr * .65), 0, 1));
      const sw = Math.sin(Math.PI * p), fa = FASE[i] * 6.2832;
      let x = de[o] + (para[o] - de[o]) * p + sw * .2 * Math.cos(fa) + .004 * Math.sin(t * 1.1 + fa);
      let y = de[o+1] + (para[o+1] - de[o+1]) * p + sw * .06 * Math.sin(fa * 1.7) + .004 * Math.cos(t * .9 + ATR[i] * 6.28);
      let z = de[o+2] + (para[o+2] - de[o+2]) * p + sw * .2 * Math.sin(fa);
      const b = de[o+3] + (para[o+3] - de[o+3]) * p;
      const x1 = x * ca + z * sa, z1 = -x * sa + z * ca;
      const y2 = y * ct - z1 * st, z2 = y * st + z1 * ct;
      const ps = f / (f + z2); if (ps <= 0) continue;
      const sx = cxp + x1 * esc * ps, sy = cyp + y2 * esc * ps;
      const r = (1.1 + 1.7 * b) * ps * (W / 1080);
      cx.globalAlpha = clamp((.22 + .78 * b) * clamp(1.15 - z2 * .55, .15, 1), 0, 1);
      cx.fillRect(sx - r/2, sy - r/2, r, r);
    }
    cx.globalAlpha = 1;
  }

  const tl = gsap.timeline({ paused: true }); const est = { t: 0 };
  tl.to(est, { t: DUR, duration: DUR, ease: "none", onUpdate: () => draw(est.t) }, 0); draw(0);
  const box = document.getElementById("txt");
  C.forEach((c, k) => {
    const ent = S[k] + c.transicao * .55, sai = S[k] + c.dur - .4;
    for (const [cls, html] of [["kick", c.kicker], ["tit", c.titulo], ["cred", c.credito]]) {
      if (!html) continue;
      const el = document.createElement("div"); el.className = cls; el.innerHTML = html; box.appendChild(el);
      tl.fromTo(el, { opacity: 0, y: 18, filter: "blur(10px)" }, { opacity: cls === "cred" ? .5 : (cls === "kick" ? .72 : 1), y: 0, filter: "blur(0px)", duration: .7, ease: "power3.out" }, ent + (cls === "tit" ? .15 : 0));
      tl.to(el, { opacity: 0, filter: "blur(8px)", duration: .35, ease: "power2.in" }, sai);
    }
  });
  window.__timelines = window.__timelines || {}; window.__timelines["point-cloud"] = tl;
})();
