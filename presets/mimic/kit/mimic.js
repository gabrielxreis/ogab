// Preset MIMIC: teatrinho de bonecos de papel num palco de cortina azul, dirigido pela timeline do HyperFrames.
// Cada quadro é função pura do tempo t (nada de Math.random nem relógio: sorteio por hash com semente).
// Linguagem estudada num Reels de teatro bíblico de papel (27/10/2026); desenho e código nossos.
// Camadas (de trás para a frente): cenário pintado > adereços do céu > chão de tábuas > bonecos > holofote >
// cortinas > placas penduradas no barbante > bambolina com franja dourada > plateia > grão e vinheta.
const P = window.PLANO, T = P.tema, W = P.w, H = P.h, CX = W / 2;
const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
const PI = Math.PI, DEG = PI / 180;
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, u) => a + (b - a) * u;
const eoc = u => 1 - Math.pow(1 - clamp(u), 3);
const eic = u => Math.pow(clamp(u), 3);
const eio = u => { u = clamp(u); return u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; };
function hash(a, b = 0) { let h = (a * 374761393 + b * 668265263 + 1013904223) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); h ^= h >>> 16; return (h >>> 0) / 4294967296; }
function rng(seed) { let k = 0; return () => hash(seed, k++); }

// ---------------------------------------------------------------- medidas do palco (tela 1080x1920)
const VAL = 128;            // bambolina (faixa de veludo de cima)
const FUNDO = 1450;         // onde o cenário encontra o chão
const PES = 1575;           // linha onde os bonecos pisam
const BORDA = 1800;         // beirada do palco (ribalta)
const CORT = 66;            // largura de cada cortina aberta
const PLACA_Y = 575;        // centro padrão da placa (dentro da caixa segura do Instagram)

// ---------------------------------------------------------------- fontes
const FT = T.fonte_titulo || 'Cardo', FX = T.fonte_texto || 'Inter Tight';
for (const [nome, arq] of [[FT, T.fonte_titulo_arquivo], [FX, T.fonte_texto_arquivo]]) {
  if (arq) { const f = new FontFace(nome, `url("${arq}")`); await f.load(); document.fonts.add(f); }
}
const tela = (w, h) => { const c = document.createElement('canvas'); c.width = Math.ceil(w); c.height = Math.ceil(h); return c; };

// ---------------------------------------------------------------- cenários pintados (feitos uma vez, offscreen)
function pinceladas(g, w, h, seed, n, claro, escuro) {
  const r = rng(seed);
  for (let i = 0; i < n; i++) {
    const y = r() * h, x = r() * w - 100, L = 80 + r() * 380;
    g.strokeStyle = r() < .5 ? claro : escuro;
    g.globalAlpha = .035 + r() * .06; g.lineWidth = 2 + r() * 5; g.lineCap = 'round';
    g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + L / 2, y + (r() - .5) * 6, x + L, y + (r() - .5) * 4); g.stroke();
  }
  g.globalAlpha = 1;
}
function vgrad(g, h, cores) {
  const gr = g.createLinearGradient(0, 0, 0, h);
  cores.forEach(([p, c]) => gr.addColorStop(p, c));
  return gr;
}
function predios(g, r, y0, y1, cores, janela, acesas, largura = [70, 150]) {
  let x = -20;
  while (x < W + 20) {
    const w = largura[0] + r() * (largura[1] - largura[0]), h = (y1 - y0) * (.35 + r() * .65);
    g.fillStyle = cores[(r() * cores.length) | 0];
    g.fillRect(x, y1 - h, w, h + 40);
    const cols = Math.max(2, Math.floor(w / 28)), linhas = Math.floor(h / 34);
    for (let a = 0; a < linhas; a++) for (let b = 0; b < cols; b++) {
      if (r() > acesas) continue;
      g.fillStyle = janela; g.globalAlpha = .55 + r() * .45;
      g.fillRect(x + 9 + b * (w - 18) / cols, y1 - h + 14 + a * 34, (w - 18) / cols - 9, 16);
    }
    g.globalAlpha = 1;
    x += w + 4 + r() * 10;
  }
}
function morro(g, r, y, amp, cor, h) {
  g.fillStyle = cor; g.beginPath(); g.moveTo(-20, h);
  const f = .8 + r() * .8, fase = r() * 6;
  for (let x = -20; x <= W + 20; x += 20) g.lineTo(x, y + Math.sin(x / W * PI * f + fase) * amp);
  g.lineTo(W + 20, h); g.closePath(); g.fill();
}
function nuvemForma(g, x, y, s, cor) {
  g.fillStyle = cor;
  for (const [dx, dy, rr] of [[-60, 8, 38], [-18, -14, 50], [32, -4, 42], [70, 12, 30], [0, 16, 40]]) {
    g.beginPath(); g.arc(x + dx * s, y + dy * s, rr * s, 0, 2 * PI); g.fill();
  }
  g.fillRect(x - 90 * s, y + 10 * s, 180 * s, 36 * s);
}
function arvore(g, x, y, s) {
  g.fillStyle = '#4a3420'; g.fillRect(x - 8 * s, y - 80 * s, 16 * s, 80 * s);
  g.fillStyle = '#2f5a3a';
  for (const [dx, dy, rr] of [[0, -150, 70], [-50, -110, 52], [52, -112, 50]]) { g.beginPath(); g.arc(x + dx * s, y + dy * s, rr * s, 0, 2 * PI); g.fill(); }
}
const PINTA = {
  noite(g, w, h) {
    g.fillStyle = vgrad(g, h, [[0, '#16285a'], [.6, '#253f7a'], [1, '#2c4a86']]); g.fillRect(0, 0, w, h);
    pinceladas(g, w, h, 11, 1100, '#5a7bc0', '#0d1a40');
    const r = rng(12);
    g.fillStyle = '#f4ecd0';
    for (let i = 0; i < 70; i++) { g.globalAlpha = .3 + r() * .6; g.beginPath(); g.arc(r() * w, VAL + r() * 700, 1 + r() * 2.2, 0, 2 * PI); g.fill(); }
    g.globalAlpha = 1;
    predios(g, r, 1020, h, ['#18213d', '#1d2848', '#141b33'], '#f2c35c', .32);
  },
  jardim(g, w, h) {
    g.fillStyle = vgrad(g, h, [[0, '#16285a'], [.7, '#2a4a80'], [1, '#30528a']]); g.fillRect(0, 0, w, h);
    pinceladas(g, w, h, 21, 1000, '#5a7bc0', '#0d1a40');
    const r = rng(22);
    g.fillStyle = '#f4ecd0';
    for (let i = 0; i < 50; i++) { g.globalAlpha = .3 + r() * .5; g.beginPath(); g.arc(r() * w, VAL + r() * 600, 1 + r() * 2, 0, 2 * PI); g.fill(); }
    g.globalAlpha = 1;
    morro(g, r, 1230, 30, '#1f3a3a', h);
    for (let i = 0; i < 7; i++) arvore(g, 60 + i * 165 + r() * 40, 1330 + r() * 30, 1 + r() * .4);
    morro(g, r, 1360, 16, '#23402f', h);
  },
  por_do_sol(g, w, h) {
    g.fillStyle = vgrad(g, h, [[0, '#b8456a'], [.45, '#e0705a'], [.75, '#f2a552'], [1, '#f6c66c']]); g.fillRect(0, 0, w, h);
    pinceladas(g, w, h, 31, 900, '#ffd29a', '#9a3456');
    const r = rng(32);
    morro(g, r, 1240, 26, '#6a3f6e', h);
    morro(g, r, 1320, 18, '#57355f', h);
  },
  dia(g, w, h) {
    g.fillStyle = vgrad(g, h, [[0, '#93c9e8'], [1, '#d6ecf3']]); g.fillRect(0, 0, w, h);
    pinceladas(g, w, h, 41, 700, '#ffffff', '#7fb2d4');
    const r = rng(42);
    predios(g, r, 760, 1330, ['#a07aa6', '#8c6a9c', '#b48aae', '#97749f'], '#f2d8b8', .75, [90, 170]);
    g.fillStyle = '#cfc6cc'; g.fillRect(0, 1330, w, h - 1330);
    g.fillStyle = '#b9afb6'; g.fillRect(0, 1330, w, 10);
  },
  palacio(g, w, h) {
    g.fillStyle = vgrad(g, h, [[0, '#3b2e66'], [1, '#55438a']]); g.fillRect(0, 0, w, h);
    pinceladas(g, w, h, 51, 1000, '#7d69b5', '#241a48');
    for (let i = 0; i < 4; i++) {
      const x = 70 + i * 250, y0 = 520, y1 = 1300;
      g.fillStyle = '#2d2255';
      g.beginPath(); g.moveTo(x, y1); g.lineTo(x, y0 + 90); g.arc(x + 90, y0 + 90, 90, PI, 0); g.lineTo(x + 180, y1); g.closePath(); g.fill();
      g.fillStyle = '#6a58a0'; g.globalAlpha = .35;
      g.beginPath(); g.moveTo(x + 20, y1); g.lineTo(x + 20, y0 + 100); g.arc(x + 90, y0 + 100, 70, PI, 0); g.lineTo(x + 160, y1); g.closePath(); g.fill();
      g.globalAlpha = 1;
    }
    g.fillStyle = '#2a2050'; g.fillRect(0, 1300, w, h - 1300);
  },
  creme(g, w, h) {
    g.fillStyle = vgrad(g, h, [[0, '#f2e1bd'], [1, '#f7ecd4']]); g.fillRect(0, 0, w, h);
    pinceladas(g, w, h, 61, 700, '#fff6e4', '#e0c89c');
    const r = rng(62);
    for (let i = 0; i < 5; i++) nuvemForma(g, 120 + i * 220 + r() * 40, 1280 + r() * 80, .9 + r() * .5, '#fffaf0');
  },
  campo(g, w, h) {
    g.fillStyle = vgrad(g, h, [[0, '#86c0e2'], [1, '#d8eef4']]); g.fillRect(0, 0, w, h);
    pinceladas(g, w, h, 71, 700, '#ffffff', '#6fa8cf');
    const r = rng(72);
    nuvemForma(g, 230, 330, 1.1, '#fbfdff'); nuvemForma(g, 820, 420, .9, '#fbfdff');
    morro(g, r, 1140, 50, '#8cae73', h);
    for (let i = 0; i < 5; i++) arvore(g, 90 + i * 230 + r() * 50, 1250 + r() * 20, .8 + r() * .3);
    morro(g, r, 1290, 30, '#6f9a58', h);
  },
  deserto(g, w, h) {
    g.fillStyle = vgrad(g, h, [[0, '#e9b36c'], [.7, '#f4d39a'], [1, '#f8e2b4']]); g.fillRect(0, 0, w, h);
    pinceladas(g, w, h, 81, 800, '#fff0cc', '#c98d4a');
    const r = rng(82);
    morro(g, r, 1180, 60, '#d49a5c', h);
    morro(g, r, 1300, 30, '#c0844a', h);
  }
};
const CEN = {};
function cenario(nome) {
  if (!CEN[nome]) {
    const c = tela(W, FUNDO + 40), g = c.getContext('2d');
    (PINTA[nome] || PINTA.noite)(g, c.width, c.height);
    CEN[nome] = c;
  }
  return CEN[nome];
}

