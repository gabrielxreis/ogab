// GANCHO · caixa de 3 segundos: bloco chapado na cor da marca com o gancho; abre por máscara e some aos 3 s, deixando o quadro limpo.
ESTILO["caixa-3s"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const hex = String(P.dest || "#F2D16B").replace("#", ""), rgb = [0, 2, 4].map(i => parseInt(hex.substr(i, 2), 16) / 255);
  const tinta = (.2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2]) > .45 ? "#111214" : "#fff";   // texto legível sobre a cor da marca
  C.css("caixa-3s", `
    .c3{position:absolute;text-wrap:balance;left:${S.lado + 30}px;right:${S.lado + 30}px;background:var(--dest);border-radius:26px;padding:34px 44px 40px;
        font-family:"PalcoSans";font-weight:900;line-height:1.05;letter-spacing:-.025em;text-align:center;box-shadow:0 24px 60px rgba(0,0,0,.35)}
    .c3 span{display:inline-block;margin:0 .12em}`);
  const txt = String(it.texto || ""), fs = txt.length <= 24 ? 84 : txt.length <= 44 ? 70 : 58;
  const larg = W - 2 * (S.lado + 30) - 88, linhas = Math.ceil(txt.length * fs * .6 / larg), alt = linhas * fs * 1.05 + 74;
  let top = S.topo + 10;
  if (top + alt > r[1] - 30 && r[3] + 40 + alt <= H - S.baixo) top = r[3] + 40;   // sem espaço acima da cabeça: vai para baixo do queixo
  const b = C.el("div", "c3", null, txt.split(/\s+/).map(w => `<span>${C.esc(w)}</span>`).join(" "));
  Object.assign(b.style, {top: top + "px", fontSize: fs + "px", color: tinta});
  const tl = C.tl, d = it.de, fim = Math.min(it.ate, d + 3);
  tl.set(b, {clipPath: "inset(0% 100% 0% 0% round 26px)"}, 0)
    .to(b, {clipPath: "inset(0% 0% 0% 0% round 26px)", duration: .5, ease: "expo.out"}, d)
    .fromTo(b.children, {y: 30, opacity: 0}, {y: 0, opacity: 1, duration: .4, stagger: .04, ease: "power3.out"}, d + .12)
    .to(b, {clipPath: "inset(0% 0% 0% 100% round 26px)", duration: .35, ease: "power3.in"}, Math.max(d + 1, fim - .35));
};
