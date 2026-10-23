// EFEITO · parede de miniaturas: mosaico levemente inclinado enche a parede atrás da pessoa (recorte por cima), do centro
// para as bordas. "imagens" = caminhos das miniaturas/posts/prints do próprio cliente; sem imagens, desenha peças fictícias
// (miniatura de vídeo, post e print de números), nunca marca de terceiros.
ESTILO["parede-miniaturas"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  C.css("parede-miniaturas", `
    .pm{position:absolute;left:50%;top:50%;width:${W * 1.5}px;height:${H * 1.3}px;margin:${-H * .65}px 0 0 ${-W * .75}px;transform:rotate(-7deg)}
    .pm-bg{position:absolute;inset:0;background:#0c0d10}
    .pm .m{position:absolute;border-radius:18px;overflow:hidden;box-shadow:0 14px 34px rgba(0,0,0,.5);background:#1a1b20}
    .pm .m img{width:100%;height:100%;object-fit:cover;display:block}
    .pm .v .pl{position:absolute;left:50%;top:50%;width:70px;height:70px;margin:-35px 0 0 -35px;border-radius:50%;background:rgba(255,255,255,.9)}
    .pm .v .pl::after{content:"";position:absolute;left:28px;top:20px;border-left:24px solid #111;border-top:15px solid transparent;border-bottom:15px solid transparent}
    .pm .v .tt{position:absolute;left:16px;bottom:16px;right:60px;height:22px;border-radius:6px;background:rgba(255,255,255,.85)}
    .pm .v .tt+.tt{bottom:46px;right:110px;background:var(--dest)}
    .pm .p{background:#f3f1ec}
    .pm .p .ft{position:absolute;left:0;right:0;top:0;height:62%}
    .pm .p .ln{position:absolute;left:16px;height:14px;border-radius:7px;background:rgba(0,0,0,.18)}
    .pm .p .ct{position:absolute;right:16px;bottom:14px;width:28px;height:26px;border-radius:50% 50% 50% 50%/60% 60% 40% 40%;background:#ff5a6e}
    .pm .n .br{position:absolute;bottom:22px;width:24px;border-radius:5px 5px 0 0;background:var(--dest)}
    .pm .n .nm{position:absolute;left:18px;top:18px;width:60%;height:30px;border-radius:8px;background:rgba(255,255,255,.85)}`);
  const imgs = (it.imagens || []).filter(Boolean), bg = C.el("div", "pm-bg"), pm = C.el("div", "pm");
  const tw = 300, th = 380, g = 26, cols = Math.ceil(W * 1.5 / (tw + g)) + 1, lins = Math.ceil(H * 1.3 / (th + g)) + 1;
  const cores = [["#ff7a45", "#ffd166"], ["#4c6fff", "#9ad0ff"], ["#2a9d8f", "#c1f0d8"], ["#c04cff", "#ffb3e6"], ["#ef476f", "#ffcf99"], ["#3d405b", "#81b29a"]];
  const cx = W * .75, cy = H * .65, pecas = [];
  let k = 0;
  for (let j = 0; j < lins; j++) for (let i = 0; i < cols; i++, k++) {
    const x = i * (tw + g) - (j % 2 ? (tw + g) / 2 : 0), y = j * (th + g) - 60, m = C.el("div", "m", pm);
    Object.assign(m.style, {left: x + "px", top: y + "px", width: tw + "px", height: th + "px"});
    const [a, b] = cores[(i * 7 + j * 3) % cores.length], tipo = (i + j * 2) % 3;
    if (imgs.length) m.innerHTML = `<img src="${C.esc(imgs[k % imgs.length])}">`;
    else if (tipo === 0) { m.classList.add("v"); m.style.background = `linear-gradient(${140 + i * 20}deg, ${a}, ${b})`; m.innerHTML = `<i class="pl"></i><i class="tt"></i><i class="tt"></i>`; }
    else if (tipo === 1) { m.classList.add("p"); m.innerHTML = `<i class="ft" style="background:linear-gradient(160deg, ${b}, ${a})"></i><i class="ln" style="top:66%;width:70%"></i><i class="ln" style="top:76%;width:48%"></i><i class="ct"></i>`; }
    else { m.classList.add("n"); m.innerHTML = `<i class="nm"></i>` + [40, 70, 55, 110, 160, 230].map((h, q) => `<i class="br" style="left:${24 + q * 44}px;height:${h}px;opacity:${.45 + q * .1}"></i>`).join(""); }
    pecas.push([m, Math.hypot(x + tw / 2 - cx, (y + th / 2 - cy) * .8)]);
  }
  const tl = C.tl, d = it.de, f = it.ate, maxd = Math.max(...pecas.map(p => p[1])), ench = Math.min(.8, (f - d) * .3);
  tl.set([bg, pm], {opacity: 0}, 0).set(pm, {opacity: 1}, d)
    .fromTo(bg, {opacity: 0}, {opacity: .92, duration: .3}, d)
    .fromTo(pm, {scale: 1.08}, {scale: 1, duration: f - d, ease: "none"}, d);   // leve recuo durante todo o trecho
  pecas.forEach(([m, dist]) => tl.fromTo(m, {opacity: 0, scale: .6, y: 40}, {opacity: 1, scale: 1, y: 0, duration: .35, ease: "back.out(1.8)"}, d + .05 + ench * dist / maxd));
  tl.to([pm, bg], {opacity: 0, duration: .4, ease: "power2.in"}, Math.max(d + ench + .5, f - .4));
};