// ---------------------------------------------------------------- chão, cortina e bambolina (estáticos)
const CHAO = (() => {
  const c = tela(W, H - FUNDO), g = c.getContext('2d'), h = c.height;
  const m = T.madeira || '#B7814E';
  g.fillStyle = vgrad(g, h, [[0, '#6e4628'], [.25, m], [.8, '#9a6a3e'], [1, '#5a3a22']]); g.fillRect(0, 0, W, h);
  const r = rng(91);
  let y = 0, k = 0;                                   // tábuas: mais finas no fundo, mais largas na frente
  while (y < BORDA - FUNDO) {
    const alt = 14 + k * 7; y += alt; k++;
    g.fillStyle = 'rgba(60,34,16,.45)'; g.fillRect(0, y, W, 2);
    let x = -r() * 200;
    while (x < W) { x += 160 + r() * 260; g.fillRect(x, y - alt, 2, alt); }
  }
  pinceladas(g, W, BORDA - FUNDO, 92, 300, '#e0b07a', '#5a3418');
  const yb = BORDA - FUNDO;                           // ribalta
  g.fillStyle = '#3a2414'; g.fillRect(0, yb, W, 46);
  g.fillStyle = '#7a5230'; g.fillRect(0, yb, W, 6);
  g.fillStyle = T.dourado || '#D4A84A'; g.fillRect(0, yb + 40, W, 4);
  g.fillStyle = '#140d08'; g.fillRect(0, yb + 46, W, h);
  return c;
})();
const CORTINA = (() => {                              // veludo com dobras, comprimido conforme abre
  const c = tela(620, H), g = c.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 620, 0);
  const n = 11;
  for (let i = 0; i <= n; i++) {
    gr.addColorStop(i / n, T.cortina_escura || '#14244F');
    if (i < n) gr.addColorStop((i + .5) / n, T.cortina || '#2F4D9A');
  }
  g.fillStyle = gr; g.fillRect(0, 0, 620, H);
  const v = g.createLinearGradient(0, 0, 0, H);
  v.addColorStop(0, 'rgba(0,0,0,.25)'); v.addColorStop(.4, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,.35)');
  g.fillStyle = v; g.fillRect(0, 0, 620, H);
  pinceladas(g, 620, H, 93, 200, 'rgba(255,255,255,.6)', 'rgba(0,0,0,.6)');
  return c;
})();
const BAMBOLINA = (() => {
  const c = tela(W, VAL + 60), g = c.getContext('2d');
  const d = T.dourado || '#D4A84A';
  g.fillStyle = vgrad(g, VAL, [[0, T.cortina_escura || '#14244F'], [.6, T.cortina || '#2F4D9A'], [1, T.cortina_escura || '#14244F']]);
  g.beginPath(); g.moveTo(0, 0); g.lineTo(W, 0); g.lineTo(W, VAL - 30);
  const n = 12, lw = W / n;
  for (let i = n; i > 0; i--) g.quadraticCurveTo(lw * (i - .5), VAL + 18, lw * (i - 1), VAL - 30);
  g.closePath(); g.fill();
  g.strokeStyle = 'rgba(0,0,0,.25)'; g.lineWidth = 3;
  for (let i = 1; i < n; i++) { g.beginPath(); g.moveTo(lw * i, 0); g.lineTo(lw * i, VAL - 30); g.stroke(); }
  g.strokeStyle = d; g.lineWidth = 5;                // corda dourada
  g.beginPath(); g.moveTo(0, VAL - 30);
  for (let i = 0; i < n; i++) g.quadraticCurveTo(lw * (i + .5), VAL + 18, lw * (i + 1), VAL - 30);
  g.stroke();
  g.lineWidth = 2;                                   // franja
  for (let i = 0; i < n; i++) for (let k = 1; k < 24; k++) {
    const u = k / 24, x = lw * (i + u), y = (VAL - 30) * (1 - u) * (1 - u) + 2 * (1 - u) * u * (VAL + 18) + u * u * (VAL - 30);
    g.strokeStyle = k % 2 ? d : '#a07a2c';
    g.beginPath(); g.moveTo(x, y); g.lineTo(x, y + 16); g.stroke();
  }
  return c;
})();
const GRAO = [0, 1, 2].map(k => {
  const c = tela(256, 256), g = c.getContext('2d'), im = g.createImageData(256, 256), r = rng(300 + k);
  for (let i = 0; i < im.data.length; i += 4) { const v = 128 + (r() - .5) * 110; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
  g.putImageData(im, 0, 0); return c;
});

// ---------------------------------------------------------------- personagens prontos (o plano só troca o que quiser)
const PERSONAGENS = {
  povo:    { roupa: '#6b7a99', calca: '#3c3a40', cabelo: '#2a1e16' },
  jesus:   { roupa: '#efe8da', faixa: '#7a4a2a', manto: true, cabelo: '#4a2f1c', cabelo_longo: true, barba: true },
  discipulo: { roupa: '#8aa0c8', manto: true, cabelo: '#4a3424', barba: true },
  soldado: { roupa: '#b8352c', calca: '#5a3a2a', chapeu: 'capacete', objeto: 'lanca', cabelo: '#3a2a1e' },
  rei:     { roupa: '#6b3d8a', manto: true, chapeu: 'coroa', barba: true, cabelo: '#4a3424', objeto: 'cetro' },
  diabo:   { roupa: '#d63a2a', calca: '#b82e22', pele: '#d63a2a', chapeu: 'chifres', objeto: 'tridente', cabelo: '#9a2018' },
  menino:  { roupa: '#e8b23a', calca: '#3c3a40', cabelo: '#2a1e16', escala: .82 },
  pessoa:  { roupa: '#e8b23a', calca: '#3c3a40', cabelo: '#2a1e16' },
  gigante: { roupa: '#8a7a52', calca: '#4a4030', chapeu: 'capacete', objeto: 'lanca', barba: true, cabelo: '#2a1e16', escala: 1.45 }
};
const POSES = {                                       // [ombro, cotovelo] em graus; 0 = braço caído
  repouso: { e: [12, 8], d: [12, 8] },
  aponta:  { e: [12, 8], d: [96, 0] },
  abertos: { e: [96, 0], d: [96, 0] },
  levanta: { e: [158, 0], d: [158, 0] },
  vitoria: { e: [140, 25], d: [140, 25] },
  acena:   { e: [12, 8], d: [140, 30], osc: 1 },
  mao_alta: { e: [12, 8], d: [168, 0] },
  bencao:  { e: [12, 8], d: [70, 80] },
  ora:     { e: [30, 120], d: [30, 120] },
  triste:  { e: [4, 0], d: [4, 0], cabeca: 10 },
  golpe:   { e: [20, 10], d: [55, -35] },
  gira:    { e: [12, 8], d: [150, 10], gira: 1 }
};

// ---------------------------------------------------------------- monta as cenas
let ini = 0;
const CENAS = P.cenas.map((c, k) => {
  const S = ini, D = c.dur; ini += D;
  const bonecos = (c.bonecos || []).map((b, i) => {
    const base = PERSONAGENS[b.personagem || 'povo'] || PERSONAGENS.povo;
    const o = { pele: '#d9a77c', calca: '#3c3a40', cabelo: '#2a1e16', escala: 1, ...base, ...b };
    o.id = 1000 * (k + 1) + i; o.t0 = S + (b.em ?? .12 + i * .1);
    o.acoes = (b.acoes || []).map(a => ({ ...a, t: S + (a.em || 0) })).sort((a, b) => a.t - b.t);
    return o;
  });
  const placas = (c.placas || []).map((p, i) => {
    let l1 = p.l1, l2 = p.l2;
    if (p.texto != null) { const s = String(p.texto).split('|'); if (s.length > 1) { l1 = s[0].trim(); l2 = s[1].trim(); } else l2 = s[0].trim(); }
    return { ...p, l1, l2, x: p.x || 0, id: 5000 * (k + 1) + i, t0: S + (p.em ?? .1) };
  });
  placas.forEach((p, i) => {                          // quando sai: a próxima que não empilha, ou o fim da cena
    const prox = placas.slice(i + 1).find(q => !q.empilha);
    p.t1 = prox ? prox.t0 - .36 : S + D - .22;   // a de antes já subiu quando a nova desce
    if (c.cortina === 'fecha' && !prox) p.t1 = 1e9;
  });
  const auto = c.auto === false ? [] : (c.cenario === 'noite' || c.cenario === 'jardim' || !c.cenario) ? [{ tipo: 'lua', x: 330, y: -690, raio: 46, em: .2 }] : [];
  const aderecos = [...auto, ...(c.aderecos || [])].map((a, i) => ({ ...a, id: 8000 * (k + 1) + i, t0: S + (a.em ?? .15) }));
  return { ...c, cenario: c.cenario || 'noite', S, D, bonecos, placas, aderecos };
});
const DUR = ini;
CENAS.forEach((c, k) => {
  c.prox = CENAS[k + 1]; c.ant = CENAS[k - 1];
  if (c.cortina === 'fecha' && c.ant) c.cenario = c.ant.cenario;   // no CTA a cortina fecha sobre o mesmo cenário
});

// cache das placas (papel + sombra assados uma vez)
function cartao(p) {
  if (p.cache) return p.cache;
  const g0 = tela(10, 10).getContext('2d');
  const s1 = p.tam1 || 52, s2 = p.tam2 || (p.l1 ? 80 : 112);
  g0.font = `500 ${s1}px "${FX}"`; const w1 = p.l1 ? g0.measureText(p.l1).width : 0;
  g0.font = `700 ${s2}px "${FT}"`; const w2 = p.l2 ? g0.measureText(p.l2).width : 0;
  const w = Math.max(p.l1 ? 380 : 170, w1, w2) + 92, h = (p.l1 ? s1 * 1.3 : 0) + (p.l2 ? s2 * 1.12 : 0) + 58;
  const M = 50, c = tela(w + 2 * M, h + 2 * M), g = c.getContext('2d');
  g.shadowColor = 'rgba(20,10,4,.42)'; g.shadowBlur = 26; g.shadowOffsetX = 8; g.shadowOffsetY = 16;
  const gr = g.createLinearGradient(M, M, M + w, M + h);
  gr.addColorStop(0, T.papel || '#F3E8D2'); gr.addColorStop(1, '#e6d3ae');
  g.fillStyle = gr; g.fillRect(M, M, w, h);
  g.shadowColor = 'transparent';
  pinceladas(g, c.width, c.height, p.id, 60, 'rgba(255,255,255,.9)', 'rgba(140,110,60,.9)');
  g.globalCompositeOperation = 'destination-in'; g.fillRect(M, M, w, h); g.globalCompositeOperation = 'source-over';
  const c2 = tela(c.width, c.height), g2 = c2.getContext('2d');
  g2.shadowColor = 'rgba(20,10,4,.42)'; g2.shadowBlur = 26; g2.shadowOffsetX = 8; g2.shadowOffsetY = 16;
  g2.drawImage(c, 0, 0); g2.shadowColor = 'transparent';
  g2.strokeStyle = T.papel_borda || '#D9C49C'; g2.lineWidth = 3; g2.strokeRect(M + 9, M + 9, w - 18, h - 18);
  g2.textAlign = 'center'; g2.textBaseline = 'alphabetic';
  let y = M + 29;
  if (p.l1) { g2.fillStyle = T.tinta || '#2B2622'; g2.font = `500 ${s1}px "${FX}"`; y += s1 * 1.02; g2.fillText(p.l1, M + w / 2, y); y += s1 * .28; }
  if (p.l2) { g2.fillStyle = p.cor || T.acento || '#A8322A'; g2.font = `700 ${s2}px "${FT}"`; y += s2 * .92; g2.fillText(p.l2, M + w / 2, y); }
  p.cache = { c: c2, w, h, M };
  if (p.ref) {
    g0.font = `500 42px "${FX}"`; const wr = g0.measureText(p.ref).width + 48, hr = 60;
    const r = tela(wr + 30, hr + 30), gr2 = r.getContext('2d');
    gr2.shadowColor = 'rgba(20,10,4,.35)'; gr2.shadowBlur = 10; gr2.shadowOffsetY = 5;
    gr2.fillStyle = '#efe2c6'; gr2.fillRect(15, 10, wr, hr); gr2.shadowColor = 'transparent';
    gr2.strokeStyle = T.papel_borda || '#D9C49C'; gr2.lineWidth = 2; gr2.strokeRect(19, 14, wr - 8, hr - 8);
    gr2.fillStyle = '#4a4038'; gr2.font = `500 42px "${FX}"`; gr2.textAlign = 'center'; gr2.fillText(p.ref, 15 + wr / 2, 10 + hr / 2 + 14);
    p.cache.ref = { c: r, w: wr, h: hr };
  }
  return p.cache;
}
CENAS.forEach(c => c.placas.forEach((p, i) => {    // placa empilhada entra logo abaixo da anterior, mordendo a borda
  const C = cartao(p), q = c.placas[i - 1];
  if (p.y != null) p.y = PLACA_Y + p.y;
  else p.y = p.empilha && q ? q.y + q.cache.h / 2 + C.h / 2 - 10 : PLACA_Y;
}));

// ---------------------------------------------------------------- placa pendurada: cai no barbante e balança
function barbante(x0, y0, x1, y1) {
  ctx.strokeStyle = 'rgba(236,226,204,.6)'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
}
function placa(p, t) {
  if (t < p.t0 - .02 || t > p.t1 + .4) return;
  const C = p.cache, dt = t - p.t0;
  let dy = -(1 - eoc(dt / .5)) * (p.y + C.h);         // desce do urdimento
  if (t > p.t1) dy -= eic((t - p.t1) / .36) * (p.y + C.h + 60);   // sobe de volta
  const lado = hash(p.id, 3) < .5 ? -1 : 1;
  const ang = (p.rot || 0) * DEG + lado * 6.5 * DEG * Math.exp(-3 * Math.max(0, dt)) * Math.sin(2 * PI * 1.25 * Math.max(0, dt) + .4)
    + .55 * DEG * Math.sin(2 * PI * .32 * t + p.id);
  const cx = CX + p.x + Math.sin(ang) * 90, top = p.y - C.h / 2 + dy;
  const ax = C.w / 2 - 44;
  const pt = (x, y) => [cx + x * Math.cos(ang) - y * Math.sin(ang), top + x * Math.sin(ang) + y * Math.cos(ang)];
  const [ex, ey] = pt(-ax, 6), [dx2, dy2] = pt(ax, 6);
  barbante(cx - ax - 6, 0, ex, ey); barbante(cx + ax + 6, 0, dx2, dy2);
  ctx.save(); ctx.translate(cx, top); ctx.rotate(ang);
  ctx.drawImage(C.c, -C.w / 2 - C.M, -C.M);
  ctx.beginPath(); ctx.fillStyle = '#8a7a5a';
  ctx.arc(-ax, 10, 4, 0, 2 * PI); ctx.arc(ax, 10, 4, 0, 2 * PI); ctx.fill();
  if (C.ref) {                                         // plaquinha da referência, pendurada embaixo
    const u = eoc((dt - .28) / .4);
    if (u > 0) {
      const R = C.ref, yy = C.h + 14 - (1 - u) * 30;
      ctx.globalAlpha = u;
      barbante(-R.w / 2 + 20, C.h - 6, -R.w / 2 + 20, yy + 12); barbante(R.w / 2 - 20, C.h - 6, R.w / 2 - 20, yy + 12);
      ctx.save(); ctx.translate(0, yy); ctx.rotate(Math.sin(2 * PI * .9 * dt + 1) * 2.5 * DEG * Math.exp(-2 * Math.max(0, dt - .3)));
      ctx.drawImage(R.c, -R.w / 2 - 15, -10); ctx.restore();
      ctx.globalAlpha = 1;
    }
  }
  ctx.restore();
}

// ---------------------------------------------------------------- bonecos de papel
function poseEm(b, t) {
  let atual = POSES[b.pose || 'repouso'] || POSES.repouso, prev = atual, tt = -1;
  for (const a of b.acoes) if (a.pose && a.t <= t) { prev = atual; atual = POSES[a.pose] || atual; tt = a.t; }
  const u = tt < 0 ? 1 : eio((t - tt) / .32);
  const mix = (A, B) => [lerp(A[0], B[0], u), lerp(A[1], B[1], u)];
  return { e: mix(prev.e, atual.e), d: mix(prev.d, atual.d), osc: atual.osc, gira: atual.gira, cabeca: lerp(prev.cabeca || 0, atual.cabeca || 0, u) };
}
function braco(lado, a, b, cor, pele, obj, t, id) {
  const sx = lado * 40, sy = -316;
  const ex = sx + lado * Math.sin(a * DEG) * 80, ey = sy + Math.cos(a * DEG) * 80;
  const hx = ex + lado * Math.sin((a + b) * DEG) * 76, hy = ey + Math.cos((a + b) * DEG) * 76;
  ctx.strokeStyle = cor; ctx.lineWidth = 17; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(ex, ey); ctx.lineTo(hx, hy); ctx.stroke();
  if (obj) objeto(obj, hx, hy, Math.atan2(hy - ey, hx - ex), t, id);
  ctx.fillStyle = pele; ctx.beginPath(); ctx.arc(hx, hy, 10, 0, 2 * PI); ctx.fill();
}
function objeto(o, x, y, ang, t, id) {
  ctx.save(); ctx.translate(x, y);
  if (o === 'espada') {
    ctx.rotate(ang);
    ctx.strokeStyle = '#7a6a4a'; ctx.lineWidth = 7; ctx.beginPath(); ctx.moveTo(-6, -14); ctx.lineTo(-6, 14); ctx.stroke();
    ctx.strokeStyle = '#d5dbe0'; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(128, 0); ctx.stroke();
    ctx.strokeStyle = '#9aa3ab'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(4, 2); ctx.lineTo(126, 2); ctx.stroke();
  } else if (o === 'lanca' || o === 'tridente' || o === 'cajado' || o === 'cetro') {
    const L = o === 'cetro' ? 120 : 300;
    ctx.strokeStyle = o === 'cetro' ? '#c9a03a' : '#6a4a2a'; ctx.lineWidth = o === 'cetro' ? 8 : 9;
    ctx.beginPath(); ctx.moveTo(0, L * .35); ctx.lineTo(0, -L * .65); ctx.stroke();
    if (o === 'lanca') { ctx.fillStyle = '#cfd6dc'; ctx.beginPath(); ctx.moveTo(-11, -L * .65); ctx.lineTo(0, -L * .65 - 42); ctx.lineTo(11, -L * .65); ctx.fill(); }
    if (o === 'cetro') { ctx.fillStyle = T.dourado || '#D4A84A'; ctx.beginPath(); ctx.arc(0, -L * .65 - 10, 14, 0, 2 * PI); ctx.fill(); }
    if (o === 'cajado') { ctx.beginPath(); ctx.arc(-18, -L * .65, 18, 0, PI, true); ctx.stroke(); }
    if (o === 'tridente') {
      ctx.strokeStyle = '#3a3a3a'; ctx.lineWidth = 6; ctx.beginPath();
      ctx.moveTo(-22, -L * .65 - 34); ctx.lineTo(-22, -L * .65); ctx.lineTo(22, -L * .65); ctx.lineTo(22, -L * .65 - 34);
      ctx.moveTo(0, -L * .65); ctx.lineTo(0, -L * .65 - 42); ctx.stroke();
    }
  } else if (o === 'tocha') {
    ctx.strokeStyle = '#5a3a22'; ctx.lineWidth = 9; ctx.beginPath(); ctx.moveTo(0, 20); ctx.lineTo(0, -80); ctx.stroke();
    const k = Math.floor(t * 12), f = 1 + (hash(id, k) - .5) * .25;
    ctx.fillStyle = '#f08a2a'; ctx.beginPath(); ctx.ellipse(0, -104, 16 * f, 30 * f, 0, 0, 2 * PI); ctx.fill();
    ctx.fillStyle = '#ffd25a'; ctx.beginPath(); ctx.ellipse(0, -98, 8 * f, 16 * f, 0, 0, 2 * PI); ctx.fill();
  } else if (o === 'funda') {
    const giro = t * 2 * PI * 2.2;
    ctx.strokeStyle = '#7a5a3a'; ctx.lineWidth = 3;
    const px = Math.sin(giro) * 18, py = 70 + Math.cos(giro) * 6;
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(px - 8, py); ctx.moveTo(0, 0); ctx.lineTo(px + 8, py); ctx.stroke();
    ctx.fillStyle = '#6a4a2a'; ctx.beginPath(); ctx.ellipse(px, py + 4, 13, 8, 0, 0, 2 * PI); ctx.fill();
    ctx.fillStyle = '#9a948a'; ctx.beginPath(); ctx.arc(px, py, 7, 0, 2 * PI); ctx.fill();
  }
  ctx.restore();
}
function boneco(b, c, t) {
  const sai = c.prox ? c.prox.S : 1e9;
  if (t < b.t0 - .02) return;
  if (b.sai != null && t > c.S + b.sai + .6) return;
  const P0 = poseEm(b, t);
  let x = b.x || 0, lift = 0, queda = 0, passo = 0;
  const ent = b.entra || 'baixo', ue = eoc((t - b.t0) / .5);
  if (ent === 'baixo') lift = -(1 - ue) * 560;
  else { const d = ent === 'esquerda' ? -1 : 1; x += d * (1 - eio((t - b.t0) / .8)) * 720; if (t - b.t0 < .8) passo = 1; }
  if (b.sai != null) lift -= eic((t - c.S - b.sai) / .5) * 600;
  if (t > sai - .3) lift -= eic((t - sai + .3) / .45) * 600;   // desce pelo alçapão na troca de cena
  for (const a of b.acoes) {
    if (a.anda != null && t >= a.t) { const u = eio((t - a.t) / (a.dur || .9)); x += a.anda * u; if (u < 1) passo = 1; }
    if (a.cai && t >= a.t) queda = (a.cai === 'esquerda' ? -1 : 1) * 86 * DEG * eic((t - a.t) / .55);
  }
  const s = b.escala || 1, chao = PES - (b.y || 0) + (b.sentado ? 45 : 0);
  const bob = Math.sin(2 * PI * .9 * t + b.id) * 3 + (passo ? -Math.abs(Math.sin(t * 2 * PI * 2.2)) * 12 : 0);
  const balanco = Math.sin(2 * PI * .5 * t + b.id * .7) * 1.3 * DEG;
  ctx.save();
  if (lift < -1) { ctx.beginPath(); ctx.rect(0, 0, W, chao + 10); ctx.clip(); }
  if (!b.sentado) {
    ctx.fillStyle = `rgba(30,16,6,${.28 * (1 - clamp(-lift / 200))})`;   // sombra no chão
    ctx.beginPath(); ctx.ellipse(CX + x, chao + 6, 70 * s, 12 * s, 0, 0, 2 * PI); ctx.fill();
  }
  ctx.translate(CX + x, chao - lift - bob);
  ctx.rotate(queda + (queda ? 0 : balanco));
  ctx.scale(s * (b.olha === -1 ? -1 : 1), s);
  // varetas e pernas
  ctx.strokeStyle = '#2a1c12'; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.moveTo(-14, 0); ctx.lineTo(-14, 26); ctx.moveTo(14, 0); ctx.lineTo(14, 26); ctx.stroke();
  if (!b.manto) {
    ctx.fillStyle = b.calca; ctx.fillRect(-23, -150, 17, 150); ctx.fillRect(6, -150, 17, 150);
    ctx.fillStyle = '#2a1c12'; ctx.fillRect(-27, -8, 23, 8); ctx.fillRect(4, -8, 23, 8);
  } else { ctx.fillStyle = b.pele; ctx.fillRect(-20, -14, 14, 14); ctx.fillRect(6, -14, 14, 14); }
  // cabelo comprido (atrás)
  if (b.cabelo_longo) { ctx.fillStyle = b.cabelo; ctx.beginPath(); ctx.moveTo(-37, -386); ctx.lineTo(-42, -300); ctx.lineTo(42, -300); ctx.lineTo(37, -386); ctx.fill(); }
  // corpo (túnica ou manto)
  const pe = b.manto ? -12 : -142, lb = b.manto ? 64 : 47;
  const gr = ctx.createLinearGradient(-lb, 0, lb, 0);
  gr.addColorStop(0, b.roupa); gr.addColorStop(.62, b.roupa); gr.addColorStop(1, 'rgba(0,0,0,.18)');
  ctx.fillStyle = b.roupa;
  ctx.beginPath(); ctx.moveTo(-40, -330); ctx.quadraticCurveTo(0, -342, 40, -330); ctx.lineTo(lb, pe); ctx.lineTo(-lb, pe); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(0,0,0,.13)';
  ctx.beginPath(); ctx.moveTo(14, -334); ctx.lineTo(40, -330); ctx.lineTo(lb, pe); ctx.lineTo(lb * .45, pe); ctx.closePath(); ctx.fill();
  if (b.faixa) { ctx.strokeStyle = b.faixa; ctx.lineWidth = 22; ctx.lineCap = 'butt'; ctx.beginPath(); ctx.moveTo(-30, -332); ctx.lineTo(lb * .62, pe + 8); ctx.stroke(); }
  if (!b.manto) { ctx.fillStyle = 'rgba(0,0,0,.28)'; ctx.fillRect(-lb, -152, 2 * lb, 9); }
  // pescoço e cabeça
  ctx.save(); ctx.translate(0, -340); ctx.rotate((P0.cabeca || 0) * DEG);
  ctx.fillStyle = b.pele; ctx.fillRect(-9, -12, 18, 20);
  ctx.beginPath(); ctx.arc(0, -40, 34, 0, 2 * PI); ctx.fill();
  ctx.fillStyle = b.cabelo;
  ctx.beginPath(); ctx.arc(0, -44, 36, PI * 1.02, PI * 1.98); ctx.closePath(); ctx.fill();
  if (b.barba) { ctx.fillStyle = b.cabelo; ctx.beginPath(); ctx.arc(0, -40, 35, .02 * PI, .98 * PI); ctx.quadraticCurveTo(0, 6, 35, -38); ctx.fill(); ctx.beginPath(); ctx.moveTo(-34, -40); ctx.quadraticCurveTo(0, 8, 34, -40); ctx.lineTo(34, -30); ctx.quadraticCurveTo(0, 22, -34, -30); ctx.fill(); }
  if (b.chapeu === 'coroa') {
    ctx.fillStyle = T.dourado || '#D4A84A'; ctx.beginPath(); ctx.moveTo(-30, -70);
    for (let i = 0; i <= 4; i++) { ctx.lineTo(-30 + i * 15, i % 2 ? -88 : -104); }
    ctx.lineTo(30, -70); ctx.closePath(); ctx.fill();
  } else if (b.chapeu === 'capacete') {
    ctx.fillStyle = '#b08a4a'; ctx.beginPath(); ctx.arc(0, -48, 39, PI, 0); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#c0382c'; ctx.beginPath(); ctx.ellipse(0, -96, 12, 22, 0, 0, 2 * PI); ctx.fill();
  } else if (b.chapeu === 'chifres') {
    ctx.fillStyle = '#f2ece0';
    for (const d of [-1, 1]) { ctx.beginPath(); ctx.moveTo(d * 16, -70); ctx.quadraticCurveTo(d * 40, -96, d * 30, -118); ctx.lineTo(d * 30, -78); ctx.fill(); }
  }
  ctx.restore();
  // braços (o objeto vai na mão direita)
  const osc = P0.osc ? Math.sin(t * 2 * PI * 1.6) * 18 : 0;
  const gira = P0.gira ? Math.sin(t * 2 * PI * 2.2) * 12 : 0;
  const resp = Math.sin(2 * PI * .7 * t + b.id) * 3;
  braco(-1, P0.e[0] + resp, P0.e[1], b.roupa, b.pele, null, t, b.id);
  braco(1, P0.d[0] + osc + gira - resp, P0.d[1], b.roupa, b.pele, b.objeto, t, b.id);
  ctx.restore();
}

// ---------------------------------------------------------------- adereços
const NO_CEU = new Set(['sol', 'lua', 'nuvem', 'estrela']);
function aderecoForma(a, t) {
  const s = a.escala || 1;
  if (a.tipo === 'sol') {
    const r = a.raio || 80;
    ctx.save(); ctx.rotate(t * .25);
    ctx.fillStyle = '#f2b93a';
    for (let i = 0; i < 16; i++) { ctx.rotate(2 * PI / 16); ctx.beginPath(); ctx.moveTo(-9, -r - 4); ctx.lineTo(0, -r - 30); ctx.lineTo(9, -r - 4); ctx.fill(); }
    ctx.restore();
    ctx.fillStyle = '#f6cc52'; ctx.beginPath(); ctx.arc(0, 0, r, 0, 2 * PI); ctx.fill();
    ctx.fillStyle = 'rgba(255,240,180,.55)'; ctx.beginPath(); ctx.arc(-r * .25, -r * .25, r * .55, 0, 2 * PI); ctx.fill();
  } else if (a.tipo === 'lua') {
    const r = a.raio || 46;
    ctx.fillStyle = '#f4ecd0'; ctx.beginPath(); ctx.arc(0, 0, r, 0, 2 * PI); ctx.arc(r * .45, -r * .2, r * .85, 0, 2 * PI, true); ctx.fill('evenodd');
  } else if (a.tipo === 'nuvem') nuvemForma(ctx, 0, 0, s, '#fffaf0');
  else if (a.tipo === 'balao') {
    const r = 46 * s, sob = Math.sin(t * 2 * PI * .6 + a.id) * 8;
    const [fx, fy] = a.fio_ate || [0, 260];
    ctx.strokeStyle = 'rgba(60,40,30,.7)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(0, sob + r * 1.15); ctx.quadraticCurveTo(fx * .3 + 14, (fy + sob) * .6, fx, fy); ctx.stroke();
    ctx.fillStyle = a.cor || '#d8352a'; ctx.beginPath(); ctx.ellipse(0, sob, r * .88, r * 1.05, 0, 0, 2 * PI); ctx.fill();
    ctx.beginPath(); ctx.moveTo(-7, sob + r * 1.03); ctx.lineTo(7, sob + r * 1.03); ctx.lineTo(0, sob + r * 1.18); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,.35)'; ctx.beginPath(); ctx.ellipse(-r * .35, sob - r * .4, r * .18, r * .3, -.4, 0, 2 * PI); ctx.fill();
    if (a.texto) { ctx.fillStyle = '#fff4e8'; ctx.font = `italic 700 ${24 * s}px "${FT}"`; ctx.textAlign = 'center'; ctx.fillText(a.texto, 0, sob + 8 * s); }
  } else if (a.tipo === 'trono') {
    ctx.scale(s, s);
    ctx.fillStyle = a.cor || '#a8322a'; ctx.fillRect(-80, -330, 160, 230);
    ctx.fillStyle = T.dourado || '#D4A84A';
    ctx.fillRect(-92, -340, 18, 340); ctx.fillRect(74, -340, 18, 340); ctx.fillRect(-100, -120, 200, 26);
    ctx.beginPath(); ctx.arc(-83, -346, 14, 0, 2 * PI); ctx.arc(83, -346, 14, 0, 2 * PI); ctx.fill();
  } else if (a.tipo === 'urna') {
    ctx.scale(s, s);
    ctx.fillStyle = '#6a4a2e'; ctx.fillRect(-120, -150, 240, 16); ctx.fillRect(-110, -134, 12, 134); ctx.fillRect(98, -134, 12, 134);
    ctx.fillStyle = '#c9ccd2'; ctx.fillRect(-110, -290, 220, 140);
    ctx.fillStyle = '#2a3e6a'; ctx.fillRect(-96, -274, 104, 70);
    ctx.fillStyle = '#3a3a3a';
    for (let i = 0; i < 3; i++) for (let k = 0; k < 4; k++) ctx.fillRect(24 + i * 26, -276 + k * 28, 20, 20);
    ctx.fillStyle = '#3a9a4a'; ctx.fillRect(76, -178, 22, 14);
  } else if (a.tipo === 'pomba') {
    const bat = Math.sin(t * 2 * PI * 4) * .6;
    ctx.scale(s, s); ctx.fillStyle = '#fbf8f2';
    ctx.beginPath(); ctx.ellipse(0, 0, 30, 14, 0, 0, 2 * PI); ctx.fill();
    ctx.beginPath(); ctx.arc(28, -8, 11, 0, 2 * PI); ctx.fill();
    ctx.fillStyle = '#e8a03a'; ctx.beginPath(); ctx.moveTo(38, -8); ctx.lineTo(50, -5); ctx.lineTo(38, -3); ctx.fill();
    ctx.fillStyle = '#efe9de';
    ctx.save(); ctx.rotate(-bat); ctx.beginPath(); ctx.moveTo(-6, -4); ctx.quadraticCurveTo(-10, -50, -40, -46); ctx.quadraticCurveTo(-20, -18, -6, -4); ctx.fill(); ctx.restore();
  } else if (a.tipo === 'pedra') {
    ctx.fillStyle = '#c4bdb0'; ctx.strokeStyle = '#4a3a2a'; ctx.lineWidth = 3; ctx.beginPath(); ctx.ellipse(0, 0, 14 * s, 10 * s, .3, 0, 2 * PI); ctx.fill(); ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,.45)'; ctx.beginPath(); ctx.ellipse(-4 * s, -3 * s, 5 * s, 3 * s, .3, 0, 2 * PI); ctx.fill();
  } else if (a.tipo === 'saco') {                     // saco de dinheiro (origem no chão)
    ctx.scale(s, s);
    ctx.fillStyle = 'rgba(30,16,6,.25)'; ctx.beginPath(); ctx.ellipse(0, 2, 62, 10, 0, 0, 2 * PI); ctx.fill();
    ctx.fillStyle = '#c9a26a'; ctx.beginPath(); ctx.moveTo(-26, -118); ctx.quadraticCurveTo(-78, -70, -64, -22);
    ctx.quadraticCurveTo(-58, 0, 0, 0); ctx.quadraticCurveTo(58, 0, 64, -22); ctx.quadraticCurveTo(78, -70, 26, -118); ctx.closePath(); ctx.fill();
    ctx.fillStyle = 'rgba(0,0,0,.14)'; ctx.beginPath(); ctx.moveTo(20, -116); ctx.quadraticCurveTo(70, -70, 60, -22); ctx.quadraticCurveTo(50, -4, 18, -2); ctx.quadraticCurveTo(46, -60, 20, -116); ctx.fill();
    ctx.fillStyle = '#b48a52'; ctx.beginPath(); ctx.moveTo(-26, -118); ctx.lineTo(-38, -146); ctx.lineTo(0, -132); ctx.lineTo(38, -146); ctx.lineTo(26, -118); ctx.fill();
    ctx.strokeStyle = '#6a4a2a'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(-28, -118); ctx.lineTo(28, -118); ctx.stroke();
    ctx.fillStyle = a.cor || '#2f7a3a'; ctx.font = `700 64px "${FT}"`; ctx.textAlign = 'center'; ctx.fillText(a.texto || '$', 0, -34);
  } else if (a.tipo === 'nota') {                     // cédula
    ctx.scale(s, s);
    ctx.fillStyle = '#6fae6a'; ctx.fillRect(-46, -22, 92, 44);
    ctx.strokeStyle = '#3f7a3c'; ctx.lineWidth = 3; ctx.strokeRect(-40, -16, 80, 32);
    ctx.fillStyle = '#3f7a3c'; ctx.beginPath(); ctx.arc(0, 0, 11, 0, 2 * PI); ctx.fill();
    ctx.fillStyle = '#cfe8c8'; ctx.font = `700 16px "${FX}"`; ctx.textAlign = 'center'; ctx.fillText('$', 0, 6);
  } else if (a.tipo === 'relogio') {                  // relógio grande com ponteiro girando (origem no centro)
    const r = (a.raio || 120);
    ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.beginPath(); ctx.arc(8, 10, r + 16, 0, 2 * PI); ctx.fill();
    ctx.fillStyle = T.dourado || '#D4A84A'; ctx.beginPath(); ctx.arc(0, 0, r + 16, 0, 2 * PI); ctx.fill();
    ctx.fillStyle = '#fbf6ea'; ctx.beginPath(); ctx.arc(0, 0, r, 0, 2 * PI); ctx.fill();
    ctx.strokeStyle = '#2b2622';
    for (let i = 0; i < 12; i++) { const q = i * PI / 6; ctx.lineWidth = i % 3 ? 4 : 9; ctx.beginPath(); ctx.moveTo(Math.sin(q) * r * .8, -Math.cos(q) * r * .8); ctx.lineTo(Math.sin(q) * r * .93, -Math.cos(q) * r * .93); ctx.stroke(); }
    const q1 = t * 2 * PI * .5, q2 = t * 2 * PI * .05;
    ctx.lineCap = 'round';
    ctx.lineWidth = 12; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.sin(q2) * r * .5, -Math.cos(q2) * r * .5); ctx.stroke();
    ctx.strokeStyle = T.acento || '#E31E24'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.sin(q1) * r * .78, -Math.cos(q1) * r * .78); ctx.stroke();
    ctx.lineCap = 'butt'; ctx.fillStyle = '#2b2622'; ctx.beginPath(); ctx.arc(0, 0, 12, 0, 2 * PI); ctx.fill();
    if (a.check) {                                       // selo verde de confirmado
      const u = eoc((t - a.t0 - a.check) / .35);
      if (u > 0) { ctx.save(); ctx.translate(r * .78, r * .7); ctx.scale(u, u);
        ctx.fillStyle = '#2f9a4a'; ctx.beginPath(); ctx.arc(0, 0, 50, 0, 2 * PI); ctx.fill();
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 12; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(-22, 2); ctx.lineTo(-6, 18); ctx.lineTo(24, -16); ctx.stroke(); ctx.restore(); }
    }
  } else if (a.tipo === 'grafico' || a.tipo === 'quadro') {   // quadro no cavalete (origem no chão): candles ou texto
    ctx.scale(s, s);
    ctx.strokeStyle = '#6a4a2a'; ctx.lineWidth = 10;
    ctx.beginPath(); ctx.moveTo(-110, 0); ctx.lineTo(-70, -330); ctx.moveTo(110, 0); ctx.lineTo(70, -330); ctx.moveTo(0, -20); ctx.lineTo(0, -330); ctx.stroke();
    ctx.fillStyle = '#5a3a22'; ctx.fillRect(-178, -560, 356, 262);
    ctx.fillStyle = a.tipo === 'quadro' ? '#2c3a32' : '#141c26'; ctx.fillRect(-164, -546, 328, 234);
    if (a.tipo === 'quadro') {
      const ls = String(a.texto || '').split('|');
      ctx.fillStyle = '#f2efe6'; ctx.textAlign = 'left';
      ls.forEach((l, i) => { const u = clamp((t - a.t0 - .3 - i * (a.passo || .5)) / .3); if (u <= 0) return;
        ctx.globalAlpha = u; ctx.font = `700 ${i ? 34 : 40}px "${FX}"`; ctx.fillText(l, -140, -490 + i * 56); });
      ctx.globalAlpha = 1;
    } else {
      ctx.strokeStyle = 'rgba(255,255,255,.08)'; ctx.lineWidth = 2;
      for (let i = 1; i < 4; i++) { ctx.beginPath(); ctx.moveTo(-164, -546 + i * 58); ctx.lineTo(164, -546 + i * 58); ctx.stroke(); }
      const n = 9, sobe = a.sobe !== false, vis = clamp((t - a.t0 - .25) / (a.dur_velas || 1.6)) * n;
      let y = sobe ? -350 : -510;
      for (let i = 0; i < n; i++) {
        if (i >= vis) break;
        const r = hash(a.id, i), verde = sobe ? r > .25 : r < .25, d = (verde ? -1 : 1) * (12 + r * 20);
        const x = -140 + i * 33, y1 = y + d;
        ctx.strokeStyle = verde ? '#4fd37a' : '#ff4a4a'; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.moveTo(x + 10, Math.min(y, y1) - 10); ctx.lineTo(x + 10, Math.max(y, y1) + 10); ctx.stroke();
        ctx.fillStyle = ctx.strokeStyle; ctx.fillRect(x, Math.min(y, y1), 20, Math.abs(d) + 4);
        y = clamp(y1, -530, -330);
      }
    }
  } else if (a.tipo === 'calendario') {                // folha de calendário (pendurada)
    ctx.scale(s, s);
    ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fillRect(-82, -62, 172, 190);
    ctx.fillStyle = '#fbf6ea'; ctx.fillRect(-90, -70, 180, 190);
    ctx.fillStyle = T.acento || '#E31E24'; ctx.fillRect(-90, -70, 180, 52);
    const [m, d] = String(a.texto || 'SET|11').split('|');
    ctx.textAlign = 'center'; ctx.fillStyle = '#fff'; ctx.font = `700 34px "${FX}"`; ctx.fillText(m, 0, -32);
    ctx.fillStyle = '#2b2622'; ctx.font = `700 ${String(d).length > 3 ? 40 : 92}px "${FT}"`; ctx.fillText(d, 0, String(d).length > 3 ? 64 : 92);
  } else if (a.tipo === 'seta') {                     // seta grande subindo (verde) ou caindo (vermelha)
    const sobe = a.dir !== 'baixo', u = eoc((t - a.t0) / .5);
    ctx.translate(0, -100 * s); ctx.scale(s, s * (sobe ? 1 : -1)); ctx.translate(0, (1 - u) * 60);
    ctx.fillStyle = a.cor || (sobe ? '#2f9a4a' : (T.acento || '#E31E24'));
    ctx.beginPath(); ctx.moveTo(-34, 90); ctx.lineTo(-34, -20); ctx.lineTo(-80, -20); ctx.lineTo(0, -110); ctx.lineTo(80, -20); ctx.lineTo(34, -20); ctx.lineTo(34, 90); ctx.closePath(); ctx.fill();
  } else if (a.tipo === 'mesa') {                     // mesa de trader (origem no chão; desenha na frente): telas em a.telas (x)
    ctx.scale(s, s);
    for (const dx of (a.telas || [0])) {
      ctx.fillStyle = '#2b2b2b'; ctx.fillRect(dx - 8, -262, 16, 34);
      ctx.fillStyle = '#1b1b1b'; ctx.fillRect(dx - 78, -372, 156, 112);
      ctx.fillStyle = '#0d1520'; ctx.fillRect(dx - 70, -364, 140, 96);
      let y = -310;
      for (let i = 0; i < 7; i++) {
        const r = hash(a.id + dx, i + Math.floor(t * 2)), verde = r > .3, d = (verde ? -1 : 1) * (5 + r * 12), x = dx - 62 + i * 19;
        ctx.fillStyle = verde ? '#4fd37a' : '#ff4a4a'; ctx.fillRect(x, Math.min(y, y + d), 11, Math.abs(d) + 3);
        y = clamp(y + d, -355, -278);
      }
    }
    ctx.fillStyle = '#7a5232'; ctx.fillRect(-330, -230, 660, 30);
    ctx.fillStyle = '#5e3e24'; ctx.fillRect(-310, -200, 620, 200);
    ctx.fillStyle = 'rgba(0,0,0,.15)'; ctx.fillRect(-310, -200, 620, 14);
  } else if (a.tipo === 'estrela') {
    ctx.fillStyle = '#f6d36a'; ctx.beginPath();
    for (let i = 0; i < 10; i++) { const r = (i % 2 ? 18 : 42) * s, q = i * PI / 5 - PI / 2; ctx.lineTo(Math.cos(q) * r, Math.sin(q) * r); }
    ctx.fill();
  }
}
const NO_CHAO = new Set(['saco', 'grafico', 'quadro', 'mesa', 'trono', 'urna']);
function puff(x, y, e, id, r0 = 70) {               // "pop": nuvem de fumaça + cédulas voando, e = 0..1
  ctx.save();
  ctx.globalAlpha = 1 - eic(e);
  ctx.fillStyle = '#fbf6ea';
  for (let i = 0; i < 8; i++) {
    const q = i * PI / 4 + hash(id, i), d = eoc(e) * r0 * 1.2;
    ctx.beginPath(); ctx.arc(x + Math.cos(q) * d, y + Math.sin(q) * d * .8, r0 * (.35 + .4 * (1 - e)), 0, 2 * PI); ctx.fill();
  }
  ctx.strokeStyle = '#fff'; ctx.lineWidth = 6; ctx.lineCap = 'round';
  for (let i = 0; i < 10; i++) {                       // risquinhos do estouro
    const q = i * PI / 5, a0 = r0 * (.5 + eoc(e) * 1.1), a1 = a0 + 26 * (1 - e);
    ctx.beginPath(); ctx.moveTo(x + Math.cos(q) * a0, y + Math.sin(q) * a0); ctx.lineTo(x + Math.cos(q) * a1, y + Math.sin(q) * a1); ctx.stroke();
  }
  ctx.lineCap = 'butt';
  for (let i = 0; i < 4; i++) {
    const q = -PI / 2 + (hash(id, i + 20) - .5) * 2.4, d = eoc(e) * r0 * 2.2;
    ctx.save(); ctx.translate(x + Math.cos(q) * d, y + Math.sin(q) * d + eic(e) * 90); ctx.rotate(e * 6 + i);
    aderecoForma({ tipo: 'nota', escala: .6 }, 0); ctx.restore();
  }
  ctx.restore();
}
function chuva(a, c, t) {                             // cédulas caindo do céu, de a.em até a.ate (s na cena)
  const fim = c.S + (a.ate ?? c.D), n = a.n || 26;
  for (let i = 0; i < n; i++) {
    const nasce = a.t0 + hash(a.id, i) * Math.max(.1, fim - a.t0 - .9), v = t - nasce;
    if (v < 0 || v > 2.2) continue;
    const x = CX + (hash(a.id, i + 50) * 2 - 1) * 470 + Math.sin(v * 3 + i) * 40, y = -80 + v * (520 + hash(a.id, i + 90) * 260);
    if (y > PES) continue;
    if (a.estoura_em != null && t >= c.S + a.estoura_em) { const e = (t - c.S - a.estoura_em) / .3; if (e < 1 && i % 3 === 0) puff(x, y, e, a.id + i, 28); continue; }
    ctx.save(); ctx.translate(x, y); ctx.rotate(Math.sin(v * 4 + i) * .9); ctx.scale(1, .6 + .4 * Math.abs(Math.cos(v * 5 + i)));
    aderecoForma({ ...a, tipo: 'nota' }, t); ctx.restore();
  }
}
function adereco(a, c, t) {
  if (t < a.t0 - .02) return;
  if (a.tipo === 'chuva') return chuva(a, c, t);
  const sai = c.prox ? c.prox.S : 1e9, dt = t - a.t0;
  let x = CX + (a.x || 0), y = 960 + (a.y ?? (NO_CHAO.has(a.tipo) ? PES - 960 : 0)), ang = 0;
  if (a.cai) {                                         // cai do céu, quica no chão; some_em = desce pelo alçapão
    const u = clamp(dt / .55), d2 = Math.max(0, dt - .55);
    let yy = lerp(-260, y, u * u) - Math.abs(Math.sin(d2 * PI * 3)) * 34 * Math.exp(-d2 * 6);
    if (a.estoura_em != null && t >= c.S + a.estoura_em) {
      const e = (t - c.S - a.estoura_em) / .4;
      if (e >= 1) return;
      const inch = e < .2 ? 1 + .35 * eoc(e / .2) : 0;      // incha e some no pop
      if (inch) { ctx.save(); ctx.translate(x, y); ctx.scale(inch, inch); aderecoForma(a, t); ctx.restore(); }
      puff(x, y - 70 * (a.escala || 1), clamp((e - .1) / .9), a.id, 80 * (a.escala || 1));
      return;
    }
    let desce = 0;
    if (a.some_em != null) desce += eic((t - c.S - a.some_em) / .45) * 600;
    desce += eic((t - sai + .3) / .45) * 600;
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, y + 10); ctx.clip();
    ctx.translate(x, yy + desce); ctx.rotate((1 - u) * (hash(a.id, 7) - .5) * 1.2); aderecoForma(a, t); ctx.restore();
    return;
  }
  if (a.tipo === 'pomba' && a.de && a.ate) {           // voa de um ponto a outro
    const u = eio(dt / (a.dur || 1.6));
    x = CX + lerp(a.de[0], a.ate[0], u); y = 960 + lerp(a.de[1], a.ate[1], u) + Math.sin(u * PI) * -60;
  } else if ((a.pendurado ?? NO_CEU.has(a.tipo)) && a.tipo !== 'balao') {
    const queda = -(1 - eoc(dt / .55)) * (y + 120) - eic((t - sai + .3) / .4) * (y + 200);
    const ag = 5 * DEG * Math.exp(-2.6 * Math.max(0, dt)) * Math.sin(2 * PI * 1.1 * Math.max(0, dt)) + .8 * DEG * Math.sin(2 * PI * .3 * t + a.id);
    y += queda; ang = ag;
    const topo = a.tipo === 'nuvem' ? -40 : -(a.raio || 50);
    barbante(x, 0, x + Math.sin(ang) * -topo, y + topo * Math.cos(ang));
  } else if (a.tipo !== 'balao') {                     // de chão: sobe do alçapão
    const lift = -(1 - eoc(dt / .5)) * 560 - eic((t - sai + .3) / .45) * 600 - (a.some_em != null ? eic((t - c.S - a.some_em) / .45) * 600 : 0);
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, y + 10); ctx.clip();
    ctx.translate(x, y - lift); aderecoForma(a, t); ctx.restore();
    return;
  } else {
    y -= (1 - eoc(dt / .6)) * 140; ctx.globalAlpha = eoc(dt / .3);
    if (t > sai - .3) ctx.globalAlpha *= 1 - clamp((t - sai + .3) / .3);
  }
  ctx.save(); ctx.translate(x, y); ctx.rotate(ang); aderecoForma(a, t); ctx.restore();
  ctx.globalAlpha = 1;
}

