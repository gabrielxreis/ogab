// Preset COLAGEM: colagem dadaísta de revista, dirigida pela timeline do HyperFrames.
// Cada quadro é função pura do tempo t. Movimento quantizado em passos de 12 qps ("on twos"); peça parada "ferve"
// a 6 qps com ±1 px (mão que colou); tudo sorteado por hash com semente (nada de Math.random nem relógio).
// Ideias de técnica (slap, tira rasgada, fiapos, borda de tesoura) do 06-collage do mg-styles-15 (MIT, Vincentwei1021).
const P = window.PLANO, T = P.tema, W = P.w, H = P.h, CX = W / 2, CY = H / 2;
const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
const PI = Math.PI, DEG = PI / 180;
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
function hash(a, b = 0) { let h = (a * 374761393 + b * 668265263 + 1013904223) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); h ^= h >>> 16; return (h >>> 0) / 4294967296; }
const PASSO = 12;                                          // qps do movimento (on twos num vídeo de 24/30)
const K = t => Math.floor(t * PASSO + 1e-4);
const Q = t => K(t) / PASSO;
function jit(id, t, amp, fps) {                            // mão que colou: ±amp px, um pouco de giro
  const k = Math.floor(t * fps + 1e-4);
  return [(hash(id, k) * 2 - 1) * amp, (hash(id + 71, k) * 2 - 1) * amp, (hash(id + 913, k) * 2 - 1) * amp * .25 * DEG];
}

// ---------------------------------------------------------------- fontes e imagens
const F1 = T.fonte || 'Anton', F2 = T.fonte_pequena || 'Courier Prime';
for (const [nome, arq] of [[F1, T.fonte_arquivo], [F2, T.fonte_pequena_arquivo]]) {
  if (arq) { const f = new FontFace(nome, `url("${arq}")`); await f.load(); document.fonts.add(f); }
}
const carrega = src => new Promise((ok, erro) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => erro(new Error('imagem ' + src)); i.src = src; });
const IMG = {};
const lista = ['papel_kraft.jpg', 'papel_jornal.jpg', 'jornal_0.png', 'jornal_1.png', 'grao_0.png', 'grao_1.png', 'grao_2.png'];
P.cenas.forEach(c => (c.fotos || []).forEach(f => lista.push(f.src.replace('assets/', ''))));
await Promise.all(lista.map(async n => { IMG[n] = await carrega('assets/' + n); }));
const PAD = { jornal: ctx.createPattern(IMG['jornal_0.png'], 'repeat') };

// ---------------------------------------------------------------- cenas
const TR = 4 / PASSO;                                      // folha nova deitada em 4 passos
let ini = 0;
const CENAS = P.cenas.map((c, k) => {
  const S = ini, D = c.dur; ini += D;
  const pecas = [];
  let id = 100 * (k + 1);
  if (c.forma) pecas.push({ ...c.forma, tipo: 'forma', figura: c.forma.tipo || 'disco', t0: S + (c.forma.em || 0), id: id++ });
  (c.jornal || []).forEach((j, i) => pecas.push({ tipo: 'jornal', ...j, n: i % 2, t0: S + (j.em || 0), id: id++ }));
  (c.fotos || []).forEach(f => pecas.push({ tipo: 'foto', ...f, t0: S + (f.em || 0), id: id++ }));
  (c.rotulos || []).forEach(r => String(r.texto).split('|').forEach((linha, i, todas) => {
    const tam = r.tam || 96, entre = (r.entre || 1.38) * tam;
    pecas.push({ tipo: 'rotulo', ...r, texto: linha.trim(), y: (r.y || 0) + (i - (todas.length - 1) / 2) * entre,
      rot: (r.rot || 0) + (i % 2 ? 2.5 : 0), t0: S + (r.em || 0) + i * 3 / PASSO, id: id++ });
  }));
  return { ...c, S, D, pecas };
});
const DUR = ini;

// ---------------------------------------------------------------- slap: a peça cai na página e bate no t0
// 3 passos antes ela aparece perto da câmera (maior, sombra longa, deslocada); no passo 0 assenta. Sem overshoot.
function slap(t, t0, id) {
  const k = K(t) - Math.round(t0 * PASSO);
  if (k < -3) return null;
  if (k < 0) {
    const u = -k / 3, lado = hash(id, 5) < .5 ? -1 : 1;
    return { k, s: 1 + .34 * u * u, lift: u, dx: lado * 150 * u * u, dy: -110 * u * u, dr: lado * 7 * DEG * u };
  }
  return { k, s: 1, lift: k === 0 ? .05 : 0, dx: 0, dy: 0, dr: 0 };
}
function sombra(lift) {
  ctx.shadowColor = `rgba(34,20,8,${.34 + .1 * lift})`;
  ctx.shadowBlur = 5 + lift * 34; ctx.shadowOffsetX = 3 + lift * 22; ctx.shadowOffsetY = 5 + lift * 32;
}
function semSombra() { ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0; ctx.shadowOffsetX = 0; ctx.shadowOffsetY = 0; }
function pose(p, st, t) {                                   // posição + tremida de mão (12 qps no ar, 6 qps parada)
  const mexendo = st.k <= 0;
  const [jx, jy, jr] = jit(p.id, t, mexendo ? 2 : 1.1, mexendo ? 12 : 6);
  ctx.translate(CX + (p.x || 0) + st.dx + jx, CY + (p.y || 0) + st.dy + jy);
  ctx.rotate((p.rot || 0) * DEG + st.dr + jr);
  ctx.scale(st.s, st.s);
}

