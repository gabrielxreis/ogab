// EFEITO · telas em órbita: cartões verticais de tela de celular (vídeo rodando: barra de progresso, ícones, legenda)
// girando numa elipse inclinada em volta da pessoa. Roda nas DUAS camadas com a mesma conta ("camada": "ambas"):
// na de trás (palco) só a metade de trás da volta, na altura da cabeça (o recorte cobre); na da frente só a metade da
// frente, abaixo do queixo. Diferente do "giro" da ÓRBITA (cartões de texto): aqui são telas de vídeo.
// "telas" = imagens (frames/capas do cliente); sem imagens, telas fictícias em gradiente.
ESTILO["orbita-telas"] = (it, C) => {
  const P = C.P, W = P.w, H = P.h, S = C.seguro, r = C.rostoEm(it.de) || [W * .32, H * .32, W * .68, H * .55];
  const atras = P.camada === "palco", fh = r[3] - r[1], cw = Math.round(Math.min(190, W * .17)), ch = Math.round(cw * 1.78);
  C.css("orbita-telas", `
    .ot{position:absolute;border-radius:${cw * .16}px;border:${cw * .035}px solid #0b0b0d;overflow:hidden;box-shadow:0 20px 50px rgba(0,0,0,.5);
        background:#222;opacity:0}
    .ot img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
    .ot .pb{position:absolute;left:8%;right:8%;bottom:5%;height:${cw * .025}px;border-radius:4px;background:rgba(255,255,255,.3)}
    .ot .pb i{display:block;height:100%;border-radius:4px;background:var(--dest)}
    .ot .ic{position:absolute;right:7%;width:${cw * .13}px;height:${cw * .13}px;border-radius:50%;background:rgba(255,255,255,.85)}
    .ot .lx{position:absolute;left:8%;height:${cw * .05}px;border-radius:4px;background:rgba(255,255,255,.8)}
    .ot .pl{position:absolute;left:50%;top:44%;width:${cw * .26}px;height:${cw * .26}px;margin-left:${-cw * .13}px;border-radius:50%;
            background:rgba(0,0,0,.25);border:2px solid rgba(255,255,255,.7)}`);
  const imgs = (it.telas || []).filter(Boolean), n = Math.max(4, Math.min(6, imgs.length || 5));
  const cores = [["#ff7a45", "#5b2cff"], ["#00b4d8", "#0b3d91"], ["#ffbe0b", "#fb5607"], ["#8338ec", "#ff006e"], ["#2a9d8f", "#264653"], ["#e76f51", "#f4a261"]];
  const cx = (r[0] + r[2]) / 2, yTras = r[1] + fh * .3, yFrente = r[3] + ch / 2 + 40, cy = (yTras + yFrente) / 2, ry = (yFrente - yTras) / 2;
  const rx = Math.min(Math.min(cx, W - cx) - S.lado - cw / 2, fh * 1.1), els = [];
  for (let i = 0; i < n; i++) {
    const [a, b] = cores[i % cores.length], e = C.el("div", "ot");
    e.style.cssText += `width:${cw}px;height:${ch}px;left:${-cw / 2}px;top:${-ch / 2}px;background:linear-gradient(${150 + i * 25}deg, ${a}, ${b})`;
    e.innerHTML = (imgs.length ? `<img src="${C.esc(imgs[i % imgs.length])}">` : `<i class="pl"></i>`)
      + `<i class="ic" style="bottom:34%"></i><i class="ic" style="bottom:24%"></i><i class="lx" style="bottom:15%;width:52%"></i>`
      + `<i class="lx" style="bottom:10%;width:34%;opacity:.6"></i><span class="pb"><i></i></span>`;
    els.push(e);
  }
  const tl = C.tl, d = it.de, f = it.ate, dur = f - d, voltas = typeof it.voltas === "number" ? it.voltas : .6, passo = 1 / 24;
  const estado = (i, tt) => {
    const ent = Math.min(1, tt / .4), sai = Math.max(0, Math.min(1, (dur - tt) / .35));
    const th = Math.PI * .15 + i * 2 * Math.PI / n + (tt / dur) * 2 * Math.PI * voltas, z = Math.sin(th), vis = atras ? z < 0 : z >= 0;
    return {x: cx + rx * Math.cos(th), y: cy + ry * z, scale: (.7 + .3 * (z + 1) / 2) * (.5 + .5 * ent), rotationY: -Math.cos(th) * 30,
            rotation: Math.cos(th) * 5, opacity: vis ? Math.min(ent, sai) * (atras ? .9 : 1) : 0, zIndex: Math.round(z * 100) + 100};
  };
  els.forEach((e, i) => {
    tl.set(e, Object.assign(estado(i, 0), {opacity: 0}), 0);
    for (let tt = 0; tt <= dur + 1e-6; tt += passo) tl.set(e, estado(i, tt), d + tt);   // quadro a quadro (o render salta quadros)
    tl.set(e, {opacity: 0}, f).fromTo(e.querySelector(".pb i"), {width: "0%"}, {width: "100%", duration: dur, ease: "none"}, d);
    if (atras) e.style.filter = "blur(1.2px) brightness(.85)";
  });
};
