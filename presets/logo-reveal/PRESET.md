# Preset LOGO REVEAL (abertura de marca)

Abertura de marca de 5-8 s, com o acabamento premium do launch. Serve para início de vídeo institucional, vinheta de canal ou fim de anúncio.

<img src="exemplo.gif" width="200" alt="Exemplo do preset logo reveal (marca fictícia)">

## Estilos (`estilo`)
| Estilo | O que acontece |
|---|---|
| `luz` (padrão) | um fio de luz se abre no centro e revela o logo de dentro para fora, com contraluz e brilho atravessando |
| `linhas` | fios finos entram das bordas e desenham a moldura do logo; o logo assenta e os fios se afastam |
| `pontos` | pontos girando se juntam no desenho do logo (amostrado do PNG) e o logo nítido assenta por cima |

## Regras
- **Logo e cores só do material do cliente:** PNG com fundo transparente. O SVG serve para `luz` e `linhas`. Sem logo, o preset usa o monograma da inicial.
- **Logo largo** (com o nome escrito) é detectado sozinho. **Logo só com símbolo:** preencher `nome` para o nome entrar embaixo.
- **Depois do logo:** a frase da marca sobe por máscara. Nada de quique nem brilho exagerado (`docs/etapas/motion_proibidos.md`).

## Como fazer
```
python3 gerar.py plano.json <pasta> [--render logo.mp4 --gif]
```
Depois: storyboard, aprovação, render e revisor.
