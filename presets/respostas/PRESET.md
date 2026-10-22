# Preset RESPOSTAS (faixa de "?" que vira resposta)

Faixa no topo do quadro para entrevista de rua, "3 regras para...", "o que você levaria?". N espaços começam com "?" (respirando de leve) e cada um vira ícone + palavra curta no instante em que a resposta é dita, com um flash leve da cor da marca. As respostas anteriores ficam; as seguintes continuam com "?".

<img src="exemplo.gif" width="200" alt="Exemplo do preset respostas (conteúdo fictício)">

## Regras
- **Quando usar:** lista curta falada (2 a 5 itens) com a pessoa na tela. Vai por cima do vídeo com `"fundo": "transparente"`.
- **Tempo vem da fala:** `em` de cada item = segundo em que a resposta é dita (transcrição palavra a palavra). A troca começa 3 quadros antes para o flash cair na palavra.
- **Duração:** último `em` + 2,5 s (padrão); costuma ser o trecho inteiro da lista.
- **Campos:** `pergunta` (opcional, `*palavra*` na cor), `itens` [{`icone`, `rotulo`, `em`}], `cor`, `letra` (`inter` | `bebas`), `fundo` (`escuro` | `transparente`). Formato completo no docstring do `gerar.py`.
- **Ícone:** imagem ou SVG no traço da marca é o padrão (`"icone": "icones/cofre.svg"`). Emoji só quando o usuário pedir (`motion_proibidos.md`).
- **Espaço:** faixa de y ~140 a ~420, centrada em x 540. Rótulo de 1-3 palavras; todos com o mesmo corpo de letra.

## Como fazer
```
python3 gerar.py plano.json <pasta> [--render respostas.mp4 --gif]
python3 gerar.py plano.json <pasta> --render respostas.mov    # com "fundo": "transparente" (alfa)
```
Depois: storyboard, aprovação, render e revisor (`docs/etapas/revisor.md`). Som: um "pop" suave ou ding curto em cada troca.
