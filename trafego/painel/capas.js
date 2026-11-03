// Capas dos anúncios da Biblioteca do Meta, para as miniaturas do painel (nada de vídeo é baixado).
// Uso: abrir a página da Biblioteca que `miniaturas.py --faltam` indicou, colar este arquivo inteiro no javascript
// do navegador com os IDs que faltam em QUERO (vazio = todos da página) e mandar o JSON devolvido para
// `python3 painel/miniaturas.py --cliente <c>` (stdin). A página do Facebook não deixa mandar direto ao 127.0.0.1.
(async (QUERO) => {
  for (let i = 0; i < 6; i++) { window.scrollTo(0, document.body.scrollHeight); await new Promise((r) => setTimeout(r, 1200)); }
  const rotulo = /(Identificação da biblioteca|ID da biblioteca|Library ID)\s*:?\s*(\d{6,})/;
  const vistos = new Map();
  const nos = [...document.querySelectorAll('div, span')].filter((e) => e.childElementCount === 0 && rotulo.test(e.textContent));
  for (const n of nos) {
    const id = n.textContent.match(rotulo)[2];
    if (vistos.has(id) || (QUERO.length && !QUERO.includes(id))) continue;
    let card = n.parentElement, capa = null;
    for (let i = 0; i < 14 && card && !capa; i++, card = card.parentElement) {
      if ((card.innerText.match(new RegExp(rotulo.source, 'g')) || []).length > 1) break; // já pegou outro anúncio
      const v = card.querySelector('video[poster]');
      if (v && v.poster) { capa = v.poster; break; }
      // imagem do anúncio: a maior do card (a foto da página é pequena e fica de fora)
      const im = [...card.querySelectorAll('img')].filter((x) => x.naturalWidth >= 250 && x.naturalHeight >= 250)
        .sort((a, b) => b.naturalWidth * b.naturalHeight - a.naturalWidth * a.naturalHeight)[0];
      if (im) capa = im.currentSrc || im.src;
    }
    vistos.set(id, capa);
  }
  const achados = [...vistos].map(([id, capa]) => ({ id, capa }));
  return JSON.stringify({ capas: achados, nao_achou: QUERO.filter((i) => !vistos.has(i)) });
})([/* IDs que faltam, ex.: '1620210178950193' */]);
