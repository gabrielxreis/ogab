// Preset KINETIC: tipografia cinética em batidas (1-3 palavras por vez), fundo preto/vermelho/branco alternando.
// Tudo numa timeline GSAP pausada (determinística: o HyperFrames renderiza quadro a quadro).
(async function () {
  try { await Promise.all([document.fonts.load('900 200px Archivo'), document.fonts.load('900 64px Inter')]); await document.fonts.ready; } catch (e) {}
  const P = window.PLANO, W = P.w, H = P.h, COR = P.cor || "#E8202A";
  const root = document.getElementById("root"), box = document.getElementById("cenas");
  root.style.setProperty("--cor", COR);
  root.style.setProperty("--brilho", P.brilho || "rgba(232,32,42,.45)");
  const tl = gsap.timeline({ paused: true });
  const LARG = W * (P.largura || 0.86);
  let t = 0;

  function ajustar(el, alvo, max) {            // fonte que ocupa a largura alvo (palavra curta fica enorme, longa encolhe)
    el.style.fontSize = "200px"; el.style.display = "inline-block"; const w = el.getBoundingClientRect().width || 1; el.style.display = "";
    el.style.fontSize = Math.min(max, 200 * alvo / w) + "px";
  }
  function linhaHTML(txt, letras) {
    let pt = "";
    if (/[.!?]$/.test(txt)) { pt = txt.slice(-1); txt = txt.slice(0, -1); }
    const corpo = letras ? [...txt].map(c => `<span class="l">${c === " " ? "&nbsp;" : c}</span>`).join("") : txt;
    return corpo + (pt ? `<span class="ponto">${pt}</span>` : "");
  }

  P.cenas.forEach((c, i) => {
    const dur = c.dur || 0.8, ent = c.entrada || "zoom";
    const el = document.createElement("div"); el.className = "cena " + (c.fundo || (["preto", "vermelho", "branco"][i % 3]));
    el.innerHTML = `<div class="fundo"></div><div class="grade"></div><div class="bloco"></div>`;
    box.appendChild(el);
    const bloco = el.querySelector(".bloco");
    const linhas = String(c.texto).split("|");
    const porLetra = ["queda", "digita", "estica"].includes(ent);
    linhas.forEach((tx, k) => {
      const d = document.createElement("div"); d.className = "linha" + ((c.destaque === k) ? " dest" : "");
      d.innerHTML = linhaHTML(tx, porLetra); bloco.appendChild(d);
      const max = linhas.length === 1 ? 900 : 480;
      ajustar(d, LARG * (c.destaque === k ? 0.92 : 1), c.destaque === k && linhas.length > 1 ? max * 0.62 : max);
    });
    const L = [...bloco.querySelectorAll(".linha")];
    if (c.tag) { const g = document.createElement("div"); g.className = "tag"; g.textContent = c.tag;
      g.style.right = "90px"; g.style.top = (P.centro_y - bloco.offsetHeight / 2 - 70) + "px"; el.appendChild(g); }
    if (c.circulo) { const r = 260; const g = document.createElement("div"); g.className = "circ";
      g.style.width = g.style.height = r * 2 + "px"; g.style.left = (W * 0.62 - r) + "px"; g.style.top = (P.centro_y - r) + "px";
      el.insertBefore(g, bloco); }

    // entra (corte seco: a batida anterior some no mesmo quadro)
    tl.set(el, { opacity: 1 }, t);
    if (i > 0) tl.set(box.children[i - 1], { opacity: 0 }, t);
    tl.fromTo(el.querySelector(".fundo"), { scale: 1.08 }, { scale: 1, duration: dur, ease: "power2.out" }, t);
    tl.fromTo(bloco, { scale: 1 }, { scale: c.zoom || 1.05, duration: dur, ease: "none" }, t);

    if (ent === "zoom") {
      tl.fromTo(L, { scale: 2.4, opacity: 0, filter: "blur(18px)" }, { scale: 1, opacity: 1, filter: "blur(0px)", duration: .22, ease: "power4.out", stagger: .06 }, t);
    } else if (ent === "blur") {
      tl.fromTo(L, { x: W * .9, skewX: -25, filter: "blur(30px)", opacity: 0 }, { x: 0, skewX: 0, filter: "blur(0px)", opacity: 1, duration: .24, ease: "expo.out", stagger: .05 }, t);
    } else if (ent === "pilha") {
      L.forEach((l, k) => tl.fromTo(l, { y: -120, opacity: 0, filter: "blur(12px)", scaleY: 1.4 }, { y: 0, opacity: 1, filter: "blur(0px)", scaleY: 1, duration: .16, ease: "back.out(2)" }, t + k * Math.min(.22, dur / (L.length + 1))));
    } else if (ent === "queda") {
      L.forEach((l, k) => tl.fromTo(l.querySelectorAll(".l"), { y: -260, rotation: () => gsap.utils.random(-25, 25, 1), opacity: 0 },
        { y: 0, rotation: 0, opacity: 1, duration: .2, ease: "back.out(2.2)", stagger: .025 }, t + k * .12));
    } else if (ent === "digita") {
      L.forEach((l, k) => { const ls = l.querySelectorAll(".l"); tl.set(ls, { opacity: 0 }, t);
        const cur = document.createElement("span"); cur.className = "cursor"; l.appendChild(cur);
        const passo = Math.min(.05, (dur * .55) / Math.max(1, ls.length));
        ls.forEach((x, j) => tl.set(x, { opacity: 1 }, t + k * ls.length * passo + j * passo));
        tl.to(cur, { opacity: 0, duration: .01, repeat: 7, yoyo: true, repeatDelay: .08 }, t + ls.length * passo); });
    } else if (ent === "estica") {
      tl.fromTo(L, { scaleX: 3.2, letterSpacing: ".3em", opacity: 0, filter: "blur(10px)" }, { scaleX: 1, letterSpacing: "-.01em", opacity: 1, filter: "blur(0px)", duration: .3, ease: "expo.out" }, t);
    } else if (ent === "glitch") {
      L.forEach(l => {
        ["#ff2a2a", "#22e0ff"].forEach((cc, j) => { const k = l.cloneNode(true); k.style.position = "absolute"; k.style.left = 0; k.style.right = 0; k.style.top = 0;
          k.style.color = cc; k.style.mixBlendMode = "screen"; k.classList.remove("dest"); l.appendChild(k);
          tl.fromTo(k, { x: j ? 22 : -22, opacity: .9 }, { x: 0, opacity: 0, duration: .26, ease: "steps(6)" }, t); });
        tl.fromTo(l, { opacity: 0, clipPath: "inset(40% 0 35% 0)" }, { opacity: 1, clipPath: "inset(0% 0 0% 0)", duration: .2, ease: "steps(4)" }, t);
        tl.fromTo(l, { x: -30 }, { x: 0, duration: .24, ease: "steps(5)" }, t); });
    }
    // impacto: tremor + flash curto
    if (c.impacto !== false) {
      tl.fromTo(bloco, { x: 0 }, { x: 10, duration: .03, yoyo: true, repeat: 3, ease: "none" }, t + .18);
      if (c.flash) tl.fromTo("#flash", { opacity: .55 }, { opacity: 0, duration: .12 }, t);
    }
    if (c.tag) tl.fromTo(el.querySelector(".tag"), { scale: 0, opacity: 0, rotation: -20 }, { scale: 1, opacity: 1, rotation: 0, duration: .14, ease: "back.out(3)" }, t + Math.min(.35, dur * .45));
    if (c.circulo) tl.fromTo(el.querySelector(".circ"), { scale: 0, opacity: 1 }, { scale: 1, duration: .35, ease: "back.out(1.6)" }, t + .08);
    // saída: chicote com desfoque nos últimos quadros (se a próxima batida pede)
    if (c.saida === "chicote") tl.to(bloco, { x: -W * .8, skewX: 20, filter: "blur(24px)", duration: .12, ease: "power3.in" }, t + dur - .12);
    t += dur;
  });
  window.__timelines = window.__timelines || {};
  window.__timelines["kinetic"] = tl;
})();
