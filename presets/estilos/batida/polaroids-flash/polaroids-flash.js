// BATIDA · polaroids com flash: cada foto (campo imagens, até 4) cai girando como polaroid e pousa com um flash de câmera
// (clarão branco curto em volta dela). Vagas fora do rosto: laterais da cabeça e faixa acima. Sem foto, desenha uma cena
// ilustrada no lugar (só para prévia; no vídeo real as fotos vêm do cliente).
ESTILO["polaroids-flash"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro;
  C.css("polaroids-flash", `
    .pf{position:absolute;background:#fbfaf7;padding:16px 16px 0;border-radius:6px;box-shadow:0 22px 50px rgba(0,0,0,.45)}
    .pf .ft{width:100%;background:#222 center/cover no-repeat;overflow:hidden;position:relative}
    .pf .ft img{width:100%;height:100%;object-fit:cover;display:block}
    .pf .lg{height:var(--rod);display:grid;place-items:center;font-family:"PalcoHand","PalcoSans";font-weight:700;color:#2a2a2a}
    .pf .fl{position:absolute;inset:-60%;border-radius:50%;background:radial-gradient(circle,#fff 0,rgba(255,255,255,.85) 30%,rgba(255,255,255,0) 70%);opacity:0;pointer-events:none}
    .pf-tela{position:absolute;inset:0;background:#fff;opacity:0;pointer-events:none}`);
  const fallback = [   // cenas ilustradas: céu + sol + morros (sem gente)
    "linear-gradient(#f8b26a,#f4797f 55%,#5a3a6b 56%,#3a2650)", "linear-gradient(#7fd3f7,#cdeefd 58%,#5fae6b 59%,#3f8a4e)",
    "linear-gradient(#2b3a67,#6c5b9e 60%,#1f2a44 61%,#141b2e)", "linear-gradient(#ffd89b,#f6c26b 50%,#c98b4a 51%,#8a5a32)"];
  const imgs = (it.imagens || []).filter(Boolean), leg = it.legendas || [], n = Math.min(4, Math.max(imgs.length, imgs.length ? 1 : 3));
  const r = C.rostoEm(it.de) || [W * .3, H * .3, W * .7, H * .55], m = 30;
  const vagas = [], esq = r[0] - m - S.lado, dir = W - S.lado - m - r[2], cima = r[1] - m - S.topo;
  // laterais (largura que couber, até 360) na altura dos olhos; acima da cabeça, uma ou duas
  if (esq >= 200) vagas.push({x: S.lado, y: r[1] + 40, w: Math.min(360, esq), rot: -8});
  if (dir >= 200) vagas.push({x: W - S.lado - Math.min(360, dir), y: r[1] + 120, w: Math.min(360, dir), rot: 7});
  const wc = Math.min(330, cima / 1.25);
  if (wc >= 200) { vagas.push({x: W / 2 - wc - 10, y: S.topo, w: wc, rot: 5}); vagas.push({x: W / 2 + 10, y: S.topo + 20, w: wc, rot: -4}); }
  if (!vagas.length) vagas.push({x: (W - 360) / 2, y: H - S.baixo - 450, w: 360, rot: -3});
  const tela = C.el("div", "pf-tela"), tl = C.tl, d = it.de, f = it.ate, fotos = [];
  for (let i = 0; i < n; i++) {
    const v = vagas[i % vagas.length], fw = v.w - 32, rod = Math.round(fw * .28);
    const p = C.el("div", "pf"); p.style.cssText += `left:${v.x}px;top:${v.y}px;width:${v.w}px;--rod:${rod}px`;
    p.innerHTML = `<div class="ft" style="height:${fw}px;${imgs[i] ? "" : "background:" + fallback[i % 4]}">${imgs[i] ? `<img src="${C.esc(imgs[i])}">` :
      `<i style="position:absolute;left:62%;top:22%;width:22%;height:22%;border-radius:50%;background:rgba(255,255,255,.75)"></i>`}</div>
      <div class="lg" style="font-size:${Math.round(rod * .5)}px">${C.esc(leg[i] || "")}</div><i class="fl"></i>`;
    fotos.push(p);
    const em = d + .15 + i * .55, fl = p.querySelector(".fl"), ft = p.querySelector(".ft");
    tl.fromTo(p, {opacity: 0, y: -260, rotation: v.rot * 4, scale: 1.15}, {opacity: 1, y: 0, rotation: v.rot, scale: 1, duration: .5, ease: "power3.in"}, em)
      .to(p, {y: -10, duration: .12, yoyo: true, repeat: 1, ease: "power1.out"}, em + .5)
      .fromTo(fl, {opacity: 0}, {opacity: 1, duration: .05, immediateRender: false}, em + .48)
      .to(fl, {opacity: 0, duration: .35, ease: "power2.out"}, em + .55)
      .fromTo(tela, {opacity: 0}, {opacity: .22, duration: .04, immediateRender: false}, em + .48)
      .to(tela, {opacity: 0, duration: .25}, em + .52)
      .fromTo(ft, {filter: "brightness(2.2) saturate(.3)"}, {filter: "brightness(1) saturate(1)", duration: .7, ease: "power2.out", immediateRender: false}, em + .5);
  }
  tl.to(fotos, {opacity: 0, y: 80, rotation: "+=6", duration: .4, stagger: .05, ease: "power2.in"}, Math.max(d + .8 + n * .55, f - .45));
};
