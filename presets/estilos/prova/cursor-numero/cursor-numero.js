// PROVA · cursor no número: cartão com o print (do cliente) ou uma tabela ilustrada; o cursor desliza até o número, clica
// (anel na cor da marca) e a célula fica marcada; rótulo pequeno de fonte no canto. Fora do rosto.
ESTILO["cursor-numero"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, wN = 940, nl = (it.linhas || []).length, hN = it.imagem ? 440 : 54 + 74 + 46 + nl * 66 + 34;
  C.css("cursor-numero", `
    .cn{position:absolute;transform-origin:50% 0}
    .cn .cd{position:absolute;inset:0;border-radius:24px;background:#fff;overflow:hidden;box-shadow:0 26px 70px rgba(0,0,0,.42);font-family:"PalcoSans";color:#17191d}
    .cn .cd > img{width:100%;height:100%;object-fit:cover;display:block}
    .cn .bar{height:54px;background:#f1f2f4;display:flex;align-items:center;gap:10px;padding:0 22px}.cn .bar i{width:14px;height:14px;border-radius:50%;background:#d5d8dd}
    .cn .ti{height:74px;display:flex;align-items:center;font-weight:800;font-size:32px;padding:6px 34px 0}
    .cn table{width:calc(100% - 68px);margin:0 34px;border-collapse:collapse;font-weight:700;font-size:30px}
    .cn th{height:46px;font-size:22px;letter-spacing:.14em;color:#8a8f97;text-align:left;padding:0 12px;border-bottom:2px solid #eceef1}
    .cn td{height:66px;padding:0 12px;border-bottom:2px solid #f2f3f5}
    .cn table,.cn tr{height:auto}.cn th,.cn td{box-sizing:border-box}.cn td:last-child,.cn th:last-child{text-align:right}
    .cn .mk{position:absolute;border:4px solid var(--dest);border-radius:12px;background:color-mix(in srgb, var(--dest) 18%, transparent)}
    .cn .an{position:absolute;width:90px;height:90px;margin:-45px 0 0 -45px;border-radius:50%;border:5px solid var(--dest)}
    .cn .cu{position:absolute;width:54px;height:66px;filter:drop-shadow(0 4px 6px rgba(0,0,0,.35))}
    .cn .fo{position:absolute;right:22px;top:9px;background:rgba(14,14,16,.82);color:#fff;border-radius:20px;padding:8px 18px;font-weight:700;font-size:22px}`);
  const r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const zc = [S.topo, r[1] - 36], zb = [r[3] + 36, H - S.baixo], z = (zb[1] - zb[0]) >= (zc[1] - zc[0]) ? zb : zc;
  const s = Math.min(1, (z[1] - z[0]) / hN, (W - 2 * S.lado) / wN);
  const b = C.el("div", "cn");
  Object.assign(b.style, {width: wN + "px", height: hN + "px", left: (W - wN) / 2 + "px", top: (z[0] + ((z[1] - z[0]) - hN * s) / 2) + "px",
                          transform: `scale(${s})`});
  const cd = C.el("div", "cd", b);
  let ax, ay, mk = null;
  if (it.imagem) {
    C.el("img", null, cd).src = it.imagem;
    const a = it.alvo || [.5, .5]; ax = a[0] * wN; ay = a[1] * hN;
  } else {   // tabela ilustrada (fictícia): linhas de altura fixa para o cursor achar a célula sem medir
    const cols = it.colunas || [], lin = it.linhas || [], k = Math.min(lin.length - 1, Math.max(0, it.destaque ?? lin.length - 1));
    cd.innerHTML = `<div class="bar"><i></i><i></i><i></i></div><div class="ti">${C.esc(it.titulo || "")}</div>
      <table><tr>${cols.map(c => `<th>${C.esc(String(c).toUpperCase())}</th>`).join("")}</tr>
      ${lin.map(l => `<tr>${l.map(c => `<td>${C.esc(c)}</td>`).join("")}</tr>`).join("")}</table>`;
    const yh = 54 + 74 + 46, rh = 66, y = yh + k * rh;   // barra + título + cabeçalho; altura de cada linha
    mk = C.el("div", "mk", cd); Object.assign(mk.style, {left: (wN - 34 - 300) + "px", top: (y - 2) + "px", width: "300px", height: (rh + 4) + "px"});
    ax = wN - 34 - 120; ay = y + rh / 2;
  }
  const an = C.el("div", "an", cd); Object.assign(an.style, {left: ax + "px", top: ay + "px"});
  const cu = C.el("div", "cu", cd, `<svg viewBox="0 0 54 66" width="54" height="66"><path d="M4 3 L4 52 L17 40 L26 61 L35 57 L26 37 L44 37 Z"
    fill="#111" stroke="#fff" stroke-width="3.5" stroke-linejoin="round"/></svg>`);
  if (it.fonte) C.el("div", "fo", cd, C.esc(it.fonte));
  const tl = C.tl, d = it.de, f = it.ate, sai = Math.max(d + 1.8, f - .45);
  tl.set(cd, {y: 80, opacity: 0}, 0).set(cu, {left: wN * .2, top: hN + 20}, 0).set(an, {scale: .3, opacity: 0}, 0)
    .to(cd, {y: 0, opacity: 1, duration: .55, ease: "expo.out"}, d)
    .to(cu, {left: ax - 4, top: ay - 3, duration: .9, ease: "power3.inOut"}, d + .4)
    .to(cu, {scale: .86, duration: .1, yoyo: true, repeat: 1, ease: "power1.inOut"}, d + 1.3)
    .to(an, {scale: 1.2, opacity: 1, duration: .25, ease: "power2.out"}, d + 1.35).to(an, {scale: 1.6, opacity: 0, duration: .35, ease: "power2.out"}, d + 1.6);
  if (mk) tl.set(mk, {opacity: 0, scale: .9}, 0).to(mk, {opacity: 1, scale: 1, duration: .3, ease: "power3.out"}, d + 1.38);
  tl.to(cd, {y: -40, opacity: 0, duration: .4, ease: "power2.in"}, sai);
};
