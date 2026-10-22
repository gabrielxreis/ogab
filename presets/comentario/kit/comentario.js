// Preset COMENTÁRIO: o card do comentário entra com pop suave (escala + leve giro que assenta em perspectiva), o
// coração enche e as curtidas sobem; a palavra-chave ganha marca-texto. Um comentário novo empurra o anterior para
// trás (sobe, encolhe, escurece) e o mais antigo some. Tudo numa timeline GSAP pausada: render determinístico.
(async function () {
  const P = window.PLANO, W = P.w, H = P.h, dur = P.dur || 8;
  try { await Promise.all(["500 46px", "600 30px", "700 32px", "800 40px"].map(f => document.fonts.load(f + " 'Inter Tight'"))); await document.fonts.ready; } catch (e) {}
  const root = document.getElementById("root"), palco = document.getElementById("palco");
  const U = Math.min(W, H) / 1080;
  root.style.setProperty("--cor", P.cor || "#FF8B3D"); root.style.setProperty("--u", U + "px");
  if (P.fundo === "transparente") root.classList.add("sem-fundo");
  const estilo = P.estilo === "vidro" ? "vidro" : "claro";
  const cy = H * (P.posicao === "centro" ? .44 : .31);           // centro do card da frente
  const LARG = Math.min(860 * U, W * .82);
  const tl = gsap.timeline({ paused: true });
  // Chegada com overshoot pequeno (passa ~3% e assenta). Função própria, sem curvas de quique.
  const assenta = p => { const s = 1.0, q = p - 1; return q * q * ((s + 1) * q + s) + 1; };
  const mk = (tag, cls, pai, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; if (pai) pai.appendChild(e); return e; };
  const fmt = n => Math.round(n).toLocaleString("pt-BR");

  const lista = (P.comentarios || []).map((c, i) => Object.assign({ em: .3 + i * 2.6 }, c));
  const cards = lista.map((c, i) => {
    const card = mk("div", "card " + estilo, palco); card.style.width = LARG + "px"; card.style.top = cy + "px";
    const av = mk("div", "av", card), nome = String(c.usuario || "").replace(/^@/, "");
    if (c.avatar) { const im = mk("img", "", av); im.src = c.avatar; im.alt = ""; }
    else av.textContent = (nome.match(/[A-Za-zÀ-ÿ0-9]/) || ["?"])[0].toUpperCase();
    const corpo = mk("div", "corpo", card), cab = mk("div", "cab", corpo);
    mk("span", "user", cab, "@" + nome); if (c.tempo) mk("span", "tempo", cab, c.tempo);
    // Texto: palavra-chave em "destaque" (ou entre *asteriscos*) ganha o marca-texto.
    const txt = mk("div", "txt", corpo); let tinta = null, t = String(c.texto || "");
    let partes = [t];
    if (c.destaque) { const k = t.toLowerCase().indexOf(String(c.destaque).toLowerCase());
      if (k >= 0) partes = [t.slice(0, k), "*" + t.slice(k, k + c.destaque.length) + "*", t.slice(k + c.destaque.length)]; }
    else partes = t.split(/(\*[^*]+\*)/);
    partes.filter(Boolean).forEach(p => {
      if (/^\*.*\*$/.test(p)) { const hl = mk("span", "hl", txt); tinta = mk("span", "tinta", hl); mk("span", "", hl, p.slice(1, -1)); }
      else txt.appendChild(document.createTextNode(p));
    });
    const rod = mk("div", "rod", corpo), like = mk("span", "like", rod);
    like.innerHTML = '<svg viewBox="0 0 24 24"><path class="contorno" d="M12 20.5s-7.5-4.6-9.3-9.2C1.4 8 3.4 4.5 6.9 4.5c2.1 0 3.6 1.2 5.1 3 1.5-1.8 3-3 5.1-3 3.5 0 5.5 3.5 4.2 6.8-1.8 4.6-9.3 9.2-9.3 9.2z"/>' +
      '<path class="cheio" d="M12 20.5s-7.5-4.6-9.3-9.2C1.4 8 3.4 4.5 6.9 4.5c2.1 0 3.6 1.2 5.1 3 1.5-1.8 3-3 5.1-3 3.5 0 5.5 3.5 4.2 6.8-1.8 4.6-9.3 9.2-9.3 9.2z"/></svg>';
    const num = typeof c.curtidas === "number" ? c.curtidas : null;
    const b = mk("b", "", like, num != null ? fmt(num * .86) : String(c.curtidas ?? ""));
    mk("span", "resp", rod, P.responder || "Responder");
    const escuro = mk("div", "escuro", card);
    return { c, card, corpo, tinta, b, num, cheio: like.querySelector(".cheio"), escuro, giro: i % 2 ? 3.5 : -4 };
  });
  await Promise.all([...palco.querySelectorAll("img")].map(im => im.decode ? im.decode().catch(() => {}) : null));
  cards.forEach(k => { k.h = k.card.offsetHeight; });

  // Estado de cada profundidade na pilha (0 = frente). O de trás espia por cima do da frente; o terceiro some.
  const estado = (d, k, frente) => {
    if (d === 0) return { y: 0, scale: 1, rotation: 0, rotationX: 0, opacity: 1 };
    const s = d === 1 ? .92 : .84, espia = (d === 1 ? 62 : 112) * U;
    return { y: -frente.h / 2 - espia + k.h * s / 2, scale: s, rotation: 0, rotationX: 6 * d, opacity: d === 1 ? 1 : 0 };
  };
  cards.forEach((k, i) => {
    gsap.set(k.card, { xPercent: -50, yPercent: -50, y: 70 * U, scale: .82, rotation: k.giro, rotationX: 14, opacity: 0, zIndex: 10 + i, transformOrigin: "50% 60%" });
    gsap.set(k.corpo, { opacity: 0, y: 14 * U });
    if (k.tinta) gsap.set(k.tinta, { scaleX: 0 });
    gsap.set(k.cheio, { scale: 0, transformOrigin: "50% 50%" });
  });
  cards.forEach((k, i) => {
    const t0 = k.c.em;
    // Os anteriores recuam junto (começam um tiquinho antes: antecipação).
    for (let j = 0; j < i; j++) {
      const d = i - j; if (d > 2) continue;
      const e = estado(d, cards[j], k);
      tl.to(cards[j].card, Object.assign({ duration: .85, ease: "power3.inOut" }, e), t0 - .05);
      if (d === 1) tl.to(cards[j].corpo, { opacity: 0, duration: .3, ease: "power2.out" }, t0 - .05);   // texto antigo não vaza pelo card novo
      tl.to(cards[j].escuro, { opacity: estilo === "claro" ? .32 * d : .4 * d, duration: .85, ease: "power3.inOut" }, t0 - .05);
    }
    tl.to(k.card, { opacity: 1, duration: .2, ease: "power2.out" }, t0);
    tl.to(k.card, Object.assign({ duration: 1.0, ease: assenta }, estado(0)), t0);
    // Overlap: o conteúdo chega um pouco depois do card, quando o giro já quase assentou.
    tl.to(k.corpo, { opacity: 1, y: 0, duration: .5, ease: "power2.out" }, t0 + .14);
    // Ação secundária: coração enche com pulso e curtidas sobem; marca-texto corre por trás da palavra.
    tl.to(k.cheio, { scale: 1.15, duration: .28, ease: "power2.out" }, t0 + .55).to(k.cheio, { scale: 1, duration: .4, ease: "power2.inOut" }, t0 + .83);
    if (k.num != null) { const o = { v: k.num * .86 };
      tl.to(o, { v: k.num, duration: 1.1, ease: "power2.out", onUpdate: () => { k.b.textContent = fmt(o.v); } }, t0 + .55); }
    if (k.tinta) tl.to(k.tinta, { scaleX: 1, duration: .7, ease: "expo.out" }, t0 + .7);
  });
  tl.fromTo("#cam", { scale: 1.03 }, { scale: 1, duration: dur, ease: "sine.out" }, 0);
  tl.set({}, {}, dur);
  window.__timelines = window.__timelines || {}; window.__timelines["comentario"] = tl;
})();
