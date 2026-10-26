// EFEITO · fichas com objeto: fichas creme giram no eixo Y e param acima da cabeça; cada uma traz um objeto "3D" brilhante
// desenhado em SVG (gradientes + reflexo) na cor da marca e um rótulo em serifa itálica. Fogem do rosto (C.rostoEm).
ESTILO["fichas-objeto"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const itens = (it.itens || []).slice(0, 3), n = Math.max(1, itens.length), gap = 34;
  const espaco = Math.max(260, r[1] - 40 - S.topo);                    // altura livre acima da cabeça
  const fh = Math.min(400, espaco), fw = Math.min(Math.round(fh * .78), Math.floor((W - 2 * S.lado - gap * (n - 1)) / n));
  C.css("fichas-objeto", `
    .fo-palco{position:absolute;left:0;right:0;perspective:1600px}
    .fo{position:absolute;border-radius:22px;background:linear-gradient(160deg,#FBF6EA,#EFE6D2);box-shadow:0 26px 50px rgba(0,0,0,.38),inset 0 0 0 2px rgba(255,255,255,.6);
        display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;padding:30px 6% 26px;transform-style:preserve-3d;backface-visibility:hidden}
    .fo::after{content:"";position:absolute;inset:14px;border:1.5px solid rgba(60,45,25,.14);border-radius:14px;pointer-events:none}
    .fo svg{flex:none;overflow:visible;margin-top:4%}
    .fo b{font-family:"PalcoSerif";font-style:italic;font-weight:600;color:#2a2219;line-height:1;white-space:nowrap}
    .fo i{position:absolute;top:22px;left:26px;font-family:"PalcoSans";font-style:normal;font-weight:800;font-size:20px;letter-spacing:.2em;color:rgba(42,34,25,.45)}`);
  // objetos: forma base pintada com gradiente radial da marca + reflexo branco + sombra no chão
  const g = id => `<defs><radialGradient id="${id}" cx="35%" cy="30%" r="75%"><stop offset="0" stop-color="#fff"/>
      <stop offset=".22" stop-color="color-mix(in srgb, var(--dest) 55%, #fff)"/><stop offset=".7" stop-color="var(--dest)"/>
      <stop offset="1" stop-color="color-mix(in srgb, var(--dest) 45%, #000)"/></radialGradient></defs>
      <ellipse cx="100" cy="190" rx="62" ry="10" fill="rgba(40,30,20,.18)"/>`;
  const brilho = (x, y, s = 1) => `<ellipse cx="${x}" cy="${y}" rx="${16 * s}" ry="${9 * s}" fill="#fff" opacity=".85" transform="rotate(-30 ${x} ${y})"/>`;
  const OBJ = {
    esfera: f => `<circle cx="100" cy="100" r="74" fill="url(#${f})"/>${brilho(72, 66, 1.3)}`,
    moeda: f => `<ellipse cx="100" cy="106" rx="70" ry="74" fill="color-mix(in srgb, var(--dest) 50%, #000)"/><ellipse cx="92" cy="100" rx="70" ry="74" fill="url(#${f})"/>
      <ellipse cx="92" cy="100" rx="48" ry="52" fill="none" stroke="rgba(255,255,255,.55)" stroke-width="6"/><text x="92" y="122" text-anchor="middle" font-family="PalcoSans" font-weight="900" font-size="64" fill="rgba(255,255,255,.8)">$</text>${brilho(64, 58)}`,
    cubo: f => `<path d="M100 30 L165 65 L100 100 L35 65Z" fill="color-mix(in srgb, var(--dest) 40%, #fff)"/><path d="M35 65 L100 100 L100 175 L35 140Z" fill="url(#${f})"/>
      <path d="M165 65 L100 100 L100 175 L165 140Z" fill="color-mix(in srgb, var(--dest) 60%, #000)"/>${brilho(80, 60, .8)}`,
    estrela: f => `<path d="M100 22 L122 76 L180 80 L135 117 L150 174 L100 142 L50 174 L65 117 L20 80 L78 76Z" fill="url(#${f})" stroke="color-mix(in srgb, var(--dest) 50%, #000)" stroke-width="4" stroke-linejoin="round"/>${brilho(84, 70)}`,
    raio: f => `<path d="M118 18 L50 108 L94 108 L76 182 L152 84 L106 84Z" fill="url(#${f})" stroke="color-mix(in srgb, var(--dest) 50%, #000)" stroke-width="4" stroke-linejoin="round"/>${brilho(92, 64, .8)}`,
    coracao: f => `<path d="M100 172 C 30 120 22 78 46 52 C 68 30 94 40 100 62 C 106 40 132 30 154 52 C 178 78 170 120 100 172Z" fill="url(#${f})"/>${brilho(62, 66)}`,
    chave: f => `<circle cx="70" cy="80" r="44" fill="url(#${f})"/><circle cx="70" cy="80" r="18" fill="#F3EBDA"/>
      <path d="M104 96 L170 150 L158 164 L146 154 L136 166 L124 156 L134 144 L94 110Z" fill="url(#${f})"/>${brilho(54, 56, .8)}`,
    lampada: f => `<path d="M100 22 C 54 22 34 58 40 90 C 46 120 72 128 76 150 L124 150 C 128 128 154 120 160 90 C 166 58 146 22 100 22Z" fill="url(#${f})"/>
      <rect x="76" y="152" width="48" height="14" rx="5" fill="#8d8a84"/><rect x="80" y="168" width="40" height="12" rx="5" fill="#6f6c66"/>
      <path d="M86 140 L92 100 L100 116 L108 100 L114 140" fill="none" stroke="rgba(255,255,255,.75)" stroke-width="5" stroke-linejoin="round"/>${brilho(72, 56, 1.1)}`,
  };
  const palco = C.el("div", "fo-palco"); palco.style.top = "0px"; palco.style.height = H + "px";
  const x0 = (W - (n * fw + (n - 1) * gap)) / 2, y = Math.max(S.topo, r[1] - 40 - fh), tl = C.tl, fichas = [];
  itens.forEach((x, i) => {
    const id = `fo-g${i}`, obj = OBJ[x.objeto] || OBJ.esfera;
    const f = C.el("div", "fo", palco, `<i>0${i + 1}</i><svg viewBox="0 0 200 200">${g(id)}${obj(id)}</svg><b>${C.esc(x.rotulo || "")}</b>`);
    const rot = (i - (n - 1) / 2) * 4;
    Object.assign(f.style, {left: x0 + i * (fw + gap) + "px", top: y + (i % 2 ? 18 : 0) + "px", width: fw + "px", height: fh + "px"});
    const sv = f.querySelector("svg"), lado = Math.round(Math.min(fw * .74, fh * .5)); sv.style.width = sv.style.height = lado + "px";
    f.querySelector("b").style.fontSize = Math.round(Math.min(fw / Math.max(4, (x.rotulo || "").length) * 1.5, fh * .12)) + "px";
    const em = typeof x.em === "number" ? x.em : it.de + .1 + i * .6;
    tl.set(f, {opacity: 0, rotationY: -180, y: 80, rotation: rot * 3}, 0)
      .to(f, {opacity: 1, duration: .12}, em)
      .to(f, {rotationY: 0, y: 0, rotation: rot, duration: .7, ease: "back.out(1.6)"}, em)
      .fromTo(f.querySelector("svg"), {scale: .6, y: 20}, {scale: 1, y: 0, duration: .55, ease: "back.out(2.4)"}, em + .25)
      .to(f.querySelector("svg"), {y: -8, duration: .9, ease: "sine.inOut", yoyo: true, repeat: 3}, em + .8);
    fichas.push(f);
  });
  tl.to(fichas, {rotationY: 90, opacity: 0, duration: .35, stagger: .05, ease: "power2.in"}, Math.max(it.de + 1, it.ate - .45));
};
