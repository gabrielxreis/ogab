/* Cinema: acabamento cinematográfico para qualquer composição HyperFrames da /ogab.
 * Brilho estourado (bloom), aberração cromática e grão num filtro SVG só (vale também para MOV com alfa),
 * + vinheta e vazamento de luz como camadas por cima (só em composição com fundo opaco).
 *
 * Uso (depois do script que cria a timeline):
 *   <script src="cinema.js"></script>
 *   <script>Cinema.aplicar(window.__timelines.main, { nivel: "suave", alvo: "#push", cor: "#ff9a3c" })</script>
 * Ou pelo terminal: python3 SKILL_DIR/scripts/fx.py cinema <projeto> --nivel suave [--cor "#ff9a3c"] [--alfa]
 *
 * Determinístico: o grão troca de semente por quadro com tl.set (nada de Math.random nem requestAnimationFrame).
 */
(function () {
  const NIVEIS = {
    sutil: { bloom: .3, limiar: .8, raio: 14, aberracao: .8, grao: .05, vinheta: .22, vazamento: 0 },
    suave: { bloom: .5, limiar: .76, raio: 22, aberracao: 1.5, grao: .08, vinheta: .32, vazamento: .4 },
    forte: { bloom: .85, limiar: .66, raio: 32, aberracao: 3, grao: .13, vinheta: .48, vazamento: .7 },
  };
  const NS = "http://www.w3.org/2000/svg";
  let n = 0;

  function el(tag, at, pai) {
    const e = document.createElementNS(NS, tag);
    for (const k in at) e.setAttribute(k, at[k]);
    if (pai) pai.appendChild(e);
    return e;
  }
  function ct(pai, entrada, saida, slope, intercept, alfa) { // feComponentTransfer linear nos 3 canais
    const f = el("feComponentTransfer", { in: entrada, result: saida }, pai);
    ["R", "G", "B"].forEach(c => el("feFunc" + c, { type: "linear", slope, intercept }, f));
    if (alfa) el("feFuncA", { type: "linear", slope: alfa, intercept: 0 }, f);
    return f;
  }

  function aplicar(tl, op) {
    op = op || {};
    const p = Object.assign({}, NIVEIS[op.nivel || "suave"] || NIVEIS.suave, op);
    const raiz = document.querySelector("[data-composition-id]");
    const alvo = typeof p.alvo === "string" ? document.querySelector(p.alvo) : (p.alvo || raiz.firstElementChild);
    const W = +raiz.dataset.width || raiz.offsetWidth, H = +raiz.dataset.height || raiz.offsetHeight;
    const T = tl.duration();
    const id = "cinema" + (n++);

    // ---------- filtro: bloom -> aberração -> grão
    const svg = el("svg", { width: 0, height: 0, style: "position:absolute" });
    document.body.appendChild(svg);
    const f = el("filter", { id, x: "0", y: "0", width: "1", height: "1", "color-interpolation-filters": "sRGB" }, el("defs", {}, svg));
    let atual = "SourceGraphic";
    if (p.bloom > 0) {
      const s = 1 / Math.max(.05, 1 - p.limiar);
      ct(f, "SourceGraphic", "claro", s, -s * p.limiar);
      el("feGaussianBlur", { in: "claro", stdDeviation: p.raio, result: "halo" }, f);
      ct(f, "halo", "haloK", p.bloom, 0);
      el("feBlend", { in: "haloK", in2: "SourceGraphic", mode: "screen", result: "bloom" }, f);
      atual = "bloom";
    }
    if (p.aberracao > 0) {
      el("feColorMatrix", { in: atual, type: "matrix", values: "1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0", result: "cR" }, f);
      el("feColorMatrix", { in: atual, type: "matrix", values: "0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 1 0", result: "cG" }, f);
      el("feColorMatrix", { in: atual, type: "matrix", values: "0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 1 0", result: "cB" }, f);
      el("feOffset", { in: "cR", dx: p.aberracao, dy: 0, result: "cR2" }, f);
      el("feOffset", { in: "cB", dx: -p.aberracao, dy: 0, result: "cB2" }, f);
      el("feBlend", { in: "cR2", in2: "cG", mode: "screen", result: "cRG" }, f);
      el("feBlend", { in: "cB2", in2: "cRG", mode: "screen", result: "ab" }, f);
      atual = "ab";
    }
    let turb = null;
    if (p.grao > 0) {
      turb = el("feTurbulence", { type: "fractalNoise", baseFrequency: p.freqGrao || .9, numOctaves: 2, seed: 1, stitchTiles: "stitch", result: "ruido" }, f);
      el("feColorMatrix", { in: "ruido", type: "matrix", values: ".33 .33 .33 0 0 .33 .33 .33 0 0 .33 .33 .33 0 0 0 0 0 0 1", result: "cinza" }, f);
      const k = p.grao * 6;
      ct(f, "cinza", "cinzaK", k, .5 - k * .5);
      el("feBlend", { in: "cinzaK", in2: atual, mode: "soft-light", result: "comGrao" }, f);
      el("feComposite", { in: "comGrao", in2: atual, operator: "in", result: "fim" }, f);
      atual = "fim";
      const fps = p.fpsGrao || 24;
      for (let i = 0; i <= Math.ceil(T * fps); i++) tl.set(turb, { attr: { seed: 1 + (i * 7919) % 9973 } }, i / fps);
    }
    alvo.style.filter = `url(#${id})`;

    // ---------- camadas por cima (só com fundo opaco)
    if (!p.alfa) {
      const pai = alvo.parentElement;
      if (p.vinheta > 0) {
        const v = document.createElement("div");
        v.style.cssText = `position:absolute;inset:0;pointer-events:none;z-index:50;
          background:radial-gradient(ellipse 80% 72% at 50% 48%,rgba(0,0,0,0) 55%,rgba(0,0,0,${p.vinheta}) 100%)`;
        pai.appendChild(v);
      }
      if (p.vazamento > 0) {
        const cor = p.cor || "#ff9a3c";
        const mk = (x, y, w, h) => {
          const d = document.createElement("div");
          d.style.cssText = `position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;pointer-events:none;z-index:49;
            mix-blend-mode:screen;border-radius:50%;opacity:0;
            background:radial-gradient(ellipse at center,${cor} 0%,${cor}88 25%,${cor}00 70%)`;
          pai.appendChild(d); return d;
        };
        // nos cantos (como luz entrando pela lente), longe do rosto e do texto central
        const a = mk(W * .4, -H * .16, W * .95, H * .38), b = mk(-W * .45, H * .76, W * .95, H * .38);
        tl.fromTo(a, { x: W * .12, opacity: 0 }, { x: -W * .12, duration: T, ease: "none" }, 0);
        tl.fromTo(b, { x: -W * .1 }, { x: W * .14, duration: T, ease: "none" }, 0);
        // pulsos de luz: entrada, meio e fim
        [[a, .15], [b, T * .45], [a, T * .78]].forEach(([d, t]) => {
          tl.to(d, { opacity: p.vazamento, duration: .9, ease: "sine.out" }, t);
          tl.to(d, { opacity: p.vazamento * .25, duration: 1.6, ease: "sine.inOut" }, t + .9);
        });
      }
    }
    return { filtro: f, alvo };
  }

  window.Cinema = { aplicar, NIVEIS };
})();
