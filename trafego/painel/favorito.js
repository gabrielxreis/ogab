// Favorito "⬇ Gab": na página de um anúncio da Biblioteca do Meta, salva o vídeo em Downloads.
(async () => {
  const id = new URLSearchParams(location.search).get('id') || '';
  const cards = [...document.querySelectorAll('div')].filter((e) => e.querySelector('video') && (!id || (e.innerText || '').includes(id)));
  const card = cards.sort((a, b) => a.innerText.length - b.innerText.length)[0];
  const v = (card && card.querySelector('video')) || document.querySelector('video');
  if (!v) { alert('Não achei vídeo nesta página. Abra o anúncio pela Biblioteca de Anúncios.'); return; }
  const nome = (card && (card.innerText.match(/\n([^\n]+)\nPatrocinado/) || [])[1] || 'Anuncio').replace(/[\\/:*?"<>|]/g, '').trim();
  const b = await (await fetch(v.currentSrc || v.src)).blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(b);
  a.download = 'Concorrente - ' + nome + (id ? ' - ' + id : '') + '.mp4';
  document.body.append(a); a.click(); a.remove();
})();
