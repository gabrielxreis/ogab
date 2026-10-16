/* Física para motions da /ogab (matter.js): objetos que caem e empilham, ou que explodem para fora.
 * A simulação roda inteira no carregamento (passo fixo de 1/60 s) e vira keyframes do GSAP, então cada quadro
 * sai igual no render (o HyperFrames pula de quadro em quadro; física "ao vivo" não funcionaria).
 *
 *   <script src="matter.min.js"></script><script src="fisica.js"></script>
 *   Fisica.cair(tl, { itens: ".peca", inicio: 1, duracao: 3.5, chao: 1500, paredes: [70, 1010] });
 *   Fisica.explodir(tl, { itens: ".peca", inicio: 6, duracao: 2, ponto: { x: 540, y: 1200 }, forca: 28 });  // some no fim (sumir:false desliga)
 *
 * Regras: cada item é position:absolute com width/height FIXOS no CSS (a medida é lida no carregamento, antes da
 * fonte chegar). `cair`: o lugar no CSS é o ponto de partida (deixe acima da tela, ex. top:-300px, cada um numa
 * altura); ele é solto em `inicio + i*atraso`. data-forma="circulo" vira círculo; o resto, retângulo com canto
 * igual ao border-radius. `explodir`: parte de onde cada item está naquele momento da timeline (use depois de
 * `cair` passando `de: resultadoDoCair`), ou do lugar no CSS.
 */
(function () {
  const M = () => window.Matter;
  const FPS = 30, PASSO = 1000 / 60;

  function lista(itens) {
    return typeof itens === "string" ? Array.from(document.querySelectorAll(itens)) : Array.from(itens);
  }
  function medida(e) {
    const cs = getComputedStyle(e);
    const w = parseFloat(cs.width) || e.offsetWidth, h = parseFloat(cs.height) || e.offsetHeight;
    const x = (parseFloat(cs.left) || e.offsetLeft) + w / 2, y = (parseFloat(cs.top) || e.offsetTop) + h / 2;
    return { w, h, x, y, raio: Math.min(parseFloat(cs.borderTopLeftRadius) || 0, w / 2, h / 2) };
  }
  function corpo(e, m, op) {
    const { Bodies } = M();
    const base = { restitution: op.quique ?? .3, friction: op.atrito ?? .4, frictionAir: op.ar ?? .01, density: .002 };
    return e.dataset.forma === "circulo"
      ? Bodies.circle(m.x, m.y, m.w / 2, base)
      : Bodies.rectangle(m.x, m.y, m.w, m.h, Object.assign({ chamfer: m.raio ? { radius: m.raio } : undefined }, base));
  }
  function mundo(op, W, H) {
    const { Engine, Bodies, Composite, Common } = M();
    Common._seed = 7;
    const eng = Engine.create({ enableSleeping: false });
    eng.gravity.y = op.gravidade ?? 1.6;
    const chao = op.chao ?? H - 120, [pe, pd] = op.paredes || [0, W];
    const est = { isStatic: true, friction: .6, restitution: .2 };
    Composite.add(eng.world, [
      Bodies.rectangle(W / 2, chao + 200, W * 3, 400, est),
      Bodies.rectangle(pe - 200, H / 2, 400, H * 6, est),
      Bodies.rectangle(pd + 200, H / 2, 400, H * 6, est),
    ]);
    return eng;
  }
  // grava a simulação em keyframes relativos ao lugar do CSS
  function gravar(tl, els, corpos, base, eng, inicio, duracao, soltar) {
    const { Engine, Body } = M();
    const quadros = Math.round(duracao * FPS), sub = Math.round(1000 / FPS / PASSO);
    const trilha = els.map(() => []);
    for (let q = 0; q <= quadros; q++) {
      const t = q / FPS;
      if (soltar) soltar(t);
      corpos.forEach((c, i) => trilha[i].push({ x: c.position.x - base[i].x, y: c.position.y - base[i].y, rotation: c.angle * 180 / Math.PI }));
      for (let s = 0; s < sub; s++) Engine.update(eng, PASSO);
    }
    els.forEach((e, i) => {
      const k = trilha[i];
      tl.set(e, k[0], inicio);
      tl.to(e, { keyframes: k.slice(1).map(v => Object.assign({ duration: 1 / FPS, ease: "none" }, v)) }, inicio);
    });
    return { els, base, ultimo: trilha.map(k => k[k.length - 1]) };
  }

  function cair(tl, op) {
    const { Composite, Body } = M();
    const raiz = document.querySelector("[data-composition-id]");
    const W = +raiz.dataset.width, H = +raiz.dataset.height;
    const els = lista(op.itens), base = els.map(medida);
    const eng = mundo(op, W, H);
    const corpos = els.map((e, i) => { const c = corpo(e, base[i], op); Body.setStatic(c, true); return c; });
    Composite.add(eng.world, corpos);
    const atraso = op.atraso ?? .12, solto = corpos.map(() => false);
    return gravar(tl, els, corpos, base, eng, op.inicio ?? 0, op.duracao ?? 3, t => {
      corpos.forEach((c, i) => {
        if (!solto[i] && t >= i * atraso) {
          solto[i] = true; Body.setStatic(c, false);
          Body.setAngularVelocity(c, ((i * 37) % 11 - 5) / 220); // giro leve, diferente em cada peça
        }
      });
    });
  }

  function explodir(tl, op) {
    const { Composite, Body } = M();
    const raiz = document.querySelector("[data-composition-id]");
    const W = +raiz.dataset.width, H = +raiz.dataset.height;
    const els = lista(op.de ? op.de.els : op.itens);
    const base = op.de ? op.de.base : els.map(medida);
    const ini = op.de ? op.de.ultimo : els.map(() => ({ x: 0, y: 0, rotation: 0 }));
    const eng = mundo(Object.assign({ chao: H * 4, paredes: [-W * 3, W * 4], gravidade: .45 }, op), W, H);
    const pt = op.ponto || { x: W / 2, y: H / 2 }, forca = op.forca ?? 26;
    const corpos = els.map((e, i) => {
      const m = Object.assign({}, base[i], { x: base[i].x + ini[i].x, y: base[i].y + ini[i].y });
      const c = corpo(e, m, op);
      Body.setAngle(c, ini[i].rotation * Math.PI / 180);
      const dx = m.x - pt.x, dy = m.y - pt.y, d = Math.hypot(dx, dy) || 1;
      const v = forca * (0.75 + ((i * 53) % 10) / 20);
      Body.setVelocity(c, { x: dx / d * v * 1.25, y: dy / d * v - forca * .12 });
      Body.setAngularVelocity(c, ((i * 29) % 13 - 6) / 40);
      return c;
    });
    Composite.add(eng.world, corpos);
    const ini0 = op.inicio ?? 0, dur = op.duracao ?? 2;
    const r = gravar(tl, els, corpos, base, eng, ini0, dur);
    if (op.sumir !== false)  // garantia: nada fica voltando por cima do texto no fim
      tl.to(els, { opacity: 0, duration: .5, ease: "power1.in" }, ini0 + dur - .5);
    return r;
  }

  window.Fisica = { cair, explodir };
})();
