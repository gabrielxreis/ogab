// GANCHO · pergunta + logos: a pergunta falada fica no topo desde o primeiro quadro; os logos pipocam juntos na palavra-chave e tudo sai no corte.
ESTILO["pergunta-logos"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const norm = s => String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]/g, "");
  C.css("pergunta-logos", `
    .pq{position:absolute;text-wrap:balance;left:${S.lado + 40}px;right:${S.lado + 40}px;text-align:center;font-family:"PalcoSans";font-weight:800;
        line-height:1.1;letter-spacing:-.02em;color:#fff;text-shadow:0 5px 22px rgba(0,0,0,.55)}
    .pq-l{position:absolute;left:0;right:0;display:flex;justify-content:center}
    .pq-i{background:#fff;border-radius:28%;display:grid;place-items:center;overflow:hidden;box-shadow:0 16px 40px rgba(0,0,0,.35);
        font-family:"PalcoSans";font-weight:900;color:#15161a;letter-spacing:-.03em}
    .pq-i img{width:78%;height:78%;object-fit:contain}`);
  const perg = String(it.pergunta || ""), fs = perg.length <= 30 ? 70 : perg.length <= 56 ? 60 : 50;
  const linhas = Math.ceil(perg.length * fs * .56 / (W - 2 * (S.lado + 40))), qa = linhas * fs * 1.1;
  const q = C.el("div", "pq", null, C.esc(perg)); Object.assign(q.style, {top: S.topo + "px", fontSize: fs + "px"});
  const logos = (it.logos || []).slice(0, 5), lt = S.topo + qa + 36;
  const lado = Math.max(80, Math.min(170, r[1] - 30 - lt, (W - 2 * S.lado - 30 * (logos.length - 1)) / Math.max(1, logos.length)));
  const fila = C.el("div", "pq-l"); Object.assign(fila.style, {top: lt + "px", gap: "30px"});
  const ics = logos.map(x => {
    const nome = String(x.nome || ""), e = C.el("div", "pq-i", fila, x.logo ? `<img src="${C.esc(x.logo)}">` : C.esc(nome));
    Object.assign(e.style, {width: lado + "px", height: lado + "px", fontSize: Math.min(lado * .3, lado * 1.5 / Math.max(3, nome.length)) + "px"});
    return e;
  });
  const d = it.de, f = it.ate, ch = norm(it.chave || "");
  const p = ch && (P.palavras || []).find(w => w.ini >= d - .05 && w.ini < f && norm(w.w) === ch);
  const em = p ? p.ini : typeof it.em === "number" ? it.em : d + .6;
  C.tl.set([q, fila], {opacity: 0}, 0).set([q, fila], {opacity: 1}, d)
    .fromTo(q, {y: 14}, {y: 0, duration: .25, ease: "power3.out"}, d)
    .set(ics, {scale: 0, opacity: 0}, 0)
    .to(ics, {scale: 1, opacity: 1, duration: .45, stagger: .06, ease: "expo.out"}, em)
    .set([q, fila], {opacity: 0}, f);   // sai seco no corte
};
