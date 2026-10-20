// Preset GRAVURA (gravura em cobre que se grava sozinha), vertical, dirigido pela timeline do HyperFrames.
// Motor de traço: kit/engine/ (lemo-opuscar, estilo "Copperplate Engraving", MIT, LemoLab). Este arquivo só monta as
// cenas do plano (window.GRAVURA, escrito pelo gerar.py) e desenha o quadro do tempo t, sempre determinístico.
import { B, engraveShape, Wash, drawSheet, engraveText, writeScript, borderInk, fitLines, PAL } from './engine/index.js';

const G = window.GRAVURA, W = G.w, H = G.h;
const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
const PLATE = [56, 56, W - 56, H - 56], BORDER = [88, 88, W - 88, H - 88];
const CX = W / 2, CY = G.centro_y || H * 0.47;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const seg = (t, a, b) => clamp((t - a) / (b - a));
const eio = t => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const LUZ = [-0.6, -0.7];   // uma luz só no filme inteiro, de cima à esquerda

await Promise.all(['600 40px "Bodoni Moda"', 'italic 400 40px "Bodoni Moda"', '400 40px "Pinyon Script"'].map(f => document.fonts.load(f)));

// ---------------------------------------------------------------- cenas
let ini = 0;
const CENAS = G.cenas.map((c, k) => {
  const S = ini, D = c.dur; ini += D;
  // cabe a figura numa caixa (largura e altura máximas), centrada em (CX, CY)
  const caixa = [W * (c.largura || .62), H * (c.altura || .36)];
  const partes = c.partes.map(p => ({ ...p, sh0: B.shape(p.d, B.xf(0, 0, 1)) }));
  const todos = partes.flatMap(p => p.sh0.polys), bb = B.bboxOf(todos);
  const s = Math.min(caixa[0] / (bb[2] - bb[0]), caixa[1] / (bb[3] - bb[1]));
  const ox = CX - (bb[0] + bb[2]) / 2 * s, oy = CY - (bb[1] + bb[3]) / 2 * s;
  const esp = Math.max(3.2, (bb[3] - bb[1]) * s / 150);    // espaçamento da hachura relativo à figura (STYLE §2)
  const ink = new B.Ink(), wash = new Wash({ scale: 1.5 }), grupos = { ol: [], h1: [], h2: [], h3: [] };
  partes.forEach((p, i) => {
    const r = engraveShape(p.d, { at: B.xf(ox, oy, s), light: LUZ, spacing: esp * (p.fino ? .85 : 1), style: p.estilo || 'contour',
      wMax: 2.0, outlineW: 2.0, ink, g: `p${i}`, seed: 3 + i * 7 });
    for (const f of ['ol', 'h1', 'h2', 'h3']) grupos[f].push(`p${i}${f}`);
    if (p.cor) {
      const b2 = B.bboxOf(r.shape.polys);
      wash.add({ path: r.shape.path, polys: r.shape.polys, color: p.cor, origin: [(b2[0] + b2[2]) / 2, b2[1] + (b2[3] - b2[1]) * .3],
        t0: S + D * .66 + i * .15, dur: 1.2, alpha: .8, seed: 11 + i });
    }
  });
  // ordem do buril: contorno -> 1ª hachura varrendo a forma -> cruzamento -> escuros (STYLE §5)
  // o contorno começa antes da cena: na 1ª já há traço cortado no quadro 0 (gancho nunca vazio, STYLE §5) e nas
  // outras ele vai sendo cortado enquanto a folha nova é deitada por cima
  ink.schedule(grupos.ol, k === 0 ? -.9 : S - .55, S + D * .34, { conc: 3 });
  ink.schedule(grupos.h1, S + D * .24, S + D * .52, { conc: 60 });
  ink.schedule(grupos.h2, S + D * .40, S + D * .62, { conc: 60 });
  ink.schedule(grupos.h3, S + D * .50, S + D * .70, { conc: 80 });
  ink.build();
  return { ...c, S, D, ink, wash };
});
const DUR = ini;

const borda = new B.Ink(); borderInk(borda, BORDER); borda.schedule('main', -.6, 1.0, { conc: 1.2 }); borda.build();

// textos: título em romanas gravadas letra a letra, linha pequena espaçada, nota em script escrita num traço só
function textos(c, t) {
  const p0 = c.S + (c === CENAS[0] ? .15 : c.D * .12);
  if (c.kicker) engraveText(ctx, c.kicker.toUpperCase(), CX, 250, { size: 30, weight: 500, track: .3, p: seg(t, p0 - .3, p0 + .5), color: PAL.inkSoft });
  if (c.titulo) {
    const { lines, size } = fitLines(ctx, c.titulo.toUpperCase(), W - 260, { size: 70, minSize: 50, weight: 600, track: .1 });
    lines.forEach((l, i) => engraveText(ctx, l, CX, 340 + i * size * 1.18, { size, weight: 600, track: .1, p: seg(t, p0 + i * .35, p0 + .9 + i * .35) }));
  }
  if (c.nota) {
    const yN = H - 420, n0 = c.S + c.D * .28;
    const { lines } = fitLines(ctx, c.nota, W - 280, { size: 62, minSize: 48, font: 'Pinyon Script', weight: 400 });
    lines.forEach((l, i) => writeScript(ctx, l, CX, yN + i * 72, { size: 62, p: seg(t, n0 + i * .7, n0 + .9 + i * .7) }));
  }
  if (c.credito) engraveText(ctx, c.credito, CX, H - 150, { size: 20, italic: true, weight: 400, p: seg(t, c.S + c.D * .3, c.S + c.D * .3 + 1), color: PAL.inkSoft });
}

function folha(c, t) {
  ctx.save();
  // câmera = lupa sobre a folha: respiro de até 2% centrado na figura (STYLE §6)
  const z = 1 + .02 * eio(seg(t, c.S, c.S + c.D));
  ctx.translate(CX, CY); ctx.scale(z, z); ctx.translate(-CX, -CY);
  drawSheet(ctx, { W, H, plate: PLATE });
  borda.draw(ctx, CENAS[0] === c ? t : Infinity);
  c.wash.draw(ctx, t);       // aquarela por baixo da tinta
  c.ink.draw(ctx, t);
  textos(c, t);
  ctx.restore();
}

function render(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  let k = CENAS.findIndex(c => t < c.S + c.D); if (k < 0) k = CENAS.length - 1;
  folha(CENAS[k], t);
  // transição do próprio meio: a folha seguinte é deitada por cima, subindo da base, com sombra (nada de fade)
  const prox = CENAS[k + 1], T = .7;
  if (prox && t > prox.S - T) {
    const u = eio(seg(t, prox.S - T, prox.S)), y = (1 - u) * H;
    ctx.save(); ctx.shadowColor = 'rgba(40,25,10,.45)'; ctx.shadowBlur = 60; ctx.shadowOffsetY = -18;
    ctx.fillStyle = PAL.paper; ctx.fillRect(0, y, W, H); ctx.restore();
    ctx.save(); ctx.beginPath(); ctx.rect(0, y, W, H); ctx.clip(); ctx.translate(0, y); folha(prox, t); ctx.restore();
  }
}

const tl = gsap.timeline({ paused: true }), est = { t: 0 };
tl.to(est, { t: DUR, duration: DUR, ease: 'none', onUpdate: () => render(est.t) }, 0);   // relogio do canvas (linear ok)
render(0);
window.__timelines['gravura'] = tl;
