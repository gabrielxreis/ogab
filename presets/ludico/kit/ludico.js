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
  { // fundo infinito do estilo "estudio" (referência Ludificando): grafite com um leve clarão atrás do assunto, pintado no
    // #root; o canvas 3D fica transparente nessas cenas e só desenha objetos e sombras por cima
    const F = Object.assign({ fundo: "#0c0c0c" }, P.tema3d || {}), cl = new THREE.Color(F.fundo).lerp(new THREE.Color(F.fundo_luz || "#ffffff"), F.fundo_luz ? .1 : .075);
    root.style.background = `radial-gradient(ellipse 110% 58% at 50% 50%, #${cl.getHexString()} 0%, ${F.fundo} 64%, ${F.fundo_base || F.fundo} 100%)`; }
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
    "barco", "skyline", "cesta", "relogios", "gangorra", "semaforo", "balanca", "cambio", "termometro", "carrinho", "luneta",
    "quique", "bussola", "cofre", "escudo", "bifurcacao", "seguir", "setas", "moeda", "martelo", "ima", "domino", "escada", "leilao", "sismografo", "cartao", "foguete", "chip", "planta", "dado", "urna", "alvo", "balao", "ponte", "pilha", "casa", "carne", "torneira", "instagram", "mesa", "hemiciclo", "semana", "documento"]);
  const EXTRA = window.CENAS_EXTRA || {};   // cenários do cliente fora do kit ("cenas_extra" no plano), mesmo contrato dos nativos
  cenas.forEach(c => { c._3d = TIPOS3D.has(c.tipo) || !!EXTRA[c.tipo] || (c.tipo === "cta" && !!c.cenario && c.cenario !== "globo"); });
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
  // batidas (gerar.py): palavras fortes nos vãos sem evento; cada uma dá um empurrão de câmera, pulso, onda e faíscas
  const BAT = (P.batidas || []).map(b => +b).sort((a, b) => a - b);
  const ultBat = t => { let u = null; for (const b of BAT) { if (b <= t) u = b; else break; } return u; };
  const kickEm = t => { const u = ultBat(t); if (u == null) return 0; const x = t - u; return x < .12 ? x / .12 : Math.exp(-(x - .12) * 5); };
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
  const POEIRA = Array.from({ length: P.poeira ?? 18 }, () => ({ x: rnd(), y: rnd(), d: .15 + rnd() * .85, s: 3 + rnd() * 11, f: rnd() * 6.28 }));
  function poeira(ctx, t, desloc, frente) {
    for (const p of POEIRA) { if ((p.d > .7) !== frente) continue;
      const x = ((p.x * W - desloc * 2.2 * U * p.d * 4 + Math.sin(t * .3 + p.f) * 8 * U) % W + W) % W;
      const y = ((p.y * H - t * 7 * U * p.d) % H + H) % H, r = p.s * U * (frente ? 1.3 : .7) * p.d + 1.2 * U;
      ctx.globalAlpha = (frente ? .18 : .2) + .25 * p.d; ctx.fillStyle = "#B9B9B2";
      ctx.filter = `blur(${((frente ? 3 : 1.2) + p.d * (frente ? 4 : 1.5)) * U}px)`;
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
    const ren = new T.WebGLRenderer({ canvas: cv3, antialias: true, alpha: true, preserveDrawingBuffer: true });
    ren.setPixelRatio(1); ren.setSize(W, H, false); ren.setClearColor(T3.fundo, 1);
    ren.shadowMap.enabled = true; ren.shadowMap.type = T.PCFSoftShadowMap;
    ren.outputColorSpace = T.SRGBColorSpace; ren.toneMapping = T.ACESFilmicToneMapping; ren.toneMappingExposure = P.exposicao ?? 1.4;   // direção de arte 27/10/2026: o estúdio estava escuro demais
    const sc = new T.Scene(); sc.fog = new T.Fog(T3.fundo, 30, 75);
    const cam = new T.PerspectiveCamera(38, W / H, .1, 300), DIST = P.estudio_dist ?? 1.85;
    cam.setViewOffset(W, H, 0, -H * (P.estudio_desce ?? .1), W, H);   // o assunto desce: a parte de cima é do cartão
    const hemi = new T.HemisphereLight(T3.ceu || 0xc9c0e0, 0x2a1838, 1.25); sc.add(hemi);
    const CHAO_PALCO = new T.Color(0x2a1838), CHAO_ESTUDIO = new T.Color(T3.chao_luz || "#3a3934");
    const dirL = new T.DirectionalLight(0xffffff, 1.0); dirL.position.set(4, 10, 8); sc.add(dirL);   // luz principal (frente-alto)
    const preench = new T.DirectionalLight(0xffffff, .35); preench.position.set(-6, 4, 6); sc.add(preench);   // preenchimento
    const recorte = new T.DirectionalLight(T3.cone || COR, 1.6); recorte.position.set(0, 6, -10); sc.add(recorte);   // contraluz que desenha o contorno
    const chao = new T.Mesh(new T.PlaneGeometry(600, 600), new T.MeshStandardMaterial({ color: T3.chao, roughness: .92 }));
    chao.rotation.x = -Math.PI / 2; chao.receiveShadow = true; sc.add(chao);
    // fundo infinito da referência: no "estudio" o chão some (só a sombra aparece sobre a cor do fundo), sem linha de horizonte
    const chaoPalco = chao.material, chaoSombra = new T.ShadowMaterial({ opacity: .24 });
    const corA = new T.Color(COR);
    const mObj = new T.MeshStandardMaterial({ color: T3.objeto, roughness: .55 }), mEsc = new T.MeshStandardMaterial({ color: T3.escuro, roughness: .7 });
    const mCinza = new T.MeshStandardMaterial({ color: T3.cinza, roughness: .7 });
    const mAcesa = () => new T.MeshStandardMaterial({ color: COR, emissive: corA, emissiveIntensity: .55, roughness: .4 });
    // caixa com canto arredondado (o acabamento "argila" da referência Ludificando); "cantos": false no plano volta ao cubo seco
    const GEO_RB = new Map();
    function caixaArred(w, h, d) {
      const r = Math.min(.11, Math.min(w, h, d) * .2), key = [w, h, d].map(v => v.toFixed(3)).join("x");
      if (r < .006 || P.cantos === false) return new T.BoxGeometry(w, h, d);
      if (GEO_RB.has(key)) return GEO_RB.get(key);
      const s = 5, g = new T.BoxGeometry(1, 1, 1, s, s, s).toNonIndexed(), pos = g.attributes.position.array, nor = g.attributes.normal.array;
      const bx = w / 2 - r, by = h / 2 - r, bz = d / 2 - r, n = new T.Vector3(), meio = .5 / s;
      for (let i = 0; i < pos.length; i += 3) { const px = pos[i], py = pos[i + 1], pz = pos[i + 2];
        n.set(px - Math.sign(px) * meio, py - Math.sign(py) * meio, pz - Math.sign(pz) * meio).normalize();
        pos[i] = bx * Math.sign(px) + n.x * r; pos[i + 1] = by * Math.sign(py) + n.y * r; pos[i + 2] = bz * Math.sign(pz) + n.z * r;
        nor[i] = n.x; nor[i + 1] = n.y; nor[i + 2] = n.z; }
      g.attributes.position.needsUpdate = true; GEO_RB.set(key, g); return g; }
    const caixa = (w, h, d, m, x = 0, y = 0, z = 0) => { const o = new T.Mesh(caixaArred(w, h, d), m); o.position.set(x, y, z); o.castShadow = o.receiveShadow = true; return o; };
    const cil = (rt, rb, h, m, seg = 24) => { const o = new T.Mesh(new T.CylinderGeometry(rt, rb, h, seg), m); o.castShadow = o.receiveShadow = true; return o; };
    // texto em plano (CanvasTexture); linhas: [{t, tam, cor, peso, mono}]
    const fundoTx = (() => { const cv = document.createElement("canvas"); cv.width = 64; cv.height = 512; const x = cv.getContext("2d"), g = x.createLinearGradient(0, 0, 0, 512);
      g.addColorStop(0, T3.fundo_topo || "#3B1F5E"); g.addColorStop(.55, T3.fundo_meio || "#1E1230"); g.addColorStop(1, T3.fundo_base || "#0E0914"); x.fillStyle = g; x.fillRect(0, 0, 64, 512);
      const tx = new T.CanvasTexture(cv); tx.colorSpace = T.SRGBColorSpace; return tx; })();
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
      const pm = new T.Mesh(new T.PlaneGeometry(larg, alt), m); pm.userData.rotulo = true; return pm;
    }
    // holofote: cone de luz aditivo + spot com sombra + anel no chão
    // ILUMINAÇÃO VARIADA (Gabriel, 27/10/2026: "não precisa ter aquele holofote de luz o tempo todo, pode explorar outras coisas").
    // A luz de verdade (sombra/brilho) vem do POOL; aqui só o que se VÊ. Estilo por cena: c.luz ou automático, alternando.
    // "estudio" = a luz da referência Ludificando (Gabriel, 27/10/2026: "esse tá muito mais bonito e lapidado"): sem facho
    // nenhum, luz suave de frente e de cima, fundo grafite levantado atrás do assunto e sombra de contato macia. É a BASE:
    // metade das cenas; as outras luzes entram entre elas para variar, e o cone clássico só 1 a cada 12.
    const ESTILOS_LUZ = ["estudio"];   // padrão = igual à referência em todas as cenas; variar só com "luz" na cena ou "luzes" no plano
    // outros estilos disponíveis: "contraluz", "neon", "janela", "feixes", "grade", "cone" (holofote clássico)
    const matSuave = (tx, op = 1) => new T.MeshBasicMaterial({ map: tx, transparent: true, opacity: op, depthWrite: false, toneMapped: false });
    function gradiente(cor, a0 = .9, forma = "radial") {
      const cv = document.createElement("canvas"); cv.width = cv.height = 256; const x = cv.getContext("2d");
      const g = forma === "radial" ? x.createRadialGradient(128, 128, 0, 128, 128, 128) : x.createLinearGradient(0, 256, 0, 0);
      const c = new T.Color(cor), rgb = `${Math.round(c.r * 255)},${Math.round(c.g * 255)},${Math.round(c.b * 255)}`;
      g.addColorStop(0, `rgba(${rgb},${a0})`); g.addColorStop(1, `rgba(${rgb},0)`); x.fillStyle = g; x.fillRect(0, 0, 256, 256);
      const tx = new T.CanvasTexture(cv); tx.colorSpace = T.SRGBColorSpace; return tx; }
    let TX_DERRAME = null;
    const novoAceso = () => { const m = new T.MeshStandardMaterial({ color: COR, emissive: new T.Color(COR), emissiveIntensity: .55, roughness: .55 });
      if (P.acesos !== false) { m.userData.aceso = true; m.toneMapped = false; m.emissiveIntensity = .7; m.color = new T.Color(COR).multiplyScalar(.42); } return m; };
    const matBranco = () => { const m = new T.MeshStandardMaterial({ color: "#d8d8d4", emissive: new T.Color("#ffffff"), emissiveIntensity: .62, roughness: .5 }); m.toneMapped = false; m.userData.aceso = true; return m; };
    const matLuz = (tx, op = 1) => new T.MeshBasicMaterial({ map: tx, transparent: true, opacity: op, depthWrite: false, blending: T.AdditiveBlending, toneMapped: false, side: T.DoubleSide });
    function holofote(grupo, x, z, raio = 1.1, alt = 9) {
      const est = grupo.userData.estilo || "cone", n0 = grupo.children.length;
      (grupo.userData.luzes = grupo.userData.luzes || []).push({ x, z, alt, est });   // a luz de verdade vem do POOL (ver abaixo)
      const corL = T3.cone || COR, primeira = grupo.userData.luzes.length === 1;
      const chao = (op = .16) => { const d = new T.Mesh(new T.CircleGeometry(raio * .92, 64), new T.MeshBasicMaterial({ color: T3.disco || COR, transparent: true, opacity: op, toneMapped: false }));
        d.rotation.x = -Math.PI / 2; d.position.set(x, .011, z); grupo.add(d); };
      if (est === "estudio") {   // referência: fundo grafite levantado atrás + sombra de contato, nada de facho
        // o grafite que levanta atrás do assunto é pintado ATRÁS do canvas 3D (fundo infinito, ver "fundoInfinito")
        const s = new T.Mesh(new T.PlaneGeometry(raio * 3.2, raio * 3.2), matSuave(gradiente("#000000", .55), 1)); s.rotation.x = -Math.PI / 2; s.position.set(x, .013, z); grupo.add(s);
      } else if (est === "cone") {
        const cone = new T.Mesh(new T.CylinderGeometry(.18, raio * 1.15, alt, 40, 1, true),
          new T.MeshBasicMaterial({ color: corL, transparent: true, opacity: T3.cone ? .085 : .045, blending: T.AdditiveBlending, depthWrite: false, side: T.DoubleSide, toneMapped: false }));
        cone.position.set(x, alt / 2, z); grupo.add(cone);
        const a = new T.Mesh(new T.RingGeometry(raio * .92, raio, 64), new T.MeshBasicMaterial({ color: COR, transparent: true, opacity: .85, toneMapped: false }));
        a.rotation.x = -Math.PI / 2; a.position.set(x, .012, z); grupo.add(a); chao();
      } else if (est === "neon") {   // aro grosso de neon no chão + reflexo
        [[raio, .055, 1], [raio * .72, .025, .55]].forEach(([r, tb, op]) => { const t = new T.Mesh(new T.TorusGeometry(r, tb, 12, 96), new T.MeshBasicMaterial({ transparent: true, opacity: op, toneMapped: false }));
          t.material.color = new T.Color(corL); t.rotation.x = -Math.PI / 2; t.position.set(x, .03, z); grupo.add(t); });
        const gl = new T.Mesh(new T.PlaneGeometry(raio * 3.4, raio * 3.4), matLuz(gradiente(corL, .5), .7)); gl.rotation.x = -Math.PI / 2; gl.position.set(x, .015, z); grupo.add(gl);
      } else if (est === "contraluz") {   // halo grande atrás: o objeto vira silhueta com contorno de luz
        if (primeira) { const h = new T.Mesh(new T.PlaneGeometry(7, 7), matLuz(gradiente(corL, .75), .95)); h.position.set(0, 2.6, -2.6); grupo.add(h);
          const r = new T.Mesh(new T.RingGeometry(2.05, 2.1, 96), new T.MeshBasicMaterial({ color: COR, transparent: true, opacity: .55, toneMapped: false })); r.position.set(0, 2.6, -2.55); grupo.add(r); }
        chao(.1);
      } else if (est === "feixes") {   // dois fachos cruzados vindo dos lados
        [-1, 1].forEach(sd => { const f = new T.Mesh(new T.CylinderGeometry(.12, raio * .9, alt, 32, 1, true),
            new T.MeshBasicMaterial({ color: corL, transparent: true, opacity: .06, blending: T.AdditiveBlending, depthWrite: false, side: T.DoubleSide, toneMapped: false }));
          f.position.set(x + sd * alt * .22, alt / 2, z); f.rotation.z = sd * .42; grupo.add(f); });
        chao(.2);
      } else if (est === "grade") {   // chão com grade luminosa e brilho no horizonte
        if (primeira) { const gr = new T.GridHelper(16, 16, corL, corL); gr.material.transparent = true; gr.material.opacity = .28; gr.position.y = .02; grupo.add(gr);
          const hz = new T.Mesh(new T.PlaneGeometry(26, 6), matLuz(gradiente(corL, .55, "linear"), .8)); hz.position.set(0, 3, -9); grupo.add(hz); }
        chao(.12);
      } else if (est === "janela") {   // fachos verticais atrás, como luz entrando por janelas
        if (primeira) [-2.2, -.75, .75, 2.2].forEach((jx, k) => { const b = new T.Mesh(new T.PlaneGeometry(.9, 9), matLuz(gradiente(corL, .5, "linear"), .55 - (k % 2) * .15));
          b.position.set(jx, 4.5, -3.2); b.rotation.z = .12; grupo.add(b); });
        chao(.14);
      }
      grupo.children.slice(n0).forEach(o => { o.userData.luz = true; });   // luz não entra na montagem
      return { cone: null, sp: null, anel: null, disco: null };
    }
    function manequim() {   // referência Ludificando: manequim articulado sem rosto, argila clara, ~1,9 de altura
      const b = new T.Group(), m = new T.MeshStandardMaterial({ color: T3.manequim || "#A19D92", roughness: .72 }), mats = [m];
      const peca = (geo, x, y, z, rz = 0) => { const o = new T.Mesh(geo, m); o.position.set(x, y, z); o.rotation.z = rz; o.castShadow = true; b.add(o); return o; };
      const bola = r => new T.SphereGeometry(r, 20, 14), osso = (r, h) => new T.CapsuleGeometry(r, h, 6, 14);
      const cab = peca(bola(.17), 0, 1.74, 0); cab.scale.set(.9, 1.18, .95);
      peca(osso(.05, .08), 0, 1.53, 0);
      const peito = peca(osso(.17, .26), 0, 1.24, 0); peito.scale.set(1.25, 1, .78);
      peca(bola(.08), 0, 1.0, 0);
      const quad = peca(osso(.15, .1), 0, .9, 0); quad.scale.set(1.2, 1, .8);
      [-1, 1].forEach(sd => { peca(bola(.07), sd * .27, 1.42, 0); peca(osso(.055, .26), sd * .31, 1.24, 0, sd * .1);
        peca(bola(.055), sd * .34, 1.05, 0); peca(osso(.05, .24), sd * .36, .87, .02, sd * .05); peca(bola(.06), sd * .37, .69, .03);
        peca(bola(.075), sd * .1, .8, 0); peca(osso(.07, .3), sd * .11, .6, 0); peca(bola(.065), sd * .11, .42, 0);
        peca(osso(.06, .28), sd * .11, .24, 0); const pe = peca(new T.BoxGeometry(.11, .06, .2), sd * .11, .03, .04); });
      b.userData.mats = mats; return b;
    }
    function boneco(cabeca = T3.objeto) {   // personagem: cápsula na cor da marca, cabeça clara, braços, base (substituiu o cilindro preto)
      const b = new T.Group(), mCorpo = new T.MeshStandardMaterial({ color: T3.personagem || "#6B4BA3", roughness: .45 }), mCab = new T.MeshStandardMaterial({ color: cabeca, roughness: .35 });
      const corpo = new T.Mesh(new T.CapsuleGeometry(.36, .7, 8, 24), mCorpo); corpo.position.y = .78; corpo.castShadow = true; b.add(corpo);
      const gola = new T.Mesh(new T.TorusGeometry(.2, .05, 10, 28), mCab); gola.rotation.x = Math.PI / 2; gola.position.y = 1.36; b.add(gola);
      const cab = new T.Mesh(new T.SphereGeometry(.34, 32, 24), mCab); cab.position.y = 1.72; cab.castShadow = true; b.add(cab);
      [-1, 1].forEach(sd => { const br = new T.Mesh(new T.CapsuleGeometry(.09, .5, 6, 12), mCorpo); br.position.set(sd * .43, .86, 0); br.rotation.z = sd * .18; br.castShadow = true; b.add(br);
        const mao = new T.Mesh(new T.SphereGeometry(.1, 16, 12), mCab); mao.position.set(sd * .5, .55, 0); b.add(mao);
        b.userData[sd > 0 ? "direito" : "esquerdo"] = { br, mao }; });   // cena que precisa do braço (luneta) reposiciona
      b.userData.mCorpo = mCorpo; b.userData.mCab = mCab;
      [-1, 1].forEach(sd => { const ol = new T.Mesh(new T.SphereGeometry(.045, 12, 8), new T.MeshBasicMaterial({ color: "#1a1420" })); ol.position.set(sd * .12, 1.76, .31); b.add(ol); });
      const base = cil(.42, .46, .08, new T.MeshStandardMaterial({ color: T3.cinza, roughness: .6 }), 28); base.position.y = .04; b.add(base);
      return b;
    }
    // POOL de holofotes: quantidade FIXA de luzes com sombra (cena atual + anterior na transição). Uma SpotLight por
    // cenário estourava o limite do WebGL com 20+ cenas e os objetos sumiam (material não compilava).
    const POOL = [...Array(4)].map(() => { const sp = new T.SpotLight(T3.luz, 0, 24, .17, .6, 1.4); sp.castShadow = true; sp.shadow.mapSize.set(1024, 1024);
      sc.add(sp, sp.target); return sp; });
    function luzes(lista) {   // lista = [[grupo, {x,z,alt}], ...] (até 4)
      // estúdio: luz mais de frente (frente clara, topo mais escuro, como a referência)
      POOL.forEach((sp, k) => { const L = lista[k]; if (!L) { sp.intensity = 0; return; } const [g, l] = L, suave = l.est === "estudio";
        // estúdio: luz larga e macia vinda da frente e de cima (sombra suave); os outros estilos: o spot fechado de palco
        sp.angle = suave ? .5 : .17; sp.penumbra = suave ? 1 : .6; sp.intensity = suave ? 8 : 16;
        sp.position.set(g.position.x + l.x, suave ? l.alt * .72 : l.alt, g.position.z + l.z + (suave ? 6.5 : 0)); sp.target.position.set(g.position.x + l.x, 0, g.position.z + l.z); sp.target.updateMatrixWorld(); }); }
    const cenas3d = [];   // {c, grupo, origem, upd(t), pose}
    let slot = 0;
    cenas.forEach((c, i) => { if (!c._3d) return;
      // "continua": true = mesma ideia da frase anterior (referência: o monitor fica e só acende mais uma tecla): a câmera
      // fica no MESMO cenário, sem viagem; o cenário lê os campos da continuação (ex.: mesa > "acesas", "acende_em")
      if (c.continua && i > 0 && cenas[i - 1]._3d) { const ant = cenas3d.find(x => x.i === i - 1);
        if (ant) { cenas3d.push(Object.assign({}, ant, { i, i0: ant.i0 ?? ant.i, cont: true, monta: null, fx: null, upd: () => {} })); return; } }   // o original já monta e anima
      const grupo = new T.Group(), O = new T.Vector3(slot * 46, 0, -(slot % 2) * 8);
      grupo.userData.estilo = c.luz || (P.luzes ? P.luzes[slot % P.luzes.length] : ESTILOS_LUZ[slot % ESTILOS_LUZ.length]); slot++;
      grupo.position.copy(O); sc.add(grupo);
      // parede ao fundo de cada canto do estúdio
      const par = new T.Mesh(new T.PlaneGeometry(44, 20), new T.MeshBasicMaterial({ map: fundoTx, toneMapped: false })); par.userData.deco = true;
      par.position.set(0, 10, -11); par.receiveShadow = true; grupo.add(par);
      if (T3.vinheta) { const vc = document.createElement("canvas"); vc.width = vc.height = 256; const vx = vc.getContext("2d"), rg = vx.createRadialGradient(128, 128, 0, 128, 128, 128);
        rg.addColorStop(0, T3.vinheta); rg.addColorStop(1, "rgba(0,0,0,0)"); vx.fillStyle = rg; vx.fillRect(0, 0, 256, 256);
        const vt = new T.CanvasTexture(vc); vt.colorSpace = T.SRGBColorSpace;
        const vi = new T.Mesh(new T.PlaneGeometry(26, 20), new T.MeshBasicMaterial({ map: vt, transparent: true, depthWrite: false, toneMapped: false }));
        vi.position.set(0, 6, -10.9); grupo.add(vi); }   // vinheta roxa do site atrás do cenário
      if (grupo.userData.estilo === "estudio") grupo.children.forEach(o => { o.visible = false; });   // estúdio: sem parede (fundo infinito)
      grupo.children.forEach(o => { o.userData.luz = true; });   // parede e vinheta: fundo, não entram na montagem
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
        // personagem em 3/4 com a luneta NO OLHO, segura pela mão direita, apontando de verdade para a placa (27/10/2026:
        // a luneta antiga atravessava o rosto do personagem novo)
        const bo = boneco(); bo.position.set(-.85, 0, .2); bo.rotation.y = .75; grupo.add(bo); grupo.updateMatrixWorld(true);
        const V3 = (x, y, z) => new T.Vector3(x, y, z);
        const alvoG = new T.Group(); alvoG.position.set(1.15, 2.85, -.2); grupo.add(alvoG);
        const pl = placaTexto([{ t: c.alvo || "O QUE ESPERA", tam: .16, cor: "#1a1420", mono: true }, { t: "?", tam: .36, cor: "#1a1420" }], 2.1, .9, COR); alvoG.add(pl);
        const olho = grupo.worldToLocal(bo.localToWorld(V3(.08, 1.74, .3))), dir = alvoG.position.clone().sub(olho).normalize();
        const lunG = new T.CylinderGeometry(.08, .14, 1.0, 20); lunG.rotateX(Math.PI / 2); lunG.translate(0, 0, .5);   // eixo em +z, base no olho
        const lun = new T.Mesh(lunG, mAcesa()); lun.castShadow = true; lun.position.copy(olho); lun.lookAt(grupo.localToWorld(alvoG.position.clone())); grupo.add(lun);
        const anel = new T.Mesh(new T.TorusGeometry(.15, .025, 8, 24), mObj); anel.position.copy(olho.clone().addScaledVector(dir, .98)); anel.lookAt(grupo.localToWorld(alvoG.position.clone())); grupo.add(anel);
        { const D = bo.userData.direito; D.br.visible = false; D.mao.visible = false;   // braço direito sobe até a luneta
          const ombro = grupo.worldToLocal(bo.localToWorld(V3(.4, 1.22, 0))), mao = olho.clone().addScaledVector(dir, .55).add(V3(0, -.12, 0));
          const meio = ombro.clone().add(mao).multiplyScalar(.5), eixo = mao.clone().sub(ombro);
          const br = new T.Mesh(new T.CapsuleGeometry(.09, Math.max(.1, eixo.length() - .18), 6, 12), bo.userData.mCorpo); br.position.copy(meio);
          br.quaternion.setFromUnitVectors(V3(0, 1, 0), eixo.normalize()); br.castShadow = true; grupo.add(br);
          const m2 = new T.Mesh(new T.SphereGeometry(.1, 16, 12), bo.userData.mCab); m2.position.copy(mao); grupo.add(m2); }
        const ponta = olho.clone().addScaledVector(dir, 1.0), dist = alvoG.position.distanceTo(ponta);
        const raio = new T.Mesh(new T.ConeGeometry(.6, dist, 24, 1, true), new T.MeshBasicMaterial({ color: T3.cone || COR, transparent: true, opacity: .12, blending: T.AdditiveBlending, depthWrite: false, side: T.DoubleSide, toneMapped: false }));
        raio.position.copy(ponta.clone().addScaledVector(dir, dist / 2)); raio.quaternion.setFromUnitVectors(V3(0, 1, 0), dir.clone().negate()); raio.userData.deco = true; grupo.add(raio);
        const tE = em(c.em, 1);
        item.pose = { pos: [.25, 2.4, 9.4], alvo: [.25, 2.1, 0] };
        item.upd = t => { const k = eout(prog(t, tE, .6)); raio.material.opacity = .14 * k; pl.material.opacity = .25 + .75 * k; alvoG.scale.setScalar(.85 + .15 * k + .02 * Math.sin(t * 3)); };
      } else if (c.tipo === "quique") {
        // a bola despenca (o tombo) e quica de volta (a reação): cai_em, sobe_em
        holofote(grupo, 0, 0, 1.7);
        const pc = placaTexto([{ t: c.chao || "FUNDO", tam: .15, cor: "#cfc8d8", mono: true }], 2.2, .34); pc.rotation.x = -Math.PI / 2; pc.position.set(0, .02, 1.35); grupo.add(pc);
        const bola = new T.Mesh(new T.SphereGeometry(.55, 32, 20), mAcesa()); bola.castShadow = true; grupo.add(bola);
        const tC = em(c.cai_em, .3), tS = em(c.sobe_em, 3), topo = 4.4, alto = c.altura_volta ?? 2.3;
        item.pose = { pos: [0, 2.4, 9.6], alvo: [0, 2.0, 0] };
        item.upd = t => { let y;
          if (t < tC) y = topo + .05 * Math.sin(t * 2);
          else if (t < tS) { const k = prog(t, tC, .65), b = t - tC - .65; y = k < 1 ? topo - (topo - .55) * k * k : .55 + Math.abs(Math.sin(b * 5.5)) * .9 * Math.exp(-b * 2.4); }
          else y = .55 + (alto - .55) * eback(prog(t, tS, 1.1)) + .06 * Math.sin((t - tS) * 2.2) * prog(t, tS + 1.1, .5);
          bola.position.y = y; const sq = y < .6 ? .8 : 1; bola.scale.set(1 / Math.sqrt(sq), sq, 1 / Math.sqrt(sq)); };
      } else if (c.tipo === "bussola") {
        // bússola: a agulha sai de "FATOS" e aponta para "EXPECTATIVAS" na palavra
        holofote(grupo, 0, 0, 1.9);
        grupo.add(caixa(.3, .8, .3, mCinza, 0, .4, 0));
        const bus = new T.Group(); bus.position.set(0, 2.5, 0); grupo.add(bus);
        const aro = cil(1.75, 1.75, .3, mObj, 64); aro.rotation.x = Math.PI / 2; bus.add(aro);
        const face = cil(1.6, 1.6, .32, mEsc, 64); face.rotation.x = Math.PI / 2; bus.add(face);
        for (let k = 0; k < 8; k++) bus.add(caixa(.05, k % 2 ? .12 : .22, .02, mObj, Math.sin(k * Math.PI / 4) * 1.4, Math.cos(k * Math.PI / 4) * 1.4, .17));
        const ag = new T.Group(); ag.position.z = .24; bus.add(ag);
        const pN = new T.Mesh(new T.ConeGeometry(.17, 1.25, 4), mAcesa()); pN.position.y = .62; ag.add(pN);
        const pS = new T.Mesh(new T.ConeGeometry(.17, 1.25, 4), mObj); pS.position.y = -.62; pS.rotation.z = Math.PI; ag.add(pS);
        const eixo = cil(.13, .13, .12, mObj, 16); eixo.rotation.x = Math.PI / 2; eixo.position.z = .3; bus.add(eixo);
        const cima = placaTexto([{ t: c.cima || "EXPECTATIVAS", tam: .17, cor: "#1a1420", mono: true }], 2.7, .42, COR); cima.position.set(0, 4.55, .2); grupo.add(cima);
        const baixo = placaTexto([{ t: c.baixo || "FATOS", tam: .17, cor: "#F2F2EE", mono: true }], 1.8, .42, "#2E2536"); baixo.position.set(0, .3, 1.1); grupo.add(baixo);
        const tE = em(c.em, 1.5);
        item.pose = { pos: [0, 2.6, 10.6], alvo: [0, 2.5, 0] };
        item.upd = t => { const k = eback(prog(t, tE, 1.0)); ag.rotation.z = Math.PI * (1 - k) + (.22 * Math.sin(t * 2.6)) * (1 - k) + .03 * Math.sin(t * 1.7);
          cima.material.opacity = .3 + .7 * eout(prog(t, tE, .5)); baixo.material.opacity = 1 - .5 * eout(prog(t, tE, .5)); };
      } else if (c.tipo === "cofre") {
        // cofre que abre na palavra: pilhas de moedas acendem lá dentro (o patrimônio)
        holofote(grupo, 0, 0, 2.0);
        grupo.add(caixa(2.4, 2.4, .15, mEsc, 0, 1.2, -.75), caixa(.15, 2.4, 1.6, mEsc, -1.15, 1.2, 0), caixa(.15, 2.4, 1.6, mEsc, 1.15, 1.2, 0),
          caixa(2.4, .15, 1.6, mEsc, 0, 2.33, 0), caixa(2.4, .15, 1.6, mEsc, 0, .08, 0));
        const porta = new T.Group(); porta.position.set(-1.2, 1.2, .85); grupo.add(porta);
        porta.add(caixa(2.4, 2.4, .16, mObj, 1.2, 0, 0));
        const roda = new T.Group(); roda.position.set(1.2, 0, .12); porta.add(roda);
        const rd = new T.Mesh(new T.TorusGeometry(.38, .05, 8, 24), mCinza); roda.add(rd); for (let k = 0; k < 3; k++) { const r2 = caixa(.76, .05, .05, mCinza, 0, 0, 0); r2.rotation.z = k * Math.PI / 3; roda.add(r2); }
        const pilhas = [-.55, 0, .55].map(x => { const g2 = new T.Group(); g2.position.set(x, .16, .1); grupo.add(g2);
          for (let j = 0; j < 7; j++) { const m = cil(.22, .22, .07, mAcesa(), 24); m.position.y = j * .085; g2.add(m); } return g2; });
        const tag = placaTexto([{ t: c.rotulo || "US$", tam: .28, cor: "#1a1420" }], 1.6, .55, COR); tag.position.set(0, 3.0, .3); grupo.add(tag);
        const tE = em(c.em, 1);
        item.pose = { pos: [0, 2.3, 9.0], alvo: [0, 1.5, 0] };
        item.upd = t => { roda.rotation.z = eio(prog(t, tE - .7, .7)) * Math.PI * 1.5; porta.rotation.y = -eio(prog(t, tE, 1.0)) * 1.75;
          pilhas.forEach((g2, i) => g2.scale.y = Math.max(.001, eback(prog(t, tE + .5 + i * .25, .5))));
          tag.material.opacity = eout(prog(t, tE + 1.1, .4)); tag.scale.setScalar(Math.max(.001, eback(prog(t, tE + 1.1, .4)))); };
      } else if (c.tipo === "escudo") {
        // escudo do gerenciamento de risco: as flechas vermelhas batem e caem
        holofote(grupo, 0, 0, 1.8);
        const esc = new T.Group(); esc.position.set(0, 2.3, .3); grupo.add(esc);
        const f = new T.Shape(); f.moveTo(0, 1.3); f.quadraticCurveTo(1.1, 1.25, 1.15, .9); f.lineTo(1.0, -.3); f.quadraticCurveTo(.6, -1.1, 0, -1.45);
        f.quadraticCurveTo(-.6, -1.1, -1.0, -.3); f.lineTo(-1.15, .9); f.quadraticCurveTo(-1.1, 1.25, 0, 1.3);
        const sh = new T.Mesh(new T.ExtrudeGeometry(f, { depth: .25, bevelEnabled: true, bevelSize: .06, bevelThickness: .06, bevelSegments: 2 }), mObj); sh.castShadow = true; esc.add(sh);
        const selo = placaTexto([{ t: c.selo || "RISCO", tam: .2, cor: "#1a1420", mono: true }], 1.7, .42, COR); selo.position.set(0, .1, .4); esc.add(selo);
        const vm = T3.vela_baixa || "#DC2626", mV = new T.MeshStandardMaterial({ color: vm, emissive: new T.Color(vm), emissiveIntensity: .5 });
        const fl = [-1, 0, 1].map(s => { const g2 = new T.Group(); const h = cil(.05, .05, 1.0, mV, 8); g2.add(h); const p = new T.Mesh(new T.ConeGeometry(.15, .32, 12), mV); p.position.y = -.64; p.rotation.z = Math.PI; g2.add(p);
          g2.rotation.x = Math.PI / 2; g2.visible = false; grupo.add(g2); return { g2, s }; });
        const tE = em(c.em, 1);
        item.pose = { pos: [0, 2.5, 9.8], alvo: [0, 2.1, 0] };
        item.upd = t => { let tr = 0; fl.forEach((o, k) => { const t0 = tE + k * .45, a = prog(t, t0, .45), cai = prog(t, t0 + .45, .7);
            o.g2.visible = t >= t0; o.g2.position.set(o.s * (.55 + 1.2 * (1 - a)), 2.5 + o.s * .25 - cai * cai * 2.2, 7.5 - 6.4 * eio(a) + cai * .9);
            o.g2.rotation.set(Math.PI / 2 + cai * 1.4, 0, cai * o.s * .8); if (a >= 1 && cai < .2) tr += (1 - cai * 5) * .07; });
          esc.position.x = Math.sin(t * 70) * tr; esc.rotation.y = .06 * Math.sin(t * .8); };
      } else if (c.tipo === "bifurcacao") {
        // placa de estrada com dois caminhos (esq e dir) e o "?" no alto
        holofote(grupo, 0, 0, 1.6);
        const poste = cil(.08, .1, 3.9, mCinza, 12); poste.position.y = 1.95; grupo.add(poste);
        const seta = (txt, s, y, cor, corT, t0) => { const g2 = new T.Group(); g2.position.set(0, y, .1); grupo.add(g2);
          const pl = placaTexto([{ t: txt, tam: .15, cor: corT, mono: true }], 2.1, .52, cor); pl.position.set(s * 1.1, 0, 0); g2.add(pl);
          const pt = new T.Mesh(new T.CircleGeometry(.36, 3), new T.MeshBasicMaterial({ color: cor, toneMapped: false })); pt.position.set(s * 2.3, 0, 0); pt.rotation.z = s > 0 ? 0 : Math.PI; g2.add(pt);
          return { g2, s, t0 }; };
        const A = seta(c.esq || "OPORTUNIDADE", -1, 3.0, COR, "#1a1420", em(c.esq_em, .5)), Bb = seta(c.dir || "RISCO", 1, 2.25, "#2E2536", "#F2F2EE", em(c.dir_em, 1.1));
        const q = placaTexto([{ t: c.selo || "?", tam: .4, cor: "#1a1420" }], .8, .7, COR); q.position.set(0, 4.2, .1); grupo.add(q);
        item.pose = { pos: [0, 2.6, 10.4], alvo: [0, 2.4, 0] };
        item.upd = t => { [A, Bb].forEach(o => { const k = eback(prog(t, o.t0, .6)); o.g2.rotation.y = (1 - k) * o.s * 1.4; o.g2.scale.setScalar(Math.max(.001, Math.min(1, k * 1.2))); });
          q.scale.setScalar(Math.max(.001, eback(prog(t, Math.max(A.t0, Bb.t0) + .5, .4)) * (1 + .04 * Math.sin(t * 4)))); };
      } else if (c.tipo === "seguir") {
        // celular com o perfil: o dedo aperta SEGUIR e vira SEGUINDO
        holofote(grupo, 0, 0, 1.5);
        const cel = new T.Group(); cel.position.set(0, 2.45, 0); grupo.add(cel);
        cel.add(caixa(1.85, 3.6, .16, mEsc, 0, 0, 0));
        const tela = (bot, cor, corT) => { const k = 256, cv = document.createElement("canvas"); cv.width = 1.65 * k; cv.height = 3.3 * k; const x = cv.getContext("2d");
          x.fillStyle = "#120d16"; x.fillRect(0, 0, cv.width, cv.height);
          x.fillStyle = COR; x.beginPath(); x.arc(cv.width / 2, 300, 130, 0, Math.PI * 2); x.fill();
          x.fillStyle = "#1a1420"; x.font = `800 120px '${FONTE}'`; x.textAlign = "center"; x.textBaseline = "middle"; x.fillText(c.inicial || "X", cv.width / 2, 306);
          const nomeP = c.perfil || "ESTÉFANO SANTOS"; let fsP = 46; x.font = `800 ${fsP}px '${FONTE}'`; const lP = x.measureText(nomeP).width; if (lP > cv.width * .86) fsP *= cv.width * .86 / lP;
          x.fillStyle = "#F2F2EE"; x.font = `800 ${fsP}px '${FONTE}'`; x.fillText(nomeP, cv.width / 2, 520);
          x.fillStyle = "#a69ab2"; x.font = `700 30px 'JetBrains Mono'`; x.fillText(c.bio || "MERCADO AMERICANO", cv.width / 2, 580);
          x.fillStyle = cor; const bw = 300, bh = 96; x.beginPath(); x.roundRect(cv.width / 2 - bw / 2, 650, bw, bh, 26); x.fill();
          x.fillStyle = corT; x.font = `800 44px '${FONTE}'`; x.fillText(bot, cv.width / 2, 700);
          for (let i = 0; i < 6; i++) { x.fillStyle = "#241b2c"; x.fillRect(30 + (i % 3) * 138, 800 + Math.floor(i / 3) * 140, 130, 130); }
          const tx = new T.CanvasTexture(cv); tx.colorSpace = T.SRGBColorSpace; const m = new T.Mesh(new T.PlaneGeometry(1.65, 3.3), new T.MeshBasicMaterial({ map: tx, toneMapped: false })); m.position.z = .085; cel.add(m); return m; };
        const t1 = tela(c.botao || "SEGUIR", COR, "#1a1420"), t2 = tela(c.botao2 || "SEGUINDO ✓", "#2E2536", "#F2F2EE"); t2.position.z = .086;
        const dedo = new T.Group(); grupo.add(dedo); const d1 = cil(.16, .18, 1.4, mObj, 16); d1.rotation.x = Math.PI / 2.4; dedo.add(d1);
        const tE = em(c.em, 1.2);
        item.pose = { pos: [0, 2.5, 8.6], alvo: [0, 2.45, 0] };
        item.upd = t => { const ida = eio(prog(t, tE - .7, .7)), volta = eio(prog(t, tE + .15, .6)), k = ida - volta;
          dedo.position.set(.25 + (1 - k) * 1.1, 1.55 - (1 - k) * 1.2, .9 + (1 - k) * .9); dedo.visible = k > .02; t2.visible = t >= tE; cel.rotation.y = .12 * Math.sin(t * .7);
          t1.scale.setScalar(t >= tE - .05 && t < tE + .15 ? .97 : 1); };
      } else if (c.tipo === "setas") {
        // duas setas grandes no mesmo dia: uma despenca (vermelha), a outra sobe (verde)
        const L = (c.lados || []).slice(0, 2).map((l, k) => { const x = (k ? 1 : -1) * 1.5, sobe = l.dir === "sobe"; holofote(grupo, x, 0, 1.0);
          const cor = sobe ? (T3.vela_alta || "#20BD5A") : (T3.vela_baixa || "#DC2626"), m = new T.MeshStandardMaterial({ color: cor, emissive: new T.Color(cor), emissiveIntensity: .45, roughness: .4 });
          const s2 = new T.Group(); grupo.add(s2); s2.add(caixa(.5, 1.6, .5, m, 0, 0, 0)); const p = new T.Mesh(new T.ConeGeometry(.62, .8, 4), m); p.rotation.y = Math.PI / 4; p.position.y = 1.2; s2.add(p);
          if (!sobe) s2.rotation.z = Math.PI;
          const nome = placaTexto([{ t: l.rotulo || "", tam: .16, cor: "#F2F2EE", mono: true }], 2.4, .4); nome.rotation.x = -1.2; nome.position.set(x, .03, 1.15); grupo.add(nome);
          const val = placaTexto([{ t: l.valor || "", tam: .3, cor: sobe ? "#1a1420" : "#F7F7F7" }], 2.0, .58, cor); grupo.add(val);
          return { s2, val, sobe, x, t0: em(l.em, .4 + k * 1.2) }; });
        item.pose = { pos: [0, 2.6, 10.8], alvo: [0, 2.1, 0] };
        item.upd = t => L.forEach(o => { const k = eback(prog(t, o.t0, .9)), y = o.sobe ? .8 + 1.8 * k : 3.0 - 1.8 * k;
          o.s2.position.set(o.x, y, 0); o.s2.scale.setScalar(Math.max(.001, Math.min(1, prog(t, o.t0 - .1, .25))));
          o.val.position.set(o.x, o.sobe ? y + 1.95 : y + 1.25, .3); o.val.material.opacity = eout(prog(t, o.t0 + .6, .4)); });
      } else if (c.tipo === "moeda") {
        // moeda gigante girando: frente e verso (oportunidade e risco no mesmo cenário)
        holofote(grupo, 0, 0, 1.6);
        const mo = new T.Group(); mo.position.set(0, 2.3, 0); grupo.add(mo);
        const mM = new T.MeshStandardMaterial({ color: COR, emissive: corA, emissiveIntensity: .2, roughness: .35, metalness: .45 });
        const disco = cil(1.3, 1.3, .2, mM, 64); disco.rotation.x = Math.PI / 2; mo.add(disco);
        const borda = new T.Mesh(new T.TorusGeometry(1.15, .04, 8, 64), mObj); mo.add(borda); const b2 = borda.clone(); b2.position.z = -.0; mo.add(b2);
        const fr = placaTexto([{ t: c.frente || "OPORTUNIDADE", tam: .16, cor: "#1a1420", mono: true }], 2.1, .5); fr.position.z = .11; mo.add(fr);
        const vs = placaTexto([{ t: c.verso || "RISCO", tam: .22, cor: "#1a1420", mono: true }], 2.1, .5); vs.position.z = -.11; vs.rotation.y = Math.PI; mo.add(vs);
        const tE = em(c.em, .8), giros = c.giros ?? 3;
        item.pose = { pos: [0, 2.4, 8.8], alvo: [0, 2.3, 0] };
        item.upd = t => { const k = prog(t, tE, 2.4); mo.rotation.y = eout(k) * Math.PI * 2 * giros + (k >= 1 ? Math.sin((t - tE - 2.4) * 1.1) * .45 : 0); mo.position.y = 2.3 + Math.sin(k * Math.PI) * .9; };
      } else if (c.tipo === "martelo") {
        // martelo da decisão: bate no bloco na palavra (placa = o que está sendo decidido)
        holofote(grupo, 0, 0, 1.8);
        grupo.add(caixa(3.0, .95, 1.4, mEsc, 0, .475, 0));
        if (c.placa) { const pl = placaTexto([{ t: c.placa, tam: .15, cor: "#1a1420", mono: true }], 2.6, .4, COR); pl.position.set(0, .5, .72); grupo.add(pl); }
        const bloco = cil(.55, .6, .25, mObj, 32); bloco.position.set(-.2, 1.07, 0); grupo.add(bloco);
        const mar = new T.Group(); mar.position.set(1.15, 1.42, 0); grupo.add(mar);
        const cabo = cil(.06, .07, 1.3, mObj, 12); cabo.rotation.z = Math.PI / 2; cabo.position.x = -.65; mar.add(cabo);
        const cab = cil(.24, .24, .8, mAcesa(), 24); cab.rotation.x = Math.PI / 2; cab.position.x = -1.35; mar.add(cab);
        const onda = new T.Mesh(new T.RingGeometry(.6, .66, 48), new T.MeshBasicMaterial({ color: COR, transparent: true, opacity: 0, toneMapped: false })); onda.rotation.x = -Math.PI / 2; onda.position.set(-.2, 1.21, 0); grupo.add(onda);
        const tE = em(c.em, 1.2);
        item.pose = { pos: [0, 2.4, 8.4], alvo: [0, 1.4, 0] };
        item.upd = t => { let a; if (t < tE - .45) a = -.95 + .05 * Math.sin(t * 3); else if (t < tE) a = -.95 * (1 - Math.pow(prog(t, tE - .45, .45), 2)); else a = -.55 * eout(prog(t, tE + .25, .6));
          mar.rotation.z = a; const k = prog(t, tE, .7); onda.material.opacity = t >= tE ? .8 * (1 - k) : 0; onda.scale.setScalar(1 + k * 2.2); };
      } else if (c.tipo === "ima") {
        // ímã: o dinheiro corre de um lado para o outro na palavra (esq = de onde sai, dir = para onde vai)
        holofote(grupo, 0, 0, 2.6);
        const im = new T.Group(); im.position.set(1.6, 1.6, 0); grupo.add(im);
        const u = new T.Mesh(new T.TorusGeometry(.62, .24, 14, 32, Math.PI), mAcesa()); u.rotation.z = Math.PI / 2; im.add(u);
        [-1, 1].forEach(s => { im.add(caixa(.55, .48, .48, mObj, -.3, s * .62, 0)); });
        const pe = cil(.6, .7, .25, mEsc, 24); pe.position.set(-1.6, .12, 0); grupo.add(pe);
        const le = placaTexto([{ t: c.esq || "BRASIL", tam: .16, cor: "#F2F2EE", mono: true }], 1.8, .38); le.rotation.x = -1.2; le.position.set(-1.6, .03, 1.15); grupo.add(le);
        const ld = placaTexto([{ t: c.dir || "EUA", tam: .16, cor: "#1a1420", mono: true }], 1.6, .38, COR); ld.position.set(1.6, 3.0, .1); grupo.add(ld);
        const tE = em(c.em, 1), mo = [...Array(8)].map((_, k) => { const m = cil(.2, .2, .06, mObj, 20); m.rotation.x = Math.PI / 2; grupo.add(m); return { m, k }; });
        item.pose = { pos: [0, 2.3, 9.4], alvo: [0, 1.5, 0] };
        item.upd = t => { im.position.x = 1.6 + .03 * Math.sin(t * 9) * prog(t, tE - .3, .3); mo.forEach(o => { const a = eio(prog(t, tE + o.k * .17, .8));
          const x0 = -1.6 + (o.k % 3 - 1) * .3, y0 = .3 + Math.floor(o.k / 3) * .14 + o.k * .02;
          o.m.position.set(x0 + (.75 - x0) * a, y0 + (1.6 + (o.k % 4 - 1.5) * .25 - y0) * a + Math.sin(a * Math.PI) * .9, 0); o.m.rotation.y = a * 6; }); };
      } else if (c.tipo === "domino") {
        // efeito dominó: uma peça derruba a próxima (pecas: [{t, em}], a primeira acesa)
        const Pc = (c.pecas || []).slice(0, 5), n = Pc.length, gap = 1.15;
        holofote(grupo, 0, 0, 2.7);
        const ps = Pc.map((p, k) => { const x = (k - (n - 1) / 2) * gap, g2 = new T.Group(); g2.position.set(x - .16, 0, 0); grupo.add(g2);
          const pc = caixa(.3, 1.9, .9, k === 0 ? mAcesa() : mObj, .16, .95, 0); g2.add(pc);
          const lb = placaTexto([{ t: p.t || "", tam: .1, cor: k === 0 ? "#1a1420" : "#F2F2EE", mono: true }], 1.1, .32, k === 0 ? COR : "#2E2536"); lb.position.set(x, .2, 1.0); grupo.add(lb);
          return { g2, lb, t0: em(p.em, .5 + k * .5), ult: k === n - 1 }; });
        item.pose = { pos: [0, 2.3, 9.4], alvo: [0, 1.1, 0] };
        item.upd = t => ps.forEach(o => { o.g2.rotation.z = -(o.ult ? 1.5 : 1.05) * Math.pow(prog(t, o.t0, .4), 2); o.lb.material.opacity = .35 + .65 * eout(prog(t, o.t0, .3)); });
      } else if (c.tipo === "escada") {
        // escada de degraus com rótulo: o boneco sobe um degrau a cada palavra (degraus: [{t, em}])
        const Dg = (c.degraus || []).slice(0, 4), n = Dg.length, dh = .7, dw = 1.25;
        holofote(grupo, 0, 0, 2.6);
        const x0 = -(n - 1) * dw / 2;
        const dd = Dg.map((d, k) => { const x = x0 + k * dw, h = (k + 1) * dh; const bl = caixa(dw, h, 1.3, k === n - 1 ? mAcesa() : mObj, x, h / 2, 0); grupo.add(bl);
          const lb = placaTexto([{ t: d.t || "", tam: .11, cor: k === n - 1 ? "#1a1420" : "#F2F2EE", mono: true }], 1.2, .3, k === n - 1 ? COR : "#2E2536"); lb.position.set(x, h / 2, .66); grupo.add(lb);
          return { x, h, t0: em(d.em, .5 + k * .7) }; });
        const bo = boneco(); bo.scale.setScalar(.62); grupo.add(bo);
        item.pose = { pos: [0, 2.6, 9.6], alvo: [0, 1.5, 0] };
        item.upd = t => { let x = x0 - dw, y = 0; dd.forEach((d, k) => { const a = eio(prog(t, d.t0, .5)); if (a > 0) { const px0 = k ? dd[k - 1].x : x0 - dw, py0 = k ? dd[k - 1].h : 0;
            x = px0 + (d.x - px0) * a; y = py0 + (d.h - py0) * a + Math.sin(a * Math.PI) * .35; } });
          bo.position.set(x, y, .1); bo.rotation.y = .5; };
      } else if (c.tipo === "leilao") {
        // leilão do Tesouro: o carimbo CANCELADO bate; depois os títulos voltam para a caixa (recompra)
        holofote(grupo, 0, 0, 2.3);
        grupo.add(caixa(1.4, 1.3, .9, mEsc, -.9, .65, 0)); const tp = placaTexto([{ t: c.placa || "LEILÃO", tam: .14, cor: "#1a1420", mono: true }], 1.25, .34, COR); tp.position.set(-.9, .95, .46); grupo.add(tp);
        const mart = new T.Group(); mart.position.set(-.9, 1.4, 0); grupo.add(mart); const ca = cil(.04, .04, .7, mObj, 8); ca.rotation.z = 1.1; mart.add(ca); const hd = cil(.11, .11, .32, mObj, 12); hd.rotation.x = Math.PI / 2; hd.position.set(-.28, .15, 0); mart.add(hd);
        const vm = T3.vela_baixa || "#DC2626", car = placaTexto([{ t: c.carimbo3d || "CANCELADO", tam: .2, cor: "#F7F7F7", mono: true }], 2.2, .5, vm); car.position.set(-.9, 2.15, .6); car.rotation.z = .12; grupo.add(car);
        const cx = new T.Group(); cx.position.set(1.15, 0, 0); grupo.add(cx); cx.add(caixa(1.5, .9, 1.1, mObj, 0, .45, 0));
        const tc = placaTexto([{ t: c.caixa || "TESOURO", tam: .13, cor: "#1a1420", mono: true }], 1.3, .3); tc.position.set(0, .45, .56); cx.add(tc);
        const pap = [...Array(6)].map((_, k) => { const p = caixa(.7, .04, .5, mAcesa(), 0, 0, 0); grupo.add(p); return { p, k }; });
        const tC = em(c.cancela_em, 1), tR = em(c.recompra_em, 3);
        item.pose = { pos: [0, 2.4, 9.2], alvo: [0, 1.3, 0] };
        item.upd = t => { const k = prog(t, tC, .3); car.scale.setScalar(Math.max(.001, 1.6 - .6 * eout(k)) * (k > 0 ? 1 : .001)); car.material.opacity = eout(k);
          mart.rotation.z = -.4 * Math.max(0, Math.sin(prog(t, tC - .4, .4) * Math.PI));
          pap.forEach(o => { const a = eio(prog(t, tR + o.k * .22, .7)); o.p.position.set(2.6 - 1.45 * a, 2.6 - (2.6 - (.95 + o.k * .05)) * a + Math.sin(a * Math.PI) * .6, 0); o.p.rotation.z = (1 - a) * 2; o.p.visible = t >= tR + o.k * .22; }); };
      } else if (c.tipo === "sismografo") {
        // sismógrafo: a agulha risca o papel e o tremor cresce na palavra (rotulo = o que está tremendo)
        holofote(grupo, 0, 0, 2.4);
        grupo.add(caixa(4.8, .5, 1.2, mEsc, 0, .9, 0)); [-2.3, 2.3].forEach(x => { const r = cil(.22, .22, 1.2, mCinza, 20); r.rotation.x = Math.PI / 2; r.position.set(x, 2.35, 0); grupo.add(r); });
        const k = 256, cv = document.createElement("canvas"); cv.width = 4.4 * k; cv.height = 2.0 * k; const x = cv.getContext("2d");
        const tx = new T.CanvasTexture(cv); tx.colorSpace = T.SRGBColorSpace; const pap = new T.Mesh(new T.PlaneGeometry(4.4, 2.0), new T.MeshBasicMaterial({ map: tx, toneMapped: false })); pap.position.set(0, 2.35, .02); grupo.add(pap);
        const ag = caixa(.05, .9, .05, mAcesa(), 0, 0, .1); grupo.add(ag);
        if (c.rotulo3d) { const lb = placaTexto([{ t: c.rotulo3d, tam: .16, cor: "#1a1420", mono: true }], 1.8, .4, COR); lb.position.set(0, .9, .62); grupo.add(lb); }
        const tE = em(c.em, 2), dur = c.ate - c.de;
        item.pose = { pos: [0, 2.3, 9.2], alvo: [0, 2.0, 0] };
        item.upd = t => { const N = 220, ate = Math.max(2, Math.floor(N * prog(t, c.de + .2, dur - .5)));
          x.fillStyle = "#EEEAF2"; x.fillRect(0, 0, cv.width, cv.height); x.strokeStyle = "rgba(60,40,80,.15)"; x.lineWidth = 2;
          for (let i = 1; i < 8; i++) { x.beginPath(); x.moveTo(0, i * cv.height / 8); x.lineTo(cv.width, i * cv.height / 8); x.stroke(); }
          x.strokeStyle = T3.vela_baixa || "#DC2626"; x.lineWidth = 9; x.lineJoin = "round"; x.beginPath(); let yy = 0;
          for (let i = 0; i < ate; i++) { const ti = c.de + .2 + (dur - .5) * i / N, amp = .04 + .4 * eio(prog(ti, tE, 2.0));
            yy = cv.height / 2 + amp * cv.height * Math.sin(i * 1.7) * Math.sin(i * .41 + 1.3); const px = cv.width * i / N; i ? x.lineTo(px, yy) : x.moveTo(px, yy); }
          x.stroke(); tx.needsUpdate = true; ag.position.set(-2.2 + 4.4 * ate / N, 2.35 + (yy - cv.height / 2) / k * -1 + .45, .1); };
      } else if (c.tipo === "cartao") {
        // cartão de crédito: a etiqueta do juro vira de "de" para "para" na palavra
        holofote(grupo, 0, 0, 1.9);
        const ct = new T.Group(); ct.position.set(0, 2.0, 0); grupo.add(ct);
        ct.add(caixa(3.0, 1.85, .08, mEsc, 0, 0, 0)); ct.add(caixa(3.0, .32, .09, new T.MeshStandardMaterial({ color: "#0b080d" }), 0, .45, .005));
        ct.add(caixa(.45, .35, .1, mAcesa(), -1.0, -.1, .01));
        const nm = placaTexto([{ t: c.titulo || "CRÉDITO", tam: .15, cor: "#F2F2EE", mono: true }], 2.0, .32); nm.position.set(.2, -.55, .05); ct.add(nm);
        const de = placaTexto([{ t: c.de_txt || "JURO", tam: .2, cor: "#F2F2EE", mono: true }], 2.2, .55, "#2E2536"), para = placaTexto([{ t: c.para_txt || "▲ JURO MAIS CARO", tam: .2, cor: "#F7F7F7", mono: true }], 2.2, .55, T3.vela_baixa || "#DC2626");
        [de, para].forEach(p => { p.position.set(0, 3.55, .1); grupo.add(p); });
        const fio = caixa(.02, .6, .02, mCinza, 0, 3.05, .05); grupo.add(fio);
        const tE = em(c.em, 1.2);
        item.pose = { pos: [0, 2.6, 9.0], alvo: [0, 2.5, 0] };
        item.upd = t => { const k = prog(t, tE, .35); de.rotation.x = eio(Math.min(1, k * 2)) * Math.PI / 2; de.visible = k < .5; para.rotation.x = -(1 - eio(Math.max(0, k * 2 - 1))) * Math.PI / 2; para.visible = k >= .5;
          ct.rotation.set(-.15 + .04 * Math.sin(t), .25 * Math.sin(t * .6), 0); ct.position.y = 2.0 - .25 * eout(k); };
      } else if (c.tipo === "foguete") {
        // foguete: sobe da base na palavra com chama e fumaça; depois paira
        holofote(grupo, 0, 0, 1.6);
        grupo.add(caixa(2.0, .25, 1.4, mEsc, 0, .125, 0));
        const fg = new T.Group(); grupo.add(fg);
        const corpo = cil(.38, .42, 1.9, mObj, 24); corpo.position.y = 1.2; fg.add(corpo);
        const nariz = new T.Mesh(new T.ConeGeometry(.38, .7, 24), mAcesa()); nariz.position.y = 2.5; fg.add(nariz);
        const jan = cil(.15, .15, .06, new T.MeshStandardMaterial({ color: "#2a1f3a", emissive: new T.Color(T3.cone || COR), emissiveIntensity: .5 }), 20); jan.rotation.x = Math.PI / 2; jan.position.set(0, 1.6, .4); fg.add(jan);
        [0, 1, 2].forEach(k => { const a = k * Math.PI * 2 / 3, al = caixa(.06, .55, .5, mAcesa(), Math.sin(a) * .42, .45, Math.cos(a) * .42); al.rotation.y = a; fg.add(al); });
        const ch = new T.Mesh(new T.ConeGeometry(.3, .9, 16), new T.MeshBasicMaterial({ color: COR, transparent: true, opacity: .9, toneMapped: false })); ch.rotation.z = Math.PI; ch.position.y = -.2; fg.add(ch);
        const fum = [...Array(8)].map((_, k) => { const s = new T.Mesh(new T.SphereGeometry(.35, 12, 8), new T.MeshBasicMaterial({ color: "#E9E4F2", transparent: true, opacity: 0, depthWrite: false, toneMapped: false })); grupo.add(s); return { s, k }; });
        const tE = em(c.em, .8), alto = c.altura ?? 1.6;
        item.pose = { pos: [0, 2.6, 9.6], alvo: [0, 2.3, 0] };
        item.upd = t => { const k = eio(prog(t, tE, 1.4)); fg.position.y = .25 + alto * k + .07 * Math.sin(t * 3) * k; fg.rotation.y = t * .4;
          ch.visible = t >= tE - .3; ch.scale.set(1, .7 + .3 * Math.sin(t * 30) + .4 * (1 - k), 1);
          fum.forEach(o => { const a = prog(t, tE + o.k * .12, 2.2); o.s.material.opacity = t >= tE ? .22 * (1 - a) : 0; o.s.position.set(Math.sin(o.k * 2.4) * (.4 + 1.4 * a), .3 + .2 * a, Math.cos(o.k * 2.4) * (.3 + .9 * a)); o.s.scale.setScalar(.5 + 1.2 * a); }); };
      } else if (c.tipo === "chip") {
        // chip de IA no centro: as trilhas acendem e ligam os servidores (em, servidores_em)
        holofote(grupo, 0, 0, 2.6);
        const ch = new T.Group(); ch.position.set(0, .2, .6); grupo.add(ch);
        ch.add(caixa(1.4, .25, 1.4, mEsc, 0, .125, 0)); const top = caixa(.9, .06, .9, mAcesa(), 0, .28, 0); ch.add(top);
        for (let s = 0; s < 4; s++) for (let k = 0; k < 5; k++) { const p = caixa(.08, .06, .22, mObj, 0, .06, 0); const d = -.48 + k * .24, a = s * Math.PI / 2;
          p.position.set(Math.sin(a) * .8 + Math.cos(a) * d, .06, Math.cos(a) * .8 - Math.sin(a) * d); p.rotation.y = a; ch.add(p); }
        const lb = placaTexto([{ t: c.chip || "IA", tam: .3, cor: "#1a1420" }], .8, .5); lb.rotation.x = -Math.PI / 2; lb.position.set(0, .32, 0); ch.add(lb);
        const srv = [-1.9, -.65, .65, 1.9].map((x, k) => { const g2 = new T.Group(); g2.position.set(x, 0, -1.4); grupo.add(g2); g2.add(caixa(.95, 2.4, .9, mEsc, 0, 1.2, 0));
          const luz = [...Array(5)].map((_, j) => { const m = new T.MeshStandardMaterial({ color: "#2a2230", emissive: corA, emissiveIntensity: 0 }); const l = caixa(.7, .08, .02, m, 0, .45 + j * .42, .46); g2.add(l); return m; });
          const tr = caixa(.06, .02, 1, new T.MeshBasicMaterial({ color: COR, transparent: true, opacity: 0, toneMapped: false }), 0, .02, 0); grupo.add(tr);
          const dx = x - 0, dz = -1.4 - .6, L = Math.hypot(dx, dz); tr.scale.z = L; tr.position.set(x / 2, .02, (-1.4 + .6) / 2); tr.rotation.y = Math.atan2(dx, dz);
          return { luz, tr, k }; });
        const tE = em(c.em, .8), tS = em(c.servidores_em, 2.5);
        item.pose = { pos: [0, 3.2, 8.4], alvo: [0, 1.0, -.4] };
        item.upd = t => { top.material.emissiveIntensity = .3 + .5 * eout(prog(t, tE, .5)) + .1 * Math.sin(t * 5);
          srv.forEach(s => { const a = prog(t, tS + s.k * .3, .5); s.tr.material.opacity = .9 * a; s.luz.forEach((m, j) => { const on = a > 0 && Math.sin(t * 9 + j * 1.7 + s.k) > -.2; m.emissiveIntensity = on ? .9 * a : 0; m.color.set(on && a > 0 ? COR : "#2a2230"); }); }); };
      } else if (c.tipo === "planta") {
        // planta que cresce no vaso: as folhas abrem e brotam moedas (construir com o tempo)
        holofote(grupo, 0, 0, 1.6);
        grupo.add(cil(.75, .55, .9, mEsc, 24)); grupo.children[grupo.children.length - 1].position.y = .45;
        const terra = cil(.7, .7, .05, new T.MeshStandardMaterial({ color: "#2a1f2e" }), 24); terra.position.y = .88; grupo.add(terra);
        const caule = cil(.06, .08, 1, new T.MeshStandardMaterial({ color: T3.vela_alta || "#20BD5A", roughness: .6 }), 10); grupo.add(caule);
        const folhas = [...Array(6)].map((_, k) => { const f = new T.Mesh(new T.SphereGeometry(.32, 12, 8), new T.MeshStandardMaterial({ color: T3.vela_alta || "#20BD5A", roughness: .5 })); f.scale.set(1, .25, .55); grupo.add(f); return { f, k }; });
        const moedas = [...Array(3)].map((_, k) => { const m = cil(.2, .2, .05, mAcesa(), 20); m.rotation.x = Math.PI / 2; grupo.add(m); return { m, k }; });
        const tE = em(c.em, .5), tF = c.fim_em ?? c.ate - .8, HC = 2.4;
        item.pose = { pos: [0, 2.3, 8.4], alvo: [0, 1.8, 0] };
        item.upd = t => { const g = eio(prog(t, tE, tF - tE)), h = .05 + HC * g; caule.scale.y = h; caule.position.y = .9 + h / 2;
          folhas.forEach(o => { const a = eback(prog(g, o.k / 7, .25)), y = .9 + HC * (o.k + 1) / 7.5, s = o.k % 2 ? 1 : -1; o.f.visible = a > 0; o.f.position.set(s * .32 * a, y, 0); o.f.rotation.z = s * -.5; o.f.scale.set(Math.max(.001, a), .25 * Math.max(.001, a), .55 * Math.max(.001, a)); });
          moedas.forEach(o => { const a = eback(prog(t, tF - .6 + o.k * .25, .5)); o.m.visible = a > 0; o.m.scale.setScalar(Math.max(.001, a)); o.m.position.set((o.k - 1) * .55, .9 + HC * (.55 + o.k % 2 * .2), .15); o.m.rotation.y = t * 2; }); };
      } else if (c.tipo === "dado") {
        // dado rolando: o resultado não é garantido
        holofote(grupo, 0, 0, 1.9);
        const dd = new T.Group(); grupo.add(dd); dd.add(caixa(1.1, 1.1, 1.1, mObj, 0, 0, 0));
        const pt = (x, y, z) => { const p = new T.Mesh(new T.SphereGeometry(.09, 10, 8), mEsc); p.position.set(x, y, z); dd.add(p); };
        const F = .56, o = .28; pt(0, 0, F); [[-o, -o], [o, o]].forEach(([a, b]) => pt(a, b, -F)); [[-o, o], [0, 0], [o, -o]].forEach(([a, b]) => pt(F, a, b));
        [[-o, -o], [o, o], [-o, o], [o, -o]].forEach(([a, b]) => pt(-F, a, b)); [[-o, -o], [o, o], [-o, o], [o, -o], [0, 0]].forEach(([a, b]) => pt(a, F, b)); [[-o, -o], [o, o], [-o, o], [o, -o], [-o, 0], [o, 0]].forEach(([a, b]) => pt(a, -F, b));
        const tE = em(c.em, .5);
        item.pose = { pos: [0, 2.4, 8.4], alvo: [0, 1.4, 0] };
        item.upd = t => { const k = prog(t, tE, 1.8), e = eout(k); dd.position.set(-2.2 + 2.2 * e, .55 + Math.abs(Math.sin(k * Math.PI * 3)) * 1.4 * (1 - k), 0);
          dd.rotation.set((1 - e) * 9 + .1, (1 - e) * 6 + .5 + .05 * Math.sin(t), (1 - e) * 7); };
      } else if (c.tipo === "urna") {
        // urna: as cédulas caem dentro; na palavra sobe a placa do resultado
        holofote(grupo, 0, 0, 1.8);
        grupo.add(caixa(1.8, 1.5, 1.3, mObj, 0, .75, 0), caixa(.8, .05, .12, mEsc, 0, 1.52, 0));
        const nm = placaTexto([{ t: c.titulo || "URNA", tam: .16, cor: "#1a1420", mono: true }], 1.4, .34, COR); nm.position.set(0, .8, .66); grupo.add(nm);
        const ced = [...Array(6)].map((_, k) => { const p = caixa(.55, .02, .38, mObj, 0, 0, 0); grupo.add(p); return { p, k }; });
        const res = placaTexto([{ t: c.resultado || "RESULTADO", tam: .2, cor: "#1a1420", mono: true }], 2.6, .55, COR); res.position.set(0, 3.0, .2); grupo.add(res);
        const tE = em(c.em, 2.5);
        item.pose = { pos: [0, 2.3, 9.0], alvo: [0, 1.5, 0] };
        item.upd = t => { ced.forEach(o => { const a = prog(t, c.de + .2 + o.k * .35, .6); o.p.visible = a > 0 && a < 1; o.p.position.set((o.k % 2 ? .3 : -.3) * (1 - a), 4.2 - 2.65 * a, 0); o.p.rotation.set(a * 2, o.k, (1 - a) * 1.5); });
          res.scale.setScalar(Math.max(.001, eback(prog(t, tE, .5)))); res.material.opacity = eout(prog(t, tE, .3)); };
      } else if (c.tipo === "alvo") {
        // alvo: a aposta mirava o centro ("mira") e o dardo cai fora na palavra (expectativa frustrada)
        holofote(grupo, 0, 0, 1.9);
        const al = new T.Group(); al.position.set(0, 2.5, 0); grupo.add(al);
        [1.5, 1.15, .8, .45].forEach((r, k) => { const d = cil(r, r, .12 + k * .02, k % 2 ? mObj : mEsc, 48); d.rotation.x = Math.PI / 2; d.position.z = k * .02; al.add(d); });
        const cen = cil(.18, .18, .2, mAcesa(), 24); cen.rotation.x = Math.PI / 2; cen.position.z = .1; al.add(cen);
        grupo.add(caixa(.2, 1.0, .2, mCinza, 0, .5, -.2));
        const mira = placaTexto([{ t: c.mira || "MUDANÇA", tam: .16, cor: "#1a1420", mono: true }], 2.0, .4, COR); mira.position.set(0, 4.35, .2); grupo.add(mira);
        const dar = new T.Group(); grupo.add(dar); const hs = cil(.035, .035, .9, mObj, 8); hs.rotation.x = Math.PI / 2; dar.add(hs);
        const pn = new T.Mesh(new T.ConeGeometry(.07, .22, 10), mEsc); pn.rotation.x = -Math.PI / 2; pn.position.z = -.55; dar.add(pn);
        const pena = caixa(.3, .02, .25, mAcesa(), 0, 0, .4); dar.add(pena);
        const tE = em(c.em, 2), fx = 1.05, fy = -1.25;
        item.pose = { pos: [0, 2.6, 9.6], alvo: [0, 2.3, 0] };
        item.upd = t => { const a = eio(prog(t, tE, .5)); dar.visible = t >= tE - .1; dar.position.set(fx * a, 2.5 + .6 * (1 - a) + fy * a, 7 - 6.6 * a); dar.rotation.z = a * .3;
          mira.material.opacity = 1 - .55 * eout(prog(t, tE + .5, .4)); al.rotation.z = a >= 1 ? .03 * Math.sin((t - tE) * 25) * Math.exp(-(t - tE - .5) * 4) : 0; };
      } else if (c.tipo === "balao") {
        // balão que enche na palavra (rotulo = o que cresce: gastos, dívida)
        holofote(grupo, 0, 0, 1.6);
        const bl = new T.Mesh(new T.SphereGeometry(1, 32, 24), new T.MeshStandardMaterial({ color: T3.vela_baixa || "#DC2626", roughness: .35, emissive: new T.Color(T3.vela_baixa || "#DC2626"), emissiveIntensity: .15 })); grupo.add(bl);
        const no = new T.Mesh(new T.ConeGeometry(.12, .2, 12), bl.material); no.rotation.z = Math.PI; grupo.add(no);
        const fio = caixa(.015, 1, .015, mCinza, 0, 0, 0); grupo.add(fio);
        grupo.add(caixa(.7, .3, .7, mEsc, 0, .15, 0));
        const lb = placaTexto([{ t: c.rotulo3d || "DÍVIDA", tam: .2, cor: "#F7F7F7", mono: true }], 1.6, .45); grupo.add(lb);
        const tE = em(c.em, .6), tF = c.fim_em ?? c.ate - .8, r0 = .35, r1 = c.raio ?? 1.45;
        item.pose = { pos: [0, 2.4, 9.4], alvo: [0, 2.3, 0] };
        item.upd = t => { const r = r0 + (r1 - r0) * eio(prog(t, tE, tF - tE)) + .02 * Math.sin(t * 3); const cy = .3 + 1.1 + r; bl.scale.set(r, r * 1.1, r); bl.position.set(.05 * Math.sin(t * .8), cy, 0);
          no.position.set(bl.position.x, cy - r * 1.1 - .05, 0); fio.scale.y = cy - r * 1.1 - .3; fio.position.set(0, .3 + (cy - r * 1.1 - .3) / 2, 0); lb.position.set(bl.position.x, cy, r + .02); lb.scale.setScalar(.6 + .4 * r / r1); };
      } else if (c.tipo === "ponte") {
        // ponte entre dois lados: o boneco atravessa (esq -> dir) na palavra
        holofote(grupo, 0, 0, 2.6);
        grupo.add(caixa(1.4, 1.2, 1.4, mEsc, -2.0, .6, 0), caixa(1.4, 1.2, 1.4, mAcesa(), 2.0, .6, 0), caixa(2.8, .12, .9, mObj, 0, 1.15, 0));
        [-1, 1].forEach(s => { grupo.add(caixa(2.8, .05, .05, mCinza, 0, 1.6, s * .42)); for (let k = 0; k < 6; k++) grupo.add(caixa(.04, .45, .04, mCinza, -1.25 + k * .5, 1.38, s * .42)); });
        const le = placaTexto([{ t: c.esq || "BRASIL", tam: .15, cor: "#F2F2EE", mono: true }], 1.4, .34); le.position.set(-2.0, .6, .71); grupo.add(le);
        const ld = placaTexto([{ t: c.dir || "EUA", tam: .15, cor: "#1a1420", mono: true }], 1.4, .34); ld.position.set(2.0, .6, .71); grupo.add(ld);
        if (c.selo) { const sl = placaTexto([{ t: c.selo, tam: .14, cor: "#1a1420", mono: true }], 2.6, .36, COR); sl.position.set(0, 2.0, .45); grupo.add(sl); }
        const bo = boneco(); bo.scale.setScalar(.55); grupo.add(bo);
        const tE = em(c.em, 1), tF = c.fim_em ?? tE + 3;
        item.pose = { pos: [0, 2.6, 9.6], alvo: [0, 1.4, 0] };
        item.upd = t => { const a = eio(prog(t, tE, tF - tE)); bo.position.set(-2.0 + 4.0 * a, 1.2 + Math.abs(Math.sin(a * 18)) * .05, 0); bo.rotation.y = Math.PI / 2 * (a > 0 && a < 1 ? 1 : .3); };
      } else if (c.tipo === "mesa") {
        // réplica da cena da referência Ludificando: monitor com play aceso sobre a base, monte de moedas douradas que
        // chovem e empilham, fileira de teclas com ícone; as últimas "acesas" teclas acendem na palavra (acende_em)
        holofote(grupo, 0, .3, 2.6);
        const mOuro = new T.MeshStandardMaterial({ color: T3.ouro || "#B8955A", roughness: .5, metalness: .3 });   // ouro pálido da referência (não brilha)
        const dx = -.35, base = caixa(2.7, .95, 1.55, mObj, dx, .475, 0); grupo.add(base);
        const mon = new T.Group(); mon.position.set(dx, 0, -.05); grupo.add(mon);
        mon.add(caixa(.62, .06, .38, mEsc, 0, .98, 0), caixa(.09, .55, .09, mEsc, 0, 1.25, -.02));
        const tela = caixa(2.25, 1.3, .12, mObj, 0, 2.05, -.05); mon.add(tela);
        const tri = new T.Shape(); tri.moveTo(-.2, -.25); tri.lineTo(.3, 0); tri.lineTo(-.2, .25); tri.closePath();
        const play = new T.Mesh(new T.ShapeGeometry(tri), mAcesa()); play.position.set(0, 2.05, .02); mon.add(play);
        const moedas = []; const pilhas = c.pilhas || [[2.3, -.4, 19], [1.85, -.15, 14], [2.75, -.1, 14], [2.3, .2, 12], [1.8, .4, 9], [2.75, .45, 9], [3.2, -.35, 10], [1.85, -.7, 11], [2.75, -.8, 12], [2.3, .7, 6], [3.2, .3, 6], [1.4, .1, 6], [3.25, .75, 3], [1.4, .65, 3]];
        pilhas.forEach(([px, pz, h], k) => { for (let j = 0; j < h; j++) { const m = cil(.235, .235, .066, mOuro, 28); grupo.add(m); moedas.push({ m, x: px + dx, z: pz, y: .034 + j * .07, ord: k * 2 + j }); } });
        moedas.forEach(o => { o.m.userData.luz = true; });   // a chuva já é a entrada das moedas (fora da montagem)
        const nT = c.teclas || 7, acesas = c.acesas ?? 2, teclas = [];
        if (!TX_DERRAME) TX_DERRAME = gradiente(COR, .55);
        const mIcone = new T.MeshStandardMaterial({ color: "#d8d8d4", emissive: new T.Color("#ffffff"), emissiveIntensity: .62, roughness: .5 }); mIcone.toneMapped = false; mIcone.userData.aceso = true;
        for (let k = 0; k < nT; k++) { const x = dx - 2.1 + k * .72;
          const tc = caixa(.6, .34, .6, mEsc, x, .17, 1.45); grupo.add(tc);
          const on = caixa(.608, .348, .608, null, x, .172, 1.45); on.visible = false; on.castShadow = false; grupo.add(on); tc.userData.casca = on;
          // luz da tecla derramada no chão (o "glow" da referência é isto: amarelo suave no chão em volta, não um halo branco)
          const der = new T.Mesh(new T.PlaneGeometry(1.25, 1.25), matLuz(TX_DERRAME, 0)); der.rotation.x = -Math.PI / 2; der.position.set(x, .012, 1.62);
          der.userData.luz = true; grupo.add(der); tc.userData.derrame = der;
          const ic = caixa(.3, .13, .2, mIcone, x, .43, 1.45); grupo.add(ic);
          grupo.add(caixa(.4, .03, .3, mEsc, x, .36, 1.45));   // bandeja escura sob o ícone (como a referência)
          teclas.push({ tc }); }
        const novaOn = () => { const m = mAcesa(); m.transparent = true; if (P.acesos !== false) { m.userData.aceso = true; m.toneMapped = false; m.emissiveIntensity = .7; m.color = corA.clone().multiplyScalar(.42); m.roughness = .55; } return m; };
        teclas.forEach(o => { o.tc.userData.casca.material = novaOn(); });
        const tChuva = em(c.em, .35), fases = [{ n: acesas, t: em(c.acende_em, 1.6) }];
        for (let j = i + 1; cenas[j] && cenas[j].continua; j++) fases.push({ n: cenas[j].acesas ?? fases[fases.length - 1].n, t: cenas[j].acende_em ?? cenas[j].de + .6 });
        const quandoAcende = k => { const f = fases.filter(f => k >= nT - f.n).sort((a, b) => a.t - b.t)[0]; return f ? f.t + (k - (nT - f.n)) * .07 : 1e9; };
        item.pose = { pos: [0, 3.0, 9.2], alvo: [.15, 1.0, .5] };
        item.upd = t => { moedas.forEach(o => { const a = prog(t, tChuva + o.ord * .045, .5); o.m.visible = a > 0;
            o.m.position.set(o.x + .02 * Math.sin(o.ord), o.y + 4.2 * (1 - a * a) , o.z); o.m.rotation.set(.6 * (1 - a), o.ord, .4 * (1 - a)); });
          teclas.forEach((o, k) => { const a = prog(t, quandoAcende(k), .28), cs = o.tc.userData.casca;   // acende em .28 s com pulso
            cs.visible = a > 0; cs.material.opacity = eout(a); cs.scale.setScalar(1 + .12 * Math.sin(Math.PI * a));
            o.tc.userData.derrame.material.opacity = (P.derrame ?? .34) * eout(a); }); };
      } else if (c.tipo === "hemiciclo") {
        // plenário da referência: fileiras em arco de assentos-cápsula que acendem assento a assento, da esquerda para a
        // direita, junto com o contador do cartão. "acende": {"fracao": 0.6 | "n": 308, "total": 513, "em", "dur"}
        holofote(grupo, 0, .6, 3.6);
        const fil = c.fileiras || 5, R0 = c.raio || 2.0, dR = .5, tot = c.n || 95, raios = [...Array(fil)].map((_, r) => R0 + r * dR);
        const soma = raios.reduce((a, b) => a + b, 0), mOnH = novoAceso(), assentos = [];
        const capGeo = new T.CapsuleGeometry(.1, .09, 6, 14), mApag = new T.MeshStandardMaterial({ color: T3.assento || "#3D3C38", roughness: .7 });
        if (c.zoom3d == null) c.zoom3d = 1.3; if (c.elevacao == null) c.elevacao = 34;
        raios.forEach((R, r) => { const n = Math.max(5, Math.round(tot * R / soma));
          for (let k = 0; k < n; k++) { const a = Math.PI * (.05 + .9 * k / (n - 1)), x = -Math.cos(a) * R, z = 1.0 - Math.sin(a) * R * .82;
            const g2 = new T.Group(); g2.position.set(x, r * .16, z); g2.rotation.y = Math.atan2(-x, 1.0 - z); grupo.add(g2);
            const cap = new T.Mesh(capGeo, mApag); cap.position.y = .15; cap.castShadow = true; g2.add(cap);
            assentos.push({ a, r, ms: [cap], ord: a + (rnd3() - .5) * .55 }); } });
        assentos.sort((p, q) => p.ord - q.ord);   // onda da esquerda para a direita, salpicada (como a referência)
        const ac = c.acende || {}, alvo = ac.fracao ?? (ac.n != null ? ac.n / (ac.total || ac.n) : 1), tA = em(ac.em, .5), dA = ac.dur ?? 1.6;
        item.pose = { pos: [0, 4.4, 8.4], alvo: [0, .5, -.6] };
        item.upd = t => { const na = Math.round(assentos.length * alvo * eout(prog(t, tA, dA)));
          assentos.forEach((p, k) => { p.ms[0].material = k < na ? mOnH : mApag; }); };
      } else if (c.tipo === "semana") {
        // fileira dos dias, como no viral da 6x1: cubos largos e baixos com o DIA GRAVADO NA FRENTE, maleta branca em cima
        // (trabalho) que vira cama (folga) quando o cubo acende; câmera BAIXA e perto, a fileira sai cortada no quadro;
        // "voce": true faz o manequim nascer na 1ª folga num disco amarelo que desce. "folgas": [5, 6] ou [{"dia": 5, "em"}]
        holofote(grupo, 0, 0, 3.6);
        const dias = c.dias || ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"], n = dias.length, passo = 1.16, mOnS = novoAceso(), mBranco = matBranco();
        if (!TX_DERRAME) TX_DERRAME = gradiente(COR, .55);
        const mCubo = new T.MeshStandardMaterial({ color: T3.cinza || "#57564F", roughness: .75 });
        const fol = (c.folgas || [n - 2, n - 1]).map((f, j) => typeof f === "number" ? { dia: f, em: em(null, .8 + j * .6) } : { dia: f.dia, em: em(f.em, .8 + j * .6) });
        const cubos = dias.map((d, k) => { const x = (k - (n - 1) / 2) * passo;
          const cb = caixa(1.0, .5, .86, mCubo, x, .25, 0); grupo.add(cb);
          const rt = placaTexto([{ t: d, tam: .15, cor: "#AEAEA4", mono: true, peso: 700 }], .9, .26); rt.position.set(x, .2, .432); rt.userData.rotulo = true; grupo.add(rt);
          const mal = new T.Group(); mal.position.set(x, .5, 0); grupo.add(mal);
          mal.add(caixa(.5, .32, .17, mBranco, 0, .16, 0));
          const al = new T.Mesh(new T.TorusGeometry(.085, .022, 8, 20, Math.PI), mBranco); al.position.set(0, .32, 0); mal.add(al);
          const cama = new T.Group(); cama.position.set(x, .5, 0); cama.visible = false; grupo.add(cama);
          cama.add(caixa(.7, .1, .48, mEsc, 0, .05, 0), caixa(.64, .1, .44, mBranco, 0, .15, 0), caixa(.2, .08, .36, mBranco, -.2, .24, 0), caixa(.7, .26, .06, mEsc, -.33, .13, 0));
          const der = new T.Mesh(new T.PlaneGeometry(1.6, 1.6), matLuz(TX_DERRAME, 0)); der.rotation.x = -Math.PI / 2; der.position.set(x, .012, .3); der.userData.luz = true; grupo.add(der);
          const f = fol.find(q => q.dia === k); return { cb, mal, cama, der, t: f ? f.em : null }; });
        const f0 = fol[0], xf = f0 ? (f0.dia - (n - 1) / 2) * passo : 0;
        let bo = null, disco = null; const corte = new T.Plane(new T.Vector3(0, 1, 0), 0);
        if (c.voce && f0) { bo = manequim(); bo.position.set(xf - .08, .5, -.1); grupo.add(bo); ren.localClippingEnabled = true;
          bo.userData.mats.forEach(m => { m.clippingPlanes = [corte]; });
          disco = cil(.42, .42, .05, novoAceso(), 40); disco.position.set(xf - .08, .5, -.1); disco.castShadow = false; grupo.add(disco); }
        const tV = em(c.voce_em, f0 ? (f0.em - c.de) + .2 : 1);
        item.fixo = true;   // câmera baixa da referência, sem enquadramento automático
        if (c.elevacao == null) c.elevacao = 7;
        const xc = c.foco_x ?? (f0 ? xf - passo * 1.2 : 0);
        item.pose = { pos: [xc + .3, 1.75, 6.2], alvo: [xc, 1.05, 0] };
        item.upd = t => { cubos.forEach(o => { const a = o.t == null ? 0 : prog(t, o.t, .3);
            o.cb.material = a > 0 ? mOnS : mCubo; o.cb.scale.setScalar(1 + .05 * Math.sin(Math.PI * a)); o.mal.visible = a <= 0; o.cama.visible = a > 0;
            o.der.material.opacity = (P.derrame ?? .34) * eout(a); });
          if (bo) { const a = prog(t, tV, .75), yD = .5 + 2.05 * (1 - eio(a)), wy = grupo.position.y + yD;   // o disco desce e o manequim aparece acima dele
            bo.visible = a > 0; disco.visible = a > 0 && a < 1; disco.position.y = yD; disco.material.opacity = 1;
            corte.constant = -(a >= 1 ? -99 : wy); } };
      } else if (c.tipo === "documento") {
        // tela/documento do viral da 6x1: TELA BRANCA ACESA (brilha), sem moldura escura, título pequeno cinza no topo e o
        // texto centralizado em cinza; a palavra entre *asteriscos* aparece letra por letra com um cursor amarelo ("revela_em")
        // e depois ganha grifo. "linhas": ["...", {"t": "UM DELES,", "tam": 1.25}, "*PREFERENCIALMENTE*", ...]
        holofote(grupo, 0, 0, 2.6);
        const Wd = c.largura || 3.7, Hd = c.altura || 2.5, y0 = .95;
        const pe = caixa(1.0, y0, .62, mObj, 0, y0 / 2, -.05); grupo.add(pe);
        const cw = 1024, ch = Math.round(cw * Hd / Wd), cvd = document.createElement("canvas"); cvd.width = cw; cvd.height = ch; const xd = cvd.getContext("2d");
        const txd = new T.CanvasTexture(cvd); txd.colorSpace = T.SRGBColorSpace; txd.anisotropy = 4;
        const tela = new T.Mesh(caixaArred(Wd, Hd, .1), new T.MeshBasicMaterial({ color: "#E9E9E3", toneMapped: false }));
        tela.position.set(0, y0 + Hd / 2 + .05, 0); tela.userData.rotulo = true; tela.castShadow = false; grupo.add(tela);
        const face = new T.Mesh(new T.PlaneGeometry(Wd - .08, Hd - .08), new T.MeshBasicMaterial({ map: txd, toneMapped: false }));
        face.position.set(0, y0 + Hd / 2 + .05, .052); face.userData.rotulo = true; grupo.add(face);
        // a tela da referência BRILHA: halo branco suave em volta (aditivo, atrás)
        const halo = new T.Mesh(new T.PlaneGeometry(Wd * 1.9, Hd * 2.1), matLuz(gradiente("#ffffff", .5), P.halo_tela ?? .55)); halo.position.set(0, y0 + Hd / 2 + .05, -.12); halo.userData.luz = true; grupo.add(halo);
        const linhas = (c.linhas || ["REPOUSO: 2 DIAS POR SEMANA,", { t: "UM DELES,", tam: 1.25 }, { t: "*PREFERENCIALMENTE*", tam: 1.25 }, "AOS DOMINGOS"]).map(l => typeof l === "string" ? { t: l, tam: 1 } : l);
        const tR = em(c.revela_em, 1.2), dR = c.revela_dur ?? 1.1;
        let ult = "";
        const pinta = (kr, kg, cur) => { const chave = kr.toFixed(3) + kg.toFixed(2) + cur; if (chave === ult) return; ult = chave;
          xd.fillStyle = "#F4F4EF"; xd.fillRect(0, 0, cw, ch); xd.textAlign = "center"; xd.textBaseline = "middle";
          xd.fillStyle = "#B1B1A8"; xd.font = `500 ${Math.round(ch * .042)}px 'Inter Tight'`; xd.fillText(c.titulo || "EMENDA CONSTITUCIONAL · FIM DA 6x1", cw / 2, ch * .1);
          const base = ch * (c.tam_linha || .088); let tot = 0; linhas.forEach(l => { tot += base * l.tam * 1.45; });
          let y = ch * .52 - tot / 2;
          linhas.forEach(l => { const fs = Math.round(base * l.tam); xd.font = `700 ${fs}px '${FONTE}'`; let txt = l.t.replace(/\*/g, ""), marca = /\*/.test(l.t);
            let w = xd.measureText(txt).width; if (w > cw * .88) { const k = cw * .88 / w; xd.font = `700 ${Math.floor(fs * k)}px '${FONTE}'`; w *= k; }
            const yy = y + fs * .72;
            if (marca) { const nL = Math.round(txt.length * kr), vis = txt.slice(0, nL), wv = xd.measureText(vis).width, x0 = cw / 2 - w / 2;
              if (kg > 0) { xd.globalAlpha = kg * .9; xd.fillStyle = COR; xd.fillRect(x0 - 10, yy - fs * .62, w + 20, fs * 1.22); xd.globalAlpha = 1; }
              xd.textAlign = "left"; xd.fillStyle = "#6E6E66"; xd.fillText(vis, x0, yy); xd.textAlign = "center";
              if (cur) { xd.fillStyle = COR; xd.fillRect(x0 + wv + 4, yy - fs * .55, Math.max(6, fs * .09), fs * 1.1); } }
            else { xd.fillStyle = "#77776F"; xd.fillText(txt, cw / 2, yy); }
            y += fs * 1.45; });
          txd.needsUpdate = true; };
        item.fixo = true; if (c.elevacao == null) c.elevacao = 6;   // referência: a tela no meio do quadro, quase de frente
        item.pose = { pos: [0, y0 + Hd / 2 + .8, 6.3], alvo: [0, y0 + Hd / 2 + .45, 0] };
        item.upd = t => { const kr = prog(t, tR, dR), pisca = t >= tR - .5 && t < tR + dR + .6 && Math.floor(t * 3.2) % 2 === 0;
          pinta(kr, eout(prog(t, tR + dR + .25, .35)), pisca ? 1 : 0); };
      } else if (c.tipo === "pilha") {
        // pilha de moedas que cresce (construir aos poucos); rotulo3d na placa da base
        holofote(grupo, 0, 0, 1.5);
        const n = c.n || 16, mo = [...Array(n)].map((_, k) => { const m = cil(.6, .6, .14, k % 4 === 3 ? mObj : mAcesa(), 32); grupo.add(m); return { m, k }; });
        const lb = placaTexto([{ t: c.rotulo3d || "US$", tam: .22, cor: "#1a1420", mono: true }], 1.3, .45, COR); lb.position.set(0, .25, 1.0); grupo.add(lb);
        const tE = em(c.em, .5), tF = c.fim_em ?? c.ate - 1;
        item.pose = { pos: [0, 2.4, 8.8], alvo: [0, 1.6, 0] };
        item.upd = t => mo.forEach(o => { const t0 = tE + (tF - tE) * o.k / n, a = prog(t, t0, .35); o.m.visible = a > 0; o.m.position.set(.03 * Math.sin(o.k * 2.1), .07 + o.k * .15 + 2.5 * (1 - eout(a)), .03 * Math.cos(o.k * 1.3)); o.m.rotation.y = o.k; });
      } else if (c.tipo === "casa") {
        // a casa própria: janelas acesas; na palavra o peso (rotulo do peso) cai no telhado; etiqueta de preço opcional
        holofote(grupo, 0, 0, 2.0);
        const ca = new T.Group(); grupo.add(ca);
        ca.add(caixa(2.2, 1.5, 1.6, mObj, 0, .75, 0));
        const tel = new T.Mesh(new T.ConeGeometry(1.75, 1.1, 4), mEsc); tel.rotation.y = Math.PI / 4; tel.position.y = 2.05; tel.scale.z = .85; tel.castShadow = true; ca.add(tel);
        ca.add(caixa(.45, .8, .05, mEsc, 0, .4, .81));
        const mJ = new T.MeshStandardMaterial({ color: COR, emissive: corA, emissiveIntensity: .7 });
        [-.65, .65].forEach(x => ca.add(caixa(.4, .4, .05, mJ, x, .95, .81)));
        let peso = null; if (c.peso) { peso = new T.Group(); grupo.add(peso); peso.add(caixa(1.3, .75, 1.0, mEsc, 0, 0, 0));
          const pl = placaTexto([{ t: c.peso, tam: .17, cor: "#F7F7F7", mono: true }], 1.2, .4, T3.vela_baixa || "#DC2626"); pl.position.z = .51; peso.add(pl); }
        let tag = null; if (c.etiqueta3d) { tag = placaTexto([{ t: c.etiqueta3d, tam: c.etiqueta3d.length < 3 ? .3 : .16, cor: "#1a1420", mono: true }], Math.max(.8, Math.min(2.6, c.etiqueta3d.length * .12 + .4)), c.etiqueta3d.length < 3 ? .6 : .45, COR); tag.position.set(0, 3.35, .3); grupo.add(tag); }
        const tP = em(c.peso_em, 1.5), tT = em(c.etiqueta_em, 1);
        item.pose = { pos: [0, 2.5, 9.2], alvo: [0, 1.6, 0] };
        item.upd = t => { if (peso) { const a = prog(t, tP, .45); peso.visible = t >= tP - .05; peso.position.set(0, 6.5 - (6.5 - 2.95) * a * a, 0);
            const sq = a >= 1 ? .93 + .07 * (1 - Math.exp(-(t - tP - .45) * 3)) * 0 : 1; ca.scale.y = a >= 1 ? .94 : 1; }
          if (tag) { tag.scale.setScalar(Math.max(.001, eback(prog(t, tT, .45)))); tag.material.opacity = eout(prog(t, tT, .3)); tag.position.y = (peso && t >= tP ? 4.1 : 3.35); }
          mJ.emissiveIntensity = .55 + .15 * Math.sin(t * 1.3); };
      } else if (c.tipo === "carne") {
        // carnê: duas pilhas de boletos (antes x agora); a de agora cresce mais na palavra
        holofote(grupo, 0, 0, 2.4);
        const L = [{ x: -1.15, n: c.n_antes || 6, rot: c.antes || "ANTES", cor: mObj }, { x: 1.15, n: c.n_agora || 10, rot: c.agora || "AGORA", cor: null }];
        const vm = new T.MeshStandardMaterial({ color: T3.vela_baixa || "#DC2626", emissive: new T.Color(T3.vela_baixa || "#DC2626"), emissiveIntensity: .35 });
        const P2 = L.map((l, s) => { const fs = [...Array(l.n)].map((_, k) => { const b = caixa(1.5, .16, 1.0, l.cor || (k >= L[0].n ? vm : mObj), l.x, .08 + k * .2, 0); b.rotation.y = (k % 3 - 1) * .05; grupo.add(b); return b; });
          const lb = placaTexto([{ t: l.rot, tam: .16, cor: s ? "#1a1420" : "#F2F2EE", mono: true }], 1.6, .38, s ? COR : "#2E2536"); lb.position.set(l.x, .2, .85); grupo.add(lb);
          return { fs, s }; });
        const tE = em(c.em, 1.5);
        item.pose = { pos: [0, 2.4, 9.4], alvo: [0, 1.4, 0] };
        item.upd = t => P2.forEach(o => o.fs.forEach((b, k) => { const t0 = o.s && k >= L[0].n ? tE + (k - L[0].n) * .22 : c.de + .2 + k * .08, a = prog(t, t0, .3);
          b.visible = a > 0; b.position.y = .08 + k * .2 + 1.5 * (1 - eout(a)); }));
      } else if (c.tipo === "torneira") {
        // torneira do dinheiro: as moedas pingam no banco; na palavra a etiqueta de custo sobe e a torneira fica vermelha
        holofote(grupo, 0, 0, 2.0);
        grupo.add(caixa(.3, 3.6, .3, mCinza, -1.4, 1.8, -.2), caixa(1.6, .3, .3, mCinza, -.75, 3.45, -.2));
        const mT = new T.MeshStandardMaterial({ color: T3.objeto, roughness: .35, emissive: new T.Color(T3.vela_baixa || "#DC2626"), emissiveIntensity: 0 });
        const bico = cil(.2, .26, .5, mT, 20); bico.position.set(0, 3.2, -.2); grupo.add(bico);
        const reg = cil(.08, .08, .5, mT, 12); reg.rotation.z = Math.PI / 2; reg.position.set(0, 3.6, -.2); grupo.add(reg);
        grupo.add(caixa(1.9, 1.1, 1.3, mEsc, 0, .55, 0));
        const bc = placaTexto([{ t: c.caixa || "BANCO", tam: .16, cor: "#1a1420", mono: true }], 1.4, .36, COR); bc.position.set(0, .6, .66); grupo.add(bc);
        const go = [...Array(8)].map((_, k) => { const m = cil(.17, .17, .05, mAcesa(), 18); m.rotation.x = Math.PI / 2; grupo.add(m); return { m, k }; });
        const tag = placaTexto([{ t: c.etiqueta3d || "▲ CUSTO DE CAPTAR", tam: .15, cor: "#F7F7F7", mono: true }], 2.6, .45, T3.vela_baixa || "#DC2626"); tag.position.set(.3, 4.25, 0); grupo.add(tag);
        const tE = em(c.em, 2);
        item.pose = { pos: [0, 2.5, 9.4], alvo: [0, 2.1, 0] };
        item.upd = t => { const lento = t >= tE ? 2.2 : 1; go.forEach(o => { const per = .9 * lento, f = ((t - c.de) / per + o.k / go.length) % 1;
            o.m.visible = t > c.de + o.k * .1; o.m.position.set(0, 2.9 - 1.85 * f * f, -.2 + .1 * f); o.m.rotation.y = t * 3 + o.k; });
          const a = eout(prog(t, tE, .4)); mT.emissiveIntensity = .5 * a; tag.material.opacity = a; tag.scale.setScalar(Math.max(.001, eback(prog(t, tE, .45)))); };
      } else if (c.tipo === "instagram") {
        // celular 3D com o perfil do Instagram igual ao app (modo escuro): foto com anel, números, bio, destaques e a grade
        // com as capas reais; o toque aperta "Seguir" na palavra (em) e vira "Seguindo". Campos em c.perfil (ver PRESET.md).
        const pf = c.perfil || {}, CW = 720, CH = 1480, SW = 1.75, SH = SW * CH / CW;
        holofote(grupo, 0, 0, 1.6);
        const cel = new T.Group(); cel.position.set(0, 2.35, 0); grupo.add(cel);
        cel.add(caixa(SW + .16, SH + .2, .16, mEsc, 0, 0, 0));
        const aro = caixa(SW + .2, SH + .24, .1, mCinza, 0, 0, -.04); cel.add(aro);
        const ilha = caixa(.42, .1, .02, new T.MeshBasicMaterial({ color: "#000" }), 0, SH / 2 - .1, .087); cel.add(ilha);
        const img = src => { const im = new Image(); im.src = src; return im; };
        const foto = pf.foto ? img(pf.foto) : null, capas = (pf.capas || []).map(img);
        const fmt = v => typeof v === "number" ? v.toLocaleString("pt-BR") : (v || "");
        function tela(seguindo) {
          const cv = document.createElement("canvas"); cv.width = CW; cv.height = CH; const x = cv.getContext("2d");
          const F = (p, w = 600) => `${w} ${p}px -apple-system, 'Inter Tight', '${FONTE}', sans-serif`;
          const desenha = () => {
            x.fillStyle = "#000"; x.fillRect(0, 0, CW, CH);
            x.fillStyle = "#F5F5F5"; x.font = F(30, 600); x.textBaseline = "middle"; x.textAlign = "left"; x.fillText("9:41", 40, 34);
            x.fillRect(CW - 92, 26, 46, 18); x.fillRect(CW - 44, 31, 4, 8);
            x.font = F(34, 700); x.fillText(pf.user || "perfil", 40, 100);
            x.font = F(34, 400); x.textAlign = "right"; x.fillText("☰", CW - 40, 100); x.fillText("⊕", CW - 100, 100);
            // foto com o anel de story
            const ax = 120, ay = 255, r = 84, gr = x.createLinearGradient(ax - r, ay + r, ax + r, ay - r);
            gr.addColorStop(0, "#FEDA75"); gr.addColorStop(.35, "#FA7E1E"); gr.addColorStop(.6, "#D62976"); gr.addColorStop(1, "#962FBF");
            x.fillStyle = gr; x.beginPath(); x.arc(ax, ay, r + 9, 0, Math.PI * 2); x.fill();
            x.fillStyle = "#000"; x.beginPath(); x.arc(ax, ay, r + 3, 0, Math.PI * 2); x.fill();
            x.save(); x.beginPath(); x.arc(ax, ay, r - 2, 0, Math.PI * 2); x.clip();
            if (foto && foto.complete && foto.naturalWidth) x.drawImage(foto, ax - r, ay - r, 2 * r, 2 * r); else { x.fillStyle = "#333"; x.fillRect(ax - r, ay - r, 2 * r, 2 * r); }
            x.restore();
            if (pf.nota) { x.font = F(22, 600); const tw = x.measureText(pf.nota).width + 30; x.fillStyle = "#262626"; x.beginPath(); x.roundRect(ax - tw / 2, ay - r - 10, tw, 42, 21); x.fill();
              x.fillStyle = "#F5F5F5"; x.textAlign = "center"; x.fillText(pf.nota, ax, ay - r + 11); }
            const segs = seguindo ? (pf.seguidores_depois || pf.seguidores) : pf.seguidores;
            [[fmt(pf.posts), "posts"], [segs, "seguidores"], [fmt(pf.seguindo), "seguindo"]].forEach(([n, l], k) => { const cx = 330 + k * 140;
              x.fillStyle = "#F5F5F5"; x.textAlign = "center"; x.font = F(32, 700); x.fillText(n, cx, ay - 14); x.font = F(24, 400); x.fillText(l, cx, ay + 22); });
            x.textAlign = "left"; let y = 390; x.fillStyle = "#F5F5F5"; x.font = F(27, 700); x.fillText(pf.nome || "", 40, y);
            x.font = F(26, 400); (pf.bio || []).forEach(l => { y += 36; x.fillText(l, 40, y); });
            if (pf.link) { y += 36; x.fillStyle = "#E0F1FF"; x.font = F(26, 600); x.fillText("🔗 " + pf.link, 40, y); }
            y += 62;
            const bw = (CW - 80 - 16) / 2, rr = (bx, w, cor, txt, corT) => { x.fillStyle = cor; x.beginPath(); x.roundRect(bx, y - 30, w, 60, 14); x.fill();
              x.fillStyle = corT; x.textAlign = "center"; x.font = F(26, 700); x.fillText(txt, bx + w / 2, y); };
            rr(40, bw, seguindo ? "#262626" : "#0095F6", seguindo ? "Seguindo ⌄" : "Seguir", "#FFFFFF"); rr(40 + bw + 16, bw, "#262626", "Mensagem", "#F5F5F5");
            tela.botao = { x: 40 + bw / 2, y };
            y += 70; (pf.destaques || []).slice(0, 5).forEach((d, k) => { const hx = 80 + k * 130, hy = y + 50;
              x.strokeStyle = "#3a3a3a"; x.lineWidth = 3; x.beginPath(); x.arc(hx, hy, 46, 0, Math.PI * 2); x.stroke();
              x.save(); x.beginPath(); x.arc(hx, hy, 40, 0, Math.PI * 2); x.clip(); const im = capas[(k + 2) % Math.max(1, capas.length)];
              if (im && im.complete && im.naturalWidth) { const s = Math.max(80 / im.naturalWidth, 80 / im.naturalHeight); x.drawImage(im, hx - im.naturalWidth * s / 2, hy - im.naturalHeight * s / 2, im.naturalWidth * s, im.naturalHeight * s); }
              else { x.fillStyle = "#262626"; x.fillRect(hx - 40, hy - 40, 80, 80); } x.restore();
              x.fillStyle = "#F5F5F5"; x.font = F(20, 400); x.textAlign = "center"; x.fillText(d, hx, hy + 70); });
            y += 160; x.strokeStyle = "#262626"; x.lineWidth = 2; x.beginPath(); x.moveTo(0, y); x.lineTo(CW, y); x.stroke();
            x.fillStyle = "#F5F5F5"; x.fillRect(0, y, CW / 3, 3); x.font = F(30, 400); x.textAlign = "center"; ["▦", "▶", "◫"].forEach((s, k) => { x.fillStyle = k ? "#737373" : "#F5F5F5"; x.fillText(s, CW / 6 + k * CW / 3, y + 40); });
            y += 76; const cw = (CW - 4) / 3, ch = cw * 4 / 3;
            capas.slice(0, 9).forEach((im, k) => { const gx = (k % 3) * (cw + 2), gy = y + Math.floor(k / 3) * (ch + 2); if (gy > CH) return;
              x.save(); x.beginPath(); x.rect(gx, gy, cw, ch); x.clip();
              if (im.complete && im.naturalWidth) { const s = Math.max(cw / im.naturalWidth, ch / im.naturalHeight); x.drawImage(im, gx + (cw - im.naturalWidth * s) / 2, gy + (ch - im.naturalHeight * s) / 2, im.naturalWidth * s, im.naturalHeight * s); }
              else { x.fillStyle = "#1c1c1c"; x.fillRect(gx, gy, cw, ch); }
              if (k < (pf.fixados || 0)) { x.fillStyle = "#FFF"; x.font = F(24, 700); x.textAlign = "right"; x.fillText("📌", gx + cw - 10, gy + 26); }
              x.restore(); });
            tx.needsUpdate = true; };
          const tx = new T.CanvasTexture(cv); tx.colorSpace = T.SRGBColorSpace; tx.anisotropy = 8;
          desenha(); [foto, ...capas].filter(Boolean).forEach(im => im.addEventListener("load", desenha));
          const m = new T.Mesh(new T.PlaneGeometry(SW, SH), new T.MeshBasicMaterial({ map: tx, toneMapped: false })); m.position.z = .085; cel.add(m); return m;
        }
        const tA = tela(false), bot = tela.botao, tB = tela(true); tB.position.z = .086;
        const bx = (bot.x / CW - .5) * SW, by = (.5 - bot.y / CH) * SH;
        const toque = new T.Mesh(new T.CircleGeometry(.16, 32), new T.MeshBasicMaterial({ color: "#FFFFFF", transparent: true, opacity: 0, depthWrite: false, toneMapped: false })); toque.position.set(bx, by, .09); cel.add(toque);
        const onda = new T.Mesh(new T.RingGeometry(.16, .2, 40), new T.MeshBasicMaterial({ color: "#FFFFFF", transparent: true, opacity: 0, depthWrite: false, toneMapped: false })); onda.position.set(bx, by, .09); cel.add(onda);
        const tE = em(c.em, 1.2);
        item.pose = { pos: [0, 2.5, 5.4], alvo: [0, 2.55, 0] };
        item.upd = t => { const e = eback(prog(t, c.de, .9)); cel.rotation.y = (1 - e) * .7 + .1 * Math.sin(t * .6); cel.rotation.x = -.05; cel.position.y = 2.35 - (1 - e) * .6;
          const ap = prog(t, tE - .35, .35), so = prog(t, tE, .3); toque.material.opacity = .55 * ap * (1 - so); toque.scale.setScalar(1 - .25 * ap);
          const o = prog(t, tE, .6); onda.material.opacity = t >= tE ? .7 * (1 - o) : 0; onda.scale.setScalar(1 + 1.8 * o);
          tB.visible = t >= tE + .05; tA.scale.setScalar(t >= tE - .05 && t < tE + .08 ? .995 : 1); };
      } else if (EXTRA[c.tipo]) { EXTRA[c.tipo]({ c, i, grupo, item, O, em, T, caixa, cil, placaTexto, holofote, boneco, gradiente, mObj, mEsc, mCinza, mAcesa, COR, corA, T3, FONTE, prog, eio, eout, eback, D2R, montaPlacas });
      } else if (c.tipo === "cta") {
        holofote(grupo, 0, 0, 1.15); const bo = boneco(); grupo.add(bo);
        item.pose = { pos: [0, 2.2, 7.5], alvo: [0, 1.6, 0] };
      }
      { // efeitos de batida desta cena
        const onda = new T.Mesh(new T.RingGeometry(1.0, 1.08, 64), new T.MeshBasicMaterial({ color: COR, transparent: true, opacity: 0, depthWrite: false, toneMapped: false }));
        onda.rotation.x = -Math.PI / 2; onda.position.y = .02; grupo.add(onda);
        const fa = [...Array(12)].map((_, k) => { const m = new T.MeshBasicMaterial({ color: k % 3 ? COR : (T3.cone || COR), transparent: true, opacity: 0, depthWrite: false, toneMapped: false });
          const o = new T.Mesh(new T.OctahedronGeometry(.06 + (k % 3) * .02), m); grupo.add(o); const a = k * 2.399, el = .35 + (k % 4) * .22;
          return { o, dir: new T.Vector3(Math.cos(a) * Math.cos(el), Math.sin(el), Math.sin(a) * Math.cos(el)), v: 1.8 + (k % 5) * .35 }; });
        item.fx = t => { const u = ultBat(t), x = u == null || u < c.de || u > c.ate ? 9 : t - u, k = kickEm(t) * (x < 9 ? 1 : 0);
          grupo.scale.setScalar(1 + .03 * k);
          const w = Math.min(1, x / .9); onda.material.opacity = x < .9 ? .7 * (1 - w) : 0; onda.scale.setScalar(.6 + 2.6 * eout(w));
          fa.forEach(f => { const y = Math.min(1, x / 1.1); f.o.material.opacity = x < 1.1 ? .95 * (1 - y) : 0;
            f.o.position.copy(f.dir).multiplyScalar(f.v * eout(y)).add(new T.Vector3(0, 1.6 - .9 * y * y, .3)); f.o.rotation.set(x * 6, x * 4, 0); }); };
      }
      if (c.camera3d) item.pose = { pos: c.camera3d.pos || item.pose.pos, alvo: c.camera3d.alvo || item.pose.alvo };
      else if (c.enquadrar !== false && !item.fixo) {   // ENQUADRAMENTO AUTOMÁTICO (27/10/2026): objetos e textos no estado final da cena, centrados,
        try { item.upd(Math.min(c.ate - .2, c.de + 3.5)); } catch (e) {}   // ocupando a área livre abaixo do cartão. As poses à mão deixavam
        grupo.updateMatrixWorld(true);                                     // objeto pequeno, cortado ou fora do centro.
        const box = new T.Box3(), tmp = new T.Box3();
        grupo.traverse(o => { if (!o.isMesh || !o.visible || o.userData.deco) return;
          if (!(o.material && o.material.isMeshStandardMaterial) && !o.userData.rotulo) return; tmp.setFromObject(o); if (isFinite(tmp.min.x)) box.union(tmp); });
        if (!box.isEmpty()) { const ctr = box.getCenter(new T.Vector3()).sub(O), sz = box.getSize(new T.Vector3());
          // estilo "estudio": proporção medida na referência (cenário ~72% da largura e no máximo ~36% da altura)
          const dist = (grupo.userData.estilo === "estudio" ? Math.max(Math.max(sz.y, .9) * 3.7, Math.max(sz.x, .9) * 3.3, 4.4)
            : Math.max(Math.max(sz.y, .9) * 2.7, Math.max(sz.x, .9) * 3.3, 4.4)) / (c.zoom3d || 1);
          item.pose = { pos: [ctr.x, ctr.y + dist * .2, ctr.z + dist].map((v, k) => k === 2 ? ctr.z + dist / DIST : k === 1 ? ctr.y + dist * .2 / DIST : ctr.x), alvo: [ctr.x, ctr.y, ctr.z] }; }
      }
      // MONTAGEM (referência Ludificando): as peças do cenário nascem pequenas e crescem passando do ponto, da esquerda
      // para a direita, enquanto a câmera chega. Só na hora do render (escala salva e devolvida), então não briga com o
      // upd de cada cena. "montagem": false na cena ou no plano desliga.
      if (c.montagem !== false && P.montagem !== false) {
        const pecas = grupo.children.filter(o => !o.userData.luz).sort((a, b) => a.position.x - b.position.x);
        item.corte = i > 0 && cenas[i - 1]._3d && grupo.userData.estilo === "estudio" && (c.troca ?? P.troca ?? "foco") === "foco";
        const t0 = i === 0 ? c.de + .1 : item.corte ? c.de + .04 : c.de + TRANS * .3, passo = Math.min(.08, .75 / Math.max(1, pecas.length));
        item.monta = pecas.map((o, k) => ({ o, t0: t0 + k * passo }));
      }
      cenas3d.push(item);
    });
    // destaque aceso da referência: o amarelo sai SATURADO (o ACES lavava para creme). Todo material na cor da marca vira
    // "aceso": emissivo na cor, fora do tone mapping, com um resto de cor difusa para ainda ter volume. "acesos": false desliga.
    if (P.acesos !== false) sc.traverse(o => { const m = o.isMesh && o.material; if (!m || !m.isMeshStandardMaterial || m.userData.aceso) return;
      const perto = cc => cc && Math.abs(cc.r - corA.r) + Math.abs(cc.g - corA.g) + Math.abs(cc.b - corA.b) < .12;
      if (!perto(m.color) && !(perto(m.emissive) && m.emissiveIntensity > .2)) return;
      m.userData.aceso = true; m.toneMapped = false; m.emissive = corA.clone(); m.emissiveIntensity = m.emissiveIntensity === 0 ? 0 : .7; m.color = corA.clone().multiplyScalar(.42); m.roughness = .55; m.needsUpdate = true; });
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
      const dt = Math.max(0, t - item.c.de), p = item.pose, lado = (item.i0 ?? item.i) % 2 ? -1 : 1, ang = lado * (item.c.orbita ?? (item.grupo.userData.estilo === "estudio" ? .012 : .06)) * dt;   // estúdio: quase de frente, como a referência
      const pos = V(p.pos, item.O), alvo = V(p.alvo, item.O), d = pos.clone().sub(alvo);
      d.applyAxisAngle(new T.Vector3(0, 1, 0), ang); d.multiplyScalar(DIST * Math.max(.75, 1 - (item.c.aproxima ?? .022) * dt) * (1 - .055 * kickEm(t)));
      d.y += .18 * Math.sin(dt * .55);
      return { pos: alvo.clone().add(d), alvo };
    }
    function render(t) {
      const i = idx(t), c = cenas[i]; let it = cenas3d.find(x => x.i === i);
      if (!it) { // globo na tela: segura a pose da cena 3D mais perto (para o fade)
        it = cenas3d.filter(x => x.i < i).pop() || cenas3d.find(x => x.i > i); if (!it) return; }
      cenas3d.forEach(x => { x.upd(t); if (x.fx) x.fx(t); });
      { const ant = cenas3d.find(x => x.i === it.i - 1), em = it.i === i && i > 0 && t < c.de + TRANS;
        const lista = (it.grupo.userData.luzes || []).map(l => [it.grupo, l]).concat(em && ant ? (ant.grupo.userData.luzes || []).map(l => [ant.grupo, l]) : []);
        luzes(lista.slice(0, POOL.length)); }
      let { pos, alvo } = poseEm(t, it);
      if (it.i === i && i > 0 && !it.cont && !it.corte) { const k = eio(prog(t, c.de, TRANS)), ant = cenas3d.find(x => x.i === i - 1);
        let p0, a0;
        if (ant) { const q = poseEm(c.de, ant); p0 = q.pos; a0 = q.alvo; }
        else { a0 = alvo.clone(); p0 = pos.clone().add(new T.Vector3(1.5, 2.2, 6)); }   // vindo do globo: entra de longe
        pos = p0.clone().lerp(pos, k); alvo = a0.clone().lerp(alvo, k); }
      cam.position.copy(pos); cam.lookAt(alvo);
      { // estilo "estudio" = a referência Ludificando medida quadro a quadro: chave branca forte de frente-alto, ambiente
        // neutro (sem roxo no chão), quase nenhum recorte colorido, lente longa de foto de produto. Mistura na troca de cena.
        const suave = x => x && x.grupo.userData.estilo === "estudio" ? 1 : 0, ant = cenas3d.find(x => x.i === it.i - 1);
        const k = it.i === i && i > 0 && ant ? eio(prog(t, c.de, TRANS)) : 1, s = suave(ant) * (1 - k) + suave(it) * k;
        chao.material = s > .5 ? chaoSombra : chaoPalco; sc.fog.near = 30 + 200 * s; sc.fog.far = 75 + 400 * s;   // fundo infinito: sem neblina
        ren.setClearColor(T3.fundo, s > .5 ? 0 : 1);
        hemi.intensity = 1.25 - .65 * s; hemi.groundColor.copy(CHAO_PALCO).lerp(CHAO_ESTUDIO, s);
        dirL.intensity = 1.0 + 1.1 * s; preench.intensity = .35 + .45 * s; recorte.intensity = 1.6 - 1.3 * s;
        const fov = 38 - (38 - (P.lente ?? 22)) * s; if (Math.abs(cam.fov - fov) > .01) { cam.fov = fov; cam.updateProjectionMatrix(); }
        // composição medida na referência: o cenário ocupa ~60% da largura (folga), fica no MEIO da tela entre o cartão e a
        // legenda (desce = 0) e a câmera olha de cima, ~26°, mostrando o topo das peças (elevacao)
        const afasta = Math.tan(19 * D2R) / Math.tan(fov / 2 * D2R) * (1 + (P.folga ?? 0) * s);   // lente longa: recua para o enquadramento ficar igual
        const d = pos.clone().sub(alvo).multiplyScalar(afasta), L = d.length(), el0 = Math.asin(clamp(d.y / L, -1, 1));
        const el = el0 + Math.max(0, (it.c.elevacao ?? P.elevacao ?? 26) * D2R - el0) * s, hz = Math.hypot(d.x, d.z) || 1;
        d.set(d.x / hz * L * Math.cos(el), L * Math.sin(el), d.z / hz * L * Math.cos(el));
        cam.position.copy(alvo.clone().add(d)); cam.lookAt(alvo);
        const desce = (P.estudio_desce ?? .1) * (1 - s) + (P.estudio_desce_ref ?? -.045) * s;
        if (cam.view && Math.abs(cam.view.offsetY + H * desce) > .5) cam.setViewOffset(W, H, 0, -H * desce, W, H); }
      const salvos = [];
      cenas3d.forEach(x => (x.monta || []).forEach(m => { const k = prog(t, m.t0, .85); if (k >= 1) return;
        const e = Math.max(eback(k), .001); salvos.push([m.o, m.o.scale.clone(), m.o.position.y]);
        m.o.scale.multiplyScalar(e); m.o.position.y += .5 * (1 - eout(k)); }));
      ren.render(sc, cam);
      salvos.forEach(([o, s, y]) => { o.scale.copy(s); o.position.y = y; });
    }
    // troca por foco (referência Ludificando): a cena nova nasce desfocada e foca em ~0,4 s
    const foco = t => { const i = idx(t), it = cenas3d.find(x => x.i === i); if (!it || !it.corte || it.cont) return 0;
      return (1 - eout(prog(t, cenas[i].de, P.foco_dur ?? .42))) * (P.foco_px ?? 22) * U; };
    return { render, foco };
  }

  // ---------- quadro: globo, estúdio e poeira por cima ----------
  let BLOOM = null, CV_BRILHO = null;
  function desenha(t) {
    const ag = alfaGlobo(t), cam = camEm(t); cam.zoom *= 1 + .035 * kickEm(t);
    if (ag > 0) desenhaGlobo(t, cam); else g.clearRect(0, 0, W, H);
    cv.style.opacity = ag.toFixed(3);
    if (E3 && ag < 1) { cv3.style.opacity = "1"; E3.render(t); } else cv3.style.opacity = "0";
    gp2.setTransform(1, 0, 0, 1, 0, 0); gp2.clearRect(0, 0, W, H);
    const fb = E3 && ag < 1 ? E3.foco(t) : 0;   // desfoque da troca: o 3D é redesenhado borrado no canvas do brilho (sem CSS filter)
    // brilho (bloom) da referência: só o que é aceso (amarelo, telas, teclas) vaza luz em volta. brightness+contrast
    // funciona como limiar (o cinza-argila vira preto e não soma nada); "brilho": 0 no plano desliga.
    if (E3 && ag < 1 && (P.brilho ?? .24) > 0) {   // em 1/4 da resolução: barato no render e a ampliação deixa o halo macio
      const bw = Math.round(W / 4), bh = Math.round(H / 4);
      if (!BLOOM) { BLOOM = [0, 1, 2].map(() => { const c = document.createElement("canvas"); c.width = bw; c.height = bh; return c; }); }
      const [b0, b1, b2] = BLOOM, x0 = b0.getContext("2d"), x1 = b1.getContext("2d"), x2 = b2.getContext("2d");
      x0.clearRect(0, 0, bw, bh); x0.drawImage(cv3, 0, 0, bw, bh);
      // limiar pela MÉDIA dos canais: só o que é aceso (amarelo da marca, ícone branco) brilha; ouro e cinza não. O resto vira
      // transparente e o halo só soma luz (sem mix-blend, que o render ignora)
      const id = x0.getImageData(0, 0, bw, bh), d = id.data, LIM = (P.brilho_limiar ?? .74) * 765, FAIXA = 765 * .16;
      for (let p = 0; p < d.length; p += 4) { const m = d[p] + d[p + 1] + d[p + 2];
        d[p + 3] = m <= LIM ? 0 : Math.min(255, (m - LIM) / FAIXA * 255) * d[p + 3] / 255; }
      x0.putImageData(id, 0, 0);
      x1.clearRect(0, 0, bw, bh); x1.filter = `blur(${(1.6 * U).toFixed(2)}px)`; x1.drawImage(b0, 0, 0); x1.filter = "none";
      x2.clearRect(0, 0, bw, bh); x2.filter = `blur(${(7 * U).toFixed(2)}px)`; x2.drawImage(b0, 0, 0); x2.filter = "none";
      if (!CV_BRILHO) { CV_BRILHO = document.createElement("canvas"); CV_BRILHO.width = W; CV_BRILHO.height = H;
        Object.assign(CV_BRILHO.style, { position: "absolute", inset: "0", width: "100%", height: "100%", pointerEvents: "none" });
        cv3.after(CV_BRILHO); }
      const gb = CV_BRILHO.getContext("2d"); gb.globalCompositeOperation = "source-over"; gb.globalAlpha = 1; gb.clearRect(0, 0, W, H);
      if (fb > .3) { cv3.style.opacity = "0"; gb.filter = `blur(${fb.toFixed(1)}px)`; gb.drawImage(cv3, 0, 0, W, H); gb.filter = "none"; }
      gb.globalCompositeOperation = "lighter"; gb.imageSmoothingEnabled = true; gb.globalAlpha = Math.min(1, (P.brilho ?? .24) * (1 - ag));
      gb.drawImage(b1, 0, 0, W, H); gb.globalAlpha *= .45; gb.drawImage(b2, 0, 0, W, H);
    } else if (CV_BRILHO) CV_BRILHO.getContext("2d").clearRect(0, 0, W, H);
    poeira(gp2, t, cam.lon, false); poeira(gp2, t, cam.lon, true);
  }
  const relogio = { t: 0 };
  tl.to(relogio, { t: dur, duration: dur, ease: "none", onUpdate: () => desenha(relogio.t) }, 0);
  desenha(0);

  // ---------- cartão (DOM) ----------
  const card = document.getElementById("card");
  Object.assign(card.style, VERT ? { left: px(66), top: (H * (P.cartao_y ?? .136)).toFixed(1) + "px" } : { left: px(80), top: px(80) });
  const FIXO = (P.kicker_fixo ?? T3.kicker_fixo ?? false) && !P.serie_sai;   // referência: kicker e pílula ficam o vídeo todo
  let kick = null;
  if (P.serie) { const k = mk("div", "kicker" + (P.kicker_ponto ? " ponto" : ""), card, { fontSize: px(24), marginBottom: px(16) }); k.textContent = P.serie; kick = k;
    if (FIXO) k.style.color = P.cor_kicker || "#A3A396";   // referência: kicker cinza-oliva apagado (inline: não mexe nas trocas dos temas)
    tl.fromTo(k, { opacity: 0 }, { opacity: 1, duration: .5, ease: "power2.out" }, 0); }
  const pil = mk("div", "pilula", card, { height: px(62), paddingRight: px(26) });
  if (!cenas.some(c => c.secao)) pil.style.display = "none";   // referência Ludificando: sem pílula de seção, só o kicker
  mk("span", "bola", pil, { width: px(40), height: px(40), margin: `0 ${px(14)} 0 ${px(11)}` });
  const txts = cenas.map(c => { const s = mk("span", "txt", pil, { fontSize: px(30), display: "none" }); s.textContent = "• " + (c.secao || ""); return s; });
  tl.fromTo(pil, { maxWidth: px(62) }, { maxWidth: px(1000), duration: .8, ease: "power3.out" }, .1);
  cenas.forEach((c, i) => { tl.set(txts[i], { display: "inline" }, c.de); if (i < cenas.length - 1) tl.set(txts[i], { display: "none" }, cenas[i + 1].de);
    if (i) tl.fromTo(txts[i], { opacity: .25 }, { opacity: 1, duration: .45, ease: "power2.out", immediateRender: false }, c.de); });
  const fontesEl = P.fontes ? mk("div", "fontes", card, { fontSize: px(18), marginTop: px(12) }) : null;
  if (fontesEl) { fontesEl.textContent = P.fontes; tl.fromTo(fontesEl, { opacity: 0 }, { opacity: 1, duration: .5, ease: "power2.out" }, P.fontes_em ?? .6); }
  const area = mk("div", "", card, { position: "relative", marginTop: px(14) });
  // topo limpo (pedido do Gabriel, 27/10/2026): série, pílula e fontes só na abertura; depois somem e o cartão sobe,
  // ficando só as palavras-chave (etiqueta, número, tópicos). As fontes voltam discretas no CTA. "topo_ate": false desliga.
  const topoAte = P.topo_ate === false ? null : (P.topo_ate ?? (cenas[1] ? cenas[1].de : null));
  if (topoAte != null && FIXO) { if (fontesEl) tl.to(fontesEl, { opacity: 0, duration: .35, ease: "power2.in" }, topoAte - .25); }
  else if (topoAte != null) { const semPilula = pil.style.display === "none";
    const sai = !!P.serie_sai;   // "serie_sai": true = a série também sai depois da abertura (X-Trader: "aqui em cima eu acho muito sujo")
    const sobe = semPilula && !sai ? (fontesEl ? area.offsetTop - fontesEl.offsetTop : 0) : area.offsetTop;   // referência: o kicker "• SÉRIE" fica o vídeo todo, só as fontes saem
    tl.to((semPilula ? [fontesEl, sai ? kick : null] : [kick, pil, fontesEl]).filter(Boolean), { opacity: 0, duration: .35, ease: "power2.in" }, topoAte - .25);
    tl.to(area, { y: -sobe, duration: .5, ease: "power3.inOut" }, topoAte - .2); }
  const sinal = (v, n) => v < 0 ? "−" : (n.sinal && v > 0 ? "+" : "");
  const fmt = (v, n) => (n.prefixo || "") + sinal(v, n) + Math.abs(v).toLocaleString("pt-BR", { minimumFractionDigits: n.decimais || 0, maximumFractionDigits: n.decimais || 0 }) + (n.sufixo || "");
  const cartoes = [];
  cenas.forEach((c, i) => {
    if (c.tipo === "cta" || c.cta) return;
    // "continua": true = mesma ideia da cena anterior (referência: "A IA:" fica e os chips vão se somando): o cartão
    // anterior fica na tela e só ganha o que esta cena trouxer (chips, tópicos, número)
    const segue = c.continua && cartoes[i - 1], t0 = c.de + .08;
    const gp = segue ? cartoes[i - 1].gp : mk("div", "", area, { position: "absolute", left: 0, top: 0, width: px(VERT ? 900 : 760) });
    cartoes[i] = { gp, chips: segue ? cartoes[i - 1].chips : null };
    if (c.etiqueta) { const e = mk("div", "etiqueta", gp, { fontSize: px(21), padding: `${px(7)} ${px(14)}` }); e.textContent = c.etiqueta;
      tl.fromTo(e, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: .45, ease: "power3.out" }, t0); }
    // título da referência Ludificando: frase curta em bold, a palavra-chave entre *asteriscos* sai na cor da marca
    if (c.manchete) { const e = mk("div", "titulo", gp, { fontSize: px(c.manchete_tam || 78), marginTop: px(c.etiqueta ? 14 : 0), maxWidth: px(VERT ? 880 : 740) });
      c.manchete.split(/(\*[^*]+\*)/).forEach(p => { if (!p) return; const s = mk("span", p[0] === "*" ? "dest" : "", e); s.textContent = p.replace(/\*/g, ""); });
      tl.fromTo(e, { opacity: 0, y: px(20) }, { opacity: 1, y: 0, duration: .55, ease: "expo.out" }, c.manchete_em ?? t0); }
    // chips: pílulas na cor da marca que vão se SOMANDO na palavra (PESQUISOU > ESCREVEU > NARROU...), "chips": [{texto, em}]
    if ((c.chips || []).length) { const cen = P.chips_esquerda !== true, herdou = !!cartoes[i].chips;   // referência: chips centralizados na tela
      const L = cartoes[i].chips || (cartoes[i].chips = cen
        ? mk("div", "chips centro", root, { top: (H * (c.chips_y ?? P.chips_y ?? (c.numero && (c.numero.caixa ?? P.numero_caixa ?? T3.kicker_fixo) ? .338 : P.etapas ? .262 : .226))).toFixed(1) + "px", gap: px(12), padding: `0 ${px(60)}` })
        : mk("div", "chips", gp, { marginTop: px(20), gap: px(12), maxWidth: px(VERT ? 880 : 740) }));
      c.chips.forEach(ch => { const am = ch.destaque ?? (P.chips_amarelos === true);
        const e = mk("div", "chip" + (am ? "" : " neutro"), L, { fontSize: px(cen ? 25 : 31), padding: cen ? `${px(12)} ${px(24)}` : `${px(13)} ${px(28)}` }); e.textContent = ch.texto;
        tl.fromTo(e, { opacity: 0, scale: .6 }, { opacity: 1, scale: 1, duration: .4, ease: "back.out(2.2)" }, ch.em ?? t0); });
      if (cen) { let j = i; while (cenas[j + 1] && cenas[j + 1].continua) j++;
        if (cenas[j + 1] && !herdou) tl.to(L, { opacity: 0, duration: .25, ease: "power2.in" }, cenas[j + 1].de - .2); } }
    const n = c.numero;
    const caixa = n && (n.caixa ?? P.numero_caixa ?? T3.kicker_fixo ?? false);
    const hostN = caixa ? mk("div", "caixanum", gp, { marginTop: px(16), padding: `${px(16)} ${px(26)} ${px(18)}`, width: px(VERT ? 905 : 700) }) : gp;
    if (caixa && (n.rotulo || c.rotulo)) { const rl = mk("div", "rot", hostN, { fontSize: px(19) }); rl.textContent = n.rotulo || c.rotulo; }
    if (caixa) tl.fromTo(hostN, { opacity: 0, y: px(16) }, { opacity: 1, y: 0, duration: .45, ease: "power3.out" }, n.em ?? c.de + .4);
    if (n) { const em = n.em ?? c.de + .4, el = mk("div", "numero", hostN, { fontSize: px(n.tamanho || (caixa ? 112 : 158)), marginTop: px(caixa ? 6 : 14) });
      if (n.texto) el.textContent = n.texto;
      else { const o = { v: 0 }; el.textContent = fmt(n.de ?? 0, n);
        tl.fromTo(o, { v: n.de ?? 0 }, { v: n.valor, duration: n.conta ?? 1.3, ease: "expo.out", immediateRender: false,
          onUpdate: () => { el.textContent = fmt(o.v, n); } }, em); }
      tl.fromTo(el, { opacity: 0, y: px(26) }, { opacity: 1, y: 0, duration: .6, ease: "expo.out" }, em);
      if (!caixa) { const dv = mk("div", "divisor", gp, { width: px(110), height: px(4), marginTop: px(16), transformOrigin: "0 50%" });
      tl.fromTo(dv, { scaleX: 0 }, { scaleX: 1, duration: .55, ease: "power3.out" }, em + .12); } }
    const tx = (cls, txt, tam, mt, quando) => { if (!txt) return; const e = mk("div", cls, gp, { fontSize: px(tam), marginTop: px(mt), maxWidth: px(VERT ? 880 : 740) });
      e.textContent = txt; tl.fromTo(e, { opacity: 0, y: px(14) }, { opacity: 1, y: 0, duration: .5, ease: "power3.out" }, quando); };
    const base = n ? (n.em ?? c.de + .4) : t0;
    if (!caixa) tx("rotulo", c.rotulo, 25, 12, base + .18); tx("sub", c.sub, 21, 6, base + .26);
    if ((c.topicos || []).length) { const L = mk("div", "topicos", gp, { marginTop: px(n || c.rotulo ? 22 : 12), gap: px(6), maxWidth: px(VERT ? 880 : 740) });
      const els = c.topicos.map(tp => { const e = mk("div", "topico", L, { fontSize: px(36) }); e.textContent = "• " + tp.texto; return e; });
      c.topicos.forEach((tp, j) => { tl.fromTo(els[j], { opacity: 0, x: px(-18), color: COR }, { opacity: 1, x: 0, duration: .45, ease: "power3.out" }, tp.em);
        if (j) tl.to(els[j - 1], { color: "#F2F2EE", duration: .35, ease: "power2.out" }, tp.em); }); }
    if (i < cenas.length - 1 && !cenas[i + 1].continua) tl.to(gp, { opacity: 0, y: px(-12), duration: .25, ease: "power2.in" }, cenas[i + 1].de - .2);
    if (c.carimbo) { const ca = document.getElementById("carimbo"), s = mk("div", "selo", ca, { borderWidth: px(4), padding: `${px(16)} ${px(30)} ${px(12)}` });
      const tt = mk("div", "t", s, { fontSize: px(c.carimbo.tamanho || 46) }); tt.textContent = c.carimbo.titulo;
      if (c.carimbo.sub) { const ss = mk("div", "s", s, { fontSize: px(16), marginTop: px(8) }); ss.textContent = c.carimbo.sub; }
      Object.assign(s.style, { position: "absolute", left: "0", top: (H * (c.carimbo.y ?? .45)).toFixed(1) + "px" });   // cada carimbo com a sua altura
      tl.set(ca, { display: "block" }, c.carimbo.em);
      tl.fromTo(s, { opacity: 0, scale: 1.4, rotation: -4, xPercent: -50, yPercent: -50 }, { opacity: 1, scale: 1, rotation: -4, xPercent: -50, yPercent: -50, duration: .32, ease: "power3.out" }, c.carimbo.em);
      if (i < cenas.length - 1) tl.to(s, { opacity: 0, duration: .25 }, cenas[i + 1].de - .2); }
  });
  // ---------- estrutura anunciada (referência: "depende de 3 coisas" / "3 rounds") ----------
  // "etapas": ["ONDE VOCÊ TRABALHA", "O SINDICATO", "A EMPRESA"] no plano + "etapa": n (1..) na cena: barra fixa no topo,
  // cada slot mostra "n · ?" até a cena dele, aí revela o nome e acende; depois fica revelado e apagado.
  // "placar": {"esq": "PRESIDENTE", "dir": "SUPREMO"} + "round": "ROUND 1 · A LEI" e "lado": "esq"|"dir" na cena.
  const topoBar = (P.etapas || P.placar) ? mk("div", "estrutura", root, { top: (H * (P.estrutura_y ?? .214)).toFixed(1) + "px", gap: px(10) }) : null;
  const ini0 = cenas.find(c => c.etapa || c.round), tIni = ini0 ? ini0.de : 0;
  if (topoBar) tl.fromTo(topoBar, { opacity: 0, y: px(-14) }, { opacity: 1, y: 0, duration: .45, ease: "power3.out", immediateRender: true }, tIni);
  if (P.etapas) P.etapas.forEach((nome, k) => {
    const sl = mk("div", "etapa", topoBar, { fontSize: px(19), padding: `${px(9)} ${px(16)}` });
    const q = mk("span", "", sl); q.textContent = `${k + 1} · ?`;
    const r = mk("span", "", sl, { display: "none" }); r.textContent = `${k + 1} · ${nome}`;
    const cs = cenas.filter(c => c.etapa === k + 1), t1 = cs.length ? cs[0].de : null;
    if (t1 != null) { tl.set(q, { display: "none" }, t1); tl.set(r, { display: "inline" }, t1);
      tl.fromTo(sl, { scale: .82 }, { scale: 1, duration: .4, ease: "back.out(2.4)", immediateRender: false }, t1); }
    cenas.forEach(c => { if (!c.etapa) return; const on = c.etapa === k + 1;
      const rev = t1 != null && c.de >= t1;
      tl.set(sl, { backgroundColor: on ? COR : rev ? "rgba(44,44,41,.95)" : "rgba(0,0,0,0)", color: on ? "#151515" : rev ? "#E8E8E0" : "#8C8C86",
        borderColor: on ? COR : rev ? "rgba(44,44,41,.95)" : "#4A4A44" }, c.de); });
  });
  if (P.placar) {
    const lado = (txt, k) => { const e = mk("div", "etapa", topoBar, { fontSize: px(22), padding: `${px(10)} ${px(18)}` }); e.textContent = txt; return e; };
    const E = lado(P.placar.esq || "A"), M = mk("div", "etapa meio", topoBar, { fontSize: px(22), padding: `${px(10)} ${px(20)}` }), D = lado(P.placar.dir || "B");
    topoBar.insertBefore(E, M);
    const rs = cenas.filter(c => c.round).map(c => { const sp = mk("span", "", M, { display: "none" }); sp.textContent = c.round; return { c, sp }; });
    rs.forEach(({ c, sp }, j) => { tl.set(sp, { display: "inline" }, c.de); if (rs[j + 1]) tl.set(sp, { display: "none" }, rs[j + 1].c.de);
      tl.set(E, { backgroundColor: c.lado === "esq" ? COR : "rgba(30,30,28,.86)", color: c.lado === "esq" ? "#151515" : "#F2F2EE" }, c.de);
      tl.set(D, { backgroundColor: c.lado === "dir" ? COR : "rgba(30,30,28,.86)", color: c.lado === "dir" ? "#151515" : "#F2F2EE" }, c.de);
      tl.fromTo(M, { scale: .9 }, { scale: 1, duration: .35, ease: "back.out(2)", immediateRender: false }, c.de); });
  }
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
  const COR_DITA = P.cor_dita || COR;   // medido na referência: o que já foi dito fica no amarelo da marca
  if (PAL.length) {
    const leg = document.getElementById("legenda"); Object.assign(leg.style, { top: (H * (P.legenda_y ?? (VERT ? .725 : .86))).toFixed(1) + "px" });
    const blocos = []; let cur = [];
    PAL.forEach((w, i) => { cur.push(w); const fimFrase = /[.,!?:;]$/.test(w.t), chars = cur.map(x => x.t).join(" ").length;
      if (fimFrase || cur.length >= (P.palavras_bloco || 6) || chars >= 28 || i === PAL.length - 1) { blocos.push(cur); cur = []; } });
    blocos.forEach((b, i) => {
      const ini = b[0].s - .04, fimB = i < blocos.length - 1 ? blocos[i + 1][0].s - .04 : Math.min(dur, b[b.length - 1].e + .8);
      const el = mk("div", "bloco", leg, { fontSize: px(P.legenda_tam || 50), padding: `${px(24)} ${px(52)} ${px(26)}`, maxWidth: px(800), minWidth: px(640), borderRadius: px(18) });
      if (FIXO) el.style.background = "rgba(19,19,17,.9)";
      b.forEach((w, j) => { const s = mk("span", "w", el, j < b.length - 1 ? { marginRight: ".26em" } : null); s.textContent = w.t;
        // referência: a palavra falada AGORA fica na cor e um pouco maior, a já dita fica amarelo-claro, a que vem fica cinza
        const solta = Math.max(w.s + .05, (b[j + 1] ? b[j + 1].s : w.e + .15));
        tl.set(s, { color: COR }, w.s); tl.set(s, { color: COR_DITA }, solta);
        tl.fromTo(s, { scale: 1.14 }, { scale: 1.07, duration: .18, ease: "power2.out", immediateRender: false }, w.s); tl.set(s, { scale: 1 }, solta); });
      tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: .08, ease: "power1.out", immediateRender: false }, ini);
      tl.set(el, { opacity: 0 }, fimB);
    });
  }
  tl.set({}, {}, dur);
  window.__timelines = window.__timelines || {}; window.__timelines["ludico"] = tl;
})();
