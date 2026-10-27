// Preset LÚDICO: explicador viral no estilo do @ludificando.br. Duas linguagens no mesmo vídeo:
//  - GLOBO (cenas "cidade" e "cta"): o globo do preset globo do /ogab, recriado do reel de referência (canvas 2D).
//  - ESTÚDIO 3D (cenas "palco", "disjuntor", "barras", "blocos", "placas"): chão escuro, parede, holofote em cone,
//    bonecos e props low-poly em Three.js; cada cena tem o seu canto do estúdio e a câmera viaja entre eles.
// Tudo é função pura do TEMPO (seek seguro). Cartão, carimbo, CTA e legenda são DOM na timeline GSAP pausada.
(async function () {
  const P = window.PLANO, W = P.w, H = P.h, VERT = H >= W, U = Math.min(W, H) / 1080, dur = P.dur;
  const FONTE = P.fonte || "Inter Tight";
  try { await Promise.all([document.fonts.load(`800 120px '${FONTE}'`), document.fonts.load(`700 40px '${FONTE}'`),
    document.fonts.load("800 30px 'JetBrains Mono'"), document.fonts.load("500 30px 'JetBrains Mono'")]); await document.fonts.ready; } catch (e) {}
  const root = document.getElementById("root"), cv = document.getElementById("cena"), g = cv.getContext("2d");
  const cvP = document.getElementById("poeira"), gp2 = cvP.getContext("2d"), cv3 = document.getElementById("estudio");
  cv.width = W; cv.height = H; cvP.width = W; cvP.height = H; root.style.setProperty("--cor", P.cor);
  const tl = gsap.timeline({ paused: true });
  const mk = (tag, cls, pai, css) => { const e = document.createElement(tag); if (cls) e.className = cls; if (css) Object.assign(e.style, css); if (pai) pai.appendChild(e); return e; };
  const px = v => (v * U).toFixed(2) + "px";
  const D2R = Math.PI / 180, clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const eio = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2, eout = t => 1 - Math.pow(1 - t, 3);
  const eback = t => { const c1 = 1.5, c3 = c1 + 1; return t <= 0 ? 0 : t >= 1 ? 1 : 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); };
  const prog = (t, t0, d) => clamp((t - t0) / d, 0, 1);
  const C = P.cidades, cenas = P.cenas, COR = P.cor;
  const T3 = Object.assign({ fundo: "#0c0c0c", chao: "#18181a", parede: "#1c2440", objeto: "#E6E6E0", escuro: "#2a2a2c", cinza: "#5a5a60",
    luz: "#fff6ea", cone: null, disco: null, queda: "#6e2a3a", vela_alta: null, vela_baixa: null, vinheta: null, off: "#8d8496" }, P.tema3d || {});

  // ---------- qual linguagem cada cena usa ----------
  const TIPOS3D = new Set(["palco", "disjuntor", "barras", "blocos", "placas", "duelo", "grafico", "pregao", "elevador", "placar", "calculadora",
    "barco", "skyline", "cesta", "relogios", "gangorra", "semaforo", "balanca", "cambio", "termometro", "carrinho", "luneta"]);
  cenas.forEach(c => { c._3d = TIPOS3D.has(c.tipo) || (c.tipo === "cta" && !!c.cenario && c.cenario !== "globo"); });
  // cena sem globo herda o foco do globo mais perto (a câmera do globo não gira à toa na volta)
  { let ult = null; cenas.forEach(c => { if (!c._3d && c.foco) ult = c.foco; else if (!c.foco) c._foco = ult; });
    let prox = null; for (let i = cenas.length - 1; i >= 0; i--) { const c = cenas[i]; if (!c._3d && c.foco) prox = c.foco; else if (!c.foco && !c._foco) c._foco = prox; } }
  const idx = t => { let i = 0; while (i < cenas.length - 1 && t >= cenas[i + 1].de) i++; return i; };
  const FADE = .45;   // troca globo <-> estúdio
  function alfaGlobo(t) {   // 1 = globo inteiro na tela
    const i = idx(t), c = cenas[i], agora = c._3d ? 0 : 1;
    if (i > 0 && cenas[i - 1]._3d !== c._3d) { const k = eio(prog(t, c.de - .12, FADE)); return cenas[i - 1]._3d ? k : 1 - k; }
    return agora;
  }

  // ================= GLOBO (igual ao preset globo) =================
  const vec = (lat, lon) => { const a = lat * D2R, o = lon * D2R; return [Math.cos(a) * Math.cos(o), Math.cos(a) * Math.sin(o), Math.sin(a)]; };
  const slerp = (a, b, k) => { const d = clamp(a[0] * b[0] + a[1] * b[1] + a[2] * b[2], -1, 1), om = Math.acos(d);
    if (om < 1e-6) return a.slice(); const s = Math.sin(om), p = Math.sin((1 - k) * om) / s, q = Math.sin(k * om) / s;
    return [a[0] * p + b[0] * q, a[1] * p + b[1] * q, a[2] * p + b[2] * q]; };
  let CAM = null;
  function prepara(cam) {
    const l0 = cam.lon * D2R, p0 = cam.lat * D2R, R = (VERT ? .40 * W : .34 * H) * cam.zoom;
    CAM = { cl: Math.cos(l0), sl: Math.sin(l0), cp: Math.cos(p0), sp: Math.sin(p0), R, cx: (VERT ? .5 : .64) * W, cy: cam.y * H };
  }
  function tela(v) {
    const c = CAM, x1 = v[0] * c.cl + v[1] * c.sl, y1 = -v[0] * c.sl + v[1] * c.cl, z1 = v[2];
    const x2 = x1 * c.cp + z1 * c.sp, z2 = -x1 * c.sp + z1 * c.cp;
    return [c.cx + c.R * y1, c.cy - c.R * z2, x2, y1 * y1 + z2 * z2 < 1];
  }
  const ve = s => s[2] > 0 || !s[3];
  const TRANS = P.transicao || 1.15, DERIVA = P.deriva ?? .45;
  const alvos = cenas.map(c => { const f = C[c.foco || c._foco] || { lat: 0, lon: 0 };
    return { lat: (c.cam && c.cam.lat != null ? c.cam.lat : f.lat + (c.inclina ?? 7)), lon: (c.cam && c.cam.lon != null ? c.cam.lon : f.lon + (c.giro || 0)),
      zoom: c.zoom ?? (c.tipo === "cta" ? .8 : 1), y: c.y ?? (c.tipo === "cta" ? .6 : .57) }; });
  const lerpLon = (a, b, k) => a + ((((b - a) % 360) + 540) % 360 - 180) * k;
  const inicio = [];
  function camEm(t) {
    const i = idx(t), c = cenas[i], T = alvos[i], dt = Math.max(0, t - c.de), len = Math.max(.5, c.ate - c.de);
    const alvo = { lat: T.lat, lon: T.lon - DERIVA * dt, zoom: T.zoom, y: T.y };
    if (!c._3d) for (const p of c.camera || []) { if (t < p.em) break; const k = eio(prog(t, p.em, p.dur || TRANS));
      if (p.zoom != null) alvo.zoom += (p.zoom - alvo.zoom) * k; if (p.y != null) alvo.y += (p.y - alvo.y) * k;
      if (p.inclina != null) { const f = C[c.foco] || { lat: 0 }; alvo.lat += (f.lat + p.inclina - alvo.lat) * k; }
      if (p.giro != null) alvo.lon += p.giro * k; }
    alvo.zoom *= 1 + .03 * Math.min(dt / len, 1);
    if (i === 0) { const k = eio(prog(t, 0, 2.0));
      return { lat: alvo.lat + 5 * (1 - k), lon: alvo.lon - 18 * (1 - k), zoom: alvo.zoom * (.95 + .05 * k), y: alvo.y }; }
    const a = inicio[i], k = eio(prog(t, c.de, TRANS));
    return { lat: a.lat + (alvo.lat - a.lat) * k, lon: lerpLon(a.lon, alvo.lon, k), zoom: a.zoom + (alvo.zoom - a.zoom) * k, y: a.y + (alvo.y - a.y) * k };
  }
  for (let i = 1; i < cenas.length; i++) inicio[i] = camEm(cenas[i].de - 1e-4);
  const ativa = t => cenas[idx(t)].foco, HP = P.altura_pino ?? .13;
  const visitou = (id, t) => cenas.some(c => c.foco === id && c.de <= t);
  const surge = {};
  const marca = (id, t) => { if (id && C[id] && (surge[id] == null || t < surge[id])) surge[id] = t; };
  const rotas = [];
  cenas.forEach(c => { if (c._3d) return; marca(c.foco, c.de); (c.pinos || []).forEach(p => marca(p, c.de));
    (c.rotas || []).forEach(r => { const rd = r.dur || .8; rotas.push({ ...r, rd }); marca(r.de, r.em); marca(r.para, r.em + rd * .9); }); });
  rotas.forEach(r => { const a = C[r.de], b = C[r.para], va = vec(a.lat, a.lon), vb = vec(b.lat, b.lon), ha = r.alt_de ?? HP, hb = r.alt ?? HP, arco = r.arco ?? .12, N = 140;
    r.pts = []; for (let i = 0; i <= N; i++) { const k = i / N, p = slerp(va, vb, k), h = 1 + ha + (hb - ha) * k + arco * Math.sin(Math.PI * k); r.pts.push([p[0] * h, p[1] * h, p[2] * h]); } });
  const PONTOS = []; { const N = P.pontos || 2600, ga = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < N; i++) { const y = 1 - (i + .5) / N * 2, r = Math.sqrt(1 - y * y), th = ga * i; PONTOS.push([Math.cos(th) * r, Math.sin(th) * r, y]); } }
  const GRADE = [];
  for (let lon = -180; lon < 180; lon += 30) { const l = []; for (let lat = -84; lat <= 84; lat += 3) l.push(vec(lat, lon)); GRADE.push(l); }
  for (let lat = -60; lat <= 60; lat += 30) { const l = []; for (let lon = -180; lon <= 180; lon += 3) l.push(vec(lat, lon)); GRADE.push(l); }
  let semente = 9071; const rnd = () => { semente = (semente * 16807) % 2147483647; return (semente - 1) / 2147483646; };
  const POEIRA = Array.from({ length: P.poeira ?? 30 }, () => ({ x: rnd(), y: rnd(), d: .15 + rnd() * .85, s: 2 + rnd() * 9, f: rnd() * 6.28 }));
  function poeira(ctx, t, desloc, frente) {
    for (const p of POEIRA) { if ((p.d > .7) !== frente) continue;
      const x = ((p.x * W - desloc * 2.2 * U * p.d * 4 + Math.sin(t * .3 + p.f) * 8 * U) % W + W) % W;
      const y = ((p.y * H - t * 7 * U * p.d) % H + H) % H, r = p.s * U * (frente ? 1.3 : .7) * p.d + 1.2 * U;
      ctx.globalAlpha = (frente ? .18 : .2) + .25 * p.d; ctx.fillStyle = "#B9B9B2";
      if (frente) ctx.filter = `blur(${(1.2 + p.d * 2.2) * U}px)`;
      ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fill(); ctx.filter = "none"; }
    ctx.globalAlpha = 1;
  }
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
    g.font = `800 ${36 * U}px '${FONTE}'`; g.textAlign = "center"; g.textBaseline = "middle"; g.fillStyle = cor;
    g.fillText(cid.nome, 0, 0); g.restore();
  }
  function desenhaGlobo(t, cam) {
    prepara(cam); const { R, cx, cy } = CAM;
    g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, W, H);
    g.save(); g.shadowColor = "rgba(0,0,0,.9)"; g.shadowBlur = 110 * U; g.fillStyle = "#0E1A34";
    g.beginPath(); g.arc(cx, cy, R, 0, 6.2832); g.fill(); g.restore();
    const gr = g.createRadialGradient(cx + .4 * R, cy - .42 * R, R * .04, cx + .12 * R, cy - .1 * R, R * 1.12);
    gr.addColorStop(0, "#3C4559"); gr.addColorStop(.3, "#25355A"); gr.addColorStop(.66, "#1B2C50"); gr.addColorStop(1, "#0F1A35");
    g.fillStyle = gr; g.beginPath(); g.arc(cx, cy, R, 0, 6.2832); g.fill();
    const lado = 2.3 * U;
    for (const [z0, z1, al] of [[.05, .4, .16], [.4, .75, .26], [.75, 1.01, .34]]) {
      g.fillStyle = `rgba(150,176,232,${al})`; g.beginPath();
      for (const v of PONTOS) { const s = tela(v); if (s[2] > z0 && s[2] <= z1) g.rect(s[0] - lado / 2, s[1] - lado / 2, lado, lado); }
      g.fill(); }
    g.lineWidth = 1.7 * U;
    for (const l of GRADE) { let a = tela(l[0]);
      for (let i = 1; i < l.length; i++) { const b = tela(l[i]);
        if (a[2] > 0 && b[2] > 0) { g.strokeStyle = `rgba(150,180,236,${(.1 + .24 * Math.min(a[2], b[2])).toFixed(3)})`;
          g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); }
        a = b; } }
    const rim = g.createRadialGradient(cx, cy, R * .8, cx, cy, R);
    rim.addColorStop(0, "rgba(6,10,24,0)"); rim.addColorStop(1, "rgba(6,10,24,.55)");
    g.fillStyle = rim; g.beginPath(); g.arc(cx, cy, R, 0, 6.2832); g.fill();
    const foco = ativa(t), inicioCena = cenas[idx(t)].de;
    for (const id in surge) { if (t < surge[id]) continue; const c = C[id], v = vec(c.lat, c.lon);
      if (id === foco) { const kk = eout(prog(t, inicioCena + .35, .7)); const b0 = surge[id] < inicioCena - .01 ? .6 : 0; anel(v, 5.2 * Math.max(b0 + (1 - b0) * kk, .001), "rgba(232,234,240,.6)", 2.6 * U);
        const o = prog(t, inicioCena + .5, 1.3); if (o > 0 && o < 1) anel(v, 5.2 + 5 * eout(o), `rgba(244,247,138,${(.5 * (1 - o)).toFixed(3)})`, 2 * U); }
      else anel(v, 4.4 * Math.max(eout(prog(t, surge[id], .6)), .001), "rgba(225,228,236,.42)", 2.2 * U); }
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
    for (const id in surge) { if (t < surge[id]) continue; rotulo(C[id], id === foco ? COR : "#F2F2EE", eout(prog(t, surge[id] + .1, .5))); }
    for (const id in surge) { if (t < surge[id]) continue; const c = C[id], v = vec(c.lat, c.lon), k = eout(prog(t, surge[id], .45));
      const at = id === foco, vi = visitou(id, t), h = 1 + HP * k, b = tela(v), cab = tela([v[0] * h, v[1] * h, v[2] * h]);
      if (!ve(cab) || (b[2] <= 0 && cab[3])) continue;
      if (b[2] > 0) { g.strokeStyle = "#E9E9E4"; g.lineWidth = 3.2 * U; g.lineCap = "round"; g.beginPath(); g.moveTo(b[0], b[1]); g.lineTo(cab[0], cab[1]); g.stroke(); }
      const pop = at ? .7 + .3 * eout(prog(t, inicioCena + .25, .45)) : 1;
      g.fillStyle = at || vi ? COR : "#ECECE8"; g.beginPath(); g.arc(cab[0], cab[1], (at ? 23 : vi ? 17 : 12) * U * k * pop, 0, 6.2832); g.fill(); }
  }

  // ================= ESTÚDIO 3D =================
  const tem3d = cenas.some(c => c._3d) && window.THREE;
  let E3 = null;
  const FOTOS = {};   // fotos do "duelo": carregadas ANTES do primeiro quadro (render determinístico)
  await Promise.all([...new Set(cenas.flatMap(c => (c.lados || []).map(l => l.foto)).filter(Boolean))].map(src => new Promise(ok => {
    const im = new Image(); im.onload = () => { FOTOS[src] = im; ok(); }; im.onerror = () => { console.warn("foto não carregou", src); ok(); }; im.src = src; })));
  if (tem3d) E3 = montaEstudio();
  function montaEstudio() {
    const T = THREE, rnd3 = (() => { let s = 4441; return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; }; })();
    const ren = new T.WebGLRenderer({ canvas: cv3, antialias: true, preserveDrawingBuffer: true });
    ren.setPixelRatio(1); ren.setSize(W, H, false); ren.setClearColor(T3.fundo, 1);
    ren.shadowMap.enabled = true; ren.shadowMap.type = T.PCFSoftShadowMap;
    ren.outputColorSpace = T.SRGBColorSpace; ren.toneMapping = T.ACESFilmicToneMapping; ren.toneMappingExposure = 1.05;
    const sc = new T.Scene(); sc.fog = new T.Fog(T3.fundo, 30, 75);
    const cam = new T.PerspectiveCamera(38, W / H, .1, 300), DIST = P.estudio_dist ?? 1.85;
    cam.setViewOffset(W, H, 0, -H * (P.estudio_desce ?? .1), W, H);   // o assunto desce: a parte de cima é do cartão
    sc.add(new T.HemisphereLight(T3.ceu || 0xc9c0e0, 0x0b0810, .7));
    const dirL = new T.DirectionalLight(0xffffff, .5); dirL.position.set(4, 10, 6); sc.add(dirL);
    const chao = new T.Mesh(new T.PlaneGeometry(600, 600), new T.MeshStandardMaterial({ color: T3.chao, roughness: .92 }));
    chao.rotation.x = -Math.PI / 2; chao.receiveShadow = true; sc.add(chao);
    const corA = new T.Color(COR);
    const mObj = new T.MeshStandardMaterial({ color: T3.objeto, roughness: .55 }), mEsc = new T.MeshStandardMaterial({ color: T3.escuro, roughness: .7 });
    const mCinza = new T.MeshStandardMaterial({ color: T3.cinza, roughness: .7 });
    const mAcesa = () => new T.MeshStandardMaterial({ color: COR, emissive: corA, emissiveIntensity: .55, roughness: .4 });
    const caixa = (w, h, d, m, x = 0, y = 0, z = 0) => { const o = new T.Mesh(new T.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.castShadow = o.receiveShadow = true; return o; };
    const cil = (rt, rb, h, m, seg = 24) => { const o = new T.Mesh(new T.CylinderGeometry(rt, rb, h, seg), m); o.castShadow = o.receiveShadow = true; return o; };
    // texto em plano (CanvasTexture); linhas: [{t, tam, cor, peso, mono}]
    function placaTexto(linhas, larg, alt, fundo) {
      const k = 256, c = document.createElement("canvas"); c.width = Math.round(larg * k); c.height = Math.round(alt * k); const x = c.getContext("2d");
      if (fundo) { x.fillStyle = fundo; x.fillRect(0, 0, c.width, c.height); }
      const tot = linhas.reduce((s, l) => s + l.tam * k * 1.18, 0); let y = (c.height - tot) / 2;
      linhas.forEach(l => { let fs = l.tam * k; const fonte = f => `${l.peso || 800} ${f}px ${l.mono ? "'JetBrains Mono'" : `'${FONTE}'`}`;
        x.font = fonte(fs); const larg0 = x.measureText(l.t).width * (l.mono ? 1.12 : 1);
        if (larg0 > c.width * .9) { fs *= c.width * .9 / larg0; x.font = fonte(fs); }   // texto longo encolhe para caber
        x.fillStyle = l.cor || "#F2F2EE"; x.textAlign = "center"; x.textBaseline = "top";
        if (l.mono) x.letterSpacing = `${fs * .12}px`; x.fillText(l.t, c.width / 2, y + fs * .09); x.letterSpacing = "0px"; y += fs * 1.18; });
      const tx = new T.CanvasTexture(c); tx.colorSpace = T.SRGBColorSpace; tx.anisotropy = 4;
      const m = new T.MeshBasicMaterial({ map: tx, transparent: true, depthWrite: !!fundo, toneMapped: false });   // com fundo também: a opacidade anima a entrada
      return new T.Mesh(new T.PlaneGeometry(larg, alt), m);
    }
    // holofote: cone de luz aditivo + spot com sombra + anel no chão
    function holofote(grupo, x, z, raio = 1.1, alt = 9) {
      const cone = new T.Mesh(new T.CylinderGeometry(.18, raio * 1.15, alt, 40, 1, true),
        new T.MeshBasicMaterial({ color: T3.cone || COR, transparent: true, opacity: T3.cone ? .085 : .045, blending: T.AdditiveBlending, depthWrite: false, side: T.DoubleSide, toneMapped: false }));
      cone.position.set(x, alt / 2, z); grupo.add(cone);
      const sp = new T.SpotLight(T3.luz, 16, 24, .17, .6, 1.4); sp.position.set(x, alt, z); sp.target.position.set(x, 0, z);
      sp.castShadow = true; sp.shadow.mapSize.set(1024, 1024); grupo.add(sp, sp.target);
      const anelM = new T.MeshBasicMaterial({ color: COR, transparent: true, opacity: .85, toneMapped: false });
      const a = new T.Mesh(new T.RingGeometry(raio * .92, raio, 64), anelM); a.rotation.x = -Math.PI / 2; a.position.set(x, .012, z); grupo.add(a);
      const d = new T.Mesh(new T.CircleGeometry(raio * .92, 64), new T.MeshBasicMaterial({ color: T3.disco || COR, transparent: true, opacity: .16, toneMapped: false }));
      d.rotation.x = -Math.PI / 2; d.position.set(x, .011, z); grupo.add(d);
      return { cone, sp, anel: a, disco: d };
    }
    function boneco(cabeca = T3.objeto) {   // low-poly: corpo escuro, cabeça clara
      const b = new T.Group();
      const corpo = cil(.3, .42, 1.25, mEsc, 10); corpo.position.y = .82; b.add(corpo);
      const ombro = new T.Mesh(new T.SphereGeometry(.42, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2), mEsc); ombro.position.y = 1.42; ombro.scale.y = .45; ombro.castShadow = true; b.add(ombro);
      const pesc = cil(.1, .12, .18, new T.MeshStandardMaterial({ color: cabeca, roughness: .5 })); pesc.position.y = 1.6; b.add(pesc);
      const cab = new T.Mesh(new T.SphereGeometry(.3, 24, 16), new T.MeshStandardMaterial({ color: cabeca, roughness: .45 })); cab.position.y = 1.9; cab.castShadow = true; b.add(cab);
      const pe = cil(.34, .36, .12, mEsc, 10); pe.position.y = .06; b.add(pe);
      return b;
    }
    const cenas3d = [];   // {c, grupo, origem, upd(t), pose}
    let slot = 0;
    cenas.forEach((c, i) => { if (!c._3d) return;
      const grupo = new T.Group(), O = new T.Vector3(slot * 46, 0, -(slot % 2) * 8); slot++;
      grupo.position.copy(O); sc.add(grupo);
      // parede ao fundo de cada canto do estúdio
      const par = new T.Mesh(new T.PlaneGeometry(44, 20), new T.MeshStandardMaterial({ color: T3.parede, roughness: .95 }));
      par.position.set(0, 10, -11); par.receiveShadow = true; grupo.add(par);
      if (T3.vinheta) { const vc = document.createElement("canvas"); vc.width = vc.height = 256; const vx = vc.getContext("2d"), rg = vx.createRadialGradient(128, 128, 0, 128, 128, 128);
        rg.addColorStop(0, T3.vinheta); rg.addColorStop(1, "rgba(0,0,0,0)"); vx.fillStyle = rg; vx.fillRect(0, 0, 256, 256);
        const vt = new T.CanvasTexture(vc); vt.colorSpace = T.SRGBColorSpace;
        const vi = new T.Mesh(new T.PlaneGeometry(26, 20), new T.MeshBasicMaterial({ map: vt, transparent: true, depthWrite: false, toneMapped: false }));
        vi.position.set(0, 6, -10.9); grupo.add(vi); }   // vinheta roxa do site atrás do cenário
      const item = { c, i, grupo, O, upd: () => {}, pose: { pos: [0, 2.8, 9], alvo: [0, 1.4, 0] } };
      const em = (v, padrao) => v == null ? c.de + padrao : v;
      if (c.tipo === "palco") {
        holofote(grupo, 0, 0, 1.15);
        const bo = boneco(); bo.position.set(0, 0, -.35); grupo.add(bo);
        const pul = caixa(1.25, 1.12, .75, mObj, 0, .56, .35); grupo.add(pul);
        if (c.placa) { const pt = placaTexto([{ t: c.placa, tam: .14, cor: "#1a1420", mono: true }], 1.05, .3, COR); pt.position.set(0, .78, .73); grupo.add(pt); }
        const placas = montaPlacas(grupo, c.placas || [], 1.95, em);
        item.pose = { pos: [1.3, 2.3, 7.4], alvo: [0.95, 1.3, 0] };
        item.upd = t => { placas(t); bo.rotation.y = Math.sin(t * .6) * .08; };
      } else if (c.tipo === "disjuntor") {
        holofote(grupo, 0, .4, 1.9);
        const quadro = caixa(2.3, 3.0, .35, mEsc, 0, 1.75, 0); grupo.add(quadro);
        const base = caixa(2.6, .24, 1.1, mCinza, 0, .12, .1); grupo.add(base);
        const haste = caixa(.22, .5, .3, mCinza, 0, .25 + .1, 0); void haste;
        if (c.rotulo_caixa) { const pt = placaTexto([{ t: c.rotulo_caixa, tam: .3, cor: "#1a1420", mono: true }], 1.4, .42, COR); pt.position.set(0, 2.92, .181); grupo.add(pt); }
        const fenda = caixa(.5, 1.3, .06, new T.MeshStandardMaterial({ color: "#0d0a10" }), 0, 1.75, .19); grupo.add(fenda);
        const piv = new T.Group(); piv.position.set(0, 1.75, .22); grupo.add(piv);
        const alav = caixa(.34, 1.1, .24, mObj, 0, .5, .1); piv.add(alav);
        const pega = caixa(.6, .26, .34, mAcesa(), 0, 1.05, .14); piv.add(pega);
        const tON = placaTexto([{ t: "ON", tam: .2, cor: COR, mono: true }], .6, .3); tON.position.set(.62, 2.35, .19); grupo.add(tON);
        const tOFF = placaTexto([{ t: "OFF", tam: .2, cor: T3.off, mono: true }], .6, .3); tOFF.position.set(.62, 1.15, .19); grupo.add(tOFF);
        // telão de candles ao lado: acende e apaga com a chave
        const telao = new T.Group(); telao.position.set(-2.55, 0, -.6); grupo.add(telao);
        telao.add(caixa(2.6, 2.1, .2, mEsc, 0, 2.0, 0));
        const velas = []; for (let k = 0; k < 9; k++) { const h = .35 + .9 * Math.abs(Math.sin(k * 1.7 + 1)), y = 1.35 + .25 * Math.sin(k * .9) + h / 2;
          const vc = T3.vela_alta ? (k % 3 === 1 ? T3.vela_baixa : T3.vela_alta) : COR, vm = new T.MeshStandardMaterial({ color: vc, emissive: new T.Color(vc), emissiveIntensity: .55, roughness: .4 });
          const v = caixa(.16, h, .06, vm, -1.0 + k * .25, y, .13); v.userData.cor = vc; telao.add(v); velas.push(v); }
        // relógio
        const rel = new T.Group(); rel.position.set(2.3, 2.4, -.3); grupo.add(rel);
        const face = cil(.75, .75, .12, mObj, 48); face.rotation.x = Math.PI / 2; rel.add(face);
        const aro = new T.Mesh(new T.TorusGeometry(.76, .06, 10, 48), mEsc); aro.position.z = .02; rel.add(aro);
        const pH = new T.Group(), pM = new T.Group(); pH.position.z = pM.position.z = .09; rel.add(pH, pM);
        const ponH = caixa(.07, .38, .03, mEsc, 0, .17, 0); pH.add(ponH); const ponM = caixa(.05, .58, .03, mAcesa(), 0, .27, 0); pM.add(ponM);
        for (let k = 0; k < 12; k++) { const m = caixa(.04, .11, .02, mEsc, Math.sin(k * Math.PI / 6) * .62, Math.cos(k * Math.PI / 6) * .62, .07); rel.add(m); }
        const suporte = caixa(.12, 1.7, .12, mCinza, 2.3, .85, -.3); grupo.add(suporte);
        const tDes = em(c.desliga, 1.5), tRel = c.religa;
        const h0 = (c.relogio && c.relogio.de) || "10:00", h1 = (c.relogio && c.relogio.para) || "10:30";
        const mins = s => { const [a, b] = s.split(":").map(Number); return a * 60 + b; };
        const faisca = []; for (let k = 0; k < 18; k++) { const f = caixa(.05, .05, .05, mAcesa(), 0, 0, 0); f.visible = false; grupo.add(f);
          faisca.push({ f, vx: (rnd3() - .5) * 3.2, vy: 1.2 + rnd3() * 2.6, vz: .6 + rnd3() * 1.6 }); }
        item.pose = { pos: [-.2, 2.9, 11.2], alvo: [-.2, 1.7, 0] };
        item.upd = t => {
          const kOff = eback(prog(t, tDes, .35)), kOn = tRel != null ? eback(prog(t, tRel, .4)) : 0, off = kOff * (1 - kOn);
          piv.rotation.x = -.55 + 1.1 * off;   // para cima = ligado; vira para baixo
          const ligado = 1 - off; velas.forEach((v, k) => { const pisca = t > tDes && t < tDes + .5 ? (Math.sin(t * 60 + k) > 0 ? 1 : .2) : 1;
            v.material.emissiveIntensity = .05 + .6 * ligado * pisca; v.material.color.set(ligado > .5 ? v.userData.cor : "#2a2230"); });
          pega.material.emissiveIntensity = .1 + .5 * ligado;
          const kr = prog(t, tDes, tRel != null ? Math.max(.5, tRel - tDes) : 2.5), m = mins(h0) + (mins(h1) - mins(h0)) * eio(kr);
          pM.rotation.z = -((m % 60) / 60) * Math.PI * 2; pH.rotation.z = -(((m / 60) % 12) / 12) * Math.PI * 2;
          const tf = t - tDes; faisca.forEach(o => { o.f.visible = tf > 0 && tf < .9; if (!o.f.visible) return;
            o.f.position.set(o.vx * tf, 1.75 + o.vy * tf - 4.9 * tf * tf, .5 + o.vz * tf); });
        };
      } else if (c.tipo === "barras") {
        const bs = c.barras || [], n = bs.length, esp = 1.55, x0 = -(n - 1) * esp / 2, max = c.max || Math.max(...bs.map(b => b.valor)), HM = c.altura || 3.6;
        holofote(grupo, 0, 0, Math.max(1.6, n * .8));
        const teto = caixa(n * esp + .6, .03, .03, new T.MeshBasicMaterial({ color: "#d8d2e0", transparent: true, opacity: .45 }), 0, HM, .5); grupo.add(teto);
        const objs = bs.map((b, k) => { const m = b.destaque ? mAcesa() : mObj.clone(), x = x0 + k * esp;
          const bar = caixa(.95, 1, .95, m, x, .5, 0); grupo.add(bar);
          const rot = placaTexto([{ t: b.rotulo || "", tam: .19, cor: "#E9E4EE", mono: true }], 1.5, .34); rot.position.set(x, .03, 1.05); rot.rotation.x = -1.2; grupo.add(rot);
          const val = placaTexto([{ t: b.texto || String(b.valor), tam: .34, cor: b.destaque ? COR : "#F2F2EE" }], 1.8, .5); grupo.add(val);
          return { bar, val, b, x, t0: em(b.em, .4 + k * .5) }; });
        item.pose = { pos: [0, 3.0, 11.5], alvo: [0, 1.9, 0] };
        item.upd = t => objs.forEach(o => { const k = eback(prog(t, o.t0, 1.0)), de = o.b.de != null ? o.b.de : 0;
          const h = Math.max(.02, HM * (de + (o.b.valor - de) * k) / max); o.bar.scale.y = h; o.bar.position.y = h / 2;
          o.val.position.set(o.x, h + .38, 0); o.val.material.opacity = eout(prog(t, o.t0 + .5, .5)); o.val.lookAt(cam.position); });
      } else if (c.tipo === "blocos") {
        holofote(grupo, 0, 0, 3.2);
        const n = c.n || 120, cols = c.colunas || 12, lin = Math.ceil(n / cols), sz = .36, gap = .48, arco = c.forma === "arco";
        const bl = []; for (let k = 0; k < n; k++) { const r = Math.floor(k / cols), q = k % cols; let x, z;
          if (arco) { const raio = 2.2 + r * .55, a = Math.PI * (.08 + .84 * q / (cols - 1)); x = -Math.cos(a) * raio; z = -Math.sin(a) * raio + 2.2; }
          else { x = (q - (cols - 1) / 2) * gap; z = (r - (lin - 1) / 2) * gap; }
          const m = new T.MeshStandardMaterial({ color: T3.objeto, roughness: .6, emissive: corA, emissiveIntensity: 0 });
          const b = caixa(sz, sz * .7, sz, m, x, sz * .35, z); grupo.add(b); bl.push({ b, x, z, ordem: rnd3(), cai: rnd3() }); }
        const ordem = bl.slice().sort((a, b) => a.ordem - b.ordem);
        const ac = c.acende, ca = c.cai, nA = ac ? Math.round(n * ac.fracao) : 0, nC = ca ? Math.round(n * ca.fracao) : 0;
        const tA = ac ? em(ac.em, .6) : 0, tC = ca ? em(ca.em, .6) : 0;
        ordem.forEach((o, k) => { o.acende = k < nA; o.caiK = k >= n - nC; o.atraso = (k / Math.max(1, n)) * .9; });
        item.pose = { pos: [0, 7.2, 8.6], alvo: [0, 0, -.2] };
        item.upd = t => bl.forEach(o => {
          const ka = o.acende ? eout(prog(t, tA + o.atraso * 1.1, .35)) : 0;
          o.b.material.color.set(ka > .5 ? COR : T3.objeto); o.b.material.emissiveIntensity = .5 * ka;
          if (o.caiK) { const tt = Math.max(0, t - tC - o.cai * 1.0); o.b.position.y = sz * .35 - 4.9 * tt * tt * 1.4; o.b.rotation.x = tt * 3 * (o.cai - .5); o.b.visible = o.b.position.y > -1;
            if (tt > 0) o.b.material.color.set(T3.queda); } });
      } else if (c.tipo === "placas") {
        const upd = montaPlacas(grupo, c.placas || [], 0, em);
        holofote(grupo, 0, .2, Math.max(1.6, (c.placas || []).length * .9));
        item.pose = { pos: [0, 2.5, 9.6], alvo: [0, 1.3, 0] };
        item.upd = upd;
      } else if (c.tipo === "duelo") {
        // duas pessoas lado a lado: foto em moldura sobre pedestal (altura pelo número), nome em cima, valor na frente
        const L = c.lados || [], esp = 2.7, x0 = -(L.length - 1) * esp / 2, maxv = Math.max(...L.map(l => l.num || 1));
        const objs = L.map((l, k) => { const x = x0 + k * esp, gq = new T.Group(); gq.position.set(x, 0, 0); grupo.add(gq);
          holofote(grupo, x, 0, 1.0);
          const hp = .35 + 1.0 * ((l.num || maxv) / maxv);
          const ped = caixa(1.5, 1, 1.0, l.destaque ? mAcesa() : mEsc, 0, .5, 0); gq.add(ped);
          const quadro = new T.Group(); gq.add(quadro);
          quadro.add(caixa(1.62, 1.97, .08, l.destaque ? mAcesa() : mObj, 0, 0, -.03));
          const im = FOTOS[l.foto];
          if (im) { const tx = new T.Texture(im); tx.colorSpace = T.SRGBColorSpace; tx.needsUpdate = true;
            const ar = 1.5 / 1.85, iar = im.width / im.height;   // recorte "cover", sem distorcer o rosto
            if (iar > ar) { tx.repeat.set(ar / iar, 1); tx.offset.set((1 - ar / iar) / 2, 0); } else { tx.repeat.set(1, iar / ar); tx.offset.set(0, 1 - iar / ar); }
            const f = new T.Mesh(new T.PlaneGeometry(1.5, 1.85), new T.MeshBasicMaterial({ map: tx, toneMapped: false })); f.position.z = .02; quadro.add(f); }
          const nome = placaTexto([{ t: l.nome || "", tam: .22, cor: "#F2F2EE" }], 1.7, .32); gq.add(nome);
          const val = placaTexto([{ t: l.valor || "", tam: .3, cor: l.destaque ? "#1a1420" : "#F2F2EE" }], 1.4, .42); gq.add(val);
          const selo = l.selo ? placaTexto([{ t: l.selo, tam: .13, cor: "#1a1420", mono: true }], 1.6, .26, l.destaque ? COR : "#F7F7F7") : null; if (selo) gq.add(selo);
          return { gq, ped, quadro, nome, val, selo, hp, t0: em(l.em, .4 + k * .3), tv: em(l.em_valor ?? l.em, .9 + k * .3) }; });
        item.pose = { pos: [0, 2.3, 10.2], alvo: [0, 2.0, 0] };
        item.upd = t => objs.forEach(o => { const k = eback(prog(t, o.t0, .6)), kv = eout(prog(t, o.tv, 1.0)), h = .15 + o.hp * kv;
          o.ped.scale.y = h; o.ped.position.y = h / 2;
          o.quadro.position.y = h + 1.08; o.quadro.scale.setScalar(Math.max(.001, k)); o.quadro.rotation.y = (1 - k) * .6;
          o.nome.position.set(0, h + 2.32, .05); o.nome.material.opacity = eout(prog(t, o.t0 + .2, .4));
          o.val.position.set(0, Math.max(.22, h / 2), .52); o.val.material.opacity = eout(prog(t, o.tv + .5, .4));
          if (o.selo) { o.selo.position.set(0, h + 2.66, .06); o.selo.material.opacity = eout(prog(t, o.tv + .7, .4)); } });
      } else if (c.tipo === "grafico") {
        // candles de um índice: caem até a linha do limite, pausa (vão com etiqueta), voltam a cair; "?" no futuro
        const n = c.velas || 14, v0 = c.inicio ?? 100, lim = c.limite, vFim = c.valor_final ?? (lim ? lim.valor - 5 : v0 - 10), vL = lim ? lim.valor : vFim;
        const tA = em(c.inicio_em, .3), tL = lim ? em(lim.em, 3) : tA + 3, tP = c.pausa ? em(c.pausa.em, tL - c.de + .3) : tL;
        const tR = c.retoma ? em(c.retoma.em, tP - c.de + 2) : tP + .8, tF = c.fim_em ?? c.ate - .6;
        const nA = c.pausa || lim ? Math.round(n * .55) : n, nB = n - nA;
        const L2 = c.limite_novo, vals = [v0, vL, vFim].concat(L2 ? [L2.valor] : []), vmin = Math.min(...vals) - 2, vmax = Math.max(...vals) + 1, HY = 3.3, y = v => .3 + (v - vmin) / (vmax - vmin) * HY;
        const gap = c.pausa ? 1.3 : 0, w = .2, passo = .3, xIni = -(n * passo + gap) / 2;
        const vel = []; let prev = v0;
        for (let k = 0; k < n; k++) { const antes = k < nA, fr = antes ? (k + 1) / nA : (k - nA + 1) / Math.max(1, nB);
          const alvo = antes ? v0 + (vL - v0) * fr : vL + (vFim - vL) * fr;
          const close = alvo + ((k === nA - 1 || k === n - 1) ? 0 : Math.sin(k * 2.3) * .45), open = prev, cor = close > open ? (T3.vela_alta || COR) : (T3.vela_baixa || "#DC2626");
          const m = new T.MeshStandardMaterial({ color: cor, emissive: new T.Color(cor), emissiveIntensity: .45, roughness: .4 });
          const x = xIni + k * passo + (antes ? 0 : gap), yb = y(Math.min(open, close)), hb = Math.max(.05, Math.abs(y(close) - y(open)));
          const corpo = caixa(w, hb, w, m, x, yb + hb / 2, 0), pav = caixa(.03, hb + .32, .03, m, x, yb + hb / 2, 0); grupo.add(corpo, pav);
          const tk = c.completo ? c.de - 5 : (antes ? tA + (tL - tA) * (k / nA) : tR + (tF - tR) * ((k - nA) / Math.max(1, nB)));
          vel.push({ corpo, pav, tk }); prev = close; }
        grupo.add(caixa(n * passo + gap + .7, .02, 1.0, mEsc, 0, .01, 0)); holofote(grupo, 0, 0, (n * passo + gap) / 2 + .4);
        const vermelho = T3.vela_baixa || "#DC2626";
        const linha = lim ? caixa(n * passo + gap + .9, .035, .035, new T.MeshBasicMaterial({ color: vermelho, toneMapped: false }), 0, y(vL), .25) : null;
        const tagL = lim ? placaTexto([{ t: lim.texto || "", tam: .14, cor: "#F7F7F7", mono: true }], 2.7, .3, vermelho) : null;
        if (linha) { grupo.add(linha, tagL); tagL.position.set(xIni + 1.4, y(vL) + (vFim > v0 ? .32 : -.32), .3); }
        // limite que muda no meio do dia (ex.: B3 amplia a oscilação de 6% para 12%): linha nova acima, a velha apaga
        const linha2 = L2 ? caixa(n * passo + gap + .9, .035, .035, new T.MeshBasicMaterial({ color: COR, toneMapped: false }), 0, y(L2.valor), .25) : null;
        const tag2 = L2 ? placaTexto([{ t: L2.texto || "", tam: .14, cor: "#1a1420", mono: true }], 2.7, .3, COR) : null;
        if (linha2) { grupo.add(linha2, tag2); tag2.position.set(xIni + 1.4, y(L2.valor) + .32, .3); }
        const tL2 = L2 ? em(L2.em, tL - c.de + 1.5) : 0;
        const pz = c.pausa ? placaTexto([{ t: c.pausa.texto || "PAUSA", tam: .15, cor: "#1a1420", mono: true }], 1.45, .3, COR) : null;
        if (pz) { pz.position.set(xIni + nA * passo + gap / 2 - passo / 2, y(vL) + .45, .3); grupo.add(pz); }
        const fut = c.futuro ? placaTexto([{ t: "?", tam: .95, cor: COR }], 1.2, 1.2) : null;
        if (fut) { fut.position.set(xIni + n * passo + gap + .55, y(vFim) + .2, .1); grupo.add(fut); }
        item.pose = { pos: [.4, 2.4, 13.0], alvo: [.4, 1.9, 0] };
        item.upd = t => { vel.forEach(v => { const k = eback(prog(t, v.tk, .3)); v.corpo.visible = v.pav.visible = t >= v.tk;
            v.corpo.scale.y = v.pav.scale.y = Math.max(.001, k); });
          if (linha) { const kl = c.completo ? 1 : eout(prog(t, tL - .25, .5)), apaga = L2 ? .65 * eout(prog(t, tL2, .5)) : 0;
            linha.scale.x = Math.max(.001, kl); tagL.material.opacity = kl * (1 - apaga); linha.material.transparent = true; linha.material.opacity = 1 - apaga; }
          if (linha2) { const k2 = c.completo ? 1 : eout(prog(t, tL2, .5)); linha2.scale.x = Math.max(.001, k2); tag2.material.opacity = k2; }
          if (pz) pz.material.opacity = c.completo ? 1 : eout(prog(t, tP, .4));
          if (fut) fut.material.opacity = eout(prog(t, c.futuro_em ?? c.de + 1.0, .6)) * (.8 + .2 * Math.sin(t * 4)); };
      } else if (c.tipo === "pregao") {
        // prédio da bolsa: colunas, janelas acesas, letreiro de cotações correndo; na palavra as luzes apagam e cai a placa
        holofote(grupo, 0, .3, 2.7);
        grupo.add(caixa(4.8, .3, 2.3, mCinza, 0, .15, 0), caixa(4.3, .22, 2.0, mObj, 0, .41, .05), caixa(3.9, 2.6, 1.3, mEsc, 0, 1.82, -.25));
        for (let k = 0; k < 5; k++) { const col = cil(.13, .15, 2.45, mObj, 16); col.position.set(-1.6 + k * .8, 1.75, .6); grupo.add(col); }
        grupo.add(caixa(4.2, .36, 1.5, mObj, 0, 3.15, 0));
        const nomeP = placaTexto([{ t: c.nome_predio || "B3", tam: .22, cor: "#1a1420", mono: true }], 1.2, .3, COR); nomeP.position.set(0, 3.15, .76); grupo.add(nomeP);
        const jan = []; for (let k = 0; k < 4; k++) for (let r = 0; r < 2; r++) { const m = mAcesa(); const j = caixa(.42, .62, .04, m, -1.2 + k * .8, 1.2 + r * .95, .42); grupo.add(j); jan.push(j); }
        const tc = document.createElement("canvas"); tc.width = 2048; tc.height = 64; const tx2 = tc.getContext("2d");
        tx2.fillStyle = "#0d0a10"; tx2.fillRect(0, 0, 2048, 64); tx2.font = "700 40px 'JetBrains Mono'"; tx2.fillStyle = COR; tx2.textBaseline = "middle";
        const fita = (c.ticker || "IBOV ▼  PETR4 ▼  VALE3 ▼  ITUB4 ▼  BBAS3 ▼") + "   ✦   "; tx2.fillText(fita + fita + fita, 10, 34);
        const ttx = new T.CanvasTexture(tc); ttx.colorSpace = T.SRGBColorSpace; ttx.wrapS = T.RepeatWrapping; ttx.repeat.x = .45;
        const tick = new T.Mesh(new T.PlaneGeometry(3.7, .26), new T.MeshBasicMaterial({ map: ttx, transparent: true, toneMapped: false })); tick.position.set(0, 2.82, .72); grupo.add(tick);
        const susp = placaTexto([{ t: c.placa_fechado || "PREGÃO SUSPENSO", tam: .17, cor: "#F7F7F7", mono: true }], 2.6, .42, T3.vela_baixa || "#DC2626"); grupo.add(susp);
        const tA = em(c.apaga, 2.5);
        item.pose = { pos: [0, 2.5, 10.8], alvo: [0, 1.85, 0] };
        item.upd = t => { const pisca = t > tA - .5 && t < tA ? (Math.sin(t * 70) > 0 ? 1 : .25) : 1, on = t < tA ? pisca : 0;
          jan.forEach((j, k) => { j.material.color.set(on > .5 ? COR : "#221a2a"); j.material.emissiveIntensity = .05 + .55 * on * (t < tA ? 1 : Math.max(0, 1 - (t - tA) * 4 - k * .1)); });
          ttx.offset.x = t < tA ? (t * .06) % 1 : (tA * .06) % 1; tick.material.opacity = t < tA ? 1 : .25;
          const ks = eback(prog(t, tA + .25, .5)); susp.position.set(0, 4.8 - 2.6 * ks, 1.0); susp.material.opacity = ks > 0 ? 1 : 0; };
      } else if (c.tipo === "elevador") {
        // elevador do índice: desce andar por andar (%), o freio de emergência trava os trilhos, depois volta a descer
        const HH = 5.4, n = (c.andares || ["0%", "−5%", "−10%", "−15%"]).length, nomes = c.andares || ["0%", "−5%", "−10%", "−15%"];
        holofote(grupo, 0, .2, 1.7);
        grupo.add(caixa(2.4, HH, .1, mEsc, 0, HH / 2, -.7), caixa(.1, HH, .14, mCinza, -.95, HH / 2, -.45), caixa(.1, HH, .14, mCinza, .95, HH / 2, -.45));
        const yTop = HH - 1.05, yEnd = .85, yAnd = k => yTop - (yTop - yEnd) * k / (n - 1);
        nomes.forEach((nm, k) => { const p = placaTexto([{ t: nm, tam: .17, cor: k ? "#F2F2EE" : COR, mono: true }], .9, .3); p.position.set(-1.7, yAnd(k) + .2, -.55); grupo.add(p);
          grupo.add(caixa(.5, .03, .03, mCinza, -1.3, yAnd(k), -.55)); });
        const carro = new T.Group(); grupo.add(carro);
        carro.add(caixa(1.5, 1.3, 1.1, mObj, 0, 0, 0), caixa(.9, .7, .02, new T.MeshStandardMaterial({ color: "#141016" }), 0, .05, .56));
        const disp = nomes.map(nm => { const p = placaTexto([{ t: nm, tam: .2, cor: COR, mono: true }], .9, .3, "#141016"); p.position.set(0, .82, .2); p.visible = false; carro.add(p); return p; });
        const dispQ = placaTexto([{ t: "?", tam: .24, cor: COR, mono: true }], .9, .3, "#141016"); dispQ.position.set(0, .82, .2); dispQ.visible = false; carro.add(dispQ);
        const vermelho = T3.vela_baixa || "#DC2626", mF = new T.MeshStandardMaterial({ color: vermelho, emissive: new T.Color(vermelho), emissiveIntensity: .5 });
        const garraE = caixa(.32, .36, .5, mF, 0, 0, -.45), garraD = caixa(.32, .36, .5, mF, 0, 0, -.45); grupo.add(garraE, garraD);
        const plF = c.freio ? placaTexto([{ t: c.freio.texto || "FREIO DE EMERGÊNCIA", tam: .15, cor: "#F7F7F7", mono: true }], 2.6, .36, vermelho) : null; if (plF) grupo.add(plF);
        const tI = em(c.inicio_em, .3), tF = c.freio ? em(c.freio.em, 3) : tI + 3, tR = c.retoma ? em(c.retoma.em, tF - c.de + 2) : tF, tE = c.fim_em ?? c.ate - .4;
        const parada = c.parada ?? .5, yB = yTop - (yTop - yEnd) * parada;
        const posY = t => { if (c.completo) return yEnd; if (t < tI) return yTop;
          if (t < tF) { const k = prog(t, tI, tF - tI); return yTop - (yTop - yB) * k * k; }
          if (t < tR) return yB; return yB - (yB - yEnd) * eio(prog(t, tR, Math.max(.5, tE - tR))); };
        item.pose = { pos: [0, 2.9, 11.6], alvo: [0, 2.6, 0] };
        item.upd = t => { let y = posY(t); const choque = t > tF && t < tF + .5 ? Math.sin((t - tF) * 60) * .06 * (1 - (t - tF) / .5) : 0;
          carro.position.set(choque, y, 0);
          const k = Math.round((yTop - y) / (yTop - yEnd) * (n - 1)); disp.forEach((d, i) => d.visible = !c.completo && i === Math.max(0, Math.min(n - 1, k))); dispQ.visible = !!c.completo;
          const kg = c.freio ? (c.completo ? 1 : eback(prog(t, tF, .2)) * (1 - eout(prog(t, tR, .3)))) : 0, gx = 1.35 - .3 * kg;
          garraE.position.set(-gx, y + .45, -.45); garraD.position.set(gx, y + .45, -.45); garraE.visible = garraD.visible = kg > .01;
          if (plF) { plF.position.set(0, y + 1.3, .3); plF.material.opacity = kg; } };
      } else if (c.tipo === "placar") {
        // placar de LED: título e linhas que viram na palavra (rótulo + valor)
        const L = c.linhas || [], hB = .55 + L.length * .62, yB = 2.2 + hB / 2;
        holofote(grupo, 0, .2, 2.3);
        grupo.add(caixa(.16, yB, .16, mCinza, -1.75, yB / 2, -.1), caixa(.16, yB, .16, mCinza, 1.75, yB / 2, -.1), caixa(4.0, hB, .25, mEsc, 0, yB, 0));
        if (c.titulo) { const tt = placaTexto([{ t: c.titulo, tam: .16, cor: "#1a1420", mono: true }], 2.8, .34, COR); tt.position.set(0, yB + hB / 2 + .25, .05); grupo.add(tt); }
        const lin = L.map((l, k) => { const g2 = new T.Group(); g2.position.set(0, yB + hB / 2 - .5 - k * .62, .14); grupo.add(g2);
          g2.add(caixa(3.7, .5, .02, new T.MeshStandardMaterial({ color: "#1d1526" }), 0, 0, 0));
          const r = placaTexto([{ t: l.rotulo || "", tam: .17, cor: "#F2F2EE", mono: true }], 2.0, .4); r.position.set(-.8, 0, .02); g2.add(r);
          const cor = l.cor === "queda" ? (T3.vela_baixa || "#DC2626") : l.cor === "alta" ? (T3.vela_alta || COR) : COR;
          const v = placaTexto([{ t: l.valor || "", tam: .26, cor }], 1.5, .44); v.position.set(1.05, 0, .02); g2.add(v);
          return { g2, t0: em(l.em, .4 + k * .6) }; });
        item.pose = { pos: [0, 2.7, 10.4], alvo: [0, yB, 0] };
        item.upd = t => lin.forEach(o => { o.g2.scale.y = Math.max(.001, eback(prog(t, o.t0, .35))); });
      } else if (c.tipo === "calculadora") {
        // calculadora do mercado: o visor troca de conta na palavra e uma tecla afunda
        holofote(grupo, 0, 0, 1.6);
        const calc = new T.Group(); calc.position.set(0, 1.9, 0); calc.rotation.x = -.18; grupo.add(calc);
        calc.add(caixa(2.3, 3.1, .32, mEsc, 0, 0, 0)); grupo.add(caixa(.5, 1.0, .5, mCinza, 0, .5, -.2));
        const teclas = []; for (let r = 0; r < 4; r++) for (let q = 0; q < 4; q++) { const m = (q === 3) ? mAcesa() : mObj; const k = caixa(.42, .38, .12, m, -.72 + q * .48, -.55 - r * .46, .2); calc.add(k); teclas.push(k); }
        const telas = (c.linhas || []).map(l => { const p = placaTexto([{ t: l.texto, tam: .15, cor: COR, mono: true }], 1.95, .62, "#141016"); p.position.set(0, .95, .17); p.visible = false; calc.add(p); return { p, t0: em(l.em, .5) }; });
        item.pose = { pos: [0, 2.5, 9.6], alvo: [0, 1.95, 0] };
        item.upd = t => { let atual = -1; telas.forEach((o, k) => { if (t >= o.t0) atual = k; }); telas.forEach((o, k) => o.p.visible = k === atual);
          teclas.forEach((k, i) => { const tq = telas.find((o, j) => (i * 7 + j * 5) % 16 === 0 && t >= o.t0 && t < o.t0 + .25); k.position.z = tq ? .12 : .2; }); };
      } else if (c.tipo === "barco") {
        // o barco no mar da notícia: as ondas crescem na palavra, o barco segue firme com a vela da disciplina
        holofote(grupo, 0, 0, 2.6);
        const geo = new T.PlaneGeometry(10, 6, 40, 24); geo.rotateX(-Math.PI / 2);
        const mar = new T.Mesh(geo, new T.MeshStandardMaterial({ color: T3.escuro, roughness: .5, flatShading: true, emissive: new T.Color(T3.cone || COR), emissiveIntensity: .06 })); mar.position.y = .4; grupo.add(mar);
        const base = geo.attributes.position.array.slice();
        const barco = new T.Group(); grupo.add(barco);
        barco.add(caixa(1.9, .42, .75, mObj, 0, 0, 0), caixa(.08, 1.9, .08, mCinza, 0, 1.15, 0));
        const proa = new T.Mesh(new T.ConeGeometry(.38, .6, 4), mObj); proa.rotation.z = -Math.PI / 2; proa.position.set(1.22, 0, 0); proa.rotation.x = Math.PI / 4; barco.add(proa);
        const vela = placaTexto([{ t: c.vela || "DISCIPLINA", tam: .13, cor: "#1a1420", mono: true }], 1.25, 1.3, COR); vela.position.set(-.05, 1.3, .06); barco.add(vela);
        const boia = placaTexto([{ t: c.boia || "NOTÍCIA", tam: .16, cor: "#F7F7F7", mono: true }], 1.3, .34, T3.vela_baixa || "#DC2626"); grupo.add(boia);
        const tN = em(c.noticia_em, 1), tD = em(c.disciplina_em, 4);
        item.pose = { pos: [0, 3.0, 10.2], alvo: [0, 1.2, 0] };
        item.upd = t => { const A = .07 + .38 * eout(prog(t, tN, 1.0)) * (1 - .55 * eout(prog(t, tD, 1.5)));
          const a = geo.attributes.position.array; for (let i = 0; i < a.length; i += 3) { const x = base[i], z = base[i + 2]; a[i + 1] = A * (Math.sin(x * 1.25 + t * 2.1) * Math.cos(z * 1.05 + t * 1.4)); }
          geo.attributes.position.needsUpdate = true; geo.computeVertexNormals();
          const firme = eout(prog(t, tD, .8)); barco.position.y = .55 + A * .35 * Math.sin(t * 2.1) * (1 - .7 * firme); barco.rotation.z = A * .5 * Math.sin(t * 1.7) * (1 - .8 * firme);
          vela.material.opacity = .55 + .45 * firme;
          boia.position.set(-1.9 + .2 * Math.sin(t), .9 + A * 1.6 * Math.sin(t * 2.6), 1.3); boia.rotation.z = A * 1.4 * Math.sin(t * 2.2); boia.material.opacity = eout(prog(t, tN, .4)); };
      } else if (c.tipo === "skyline") {
        // duas cidades lado a lado: uma apagada (fechada), outra acesa; lua no meio
        holofote(grupo, 0, 0, 3.0);
        const lados = [c.esquerda || {}, c.direita || {}], jan = [[], []];
        lados.forEach((l, s) => { const sx = s ? 1 : -1;
          for (let k = 0; k < 5; k++) { const h = 1.2 + 2.2 * Math.abs(Math.sin(k * 2.7 + s * 1.3)), w = .5 + .15 * ((k + s) % 2), x = sx * (.45 + k * .52);
            grupo.add(caixa(w, h, .6, mEsc, x, h / 2, -.2 - (k % 2) * .3));
            for (let r = 0; r < Math.floor(h / .32); r++) { const m = new T.MeshStandardMaterial({ color: "#221a2a", emissive: corA, emissiveIntensity: 0 }); const j = caixa(.12, .14, .02, m, x + (r % 2 ? .1 : -.1), .3 + r * .3, .11 - (k % 2) * .3); grupo.add(j); jan[s].push({ j, r: rnd3() }); } }
          const nm = placaTexto([{ t: l.nome || "", tam: .18, cor: "#F2F2EE", mono: true }], 2.2, .32); nm.position.set(sx * 1.55, -.05 + .02, 1.0); nm.rotation.x = -1.1; grupo.add(nm);
          if (l.placa) { const pl = placaTexto([{ t: l.placa, tam: .14, cor: l.acesa ? "#1a1420" : "#F7F7F7", mono: true }], 1.9, .32, l.acesa ? (T3.vela_alta || COR) : (T3.vela_baixa || "#DC2626")); pl.position.set(sx * 1.55, 4.1, .2); grupo.add(pl); jan[s].placa = pl; } });
        const lua = new T.Mesh(new T.SphereGeometry(.42, 24, 16), new T.MeshBasicMaterial({ color: "#F7F2E6", toneMapped: false })); lua.position.set(0, 4.6, -1.5); grupo.add(lua);
        const tA = em(c.acende_em, .6);
        item.pose = { pos: [0, 2.4, 12.2], alvo: [0, 2.1, 0] };
        item.upd = t => lados.forEach((l, s) => { jan[s].forEach(o => { const on = l.acesa ? eout(prog(t, tA + o.r * .8, .3)) * (o.r > .25 ? 1 : 0) : (o.r > .93 ? .3 : 0);
            o.j.material.color.set(on > .2 ? COR : "#221a2a"); o.j.material.emissiveIntensity = .55 * on; });
          if (jan[s].placa) jan[s].placa.material.opacity = eout(prog(t, tA + .6 + s * .3, .4)); });
      } else if (c.tipo === "cesta") {
        // a cesta do fundo (EWZ): cheia de empresas; na palavra parte delas pula para fora e o preço vira
        holofote(grupo, 0, 0, 1.9);
        const cesta = new T.Mesh(new T.CylinderGeometry(1.35, 1.05, 1.1, 32, 1, true), new T.MeshStandardMaterial({ color: T3.escuro, side: T.DoubleSide, roughness: .7 })); cesta.position.y = .55; grupo.add(cesta);
        const aro = new T.Mesh(new T.TorusGeometry(1.35, .05, 8, 48), mAcesa()); aro.rotation.x = Math.PI / 2; aro.position.y = 1.1; grupo.add(aro);
        const blocos = []; for (let k = 0; k < 34; k++) { const a = rnd3() * 6.28, r = rnd3() * .95, y = .25 + Math.floor(k / 12) * .3 + rnd3() * .1;
          const b = caixa(.26, .26, .26, k % 5 ? mObj : mAcesa(), Math.cos(a) * r, y, Math.sin(a) * r); grupo.add(b); blocos.push({ b, x: b.position.x, y, z: b.position.z, sai: rnd3() < (c.fracao ?? .2), vx: Math.cos(a) * (1.2 + rnd3()), vz: Math.sin(a) * .8 + .9, atr: rnd3() * .5 }); }
        const nm = placaTexto([{ t: c.rotulo_cesta || "EWZ", tam: .2, cor: "#1a1420", mono: true }], 1.1, .32, COR); nm.position.set(0, .55, 1.3); grupo.add(nm);
        const de = placaTexto([{ t: c.preco_de || "", tam: .28, cor: "#F2F2EE" }], 2.0, .5), para = placaTexto([{ t: c.preco_para || "", tam: .28, cor: T3.vela_baixa || "#DC2626" }], 2.0, .5);
        de.position.set(0, 2.15, .3); para.position.set(0, 2.15, .3); grupo.add(de, para);
        const tQ = em(c.em, 1.5);
        item.pose = { pos: [0, 3.4, 9.0], alvo: [0, 1.05, 0] };
        item.upd = t => { blocos.forEach(o => { if (!o.sai) return; const tt = Math.max(0, t - tQ - o.atr);
            const yy = o.y + 3.2 * tt - 4.9 * tt * tt; o.b.position.set(o.x + o.vx * tt, Math.max(.13, yy), o.z + o.vz * tt); o.b.rotation.set(tt * 4, tt * 3, 0); });
          const k = eout(prog(t, tQ + .2, .35)); de.rotation.x = k * Math.PI / 2; de.visible = k < .99; para.rotation.x = (1 - k) * -Math.PI / 2; para.visible = k > .01; };
      } else if (c.tipo === "relogios") {
        // dois relógios de cidades lado a lado com o status de cada mercado
        holofote(grupo, 0, 0, 2.6);
        const R = c.relogios || [], objs = R.map((r, s) => { const x = (s - (R.length - 1) / 2) * 2.7, g2 = new T.Group(); g2.position.set(x, 2.6, 0); grupo.add(g2);
          const face = cil(.95, .95, .14, mObj, 48); face.rotation.x = Math.PI / 2; g2.add(face);
          const aro = new T.Mesh(new T.TorusGeometry(.97, .07, 10, 48), r.ok ? mAcesa() : mEsc); aro.position.z = .03; g2.add(aro);
          for (let k = 0; k < 12; k++) g2.add(caixa(.05, .14, .02, mEsc, Math.sin(k * Math.PI / 6) * .78, Math.cos(k * Math.PI / 6) * .78, .09));
          const [hh, mm] = (r.hora || "12:00").split(":").map(Number), pH = new T.Group(), pM = new T.Group(); pH.position.z = pM.position.z = .1; g2.add(pH, pM);
          pH.add(caixa(.08, .48, .03, mEsc, 0, .2, 0)); pM.add(caixa(.06, .72, .03, mAcesa(), 0, .32, 0));
          pM.rotation.z = -(mm / 60) * 6.283; pH.rotation.z = -(((hh % 12) + mm / 60) / 12) * 6.283;
          grupo.add(caixa(.1, 1.7, .1, mCinza, x, .85, -.1));
          const nm = placaTexto([{ t: r.cidade || "", tam: .18, cor: "#F2F2EE", mono: true }], 2.2, .32); nm.position.set(x, 3.85, 0); grupo.add(nm);
          const hr = placaTexto([{ t: r.hora || "", tam: .2, cor: COR, mono: true }], 1.2, .32); hr.position.set(x, 1.38, .1); grupo.add(hr);
          const st = placaTexto([{ t: r.status || "", tam: .14, cor: r.ok ? "#1a1420" : "#F7F7F7", mono: true }], 2.0, .34, r.ok ? (T3.vela_alta || COR) : (T3.vela_baixa || "#DC2626")); st.position.set(x, .95, .3); grupo.add(st);
          return { st, g2, t0: em(r.em, .5 + s * .7) }; });
        item.pose = { pos: [0, 2.5, 10.6], alvo: [0, 2.2, 0] };
        item.upd = t => objs.forEach(o => { const k = eback(prog(t, o.t0, .4)); o.st.scale.setScalar(Math.max(.001, k)); o.st.material.opacity = Math.min(1, k); });
      } else if (c.tipo === "gangorra") {
        // gangorra da liquidez: com pouca gente, um empurrão pequeno vira um balanço enorme
        holofote(grupo, 0, 0, 2.6);
        const piv = new T.Mesh(new T.ConeGeometry(.45, .8, 4), mCinza); piv.position.y = .4; piv.rotation.y = Math.PI / 4; grupo.add(piv);
        const tab = new T.Group(); tab.position.y = .82; grupo.add(tab);
        tab.add(caixa(5.0, .14, .7, mObj, 0, 0, 0));
        const b1 = boneco(), b2 = boneco(); b1.scale.setScalar(.6); b2.scale.setScalar(.6); b1.position.set(-2.1, .07, 0); b2.position.set(2.1, .07, 0); tab.add(b1, b2);
        const pl = c.placa_texto ? placaTexto([{ t: c.placa_texto, tam: .14, cor: "#1a1420", mono: true }], 3.0, .34, COR) : null; if (pl) { pl.position.set(0, 3.3, 0); grupo.add(pl); }
        const tE = em(c.em, 1.2);
        item.pose = { pos: [0, 2.3, 10.4], alvo: [0, 1.4, 0] };
        item.upd = t => { const dt = t - tE, ang = dt > 0 ? .42 * Math.exp(-dt * .35) * Math.sin(dt * 3.2) : .03 * Math.sin(t * 1.5);
          tab.rotation.z = ang; b1.position.y = .07 + (dt > 0 && dt < .5 ? Math.sin(dt / .5 * Math.PI) * .5 : 0);
          if (pl) pl.material.opacity = eout(prog(t, tE + .3, .4)); };
      } else if (c.tipo === "semaforo") {
        // semáforo da confirmação: vermelho = não opera, verde = confirmou
        holofote(grupo, 0, 0, 1.5);
        grupo.add(cil(.1, .12, 2.4, mCinza, 12)); grupo.children[grupo.children.length - 1].position.y = 1.2;
        grupo.add(caixa(1.0, 2.5, .6, mEsc, 0, 3.4, 0));
        const cores = { vermelho: T3.vela_baixa || "#DC2626", amarelo: COR, verde: T3.vela_alta || "#20BD5A" };
        const luzes = ["vermelho", "amarelo", "verde"].map((nm, k) => { const m = new T.MeshStandardMaterial({ color: "#2a2230", emissive: new T.Color(cores[nm]), emissiveIntensity: 0 });
          const l = cil(.3, .3, .1, m, 24); l.rotation.x = Math.PI / 2; l.position.set(0, 4.15 - k * .75, .32); grupo.add(l); return { nm, m }; });
        const E = (c.estados || []).map(e => ({ ...e, t0: em(e.em, .5) }));
        const txs = E.map(e => { const p = placaTexto([{ t: e.texto || "", tam: .16, cor: e.luz === "verde" ? "#1a1420" : "#F7F7F7", mono: true }], 3.0, .4, cores[e.luz] || COR); p.position.set(0, 1.55, .5); p.visible = false; grupo.add(p); return p; });
        item.pose = { pos: [0, 2.6, 10.2], alvo: [0, 2.6, 0] };
        item.upd = t => { let at = -1; E.forEach((e, k) => { if (t >= e.t0) at = k; }); const luz = at >= 0 ? E[at].luz : "amarelo";
          luzes.forEach(l => { const on = l.nm === luz; l.m.color.set(on ? cores[l.nm] : "#2a2230"); l.m.emissiveIntensity = on ? .9 : 0; });
          txs.forEach((p, k) => { p.visible = k === at; if (k === at) p.scale.setScalar(Math.max(.001, eback(prog(t, E[k].t0, .35)))); }); };
      } else if (c.tipo === "balanca") {
        // balança real x dólar: na palavra ela pende para o lado mais pesado
        holofote(grupo, 0, 0, 2.4);
        grupo.add(caixa(1.2, .2, .8, mCinza, 0, .1, 0)); const poste = cil(.09, .12, 2.6, mObj, 12); poste.position.y = 1.4; grupo.add(poste);
        const viga = new T.Group(); viga.position.y = 2.7; grupo.add(viga); viga.add(caixa(4.0, .12, .14, mObj, 0, 0, 0));
        const pratos = [-1, 1].map(s => { const g2 = new T.Group(); grupo.add(g2); const pr = cil(.75, .62, .1, mEsc, 32); pr.position.y = -1.0; g2.add(pr);
          g2.add(caixa(.02, 1.0, .02, mCinza, 0, -.5, 0));
          const nMoedas = s < 0 ? 4 : 7, m = s < 0 ? mObj : mAcesa(); for (let k = 0; k < nMoedas; k++) { const mo = cil(.3, .3, .07, m, 24); mo.position.y = -.92 + k * .08; g2.add(mo); }
          const lb = placaTexto([{ t: s < 0 ? (c.esq || "REAL") : (c.dir || "DÓLAR"), tam: .18, cor: "#F2F2EE", mono: true }], 1.4, .32); lb.position.y = -1.55; g2.add(lb);
          return { g2, s }; });
        const selo = c.selo ? placaTexto([{ t: c.selo, tam: .3, cor: "#1a1420" }], 1.3, .5, COR) : null; if (selo) { selo.position.set(0, 3.45, .2); grupo.add(selo); }
        const tE = em(c.em, 1), ang = (c.inclina ?? 14) * D2R;
        item.pose = { pos: [0, 2.3, 10.0], alvo: [0, 1.8, 0] };
        item.upd = t => { const a = -ang * eback(prog(t, tE, 1.1)) + .02 * Math.sin(t * 1.3); viga.rotation.z = a;
          pratos.forEach(p => p.g2.position.set(p.s * 1.9 * Math.cos(a), 2.7 + p.s * 1.9 * Math.sin(a), 0));
          if (selo) { selo.material.opacity = eout(prog(t, tE + .6, .4)); selo.scale.setScalar(Math.max(.001, eback(prog(t, tE + .6, .4)))); } };
      } else if (c.tipo === "cambio") {
        // casa de câmbio: o letreiro de palhetas vira do preço antigo para o novo
        holofote(grupo, 0, 0, 2.0);
        grupo.add(caixa(3.4, 2.0, 1.1, mEsc, 0, 1.0, 0), caixa(3.6, .14, 1.3, mObj, 0, 2.05, 0));
        const tit = placaTexto([{ t: c.titulo || "CÂMBIO", tam: .22, cor: "#1a1420", mono: true }], 2.0, .4, COR); tit.position.set(0, 3.95, 0); grupo.add(tit);
        grupo.add(caixa(3.2, 1.5, .16, new T.MeshStandardMaterial({ color: "#141016" }), 0, 3.0, 0), caixa(.1, 1.0, .1, mCinza, -1.4, 2.4, 0), caixa(.1, 1.0, .1, mCinza, 1.4, 2.4, 0));
        const mo = placaTexto([{ t: c.moeda || "DÓLAR", tam: .17, cor: "#F2F2EE", mono: true }], 1.4, .32); mo.position.set(-.85, 3.0, .1); grupo.add(mo);
        const de = placaTexto([{ t: c.preco_de || "R$ —", tam: .32, cor: "#F2F2EE" }], 1.6, .62, "#1d1526"), para = placaTexto([{ t: c.preco_para || "", tam: .32, cor: COR }], 1.6, .62, "#1d1526");
        de.position.set(.7, 3.0, .1); para.position.set(.7, 3.0, .1); grupo.add(de, para);
        const tE = em(c.em, 1);
        item.pose = { pos: [0, 2.6, 9.4], alvo: [0, 2.3, 0] };
        item.upd = t => { const k = prog(t, tE, .3); de.rotation.x = eio(Math.min(1, k * 2)) * Math.PI / 2; de.visible = k < .5; para.rotation.x = -(1 - eio(Math.max(0, k * 2 - 1))) * Math.PI / 2; para.visible = k >= .5; };
      } else if (c.tipo === "termometro") {
        // termômetro do mercado: sobe até o limite, o limite é ampliado e ele continua subindo
        const mx = c.max || 14, HT = 4.0, y0 = .95, yv = v => y0 + HT * v / mx;
        holofote(grupo, 0, 0, 1.4);
        const vidro = new T.Mesh(new T.CylinderGeometry(.3, .3, HT + .2, 32, 1, true), new T.MeshStandardMaterial({ color: "#d8d2e0", transparent: true, opacity: .22, side: T.DoubleSide })); vidro.position.y = y0 + HT / 2; grupo.add(vidro);
        const vermelho = T3.vela_baixa || "#DC2626", mL = new T.MeshStandardMaterial({ color: COR, emissive: corA, emissiveIntensity: .5 });
        const bulbo = new T.Mesh(new T.SphereGeometry(.5, 24, 16), mL); bulbo.position.y = .55; grupo.add(bulbo);
        const liq = cil(.19, .19, 1, mL, 20); grupo.add(liq);
        (c.marcas || [0, 3, 6, 9, 12]).forEach(v => { grupo.add(caixa(.25, .03, .03, mCinza, -.45, yv(v), 0)); const p = placaTexto([{ t: v + "%", tam: .16, cor: "#cfc8d8", mono: true }], .7, .28); p.position.set(-.95, yv(v), 0); grupo.add(p); });
        const mk = (L, cor, escura) => { if (!L) return null; const ln = caixa(1.6, .04, .04, new T.MeshBasicMaterial({ color: cor, toneMapped: false, transparent: true }), .35, yv(L.valor), .05);
          const tg = placaTexto([{ t: L.texto || "", tam: .13, cor: escura ? "#1a1420" : "#F7F7F7", mono: true }], 2.2, .3, cor); tg.position.set(1.55, yv(L.valor) + .22, .05); grupo.add(ln, tg); return { ln, tg, t0: em(L.em, 2) }; };
        const L1 = mk(c.limite, vermelho, false), L2 = mk(c.limite_novo, COR, true);
        const tI = em(c.inicio_em, .3), tF = c.fim_em ?? c.ate - .5, v1 = c.limite ? c.limite.valor : c.valor, vf = c.valor ?? mx * .8;
        item.pose = { pos: [0, 2.7, 10.0], alvo: [.3, 2.8, 0] };
        item.upd = t => { let v; if (!L1) v = vf * eio(prog(t, tI, tF - tI));
            else if (t < L1.t0) v = v1 * eio(prog(t, tI, L1.t0 - tI));
            else if (!L2 || t < L2.t0) v = v1; else v = v1 + (vf - v1) * eio(prog(t, L2.t0, Math.max(.5, tF - L2.t0)));
          const h = Math.max(.01, yv(v) - y0); liq.scale.y = h; liq.position.y = y0 + h / 2;
          [L1, L2].forEach((L, k) => { if (!L) return; const a = eout(prog(t, L.t0 - .1, .4)) * (k === 0 && L2 ? 1 - .6 * eout(prog(t, L2.t0, .4)) : 1); L.ln.material.opacity = a; L.tg.material.opacity = a; L.ln.scale.x = Math.max(.001, a); }); };
      } else if (c.tipo === "carrinho") {
        // carrinho de compras: os produtos caem dentro, cada um com a etiqueta subindo
        holofote(grupo, 0, 0, 2.2);
        const cx = new T.Group(); cx.position.y = .35; grupo.add(cx);
        const aresta = (w, h, d, x, y, z) => cx.add(caixa(w, h, d, mObj, x, y, z));
        aresta(2.6, .05, 1.3, 0, .55, 0); [[-1.3, 0], [1.3, 0]].forEach(([x]) => aresta(.05, 1.1, 1.3, x, 1.1, 0)); aresta(2.6, 1.1, .05, 0, 1.1, -.65); aresta(2.6, .05, .05, 0, 1.65, .65); aresta(2.6, .05, .05, 0, 1.1, .65);
        aresta(.05, .8, .05, 1.55, 1.9, 0); aresta(.05, .05, 1.3, 1.6, 2.3, 0);
        [[-1.0, -.5], [-1.0, .5], [1.0, -.5], [1.0, .5]].forEach(([x, z]) => { const r = cil(.16, .16, .1, mEsc, 16); r.rotation.x = Math.PI / 2; r.position.set(x, .16, z); cx.add(r); });
        const formas = { galao: () => { const g2 = new T.Group(); g2.add(caixa(.55, .7, .35, mAcesa(), 0, 0, 0)); const b = cil(.06, .06, .2, mEsc, 10); b.position.set(.15, .45, 0); g2.add(b); return g2; },
          tv: () => { const g2 = new T.Group(); g2.add(caixa(.85, .55, .08, mEsc, 0, 0, 0), caixa(.75, .45, .01, new T.MeshStandardMaterial({ color: "#2a1f3a", emissive: new T.Color(T3.cone || COR), emissiveIntensity: .35 }), 0, 0, .05)); return g2; },
          aviao: () => { const g2 = new T.Group(); const f = cil(.12, .12, .9, mObj, 12); f.rotation.z = Math.PI / 2; g2.add(f, caixa(.25, .04, .9, mAcesa(), 0, 0, 0), caixa(.12, .25, .04, mAcesa(), -.4, .12, 0)); return g2; } };
        const its = (c.itens || []).map((it, k) => { const g2 = (formas[it.forma] || formas.galao)(); g2.position.set(-.8 + k * .8, 5, 0); grupo.add(g2);
          const tag = placaTexto([{ t: it.nome || "", tam: .13, cor: "#F2F2EE", mono: true }, { t: c.selo || "▲ PREÇO", tam: .12, cor: COR, mono: true }], 1.4, .5, "#141016"); grupo.add(tag);
          return { g2, tag, x: -.8 + k * .8, t0: em(it.em, .5 + k * .6), k }; });
        item.pose = { pos: [0, 3.0, 9.6], alvo: [0, 1.5, 0] };
        item.upd = t => its.forEach(o => { const k = eback(prog(t, o.t0, .55)); o.g2.position.set(o.x, 4.6 - (4.6 - 1.35) * k, 0); o.g2.rotation.y = (1 - k) * 2;
          o.tag.position.set(o.x, 2.55 + o.k % 2 * .55, .5); o.tag.material.opacity = eout(prog(t, o.t0 + .4, .3)); });
      } else if (c.tipo === "luneta") {
        // o mentor de luneta: olha para o que o mercado espera (o futuro), não só para o que aconteceu
        holofote(grupo, -.5, 0, 1.2);
        const bo = boneco(); bo.position.set(-.75, 0, 0); bo.rotation.y = .5; grupo.add(bo);
        const lun = cil(.09, .15, 1.2, mAcesa(), 16); lun.position.set(-.2, 1.95, .1); lun.rotation.z = -1.15; grupo.add(lun);
        const alvoG = new T.Group(); alvoG.position.set(1.3, 3.1, -.3); grupo.add(alvoG);
        const pl = placaTexto([{ t: c.alvo || "O QUE ESPERA", tam: .16, cor: "#1a1420", mono: true }, { t: "?", tam: .36, cor: "#1a1420" }], 2.1, .9, COR); alvoG.add(pl);
        const raio = new T.Mesh(new T.ConeGeometry(.75, 2.3, 24, 1, true), new T.MeshBasicMaterial({ color: T3.cone || COR, transparent: true, opacity: .12, blending: T.AdditiveBlending, depthWrite: false, side: T.DoubleSide, toneMapped: false }));
        raio.position.set(.55, 2.55, -.1); raio.rotation.z = Math.PI / 2 + .42; grupo.add(raio);
        const tE = em(c.em, 1);
        item.pose = { pos: [.25, 2.4, 9.4], alvo: [.25, 2.1, 0] };
        item.upd = t => { const k = eout(prog(t, tE, .6)); raio.material.opacity = .14 * k; pl.material.opacity = .25 + .75 * k; alvoG.scale.setScalar(.85 + .15 * k + .02 * Math.sin(t * 3)); };
      } else if (c.tipo === "cta") {
        holofote(grupo, 0, 0, 1.15); const bo = boneco(); grupo.add(bo);
        item.pose = { pos: [0, 2.2, 7.5], alvo: [0, 1.6, 0] };
      }
      if (c.camera3d) item.pose = { pos: c.camera3d.pos || item.pose.pos, alvo: c.camera3d.alvo || item.pose.alvo };
      cenas3d.push(item);
    });
    // placas: postes com cartaz que sobem do chão na palavra (até 4 lado a lado)
    function montaPlacas(grupo, lista, dx, em) {
      const n = lista.length, esp = 2.15, x0 = dx + (dx ? 0 : -(n - 1) * esp / 2);
      const objs = lista.map((p, k) => { const gq = new T.Group(); gq.position.set(x0 + k * (dx ? 0 : esp), 0, dx ? 0 : 0); grupo.add(gq);
        if (dx) { gq.position.set(dx, 0, .2 - k * .01); gq.scale.setScalar(.72); }
        const poste = caixa(.08, 1.3, .08, mCinza, 0, .65, 0); gq.add(poste);
        const cart = caixa(2.0, 1.0, .1, mEsc, 0, 1.75, 0); gq.add(cart);
        const txt = placaTexto([{ t: p.titulo || "", tam: .2, cor: "#F2F2EE" }, ...(p.valor ? [{ t: p.valor, tam: .17, cor: COR, mono: true }] : [])], 1.9, .9);
        txt.position.set(0, 1.75, .056); gq.add(txt);
        const tag = p.etiqueta ? placaTexto([{ t: p.etiqueta, tam: .13, cor: "#1a1420", mono: true }], 1.3, .22, COR) : null;
        if (tag) { tag.position.set(0, 2.33, .06); gq.add(tag); }
        return { gq, t0: em(p.em, .5 + k * .5), dxMode: !!dx, k }; });
      return t => objs.forEach(o => { const k = eback(prog(t, o.t0, .55)); o.gq.position.y = -2.6 * (1 - k);
        if (o.dxMode) o.gq.visible = t >= o.t0 && (o.k === objs.filter(x => t >= x.t0).length - 1); });
    }
    const V = (a, O) => new T.Vector3(a[0] + O.x, a[1] + O.y, a[2] + O.z);
    function poseEm(t, item) {   // pose da cena com deriva lenta (órbita) e respiração
      const dt = Math.max(0, t - item.c.de), p = item.pose, ang = (item.c.orbita ?? .025) * dt;
      const pos = V(p.pos, item.O), alvo = V(p.alvo, item.O), d = pos.clone().sub(alvo);
      d.applyAxisAngle(new T.Vector3(0, 1, 0), ang); d.multiplyScalar(DIST * (1 - .012 * dt));
      return { pos: alvo.clone().add(d), alvo };
    }
    function render(t) {
      const i = idx(t), c = cenas[i]; let it = cenas3d.find(x => x.i === i);
      if (!it) { // globo na tela: segura a pose da cena 3D mais perto (para o fade)
        it = cenas3d.filter(x => x.i < i).pop() || cenas3d.find(x => x.i > i); if (!it) return; }
      cenas3d.forEach(x => x.upd(t));
      let { pos, alvo } = poseEm(t, it);
      if (it.i === i && i > 0) { const k = eio(prog(t, c.de, TRANS)), ant = cenas3d.find(x => x.i === i - 1);
        let p0, a0;
        if (ant) { const q = poseEm(c.de, ant); p0 = q.pos; a0 = q.alvo; }
        else { a0 = alvo.clone(); p0 = pos.clone().add(new T.Vector3(1.5, 2.2, 6)); }   // vindo do globo: entra de longe
        pos = p0.clone().lerp(pos, k); alvo = a0.clone().lerp(alvo, k); }
      cam.position.copy(pos); cam.lookAt(alvo); ren.render(sc, cam);
    }
    return { render };
  }

  // ---------- quadro: globo, estúdio e poeira por cima ----------
  function desenha(t) {
    const ag = alfaGlobo(t), cam = camEm(t);
    if (ag > 0) desenhaGlobo(t, cam); else g.clearRect(0, 0, W, H);
    cv.style.opacity = ag.toFixed(3);
    if (E3 && ag < 1) { cv3.style.opacity = "1"; E3.render(t); } else cv3.style.opacity = "0";
    gp2.setTransform(1, 0, 0, 1, 0, 0); gp2.clearRect(0, 0, W, H);
    poeira(gp2, t, cam.lon, false); poeira(gp2, t, cam.lon, true);
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
    if (c.tipo === "cta" || c.cta) return;
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
    if (c.carimbo) { const ca = document.getElementById("carimbo"), s = mk("div", "selo", ca, { borderWidth: px(4), padding: `${px(16)} ${px(30)} ${px(12)}` });
      const tt = mk("div", "t", s, { fontSize: px(c.carimbo.tamanho || 46) }); tt.textContent = c.carimbo.titulo;
      if (c.carimbo.sub) { const ss = mk("div", "s", s, { fontSize: px(16), marginTop: px(8) }); ss.textContent = c.carimbo.sub; }
      Object.assign(s.style, { position: "absolute", left: "0", top: (H * (c.carimbo.y ?? .45)).toFixed(1) + "px" });   // cada carimbo com a sua altura
      tl.set(ca, { display: "block" }, c.carimbo.em);
      tl.fromTo(s, { opacity: 0, scale: 1.4, rotation: -4, xPercent: -50, yPercent: -50 }, { opacity: 1, scale: 1, rotation: -4, xPercent: -50, yPercent: -50, duration: .32, ease: "power3.out" }, c.carimbo.em);
      if (i < cenas.length - 1) tl.to(s, { opacity: 0, duration: .25 }, cenas[i + 1].de - .2); }
  });
  const fim = cenas.find(c => c.tipo === "cta" || c.cta);   // CTA no globo ou em qualquer cenário 3D ("cta": true)
  if (fim) { const box = document.getElementById("cta"); Object.assign(box.style, { top: (H * (VERT ? .225 : .1)).toFixed(1) + "px" });
    const q = mk("div", "q", box, { fontSize: px(fim.tam_pergunta || 52), maxWidth: px(940) }); q.textContent = fim.pergunta || "";
    tl.to(box, { opacity: 1, duration: .01 }, fim.de);
    tl.fromTo(q, { opacity: 0, y: px(24) }, { opacity: 1, y: 0, duration: .7, ease: "expo.out" }, fim.de + .1);
    if (fim.botao) { const b = mk("div", "b", box, { fontSize: px(28), padding: `${px(12)} ${px(30)}`, marginTop: px(26) }); b.textContent = fim.botao;
      tl.fromTo(b, { opacity: 0, scale: .9 }, { opacity: 1, scale: 1, duration: .55, ease: "power3.out" }, fim.botao_em ?? fim.de + .7); }
    if (fontesEl) tl.to(fontesEl, { opacity: .55, duration: .4 }, fim.de); }

  // ---------- legenda karaokê (só quando o plano pede) ----------
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
  window.__timelines = window.__timelines || {}; window.__timelines["ludico"] = tl;
})();
