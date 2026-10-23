// BROLL · link abre a planilha: balão de chat com link de pasta; o cursor clica, a pasta (desenhada) abre a tampa e a planilha
// genérica sobe de dentro dela, com as linhas entrando uma a uma (a primeira coluna na cor da marca). Fora do rosto.
ESTILO["chat-planilha"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, wN = 960, hN = 540;
  C.css("chat-planilha", `
    .cl{position:absolute;transform-origin:50% 0}
    .cl .cd{position:absolute;inset:0;border-radius:34px;background:#151619;border:1.5px solid rgba(255,255,255,.12);overflow:hidden;
        box-shadow:0 28px 70px rgba(0,0,0,.5);font-family:"PalcoSans";color:#fff;perspective:900px}
    .cl .ch{position:absolute;inset:0;padding:40px 36px}
    .cl .bo{max-width:80%;background:#25272c;border-radius:30px 30px 30px 8px;padding:22px 28px;font-weight:700;font-size:32px;line-height:1.3}
    .cl .lk{margin-top:18px;display:flex;align-items:center;gap:18px;background:#1d1f23;border:1.5px solid rgba(255,255,255,.12);border-radius:22px;
        padding:18px 22px;width:fit-content;font-weight:800;font-size:28px}
    .cl .lk i{width:56px;height:56px;border-radius:14px;background:var(--dest);display:grid;place-items:center;flex:none}
    .cl .lk u{text-decoration-color:var(--dest);text-decoration-thickness:3px;text-underline-offset:6px}
    .cl .pa{position:absolute;left:50%;top:46%;width:260px;height:190px;margin:-95px 0 0 -130px}
    .cl .pa .fu{position:absolute;inset:26px 0 0;border-radius:18px;background:#d9b65a}
    .cl .pa .ab{position:absolute;left:0;top:0;width:110px;height:50px;border-radius:14px 14px 0 0;background:#c9a447}
    .cl .pa .ta{position:absolute;inset:46px 0 0;border-radius:18px;background:#ecc969;transform-origin:50% 100%}
    .cl .pa b{position:absolute;left:0;right:0;top:208px;text-align:center;font-weight:800;font-size:28px;white-space:nowrap}
    .cl .pl{position:absolute;left:34px;right:34px;top:34px;bottom:34px;background:#fff;border-radius:16px;color:#17191d;overflow:hidden}
    .cl .pl .tt{height:58px;display:flex;align-items:center;gap:12px;padding:0 22px;background:#f1f2f4;font-weight:800;font-size:24px}
    .cl .pl .tt i{width:22px;height:22px;border-radius:5px;background:var(--dest)}
    .cl .rw{display:grid;grid-template-columns:120px 1fr 200px;border-bottom:2px solid #eef0f2;font-weight:700;font-size:27px}
    .cl .rw span{padding:16px 20px;border-right:2px solid #eef0f2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .cl .rw.h{font-size:20px;letter-spacing:.14em;color:#8a8f97;background:#fafafb}.cl .rw:not(.h) span:first-child{color:#111;background:color-mix(in srgb, var(--dest) 30%, #fff)}
    .cl .cu{position:absolute;filter:drop-shadow(0 4px 6px rgba(0,0,0,.4))}`);
  const r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const zc = [S.topo, r[1] - 36], zb = [r[3] + 36, H - S.baixo], z = (zb[1] - zb[0]) >= (zc[1] - zc[0]) ? zb : zc;
  const s = Math.min(1, (z[1] - z[0]) / hN, (W - 2 * S.lado) / wN);
  const b = C.el("div", "cl");
  Object.assign(b.style, {width: wN + "px", height: hN + "px", left: (W - wN) / 2 + "px", top: (z[0] + ((z[1] - z[0]) - hN * s) / 2) + "px",
                          transform: `scale(${s})`});
  const cols = it.colunas || [], lin = it.linhas || [];
  const cd = C.el("div", "cd", b, `<div class="ch"><div class="bo">${C.esc(it.mensagem || "")}</div>
      <div class="lk"><i><svg width="30" height="26" viewBox="0 0 30 26"><path d="M2 5a3 3 0 0 1 3-3h7l3 4h10a3 3 0 0 1 3 3v12a3 3 0 0 1-3 3H5a3 3 0 0 1-3-3z"
        fill="none" stroke="#111" stroke-width="3" stroke-linejoin="round"/></svg></i><u>${C.esc(it.link || "")}</u></div></div>
    <div class="pa"><div class="ab"></div><div class="fu"></div><div class="ta"></div><b>${C.esc(it.pasta || "")}</b></div>
    <div class="pl"><div class="tt"><i></i>${C.esc(it.pasta || "")}</div>
      <div class="rw h">${cols.map(c => `<span>${C.esc(String(c).toUpperCase())}</span>`).join("")}</div>
      ${lin.map(l => `<div class="rw">${l.map(c => `<span>${C.esc(c)}</span>`).join("")}</div>`).join("")}</div>`);
  const ch = cd.querySelector(".ch"), lk = cd.querySelector(".lk"), pa = cd.querySelector(".pa"), ta = pa.querySelector(".ta"), pl = cd.querySelector(".pl");
  const rows = [...pl.querySelectorAll(".rw:not(.h)")];
  const cu = C.el("div", "cu", cd, `<svg viewBox="0 0 54 66" width="54" height="66"><path d="M4 3 L4 52 L17 40 L26 61 L35 57 L26 37 L44 37 Z"
    fill="#111" stroke="#fff" stroke-width="3.5" stroke-linejoin="round"/></svg>`);
  const tl = C.tl, d = it.de, f = it.ate, tc = d + 1.2, sai = Math.max(tc + 2, f - .45);
  tl.set(cd, {y: 80, opacity: 0}, 0).set(lk, {opacity: 0, y: 24}, 0).set(pa, {scale: .6, opacity: 0}, 0).set(ta, {rotationX: 0}, 0)
    .set(pl, {y: 120, scale: .7, opacity: 0}, 0).set(rows, {opacity: 0, x: -30}, 0).set(cu, {left: wN * .75, top: hN + 20}, 0)
    .to(cd, {y: 0, opacity: 1, duration: .55, ease: "expo.out"}, d)
    .to(lk, {opacity: 1, y: 0, duration: .4, ease: "power3.out"}, d + .3)
    .to(cu, {left: 300, top: 200, duration: .6, ease: "power3.inOut"}, d + .55)
    .to(lk, {scale: .96, duration: .1, yoyo: true, repeat: 1, ease: "power1.inOut"}, tc)
    .to([ch, cu], {opacity: 0, duration: .25}, tc + .15)
    .to(pa, {scale: 1, opacity: 1, duration: .4, ease: "expo.out"}, tc + .15)
    .to(ta, {rotationX: -55, duration: .35, ease: "power2.out"}, tc + .5)
    .to(pl, {y: 0, scale: 1, opacity: 1, duration: .5, ease: "expo.out"}, tc + .75)
    .to(pa, {opacity: 0, duration: .2}, tc + .8)
    .to(rows, {opacity: 1, x: 0, duration: .35, stagger: .22, ease: "power3.out"}, tc + 1.05)
    .to(cd, {y: -40, opacity: 0, duration: .4, ease: "power2.in"}, sai);
};
