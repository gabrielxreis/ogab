// BATIDA · cronômetro em anel: disco de vidro desfocado com anel na cor da marca que enche enquanto o número sobe até o
// valor dito (~2 s), dá um pulso no fim e some. Fica no meio do maior espaço livre (acima da cabeça ou abaixo do queixo).
ESTILO["timer-anel"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, R = 150, CI = 2 * Math.PI * R;
  C.css("timer-anel", `
    .ta{position:absolute;width:360px;height:360px;transform-origin:50% 50%}
    .ta .vd{position:absolute;inset:22px;border-radius:50%;background:rgba(255,255,255,.12);backdrop-filter:blur(26px);-webkit-backdrop-filter:blur(26px);
        border:1.5px solid rgba(255,255,255,.32);box-shadow:0 24px 60px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.4)}
    .ta svg{position:absolute;inset:0;transform:rotate(-90deg)}
    .ta .nu{position:absolute;left:0;right:0;top:96px;text-align:center;font-weight:900;font-size:124px;line-height:1;letter-spacing:-.04em;color:#fff;
        text-shadow:0 4px 18px rgba(0,0,0,.35)}
    .ta .nu b{position:absolute;left:0;right:0;font-weight:900;opacity:0}
    .ta .un{position:absolute;left:0;right:0;top:236px;text-align:center;font-weight:700;font-size:28px;letter-spacing:.2em;color:rgba(255,255,255,.85)}`);
  const n = Math.max(1, Math.round(Number(it.numero) || 10)), r = C.rostoEm(it.de) || [W * .3, H * .3, W * .7, H * .55];
  const cima = r[1] - 30 - S.topo, baixo = H - S.baixo - (r[3] + 40);
  const zona = cima >= baixo ? [S.topo, r[1] - 30] : [r[3] + 40, H - S.baixo], esc = Math.min(1, (zona[1] - zona[0]) / 360);
  const e = C.el("div", "ta");
  Object.assign(e.style, {left: (W - 360) / 2 + "px", top: ((zona[0] + zona[1]) / 2 - 180) + "px"});
  // um número por valor (o render salta de quadro em quadro: nada de onUpdate); até 60 passos, depois pula de vários em vários
  const passo = Math.ceil(n / 60), vals = []; for (let v = 0; v < n; v += passo) vals.push(v); vals.push(n);
  e.innerHTML = `<div class="vd"></div><svg width="360" height="360"><circle cx="180" cy="180" r="${R}" fill="none" stroke="rgba(255,255,255,.2)" stroke-width="16"/>
    <circle class="pg" cx="180" cy="180" r="${R}" fill="none" stroke="var(--dest)" stroke-width="16" stroke-linecap="round"
      stroke-dasharray="${CI}" stroke-dashoffset="${CI}"/></svg>
    <div class="nu">${vals.map(v => `<b>${v}</b>`).join("")}</div><div class="un">${C.esc(String(it.unidade || "").toUpperCase())}</div>`;
  const tl = C.tl, d = it.de, f = it.ate, conta = 2, bs = [...e.querySelectorAll(".nu b")], pg = e.querySelector(".pg");
  tl.set(e, {opacity: 0, scale: .6 * esc}, 0)
    .to(e, {opacity: 1, scale: esc, duration: .5, ease: "back.out(1.6)"}, d)
    .to(pg, {attr: {"stroke-dashoffset": 0}, duration: conta, ease: "power1.inOut"}, d + .35);
  const ease = gsap.parseEase("power1.inOut");   // o número segue a mesma curva do anel
  const quando = vals.map((v, i) => {   // tempo em que o anel passa por v (busca binária na curva)
    if (!i) return d;
    let a = 0, b = 1; for (let k = 0; k < 30; k++) { const m = (a + b) / 2; if (ease(m) < v / n) a = m; else b = m; }
    return d + .35 + b * conta;
  });
  // troca por tweens curtíssimos (set no tempo 0 se desfaz quando o render volta ao início)
  bs.forEach((b, i) => {
    tl.to(b, {opacity: 1, duration: .001}, quando[i]);
    if (i < bs.length - 1) tl.to(b, {opacity: 0, duration: .001}, quando[i + 1]);
  });
  tl.to(e, {scale: esc * 1.08, duration: .14, yoyo: true, repeat: 1, ease: "power1.inOut"}, d + .35 + conta)
    .to(e, {opacity: 0, scale: esc * .85, duration: .35, ease: "power2.in"}, Math.max(d + conta + .7, f - .35));
};
