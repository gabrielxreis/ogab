// LAYOUT · antes e depois (tela cheia): fundo claro com linhas diagonais suaves, cabeçalho, cartão "Antes" pequeno e sem cor à
// esquerda, seta desenhada e cartão "Depois" grande com borda da marca à direita. antes/depois: caminho da imagem ou {imagem, rotulo}.
ESTILO["antes-depois"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, en = P.lingua === "en";
  C.css("antes-depois", `
    .ad{position:absolute;inset:0;background:repeating-linear-gradient(135deg, rgba(20,22,28,.035) 0 14px, transparent 14px 34px), #F2EFE8;color:#15161a}
    .ad .cab{position:absolute;left:${S.lado + 30}px;right:${S.lado + 30}px;top:${S.topo + 10}px;text-align:center}
    .ad .cab small{font-weight:800;font-size:28px;letter-spacing:.34em;color:#7b7c80}
    .ad .cab div{font-weight:900;font-size:76px;line-height:1.02;letter-spacing:-.03em;margin-top:12px}
    .ad .k{position:absolute;background:#fff;border-radius:22px;padding:14px;box-shadow:0 24px 56px rgba(0,0,0,.22)}
    .ad .k .im{width:100%;height:100%;border-radius:12px;overflow:hidden;position:relative}
    .ad .k img{width:100%;height:100%;object-fit:cover}.ad .k svg{width:100%;height:100%;display:block}
    .ad .k em{position:absolute;top:-26px;left:24px;font-style:normal;font-weight:900;font-size:30px;letter-spacing:.12em;padding:10px 24px;border-radius:30px}
    .ad .an{filter:grayscale(1) brightness(.92)}.ad .an em{background:#2b2c31;color:#fff}
    .ad .de{outline:8px solid var(--dest);outline-offset:-2px}.ad .de em{background:var(--dest);color:#111}
    .ad .seta{position:absolute;overflow:visible}`);
  const pega = (v, pad) => typeof v === "string" ? {imagem: v, rotulo: pad} : Object.assign({rotulo: pad}, v || {});
  const a = pega(it.antes, en ? "Before" : "Antes"), b = pega(it.depois, en ? "After" : "Depois");
  const ilu = bom => `<svg viewBox="0 0 400 520" preserveAspectRatio="xMidYMid slice"><rect width="400" height="520" fill="${bom ? "#1c2230" : "#8d8f94"}"/>
    ${[0, 1, 2, 3, 4].map(i => { const h = bom ? 70 + i * 70 : 120 - (i % 2) * 40 + i * 6;
      return `<rect x="${40 + i * 68}" y="${460 - h}" width="46" height="${h}" rx="8" fill="${bom ? (i === 4 ? "var(--dest)" : "rgba(255,255,255,.75)") : "#b4b6ba"}"/>`; }).join("")}
    ${bom ? `<circle cx="330" cy="80" r="40" fill="var(--dest)"/><path d="M312 80 l12 13 l24 -26" stroke="#111" stroke-width="9" fill="none" stroke-linecap="round"/>` : ""}</svg>`;
  const ad = C.el("div", "ad");
  const cab = C.el("div", "cab", ad, `<small>${en ? "BEFORE · AFTER" : "ANTES · DEPOIS"}</small><div>${C.esc(it.titulo || "")}</div>`);
  const ka = C.el("div", "k an", ad), kb = C.el("div", "k de", ad);
  const y0 = S.topo + 270, yb = H - S.baixo - 10, hb = yb - y0, wb = Math.round(W * .54), wa = Math.round(W * .33);
  Object.assign(ka.style, {left: S.lado + 25 + "px", top: y0 + hb * .3 + "px", width: wa + "px", height: hb * .55 + "px"});
  Object.assign(kb.style, {right: S.lado + 25 + "px", top: y0 + "px", width: wb + "px", height: hb + "px"});
  [[ka, a, 0], [kb, b, 1]].forEach(([k, v, bom]) => { k.innerHTML = `<div class="im">${v.imagem || v.src ? `<img src="${C.esc(v.imagem || v.src)}">` : ilu(bom)}</div><em>${C.esc(v.rotulo)}</em>`; });
  const sx = S.lado + 25 + wa * .55, sy = y0 + hb * .3 - 30, seta = C.el("div", "seta", ad);
  Object.assign(seta.style, {left: sx + "px", top: sy - 150 + "px", width: "260px", height: "160px"});
  seta.innerHTML = `<svg width="260" height="160" viewBox="0 0 260 160"><path d="M10 150 C 30 40 140 10 230 50" stroke="#15161a" stroke-width="9" fill="none" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>
    <path d="M205 26 L238 54 L198 70" stroke="#15161a" stroke-width="9" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="0"/></svg>`;
  const [p1, p2] = seta.querySelectorAll("path");
  const tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 1.2, f - .45);
  tl.set(ad, {clipPath: "inset(100% 0 0 0)"}, 0).to(ad, {clipPath: "inset(0% 0 0 0)", duration: .45, ease: "expo.out"}, d)
    .fromTo(cab, {y: -40, opacity: 0}, {y: 0, opacity: 1, duration: .45, ease: "power3.out"}, d + .1)
    .fromTo(ka, {x: -260, rotation: -14}, {x: 0, rotation: -5, duration: .55, ease: "back.out(1.4)"}, d + .2)
    .to(p1, {attr: {"stroke-dashoffset": 0}, duration: .4, ease: "power2.out"}, d + .55).set(p2, {opacity: 1}, d + .9)
    .fromTo(kb, {x: 320, rotation: 8, scale: .85}, {x: 0, rotation: 2, scale: 1, duration: .6, ease: "back.out(1.4)"}, d + .7)
    .to(kb, {scale: 1.025, duration: Math.max(.4, sai - d - 1.3), ease: "sine.inOut"}, d + 1.3)
    .to(ad, {clipPath: "inset(0 0 100% 0)", duration: .45, ease: "power3.in"}, sai);
};
