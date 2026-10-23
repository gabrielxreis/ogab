// LAYOUT · faixa no topo: painel claro do topo até acima da cabeça (nunca passa do rosto). Dentro, um item por vez:
// {tipo: "citacao", texto, autor} | {tipo: "foto", imagem?, legenda} | {tipo: "numero", valor, texto}; cada um com "em".
ESTILO["faixa-topo"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  C.css("faixa-topo", `
    .ft{position:absolute;left:0;right:0;top:0;background:#F5F2EB;box-shadow:0 18px 50px rgba(0,0,0,.35);overflow:hidden;color:#16171b}
    .ft::after{content:"";position:absolute;left:0;right:0;bottom:0;height:8px;background:var(--dest)}
    .ft-i{position:absolute;left:${S.lado + 30}px;right:${S.lado + 30}px;display:flex;align-items:center;gap:34px}
    .ft-q{font-family:"PalcoSerif";font-style:italic;font-weight:600;font-size:66px;line-height:1.1}
    .ft-q::before{content:"\\201C";display:block;font-size:130px;line-height:.6;color:var(--dest);-webkit-text-stroke:3px #16171b;paint-order:stroke fill}
    .ft-a{font-weight:700;font-size:26px;letter-spacing:.24em;text-transform:uppercase;color:#6a6b70;margin-top:14px}
    .ft-f{flex:none;width:340px;height:100%;border:10px solid #fff;box-shadow:0 10px 26px rgba(0,0,0,.25);transform:rotate(-2deg);overflow:hidden;
          position:relative;background:linear-gradient(#cdb48f,#9c7f57)}
    .ft-f img{width:100%;height:100%;object-fit:cover;filter:sepia(.25)}
    .ft-f svg{position:absolute;left:0;bottom:0;width:100%}
    .ft-l{font-family:"PalcoSerif";font-style:italic;font-weight:600;font-size:58px;line-height:1.1}
    .ft-l small{display:block;font-family:"PalcoSans";font-style:normal;font-weight:800;font-size:24px;letter-spacing:.3em;color:#6a6b70;margin-bottom:10px}
    .ft-n{font-weight:900;font-size:172px;letter-spacing:-.05em;line-height:.9;color:#16171b}
    .ft-n b{display:block;width:100%;height:14px;background:var(--dest);margin-top:8px;transform-origin:0 50%}
    .ft-t{font-weight:800;font-size:48px;line-height:1.15}`);
  const base = Math.min(Math.round(H / 3), r[1] - 26), alto = Math.max(120, base - S.topo - 34);
  const fx = C.el("div", "ft"); fx.style.height = base + "px";
  const tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 1, f - .45), its = it.itens || [];
  tl.set(fx, {yPercent: -101}, 0).to(fx, {yPercent: 0, duration: .55, ease: "expo.out"}, d).to(fx, {yPercent: -101, duration: .45, ease: "power3.in"}, sai);
  const els = its.map(x => {
    const e = C.el("div", "ft-i", fx); Object.assign(e.style, {top: S.topo + "px", height: alto + "px"});
    if (x.tipo === "foto") {
      const src = x.imagem || x.src;
      e.innerHTML = `<div class="ft-f">${src ? `<img src="${C.esc(src)}">` : `<svg viewBox="0 0 300 160"><path d="M0 160 L0 90 L70 40 L130 95 L190 55 L300 120 L300 160Z" fill="#6f5638"/><circle cx="235" cy="45" r="22" fill="#efe1c4"/></svg>`}</div>
        <div class="ft-l"><small>${P.lingua === "en" ? "ARCHIVE" : "ARQUIVO"}</small>${C.esc(x.legenda || "")}</div>`;
    } else if (x.tipo === "numero") {
      e.innerHTML = `<div class="ft-n">${C.esc(x.valor || "")}<b></b></div><div class="ft-t">${C.esc(x.texto || "")}</div>`;
    } else {
      e.innerHTML = `<div><div class="ft-q">${C.esc(x.texto || "")}</div><div class="ft-a">${C.esc(x.autor || "")}</div></div>`;
    }
    const esc = Math.min(1, alto / 300); e.style.transformOrigin = "0 50%"; if (esc < 1) e.style.transform = `scale(${esc})`;
    return e;
  });
  els.forEach((e, i) => {   // entra pela direita; o anterior sai pela esquerda
    const em = typeof its[i].em === "number" ? its[i].em : d + .3 + i * (f - d - .8) / Math.max(1, els.length);
    tl.set(e, {opacity: 0}, 0).fromTo(e, {opacity: 0, x: 120}, {opacity: 1, x: 0, duration: .45, ease: "power3.out"}, Math.max(em, d + .25));
    const b = e.querySelector(".ft-n b"); if (b) tl.fromTo(b, {scaleX: 0}, {scaleX: 1, duration: .5, ease: "expo.out"}, em + .2);
    if (els[i + 1]) {
      const pr = typeof its[i + 1].em === "number" ? its[i + 1].em : em + .9;
      tl.to(e, {opacity: 0, x: -120, duration: .3, ease: "power2.in"}, pr - .25);
    }
  });
};
