# Preset CARTÕES (pilha de provas)

Cartões de prova empilhando em profundidade: cada novo cartão (número, depoimento, print ou foto) entra pela frente e assenta em perspectiva, e os anteriores recuam (menores, mais escuros, um pouco acima). Ficam no máximo 4 visíveis; os mais antigos saem pelo fundo. No fim, opcional, a pilha inteira volta e se abre em leque ou grade para o "olha quanta prova", com uma frase subindo por cima. Números contam no mesmo formato do plano ("+3.200", "4,9").

<img src="exemplo.gif" width="200" alt="Exemplo do preset cartoes (provas fictícias)">

## Regras
- **Quando usar:** a fala empilha provas ("mais de 3 mil alunos, nota 4,9, olha o que eles dizem"). Cada cartão entra na palavra que ele mostra.
- **Duração:** ~2,1 s por cartão + 3,4 s de final. Exemplo: 5 cartões em leque, 14,1 s. Depoimento curto (até 8 palavras), porque o cartão de trás fica coberto.
- **Tipos:** `numero` (`titulo` em cima, `numero` grande na cor da marca, `texto` embaixo), `texto` (depoimento: `texto` + `titulo` com quem disse), `imagem` (print ou foto + `titulo` e `texto` de legenda).
- **Campos:** `w`, `h`, `fps`, `dur`, `cor`, `fundo` (`transparente` para ir por cima do vídeo, render em `.mov`), `cartoes` [{`tipo`, `titulo`, `texto`, `numero`, `imagem`, `em`}], `final` (`leque` | `grade` | `nenhum`), `emFinal`, `frase`. Formato completo na docstring do `gerar.py`.
- **Fatos:** todo número e depoimento vem da lista aprovada (`docs/etapas/revisor.md`); print só do material do cliente. A faixa da legenda (y 1500-1800) fica livre.

## Como fazer
```
python3 gerar.py plano.json <pasta> [--render cartoes.mp4 --gif]
```
Com `"fundo": "transparente"`, renderizar para `.mov` (sai com alfa). Depois: storyboard, aprovação, render e revisor (`docs/etapas/revisor.md`).
