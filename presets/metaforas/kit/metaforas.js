// Motor do preset METÁFORAS (Gab /ogab): cada frase vira uma metáfora visual (protagonista em destaque, resto em cinza).
// Estilos: destaque (v1), bolhas (v3), grade (v4/v5), objetos (v2). Tudo função de t (determinístico p/ HyperFrames).
(function () {
  const P = window.PLANO, W = P.w, H = P.h, CN = P.cenas, IC = P.icones;
  const EST = {
    destaque: { bg: "#0d0d0d", dim: "#5f5f5f", mid: "#8f8f8f", hi: "#ffffff", glow: 38, piso: null, trans: "iris" },
    bolhas:   { bg: "#151515", dim: "#4d4d4d", mid: "#7c7c7c", hi: "#f2f2f2", glow: 30, piso: null, bokeh: true, trans: "fade" },
    grade:    { bg: "#050505", dim: "#3a3a3a", mid: "#9a9a9a", hi: "#ffffff", glow: 44, piso: "grade", vidro: true, trans: "push" },
    objetos:  { bg: "#090909", dim: "#4a4a4a", mid: "#a5a5a5", hi: "#f7f7f7", glow: 34, piso: "reflexo", trans: "slide" },
  };
  const S = Object.assign({}, EST[P.estilo] || EST.destaque, P.cores || {}); S.estilo = P.estilo;
  const cv = document.getElementById("cv"), cx = cv.getContext("2d");
  const T0 = []; let acc = 0; for (const c of CN) { T0.push(acc); acc += c.dur; } const DUR = acc;
  const cl = (v, a, b) => Math.max(a, Math.min(b, v)), lerp = (a, b, p) => a + (b - a) * p;
  const eo = p => 1 - Math.pow(1 - cl(p, 0, 1), 3), eio = p => { p = cl(p, 0, 1); return p < .5 ? 4*p*p*p : 1 - Math.pow(-2*p+2, 3)/2; };
  const back = p => { p = cl(p, 0, 1); const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); };
  const rnd = (i, s = 1) => { const x = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return x - Math.floor(x); };

  // ---------- primitivas ----------
  function brilho(cor, forca) { cx.shadowColor = cor; cx.shadowBlur = forca; }
  function semBrilho() { cx.shadowBlur = 0; }
  function icone(nome, x, y, tam, cor, glow = 0, alpha = 1) {
    const cp = IC[nome]; if (!cp) return;
    cx.save(); cx.globalAlpha *= alpha; cx.fillStyle = cor; cx.font = `${tam}px Icones`; cx.textAlign = "center"; cx.textBaseline = "middle";
    if (glow) brilho(cor, glow); cx.fillText(String.fromCodePoint(parseInt(cp, 16)), x, y); cx.restore();
  }
  function bola(x, y, r, cor, glow = 0, alpha = 1, volume = false) {
    cx.save(); cx.globalAlpha *= alpha; if (glow) brilho(cor, glow);
    if (volume) { const g = cx.createRadialGradient(x - r*.35, y - r*.4, r*.1, x, y, r); g.addColorStop(0, "#ffffff"); g.addColorStop(.55, cor); g.addColorStop(1, "#2a2a2a"); cx.fillStyle = g; }
    else cx.fillStyle = cor;
    cx.beginPath(); cx.arc(x, y, Math.max(0, r), 0, Math.PI * 2); cx.fill(); cx.restore();
  }
  function retR(x, y, w, h, r, cor, modo = "fill", lw = 4, glow = 0, alpha = 1) {
    cx.save(); cx.globalAlpha *= alpha; if (glow) brilho(cor, glow);
    cx.beginPath(); cx.roundRect(x, y, w, h, r);
    if (modo === "fill") { cx.fillStyle = cor; cx.fill(); } else { cx.strokeStyle = cor; cx.lineWidth = lw; cx.stroke(); }
    cx.restore();
  }
  function vidro(x, y, w, h, alpha = 1) {  // cartão de vidro (grade)
    cx.save(); cx.globalAlpha *= alpha;
    const g = cx.createLinearGradient(x, y, x + w, y + h); g.addColorStop(0, "rgba(255,255,255,.22)"); g.addColorStop(.5, "rgba(255,255,255,.07)"); g.addColorStop(1, "rgba(255,255,255,.16)");
    cx.fillStyle = g; cx.beginPath(); cx.roundRect(x, y, w, h, 26); cx.fill();
    cx.strokeStyle = "rgba(255,255,255,.55)"; cx.lineWidth = 2.5; brilho("rgba(255,255,255,.6)", 18); cx.stroke(); cx.restore();
  }
  function blob(x, y, s, cor, olhos = true, boca = 0, braco = 0) {  // personagem-bolinha (bolhas)
    cx.save(); cx.fillStyle = cor; cx.beginPath(); cx.roundRect(x - 55*s, y - 130*s, 110*s, 260*s, 55*s); cx.fill();
    if (braco) { cx.strokeStyle = cor; cx.lineWidth = 12*s; cx.lineCap = "round"; cx.beginPath(); cx.moveTo(x + 40*s, y + 10*s); cx.lineTo(x + 100*s, y - 60*s * braco); cx.stroke(); }
    if (olhos) { cx.fillStyle = "#1b1b1b"; for (const dx of [-18, 18]) { cx.beginPath(); cx.arc(x + dx*s, y - 70*s, 7*s, 0, 7); cx.fill(); }
      cx.beginPath(); cx.ellipse(x, y - 40*s, 12*s, (6 + 8*boca)*s, 0, 0, 7); cx.fill(); }
    cx.restore();
  }
  function pessoa(x, y, tam, cor, glow = 0, alpha = 1) { S.estilo === "bolhas" ? blob(x, y, tam / 260, cor) : icone("person", x, y, tam * 1.35, cor, glow, alpha); }
  function balao(x, y, s, cor, alpha = 1) {
    cx.save(); cx.globalAlpha *= alpha; retR(x - 70*s, y - 45*s, 140*s, 90*s, 18*s, cor);
    cx.fillStyle = cor; cx.beginPath(); cx.moveTo(x - 30*s, y + 44*s); cx.lineTo(x - 50*s, y + 75*s); cx.lineTo(x - 5*s, y + 44*s); cx.fill();
    cx.fillStyle = "#1a1a1a"; for (let i = 0; i < 3; i++) cx.fillRect(x - 48*s, y - 22*s + i * 20*s, (i === 2 ? 60 : 96)*s, 8*s); cx.restore();
  }

  // ---------- fundos ----------
  function fundo(t) {
    cx.fillStyle = S.bg; cx.fillRect(0, 0, W, H);
    const v = cx.createRadialGradient(W/2, H*.45, 100, W/2, H*.45, H*.75); v.addColorStop(0, "rgba(255,255,255,.035)"); v.addColorStop(1, "rgba(0,0,0,.72)");
    cx.fillStyle = v; cx.fillRect(0, 0, W, H);
    if (S.bokeh) for (let i = 0; i < 46; i++) { const r = 20 + rnd(i) * 70, x = rnd(i, 2) * W + Math.sin(t * .3 + i) * 20, y = rnd(i, 3) * H - (t * 18 * (0.4 + rnd(i, 4))) % 200;
      bola(x, y, r, `rgba(255,255,255,${.04 + rnd(i, 5) * .1})`); }
    if (S.piso === "grade") { cx.save(); cx.strokeStyle = "rgba(255,255,255,.28)"; cx.lineWidth = 2; const hz = H * .5;
      for (let i = -14; i <= 14; i++) { cx.beginPath(); cx.moveTo(W/2 + i * 40, hz); cx.lineTo(W/2 + i * 420, H); cx.stroke(); }
      for (let j = 0; j < 16; j++) { const z = ((j + (t * 1.2) % 1) / 16); const y = hz + Math.pow(z, 2.2) * (H - hz); cx.globalAlpha = .15 + z * .8; cx.beginPath(); cx.moveTo(0, y); cx.lineTo(W, y); cx.stroke(); }
      cx.restore(); const nv = cx.createLinearGradient(0, hz - 260, 0, hz + 120); nv.addColorStop(0, S.bg); nv.addColorStop(.6, "rgba(0,0,0,0)"); cx.fillStyle = nv; cx.fillRect(0, hz - 260, W, 380); }
    if (S.piso === "reflexo") { const hz = H * .62; const g = cx.createLinearGradient(0, hz, 0, H); g.addColorStop(0, "rgba(255,255,255,.08)"); g.addColorStop(1, "rgba(0,0,0,0)");
      cx.fillStyle = g; cx.fillRect(0, hz, W, H - hz); cx.save(); cx.strokeStyle = "rgba(255,255,255,.07)"; for (let i = 0; i < 9; i++) { const y = hz + Math.pow(i / 9, 2) * (H - hz); cx.beginPath(); cx.moveTo(0, y); cx.lineTo(W, y); cx.stroke(); } cx.restore(); }
  }

  // ---------- metáforas: (p = 0..1 na cena, t = s da cena, c = cena) -> devolve o ponto focal {x,y} p/ transição ----------
  const M = {
    um_entre_muitos(p, t, c) {
      const col = 6, lin = 8, esp = 150, x0 = W/2 - (col - 1) * esp / 2, y0 = 820 - (lin - 1) * esp / 2; let foco = { x: W/2, y: 820 };
      const alvo = c.alvo ?? 27;
      for (let i = 0; i < col * lin; i++) { const cxp = x0 + (i % col) * esp + Math.sin(t + i) * 4, cyp = y0 + Math.floor(i / col) * esp + Math.cos(t * .8 + i) * 4;
        const ent = back((t - rnd(i) * .5) / .5);
        if (i === alvo) { foco = { x: cxp, y: cyp }; continue; }
        c.icone ? icone(c.icone, cxp, cyp, 96 * ent, S.dim) : bola(cxp, cyp, 46 * ent, S.estilo === "bolhas" ? `rgba(255,255,255,${.12 + rnd(i) * .2})` : S.dim); }
      const pul = 1 + .08 * Math.sin(t * 5) * eo((t - .6) / .4), r = 52 * back((t - .4) / .5) * pul;
      c.icone ? icone(c.icone, foco.x, foco.y, 110 * r / 52, S.hi, S.glow) : bola(foco.x, foco.y, r, S.hi, S.glow);
      return foco;
    },
    trabalhando(p, t, c) {
      const y = 760, a = eo(t / .6); cx.save(); cx.globalAlpha = a;
      retR(260, y - 330, 560, 360, 22, S.hi, "stroke", 6, S.glow);
      cx.fillStyle = S.hi; cx.font = "26px monospace"; const linhas = ["def resolver(problema):", "  plano = dividir(problema)", "  for passo in plano:", "    executar(passo)", "  return feito"];
      const nch = Math.floor(cl((t - .4) / (c.dur - 1), 0, 1) * 110); let k = 0;
      linhas.forEach((l, i) => { const s = l.slice(0, cl(nch - k, 0, l.length)); k += l.length; cx.fillText(s, 300, y - 270 + i * 46); });
      cx.fillRect(500, y + 30, 80, 70); cx.fillRect(420, y + 96, 240, 10);
      cx.strokeStyle = S.mid; cx.lineWidth = 6; cx.beginPath(); cx.moveTo(140, y + 260); cx.lineTo(940, y + 260); cx.stroke(); cx.restore();
      pessoa(W/2, y + 330, 330, S.hi, S.glow, a);
      return { x: W/2, y: y - 150 };
    },
    multidao(p, t, c) {
      const n = 5; for (let i = 0; i < n; i++) { const x = 120 + i * 150, y = 920 + (i % 2) * 50, a = eo((t - i * .08) / .4);
        S.estilo === "bolhas" ? blob(x, y, .9, S.mid, true, .8, Math.sin(t * 6 + i) * .5 + .5) : icone("person", x, y, 400, S.mid, 0, a);
        if (i % 2 === 0) balao(x + 30, y - 260 - Math.sin(t * 3 + i) * 10, .9, S.mid, eo((t - .4 - i * .15) / .3)); }
      const hx = 900, hy = 920, a = eo((t - .3) / .5); pessoa(hx, hy, 330, S.hi, S.glow, a);
      return { x: hx, y: hy };
    },
    frase(p, t, c) {   // a frase grande fica no texto (HTML); aqui só o check desenhando
      if (c.check === false) return { x: W/2, y: 960 };
      const q = eio((t - .6) / .5); cx.save(); cx.strokeStyle = S.hi; cx.lineWidth = 16; cx.lineCap = "round"; cx.lineJoin = "round"; brilho(S.hi, S.glow);
      const pts = [[440, 1180], [520, 1260], [660, 1110]]; cx.beginPath(); cx.moveTo(...pts[0]);
      const L1 = Math.hypot(80, 80), L2 = Math.hypot(140, 150), d = q * (L1 + L2);
      if (d <= L1) cx.lineTo(lerp(440, 520, d / L1), lerp(1180, 1260, d / L1)); else { cx.lineTo(520, 1260); cx.lineTo(lerp(520, 660, (d - L1) / L2), lerp(1260, 1110, (d - L1) / L2)); }
      cx.stroke(); cx.restore(); return { x: W/2, y: 960 };
    },
    sobe_da_pilha(p, t, c) {
      for (let i = 0; i < 70; i++) { const x = (i % 10) * 116 + 30 + (Math.floor(i / 10) % 2) * 58, y = 1700 - Math.floor(i / 10) * 70 - rnd(i) * 20;
        S.estilo === "bolhas" ? blob(x, y - 40, .5, S.dim, false) : bola(x, y, 52, S.dim); }
      const sobe = eio((t - .3) / (c.dur - .8)), y = lerp(1300, 650, sobe);
      for (let k = 1; k < 7; k++) bola(W/2, y + k * 46, 30 - k * 3.5, S.hi, 0, .25 - k * .03);
      bola(W/2, y, 40, S.hi, S.glow); return { x: W/2, y };
    },
    empurra(p, t, c) {
      const ch = 1000, ax = lerp(560, 640, eio(t / c.dur)); cx.save(); cx.strokeStyle = S.hi; cx.lineWidth = 6; cx.beginPath(); cx.moveTo(0, ch); cx.lineTo(W, ch); cx.stroke(); cx.restore();
      retR(ax, ch - 300, 300, 300, 6, S.hi, "stroke", 22, S.glow * .6);
      icone("directions_run", ax - 120, ch - 150, 300, S.hi, S.glow * .5); return { x: ax + 150, y: ch - 150 };
    },
    forma_vira(p, t, c) {
      const q = eio((t - .3) / 1.0), x = W/2 + Math.sin(t * .8) * 20, y = 900, r = 210;
      cx.save(); const rr = lerp(6, r, q); retR(x - r, y - r, 2 * r, 2 * r, rr, lerp(1, 0, q) > .02 ? S.hi : S.hi, q < .5 ? "stroke" : "fill", 22, S.glow * .5, 1);
      cx.restore(); if (q > .45) bola(x, y, r, "#cfcfcf", S.glow * .4, eo((q - .45) / .3), true);
      if (S.piso === "reflexo") bola(x, y + r * 2.05, r, "#cfcfcf", 0, .12 * q, true);
      return { x, y };
    },
    revoada(p, t, c) {
      for (let i = 0; i < 26; i++) { const x = ((rnd(i) * W * 1.3 + t * 260 * (0.7 + rnd(i, 2) * .5)) % (W * 1.3)) - 120, y = rnd(i, 3) * H * .9 + 120 - x * .35;
        icone("send", x, y, 60 + rnd(i, 4) * 60, S.mid, 0, .5 + rnd(i, 5) * .4); }
      const q = eio((t - .6) / 1.0), ang = lerp(0, -Math.PI * .75, q), x = W/2, y = 960;
      cx.save(); cx.translate(x, y); cx.rotate(ang); icone("send", 0, 0, 190, S.hi, S.glow); cx.restore(); return { x, y };
    },
    porta(p, t, c) {
      const a = eo(t / .8), x = W/2, y = 860; cx.save(); cx.globalAlpha = a; brilho(S.hi, 90);
      const g = cx.createLinearGradient(0, y - 330, 0, y + 330); g.addColorStop(0, "#ffffff"); g.addColorStop(1, "#d9d9d9"); cx.fillStyle = g; cx.fillRect(x - 190, y - 330, 380, 660); cx.restore();
      cx.save(); cx.globalAlpha = a; cx.strokeStyle = S.mid; cx.lineWidth = 5; for (let i = 0; i < 4; i++) { const yy = y + 330 + i * 70, w = 420 + i * 80; cx.strokeRect(x - w/2, yy, w, 70); } cx.restore();
      return { x, y };
    },
    caminho(p, t, c) {
      const n = 7; for (let i = 0; i < n; i++) { const q = back((t - i * .18) / .35), z = i / n, y = 1500 - i * 95, w = lerp(330, 120, z), h = lerp(70, 30, z);
        if (q <= 0) continue; cx.save(); cx.globalAlpha = cl(q, 0, 1); retR(W/2 - w/2 + (i % 2 ? 40 : -40) * (1 - z), y - h/2, w * q, h, 6, S.hi, "fill", 0, S.glow * .5); cx.restore(); }
      icone(c.icone || "sprint", W/2, 1050 + Math.sin(t * 9) * 8, 320, S.hi, S.glow); return { x: W/2, y: 1050 };
    },
    calendario(p, t, c) {
      const s = back(t / .6), x = W/2, y = 900; cx.save(); cx.translate(x, y); cx.scale(s, s);
      S.vidro ? vidro(-200, -200, 400, 400) : retR(-200, -200, 400, 400, 40, S.hi, "stroke", 10, S.glow);
      cx.fillStyle = S.hi; cx.textAlign = "center"; cx.font = "800 150px Poppins"; cx.fillText(c.dia || "26", 0, 30); cx.font = "700 76px Poppins"; cx.fillText(c.mes || "MAI", 0, 130);
      const q = eio((t - .9) / .5); if (q > 0) { cx.strokeStyle = S.hi; cx.lineWidth = 22; cx.lineCap = "round"; brilho(S.hi, S.glow); cx.beginPath(); cx.moveTo(-120, -10); cx.lineTo(-30, 80); cx.lineTo(lerp(-30, 150, q), lerp(80, -150, q)); cx.stroke(); }
      cx.restore(); return { x, y };
    },
    cartoes(p, t, c) {
      const ics = c.icones || ["directions_run", "fitness_center", "menu_book"]; let foco = { x: W/2, y: 960 };
      ics.forEach((nome, i) => { const k = i - (ics.length - 1) / 2, q = back((t - i * .25) / .6), x = W/2 + k * 300 * q, y = 980 + Math.abs(k) * 30, rot = k * .08 * q;
        cx.save(); cx.translate(x, y); cx.rotate(rot); S.vidro ? vidro(-130, -200, 260, 400, cl(q, 0, 1)) : retR(-130, -200, 260, 400, 26, S.hi, "stroke", 6, S.glow * .5, cl(q, 0, 1));
        icone(nome, 0, 0, 150, S.hi, S.glow * .5, cl(q, 0, 1)); cx.restore(); });
      return foco;
    },
    heroi(p, t, c) {
      const a = eo(t / .8); cx.save(); cx.globalAlpha = a; cx.fillStyle = "#e9e9e9"; cx.fillRect(0, 0, W, H);
      cx.strokeStyle = "rgba(0,0,0,.18)"; cx.lineWidth = 3; const vx = W/2, vy = 900;
      for (let i = -8; i <= 8; i++) { cx.beginPath(); cx.moveTo(vx, vy); cx.lineTo(vx + i * 260, H); cx.stroke(); cx.beginPath(); cx.moveTo(vx, vy); cx.lineTo(vx + i * 260, 0); cx.stroke(); }
      const g = cx.createRadialGradient(vx, vy, 10, vx, vy, 600); g.addColorStop(0, "rgba(255,255,255,1)"); g.addColorStop(1, "rgba(255,255,255,0)"); cx.fillStyle = g; cx.fillRect(0, 0, W, H); cx.restore();
      const s = lerp(.85, 1, eo(t / c.dur)); icone("accessibility_new", vx, 1180, 420 * s, "#111111", 0, a); return { x: vx, y: 1100 };
    },
    identidade(p, t, c) {
      let foco = { x: W/2, y: 960 }; for (let i = 0; i < 5; i++) { const x = W/2 + (i - 2) * 220 - eio(t / c.dur) * 60, y = 960, s = i === 2 ? 1.1 : .9;
        if (i === 2) { bola(x, y, 100 * s, "#dcdcdc", S.glow * .6, 1, true); icone("fingerprint", x, y, 130, "#5a5a5a"); foco = { x, y }; }
        else { retR(x - 90, y - 90, 180, 180, 40, "#bdbdbd", "fill", 0, 0, .9); retR(x - 50, y - 50, 100, 100, 14, "#1a1a1a"); } }
      return foco;
    },
  };

  // ---------- quadro ----------
  function cena(k, tl) { const c = CN[k]; const z = lerp(1, c.zoom ?? 1.06, eio(tl / c.dur));
    cx.save(); cx.translate(W/2, H*.47); cx.scale(z, z); cx.translate(-W/2, -H*.47);
    const f = (M[c.metafora] || M.frase)(tl / c.dur, tl, c); cx.restore(); return f; }
  function draw(t) {
    let k = 0; while (k < CN.length - 1 && t >= T0[k+1]) k++;
    const TR = .45, tl = t - T0[k] + (k ? TR : 0); fundo(t);   // cena k já vinha correndo desde a transição
    const f = cena(k, tl);
    const fimK = CN[k].dur + (k ? TR : 0);
    if (k < CN.length - 1 && tl > fimK - TR) {          // transição para a próxima
      const q = eio((tl - (fimK - TR)) / TR);
      cx.save();
      if (S.trans === "iris") { cx.beginPath(); cx.arc(f.x, f.y, q * H * 1.2, 0, Math.PI * 2); cx.clip(); }
      else cx.globalAlpha = q;
      if (S.trans === "push") { cx.translate(W/2, H/2); const s = lerp(.86, 1, q); cx.scale(s, s); cx.translate(-W/2, -H/2); }
      if (S.trans === "slide") cx.translate((1 - q) * W * .35, 0);
      fundo(t); cena(k + 1, tl - (fimK - TR)); cx.restore();
    }
  }

  // ---------- texto (HTML), animação por estilo ----------
  const tl = gsap.timeline({ paused: true }); const st = { t: 0 };
  tl.to(st, { t: DUR, duration: DUR, ease: "none", onUpdate: () => draw(st.t) }, 0); draw(0);
  const box = document.getElementById("txt");
  CN.forEach((c, k) => {
    if (!c.fala) return;
    const el = document.createElement("div"); el.className = "fala " + (c.metafora === "frase" ? "grande " : "") + (c.metafora === "heroi" ? "escuro" : ""); box.appendChild(el);
    const ent = T0[k] + .15, sai = T0[k] + c.dur - .3;
    if (P.estilo === "bolhas") {                     // digita letra a letra
      el.innerHTML = c.fala.split(" ").map(w => `<span class="w">${[...w].map(ch => `<span class="l">${ch}</span>`).join("")}</span>`).join(" "); const ls = el.querySelectorAll(".l");
      tl.set(ls, { opacity: 0 }, 0); tl.to(ls, { opacity: 1, duration: .01, stagger: .045 }, ent);
    } else if (P.estilo === "objetos") {             // letras caem
      el.innerHTML = c.fala.split(" ").map(w => `<span class="w">${[...w].map(ch => `<span class="l">${ch}</span>`).join("")}</span>`).join(" ");
      tl.from(el.querySelectorAll(".l"), { y: -60, opacity: 0, rotation: (i) => (rnd(i, 9) - .5) * 40, duration: .45, stagger: .03, ease: "back.out(2)" }, ent);
    } else if (P.estilo === "grade") {               // palavras sobem uma a uma
      el.innerHTML = c.fala.split(" ").map(w => `<span class="w">${w}</span>`).join(" ");
      tl.from(el.querySelectorAll(".w"), { y: 40, opacity: 0, filter: "blur(8px)", duration: .4, stagger: .12, ease: "power3.out" }, ent);
    } else {                                          // destaque: legenda condensada sobe
      el.textContent = c.fala; tl.from(el, { y: 30, opacity: 0, duration: .35, ease: "power3.out" }, ent);
    }
    tl.to(el, { opacity: 0, duration: .25, ease: "power2.in" }, sai);
  });
  window.__timelines = window.__timelines || {}; window.__timelines["metaforas"] = tl;
})();
