// Carrossel de Motion (estilo PAINEL): cada slide é um vídeo 1080x1350 que se monta sozinho e para no quadro final.
// window.SLIDE vem do gerar.py. Tipos: capa, app (agente/produto num celular), conexao (hub), cta.
// Nada de onUpdate (o render salta quadros): números contam com tl.set quadro a quadro.
(function () {
  const S = window.SLIDE, M = S.marca, root = document.getElementById("root"), tl = gsap.timeline({ paused: true });
  for (const [k, v] of Object.entries(M.cores || {})) root.style.setProperty("--" + k, v);
  document.documentElement.style.setProperty("--fundo", (M.cores || {}).fundo || "#ECEAE6");
  const el = (tag, cls, pai, html, css) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html;
    if (css) Object.assign(e.style, css); (pai || root).appendChild(e); return e; };
  const esc = s => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  const neg = s => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
  const ICO = window.ICONES || {};
  const ico = (n, cor) => `<svg viewBox="0 0 24 24" fill="none" stroke="${cor || "currentColor"}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${(ICO[n] || ICO.check || []).map(d => `<path d="${d}"/>`).join("")}</svg>`;
  const CHK = '<svg viewBox="0 0 12 10"><path d="M1 5l3.5 3.5L11 1" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const sobe = (e, t, d = .55, y = 40) => tl.fromTo(e, { opacity: 0, y, filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: d, ease: "power3.out" }, t);
  const conta = (e, de, ate, t, d, fmt) => { const n = Math.round(d * 30); for (let i = 0; i <= n; i++) {
      const v = de + (ate - de) * gsap.parseEase("power2.out")(i / n); tl.set(e, { innerHTML: fmt(Math.round(v)) }, t + i / 30); } };

  // ---- moldura: logo, @, contador, título em duas cores, subtítulo, "arrasta"
  const lg = el("div", "abs logo", null, M.logo_img ? `<img src="${M.logo_img}">` : `<span class="nm">${M.logo_html || esc(M.nome)}</span>`);
  if (M.handle) el("span", "hd", lg, esc(M.handle));
  if (S.contador) el("div", "abs cont", null, esc(S.contador));
  tl.fromTo([lg, root.querySelector(".cont")].filter(Boolean), { opacity: 0 }, { opacity: 1, duration: .4 }, 0);
  let yTexto = 112;
  if (S.titulo) {
    const t = el("div", "abs tit", null, null, { top: (S.titulo_y || 112) + "px", fontSize: (S.titulo_tam || 98) + "px" });
    S.titulo.forEach((ln, i) => { const l = el("span", "l" + (i === S.titulo.length - 1 && S.titulo.length > 1 ? " d" : ""), t, `<span>${esc(ln)}</span>`);
      tl.fromTo(l.firstChild, { yPercent: 105 }, { yPercent: 0, duration: .6, ease: "power4.out" }, .05 + i * .12); });
    yTexto = (S.titulo_y || 112) + S.titulo.length * (S.titulo_tam || 98) * .92 + 30;
  }
  if (S.texto) { const s = el("div", "abs sub", null, neg(S.texto), { top: yTexto + "px" }); sobe(s, .45, .6, 16); }
  if (S.arrasta !== false) { const a = el("div", "abs arrasta", null, "arrasta →"); tl.fromTo(a, { opacity: 0, x: -20 }, { opacity: 1, x: 0, duration: .5, ease: "power2.out" }, S.dur - 2.6);
    tl.to(a, { x: 10, duration: .4, yoyo: true, repeat: 3, ease: "sine.inOut" }, S.dur - 2.0); }

  // ---- fios finos com pontinhos ligando cartões ao celular/hub
  const fios = el("div", "fios", null, `<svg width="1080" height="1350" viewBox="0 0 1080 1350"></svg>`).firstChild;
  const fio = (x1, y1, x2, y2, t, laranja) => {
    const mx = (x1 + x2) / 2, p = document.createElementNS("http://www.w3.org/2000/svg", "path");
    p.setAttribute("d", `M${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`);
    p.setAttribute("fill", "none"); p.setAttribute("stroke", laranja ? "var(--dest)" : "#c9c3ba"); p.setAttribute("stroke-width", laranja ? 2 : 1.6);
    fios.appendChild(p); const L = p.getTotalLength(); p.style.strokeDasharray = L;
    tl.fromTo(p, { strokeDashoffset: L }, { strokeDashoffset: 0, duration: .45, ease: "power2.inOut" }, t);
    const c = document.createElementNS("http://www.w3.org/2000/svg", "circle"); c.setAttribute("r", 6); c.setAttribute("fill", "var(--dest)");
    c.setAttribute("cx", laranja ? x1 : x2); c.setAttribute("cy", laranja ? y1 : y2); fios.appendChild(c);
    tl.fromTo(c, { opacity: 0, scale: 0, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, duration: .25, ease: "back.out(3)" }, t + .35);
  };

  const T = {
    capa() {
      const topo = yTexto + (S.texto ? 120 : 30), n = (S.itens || []).length, linhas = Math.ceil(n / 2);
      const g = el("div", "grade", null, null, { top: topo + "px" });
      g.style.setProperty("--agh", Math.min(240, (1240 - topo - 18 * (linhas - 1)) / linhas) + "px");
      (S.itens || []).forEach((it, i) => {
        const c = el("div", "ag", g, `<div class="ico">${ico(it.icone, "var(--dest)")}</div><div class="nn">${String(i + 1).padStart(2, "0")}</div><b>${esc(it.titulo)}</b><span>${esc(it.sub || "")}</span>`);
        tl.fromTo(c, { opacity: 0, y: 50, scale: .9 }, { opacity: 1, y: 0, scale: 1, duration: .5, ease: "back.out(1.6)" }, .8 + i * .14);
      });
    },
    app() {
      const A = S.app, cel = el("div", "cel", null, null, { left: "320px", top: "440px" }), tela = el("div", "tela", cel), topo = el("div", "topo", tela);
      tl.fromTo(cel, { y: 260, opacity: 0 }, { y: 0, opacity: 1, duration: .8, ease: "power3.out" }, .55);
      el("div", "ilha", topo); el("div", "hora", topo, "9:41"); el("div", "bat", topo, "<i></i><i></i><b></b>");
      el("div", "av", topo, esc((A.usuario || "T")[0])); el("div", "abs", topo, ico("lupa", "#fff") + ico("sino", "#fff"), { right: "22px", top: "92px", width: "56px", display: "flex", gap: "8px" });
      el("div", "ola", topo, esc(A.saudacao)); el("div", "met", topo, esc(A.metrica));
      if (A.selo) { const s = el("div", "selo", topo, esc(A.selo)); tl.fromTo(s, { opacity: 0, scale: .7 }, { opacity: 1, scale: 1, duration: .3, ease: "back.out(2)" }, 2.6); }
      const num = el("div", "num", topo); const tot = A.total ? `<small>/ ${esc(A.total)}${A.unidade ? " " + esc(A.unidade) : ""}</small>` : (A.unidade ? `<small>${esc(A.unidade)}</small>` : "");
      conta(num, 0, A.valor, 1.0, 2.2, v => v + tot);
      const bar = el("div", "barra", topo).appendChild(document.createElement("i"));
      tl.fromTo(bar, { width: "0%" }, { width: Math.min(100, A.total ? 100 * A.valor / A.total : 88) + "%", duration: 2.2, ease: "power2.out" }, 1.0);
      const tiles = el("div", "tiles", topo);
      (A.blocos || []).forEach((b, i) => { const t = el("div", "tile", tiles, `${ico(b.icone, "var(--dest)")}<b>0</b><span>${esc(b.rotulo)}</span>`);
        tl.fromTo(t, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: .35, ease: "power2.out" }, 1.6 + i * .12);
        conta(t.querySelector("b"), 0, b.valor, 1.7 + i * .12, 1.4, v => v); });
      const ag = el("div", "agora", tela, `<b>${esc(A.lista_titulo || "Agora")}</b><span>ao vivo</span>`); sobe(ag, 2.0, .4, 10);
      const lista = el("div", "lista", tela);
      (A.lista || []).forEach((it, i) => {
        const r = el("div", "item", lista, `<div class="chk"><i></i>${CHK}</div><div class="ini" style="background:${it.cor || "#6c5ce7"}">${esc(it.sigla)}</div>
          <div class="tx"><b>${esc(it.nome)}</b><span>${esc(it.texto)}</span></div><div class="tag ${it.tag_tipo || "ok"}">${esc(it.tag)}</div>`);
        const t0 = 2.1 + i * .38; tl.fromTo(r, { opacity: 0, x: 30 }, { opacity: 1, x: 0, duration: .35, ease: "power2.out" }, t0);
        if (it.feito !== false) { tl.to(r.querySelector(".chk i"), { opacity: 1, duration: .15 }, t0 + .3); tl.to(r.querySelector(".chk svg"), { opacity: 1, duration: .15 }, t0 + .35); }
      });
      const nav = el("div", "nav", tela, `<span class="on">${ico("casa", "#fff").replace("<svg", '<svg style="vertical-align:-4px;margin-right:6px"')}Início</span>${ico("pasta", "#555")}${ico("grafico", "#555")}${ico("pessoa", "#555")}`);
      el("div", "home", tela);
      // lados
      const yE = [560, 690, 820];
      if (S.entra) { const r = el("div", "abs rot", null, esc(S.entra_rotulo || "O que entra"), { left: "42px", top: "526px" }); sobe(r, 1.0, .4, 10);
        S.entra.forEach((e, i) => { const c = el("div", "card ent", null, `<div class="ico">${ico(e.icone, "#333")}</div><div><div class="t">${esc(e.titulo)}</div><div class="s">${esc(e.sub || "")}</div></div>`,
          { left: "40px", top: yE[i] + "px", width: "236px", height: (i === 0 ? 86 : 72) + "px" });
          tl.fromTo(c, { opacity: 0, x: -40 }, { opacity: 1, x: 0, duration: .45, ease: "power3.out" }, 1.1 + i * .15);
          fio(276, yE[i] + (i === 0 ? 43 : 36), 322, 700 + i * 30, 1.4 + i * .15, false); }); }
      if (S.decide) { const r = el("div", "abs rot", null, esc(S.decide_rotulo || "O que ele decide"), { left: "806px", top: "526px" }); sobe(r, 2.4, .4, 10);
        S.decide.forEach((d, i) => { const c = el("div", "card ent dec", null, `<div class="ico">${ico(d.icone, "var(--dest)")}</div><div class="t">${esc(d.titulo)}</div><div class="n">0</div>`,
          { left: "803px", top: yE[i] + "px", width: "238px", height: "74px" });
          tl.fromTo(c, { opacity: 0, x: 40 }, { opacity: 1, x: 0, duration: .45, ease: "power3.out" }, 2.6 + i * .18);
          fio(758, 730 + i * 30, 803, yE[i] + 37, 2.4 + i * .18, true); conta(c.querySelector(".n"), 0, d.valor, 2.7 + i * .18, 1.0, v => v); }); }
      if (S.regras) { const c = el("div", "card regras", null, `<div class="rot" style="margin-bottom:10px">${esc(S.regras_rotulo || "As regras dele")}</div>` +
          S.regras.map(r => `<div class="r">${esc(r[0])}<b>${esc(r[1])}</b></div>`).join(""), { left: "40px", top: "960px", width: "236px", padding: "20px 18px 8px" });
        tl.fromTo(c, { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: .5, ease: "power3.out" }, 3.3); }
    },
    conexao() {
      const C = S.conexao, hx = 540, hy = 790, hw = 340, hh = 230;
      const hub = el("div", "hub", null, `<div class="ico">${ico(C.hub_icone || "alvo", "#fff")}</div><b>${esc(C.hub)}</b><span>${esc(C.hub_sub || "")}</span>`,
        { left: (hx - hw / 2) + "px", top: (hy - hh / 2) + "px", width: hw + "px", height: hh + "px" });
      tl.fromTo(hub, { opacity: 0, scale: .7 }, { opacity: 1, scale: 1, duration: .6, ease: "back.out(1.7)" }, .7);
      const pos = [[158, 600], [540, 600], [922, 600], [158, 770], [922, 770], [158, 930], [922, 930]];
      C.nos.forEach((n, i) => { const [x, y] = pos[i], w = 236;
        const c = el("div", "card ent", null, `<div class="ico">${ico(n.icone, "#333")}</div><div><div class="t">${esc(n.titulo)}</div><div class="s">${esc(n.sub || "")}</div></div>`,
          { left: (x - w / 2) + "px", top: (y - 36) + "px", width: w + "px", height: "72px" });
        tl.fromTo(c, { opacity: 0, scale: .85 }, { opacity: 1, scale: 1, duration: .4, ease: "back.out(1.8)" }, 1.1 + i * .12);
        const ax = x === 540 ? 540 : (x < 540 ? x + w / 2 : x - w / 2), ay = x === 540 ? y + 36 : y;
        fio(ax, ay, x === 540 ? 540 : (x < 540 ? hx - hw / 2 : hx + hw / 2), x === 540 ? hy - hh / 2 : hy + (y - hy) * .2, 1.4 + i * .12, false);
      });
      if (C.aviso) { const n = el("div", "card noti", null, `<div class="q"><div class="lg"></div><div><b>${esc(C.aviso.de)}</b><span>${esc(C.aviso.sub || "")}</span></div><em>${esc(C.aviso.hora || "18:00")}</em></div><p>${neg(C.aviso.texto)}</p>`,
          { left: "250px", top: "1010px", width: "640px" });
        fio(540, hy + hh / 2, 540, 1010, 2.7, true);
        tl.fromTo(n, { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: .55, ease: "power3.out" }, 3.0); }
      if (C.mao) { const m = el("div", "abs mao", null, esc(C.mao), { left: "250px", top: "1232px", fontSize: "36px", color: "var(--dest)", transform: "rotate(-3deg)" });
        tl.fromTo(m, { opacity: 0, clipPath: "inset(0 100% 0 0)" }, { opacity: 1, clipPath: "inset(0 0% 0 0)", duration: .8, ease: "power1.inOut" }, 3.7); }
    },
    cta() {
      const C = S.cta, y0 = yTexto + 10;
      const k = el("div", "abs tit", null, `<span class="l"><span>${esc(C.chamada || "Comenta")}</span></span><span class="l"><span class="pill">${esc(C.palavra)}</span></span>`,
        { top: y0 + "px", fontSize: "104px" });
      k.querySelectorAll(".l > span").forEach((s, i) => tl.fromTo(s, { yPercent: 110 }, { yPercent: 0, duration: .6, ease: "power4.out" }, .6 + i * .15));
      const box = el("div", "card coment", null, `<div class="a"></div><div><small>você · agora</small><b></b></div>`, { left: "40px", top: (y0 + 260) + "px", width: "470px", height: "84px" });
      tl.fromTo(box, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: .45, ease: "back.out(1.6)" }, 1.2);
      const b = box.querySelector("b"); [...C.palavra].forEach((_, i) => tl.set(b, { innerHTML: esc(C.palavra.slice(0, i + 1)) + '<span class="car"></span>' }, 1.7 + i * .12));
      tl.set(b, { innerHTML: '<span class="car"></span>' }, 1.2);
      if (C.isca) { const I = C.isca, c = el("div", "isca", null, `<span class="tg">${esc(I.selo || "GRÁTIS")}</span><h3>${neg(I.titulo).replace(/<b>/g, "<em>").replace(/<\/b>/g, "</em>")}</h3>` +
          (I.itens || []).map(t => `<div class="li">${ico(t[1] || "check", "#F3956D")}${esc(t[0])}</div>`).join("") + `<div class="pe"><span>${esc(M.nome)}</span><span>${esc(I.rodape || "")}</span></div>`,
          { left: "560px", top: (y0 + 300) + "px", width: "400px", height: "520px" });
        tl.fromTo(c, { opacity: 0, y: 200, rotation: 14 }, { opacity: 1, y: 0, rotation: 6, duration: .8, ease: "back.out(1.4)" }, 2.6); }
      if (C.mao) C.mao.forEach((ln, i) => { const m = el("div", "abs mao", null, esc(ln), { left: (60 + i * 18) + "px", top: (y0 + 400 + i * 52) + "px", fontSize: "40px", color: i === 0 ? "var(--dest)" : "#222" });
        tl.fromTo(m, { opacity: 0, clipPath: "inset(0 100% 0 0)" }, { opacity: 1, clipPath: "inset(0 0% 0 0)", duration: .7, ease: "power1.inOut" }, 3.3 + i * .6); });
    },
  };
  (T[S.tipo] || T.capa)();
  tl.set({}, {}, S.dur);
  window.__TL = tl;
})();
