// EFEITO · vertigem (dolly zoom): na camada atrás, uma cópia do vídeo (P.video) encolhe a partir do centro do corpo enquanto a
// pessoa recortada (por cima) não muda: a sala "foge" para trás. A pessoa da cópia fica menor e some atrás da de verdade; as
// bordas que sobram são cobertas por outra cópia ampliada e desfocada. Volta ao normal no fim.
ESTILO["vertigem"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const tl = C.tl, d = it.de, f = it.ate, k = 1 - Math.min(.45, Math.max(.1, +it.forca || .3));
  C.css("vertigem", `
    .vg{position:absolute;inset:0;overflow:hidden;background:#000}
    .vg video{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:fill}
    .vg .vg-borda{filter:blur(28px) brightness(.8);transform:scale(1.25)}
    .vg-vin{position:absolute;inset:0;background:radial-gradient(ellipse 70% 60% at 50% 45%,rgba(0,0,0,0) 40%,rgba(0,0,0,.55))}`);
  const box = C.el("div", "vg");
  const vid = (cls) => C.video(P.video, box, cls);
  if (!P.video) return;
  const borda = vid("vg-borda"), sala = vid("vg-sala"), vin = C.el("div", "vg-vin", box);
  // centro do encolhimento: meio do rosto na horizontal, um pouco abaixo do queixo (a pessoa da cópia cabe dentro da de verdade)
  const ox = (r[0] + r[2]) / 2, oy = r[3] + (r[3] - r[1]) * .2;
  sala.style.transformOrigin = `${ox}px ${oy}px`;
  const ida = Math.max(.6, (f - d) * .7);
  tl.set(box, {opacity: 0}, 0).set(box, {opacity: 1}, d).set(box, {opacity: 0}, f)
    .fromTo(sala, {scale: 1}, {scale: k, duration: ida, ease: "power2.inOut"}, d)
    .fromTo(sala, {filter: "blur(0px)"}, {filter: "blur(1.5px)", duration: ida, ease: "power1.in"}, d)
    .fromTo(vin, {opacity: 0}, {opacity: 1, duration: ida, ease: "power1.inOut"}, d)
    .to(sala, {scale: 1, filter: "blur(0px)", duration: f - d - ida, ease: "power3.inOut"}, d + ida)
    .to(vin, {opacity: 0, duration: f - d - ida}, d + ida);
};