// ---------------------------------------------------------------- holofote, cortina, plateia, grão
function holofote(t) {
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  const g = ctx.createLinearGradient(0, VAL, 0, PES + 40);
  g.addColorStop(0, 'rgba(255,246,220,.16)'); g.addColorStop(1, 'rgba(255,240,200,.05)');
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.moveTo(CX - 95, VAL - 20); ctx.lineTo(CX + 95, VAL - 20); ctx.lineTo(CX + 400, PES + 40); ctx.lineTo(CX - 400, PES + 40); ctx.closePath(); ctx.fill();
  const r = ctx.createRadialGradient(CX, PES + 10, 10, CX, PES + 10, 420);
  r.addColorStop(0, 'rgba(255,236,190,.30)'); r.addColorStop(1, 'rgba(255,236,190,0)');
  ctx.fillStyle = r; ctx.save(); ctx.translate(CX, PES + 10); ctx.scale(1, .2); ctx.translate(-CX, -PES - 10);
  ctx.beginPath(); ctx.arc(CX, PES + 10, 420, 0, 2 * PI); ctx.fill(); ctx.restore();
  ctx.fillStyle = 'rgba(255,248,230,.5)';                // poeira no facho
  for (let i = 0; i < 46; i++) {
    const v = (hash(i, 1) * 1.0 + t * (.02 + hash(i, 2) * .03)) % 1;
    const yy = lerp(VAL, PES, hash(i, 3)) - v * 300 + 150, lar = lerp(95, 400, (yy - VAL) / (PES - VAL));
    const xx = CX + (hash(i, 4) * 2 - 1) * lar * .85 + Math.sin(t * .7 + i) * 10;
    ctx.globalAlpha = .15 + .25 * Math.sin(PI * v);
    ctx.beginPath(); ctx.arc(xx, yy, 1.3 + hash(i, 5) * 1.6, 0, 2 * PI); ctx.fill();
  }
  ctx.restore();
}
function cortinas(t) {
  let w = CORT;
  w = lerp(200, CORT, eio(t / .45));                       // abre no começo
  const ult = CENAS[CENAS.length - 1];
  if (ult.cortina === 'fecha') w = lerp(w, CX + 30, eio((t - ult.S) / .65));
  for (const lado of [0, 1]) {
    ctx.save();
    if (lado) { ctx.translate(W, 0); ctx.scale(-1, 1); }
    ctx.shadowColor = 'rgba(0,0,0,.45)'; ctx.shadowBlur = 30; ctx.shadowOffsetX = 10;
    ctx.drawImage(CORTINA, 0, 0, 620, H, -10, 0, w + 10, BORDA + 20);
    ctx.restore();
  }
}
function plateia() {
  ctx.fillStyle = '#0c0806';
  for (let i = 0; i < 14; i++) {
    const x = 20 + i * 80 + hash(i, 9) * 20, y = H - 40 + hash(i, 8) * 20;
    ctx.beginPath(); ctx.arc(x, y - 50, 40, 0, 2 * PI); ctx.fill(); ctx.fillRect(x - 60, y - 20, 120, 80);
  }
}
function acabamento(t) {
  const k = Math.floor(t * 12), g = GRAO[k % 3];
  ctx.save(); ctx.globalAlpha = .07; ctx.globalCompositeOperation = 'overlay';
  const ox = -(hash(k, 1) * 256) | 0, oy = -(hash(k, 2) * 256) | 0;
  for (let y = oy; y < H; y += 256) for (let x = ox; x < W; x += 256) ctx.drawImage(g, x, y);
  ctx.restore();
  const v = ctx.createRadialGradient(CX, 900, 400, CX, 900, 1250);
  v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(10,5,2,.5)');
  ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
}

