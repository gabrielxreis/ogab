// BROLL · link vira evento na agenda: balão de chat com um link; o cursor clica, a agenda da semana (genérica) sobe no lugar
// do chat e o evento cai no dia e hora certos, na cor da marca. Fora do rosto.
ESTILO["chat-agenda"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, wN = 960, hN = 540, en = P.lingua === "en";
  C.css("chat-agenda", `
    .ca{position:absolute;transform-origin:50% 0}
    .ca .cd{position:absolute;inset:0;border-radius:34px;background:#151619;border:1.5px solid rgba(255,255,255,.12);overflow:hidden;
        box-shadow:0 28px 70px rgba(0,0,0,.5);font-family:"PalcoSans";color:#fff}
    .ca .ch{position:absolute;inset:0;padding:40px 36px}
    .ca .bo{max-width:80%;background:#25272c;border-radius:30px 30px 30px 8px;padding:22px 28px;font-weight:700;font-size:32px;line-height:1.3}
    .ca .lk{margin-top:18px;display:flex;align-items:center;gap:18px;background:#1d1f23;border:1.5px solid rgba(255,255,255,.12);border-radius:22px;
        padding:18px 22px;width:fit-content;font-weight:800;font-size:28px}
    .ca .lk i{width:56px;height:56px;border-radius:14px;background:var(--dest);display:grid;place-items:center;flex:none}
    .ca .lk u{text-decoration-color:var(--dest);text-decoration-thickness:3px;text-underline-offset:6px}
    .ca .ag{position:absolute;inset:0;background:#f7f7f8;color:#17191d;padding:26px 30px}
    .ca .mes{font-weight:800;font-size:30px;margin-bottom:14px}
    .ca .gr{position:relative;display:grid;grid-template-columns:90px repeat(5,1fr);grid-template-rows:44px repeat(4,90px);font-weight:700;font-size:22px;color:#8a8f97}
    .ca .gr div{border-top:2px solid #e8e9ec;padding:6px 8px}.ca .gr .dd{border-top:none;text-align:center;font-size:22px;letter-spacing:.1em}
    .ca .ev{position:absolute;border-radius:14px;background:var(--dest);color:#111;padding:10px 14px;font-weight:800;font-size:24px;line-height:1.15;
        box-shadow:0 10px 24px rgba(0,0,0,.2)}.ca .ev small{display:block;font-size:19px;opacity:.75}
    .ca .cu{position:absolute;filter:drop-shadow(0 4px 6px rgba(0,0,0,.4))}`);
  const r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const zc = [S.topo, r[1] - 36], zb = [r[3] + 36, H - S.baixo], z = (zb[1] - zb[0]) >= (zc[1] - zc[0]) ? zb : zc;
  const s = Math.min(1, (z[1] - z[0]) / hN, (W - 2 * S.lado) / wN);
  const b = C.el("div", "ca");
  Object.assign(b.style, {width: wN + "px", height: hN + "px", left: (W - wN) / 2 + "px", top: (z[0] + ((z[1] - z[0]) - hN * s) / 2) + "px",
                          transform: `scale(${s})`});
  const dias = en ? ["MON", "TUE", "WED", "THU", "FRI"] : ["SEG", "TER", "QUA", "QUI", "SEX"], horas = ["9:00", "11:00", "14:00", "16:00"];
  const cd = C.el("div", "cd", b, `<div class="ch"><div class="bo">${C.esc(it.mensagem || "")}</div>
      <div class="lk"><i><svg width="30" height="30" viewBox="0 0 30 30"><rect x="4" y="6" width="22" height="20" rx="4" fill="none" stroke="#111" stroke-width="3"/>
        <path d="M4 12h22M10 3v6M20 3v6" stroke="#111" stroke-width="3" stroke-linecap="round"/></svg></i><u>${C.esc(it.link || "")}</u></div></div>
    <div class="ag"><div class="mes">${en ? "This week" : "Esta semana"}</div><div class="gr"><div class="dd"></div>${dias.map(x => `<div class="dd">${x}</div>`).join("")}
      ${horas.map(h => `<div>${h}</div>` + "<div></div>".repeat(5)).join("")}</div></div>`);
  const ch = cd.querySelector(".ch"), ag = cd.querySelector(".ag"), lk = cd.querySelector(".lk"), gr = cd.querySelector(".gr");
  // evento: coluna do dia, linha da hora mais próxima (grade de medidas fixas: 90 px de hora + 5 colunas iguais)
  const dia = Math.max(0, Math.min(4, it.dia ?? 3)), hh = parseInt(it.hora || "14", 10), lin = hh < 10 ? 0 : hh < 13 ? 1 : hh < 15 ? 2 : 3;
  const colw = (wN - 60 - 90) / 5, ev = C.el("div", "ev", gr, `${C.esc(it.evento || "")}<small>${C.esc(it.hora || "")}</small>`);
  Object.assign(ev.style, {left: (90 + dia * colw + 6) + "px", top: (44 + lin * 90 + 6) + "px", width: (colw - 12) + "px", height: "78px"});
  const cu = C.el("div", "cu", cd, `<svg viewBox="0 0 54 66" width="54" height="66"><path d="M4 3 L4 52 L17 40 L26 61 L35 57 L26 37 L44 37 Z"
    fill="#111" stroke="#fff" stroke-width="3.5" stroke-linejoin="round"/></svg>`);
  const tl = C.tl, d = it.de, f = it.ate, tc = d + 1.25, sai = Math.max(tc + 1.3, f - .45);
  tl.set(cd, {y: 80, opacity: 0}, 0).set(lk, {opacity: 0, y: 24}, 0).set(ag, {yPercent: 100}, 0).set(ev, {y: -160, opacity: 0}, 0)
    .set(cu, {left: wN * .75, top: hN + 20}, 0)
    .to(cd, {y: 0, opacity: 1, duration: .55, ease: "expo.out"}, d)
    .to(lk, {opacity: 1, y: 0, duration: .4, ease: "power3.out"}, d + .3)
    .to(cu, {left: 300, top: 200, duration: .6, ease: "power3.inOut"}, d + .6)
    .to(lk, {scale: .96, duration: .1, yoyo: true, repeat: 1, ease: "power1.inOut"}, tc)
    .to(ag, {yPercent: 0, duration: .55, ease: "expo.out"}, tc + .15)
    .to(ch, {opacity: .0, duration: .3}, tc + .15)
    .to(cu, {opacity: 0, duration: .2}, tc + .15)
    .to(ev, {y: 0, opacity: 1, duration: .5, ease: "power3.out"}, tc + .6)
    .to(cd, {y: -40, opacity: 0, duration: .4, ease: "power2.in"}, sai);
};
