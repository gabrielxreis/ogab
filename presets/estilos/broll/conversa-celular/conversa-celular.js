// BROLL · conversa no celular: um celular escuro (desenhado, sem marca) sobe da borda de baixo até abaixo do queixo; a conversa
// cresce de baixo para cima como num app de mensagens: balões dele em cinza à esquerda, os seus na cor da marca à direita.
ESTILO["conversa-celular"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, pw = 640, ph = 1240;
  C.css("conversa-celular", `
    .cc{position:absolute;width:${pw}px;height:${ph}px;border-radius:90px;background:#0d0d0f;padding:22px;
        box-shadow:0 30px 80px rgba(0,0,0,.55),inset 0 0 0 3px #2a2b2f;font-family:"PalcoSans"}
    .cc .tl{position:relative;width:100%;height:100%;border-radius:70px;background:#f3f3f5;overflow:hidden}
    .cc .hd{position:absolute;left:0;right:0;top:0;height:104px;z-index:2;background:rgba(243,243,245,.96);display:flex;gap:14px;align-items:center;
        justify-content:center;padding-top:34px;border-bottom:2px solid #e3e4e8}
    .cc .ilha{position:absolute;top:14px;left:50%;width:130px;height:30px;margin-left:-65px;border-radius:20px;background:#0d0d0f}
    .cc .av{width:46px;height:46px;border-radius:50%;background:var(--dest);display:grid;place-items:center;font-weight:900;font-size:22px;color:#111}
    .cc .nm{font-weight:800;font-size:24px;color:#17191d}
    .cc .ls{position:absolute;left:26px;right:26px;display:flex;flex-direction:column;gap:14px}
    .cc .b{max-width:78%;padding:16px 24px;border-radius:30px;font-weight:700;font-size:30px;line-height:1.28;display:none}
    .cc .b.ele{align-self:flex-start;background:#e2e3e8;color:#17191d;border-bottom-left-radius:8px}
    .cc .b.eu{align-self:flex-end;background:var(--dest);color:#111;border-bottom-right-radius:8px}`);
  const r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const visivel = H - S.baixo, topo = Math.min(r[3] + 40, visivel - 340);   // abaixo do queixo; mostra pelo menos 340 px de tela
  const c = C.el("div", "cc"); Object.assign(c.style, {left: (W - pw) / 2 + "px", top: topo + "px"});
  const nome = String(it.contato || "");
  c.innerHTML = `<div class="tl"><div class="hd"><div class="ilha"></div><div class="av">${C.esc(nome.slice(0, 1))}</div><div class="nm">${C.esc(nome)}</div></div>
    <div class="ls"></div></div>`;
  const ls = c.querySelector(".ls"); ls.style.bottom = (ph - 22 - (visivel - topo) + 24) + "px";   // a conversa termina na borda visível
  const tl = C.tl, d = it.de, f = it.ate, msgs = it.mensagens || [];
  tl.set(c, {y: H - topo + 40}, 0).to(c, {y: 0, duration: .7, ease: "expo.out"}, d);
  msgs.forEach((x, i) => {
    const bo = C.el("div", "b " + (x.eu ? "eu" : "ele"), ls, C.esc(x.texto || ""));
    const em = typeof x.em === "number" ? x.em : d + .55 + i * .85;
    tl.set(bo, {display: "block", scale: .6, opacity: 0, transformOrigin: x.eu ? "100% 100%" : "0% 100%"}, em)
      .to(bo, {scale: 1, opacity: 1, duration: .35, ease: "power3.out"}, em);
  });
  tl.to(c, {y: H - topo + 40, duration: .45, ease: "power3.in"}, Math.max(d + 1.6, f - .45));
};