// ---------------------------------------------------------------- quadro
const frente = a => a.frente ?? (a.tipo === 'mesa' || a.tipo === 'chuva');
function conteudo(c, t) {
  c.aderecos.filter(a => NO_CEU.has(a.tipo) || a.pendurado).forEach(a => adereco(a, c, t));
}
function render(t) {
  t = clamp(t, 0, DUR - 1e-4);
  let i = 0; while (i < CENAS.length - 1 && t >= CENAS[i + 1].S - .3) i++;
  const c = CENAS[i], ant = c.ant;
  const trocando = ant && t < c.S + .35 && c.cenario !== ant.cenario;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = '#120d0a'; ctx.fillRect(0, 0, W, H);
  const cam = 1 + .022 * clamp((t - c.S) / c.D);          // câmera viva: chega perto devagar em cada cena
  ctx.translate(CX, 1000); ctx.scale(cam, cam); ctx.translate(-CX, -1000);
  // cenário: o novo desce do urdimento como um telão pintado
  if (trocando) {
    ctx.drawImage(cenario(ant.cenario), 0, 0);
    if (t < c.S) conteudo(ant, t);
    const u = eio((t - c.S + .3) / .62), y = -(1 - u) * (FUNDO + 40);
    ctx.save(); ctx.shadowColor = 'rgba(0,0,0,.5)'; ctx.shadowBlur = 30; ctx.shadowOffsetY = 18;
    ctx.drawImage(cenario(c.cenario), 0, y); ctx.restore();
    ctx.fillStyle = '#4a2e1a'; ctx.fillRect(0, y + FUNDO + 30, W, 12);   // vara do telão
  } else ctx.drawImage(cenario(c.cenario), 0, 0);
  if (!trocando || t >= c.S - .1) conteudo(c, t);
  ctx.drawImage(CHAO, 0, FUNDO);
  if (ant && t < c.S + .2) {
    ant.aderecos.filter(a => !(NO_CEU.has(a.tipo) || a.pendurado) && !frente(a)).forEach(a => adereco(a, ant, t));
    ant.bonecos.forEach(b => boneco(b, ant, t));
    ant.aderecos.filter(frente).forEach(a => adereco(a, ant, t));
  }
  c.aderecos.filter(a => !(NO_CEU.has(a.tipo) || a.pendurado) && !frente(a)).forEach(a => adereco(a, c, t));
  c.bonecos.forEach(b => boneco(b, c, t));
  c.aderecos.filter(frente).forEach(a => adereco(a, c, t));
  holofote(t);
  cortinas(t);
  if (ant) ant.placas.forEach(p => placa(p, t));
  c.placas.forEach(p => placa(p, t));
  ctx.drawImage(BAMBOLINA, 0, 0);
  if (c.plateia) plateia();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  acabamento(t);
}

window.__timelines = window.__timelines || {};
const tl = gsap.timeline({ paused: true }), est = { t: 0 };
tl.to(est, { t: DUR, duration: DUR, ease: 'none', onUpdate: () => render(est.t) }, 0);   // relógio do canvas (linear ok)
render(0);
window.__timelines['mimic'] = tl;
