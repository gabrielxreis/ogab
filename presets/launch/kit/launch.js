// Preset LAUNCH, acabamento premium: a linguagem dos filmes de lançamento de produto (fundo preto, uma ideia por cena,
// revelações longas que freiam no fim, o produto flutuando em 3D com a câmera se aproximando devagar, luz guiando o olhar).
// Ponto de partida: o /brag (latent-spaces/brag, MIT). Timeline GSAP pausada e determinística (HyperFrames renderiza
// quadro a quadro). Campos dos tipos de cena: ver gerar.py.
(async function () {
  const P = window.PLANO, W = P.w, H = P.h, VERT = H > W;
  const fam = (P.fonte || "Inter Tight");
  try { await Promise.all([document.fonts.load(`700 120px '${fam}'`), document.fonts.load(`600 120px '${fam}'`), document.fonts.load(`200 120px '${fam}'`),
    document.fonts.load(`500 40px '${fam}'`), document.fonts.load(`120px 'Instrument Serif'`), document.fonts.load(`italic 120px 'Instrument Serif'`)]); await document.fonts.ready; } catch (e) {}
  const root = document.getElementById("root"), box = document.getElementById("cenas");
  root.classList.add("letra-" + (P.letra || "apple"));   // apple | editorial | cinema
  root.style.setProperty("--cor", P.cor || "#C4A34F"); root.style.setProperty("--cor2", P.cor2 || "#F2E2B3");
  const U = Math.min(W, H) / 1080, px = v => Math.round(v * U) + "px";
  const tl = gsap.timeline({ paused: true });
  const mk = (tag, cls, pai, css) => { const e = document.createElement(tag); if (cls) e.className = cls; if (css) Object.assign(e.style, css); if (pai) pai.appendChild(e); return e; };
  const M = P.marca || {};
  // Curvas: revelação longa que freia (expo.out), movimento de câmera sem tranco (power2.inOut), nunca linear no que se vê.
  const REVELA = "expo.out", CAMERA = "power2.inOut", SAI = "power2.in";

  // "*palavra*" = degradê metálico na cor da marca; "|" = nova linha. Cada linha sobe de dentro de uma máscara.
  function titulo(pai, txt, tam, peso) {
    const el = mk("div", "titulo", pai, { fontSize: px(tam) }); if (peso) el.style.fontWeight = peso;
    const linhas = String(txt).split("|").map(ln => {
      const L = mk("span", "linha", el), dentro = mk("span", "", L);
      ln.split(/(\*[^*]+\*)/).filter(Boolean).forEach(pd => {
        const cor = /^\*.*\*$/.test(pd), s = mk("span", "p" + (cor ? " cor" : ""), dentro); s.textContent = cor ? pd.slice(1, -1) : pd;
      });
      return dentro;
    });
    return { el, linhas };
  }
  function revela(t0, linhas, dur = 1.1, passo = .12) {
    tl.fromTo(linhas, { yPercent: 115, opacity: 0, filter: "blur(6px)" }, { yPercent: 0, opacity: 1, filter: "blur(0px)", duration: dur, ease: REVELA, stagger: passo }, t0);
  }
  function linhaSuave(pai, txt, tam, cls = "sub") { const e = mk("div", cls, pai, { fontSize: px(tam) }); e.textContent = txt; return e; }
  const aparece = (els, t0, d = .9) => tl.fromTo(els, { opacity: 0, y: px(24), filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: d, ease: REVELA, stagger: .1 }, t0);

  const TIPOS = {
    // Uma frase forte, linha a linha, com a palavra-chave em degradê da marca. A câmera se aproxima devagar.
    // Frase forte, grande, uma de cada vez: "||" separa as batidas (a anterior sai subindo e desfocando antes da próxima).
    gancho(c, el, t, d) {
      if (c.olho) { const o = linhaSuave(el, c.olho, 26, "olho"); Object.assign(o.style, { position: "absolute", left: 0, right: 0, top: `calc(50% - ${(VERT ? 300 : 210) * U}px)` });
        aparece(o, t + .1); }
      const batidas = String(c.texto).split("||"), cada = d / batidas.length;
      batidas.forEach((txt, k) => {
        const T = titulo(el, txt, c.tam || (VERT ? 162 : 128));
        Object.assign(T.el.style, { position: "absolute", inset: 0, display: "flex", flexDirection: "column", justifyContent: "center" });
        const t0 = t + k * cada; revela(t0 + (k ? .05 : .2), T.linhas, 1.15, .14);
        tl.fromTo(T.el, { scale: 1 }, { scale: 1.035, duration: cada + .3, ease: "sine.inOut" }, t0);
        if (k < batidas.length - 1) tl.to(T.linhas, { yPercent: -60, opacity: 0, filter: "blur(10px)", duration: .45, ease: SAI, stagger: .05 }, t0 + cada - .45);
      });
      if (c.sub) { const s = linhaSuave(el, c.sub, 38); s.style.position = "absolute"; s.style.top = "62%"; s.style.left = 0; s.style.right = 0; aparece(s, t + d - cada + .7); }
    },
    // O produto nasce do escuro: contraluz, escala que assenta, brilho atravessando o logo; o nome e a frase em seguida.
    logo(c, el, t, d) {
      const prop = c.logoProp || M.logoProp || 1, largo = prop < .75, tam = (c.tamLogo || (largo ? 640 : 300)) * U;
      const caixa = mk("div", "logo-caixa", el, { width: tam + "px", height: (largo ? tam * prop : tam) + "px", marginBottom: px(56) });
      const luz = mk("div", "contraluz", caixa);
      tl.fromTo(luz, { opacity: 0, scale: .6 }, { opacity: 1, scale: 1, duration: 1.6, ease: "power2.out" }, t);
      const logo = c.logo || M.logo; let lg;
      if (logo) { lg = mk("img", "logo-img", caixa, { width: "100%", height: "100%" }); lg.src = logo; }
      else { lg = mk("div", "monograma", caixa, { width: "100%", height: "100%", fontSize: tam * .5 + "px" }); lg.textContent = (c.nome || M.nome || "?").trim()[0].toUpperCase(); }
      tl.fromTo(lg, { opacity: 0, scale: 1.12, filter: "blur(18px) brightness(.4)" }, { opacity: 1, scale: 1, filter: "blur(0px) brightness(1)", duration: 1.5, ease: REVELA }, t + .1);
      if (logo) {   // brilho que atravessa só o logo (máscara = a própria imagem)
        const b = mk("div", "brilho", caixa, { webkitMaskImage: `url(${logo})`, maskImage: `url(${logo})`, webkitMaskSize: "contain", maskSize: "contain",
          webkitMaskRepeat: "no-repeat", maskRepeat: "no-repeat", webkitMaskPosition: "center", maskPosition: "center" });
        tl.fromTo(b, { backgroundPosition: "120% 0" }, { backgroundPosition: "-20% 0", duration: 1.4, ease: "power2.inOut" }, t + .9);
      }
      const nome = c.nome === "" ? "" : (c.nome || (logo ? "" : M.nome || ""));
      if (nome) { const T = titulo(el, nome, c.tam || 110); revela(t + .5, T.linhas, 1.1); }
      if (c.frase) aparece(linhaSuave(el, c.frase, VERT ? 40 : 34), t + .9);
      tl.fromTo(el.children, { y: 0 }, { y: px(-16), duration: d, ease: "sine.inOut" }, t);
    },
    // O produto de verdade: painel de vidro flutuando em 3D, girando devagar enquanto a câmera chega perto; reflexo no
    // chão; uma faixa de luz passa pelo vidro; dentro, a página rola até o ponto que importa (foco).
    tela(c, el, t, d) {
      const cel = c.moldura === "celular";
      if (c.titulo) { const T = titulo(el, c.titulo, c.tam || (VERT ? 104 : 76)); Object.assign(T.el.style, { position: "absolute", left: 0, right: 0, top: px(VERT ? 250 : 70), zIndex: 5 });
        revela(t + .35, T.linhas, 1.1, .12); }
      const fw = cel ? (VERT ? 600 : 420) * U : (VERT ? 900 : 1240) * U, fh = cel ? fw * 2.06 : fw * (VERT ? 1.18 : .62);
      const palco = mk("div", "palco", el, { width: fw + "px", height: fh + "px", marginTop: c.titulo ? px(VERT ? 260 : 120) : 0, alignSelf: "center" });
      const montar = pai => {
        const pn = mk("div", "painel" + (cel ? " celular" : ""), pai, { width: fw + "px", height: fh + "px" });
        let topo = 0;
        if (!cel) { topo = 54 * U; const b = mk("div", "barra-nav", pn, { height: topo + "px" }); for (let k = 0; k < 3; k++) mk("i", "", b);
          mk("div", "url", b, { fontSize: px(20) }).textContent = c.url || M.dominio || ""; }
        const v = mk("div", "vidro", pn, cel ? {} : { top: topo + "px" }); const img = mk("img", "", v); img.src = c.imagem;
        return { pn, img, topo };
      };
      const A = montar(palco);
      const ch = mk("div", "chao", palco, { height: fh * .5 + "px" }); const B = montar(ch);
      Object.assign(B.pn.style, { position: "absolute", left: 0, top: -fh * .5 + "px" });   // o reflexo mostra a metade de baixo, espelhada
      const ref = mk("div", "reflexo-vidro", A.pn);
      const jw = cel ? fw - 24 : fw, jh = cel ? fh - 24 : fh - A.topo;
      const prop = c.proporcao || (cel ? 4.9 : 2.5), rolar = Math.max(0, jw * prop - jh);
      const focos = c.foco && c.foco.length ? c.foco : [{ y: 0, zoom: 1 }, { y: .3, zoom: 1.04 }];
      [A.img, B.img].forEach(img => {
        tl.set(img, { y: -focos[0].y * rolar, scale: focos[0].zoom || 1 }, t);
        const passo = (d - 1.2) / Math.max(1, focos.length - 1);
        focos.slice(1).forEach((f, k) => tl.to(img, { y: -f.y * rolar, scale: f.zoom || 1, duration: passo * .9, ease: CAMERA }, t + 1 + k * passo));
      });
      // Entrada: vem do escuro, de baixo e de lado, assentando devagar; depois gira e aproxima sem parar.
      tl.fromTo(palco, { opacity: 0, y: px(220), rotationX: 26, rotationY: VERT ? -18 : -24, scale: .82, filter: "blur(10px)" },
        { opacity: 1, y: 0, rotationX: 8, rotationY: VERT ? -9 : -12, scale: .94, filter: "blur(0px)", duration: 1.6, ease: REVELA }, t + .1);
      tl.to(palco, { rotationX: 2, rotationY: VERT ? 6 : 8, scale: 1.04, duration: d - 1.5, ease: CAMERA }, t + 1.5);
      tl.fromTo(ref, { backgroundPosition: "140% 0" }, { backgroundPosition: "-40% 0", duration: 1.8, ease: "power2.inOut" }, t + 1.2);
      if (c.sub) { const s = linhaSuave(el, c.sub, 34); s.style.marginTop = px(VERT ? 90 : 50); s.style.position = "relative"; s.style.zIndex = 5; aparece(s, t + 1.1); }
    },
    // Recursos, um de cada vez, grandes; o anterior apaga para 28% enquanto o próximo nasce. Sem cartões, sem emoji.
    lista(c, el, t, d) {
      if (c.olho) { const o = linhaSuave(el, c.olho, 26, "olho"); o.style.marginBottom = px(50); aparece(o, t + .1); }
      const itens = c.itens || [], cada = (d - .5) / Math.max(1, itens.length);
      itens.forEach((it, k) => {
        const T = titulo(el, typeof it === "string" ? it : it.t, c.tam || (VERT ? 140 : 110)); T.el.style.margin = "0 0 -.2em";   // mesmo respiro da quebra de linha
        const t0 = t + .2 + k * cada; revela(t0, T.linhas, 1.0, .1);
        if (k < itens.length - 1) tl.to(T.el, { opacity: .28, duration: .8, ease: "power2.inOut" }, t0 + cada * .85);
        if (it.d) { const s = linhaSuave(el, it.d, 32); s.style.marginBottom = px(18); aparece(s, t0 + .35, .7);
          if (k < itens.length - 1) tl.to(s, { opacity: .2, duration: .8 }, t0 + cada * .85); }
      });
    },
    // Um número enorme e fino contando, com a frase embaixo.
    numero(c, el, t, d) {
      const n = mk("div", "numero", el, { fontSize: px(c.tam || (VERT ? 360 : 300)) });
      const o = { v: c.de || 0 }, dec = c.decimais || 0;
      const pinta = () => { n.textContent = (c.prefixo || "") + Number(o.v).toLocaleString("pt-BR", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + (c.sufixo || ""); };
      pinta();
      tl.fromTo(n, { opacity: 0, scale: 1.08, filter: "blur(16px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 1.2, ease: REVELA }, t);
      tl.to(o, { v: c.ate, duration: Math.min(1.8, d * .75), ease: "expo.out", onUpdate: pinta }, t + .15);
      if (c.texto) { const T = titulo(el, c.texto, VERT ? 64 : 54, 500); T.el.style.marginTop = px(10); revela(t + .6, T.linhas, 1.0); }
    },
    // Fecho: a frase, o endereço e (se pedir) um botão discreto. Segura parado no fim.
    cta(c, el, t, d) {
      const logo = c.logo || M.logo;
      if (logo && c.comLogo !== false) { const prop = c.logoProp || M.logoProp || 1, lw = (prop < .75 ? 260 : 110) * U;
        const im = mk("img", "logo-img", el, { width: lw + "px", height: (prop < .75 ? lw * prop : lw) + "px", marginBottom: px(60), opacity: .9 }); im.src = logo; aparece(im, t + .1, 1); }
      if (c.texto) { const T = titulo(el, c.texto, c.tam || (VERT ? 140 : 104)); revela(t + .25, T.linhas, 1.15, .14); }
      const url = c.url || M.dominio || "";
      if (url) { const u = linhaSuave(el, url, VERT ? 44 : 38, "url-cta"); u.style.marginTop = px(44); aparece(u, t + .8); }
      if (c.botao) { const b = mk("div", "botao", el, { fontSize: px(VERT ? 36 : 30), marginTop: px(44) }); b.textContent = c.botao; aparece(b, t + 1.05); }
      if (c.aviso) { const a = linhaSuave(el, c.aviso, 26, "aviso"); a.style.position = "absolute"; a.style.bottom = px(VERT ? 150 : 70); aparece(a, t + 1.3); }
    },
  };
  TIPOS.recursos = (c, el, t, d) => TIPOS.lista({ ...c, itens: (c.itens || []).map(i => ({ t: i.t, d: i.d })) }, el, t, d);

  // Montagem: cada cena entra do escuro (dissolve, sem tranco) e sai sumindo um pouco para frente com desfoque.
  // Entre cenas, uma faixa de luz atravessa a tela quando o plano pede (luz: true).
  let t = 0;
  P.cenas.forEach((c, i) => {
    const d = c.dur || 3, el = mk("div", "cena tipo-" + (c.tipo || "gancho"), box);
    (TIPOS[c.tipo] || TIPOS.gancho)(c, el, t, d);
    tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: .6, ease: "power1.out" }, t);
    if (i < P.cenas.length - 1) tl.to(el, { opacity: 0, scale: 1.035, filter: "blur(10px)", duration: .55, ease: SAI }, t + d - .5);
    if (c.luz) tl.fromTo("#luz", { left: "-40%", opacity: 0 }, { left: "110%", opacity: 1, duration: 1.3, ease: "power2.inOut" }, t + d - .7);
    t += d;
  });
  // Fundo vivo, mas quase imperceptível: o foco respira, a névoa da marca passeia, a câmera chega perto bem devagar.
  tl.fromTo("#nevoa", { xPercent: -50, yPercent: -50, x: -W * .08 }, { x: W * .08, duration: t, ease: "sine.inOut" }, 0)
    .fromTo("#foco", { opacity: .7 }, { opacity: 1, duration: t / 2, ease: "sine.inOut", yoyo: true, repeat: 1 }, 0)
    .fromTo("#cam", { scale: 1 }, { scale: 1.025, duration: t, ease: "none" }, 0);
  tl.set({}, {}, t);
  window.__timelines = window.__timelines || {}; window.__timelines["launch"] = tl;
})();