// fiapos de papel e pontinhos que saltam da batida por 2 passos
function fiapos(p, st, raioX, raioY) {
  if (st.k < 0 || st.k > 1) return;
  ctx.save(); semSombra(); ctx.lineCap = 'round';
  for (let i = 0; i < 9; i++) {
    const a = hash(p.id, i + 40) * 2 * PI, d = (14 + hash(p.id, i + 60) * 26) * (st.k + 1);
    const x = Math.cos(a) * (raioX + d), y = Math.sin(a) * (raioY + d);
    ctx.globalAlpha = st.k ? .45 : .9;
    if (i % 3 === 2) { ctx.fillStyle = T.tinta; ctx.beginPath(); ctx.arc(x, y, 2 + hash(p.id, i) * 2.5, 0, 2 * PI); ctx.fill(); }
    else {
      const L = 10 + hash(p.id, i + 80) * 14;
      ctx.strokeStyle = T.claro; ctx.lineWidth = 2.6;
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(a) * L, y + Math.sin(a) * L); ctx.stroke();
    }
  }
  ctx.restore();
}

// ---------------------------------------------------------------- formas de papel
function tira(w, h, sem, aspero = 9) {                       // tira de papel rasgada nas pontas
  ctx.beginPath(); ctx.moveTo(-w / 2, -h / 2);
  for (let i = 1; i <= 20; i++) ctx.lineTo(-w / 2 + w * i / 20, -h / 2 + (hash(sem, i) - .5) * 3);
  for (let i = 1; i <= 9; i++) ctx.lineTo(w / 2 + (hash(sem + 1, i) - .5) * aspero * 2, -h / 2 + h * i / 9);
  for (let i = 1; i <= 20; i++) ctx.lineTo(w / 2 - w * i / 20, h / 2 + (hash(sem + 2, i) - .5) * 3);
  for (let i = 1; i < 9; i++) ctx.lineTo(-w / 2 + (hash(sem + 3, i) - .5) * aspero * 2, h / 2 - h * i / 9);
  ctx.closePath();
}
function disco(r, sem) {                                     // círculo cortado à tesoura (facetas)
  ctx.beginPath();
  const n = 46;
  for (let i = 0; i < n; i++) {
    const a = i / n * 2 * PI, rr = r + (hash(sem, i) - .5) * 5;
    i ? ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr) : ctx.moveTo(Math.cos(a) * rr, Math.sin(a) * rr);
  }
  ctx.closePath();
}
const cor = c => (!c || c === 'acento') ? T.acento : c === 'tinta' ? T.tinta : c === 'claro' ? T.claro : c;

function desenhaForma(p, t) {
  const st = slap(t, p.t0, p.id); if (!st) return;
  ctx.save(); pose(p, st, t);
  sombra(st.lift); ctx.fillStyle = cor(p.cor);
  if (p.figura === 'faixa') tira(p.largura || 860, p.altura || 230, p.id, 6);
  else disco(p.raio || 320, p.id);
  ctx.fill(); semSombra();
  ctx.restore();
}

function desenhaJornal(p, t) {
  const st = slap(t, p.t0, p.id); if (!st) return;
  const img = IMG[`jornal_${p.n}.png`], e = p.escala || .8;
  ctx.save(); pose(p, st, t); ctx.scale(e, e);
  sombra(st.lift); ctx.drawImage(img, -img.width / 2, -img.height / 2); semSombra();
  ctx.restore();
}

function fita(x, y, w, rot, sem) {                          // fita crepe meio transparente
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
  ctx.globalAlpha = .82; ctx.shadowColor = 'rgba(30,18,6,.18)'; ctx.shadowBlur = 3; ctx.shadowOffsetY = 2;
  ctx.fillStyle = T.fita; tira(w, 44, sem, 5); ctx.fill();
  ctx.restore();
}

function desenhaFoto(p, t) {
  const st = slap(t, p.t0, p.id); if (!st) return;
  const img = IMG[p.src.replace('assets/', '')], e = p.escala || 1;
  ctx.save(); pose(p, st, t); ctx.scale(e, e);
  sombra(st.lift); ctx.drawImage(img, -img.width / 2, -img.height / 2); semSombra();
  const retangulo = p.recorte === 'retangulo';
  if ((p.fita ?? retangulo) && st.k >= 2) {                // a fita vem depois que a foto assentou
    fita(-img.width * .3, -img.height / 2 + 16, 170, -14 * DEG, p.id + 3);
    fita(img.width * .32, -img.height / 2 + 20, 150, 11 * DEG, p.id + 4);
  }
  if (p.credito && st.k >= 3) {                            // crédito miúdo de revista, embaixo da foto, à direita
    ctx.save(); ctx.font = `20px "${F2}"`; ctx.fillStyle = T.tinta; ctx.globalAlpha = .8;
    ctx.translate(img.width / 2 - 20, img.height / 2 + 2); ctx.textAlign = 'right'; ctx.textBaseline = 'top';
    ctx.fillText(String(p.credito).toUpperCase(), 0, 0);
    ctx.restore();
  }
  fiapos(p, st, img.width * .42, img.height * .42);
  ctx.restore();
}

