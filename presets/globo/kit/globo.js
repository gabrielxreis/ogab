// Preset GLOBO: explicador de dados num globo 3D que gira até cada cidade, rotas pontilhadas que crescem entre elas,
// cartão de dado (seção, etiqueta, número contando, rótulo e fonte) e legenda karaokê opcional.
// O globo é desenhado num canvas a partir do TEMPO (função pura de t), então o render sai igual em qualquer seek.
// O cartão e a legenda são DOM animado pela timeline GSAP pausada (HyperFrames). Campos: ver gerar.py.
(async function () {
  const P = window.PLANO, W = P.w, H = P.h, VERT = H >= W, U = Math.min(W, H) / 1080, dur = P.dur;
  try { await Promise.all([document.fonts.load("800 120px 'Inter Tight'"), document.fonts.load("700 40px 'Inter Tight'"),
    document.fonts.load("800 30px 'JetBrains Mono'"), document.fonts.load("500 30px 'JetBrains Mono'")]); await document.fonts.ready; } catch (e) {}
  const root = document.getElementById("root"), cv = document.getElementById("cena"), g = cv.getContext("2d");
  cv.width = W; cv.height = H; root.style.setProperty("--cor", P.cor);
  const tl = gsap.timeline({ paused: true });
  const mk = (tag, cls, pai, css) => { const e = document.createElement(tag); if (cls) e.className = cls; if (css) Object.assign(e.style, css); if (pai) pai.appendChild(e); return e; };
  const px = v => (v * U).toFixed(2) + "px";
  const D2R = Math.PI / 180, clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const eio = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2, eout = t => 1 - Math.pow(1 - t, 3);
  const prog = (t, t0, d) => clamp((t - t0) / d, 0, 1);
  const C = P.cidades, cenas = P.cenas, COR = P.cor;

  // ---------- geometria ----------
  const vec = (lat, lon) => { const a = lat * D2R, o = lon * D2R; return [Math.cos(a) * Math.cos(o), Math.cos(a) * Math.sin(o), Math.sin(a)]; };
  const slerp = (a, b, k) => { const d = clamp(a[0] * b[0] + a[1] * b[1] + a[2] * b[2], -1, 1), om = Math.acos(d);
    if (om < 1e-6) return a.slice(); const s = Math.sin(om), p = Math.sin((1 - k) * om) / s, q = Math.sin(k * om) / s;
    return [a[0] * p + b[0] * q, a[1] * p + b[1] * q, a[2] * p + b[2] * q]; };
  let CAM = null;   // câmera do quadro atual: centro, raio e senos
  function prepara(cam) {
    const l0 = cam.lon * D2R, p0 = cam.lat * D2R, R = (VERT ? .40 * W : .34 * H) * cam.zoom;
    CAM = { cl: Math.cos(l0), sl: Math.sin(l0), cp: Math.cos(p0), sp: Math.sin(p0), R, cx: (VERT ? .5 : .64) * W, cy: cam.y * H };
  }
  // mundo -> [x tela, y tela, z (frente > 0), dentro do disco?]
  function tela(v) {
    const c = CAM, x1 = v[0] * c.cl + v[1] * c.sl, y1 = -v[0] * c.sl + v[1] * c.cl, z1 = v[2];
    const x2 = x1 * c.cp + z1 * c.sp, z2 = -x1 * c.sp + z1 * c.cp;
    return [c.cx + c.R * y1, c.cy - c.R * z2, x2, y1 * y1 + z2 * z2 < 1];
  }
  const ve = s => s[2] > 0 || !s[3];   // visível: na frente, ou fora do disco (no espaço)

  // ---------- câmera por cena (transição suave + deriva lenta) ----------
  const TRANS = P.transicao || 1.15, DERIVA = P.deriva ?? .45;
  const alvos = cenas.map(c => { const f = C[c.foco] || { lat: 0, lon: 0 };
    return { lat: (c.cam && c.cam.lat != null ? c.cam.lat : f.lat + (c.inclina ?? 7)), lon: (c.cam && c.cam.lon != null ? c.cam.lon : f.lon + (c.giro || 0)),
      zoom: c.zoom ?? (c.tipo === "cta" ? .8 : 1), y: c.y ?? (c.tipo === "cta" ? .6 : .57) }; });
  const idx = t => { let i = 0; while (i < cenas.length - 1 && t >= cenas[i + 1].de) i++; return i; };
  const lerpLon = (a, b, k) => a + ((((b - a) % 360) + 540) % 360 - 180) * k;
  const inicio = [];
  function camEm(t) {
    const i = idx(t), c = cenas[i], T = alvos[i], dt = Math.max(0, t - c.de), len = Math.max(.5, c.ate - c.de);
    const alvo = { lat: T.lat, lon: T.lon - DERIVA * dt, zoom: T.zoom, y: T.y };
    // passos de câmera dentro da cena (ex.: afasta quando o número entra), cada um com a mesma curva da transição
    for (const p of c.camera || []) { if (t < p.em) break; const k = eio(prog(t, p.em, p.dur || TRANS));
      if (p.zoom != null) alvo.zoom += (p.zoom - alvo.zoom) * k; if (p.y != null) alvo.y += (p.y - alvo.y) * k;
      if (p.inclina != null) { const f = C[c.foco] || { lat: 0 }; alvo.lat += (f.lat + p.inclina - alvo.lat) * k; }
      if (p.giro != null) alvo.lon += p.giro * k; }
    alvo.zoom *= 1 + .03 * Math.min(dt / len, 1);
    if (i === 0) { const k = eio(prog(t, 0, 2.0));   // abertura: o globo já está na tela no quadro 0 e assenta girando
      return { lat: alvo.lat + 5 * (1 - k), lon: alvo.lon - 18 * (1 - k), zoom: alvo.zoom * (.95 + .05 * k), y: alvo.y }; }
    const a = inicio[i], k = eio(prog(t, c.de, TRANS));
    return { lat: a.lat + (alvo.lat - a.lat) * k, lon: lerpLon(a.lon, alvo.lon, k), zoom: a.zoom + (alvo.zoom - a.zoom) * k, y: a.y + (alvo.y - a.y) * k };
  }
  for (let i = 1; i < cenas.length; i++) inicio[i] = camEm(cenas[i].de - 1e-4);

  // ---------- o que aparece quando ----------
  const ativa = t => cenas[idx(t)].foco, HP = P.altura_pino ?? .13;   // altura da haste (fração do raio)
  const visitou = (id, t) => cenas.some(c => c.foco === id && c.de <= t);
  const surge = {};   // cidade -> instante em que o pino aparece
  const marca = (id, t) => { if (id && C[id] && (surge[id] == null || t < surge[id])) surge[id] = t; };
  const rotas = [];
  cenas.forEach(c => { marca(c.foco, c.de); (c.pinos || []).forEach(p => marca(p, c.de));
    (c.rotas || []).forEach(r => { const rd = r.dur || .8; rotas.push({ ...r, rd }); marca(r.de, r.em); marca(r.para, r.em + rd * .9); }); });
  rotas.forEach(r => { const a = C[r.de], b = C[r.para], va = vec(a.lat, a.lon), vb = vec(b.lat, b.lon), ha = r.alt_de ?? HP, hb = r.alt ?? HP, arco = r.arco ?? .12, N = 140;
    r.pts = []; for (let i = 0; i <= N; i++) { const k = i / N, p = slerp(va, vb, k), h = 1 + ha + (hb - ha) * k + arco * Math.sin(Math.PI * k); r.pts.push([p[0] * h, p[1] * h, p[2] * h]); } });

  // ---------- malha fixa: pontos da superfície e grade ----------
  const PONTOS = []; { const N = P.pontos || 2600, ga = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < N; i++) { const y = 1 - (i + .5) / N * 2, r = Math.sqrt(1 - y * y), th = ga * i; PONTOS.push([Math.cos(th) * r, Math.sin(th) * r, y]); } }
  const GRADE = [];
  for (let lon = -180; lon < 180; lon += 30) { const l = []; for (let lat = -84; lat <= 84; lat += 3) l.push(vec(lat, lon)); GRADE.push(l); }
  for (let lat = -60; lat <= 60; lat += 30) { const l = []; for (let lon = -180; lon <= 180; lon += 3) l.push(vec(lat, lon)); GRADE.push(l); }

  // poeira com semente (nada de Math.random): na frente e atrás do globo, com paralaxe da câmera
  let semente = 9071; const rnd = () => { semente = (semente * 16807) % 2147483647; return (semente - 1) / 2147483646; };
  const POEIRA = Array.from({ length: P.poeira ?? 30 }, () => ({ x: rnd(), y: rnd(), d: .15 + rnd() * .85, s: 2 + rnd() * 9, f: rnd() * 6.28 }));
  function poeira(t, cam, frente) {
    for (const p of POEIRA) { if ((p.d > .7) !== frente) continue;
      const x = ((p.x * W - cam.lon * 2.2 * U * p.d * 4 + Math.sin(t * .3 + p.f) * 8 * U) % W + W) % W;
      const y = ((p.y * H - t * 7 * U * p.d) % H + H) % H, r = p.s * U * (frente ? 1.3 : .7) * p.d + 1.2 * U;
      g.globalAlpha = (frente ? .18 : .2) + .25 * p.d; g.fillStyle = "#B9B9B2";
      if (frente) g.filter = `blur(${(1.2 + p.d * 2.2) * U}px)`;
      g.beginPath(); g.arc(x, y, r, 0, 6.2832); g.fill(); g.filter = "none"; }
    g.globalAlpha = 1;
  }

  // ---------- desenho do quadro ----------
  function anel(v, raioGraus, cor, larg) {
    const lat = Math.asin(v[2]), lon = Math.atan2(v[1], v[0]);
    const e = [-Math.sin(lon), Math.cos(lon), 0], n = [-Math.sin(lat) * Math.cos(lon), -Math.sin(lat) * Math.sin(lon), Math.cos(lat)];
    const a = raioGraus * D2R, ca = Math.cos(a), sa = Math.sin(a);
    g.beginPath(); let on = false;
    for (let i = 0; i <= 48; i++) { const th = i / 48 * 6.2832, c = Math.cos(th) * sa, s = Math.sin(th) * sa;
      const p = tela([v[0] * ca + e[0] * c + n[0] * s, v[1] * ca + e[1] * c + n[1] * s, v[2] * ca + e[2] * c + n[2] * s]);
      if (p[2] <= 0) { on = false; continue; } on ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]); on = true; }
    g.strokeStyle = cor; g.lineWidth = larg; g.stroke();
  }
  function rotulo(cid, cor, alfa) {
    const R = CAM.R, desce = 50 * U / (R * D2R), la = cid.lat - desce;
    const A = tela(vec(la, cid.lon)), E = tela(vec(la, cid.lon + 1)), N = tela(vec(la + 1, cid.lon));
    if (A[2] <= 0) return;
    const se = R * Math.max(.25, Math.cos(la * D2R)) * D2R, sn = R * D2R;
    const ux = (E[0] - A[0]) / se, uy = (E[1] - A[1]) / se, vx = (N[0] - A[0]) / sn, vy = (N[1] - A[1]) / sn;
    g.save(); g.setTransform(ux, uy, -vx, -vy, A[0], A[1]); g.globalAlpha = alfa;
    g.font = `800 ${36 * U}px 'Inter Tight'`; g.textAlign = "center"; g.textBaseline = "middle"; g.fillStyle = cor;
    g.fillText(cid.nome, 0, 0); g.restore();
  }
  function desenha(t) {
    const cam = camEm(t); prepara(cam); const { R, cx, cy } = CAM;
    g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, W, H);
    poeira(t, cam, false);
    // globo: sombra, corpo azul-marinho com luz no alto à direita, borda escura
    g.save(); g.shadowColor = "rgba(0,0,0,.9)"; g.shadowBlur = 110 * U; g.fillStyle = "#0E1A34";
    g.beginPath(); g.arc(cx, cy, R, 0, 6.2832); g.fill(); g.restore();
    const gr = g.createRadialGradient(cx + .4 * R, cy - .42 * R, R * .04, cx + .12 * R, cy - .1 * R, R * 1.12);
    gr.addColorStop(0, "#3C4559"); gr.addColorStop(.3, "#25355A"); gr.addColorStop(.66, "#1B2C50"); gr.addColorStop(1, "#0F1A35");
    g.fillStyle = gr; g.beginPath(); g.arc(cx, cy, R, 0, 6.2832); g.fill();
    // pontos da superfície (3 faixas de opacidade pela profundidade)
    const lado = 2.3 * U;
    for (const [z0, z1, al] of [[.05, .4, .16], [.4, .75, .26], [.75, 1.01, .34]]) {
      g.fillStyle = `rgba(150,176,232,${al})`; g.beginPath();
      for (const v of PONTOS) { const s = tela(v); if (s[2] > z0 && s[2] <= z1) g.rect(s[0] - lado / 2, s[1] - lado / 2, lado, lado); }
      g.fill(); }
    // grade (meridianos e paralelos), mais fraca perto da borda
    g.lineWidth = 1.7 * U;
    for (const l of GRADE) { let a = tela(l[0]);
      for (let i = 1; i < l.length; i++) { const b = tela(l[i]);
        if (a[2] > 0 && b[2] > 0) { g.strokeStyle = `rgba(150,180,236,${(.1 + .24 * Math.min(a[2], b[2])).toFixed(3)})`;
          g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); }
        a = b; } }
    // borda interna escura
    const rim = g.createRadialGradient(cx, cy, R * .8, cx, cy, R);
    rim.addColorStop(0, "rgba(6,10,24,0)"); rim.addColorStop(1, "rgba(6,10,24,.55)");
    g.fillStyle = rim; g.beginPath(); g.arc(cx, cy, R, 0, 6.2832); g.fill();
    const foco = ativa(t), inicioCena = cenas[idx(t)].de;
    // anéis na base dos pinos (o da cidade em foco abre e solta uma onda quando a câmera chega)
    for (const id in surge) { if (t < surge[id]) continue; const c = C[id], v = vec(c.lat, c.lon), k = eout(prog(t, surge[id], .6));
      if (id === foco) { const kk = eout(prog(t, inicioCena + .35, .7)); const b0 = surge[id] < inicioCena - .01 ? .6 : 0; anel(v, 5.2 * Math.max(b0 + (1 - b0) * kk, .001), "rgba(232,234,240,.6)", 2.6 * U);
        const o = prog(t, inicioCena + .5, 1.3); if (o > 0 && o < 1) anel(v, 5.2 + 5 * eout(o), `rgba(244,247,138,${(.5 * (1 - o)).toFixed(3)})`, 2 * U); void k; }
      else anel(v, 4.4 * Math.max(k, .001), "rgba(225,228,236,.42)", 2.2 * U); }
    // rotas pontilhadas: crescem do ponto de partida, somem atrás do globo
    g.fillStyle = COR; const passo = 14 * U, rp = 4.6 * U;
    for (const r of rotas) { const p = eio(prog(t, r.em, r.rd)); if (p <= 0) continue;
      const S = r.pts.map(tela); let acc = 0, prox = 0; const tot = []; tot[0] = 0;
      for (let i = 1; i < S.length; i++) tot[i] = tot[i - 1] + Math.hypot(S[i][0] - S[i - 1][0], S[i][1] - S[i - 1][1]);
      const lim = tot[S.length - 1] * p;
      for (let i = 1; i < S.length && acc <= lim; i++) { const segL = tot[i] - tot[i - 1];
        while (prox <= tot[i] && prox <= lim) { const k = segL ? (prox - tot[i - 1]) / segL : 0, a = S[i - 1], b = S[i];
          if (ve(a) && ve(b)) { g.beginPath(); g.arc(a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, rp, 0, 6.2832); g.fill(); }
          prox += passo; }
        acc = tot[i]; } }
    // rótulos das cidades deitados na superfície
    for (const id in surge) { if (t < surge[id]) continue; const c = C[id], al = eout(prog(t, surge[id] + .1, .5));
      rotulo(c, id === foco ? COR : "#F2F2EE", al); }
    // pinos: haste branca saindo da superfície; o da cidade em foco tem a cabeça amarela e maior
    for (const id in surge) { if (t < surge[id]) continue; const c = C[id], v = vec(c.lat, c.lon), k = eout(prog(t, surge[id], .45));
      const at = id === foco, vi = visitou(id, t), h = 1 + HP * k, b = tela(v), cab = tela([v[0] * h, v[1] * h, v[2] * h]);
      if (!ve(cab) || (b[2] <= 0 && cab[3])) continue;
      if (b[2] > 0) { g.strokeStyle = "#E9E9E4"; g.lineWidth = 3.2 * U; g.lineCap = "round"; g.beginPath(); g.moveTo(b[0], b[1]); g.lineTo(cab[0], cab[1]); g.stroke(); }
      const pop = at ? .7 + .3 * eout(prog(t, inicioCena + .25, .45)) : 1;
      g.fillStyle = at || vi ? COR : "#ECECE8"; g.beginPath(); g.arc(cab[0], cab[1], (at ? 23 : vi ? 17 : 12) * U * k * pop, 0, 6.2832); g.fill(); }
    poeira(t, cam, true);
  }
  const relogio = { t: 0 };
  tl.to(relogio, { t: dur, duration: dur, ease: "none", onUpdate: () => desenha(relogio.t) }, 0);
  desenha(0);

  // ---------- cartão (DOM) ----------
  const card = document.getElementById("card");
  Object.assign(card.style, VERT ? { left: px(90), top: (H * .152).toFixed(1) + "px" } : { left: px(80), top: px(80) });
  if (P.serie) { const k = mk("div", "kicker", card, { fontSize: px(24), marginBottom: px(14) }); k.textContent = P.serie;
    tl.fromTo(k, { opacity: 0 }, { opacity: 1, duration: .5, ease: "power2.out" }, 0); }
  const pil = mk("div", "pilula", card, { height: px(62), paddingRight: px(26) });
  mk("span", "bola", pil, { width: px(40), height: px(40), margin: `0 ${px(14)} 0 ${px(11)}` });
  const txts = cenas.map(c => { const s = mk("span", "txt", pil, { fontSize: px(30), display: "none" }); s.textContent = "• " + (c.secao || ""); return s; });
  tl.fromTo(pil, { maxWidth: px(62) }, { maxWidth: px(1000), duration: .8, ease: "power3.out" }, .1);
  cenas.forEach((c, i) => { tl.set(txts[i], { display: "inline" }, c.de); if (i < cenas.length - 1) tl.set(txts[i], { display: "none" }, cenas[i + 1].de);
    if (i) tl.fromTo(txts[i], { opacity: .25 }, { opacity: 1, duration: .45, ease: "power2.out", immediateRender: false }, c.de); });
  const fontesEl = P.fontes ? mk("div", "fontes", card, { fontSize: px(18), marginTop: px(12) }) : null;
  if (fontesEl) { fontesEl.textContent = P.fontes; tl.fromTo(fontesEl, { opacity: 0 }, { opacity: 1, duration: .5, ease: "power2.out" }, P.fontes_em ?? .6); }
  const area = mk("div", "", card, { position: "relative", marginTop: px(14) });
  const sinal = (v, n) => v < 0 ? "−" : (n.sinal && v > 0 ? "+" : "");
  const fmt = (v, n) => (n.prefixo || "") + sinal(v, n) + Math.abs(v).toLocaleString("pt-BR", { minimumFractionDigits: n.decimais || 0, maximumFractionDigits: n.decimais || 0 }) + (n.sufixo || "");
  cenas.forEach((c, i) => {
    if (c.tipo === "cta") return;
    const gp = mk("div", "", area, { position: "absolute", left: 0, top: 0, width: px(VERT ? 900 : 760) }), t0 = c.de + .08;
    if (c.etiqueta) { const e = mk("div", "etiqueta", gp, { fontSize: px(21), padding: `${px(7)} ${px(14)}` }); e.textContent = c.etiqueta;
      tl.fromTo(e, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: .45, ease: "power3.out" }, t0); }
    const n = c.numero;
    if (n) { const em = n.em ?? c.de + .4, el = mk("div", "numero", gp, { fontSize: px(n.tamanho || 158), marginTop: px(14) });
      if (n.texto) el.textContent = n.texto;
      else { const o = { v: 0 }; el.textContent = fmt(n.de ?? 0, n);
        tl.fromTo(o, { v: n.de ?? 0 }, { v: n.valor, duration: n.conta ?? 1.3, ease: "expo.out", immediateRender: false,
          onUpdate: () => { el.textContent = fmt(o.v, n); } }, em); }
      tl.fromTo(el, { opacity: 0, y: px(26) }, { opacity: 1, y: 0, duration: .6, ease: "expo.out" }, em);
      const dv = mk("div", "divisor", gp, { width: px(110), height: px(4), marginTop: px(16), transformOrigin: "0 50%" });
      tl.fromTo(dv, { scaleX: 0 }, { scaleX: 1, duration: .55, ease: "power3.out" }, em + .12); }
    const tx = (cls, txt, tam, mt, quando) => { if (!txt) return; const e = mk("div", cls, gp, { fontSize: px(tam), marginTop: px(mt), maxWidth: px(VERT ? 880 : 740) });
      e.textContent = txt; tl.fromTo(e, { opacity: 0, y: px(14) }, { opacity: 1, y: 0, duration: .5, ease: "power3.out" }, quando); };
    const base = n ? (n.em ?? c.de + .4) : t0;
    tx("rotulo", c.rotulo, 25, 12, base + .18); tx("sub", c.sub, 21, 6, base + .26);
    if ((c.topicos || []).length) { const L = mk("div", "topicos", gp, { marginTop: px(n || c.rotulo ? 22 : 12), gap: px(6), maxWidth: px(VERT ? 880 : 740) });
      const els = c.topicos.map(tp => { const e = mk("div", "topico", L, { fontSize: px(36) }); e.textContent = "• " + tp.texto; return e; });
      c.topicos.forEach((tp, j) => { tl.fromTo(els[j], { opacity: 0, x: px(-18), color: COR }, { opacity: 1, x: 0, duration: .45, ease: "power3.out" }, tp.em);
        if (j) tl.to(els[j - 1], { color: "#F2F2EE", duration: .35, ease: "power2.out" }, tp.em); }); }
    if (i < cenas.length - 1) tl.to(gp, { opacity: 0, y: px(-12), duration: .25, ease: "power2.in" }, cenas[i + 1].de - .2);
    // carimbo: bate e assenta (sem quique)
    if (c.carimbo) { const ca = document.getElementById("carimbo"), s = mk("div", "selo", ca, { borderWidth: px(4), padding: `${px(16)} ${px(30)} ${px(12)}` });
      const tt = mk("div", "t", s, { fontSize: px(c.carimbo.tamanho || 46) }); tt.textContent = c.carimbo.titulo;
      if (c.carimbo.sub) { const ss = mk("div", "s", s, { fontSize: px(16), marginTop: px(8) }); ss.textContent = c.carimbo.sub; }
      Object.assign(ca.style, { top: (H * (c.carimbo.y ?? .45)).toFixed(1) + "px" });
      tl.set(ca, { display: "block" }, c.carimbo.em);
      tl.fromTo(s, { opacity: 0, scale: 1.4, rotation: -4, xPercent: -50, yPercent: -50 }, { opacity: 1, scale: 1, rotation: -4, xPercent: -50, yPercent: -50, duration: .32, ease: "power3.out" }, c.carimbo.em);
      if (i < cenas.length - 1) tl.to(s, { opacity: 0, duration: .25 }, cenas[i + 1].de - .2); }
  });
  // CTA final: pergunta grande e botão na cor de destaque
  const fim = cenas.find(c => c.tipo === "cta");
  if (fim) { const box = document.getElementById("cta"); Object.assign(box.style, { top: (H * (VERT ? .225 : .1)).toFixed(1) + "px" });
    const q = mk("div", "q", box, { fontSize: px(fim.tam_pergunta || 52), maxWidth: px(940) }); q.textContent = fim.pergunta || "";
    tl.to(box, { opacity: 1, duration: .01 }, fim.de);
    tl.fromTo(q, { opacity: 0, y: px(24) }, { opacity: 1, y: 0, duration: .7, ease: "expo.out" }, fim.de + .1);
    if (fim.botao) { const b = mk("div", "b", box, { fontSize: px(28), padding: `${px(12)} ${px(30)}`, marginTop: px(26) }); b.textContent = fim.botao;
      tl.fromTo(b, { opacity: 0, scale: .9 }, { opacity: 1, scale: 1, duration: .55, ease: "power3.out" }, fim.botao_em ?? fim.de + .7); }
    if (fontesEl) tl.to(fontesEl, { opacity: .55, duration: .4 }, fim.de); }

  // ---------- legenda karaokê (só quando o plano pede: na timeline do editor a legenda é do software) ----------
  const PAL = P.legenda ? (P.palavras || []) : [];
  if (PAL.length) {
    const leg = document.getElementById("legenda"); Object.assign(leg.style, { top: (H * (P.legenda_y ?? (VERT ? .775 : .86))).toFixed(1) + "px" });
    const blocos = []; let cur = [];
    PAL.forEach((w, i) => { cur.push(w); const fimFrase = /[.,!?:;]$/.test(w.t), chars = cur.map(x => x.t).join(" ").length;
      if (fimFrase || cur.length >= (P.palavras_bloco || 6) || chars >= 28 || i === PAL.length - 1) { blocos.push(cur); cur = []; } });
    blocos.forEach((b, i) => {
      const ini = b[0].s - .04, fimB = i < blocos.length - 1 ? blocos[i + 1][0].s - .04 : Math.min(dur, b[b.length - 1].e + .8);
      const el = mk("div", "bloco", leg, { fontSize: px(P.legenda_tam || 48), padding: `${px(10)} ${px(24)} ${px(12)}`, maxWidth: px(800) });
      b.forEach((w, j) => { const s = mk("span", "w", el, j < b.length - 1 ? { marginRight: ".26em" } : null); s.textContent = w.t;
        tl.set(s, { color: COR }, w.s);
        tl.fromTo(s, { scale: 1.1 }, { scale: 1, duration: .22, ease: "power2.out", immediateRender: false }, w.s); });
      tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: .08, ease: "power1.out", immediateRender: false }, ini);
      tl.set(el, { opacity: 0 }, fimB);
    });
  }
  tl.set({}, {}, dur);
  window.__timelines = window.__timelines || {}; window.__timelines["globo"] = tl;
})();
