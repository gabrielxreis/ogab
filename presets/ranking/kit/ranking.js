// Preset RANKING: quadro de ranking que se monta conforme a fala. Forma "tier" (faixas S, A, B, C, D) ou "top3"
// (pódio revelado do 3º ao 1º). Cada item entra no instante "em" (segundos da fala), cresce no centro (destaque)
// e voa em arco até a vaga dele, onde fica. Tudo é calculado por tempo (função desenha), então o render é igual
// em qualquer ordem de quadros. Campos: ver gerar.py.
(async function () {
  const P = window.PLANO, W = P.w, H = P.h, dur = P.dur;
  const bebas = P.letra === "bebas";
  const FAM = bebas ? "'Bebas Neue'" : "'Inter Tight'", PESO = bebas ? 400 : 700, PESO_ROT = bebas ? 400 : 800;
  try { await Promise.all([document.fonts.load("700 80px 'Inter Tight'"), document.fonts.load("800 80px 'Inter Tight'"),
    document.fonts.load("80px 'Bebas Neue'")]); await document.fonts.ready; } catch (e) {}
  const root = document.getElementById("root"), cam = document.getElementById("cam"), quadro = document.getElementById("quadro"),
    voo = document.getElementById("voo"), spot = document.getElementById("spot");
  const COR = P.cor || "#C4A34F";
  root.style.setProperty("--cor", COR);
  root.classList.add("letra-" + (bebas ? "bebas" : "inter"));
  if (P.fundo === "transparente") { root.classList.add("transparente"); document.documentElement.classList.add("transparente"); }

  // Grade de base 1080x1920, centrada no quadro real.
  const S = Math.min(W / 1080, H / 1920), X = v => W / 2 + (v - 540) * S, Y = v => H / 2 + (v - 960) * S, L = v => v * S;
  const mk = (tag, cls, pai, css) => { const e = document.createElement(tag); if (cls) e.className = cls; if (css) Object.assign(e.style, css); if (pai) pai.appendChild(e); return e; };

  // Curvas (nada linear no que se vê; "assenta" passa um pouco do ponto e volta).
  const cl = v => Math.max(0, Math.min(1, v)), lerp = (a, b, p) => a + (b - a) * p;
  const expoOut = p => p >= 1 ? 1 : 1 - Math.pow(2, -10 * p);
  const p2Out = p => 1 - (1 - p) * (1 - p), p3Out = p => 1 - Math.pow(1 - p, 3);
  const p3InOut = p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
  const assenta = p => { const s = 1.25, q = p - 1; return q * q * ((s + 1) * q + s) + 1; };
  const vooEase = p => p3InOut(p) + .07 * Math.sin(Math.PI * cl((p - .62) / .38));
  const seg = (t, t0, d, e) => e(cl((t - t0) / d));

  // Cores derivadas da cor da marca (ou as do plano).
  const hex = c => { c = c.replace("#", ""); if (c.length === 3) c = c.replace(/./g, "$&$&"); return [0, 2, 4].map(i => parseInt(c.substr(i, 2), 16)); };
  const mistura = (a, b, k) => { const A = hex(a), B = hex(b); return "#" + A.map((v, i) => Math.round(v * k + B[i] * (1 - k)).toString(16).padStart(2, "0")).join(""); };
  const claro = c => { const [r, g, b] = hex(c).map(v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }); return .2126 * r + .7152 * g + .0722 * b > .32; };

  // Texto que cabe: maior tamanho com até N linhas dentro da caixa.
  const med = document.createElement("canvas").getContext("2d");
  function ajusta(txt, fam, peso, maxW, maxH, maxLin, lh, maxS) {
    txt = bebas ? String(txt).toUpperCase() : String(txt);
    const pal = txt.split(/\s+/).filter(Boolean);
    for (let s = Math.floor(maxS || maxH); s >= 8; s -= 1) {
      med.font = `${peso} ${s}px ${fam}`;
      const larg = w => med.measureText(w).width * 1.05;
      if (pal.some(w => larg(w) > maxW)) continue;
      const lin = []; let at = "";
      pal.forEach(w => { const n = at ? at + " " + w : w; if (larg(n) <= maxW) at = n; else { lin.push(at); at = w; } });
      if (at) lin.push(at);
      if (lin.length <= maxLin && lin.length * s * lh <= maxH) return { s, lin };
    }
    return { s: 8, lin: [txt] };
  }
  const escreve = (el, r) => { el.innerHTML = ""; r.lin.forEach((l, i) => { if (i) el.appendChild(document.createElement("br")); el.appendChild(document.createTextNode(l)); }); el.style.fontSize = r.s + "px"; };

  const anima = [];   // funções (t) => void, chamadas a cada quadro

  // Título (linhas por máscara; "*palavra*" sai na cor da marca, "|" quebra linha).
  const temTitulo = !!String(P.titulo || "").trim();
  if (temTitulo) {
    const linhas = String(P.titulo).split("|");
    let tam = L(P.tamTitulo || (bebas ? 92 : 70));
    linhas.forEach(l => { med.font = `${PESO} ${tam}px ${FAM}`; const w = med.measureText(bebas ? l.replace(/\*/g, "").toUpperCase() : l.replace(/\*/g, "")).width * 1.04; if (w > L(900)) tam *= L(900) / w; });
    const t = mk("div", "titulo", cam, { top: Y(P.forma === "top3" ? 410 : 215) + "px", fontSize: tam + "px", fontFamily: FAM, fontWeight: PESO });
    linhas.forEach((ln, i) => {
      const box = mk("span", "linha", t), d = mk("span", "", box);
      ln.split(/(\*[^*]+\*)/).filter(Boolean).forEach(p => { const c = /^\*.*\*$/.test(p), s = mk("span", "", d); s.textContent = c ? p.slice(1, -1) : p; if (c) s.style.color = "var(--cor)"; });
      anima.push(tt => { const p = seg(tt, .08 + i * .1, 1, expoOut); d.style.transform = `translateY(${(1 - p) * 112}%)`; d.style.opacity = cl(p * 1.6); });
    });
  }

  // Itens em ordem de entrada.
  const itens = (P.itens || []).map((it, i) => Object.assign({ i }, it)).sort((a, b) => a.em - b.em);
  const vagas = [];   // {item, cx, cy, w, h (base), aoPousar(t) para o brilho do lugar}

  if (P.forma === "top3") {
    // Pódio: 2º à esquerda, 1º no meio, 3º à direita. Base em y 1380.
    const ALT = { 1: 470, 2: 360, 3: 285 }, XC = { 1: 540, 2: 540 - 292, 3: 540 + 292 }, BW = 270, CARD = 236, BASE = 1380;
    const corPos = { 1: COR, 2: mistura(COR, "#9aa0a8", .55), 3: mistura(COR, "#6d7178", .38) };
    const livres = [3, 2, 1];
    itens.forEach(it => { const n = parseInt(String(it.faixa || "").replace(/\D/g, ""), 10); it.pos = [1, 2, 3].includes(n) ? n : null; if (it.pos) livres.splice(livres.indexOf(it.pos), 1); });
    itens.forEach(it => { if (!it.pos) it.pos = livres.shift(); });
    [2, 1, 3].forEach((pos, ordem) => {
      const top = BASE - ALT[pos], b = mk("div", "bloco", quadro, { left: X(XC[pos] - BW / 2) + "px", top: Y(top) + "px", width: L(BW) + "px", height: L(ALT[pos]) + "px" });
      const luz = mk("div", "luz", b, { background: `linear-gradient(180deg, ${corPos[pos]}, ${mistura(corPos[pos], "#000000", .55)})` });
      const num = mk("div", "pos", b, { top: L(34) + "px", fontSize: L(bebas ? 170 : 150) + "px", fontFamily: FAM, fontWeight: PESO_ROT, color: "rgba(255,255,255,.16)" });
      num.textContent = pos;
      const vg = mk("div", "vaga", quadro, { left: X(XC[pos] - CARD / 2) + "px", top: Y(top - 18 - CARD) + "px", width: L(CARD) + "px", height: L(CARD) + "px", fontSize: L(120) + "px" });
      vg.textContent = "?";
      const it = itens.find(x => x.pos === pos);
      let pousa = 1e9;
      anima.push(t => {
        const p = seg(t, .15 + ordem * .12, .95, expoOut);
        b.style.transform = `scaleY(${.35 + .65 * p})`; b.style.opacity = .6 + .4 * cl(p * 3);
        const a = seg(t, pousa - .05, .55, p2Out);
        vg.style.opacity = cl(p * 2 - 1) * (1 - seg(t, pousa - .25, .3, p2Out)) * (it ? 1 : .6);
        luz.style.opacity = a;
        num.style.color = a > .5 ? (claro(corPos[pos]) ? "rgba(0,0,0,.42)" : "rgba(255,255,255,.55)") : "rgba(255,255,255,.16)";
      });
      if (it) vagas.push({ item: it, cx: XC[pos], cy: top - 18 - CARD / 2, w: CARD, h: CARD, cor: corPos[pos], defPousa: t => { pousa = t; } });
    });
  } else {
    // Tier: faixas empilhadas de y0 para baixo; rótulo colorido + trilho onde os cards assentam.
    let fx = P.faixas && P.faixas.length ? P.faixas : ["S", "A", "B", "C", "D"];
    const MIX = [1, .78, .58, .4, .25, .15, .08];
    fx = fx.map((f, i) => typeof f === "string" ? { nome: f } : Object.assign({}, f)).map((f, i) => Object.assign(f, { cor: f.cor || mistura(COR, "#2a2a30", MIX[Math.min(i, MIX.length - 1)]) }));
    const n = fx.length, GAP = 14, Y0 = temTitulo ? 380 : 330, ALT = 976, RH = Math.min(200, (ALT - GAP * (n - 1)) / n);
    const X0 = 90, LARG = 900, RW = Math.min(150, RH * .95), TL = X0 + RW + 12, TW = LARG - RW - 12;
    fx.forEach((f, i) => {
      const top = Y0 + i * (RH + GAP);
      const linha = mk("div", "faixa", quadro, { left: X(X0) + "px", top: Y(top) + "px", width: L(LARG) + "px", height: L(RH) + "px" });
      const rot = mk("div", "rotulo", linha, { width: L(RW) + "px", background: f.cor, color: claro(f.cor) ? "#111114" : "#f5f5f7",
        fontFamily: FAM, fontWeight: PESO_ROT, borderRadius: L(18) + "px" });
      escreve(rot, ajusta(f.nome, FAM, PESO_ROT, L(RW) * .78, L(RH) * (bebas ? .62 : .5), 1, 1));
      const tri = mk("div", "trilho", linha, { left: L(RW + 12) + "px", borderRadius: L(18) + "px" });
      const aceso = mk("div", "aceso", tri, { borderRadius: L(18) + "px" }); aceso.style.setProperty("--c", f.cor);
      const meus = itens.filter(it => String(it.faixa).trim().toLowerCase() === String(f.nome).trim().toLowerCase());
      const PAD = 14, GI = 12, SH = RH - 2 * PAD, SW = Math.min(SH * 1.55, (TW - 2 * PAD - GI * (meus.length - 1)) / Math.max(1, meus.length));
      const pousos = [];
      meus.forEach((it, k) => vagas.push({ item: it, cx: TL + PAD + k * (SW + GI) + SW / 2, cy: top + RH / 2, w: SW, h: SH, cor: f.cor, defPousa: t => pousos.push(t) }));
      anima.push(t => {
        const p = seg(t, .15 + i * .07, .85, expoOut);
        linha.style.opacity = .6 + .4 * cl(p * 1.4);   // o quadro já existe no quadro 0 (sem vir do preto) linha.style.transform = `translateY(${(1 - p) * L(26)}px)`;
        let a = 0; pousos.forEach(tp => { a = Math.max(a, seg(t, tp, .1, p2Out) * (1 - seg(t, tp + .1, .9, expoOut))); });
        aceso.style.opacity = a; rot.style.transform = `scale(${1 + .07 * a})`;
      });
    });
  }

  // Cards: nascem no tamanho do destaque (texto nítido) e encolhem até a vaga.
  const CX = 540, CY = P.forma === "top3" ? 830 : 880, GRANDE = 430;
  const eventos = [];   // janelas de destaque (escurecem o quadro)
  vagas.sort((a, b) => a.item.em - b.item.em).forEach((v, k, arr) => {
    const it = v.item, prox = k + 1 < arr.length ? arr[k + 1].item.em : dur, G = prox - it.em;
    const K = GRANDE / Math.max(v.w, v.h), cw = L(v.w * K), ch = L(v.h * K);
    const destaque = P.destaque !== false && G >= 1.4;
    const t0 = it.em - .05, hold = Math.max(.55, Math.min(1.3, G - 1.05)), tf = t0 + hold, VD = .85;
    const pousa = destaque ? tf + VD : t0 + .55;
    v.defPousa(pousa);
    const card = mk("div", "card" + (it.imagem ? "" : " so-texto"), voo, { width: cw + "px", height: ch + "px",
      left: X(v.cx) - cw / 2 + "px", top: Y(v.cy) - ch / 2 + "px", borderRadius: cw * .11 + "px", borderWidth: Math.max(2, cw * .008) + "px",
      background: mistura(v.cor, "#18181c", .14), borderColor: mistura(v.cor, "#2a2a30", .55) });
    if (it.imagem) mk("div", "foto", card, { backgroundImage: `url("${it.imagem}")` });
    const nome = mk("div", "nome", card, { fontFamily: FAM, fontWeight: PESO, height: it.imagem ? ch * .3 + "px" : "auto" });
    v.nome = nome; v.caixa = [cw * .84, it.imagem ? ch * .26 : ch * .42, it.imagem ? 1 : 2]; v.K = K;
    nome.style.lineHeight = 1.05;
    const dx = X(CX) - X(v.cx), dy = Y(CY) - Y(v.cy), arco = L(110);
    if (destaque) eventos.push({ t0, tf, pousa });
    anima.push(t => {
      if (t < t0) { card.style.visibility = "hidden"; return; }
      card.style.visibility = "visible";
      let x, y, s, r, o;
      if (destaque) {
        const a = seg(t, t0, .6, assenta), f = cl((t - tf) / VD), fp = p3InOut(f);
        x = dx * (1 - fp); y = dy * (1 - fp) - Math.sin(Math.PI * f) * arco;
        s = lerp(lerp(.62, 1, a) * (1 + .03 * seg(t, t0 + .5, hold, p2Out)), 1 / K, vooEase(f)); r = lerp(-3, 0, a) - Math.sin(Math.PI * f) * 4;
        o = seg(t, t0, .35, p2Out);
      } else {
        const a = seg(t, t0, .7, assenta);
        x = 0; y = (1 - a) * -L(70); s = lerp(1.22, 1, a) / K; r = 0; o = seg(t, t0, .3, p2Out);
      }
      let d = 0; eventos.forEach(e => { if (e.t0 >= pousa - .01) d = Math.max(d, dimDe(e, t)); });
      card.style.opacity = o * (1 - .68 * d);
      card.style.transform = `translate(${x}px, ${y}px) rotate(${r}deg) scale(${s})`;
    });
  });
  // Mesmo corpo de letra em todos os cards (medido no tamanho final da vaga), para o quadro ficar uniforme.
  const fin = vagas.map(v => ajusta(v.item.texto || "", FAM, PESO, v.caixa[0], v.caixa[1], v.caixa[2], 1.05).s / v.K);
  const corpo = Math.min(...fin);
  vagas.forEach(v => escreve(v.nome, ajusta(v.item.texto || "", FAM, PESO, v.caixa[0], v.caixa[1], v.caixa[2], 1.05, corpo * v.K)));
  function dimDe(e, t) { return seg(t, e.t0, .45, p2Out) * (1 - seg(t, e.tf + .25, .6, p2Out)); }

  // Quadro escurece durante cada destaque; luz da cor da marca atrás do card grande.
  const SP = L(900); Object.assign(spot.style, { width: SP + "px", height: SP + "px", left: X(CX) - SP / 2 + "px", top: Y(CY) - SP / 2 + "px" });
  anima.push(t => {
    let d = 0; eventos.forEach(e => { d = Math.max(d, dimDe(e, t)); });
    quadro.style.opacity = 1 - .68 * d; spot.style.opacity = d;
    cam.style.transform = `scale(${1.03 - .03 * Math.min(1, t / dur)})`;   // câmera contínua bem lenta
  });

  const tl = gsap.timeline({ paused: true }), relogio = { t: 0 };
  const desenha = () => anima.forEach(f => f(relogio.t));
  desenha();
  tl.to(relogio, { t: dur, duration: dur, ease: "none", onUpdate: desenha }, 0);
  tl.set({}, {}, dur);
  window.__timelines = window.__timelines || {}; window.__timelines["ranking"] = tl;
})();