function medeRotulo(p) {
  let tam = p.tam || 96;
  ctx.font = `${tam}px "${F1}"`;
  let m = ctx.measureText(p.texto), larg = m.width + tam * .64;
  const max = (P.segura[2] - P.segura[0]) - 30;
  if (larg > max) { tam *= max / larg; ctx.font = `${tam}px "${F1}"`; m = ctx.measureText(p.texto); larg = m.width + tam * .64; }
  const asc = m.actualBoundingBoxAscent, desc = m.actualBoundingBoxDescent;
  return { tam, larg, alt: asc + desc + tam * .42, base: (asc - desc) / 2 };
}
function desenhaRotulo(p, t) {
  const st = slap(t, p.t0, p.id); if (!st) return;
  const r = medeRotulo(p), est = p.estilo || 'tinta';
  const fundo = est === 'acento' ? T.acento : est === 'papel' ? T.claro : est === 'jornal' ? PAD.jornal : T.tinta;
  const letra = (est === 'papel' || est === 'jornal') ? T.tinta : T.claro;
  ctx.save(); pose(p, st, t);
  sombra(st.lift); ctx.fillStyle = T.claro; tira(r.larg + 18, r.alt + 18, p.id, 10); ctx.fill(); semSombra();   // beira branca
  ctx.fillStyle = fundo; tira(r.larg, r.alt, p.id + 9, 8); ctx.fill();
  ctx.font = `${r.tam}px "${F1}"`; ctx.fillStyle = letra; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
  ctx.fillText(p.texto, 0, r.base);
  fiapos(p, st, r.larg * .5, r.alt * .5);
  ctx.restore();
}

const DESENHA = { forma: desenhaForma, jornal: desenhaJornal, foto: desenhaFoto, rotulo: desenhaRotulo };

function papel(c) { return IMG[c.papel === 'jornal' ? 'papel_jornal.jpg' : 'papel_kraft.jpg']; }

function cena(c, t) {
  // câmera de mesa de animação: aproxima 2,5% na cena, em degraus de 6 qps
  const u = clamp((Math.floor(t * 6 + 1e-4) / 6 - c.S) / c.D), z = 1 + .025 * u;
  ctx.save(); ctx.translate(CX, CY); ctx.scale(z, z); ctx.translate(-CX, -CY);
  ctx.drawImage(papel(c), 0, 0, W, H);
  for (const p of c.pecas) DESENHA[p.tipo](p, t);
  ctx.restore();
}

// folha nova deitada por cima, entrando pela direita em 4 passos, borda rasgada e sombra
function folha(c, t) {
  const k = K(t) - Math.round(c.S * PASSO);                // -4..-1
  if (k < -4 || k >= 0) return;
  const x = W * (-k) / 5 + 20;
  ctx.save(); ctx.translate(x, 0);
  ctx.beginPath(); ctx.moveTo(0, -10);
  for (let i = 1; i <= 40; i++) ctx.lineTo((hash(c.S * 100 | 0, i) - .5) * 22, H * i / 40);
  ctx.lineTo(W + 40, H + 10); ctx.lineTo(W + 40, -10); ctx.closePath();
  ctx.shadowColor = 'rgba(30,18,6,.45)'; ctx.shadowBlur = 40; ctx.shadowOffsetX = -18;
  ctx.fillStyle = T.claro; ctx.fill(); semSombra();
  ctx.clip(); ctx.drawImage(papel(c), -x, 0, W, H);
  ctx.restore();
}

function grao(t) {
  const k = K(t), img = IMG[`grao_${k % 3}.png`];
  ctx.save(); ctx.globalAlpha = .09; ctx.globalCompositeOperation = 'overlay';
  const ox = -(hash(k, 1) * 384) | 0, oy = -(hash(k, 2) * 384) | 0;
  for (let y = oy; y < H; y += 384) for (let x = ox; x < W; x += 384) ctx.drawImage(img, x, y);
  ctx.restore();
}

function render(t) {
  t = clamp(t, 0, DUR - 1e-4);
  let i = 0; while (i < CENAS.length - 1 && t >= CENAS[i + 1].S) i++;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  cena(CENAS[i], t);
  if (CENAS[i + 1] && t >= CENAS[i + 1].S - TR) folha(CENAS[i + 1], t);
  grao(t);
}

window.__timelines = window.__timelines || {};
const tl = gsap.timeline({ paused: true }), est = { t: 0 };
tl.to(est, { t: DUR, duration: DUR, ease: 'none', onUpdate: () => render(est.t) }, 0);   // relogio do canvas (linear ok)
render(0);
window.__timelines['colagem'] = tl;
