# Preset RANKING (quadro que se monta com a fala)

Um quadro de ranking vai se montando enquanto a pessoa fala. Em `tier`, as faixas S, A, B, C e D (tons da cor da marca) já estão na tela e cada item, no instante em que é dito, cresce no centro, o quadro escurece um pouco e o card voa em arco até a faixa dele, onde assenta e FICA. Em `top3`, o pódio começa com "?" e é revelado do 3º ao 1º.

<img src="exemplo.gif" width="200" alt="Exemplo do preset ranking (conteúdo fictício)">

## Regras
- **Quando usar:** "tier list", "do pior ao melhor", "top 3", comparação de opções com nota. Não serve para dado numérico (use o GRÁFICO).
- **Tempo vem da fala:** `em` de cada item = segundo em que ele é dito (transcrição palavra a palavra). Destaque precisa de pelo menos 1,4 s até o próximo item; menos que isso, o item entra direto na vaga.
- **Duração:** último `em` + 2,5 s (padrão). Tier com 5-8 itens: 10-16 s. Top3: 6-9 s.
- **Campos:** `titulo` ("|" quebra, `*palavra*` na cor), `forma` (`tier` | `top3`), `faixas` (opcional, nomes ou `{nome, cor}`), `itens` [{`texto`, `imagem` opcional, `faixa`, `em`}], `destaque` (padrão true), `cor`, `letra` (`inter` | `bebas`), `fundo` (`escuro` | `transparente`). Formato completo no docstring do `gerar.py`.
- **Espaço:** quadro de y ~215 a ~1380, centrado em x 540; a parte de baixo (y 1500-1800) fica livre para a legenda.
- **Texto do card:** 1-3 palavras. Todos os cards usam o mesmo corpo de letra (o do texto mais longo).

## Como fazer
```
python3 gerar.py plano.json <pasta> [--render ranking.mp4 --gif]
python3 gerar.py plano.json <pasta> --render ranking.mov      # com "fundo": "transparente" (alfa, vai por cima do vídeo)
```
Depois: storyboard, aprovação, render e revisor (`docs/etapas/revisor.md`). Som: whoosh curto no voo e um toque seco quando o card assenta.
