// EFEITO · sair da tela do celular: o vídeo da pessoa (C.P.video) encolhe para dentro de uma tela de celular arredondada,
// com a sala desfocada e escura em volta ("base" do estilo.json). Por cima, a silhueta (C.P.silhueta) com a MESMA escala e
// sem recorte da tela: a cabeça e os ombros passam por cima da borda de cima (pop-out 3D). Tudo na mesma camada, em sincronia.
ESTILO["quebra-moldura"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  C.css("quebra-moldura", `
    .qm{position:absolute;left:0;top:0;width:${W}px;height:${H}px;transform-origin:50% 100%}
    .qm video{position:absolute;left:0;top:0;width:${W}px;height:${H}px;object-fit:cover}
    .qm-b{position:absolute;border:18px solid #17181c;box-shadow:inset 0 0 0 2px rgba(255,255,255,.08),0 0 0 2px rgba(255,255,255,.14),
          0 50px 120px rgba(0,0,0,.65),0 0 80px color-mix(in srgb, var(--dest) 30%, transparent)}
    .qm-b i{position:absolute;top:22px;left:50%;width:170px;height:46px;margin-left:-85px;border-radius:24px;background:#07080a}`);
  const fh = r[3] - r[1], topo = r[3] - fh * .28, lado = Math.max(W * .1, (r[0] + r[2]) / 2 - fh * 1.05), s = .7, sobe = S.baixo - 150;
  const ladoD = W - Math.min(W * .9, (r[0] + r[2]) / 2 + fh * 1.05), rad = (W - lado - ladoD) * .13;
  const g = C.el("div", "qm"), vid = C.video(P.video, g, "qm-v"), bor = C.el("div", "qm-b", g, "<i></i>"), sil = C.video(P.silhueta, g, "qm-s");
  const ins = (t, d, b, e, k) => `inset(${t}px ${d}px ${b}px ${e}px round ${k}px)`;
  const cheio = ins(0, 0, 0, 0, 0), cel = ins(topo, ladoD, 0, lado, rad);
  const bCheio = {left: -18, top: -18, width: W + 36, height: H + 36, borderRadius: 0},
        bCel = {left: lado - 18, top: topo - 18, width: W - lado - ladoD + 36, height: H - topo + 36, borderRadius: rad + 18};
  const tl = C.tl, d = it.de, f = it.ate, ent = .6, sai = Math.max(d + ent + .5, f - .5);
  tl.set(g, {opacity: 0}, 0).set(g, {opacity: 1, scale: 1, y: 0, rotation: 0}, d).set(vid, {clipPath: cheio}, d).set(bor, Object.assign({opacity: 0}, bCheio), d)
    .to(g, {scale: s, y: -sobe, duration: ent, ease: "expo.inOut"}, d)
    .to(vid, {clipPath: cel, duration: ent, ease: "expo.inOut"}, d)
    .to(bor, Object.assign({duration: ent, ease: "expo.inOut"}, bCel), d).to(bor, {opacity: 1, duration: .3}, d + ent * .4)
    .to(g, {rotation: -2, duration: sai - d - ent, ease: "sine.inOut"}, d + ent)                 // leve inclinação: sensação 3D
    .to(g, {scale: 1, y: 0, rotation: 0, duration: .5, ease: "expo.inOut"}, sai)
    .to(vid, {clipPath: cheio, duration: .5, ease: "expo.inOut"}, sai)
    .to(bor, Object.assign({duration: .5, ease: "expo.inOut", opacity: 0}, bCheio), sai)
    .set(g, {opacity: 0}, f);
};
