// BATIDA · comentar e seguir: tela escura de app social (desenho próprio) abaixo do queixo. Cena 1: a palavra é digitada no
// campo, o botão enviar é tocado, o comentário entra na lista e o coração enche na cor da marca. Cena 2: a tela desliza para
// o perfil e o dedo toca "Seguir", que vira "Seguindo". Tudo em tamanho fixo 940x420 escalado para o espaço livre.
ESTILO["perfil-cta"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, LW = 940, LH = 420, en = P.lingua === "en";
  C.css("perfil-cta", `
    .pc{position:absolute;width:${LW}px;height:${LH}px;border-radius:52px;background:#101114;border:1.5px solid rgba(255,255,255,.12);
        box-shadow:0 30px 70px rgba(0,0,0,.5);overflow:hidden;transform-origin:50% 0;color:#fff}
    .pc .tr{position:absolute;left:0;top:0;width:${LW * 2}px;height:100%;display:flex}
    .pc .tl{width:${LW}px;height:100%;position:relative;padding:34px 44px}
    .pc .hd{text-align:center;font-weight:800;font-size:28px;color:rgba(255,255,255,.55)}
    .pc .hd:after{content:"";display:block;width:70px;height:6px;border-radius:4px;background:rgba(255,255,255,.2);margin:14px auto 0}
    .pc .cm{display:flex;align-items:center;gap:22px;margin-top:34px;opacity:0}
    .pc .av{width:76px;height:76px;border-radius:50%;flex:none;background:linear-gradient(135deg,#c9ced6,#6f7580)}
    .pc .cm .tx{flex:1}.pc .cm .us{font-weight:700;font-size:26px;color:rgba(255,255,255,.55)}.pc .cm .pv{font-weight:900;font-size:44px;letter-spacing:.01em}
    .pc .co{width:56px;height:56px;position:relative}
    .pc .co svg{position:absolute;inset:0}
    .pc .in{position:absolute;left:44px;right:44px;bottom:36px;height:96px;border-radius:50px;background:#1e2026;display:flex;align-items:center;padding:0 14px 0 36px;gap:16px}
    .pc .in .ph{position:absolute;left:36px;font-weight:700;font-size:32px;color:rgba(255,255,255,.35)}
    .pc .in .ty{flex:1;font-weight:900;font-size:40px;white-space:nowrap}.pc .in .ty span{display:none}
    .pc .in .cu{display:inline-block;width:4px;height:40px;background:var(--dest);vertical-align:-6px;margin-left:3px}
    .pc .in .en{width:70px;height:70px;border-radius:50%;background:var(--dest);display:grid;place-items:center;flex:none}
    .pc .pf{display:flex;align-items:center;gap:34px;margin-top:6px}
    .pc .ar{width:150px;height:150px;border-radius:50%;padding:7px;flex:none;background:linear-gradient(135deg,var(--dest),#7b5cff);
        background:linear-gradient(135deg,var(--dest),hsl(from var(--dest) calc(h + 70) s l))}
    .pc .ar i{display:block;width:100%;height:100%;border-radius:50%;border:6px solid #101114;background:linear-gradient(135deg,#c9ced6,#6f7580)}
    .pc .nm{font-weight:900;font-size:42px;line-height:1.1}.pc .ur{font-weight:700;font-size:28px;color:rgba(255,255,255,.55)}
    .pc .st{display:flex;gap:44px;margin-top:14px}.pc .st b{display:block;font-weight:900;font-size:34px}.pc .st span{font-weight:700;font-size:22px;color:rgba(255,255,255,.55)}
    .pc .sg{position:absolute;left:44px;right:44px;bottom:36px;height:96px;border-radius:26px;background:var(--dest);color:#111;
        display:grid;place-items:center;font-weight:900;font-size:38px;overflow:hidden}
    .pc .sg .s2{position:absolute;inset:0;display:grid;place-items:center;background:#2a2c33;color:#fff;opacity:0}
    .pc .dd{position:absolute;width:90px;height:90px;border-radius:50%;background:rgba(255,255,255,.55);border:3px solid rgba(255,255,255,.9);opacity:0;margin:-45px 0 0 -45px}`);
  const r = C.rostoEm(it.de) || [W * .3, H * .3, W * .7, H * .55];
  const baixo = [r[3] + 40, H - S.baixo], cima = [S.topo, r[1] - 30];
  const zona = baixo[1] - baixo[0] >= (cima[1] - cima[0]) * .8 ? baixo : cima;
  const esc = Math.min((W - 2 * S.lado - 20) / LW, (zona[1] - zona[0]) / LH);
  const e = C.el("div", "pc"); Object.assign(e.style, {left: (W - LW) / 2 + "px", top: zona[0] + Math.max(0, (zona[1] - zona[0] - LH * esc) / 2) + "px"});
  const pal = String(it.palavra || ""), us = String(it.usuario || "").replace(/^@/, "");
  const cor = `<path d="M28 48S6 35 6 20c0-7 5-12 11-12 5 0 9 3 11 7 2-4 6-7 11-7 6 0 11 5 11 12 0 15-22 28-22 28z"`;
  e.innerHTML = `<div class="tr"><div class="tl"><div class="hd">${en ? "Comments" : "Comentários"}</div>
      <div class="cm"><div class="av"></div><div class="tx"><div class="us">${en ? "you" : "você"} · ${en ? "now" : "agora"}</div><div class="pv">${C.esc(pal)}</div></div>
        <div class="co"><svg viewBox="0 0 56 56">${cor} fill="none" stroke="rgba(255,255,255,.6)" stroke-width="4"/></svg>
        <svg viewBox="0 0 56 56" class="ch">${cor} fill="var(--dest)" stroke="var(--dest)" stroke-width="4"/></svg></div></div>
      <div class="in"><span class="ph">${en ? "Add a comment..." : "Adicione um comentário..."}</span><div class="ty">${[...pal].map(c => `<span>${C.esc(c)}</span>`).join("")}<i class="cu"></i></div>
        <div class="en"><svg width="34" height="34" viewBox="0 0 34 34"><path d="M17 28V7M8 15l9-9 9 9" fill="none" stroke="#111" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg></div></div></div>
    <div class="tl"><div class="pf"><div class="ar"><i></i></div><div><div class="nm">${C.esc(it.nome || us)}</div><div class="ur">@${C.esc(us)}</div>
      <div class="st"><div><b>214</b><span>posts</span></div><div><b>${C.esc(it.seguidores || "")}</b><span>${en ? "followers" : "seguidores"}</span></div><div><b>180</b><span>${en ? "following" : "seguindo"}</span></div></div></div></div>
      <div class="sg">${en ? "Follow" : "Seguir"}<div class="s2">${en ? "Following" : "Seguindo"}</div></div></div></div><i class="dd"></i>`;
  const q = s => e.querySelector(s), ls = [...e.querySelectorAll(".ty span")], tl = C.tl, d = it.de, f = it.ate, dd = q(".dd");
  const toque = (x, y, t) => tl.set(dd, {left: x, top: y}, t - .01).fromTo(dd, {opacity: 0, scale: 1.4}, {opacity: 1, scale: 1, duration: .12, immediateRender: false}, t)
    .to(dd, {opacity: 0, scale: .7, duration: .25}, t + .2);
  tl.fromTo(e, {opacity: 0, y: 60, scale: esc * .92}, {opacity: 1, y: 0, scale: esc, duration: .45, ease: "power3.out"}, d);
  ls.forEach((l, i) => tl.to(l, {display: "inline", duration: .001}, d + .45 + i * .06));
  tl.to(q(".ph"), {opacity: 0, duration: .001}, d + .45);
  const tt = d + .45 + ls.length * .06 + .15;
  toque(LW - 44 - 14 - 35, LH - 36 - 48, tt);
  tl.to(q(".ty"), {opacity: 0, duration: .15}, tt + .1).to(q(".ph"), {opacity: 1, duration: .2}, tt + .25)
    .fromTo(q(".cm"), {opacity: 0, y: 40}, {opacity: 1, y: 0, duration: .35, ease: "back.out(1.6)", immediateRender: false}, tt + .1)
    .fromTo(q(".ch"), {opacity: 0, scale: .3, transformOrigin: "50% 50%"}, {opacity: 1, scale: 1, duration: .35, ease: "back.out(3)", immediateRender: false}, tt + .5)
    .to(q(".tr"), {x: -LW, duration: .5, ease: "power3.inOut"}, tt + .95);
  toque(LW / 2, LH - 36 - 48, tt + 1.65);
  tl.to(q(".s2"), {opacity: 1, duration: .15}, tt + 1.75)
    .to(q(".sg"), {scale: .96, duration: .1, yoyo: true, repeat: 1}, tt + 1.65)
    .to(e, {opacity: 0, y: 50, duration: .4, ease: "power2.in"}, Math.max(tt + 2.2, f - .4));
};
