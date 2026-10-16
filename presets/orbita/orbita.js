// ÓRBITA: cartões em volta da pessoa. Tipos nesta versão: checklist (vidro escuro, check amarelo um a um),
// progresso ("seu reel está pronto" 0->100% + pílulas), cta (caixa de comentário digitando a palavra).
CENA.mod.orbita = function (cartoes, C) {
  const { tl, el, esc } = C;
  const CHECK = '<svg viewBox="0 0 26 22"><path d="M2 11 L10 19 L24 3" fill="none" stroke="#111" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const entra = (n, de) => tl.fromTo(n, { opacity: 0, y: 40, scale: .92 }, { opacity: 1, y: 0, scale: 1, duration: .5, ease: "back.out(1.8)" }, de);
  const sai = (n, ate) => tl.to(n, { opacity: 0, y: -20, duration: .3, ease: "power2.in" }, ate - .3);
  const pos = (n, c) => { n.style.left = c.x + "px"; n.style.top = c.y + "px"; if (c.w) n.style.width = c.w + "px"; };

  const tipos = {
    checklist(c) {
      const card = el("div", "card"); pos(card, c);
      if (c.titulo) el("div", "tit", card, esc(c.titulo));
      entra(card, c.de);
      c.itens.forEach(it => {
        const row = el("div", "it", card); const ck = el("div", "ck", row, "<i></i>" + CHECK); el("span", "", row, esc(it.t));
        tl.fromTo(row, { opacity: .35 }, { opacity: 1, duration: .2 }, it.em - .05);
        tl.to(ck.querySelector("i"), { opacity: 1, duration: .18 }, it.em);
        tl.fromTo(ck.querySelector("svg"), { opacity: 0, scale: .4 }, { opacity: 1, scale: 1, duration: .28, ease: "back.out(3)" }, it.em + .05);
      });
      sai(card, c.ate);
    },
    progresso(c) {
      const card = el("div", "card prog"); pos(card, c);
      const top = el("div", "pt", card); el("span", "", top, esc(c.titulo || "Seu reel está pronto")); const pc = el("b", "", top, "0%");
      const bar = el("div", "pb", card); const fill = el("i", "", bar);
      const pils = el("div", "pp", card);
      entra(card, c.de);
      const ate100 = c.de + (c.duracao || 1.6), o = { v: 0 };
      tl.to(o, { v: 100, duration: ate100 - c.de - .3, ease: "power2.inOut", onUpdate: () => { pc.textContent = Math.round(o.v) + "%"; } }, c.de + .3);
      tl.fromTo(fill, { width: "0%" }, { width: "100%", duration: ate100 - c.de - .3, ease: "power2.inOut" }, c.de + .3);
      (c.itens || []).forEach((t, i) => {
        const p = el("span", "pil2", pils, CHECK + esc(t));
        tl.fromTo(p, { opacity: 0, scale: .6 }, { opacity: 1, scale: 1, duration: .3, ease: "back.out(2.5)" }, c.de + .5 + i * ((ate100 - c.de - .3) / Math.max(1, c.itens.length)));
      });
      sai(card, c.ate);
    },
    cta(c) {
      if (c.rotulo) {
        const r = el("div", "cta-rot", null, esc(c.rotulo)); r.style.top = (c.y - 70) + "px";
        tl.fromTo(r, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: .3 }, c.de); tl.to(r, { opacity: 0, duration: .25 }, c.ate - .25);
      }
      const b = el("div", "cta"); b.style.top = c.y + "px";
      el("div", "av", b); const tx = el("div", "tx", b); const env = el("div", "env", b,
        '<svg width="36" height="40" viewBox="0 0 36 40"><path d="M18 36 V6 M5 18 L18 5 L31 18" fill="none" stroke="#111" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>');
      tl.fromTo(b, { opacity: 0, scale: .82, y: 30 }, { opacity: 1, scale: 1, y: 0, duration: .45, ease: "back.out(2)" }, c.de);
      const letras = [...c.texto].map(ch => el("span", "", tx, esc(ch)));
      const car = el("span", "car", tx);
      letras.forEach((s, i) => tl.fromTo(s, { opacity: 0 }, { opacity: 1, duration: .01 }, c.de + .45 + i * .11));
      for (let k = 0; c.de + .45 + k * .5 < c.ate; k++) tl.set(car, { opacity: k % 2 ? 1 : 0 }, c.de + .45 + k * .5 + .25);
      tl.fromTo(env, { scale: 1 }, { scale: 1.18, duration: .15, yoyo: true, repeat: 1 }, c.de + .55 + letras.length * .11);
      tl.to(b, { opacity: 0, duration: .25 }, c.ate - .25);
    },
  };
  cartoes.forEach(c => tipos[c.tipo] && tipos[c.tipo](c));
};
