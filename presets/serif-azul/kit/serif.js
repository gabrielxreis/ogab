/* SERIF AZUL: os movimentos do preset (GSAP, linha do tempo pausada do HyperFrames, determinístico).
   Uso: S.legenda(tl, "#l1", 0.2, "Esses *três erros* / deixam sua edição amadora")
   Cada função recebe a timeline, o seletor, o tempo de entrada e opções, e devolve o tempo em que termina.
   Tempos medidos quadro a quadro na referência (2 e 12 qps): palavra a palavra na fala, entradas de 0,25-0,5 s com desfoque. */
(function () {
  const $ = (s) => (typeof s === "string" ? document.querySelector(s) : s);
  const $$ = (s) => (typeof s === "string" ? [...document.querySelectorAll(s)] : s);

  /* "Esses *três erros* / deixam sua edição" -> linhas (/) com palavras; *entre asteriscos* = serifada itálica azul;
     _entre sublinhados_ = serifada fina (linha de título no papel). */
  function monta(el, texto) {
    el.innerHTML = texto.split("/").map((linha) => {
      const partes = [];
      linha.trim().replace(/\*([^*]+)\*|_([^_]+)_|(\S+)/g, (m, sf, fina, w) => {
        if (sf) partes.push(`<span class="w sf">${sf}</span>`);
        else if (fina) fina.split(/\s+/).forEach((p) => partes.push(`<span class="w fina">${p}</span>`));
        else partes.push(`<span class="w">${w}</span>`);
      });
      return `<span class="l">${partes.join(" ")}</span>`;
    }).join("");
  }

  const S = {
    monta,

    /* 1. LEGENDA palavra a palavra: cada palavra entra com desfoque e sobe 14 px; a serifada entra maior e assenta.
       o.tempos = [t de cada palavra] (da transcrição) ou o.passo fixo (padrão 0,2 s). */
    legenda(tl, sel, t, texto, o = {}) {
      const el = $(sel);
      monta(el, texto);
      const ws = [...el.querySelectorAll(".w")];
      ws.forEach((w, i) => {
        const ti = o.tempos ? o.tempos[i] : t + i * (o.passo ?? 0.2);
        const sf = w.classList.contains("sf");
        tl.fromTo(w, { opacity: 0, y: sf ? 0 : 14, scale: sf ? 1.12 : 1, filter: `blur(${sf ? 14 : 8}px)` },
          { opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: sf ? 0.42 : 0.26, ease: "power3.out" }, ti);
      });
      tl.set(el, { opacity: 1 }, t);
      const fim = o.tempos ? o.tempos[o.tempos.length - 1] : t + (ws.length - 1) * (o.passo ?? 0.2);
      return fim + 0.42;
    },

    /* 2. Sai desfocando (legenda, cartão, cena). */
    sai(tl, sel, t, o = {}) {
      tl.to(sel, { opacity: 0, filter: `blur(${o.blur ?? 12}px)`, y: o.y ?? 0, duration: o.dur ?? 0.28, ease: "power2.in" }, t);
      return t + (o.dur ?? 0.28);
    },

    /* 3. PASSOS 1-2-3: o trilho surge e os círculos acendem em sequência (vermelho = "os erros"). */
    passos(tl, sel, t, o = {}) {
      const el = $(sel), n = o.n ?? 3;
      if (!el.dataset.s) {
        el.innerHTML = Array.from({ length: n }, (_, i) => (i ? '<span class="f"></span>' : "") + `<span class="p">${i + 1}</span>`).join("");
        el.dataset.s = 1;
      }
      tl.fromTo(el, { opacity: 0, y: 24, filter: "blur(10px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.35, ease: "power3.out" }, t);
      if (o.erro) {
        el.querySelectorAll(".p").forEach((p, i) => {
          tl.call(() => p.classList.add("erro"), null, t + 0.25 + i * 0.22);
          tl.fromTo(p, { scale: 0.7 }, { scale: 1, duration: 0.3, ease: "back.out(2.5)" }, t + 0.25 + i * 0.22);
        });
        el.querySelectorAll(".f").forEach((f, i) => tl.call(() => f.classList.add("erro"), null, t + 0.36 + i * 0.22));
      }
      return t + 0.35 + (o.erro ? n * 0.22 : 0);
    },
    /* volta todos para neutro (some o vermelho) antes de contar os passos de verdade */
    passosLimpa(tl, sel, t) {
      tl.call(() => $$(`${sel} .p, ${sel} .f`).forEach((e) => e.classList.remove("erro", "on")), null, t);
    },
    /* acende o passo k (1, 2, 3...) e a linha até ele */
    passo(tl, sel, t, k) {
      const ps = $$(`${sel} .p`), fs = $$(`${sel} .f`);
      for (let i = 0; i < k; i++) tl.call(() => ps[i].classList.add("on"), null, t);
      for (let i = 0; i < k - 1; i++) tl.call(() => fs[i].classList.add("on"), null, t);
      tl.fromTo(ps[k - 1], { scale: 0.75 }, { scale: 1, duration: 0.32, ease: "back.out(2.2)" }, t);
      return t + 0.32;
    },
    /* rótulo "Número 2" abaixo dos passos */
    rotulo(tl, sel, t, texto) {
      tl.call(() => { $(sel).textContent = texto; }, null, t);
      tl.fromTo(sel, { opacity: 0, y: 12, filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.3, ease: "power3.out" }, t);
      return t + 0.3;
    },

    /* 4. SLIDER de nível (Iniciante -> Profissional): a bolinha corre e o rótulo final acende na cor. */
    slider(tl, sel, t, o = {}) {
      const el = $(sel), dur = o.dur ?? 1.4, ate = o.ate ?? 100;
      tl.fromTo(el, { opacity: 0, y: 20, filter: "blur(10px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.3 }, t);
      tl.fromTo(el.querySelector(".bola"), { left: "0%" }, { left: `${ate}%`, duration: dur, ease: "power2.inOut" }, t + 0.3);
      tl.fromTo(el.querySelector(".cheio"), { width: "0%" }, { width: `${ate}%`, duration: dur, ease: "power2.inOut" }, t + 0.3);
      tl.to(el.querySelector(".tit span:last-child"), { color: "#6f97ff", duration: 0.2 }, t + 0.3 + dur - 0.1);
      return t + 0.3 + dur;
    },

    /* 5. PAINEL off-white entra por cima do vídeo: sobe de baixo como um cartão arredondado e encaixa na tela
       (tela cheia ou .metade de cima). Sai descendo. */
    painel(tl, sel, t, o = {}) {
      tl.fromTo(sel, { yPercent: 100, borderRadius: 60, scale: 0.92 },
        { yPercent: 0, borderRadius: 0, scale: 1, duration: o.dur ?? 0.5, ease: "power4.out" }, t);
      return t + (o.dur ?? 0.5);
    },
    painelSai(tl, sel, t, o = {}) {
      tl.to(sel, { yPercent: o.cima ? -100 : 100, borderRadius: 60, scale: 0.94, duration: o.dur ?? 0.4, ease: "power3.in" }, t);
      return t + (o.dur ?? 0.4);
    },

    /* 6. CELULAR (print do Reels, thumbnail) desce do alto inclinado, assenta e flutua devagar. */
    cartao(tl, sel, t, o = {}) {
      tl.fromTo(sel, { y: o.de ?? -900, rotation: o.giro ?? -8, opacity: 0.4, filter: "blur(10px)" },
        { y: 0, rotation: o.giroFim ?? -3, opacity: 1, filter: "blur(0px)", duration: o.dur ?? 0.6, ease: "expo.out" }, t);
      tl.to(sel, { y: -24, rotation: (o.giroFim ?? -3) + 1.5, duration: o.flutua ?? 2.4, ease: "sine.inOut" }, t + 0.6);
      return t + (o.dur ?? 0.6);
    },

    /* 7. ÍCONE 3D de app nasce pequeno e desfocado e cresce (pop). */
    icone(tl, sel, t, o = {}) {
      tl.fromTo(sel, { scale: o.de ?? 0.55, opacity: 0, filter: "blur(16px)", y: 40 },
        { scale: 1, opacity: 1, filter: "blur(0px)", y: 0, duration: o.dur ?? 0.55, ease: "back.out(1.5)" }, t);
      tl.to(sel, { scale: 1.03, duration: 1.4, ease: "sine.inOut" }, t + 0.55);
      return t + (o.dur ?? 0.55);
    },
    /* 7b. ENCOLHE com caixa tracejada, selo (-25%) e partículas saindo (regra "25% menor"). */
    encolhe(tl, sel, t, o = {}) {
      const el = $(sel), fator = o.fator ?? 0.75, caixa = $(o.caixa), selo = $(o.selo), pontos = $$(o.pontos);
      tl.to(el, { scale: fator, duration: 0.5, ease: "power3.inOut" }, t);
      if (caixa) {
        tl.fromTo(caixa, { opacity: 0, scale: 1.08 }, { opacity: 1, scale: 1, duration: 0.3 }, t);
        tl.to(caixa, { scale: fator + 0.08, duration: 0.5, ease: "power3.inOut" }, t);
      }
      if (selo) tl.fromTo(selo, { opacity: 0, scale: 0.5 }, { opacity: 1, scale: 1, duration: 0.3, ease: "back.out(3)" }, t + 0.35);
      pontos.forEach((p, i) => {
        const a = (i / pontos.length) * Math.PI * 2 + (i % 3) * 0.3, r = 260 + (i * 47) % 160;
        tl.fromTo(p, { x: 0, y: 0, opacity: 0, scale: 0.4 },
          { x: Math.cos(a) * r, y: Math.sin(a) * r, opacity: 1, scale: 1, duration: 0.7, ease: "expo.out" }, t + 0.05 + (i % 5) * 0.03);
        tl.to(p, { opacity: 0, duration: 0.5 }, t + 1.0 + (i % 4) * 0.1);
      });
      return t + 0.5;
    },

    /* 8. BARRA DE GRAU (intensidade do efeito): segmentos acendem até o k e o cursor recua para o meio. */
    graus(tl, sel, t, k, o = {}) {
      const el = $(sel), seg = [...el.querySelectorAll("i")];
      tl.fromTo(el, { opacity: 0, y: 30, filter: "blur(12px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.4, ease: "power3.out" }, t);
      const cheio = o.de ?? seg.length;
      seg.forEach((s, i) => { if (i < cheio) tl.call(() => s.classList.add("on"), null, t + 0.35 + i * 0.07); });
      seg.forEach((s, i) => { if (i >= k) tl.call(() => s.classList.remove("on"), null, t + 0.35 + cheio * 0.07 + 0.3 + (seg.length - i) * 0.06); });
      return t + 0.35 + cheio * 0.07 + 0.3 + seg.length * 0.06;
    },

    /* 9. AMOSTRAS de cor surgem uma a uma (pop) com nome e código. */
    amostras(tl, sel, t, o = {}) {
      const els = $$(sel);
      els.forEach((e, i) => tl.fromTo(e, { opacity: 0, scale: 0.6, y: 30, filter: "blur(10px)" },
        { opacity: 1, scale: 1, y: 0, filter: "blur(0px)", duration: 0.4, ease: "back.out(1.8)" }, t + i * (o.passo ?? 0.45)));
      return t + (els.length - 1) * (o.passo ?? 0.45) + 0.4;
    },

    /* 10. NUVEM de pílulas (marcas, ferramentas, tags) em volta do texto central: entram uma a uma com escala e
       desfoque e ficam boiando; o.ordem = índices na ordem de entrada. */
    nuvem(tl, sel, t, o = {}) {
      const els = $$(sel);
      els.forEach((e, i) => {
        const ti = t + i * (o.passo ?? 0.28);
        tl.fromTo(e, { opacity: 0, scale: 0.7, filter: "blur(12px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.4, ease: "back.out(1.6)" }, ti);
        tl.to(e, { y: (i % 2 ? 1 : -1) * 14, duration: 2.2, ease: "sine.inOut" }, ti + 0.4);
      });
      return t + (els.length - 1) * (o.passo ?? 0.28) + 0.4;
    },

    /* 11. ÓRBITA: cartões de UI aparecem em volta de um objeto central (olho, produto, rosto) e flutuam. */
    orbita(tl, centro, cartoes, t, o = {}) {
      tl.fromTo(centro, { opacity: 0, scale: 0.8, filter: "blur(14px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.5, ease: "power3.out" }, t);
      tl.to(centro, { scale: 1.04, duration: 2.5, ease: "sine.inOut" }, t + 0.5);
      $$(cartoes).forEach((c, i) => {
        const ti = t + 0.35 + i * (o.passo ?? 0.35);
        tl.fromTo(c, { opacity: 0, x: (i % 2 ? 60 : -60), filter: "blur(12px)" }, { opacity: 1, x: 0, filter: "blur(0px)", duration: 0.45, ease: "expo.out" }, ti);
        tl.to(c, { y: i % 2 ? 12 : -12, duration: 2, ease: "sine.inOut" }, ti + 0.45);
      });
      return t + 0.8;
    },
  };
  window.S = S;
})();
