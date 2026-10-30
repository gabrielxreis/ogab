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
  // velocidade: 1 = ritmo de filme de produto; 1.5-1.8 = música com energia (revelações e entradas mais curtas)
  const V = P.velocidade || 1, rv = s => s / V;

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
    tl.fromTo(linhas, { yPercent: 115, opacity: 0, filter: "blur(6px)" }, { yPercent: 0, opacity: 1, filter: "blur(0px)", duration: rv(dur), ease: REVELA, stagger: rv(passo) }, t0);
  }
  function linhaSuave(pai, txt, tam, cls = "sub") { const e = mk("div", cls, pai, { fontSize: px(tam) }); e.textContent = txt; return e; }
  const aparece = (els, t0, d = .9) => tl.fromTo(els, { opacity: 0, y: px(24), filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: rv(d), ease: REVELA, stagger: rv(.1) }, t0);

  const TIPOS = {
    // Uma frase forte, linha a linha, com a palavra-chave em degradê da marca. A câmera se aproxima devagar.
    // Frase forte, grande, uma de cada vez: "||" separa as batidas (a anterior sai subindo e desfocando antes da próxima).
    gancho(c, el, t, d) {
      if (c.olho) { const o = linhaSuave(el, c.olho, c.tamOlho || (VERT ? 40 : 26), "olho"); Object.assign(o.style, { position: "absolute", left: 0, right: 0, top: `calc(50% - ${(VERT ? 340 : 210) * U}px)` });
        aparece(o, t + .1); }
      const batidas = String(c.texto).split("||"), cada = d / batidas.length;
      batidas.forEach((txt, k) => {
        const T = titulo(el, txt, c.tam || (VERT ? 162 : 128));
        Object.assign(T.el.style, { position: "absolute", inset: 0, display: "flex", flexDirection: "column", justifyContent: "center" });
        const t0 = t + k * cada, abre = t === 0 && !k;   // 1º quadro do vídeo: o texto já sobe, sem espera
        revela(t0 + (k ? .05 : abre ? 0 : .2), T.linhas, abre ? .8 : 1.15, .14);
        tl.fromTo(T.el, { scale: 1 }, { scale: 1.035, duration: cada + .3, ease: "sine.inOut" }, t0);
        if (k < batidas.length - 1) {
          tl.to(T.linhas, { yPercent: -60, opacity: 0, filter: "blur(10px)", duration: rv(.45), ease: SAI, stagger: .05 }, t0 + cada - rv(.45));
          // a palavra em destaque (background-clip: text) escapa da opacidade da linha no Chrome: sai por conta própria
          tl.to(T.el.querySelectorAll(".p.cor"), { opacity: 0, duration: rv(.4), ease: SAI }, t0 + cada - rv(.45));
        }
      });
      if (c.sub) { const s = linhaSuave(el, c.sub, 38); s.style.position = "absolute"; s.style.top = "62%"; s.style.left = 0; s.style.right = 0; aparece(s, t + d - cada + .7); }
    },
    // O produto nasce do escuro: contraluz, escala que assenta, brilho atravessando o logo; o nome e a frase em seguida.
    logo(c, el, t, d) {
      const prop = c.logoProp || M.logoProp || 1, largo = prop < .75, tam = (c.tamLogo || (largo ? 640 : 300)) * U;
      const caixa = mk("div", "logo-caixa", el, { width: tam + "px", height: (largo ? tam * prop : tam) + "px", marginBottom: px(56) });
      const luz = mk("div", "contraluz", caixa);
      tl.fromTo(luz, { opacity: 0, scale: .6 }, { opacity: 1, scale: 1, duration: rv(1.6), ease: "power2.out" }, t);
      const logo = c.logo || M.logo; let lg;
      if (logo) { lg = mk("img", "logo-img", caixa, { width: "100%", height: "100%" }); lg.src = logo; }
      else { lg = mk("div", "monograma", caixa, { width: "100%", height: "100%", fontSize: tam * .5 + "px" }); lg.textContent = (c.nome || M.nome || "?").trim()[0].toUpperCase(); }
      tl.fromTo(lg, { opacity: 0, scale: 1.12, filter: "blur(18px) brightness(.4)" }, { opacity: 1, scale: 1, filter: "blur(0px) brightness(1)", duration: rv(1.5), ease: REVELA }, t + .1);
      if (logo) {   // brilho que atravessa só o logo (máscara = a própria imagem)
        const b = mk("div", "brilho", caixa, { webkitMaskImage: `url(${logo})`, maskImage: `url(${logo})`, webkitMaskSize: "contain", maskSize: "contain",
          webkitMaskRepeat: "no-repeat", maskRepeat: "no-repeat", webkitMaskPosition: "center", maskPosition: "center" });
        tl.fromTo(b, { backgroundPosition: "120% 0" }, { backgroundPosition: "-20% 0", duration: 1.4, ease: "power2.inOut" }, t + .9);
      }
      const nome = c.nome === "" ? "" : (c.nome || (logo ? "" : M.nome || ""));
      if (nome) { const T = titulo(el, nome, c.tam || 110); revela(t + .5, T.linhas, 1.1); }
      // a frase fica num contêiner: a entrada (y) mexe nela, o flutuar da cena mexe no contêiner (antes as duas brigavam e ela pulava)
      if (c.frase) aparece(linhaSuave(mk("div", "", el, { width: "100%", alignSelf: "stretch" }), c.frase, c.tamFrase || (VERT ? 40 : 34)), t + .9);
      tl.fromTo(el.children, { y: 0 }, { y: px(-16), duration: d, ease: "sine.inOut" }, t);
    },
    // O produto de verdade: painel de vidro flutuando em 3D, girando devagar enquanto a câmera chega perto; reflexo no
    // chão; uma faixa de luz passa pelo vidro; dentro, a página rola até o ponto que importa (foco).
    tela(c, el, t, d) {
      const cel = c.moldura === "celular";
      if (c.titulo) { const T = titulo(el, c.titulo, c.tam || (VERT ? 104 : 76)); Object.assign(T.el.style, { position: "absolute", left: 0, right: 0, top: px(VERT ? 250 : 70), zIndex: 5 });
        revela(t + .35, T.linhas, 1.1, .12); }
      const fw = cel ? (VERT ? 600 : 330) * U : (VERT ? 900 : 1240) * U, fh = cel ? fw * 2.06 : fw * (VERT ? 1.18 : .62);
      const palco = mk("div", "palco", el, { width: fw + "px", height: fh + "px", marginTop: c.titulo ? px(VERT ? 260 : 120) : 0, alignSelf: "center" });
      const montar = (pai, espelho) => {
        const pn = mk("div", "painel" + (cel ? " celular" : ""), pai, { width: fw + "px", height: fh + "px" });
        let topo = 0;
        if (!cel) { topo = 54 * U; const b = mk("div", "barra-nav", pn, { height: topo + "px" }); for (let k = 0; k < 3; k++) mk("i", "", b);
          mk("div", "url", b, { fontSize: px(20) }).textContent = c.url || M.dominio || ""; }
        const v = mk("div", "vidro", pn, cel ? {} : { top: topo + "px" });
        // quadros: sequência de imagens que se revezam (um vídeo "tocando" no painel, seguro no 3D e no render);
        // o reflexo fica com a imagem parada
        let img;
        if (!espelho && c.quadros && c.quadros.length) {
          img = mk("div", "", v, { position: "absolute", left: 0, top: 0, width: "100%", transformOrigin: "50% 0" });
          const fq = c.fpsQuadros || 12, ini = t + (c.inicioQuadros || 0);
          c.quadros.forEach((src, k) => { const q = mk("img", "", img, { position: k ? "absolute" : "relative", left: 0, top: 0, width: "100%", opacity: k ? 0 : 1 });
            q.src = src; if (k) { tl.set(q, { opacity: 1 }, ini + k / fq); tl.set(img.children[k - 1], { opacity: 0 }, ini + k / fq); } });
        } else if (c.imagem) { img = mk("img", "", v); img.src = c.imagem; }   // sem imagem: a interface viva vem do "extra" do plano
        else img = null;
        return { pn, img, topo };
      };
      const A = montar(palco);
      const ch = mk("div", "chao", palco, { height: fh * .5 + "px" }); const B = montar(ch, true);
      Object.assign(B.pn.style, { position: "absolute", left: 0, top: -fh * .5 + "px" });   // o reflexo mostra a metade de baixo, espelhada
      const ref = mk("div", "reflexo-vidro", A.pn);
      const jw = cel ? fw - 24 : fw, jh = cel ? fh - 24 : fh - A.topo;
      const prop = c.proporcao || (cel ? 4.9 : 2.5), rolar = Math.max(0, jw * prop - jh);
      const focos = c.foco && c.foco.length ? c.foco : [{ y: 0, zoom: 1 }, { y: .3, zoom: 1.04 }];
      [A.img, B.img].filter(Boolean).forEach(img => {
        tl.set(img, { y: -focos[0].y * rolar, scale: focos[0].zoom || 1 }, t);
        const passo = (d - 1.2) / Math.max(1, focos.length - 1);
        focos.slice(1).forEach((f, k) => tl.to(img, { y: -f.y * rolar, scale: f.zoom || 1, duration: passo * .9, ease: CAMERA }, t + 1 + k * passo));
      });
      // Entrada: vem do escuro, de baixo e de lado, assentando devagar; depois gira e aproxima sem parar.
      tl.fromTo(palco, { opacity: 0, y: px(220), rotationX: 26, rotationY: VERT ? -18 : -24, scale: .82, filter: "blur(10px)" },
        { opacity: 1, y: 0, rotationX: 8, rotationY: VERT ? -9 : -12, scale: .94, filter: "blur(0px)", duration: rv(1.6), ease: REVELA }, t + .1);
      tl.to(palco, { rotationX: 2, rotationY: VERT ? 6 : 8, scale: 1.04, duration: Math.max(.3, d - rv(1.5)), ease: CAMERA }, t + rv(1.5));
      tl.fromTo(ref, { backgroundPosition: "140% 0" }, { backgroundPosition: "-40% 0", duration: 1.8, ease: "power2.inOut" }, t + 1.2);
      if (c.sub) { const s = linhaSuave(el, c.sub, 34); s.style.marginTop = px(VERT ? 90 : 50); s.style.position = "relative"; s.style.zIndex = 5; aparece(s, t + 1.1); }
    },
    // Recursos, um de cada vez, grandes; o anterior apaga para 28% enquanto o próximo nasce. Sem cartões, sem emoji.
    lista(c, el, t, d) {
      if (c.olho) { const o = linhaSuave(el, c.olho, c.tamOlho || (VERT ? 40 : 26), "olho"); o.style.marginBottom = px(50); aparece(o, t + .1); }
      const itens = c.itens || [], cada = c.cada || (d - .5) / Math.max(1, itens.length), ini = c.inicio ?? .2;   // cada/inicio: itens na batida
      itens.forEach((it, k) => {
        const T = titulo(el, typeof it === "string" ? it : it.t, c.tam || (VERT ? 140 : 110)); T.el.style.margin = "0 0 -.2em";   // mesmo respiro da quebra de linha
        const t0 = t + ini + k * cada; revela(t0, T.linhas, 1.0, .1);
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
      if (logo && c.comLogo !== false) { const prop = c.logoProp || M.logoProp || 1, lw = (c.tamLogo || (prop < .75 ? 260 : 110)) * U;
        const im = mk("img", "logo-img", el, { width: lw + "px", height: (prop < .75 ? lw * prop : lw) + "px", marginBottom: px(60), opacity: .9 }); im.src = logo; aparece(im, t + .1, 1); }
      if (c.texto) { const T = titulo(el, c.texto, c.tam || (VERT ? 140 : 104)); revela(t + .25, T.linhas, 1.15, .14); }
      const url = c.url || M.dominio || "";
      if (url) { const u = linhaSuave(el, url, VERT ? 44 : 38, "url-cta"); u.style.marginTop = px(44); aparece(u, t + .8); }
      if (c.botao) { const b = mk("div", "botao", el, { fontSize: px(VERT ? 36 : 30), marginTop: px(44) }); b.textContent = c.botao; aparece(b, t + 1.05); }
      if (c.aviso) { const a = linhaSuave(el, c.aviso, 26, "aviso"); Object.assign(a.style, { position: "absolute", left: px(60), right: px(60), textAlign: "center" }); a.style.bottom = px(VERT ? 150 : 70); aparece(a, t + 1.3); }   // largura fixa: na letra editorial vazava pela esquerda
    },
  };
  // Editor (DaVinci simulado): janela escura com visor, régua, cursor e trilhas; cada passo do plano faz um clipe entrar
  // na trilha dele (cresce a partir da esquerda, freando no fim) e troca o aviso do que o editor de IA está fazendo.
  // passos: [{ at (s na cena), trilha: "V3"|"V2"|"V1"|"ST"|"A1"|"A2"|"A3", ini, fim (0-1 da largura), rotulo, aviso }]
  TIPOS.editor = function (c, el, t, d) {
    if (c.titulo) { const T = titulo(el, c.titulo, c.tam || (VERT ? 96 : 70)); Object.assign(T.el.style, { position: "absolute", left: 0, right: 0, top: px(VERT ? 230 : 46), zIndex: 5 });
      revela(t + .3, T.linhas, 1.1, .12); }
    const fw = (VERT ? 980 : 1440) * U, fh = (VERT ? 1180 : 700) * U;
    const win = mk("div", "ed-janela", el, { width: fw + "px", height: fh + "px", marginTop: c.titulo ? px(VERT ? 220 : 110) : 0, borderRadius: px(18),
      background: "#151517", border: "1px solid rgba(255,255,255,.09)", boxShadow: `0 ${px(60)} ${px(140)} rgba(0,0,0,.7), 0 0 ${px(90)} color-mix(in srgb, var(--cor) 14%, transparent)`,
      overflow: "hidden", position: "relative", display: "flex", flexDirection: "column", fontFamily: `'${fam}', sans-serif`, color: "#c9c9cf" });
    const barra = mk("div", "", win, { height: px(40), background: "#1d1d20", borderBottom: "1px solid #2a2a2e", display: "flex", alignItems: "center", gap: px(10), padding: `0 ${px(16)}` });
    ["#ff5f57", "#febc2e", "#28c840"].forEach(cc => mk("i", "", barra, { width: px(12), height: px(12), borderRadius: "50%", background: cc, display: "block" }));
    mk("div", "", barra, { marginLeft: px(14), fontSize: px(15), color: "#8c8c94", letterSpacing: ".02em" }).textContent = c.janela || "DaVinci Resolve  ·  Edit";
    // visor
    const topo = mk("div", "", win, { flex: "0 0 44%", display: "flex", gap: px(12), padding: px(12), background: "#18181b" });
    const pool = mk("div", "", topo, { flex: "0 0 24%", background: "#1f1f23", borderRadius: px(8), padding: px(10), display: "grid", gridTemplateColumns: "1fr 1fr", gap: px(8), alignContent: "start" });
    (c.miniaturas || []).slice(0, 6).forEach((src, k) => { const m = mk("img", "", pool, { width: "100%", aspectRatio: "16/9", objectFit: "cover", borderRadius: px(4), opacity: .85 }); m.src = src;
      tl.fromTo(m, { opacity: 0, y: px(10) }, { opacity: .85, y: 0, duration: .6, ease: REVELA }, t + .4 + k * .08); });
    const visor = mk("div", "", topo, { flex: 1, background: "#0b0b0c", borderRadius: px(8), position: "relative", overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center" });
    const telas = (c.visor || []).map((src, k) => { const im = mk("img", "", visor, { position: "absolute", height: "100%", objectFit: "contain", opacity: k ? 0 : 1 }); im.src = src; return im; });
    const tc = mk("div", "", visor, { position: "absolute", right: px(12), bottom: px(10), fontSize: px(16), fontVariantNumeric: "tabular-nums", color: "#e6e6ea", background: "rgba(0,0,0,.55)", padding: `${px(3)} ${px(8)}`, borderRadius: px(4) });
    // aviso do que o editor de IA está fazendo
    const aviso = mk("div", "", el, { position: "absolute", left: "50%", top: `calc(50% + ${fh / 2 + 18 * U}px + ${c.titulo ? (VERT ? 110 : 55) * U : 0}px)`, transform: "translateX(-50%)",
      fontSize: px(c.tamAviso || 26), fontWeight: 600, color: "#eaeaee", background: "rgba(20,20,22,.9)", border: "1px solid color-mix(in srgb, var(--cor) 45%, transparent)",
      borderRadius: px(999), padding: `${px(10)} ${px(24)}`, display: "flex", alignItems: "center", gap: px(12), whiteSpace: "nowrap", zIndex: 6 });
    mk("i", "", aviso, { width: px(10), height: px(10), borderRadius: "50%", background: "var(--cor)", boxShadow: "0 0 12px var(--cor)", display: "block" });
    const avisoBox = mk("span", "", aviso, { display: "grid" });   // avisos empilhados: só um visível por vez
    const avisos = [];
    // timeline
    const tlw = mk("div", "", win, { flex: 1, display: "flex", flexDirection: "column", background: "#141416", borderTop: "1px solid #2a2a2e", position: "relative" });
    const regua = mk("div", "", tlw, { height: px(26), marginLeft: px(150), borderBottom: "1px solid #2a2a2e",
      background: `repeating-linear-gradient(90deg, #3a3a40 0 1px, transparent 1px ${px(60)})` });
    const TR = [["V3", "Motion"], ["V2", "B-roll"], ["V1", "Video"], ["ST", "Captions"], ["A1", "Voice"], ["A2", "Music"], ["A3", "SFX"]];
    const COR = { V3: "#8a4fb0", V2: "#2f7aa0", V1: "#3a67a8", ST: "#b08a35", A1: "#3c8f5a", A2: "#4c8f36", A3: "#2f8f7a" };
    const lanes = {};
    TR.forEach(([id, nome]) => {
      const row = mk("div", "", tlw, { flex: 1, display: "flex", borderBottom: "1px solid #1f1f23" });
      const cab = mk("div", "", row, { flex: `0 0 ${px(150)}`, background: "#1b1b1e", display: "flex", alignItems: "center", gap: px(10), padding: `0 ${px(12)}`, fontSize: px(15), borderRight: "1px solid #2a2a2e" });
      mk("b", "", cab, { color: "#e2e2e6", fontWeight: 700, width: px(30) }).textContent = id; mk("span", "", cab, { color: "#8c8c94" }).textContent = nome;
      lanes[id] = mk("div", "", row, { flex: 1, position: "relative" });
    });
    const cursor = mk("div", "", tlw, { position: "absolute", top: 0, bottom: 0, left: px(150), width: px(2), background: "#ff4d3d", boxShadow: "0 0 10px rgba(255,77,61,.6)", zIndex: 4 });
    const laneW = fw - 150 * U;
    tl.fromTo(cursor, { x: 0 }, { x: laneW * .92, duration: d - .4, ease: "sine.inOut" }, t + .3);
    const fps = 24, total = d * fps;
    tl.to({ f: 0 }, { f: total, duration: d, ease: "none", onUpdate() { const f = Math.round(this.targets()[0].f), s = Math.floor(f / fps);
      tc.textContent = `01:00:${String(s).padStart(2, "0")}:${String(f % fps).padStart(2, "0")}`; } }, t);
    // entrada da janela
    tl.fromTo(win, { opacity: 0, y: px(140), rotationX: 18, scale: .9, filter: "blur(10px)" }, { opacity: 1, y: 0, rotationX: 4, scale: .97, filter: "blur(0px)", duration: rv(1.4), ease: REVELA }, t + .05);
    tl.to(win, { rotationX: 0, scale: 1.01, duration: d - 1.4, ease: CAMERA }, t + 1.4);
    // passos
    let telaAtual = 0;
    (c.passos || []).forEach((s, k) => {
      const at = t + (s.at ?? (.9 + k * .55));
      if (s.aviso) { const a = mk("span", "", avisoBox, { gridArea: "1 / 1", opacity: 0 }); a.textContent = s.aviso;
        if (avisos.length) tl.to(avisos[avisos.length - 1], { opacity: 0, y: px(-8), duration: .25, ease: SAI }, at - .05);
        tl.fromTo(a, { opacity: 0, y: px(8) }, { opacity: 1, y: 0, duration: .35, ease: REVELA }, at + .15); avisos.push(a); }
      if (s.visor != null && telas[s.visor] && s.visor !== telaAtual) { tl.to(telas[telaAtual], { opacity: 0, duration: .4 }, at + .1).to(telas[s.visor], { opacity: 1, duration: .4 }, at + .1); telaAtual = s.visor; }
      if (!s.trilha) return;   // passo só de aviso (ex.: "Timeline ready")
      const lane = lanes[s.trilha] || lanes.V1, audio = /^A/.test(s.trilha), leg = s.trilha === "ST";
      const clip = mk("div", "", lane, { position: "absolute", top: "12%", bottom: "12%", left: (s.ini || 0) * 100 + "%", width: ((s.fim || 1) - (s.ini || 0)) * 100 + "%",
        background: COR[s.trilha] || COR.V1, borderRadius: px(4), overflow: "hidden", transformOrigin: "left center", fontSize: px(13), color: "rgba(255,255,255,.92)",
        padding: `0 ${px(8)}`, display: "flex", alignItems: "center", whiteSpace: "nowrap", boxShadow: "inset 0 0 0 1px rgba(255,255,255,.14)" });
      if (audio) clip.style.backgroundImage = "repeating-linear-gradient(90deg, rgba(255,255,255,.28) 0 2px, transparent 2px 5px)";
      if (leg) { clip.style.background = "transparent"; clip.style.boxShadow = "none"; clip.style.gap = px(4); clip.style.padding = "0";
        for (let q = 0; q < 6; q++) mk("i", "", clip, { flex: 1, height: "100%", background: COR.ST, borderRadius: px(3), display: "block" }); }
      else clip.textContent = s.rotulo || "";
      tl.fromTo(clip, { scaleX: 0, opacity: 0 }, { scaleX: 1, opacity: 1, duration: .7, ease: REVELA }, at);
    });
    tl.fromTo(aviso, { opacity: 0, y: px(16) }, { opacity: 1, y: 0, duration: .6, ease: REVELA }, t + .8);
  };
  TIPOS.recursos = (c, el, t, d) => TIPOS.lista({ ...c, itens: (c.itens || []).map(i => ({ t: i.t, d: i.d })) }, el, t, d);

  // Flutuantes: cartões (quadros de motions, telas) em volta da frase, nunca no centro; entram em profundidade,
  // derivam devagar em direções opostas (paralaxe) e saem junto com a cena. Posições fixas (sem acaso: render igual).
  function flutuar(c, el, t, d) {
    const camada = mk("div", "", el, { position: "absolute", inset: 0, zIndex: 0, pointerEvents: "none" });
    const POS = VERT ? [[.12,.1],[.82,.14],[.08,.82],[.86,.8],[.5,.06],[.5,.92],[.15,.46],[.85,.5]]
                     : [[.09,.2],[.9,.24],[.12,.8],[.88,.78],[.27,.1],[.73,.9],[.03,.5],[.97,.52],[.3,.88],[.7,.12]];
    c.flutuantes.slice(0, POS.length).forEach((src, k) => {
      const [x, y] = POS[k], larg = (VERT ? 200 : 190 + (k % 3) * 40) * U, prof = .55 + (k % 3) * .2;
      const im = mk("img", "", camada, { position: "absolute", left: `calc(${x * 100}% - ${larg / 2}px)`, top: `calc(${y * 100}% - ${larg * .9}px)`,
        width: larg + "px", borderRadius: px(14), boxShadow: `0 ${px(30)} ${px(60)} rgba(0,0,0,.6)`, opacity: 0,
        filter: `brightness(.8) blur(${(1 - prof) * 3}px)`, transform: `rotate(${(k % 2 ? 1 : -1) * (3 + k % 4)}deg)` });
      im.src = src;
      const dir = k % 2 ? 1 : -1;
      tl.fromTo(im, { opacity: 0, scale: .7, z: 0 }, { opacity: .25 + prof * .35, scale: 1, duration: rv(1.1), ease: REVELA }, t + .05 + k * .04);
      tl.fromTo(im, { x: 0, y: 0 }, { x: dir * 40 * U * prof, y: -dir * 30 * U * prof, duration: d, ease: "sine.inOut" }, t);
    });
  }

  // Montagem: cada cena entra do escuro (dissolve, sem tranco) e sai sumindo um pouco para frente com desfoque.
  // Entre cenas, uma faixa de luz atravessa a tela quando o plano pede (luz: true).
  let t = 0; const INFO = [];
  P.cenas.forEach((c, i) => {
    const d = c.dur || 3, el = mk("div", "cena tipo-" + (c.tipo || "gancho"), box);
    if (c.flutuantes && c.flutuantes.length) flutuar(c, el, t, d);   // imagens nas bordas, atrás do texto
    (TIPOS[c.tipo] || TIPOS.gancho)(c, el, t, d); INFO.push({ c, el, t, d, i });
    if (i) tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: rv(.6), ease: "power1.out" }, t);
    else tl.set(el, { opacity: 1 }, 0);   // a 1ª cena já está acesa no quadro 0 (o CSS esconde as cenas)
    if (i < P.cenas.length - 1) tl.to(el, { opacity: 0, scale: 1.035, filter: "blur(10px)", duration: rv(.55), ease: SAI }, t + d - rv(.5));
    if (c.luz) tl.fromTo("#luz", { left: "-40%", opacity: 0 }, { left: "110%", opacity: 1, duration: 1.3, ease: "power2.inOut" }, t + d - .7);
    t += d;
  });
  // Fundo vivo, mas quase imperceptível: o foco respira, a névoa da marca passeia, a câmera chega perto bem devagar.
  tl.fromTo("#nevoa", { xPercent: -50, yPercent: -50, x: -W * .08 }, { x: W * .08, duration: t, ease: "sine.inOut" }, 0)
    .fromTo("#foco", { opacity: 1 }, { opacity: .8, duration: t / 2, ease: "sine.inOut", yoyo: true, repeat: 1 }, 0)   // cheio no quadro 0: motion nunca começa do preto
    .fromTo("#cam", { scale: 1 }, { scale: 1.025, duration: t, ease: "none" }, 0);
  // Pegada da música: um pulso curto das cenas em cada compasso (batida: { bpm, inicio, cada (batidas), forca }).
  if (P.batida && P.batida.bpm) {
    const B = P.batida, passo = 60 / B.bpm * (B.cada || 4), f = B.forca || .012;
    for (let x = B.inicio || 0; x < t - .2; x += passo) tl.fromTo("#cenas", { scale: 1 + f }, { scale: 1, duration: Math.min(.45, passo * .8), ease: "power3.out" }, x);
  }
  // Camada do projeto ("extra" no plano: BG animado, interfaces vivas, elementos por cena) entra na MESMA timeline.
  if (window.LAUNCH_EXTRA) await window.LAUNCH_EXTRA({ tl, P, W, H, U, VERT, px, mk, titulo, revela, aparece, cenas: INFO, total: t, REVELA, CAMERA, SAI });
  tl.set({}, {}, t);
  window.__timelines = window.__timelines || {}; window.__timelines["launch"] = tl;
})();
