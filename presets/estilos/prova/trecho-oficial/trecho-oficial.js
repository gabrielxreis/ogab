// PROVA · selo de trecho oficial: pílula escura no canto de cima (ícone de vídeo na cor da marca, rótulo e origem), entra por
// máscara e uma linha fina corre embaixo enquanto o trecho passa. O trecho em si é o vídeo que o editor colocou.
ESTILO["trecho-oficial"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, alto = 112;
  C.css("trecho-oficial", `
    .to-s{position:absolute;display:flex;align-items:center;gap:22px;padding:18px 34px 18px 20px;border-radius:30px;white-space:nowrap;
        background:rgba(12,12,14,.72);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);border:1.5px solid rgba(255,255,255,.16);
        box-shadow:0 16px 40px rgba(0,0,0,.35);color:#fff;font-family:"PalcoSans";overflow:hidden}
    .to-s .ic{width:72px;height:72px;border-radius:18px;background:var(--dest);display:grid;place-items:center;flex:none}
    .to-s .r{font-weight:800;font-size:22px;letter-spacing:.24em;color:rgba(255,255,255,.62)}
    .to-s .o{font-weight:800;font-size:36px;margin-top:2px}.to-s .o em{font-style:normal;font-weight:700;color:rgba(255,255,255,.6)}
    .to-s .bar{position:absolute;left:0;bottom:0;height:5px;width:100%;background:var(--dest);transform-origin:0 50%}`);
  const r = C.rostoEm(it.de);
  let y = S.topo + 10;
  if (r && r[1] < y + alto + 30) y = H - S.baixo - alto;   // rosto muito alto: o selo vai para baixo
  const s = C.el("div", "to-s"); Object.assign(s.style, {left: (S.lado + 25) + "px", top: y + "px"});
  s.innerHTML = `<div class="ic"><svg width="34" height="34" viewBox="0 0 34 34"><path d="M10 6 L28 17 L10 28 Z" fill="#111"/></svg></div>
    <div><div class="r">${C.esc(String(it.rotulo || "").toUpperCase())}</div>
    <div class="o">${C.esc(it.origem || "")}${it.data ? ` <em>· ${C.esc(it.data)}</em>` : ""}</div></div><i class="bar"></i>`;
  const bar = s.querySelector(".bar"), tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 1, f - .4);
  tl.set(s, {clipPath: "inset(0 100% 0 0 round 30px)", x: -20}, 0).set(bar, {scaleX: 0}, 0)
    .to(s, {clipPath: "inset(0 0% 0 0 round 30px)", x: 0, duration: .6, ease: "expo.out"}, d)
    .to(bar, {scaleX: 1, duration: Math.max(.5, sai - d - .3), ease: "none"}, d + .3)   // linha do tempo do trecho: contínua
    .to(s, {clipPath: "inset(0 0 0 100% round 30px)", duration: .4, ease: "power3.in"}, sai);
};
