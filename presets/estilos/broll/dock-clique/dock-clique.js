// BROLL · clique na barra de apps: barra de vidro escuro com ícones genéricos (inicial do nome); a vista aproxima do ícone alvo,
// o cursor clica, o ícone dá um pulo e a janela do app abre crescendo a partir dele. Fora do rosto.
ESTILO["dock-clique"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, wN = 960, hN = 460;
  C.css("dock-clique", `
    .dk{position:absolute;transform-origin:50% 0}
    .dk .cv{position:absolute;inset:0;overflow:hidden;border-radius:30px}
    .dk .mu{position:absolute;inset:0}
    .dk .bar{position:absolute;left:50%;bottom:36px;transform:translateX(-50%);display:flex;gap:18px;padding:16px 20px;border-radius:34px;
        background:rgba(28,29,33,.72);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border:1.5px solid rgba(255,255,255,.16);
        box-shadow:0 20px 50px rgba(0,0,0,.45)}
    .dk .ic{width:96px;height:96px;border-radius:24px;display:grid;place-items:center;font-family:"PalcoSans";font-weight:900;font-size:44px;overflow:hidden}
    .dk .ic img{width:100%;height:100%;object-fit:cover}
    .dk .pt{position:absolute;left:50%;bottom:-11px;width:8px;height:8px;margin-left:-4px;border-radius:50%;background:#fff}
    .dk .ja{position:absolute;left:60px;right:60px;top:24px;height:250px;border-radius:22px;background:#f6f6f7;overflow:hidden;
        box-shadow:0 24px 60px rgba(0,0,0,.45);font-family:"PalcoSans";color:#17191d}
    .dk .ja .tt{height:52px;background:#ebecef;display:flex;align-items:center;gap:10px;padding:0 20px;font-weight:800;font-size:22px}
    .dk .ja .tt i{width:14px;height:14px;border-radius:50%;background:#cfd2d7}.dk .ja .tt b{margin-left:14px}
    .dk .ja .ln{height:18px;border-radius:9px;background:#e4e5e9;margin:22px 26px 0}.dk .ja .ln.d{background:var(--dest);width:30%}
    .dk .cu{position:absolute;filter:drop-shadow(0 4px 6px rgba(0,0,0,.4))}`);
  const r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const zc = [S.topo, r[1] - 36], zb = [r[3] + 36, H - S.baixo], z = (zb[1] - zb[0]) >= (zc[1] - zc[0]) ? zb : zc;
  const s = Math.min(1, (z[1] - z[0]) / hN, (W - 2 * S.lado) / wN);
  const b = C.el("div", "dk");
  Object.assign(b.style, {width: wN + "px", height: hN + "px", left: (W - wN) / 2 + "px", top: (z[0] + ((z[1] - z[0]) - hN * s) / 2) + "px",
                          transform: `scale(${s})`});
  const apps = it.apps || [], k = Math.max(0, Math.min(apps.length - 1, it.alvo ?? 0));
  const tons = [["#E9E9EC", "#17191d"], ["#2B2D33", "#fff"], ["#C9CDD3", "#17191d"], ["#3A3D44", "#fff"]];
  const cv = C.el("div", "cv", b), mu = C.el("div", "mu", cv), bar = C.el("div", "bar", mu);
  const ics = apps.map((a, i) => {
    return C.el("div", "ic", bar, i === k && it.logo ? `<img src="${C.esc(it.logo)}">` : C.esc(String(a).slice(0, 1).toUpperCase()));
  });
  ics.forEach((e, i) => { const [bg, cor] = i === k ? ["var(--dest)", "#111"] : tons[i % tons.length]; Object.assign(e.style, {background: bg, color: cor}); });
  // posição do ícone alvo na barra (medidas fixas: 96 de ícone + 18 de vão + 20 de borda)
  const n = apps.length, bw = n * 96 + (n - 1) * 18 + 40, ix = (wN - bw) / 2 + 20 + k * 114 + 48, iy = hN - 36 - 16 - 48;
  mu.style.transformOrigin = `${ix}px ${iy}px`;
  const pt = C.el("i", "pt", ics[k]); ics[k].style.position = "relative"; ics[k].style.overflow = "visible";
  const ja = C.el("div", "ja", cv, `<div class="tt"><i></i><i></i><i></i><b>${C.esc(it.janela || "")}</b></div>
    <div class="ln d"></div><div class="ln" style="width:80%"></div><div class="ln" style="width:62%"></div><div class="ln" style="width:72%"></div>`);
  ja.style.transformOrigin = `${ix - 60}px ${iy - 24}px`;
  const cu = C.el("div", "cu", cv, `<svg viewBox="0 0 54 66" width="54" height="66"><path d="M4 3 L4 52 L17 40 L26 61 L35 57 L26 37 L44 37 Z"
    fill="#111" stroke="#fff" stroke-width="3.5" stroke-linejoin="round"/></svg>`);
  const tl = C.tl, d = it.de, f = it.ate, tc = d + 1.1, sai = Math.max(tc + 1.2, f - .45);
  tl.set(bar, {y: 160, opacity: 0}, 0).set(mu, {scale: 1}, 0).set(pt, {opacity: 0}, 0).set(ja, {scale: .05, opacity: 0}, 0)
    .set(cu, {left: wN * .85, top: hN + 20}, 0)
    .to(bar, {y: 0, opacity: 1, duration: .55, ease: "expo.out"}, d)
    .to(mu, {scale: 1.35, duration: .8, ease: "power2.inOut"}, d + .35)
    .to(cu, {left: ix + 6, top: iy - 2, duration: .6, ease: "power3.inOut"}, d + .45)
    .to(cu, {scale: .86, duration: .1, yoyo: true, repeat: 1, ease: "power1.inOut"}, tc)
    .to(ics[k], {y: -46, duration: .2, ease: "power2.out"}, tc + .08).to(ics[k], {y: 0, duration: .22, ease: "power2.in"}, tc + .28)
    .to(pt, {opacity: 1, duration: .2}, tc + .3)
    .to(cu, {opacity: 0, duration: .2}, tc + .3)
    .to(mu, {scale: 1, duration: .6, ease: "power2.inOut"}, tc + .45)
    .to(ja, {scale: 1, opacity: 1, duration: .55, ease: "expo.out"}, tc + .5)
    .to([bar, ja], {y: -40, opacity: 0, duration: .4, ease: "power2.in"}, sai);
};
