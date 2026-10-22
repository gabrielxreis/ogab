# Preset COMENTÁRIO (respondendo comentário)

O card do comentário de um seguidor entra na tela com um pop suave: escala, leve giro e inclinação em perspectiva que assentam com um overshoot pequeno. O coração enche, as curtidas sobem e a palavra-chave ganha marca-texto na cor da marca. Vários comentários em sequência empilham: o anterior sobe, encolhe e escurece atrás do novo, e o mais antigo some. Serve para Reels no formato "respondendo comentário", perguntas frequentes e prova social leve.

<img src="exemplo.gif" width="200" alt="Exemplo do preset comentario (comentários fictícios)">

## Regras
- **Quando usar:** a fala responde ou lê um comentário ("a Ana perguntou como eu organizo a semana"). O card entra junto com a palavra que cita o comentário.
- **Duração:** 2,5-3 s por comentário (tempo de ler: 0,3 s por palavra + 0,5 s). Exemplo: 3 comentários, 8,3 s. Comentário curto (até 8 palavras).
- **Estilo:** `claro` (card branco de rede social genérica, sem logo de app real) ou `vidro` (glass escuro). `posicao`: `topo` (padrão, deixa o rosto e a legenda livres) ou `centro`.
- **Campos:** `w`, `h`, `fps`, `dur`, `cor`, `estilo`, `posicao`, `fundo` (`transparente` para ir por cima do vídeo da pessoa, render em `.mov`), `comentarios` [{`usuario`, `texto`, `curtidas`, `tempo`, `avatar` (opcional; sem ele, círculo na cor com a inicial), `destaque` (opcional), `em`}]. Formato completo na docstring do `gerar.py`.
- **Conteúdo:** comentário real só com print ou autorização do cliente; nada de nome de app real no card. A faixa de baixo (legenda, y 1500-1800) fica sempre livre.

## Como fazer
```
python3 gerar.py plano.json <pasta> [--render comentario.mp4 --gif]
```
Com `"fundo": "transparente"`, renderizar para `.mov` (sai com alfa). Depois: storyboard, aprovação, render e revisor (`docs/etapas/revisor.md`).
