/* LUME: os movimentos do preset (GSAP, linha do tempo pausada do HyperFrames, determinístico).
   Uso: L.brilho(tl, "#l1", 0.2, "A gente trabalha / *em vídeos*", { serif: true })
   Cada função recebe a timeline, o seletor, o tempo de entrada e opções, e devolve o tempo em que termina.
   Tempos medidos quadro a quadro na referência (2, 10 e 15 qps): letras de 0,35 s com desfoque, objeto nasce em 0,4 s,
   luz vazada de 0,7 s com o corte no pico. */
(function () {
  const $ = (s) => (typeof s === "string" ? document.querySelector(s) : s);
  let nMask = 0;

  /* "A gente trabalha / *em vídeos*" -> linhas (/) com palavras.
     comum = linha pequena branca | *x* = chave grande que brilha (letra a letra) | ^x^ = destaque laranja
     ~x~ = palavra fria desfocada | =x= = branca em negrito */
  function monta(el, texto, o) {
    const letras = (s) => [...s].map((ch) => (ch === " " ? '<span class="c">&nbsp;</span>' : `<span class="c">${ch}</span>`)).join("");
    const sf = o.serif ? " serif" : "";
    el.innerHTML = '<span class="bloco">' + texto.split("/").map((linha) => {
      const partes = [];
      linha.trim().replace(/\*([^*]+)\*|\^([^^]+)\^|~([^~]+)~|=([^=]+)=|(\S+)/g, (m, ch, qu, fr, br, w) => {
        if (ch) partes.push(`<span class="w chave${sf}" data-l="1">${letras(ch)}</span>`);
        else if (qu) partes.push(`<span class="w quente">${qu}</span>`);
        else if (fr) partes.push(`<span class="w frio" data-l="1">${letras(fr)}</span>`);
        else if (br) partes.push(`<span class="w branca">${br}</span>`);
        else partes.push(`<span class="w peq${o.serifPeq ? " serif" : ""}">${w}</span>`);
      });
      return `<span class="l">${partes.join(" ")}</span>`;
    }).join("") + "</span>";
  }

  const L = {
    monta,

    /* 1. LEGENDA QUE BRILHA. Palavras pequenas sobem 26 px saindo do desfoque; a chave entra LETRA A LETRA
       (desfoque 16 px, sobe 40 px, nasce 1,25x maior) e fica brilhando; o bloco todo flutua devagar.
       o.tempos = [t de cada palavra] (da transcrição) ou o.passo (padrão 0,16 s); o.serif = chave em Playfair 900. */
    brilho(tl, sel, t, texto, o = {}) {
      const el = $(sel);
      monta(el, texto, o);
      tl.set(el, { opacity: 1 }, t);
      const ws = [...el.querySelectorAll(".w")];
      let fim = t;
      ws.forEach((w, i) => {
        const ti = o.tempos ? o.tempos[i] : t + i * (o.passo ?? 0.16);
        if (w.dataset.l) {
          const cs = [...w.querySelectorAll(".c")], frio = w.classList.contains("frio");
          tl.fromTo(cs, { opacity: 0, y: 40, scale: 1.25, filter: "blur(16px)" },
            { opacity: 1, y: 0, scale: 1, filter: frio ? "blur(1.5px)" : "blur(0px)", duration: 0.38, ease: "power3.out", stagger: o.letra ?? 0.035 }, ti);
          fim = Math.max(fim, ti + (cs.length - 1) * (o.letra ?? 0.035) + 0.38);
        } else {
          tl.fromTo(w, { opacity: 0, y: 26, filter: "blur(10px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.32, ease: "power3.out" }, ti);
          fim = Math.max(fim, ti + 0.32);
        }
      });
      const bloco = el.querySelector(".bloco");
      tl.fromTo(bloco, { y: 10 }, { y: -8, duration: o.vida ?? 2.4, ease: "sine.inOut" }, t);   // flutua: nunca parado
      return fim;
    },

    /* 2. Sai: desfoca e some (legenda, objeto, cena). */
    sai(tl, sel, t, o = {}) {
      tl.to(sel, { opacity: 0, filter: `blur(${o.blur ?? 14}px)`, y: o.y ?? 0, duration: o.dur ?? 0.25, ease: "power2.in" }, t);
      return t + (o.dur ?? 0.25);
    },

    /* 3. Câmera no vídeo: aproximação lenta (Ken Burns) ou punch-in rápido entre frases. */
    camera(tl, sel, t, dur, o = {}) {
      tl.fromTo(sel, { scale: o.de ?? 1 }, { scale: o.para ?? 1.06, duration: dur, ease: o.ease ?? "none" }, t);
      return t + dur;
    },

    /* 4. CENA DE MESA: entra no corte seco (como na referência) e empurra devagar 1 -> 1,05. */
    mesa(tl, sel, t, dur, o = {}) {
      tl.set(sel, { opacity: 1, filter: "blur(0px)" }, t);
      const foto = $(sel).querySelector("img.l-foto");
      if (foto) tl.fromTo(foto, { scale: 1 }, { scale: o.zoom ?? 1.05, duration: dur, ease: "none" }, t);
      return t + dur;
    },

    /* 5. OBJETO nasce pequeno e desfocado no lugar e cresce nítido (0,45 s), com um respiro no fim.
       o.rot = inclinação final (graus; não usar rotate no CSS, o GSAP sobrescreve), o.giro = quanto gira ao entrar. */
    objeto(tl, sel, t, o = {}) {
      tl.fromTo(sel, { opacity: 0, scale: o.de ?? 0.12, rotation: (o.rot ?? 0) + (o.giro ?? 0), filter: "blur(14px)" },
        { opacity: 1, scale: 1, rotation: o.rot ?? 0, filter: "blur(0px)", duration: o.dur ?? 0.45, ease: "power3.out" }, t);
      tl.to(sel, { scale: 1.02, duration: 1.6, ease: "sine.inOut", yoyo: true, repeat: 1 }, t + (o.dur ?? 0.45));
      return t + (o.dur ?? 0.45);
    },

    /* 6. SETA TRACEJADA que se desenha (máscara sólida percorrendo o traço tracejado) e a ponta aparece no fim.
       o.d = caminho SVG em coordenadas do próprio svg; o.ponta = [x, y, ângulo]. */
    seta(tl, sel, t, o = {}) {
      const el = $(sel), id = "lm" + (++nMask), cor = o.cor ?? "var(--l-tinta)";
      const [px, py, pa] = o.ponta ?? [0, 0, 90];
      el.innerHTML = `<defs><mask id="${id}"><path class="m" d="${o.d}" stroke="#fff" stroke-width="16" fill="none" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/></mask></defs>
        <path d="${o.d}" stroke="${cor}" stroke-width="${o.esp ?? 5}" fill="none" stroke-linecap="round" stroke-dasharray="9 11" mask="url(#${id})"/>
        <path class="pt" d="M -16 -12 L 0 0 L -16 12" stroke="${cor}" stroke-width="${o.esp ?? 5}" fill="none" stroke-linecap="round" stroke-linejoin="round" transform="translate(${px} ${py}) rotate(${pa})" opacity="0"/>`;
      const dur = o.dur ?? 0.7;
      tl.set(el, { opacity: 1 }, t);
      tl.fromTo(el.querySelector(".m"), { attr: { "stroke-dashoffset": 1 } }, { attr: { "stroke-dashoffset": 0 }, duration: dur, ease: "power1.inOut" }, t);
      tl.to(el.querySelector(".pt"), { opacity: 1, duration: 0.08 }, t + dur - 0.06);
      return t + dur;
    },

    /* 7. TRAÇO à mão (rabisco do storyboard, sublinhado): cada <path> do svg se desenha em sequência. */
    traco(tl, sel, t, o = {}) {
      const ps = [...$(sel).querySelectorAll("path")];
      tl.set(sel, { opacity: 1 }, t);
      ps.forEach((p, i) => {
        p.setAttribute("pathLength", "1"); p.style.strokeDasharray = 1; p.style.strokeDashoffset = 1;
        tl.to(p, { strokeDashoffset: 0, duration: o.dur ?? 0.3, ease: "power1.inOut" }, t + i * (o.passo ?? 0.12));
      });
      return t + (ps.length - 1) * (o.passo ?? 0.12) + (o.dur ?? 0.3);
    },

    /* 8. MANUSCRITO: o texto à mão "se escreve" da esquerda para a direita (máscara que corre). */
    manuscrito(tl, sel, t, o = {}) {
      tl.set(sel, { opacity: 1 }, t);
      tl.fromTo(sel, { clipPath: "inset(-20% 100% -20% 0%)" }, { clipPath: "inset(-20% 0% -20% 0%)", duration: o.dur ?? 0.8, ease: "none" }, t);
      return t + (o.dur ?? 0.8);
    },

    /* 9. FRASE sobre a mesa: palavra a palavra em laranja, saindo de um rascunho fantasma à mão.
       "pensando no que / vem depois" -> o fantasma aparece inteiro e cada palavra laranja nasce por cima dele. */
    frase(tl, sel, t, texto, o = {}) {
      const el = $(sel);
      const ws = texto.split(/\s+/);
      el.innerHTML = `<div class="fant" style="position:absolute;left:0;right:0;top:-6px;opacity:0">${texto}</div><div class="cheia">` +
        ws.map((w) => (w === "/" ? "<br>" : `<span class="w">${w}</span>`)).join(" ") + "</div>";
      tl.set(el, { opacity: 1 }, t);
      tl.fromTo(el.querySelector(".fant"), { opacity: 0, filter: "blur(6px)" }, { opacity: 0.55, filter: "blur(1px)", duration: 0.35 }, t);
      const pal = [...el.querySelectorAll(".cheia .w")];
      pal.forEach((w, i) => tl.fromTo(w, { opacity: 0, y: 18, filter: "blur(8px)" },
        { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.3, ease: "power3.out" }, t + 0.25 + i * (o.passo ?? 0.18)));
      tl.to(el.querySelector(".fant"), { opacity: 0, duration: 0.3 }, t + 0.25 + pal.length * (o.passo ?? 0.18));
      return t + 0.25 + pal.length * (o.passo ?? 0.18) + 0.3;
    },

    /* 10. MERGULHO DE FOCO: a cena inteira desfoca e escurece enquanto UM objeto cresce nítido por cima, do centro. */
    mergulho(tl, cena, obj, t, o = {}) {
      tl.to(cena, { filter: "blur(16px) brightness(.72)", scale: 1.08, duration: 0.55, ease: "power2.inOut" }, t);
      tl.fromTo(obj, { opacity: 0, scale: 0.35, y: 90, filter: "blur(12px)" },
        { opacity: 1, scale: 1, y: 0, filter: "blur(0px)", duration: 0.6, ease: "power3.out" }, t + 0.15);
      return t + 0.75;
    },

    /* 11. LUZ VAZADA quente (roxo -> amarelo -> laranja) subindo pela tela; devolve o PICO, onde entra o corte. */
    luz(tl, sel, t, o = {}) {
      const dur = o.dur ?? 0.75;
      tl.fromTo(sel, { opacity: 0, yPercent: 30 }, { opacity: 1, yPercent: 0, duration: dur * 0.5, ease: "power2.in" }, t);
      tl.to(sel, { opacity: 0, yPercent: -25, duration: dur * 0.5, ease: "power2.out" }, t + dur * 0.5);
      return t + dur * 0.5;
    },
  };
  window.L = L;
})();
