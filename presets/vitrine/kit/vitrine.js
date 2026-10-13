/* VITRINE: os movimentos do preset (GSAP, linha do tempo pausada do HyperFrames, determinístico).
   Uso: V.palavras(tl, "#frase", 0.1)  (cada função recebe a timeline, o seletor, o tempo de entrada e opções).
   Tempos medidos quadro a quadro na referência (12 qps): entradas de 0,25-0,45 s, sempre com desfoque. */
(function () {
  const $ = (s) => (typeof s === "string" ? document.querySelector(s) : s);
  const $$ = (s) => (typeof s === "string" ? [...document.querySelectorAll(s)] : s);

  const V = {
    /* 1. Palavras sobem uma a uma com desfoque e a câmera recua devagar (abertura, frase literal da fala). */
    palavras(tl, sel, t, o = {}) {
      const el = $(sel);
      if (!el.dataset.v) {
        el.innerHTML = el.textContent.trim().split(/\s+/).map((p) => `<span class="v-palavra">${p}</span>`).join("");
        el.dataset.v = 1;
      }
      tl.fromTo(el.querySelectorAll(".v-palavra"), { opacity: 0, y: o.y ?? 26, filter: "blur(12px)" },
        { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.32, stagger: o.passo ?? 0.12, ease: "power3.out" }, t);
      tl.fromTo(el, { scale: o.de ?? 1.18 }, { scale: 1, duration: o.dur ?? 1.0, ease: "power2.out" }, t);
      return t + (o.dur ?? 1.0);
    },

    /* 2. Saída em chicote: desliza para o lado com desfoque de movimento. */
    chicote(tl, sel, t, o = {}) {
      tl.to(sel, { x: o.x ?? -520, opacity: 0, filter: "blur(18px)", duration: o.dur ?? 0.28, ease: "power3.in" }, t);
      return t + (o.dur ?? 0.28);
    },

    /* 3. Carrossel de celulares: entram da direita borrados e seguem andando; saem caindo e sumindo. */
    carrossel(tl, sel, t, o = {}) {
      const cards = $$(sel), dur = o.dur ?? 1.4;
      tl.fromTo(cards, { x: o.de ?? 700, opacity: 0, filter: "blur(16px)" },
        { x: 0, opacity: 1, filter: "blur(0px)", duration: 0.45, stagger: 0.09, ease: "expo.out" }, t);
      tl.to(cards, { x: o.anda ?? -90, duration: dur, ease: "none" }, t + 0.2);
      tl.to(cards, { y: 60, scale: 0.9, opacity: 0, filter: "blur(10px)", duration: 0.35, stagger: 0.05, ease: "power2.in" }, t + dur - 0.1);
      return t + dur + 0.25;
    },

    /* 4. Troca de imagem dentro do cartão com um clarão branco rápido. */
    trocaImagem(tl, sel, t, novaUrl) {
      const el = $(sel);
      tl.to(el, { filter: "brightness(2.2) blur(6px)", duration: 0.08 }, t);
      tl.set(el, { backgroundImage: `url(${novaUrl})` }, t + 0.08);
      tl.to(el, { filter: "brightness(1) blur(0px)", duration: 0.18, ease: "power2.out" }, t + 0.08);
    },

    /* 5. Cortina escura sobe de baixo e cobre a cena (troca de bloco claro para escuro). */
    cortina(tl, sel, t, o = {}) {
      tl.fromTo(sel, { yPercent: 100 }, { yPercent: 0, duration: o.dur ?? 0.38, ease: "power4.inOut" }, t);
      return t + (o.dur ?? 0.38);
    },

    /* 6. Cartão de interface cai do alto com desfoque vertical e assenta. */
    cai(tl, sel, t, o = {}) {
      tl.fromTo(sel, { y: o.de ?? -160, opacity: 0, filter: "blur(14px)" },
        { y: 0, opacity: 1, filter: "blur(0px)", duration: o.dur ?? 0.5, ease: "expo.out" }, t);
      tl.to(sel, { scale: 0.97, duration: o.respira ?? 1.6, ease: "none" }, t + 0.5);   // nunca parado
      return t + (o.dur ?? 0.5);
    },

    /* 7. Digitação com cursor (campo de busca, valor, nome). ~11 caracteres por segundo. */
    digita(tl, sel, t, texto, o = {}) {
      const el = $(sel), cps = o.cps ?? 11;
      [...texto].forEach((_, i) => tl.call(() => { el.innerHTML = texto.slice(0, i + 1) + '<span class="v-cursor"></span>'; }, null, t + i / cps));
      tl.call(() => { el.innerHTML = texto.slice(0, 0) + '<span class="v-cursor"></span>'; }, null, Math.max(0, t - 0.001));
      return t + texto.length / cps;
    },

    /* 8. Número que conta (resultado, seguidores, preço), formato brasileiro. */
    conta(tl, sel, t, de, ate, o = {}) {
      const el = $(sel), n = { v: de }, casas = o.casas ?? 0, suf = o.sufixo ?? "", pre = o.prefixo ?? "";
      tl.to(n, { v: ate, duration: o.dur ?? 0.8, ease: o.ease ?? "power2.out",
        onUpdate: () => { el.textContent = pre + n.v.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas }) + suf; } }, t);
      return t + (o.dur ?? 0.8);
    },

    /* 9. Vira o tema: escuro vira claro num quadro (o "flip" de interface). */
    viraTema(tl, cena, cartao, t) {
      tl.set(cena, { backgroundColor: "#ffffff", color: "#111113" }, t);
      tl.set(cartao, { backgroundColor: "#f2f2f4", color: "#111113", borderColor: "rgba(0,0,0,.06)" }, t);
      return t;
    },

    /* 10. Zoom de perfil: começa pequeno e cresce devagar até preencher; sai desfocando. */
    zoomCartao(tl, sel, t, o = {}) {
      tl.fromTo(sel, { scale: o.de ?? 0.45, opacity: 0 }, { scale: o.ate ?? 1, opacity: 1, duration: o.dur ?? 1.2, ease: "power2.out" }, t);
      return t + (o.dur ?? 1.2);
    },
    someDesfocando(tl, sel, t, o = {}) {
      tl.to(sel, { opacity: 0, filter: "blur(14px)", scale: o.escala ?? 1.03, duration: o.dur ?? 0.3, ease: "power2.in" }, t);
      return t + (o.dur ?? 0.3);
    },

    /* 11. Foco puxando no b-roll real (vídeo ou foto): começa desfocado e aproxima. */
    foco(tl, sel, t, o = {}) {
      tl.fromTo(sel, { filter: "blur(18px)", scale: 1.1 }, { filter: "blur(0px)", duration: 0.5, ease: "power2.out" }, t);
      tl.to(sel, { scale: 1.0, duration: o.dur ?? 2.0, ease: "none" }, t);
      return t + (o.dur ?? 2.0);
    },

    /* 12. Clarão branco (passagem de um bloco para o outro). */
    clarao(tl, sel, t, o = {}) {
      tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: o.sobe ?? 0.16, ease: "power1.in" }, t);
      tl.to(sel, { opacity: 0, duration: o.desce ?? 0.3, ease: "power1.out" }, t + (o.sobe ?? 0.16) + (o.segura ?? 0.05));
      return t + (o.sobe ?? 0.16);
    },

    /* 13. Letras uma a uma (nome no cartão, texto na caixa de seleção). */
    letras(tl, sel, t, texto, o = {}) {
      const el = $(sel), cps = o.cps ?? 16;
      tl.call(() => { el.textContent = ""; }, null, Math.max(0, t - 0.001));
      [...texto].forEach((_, i) => tl.call(() => { el.textContent = texto.slice(0, i + 1); }, null, t + i / cps));
      return t + texto.length / cps;
    },

    /* 14. Caixa de seleção: abre como um cursor e cresce com o texto sendo digitado dentro (título de bloco). */
    selecao(tl, sel, t, texto, o = {}) {
      const el = $(sel);
      tl.fromTo(el, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.18, ease: "back.out(2)" }, t);
      return V.letras(tl, el, t + 0.06, texto, { cps: o.cps ?? 14 });
    },

    /* 15. Janela entra acesa a partir de um fantasma escuro e desfocado. */
    janela(tl, sel, t, o = {}) {
      tl.fromTo(sel, { opacity: 0, scale: 0.94, filter: "blur(16px) brightness(.4)" },
        { opacity: 1, scale: 1, filter: "blur(0px) brightness(1)", duration: o.dur ?? 0.45, ease: "power3.out" }, t);
      return t + (o.dur ?? 0.45);
    },

    /* 16. Pílula (ilha dinâmica): nasce como um ícone redondo e abre em texto; fecha e abre com outro texto. */
    pilula(tl, sel, t, texto, o = {}) {
      const el = $(sel), txt = el.querySelector(".txt"), larg = o.largura ?? 420;
      tl.call(() => { txt.innerHTML = texto; }, null, t);
      tl.fromTo(el, { width: 76, opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.22, ease: "back.out(2)" }, t);
      tl.to(el, { width: larg, duration: 0.42, ease: "back.out(1.3)" }, t + 0.22);
      tl.fromTo(txt, { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.25 }, t + 0.38);
      return t + 0.64;
    },
    fechaPilula(tl, sel, t) {
      const el = $(sel);
      tl.to(el.querySelector(".txt"), { opacity: 0, duration: 0.12 }, t);
      tl.to(el, { width: 76, duration: 0.3, ease: "power3.inOut" }, t + 0.08);
      return t + 0.38;
    },

    /* 17. Sino balança (inscrever / notificação). */
    sino(tl, sel, t) {
      tl.fromTo(sel, { rotation: 0 }, { keyframes: [{ rotation: -18 }, { rotation: 14 }, { rotation: -9 }, { rotation: 5 }, { rotation: 0 }],
        duration: 0.6, ease: "sine.inOut", transformOrigin: "50% 10%" }, t);
    },
  };
  window.V = V;
})();
