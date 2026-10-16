# Carrossel de MOTION (estilo PAINEL)

Estudado em 16/10/2026 de um carrossel de agentes de IA (8 slides em vídeo): cada slide é um **vídeo 1080x1350 de
~6,5 s que se monta sozinho** e para no quadro final, então funciona como vídeo no carrossel e o último quadro vale
como imagem. Pede-se "carrossel de motion", "carrossel animado" ou "carrossel em vídeo".

Visual: fundo creme com luz suave, título gigante em sans black (última linha na cor de destaque), subtítulo com
trecho em **negrito**, logo + @ no topo, contador "01 / 06" e "arrasta →" manuscrito no canto.

## Tipos de slide
| Tipo | O que é | Animação |
|---|---|---|
| `capa` | título + grade de até 6 cartões numerados (ícone, nome, uma linha) | título sobe por máscara, cartões entram um a um |
| `app` | celular com o app (saudação, número contando, barra, 3 mini-cartões, lista "Agora" recebendo check) + "O QUE ENTRA" (3), "O QUE ELE DECIDE" (3, com número) e "AS REGRAS DELE" | celular sobe, fios finos se desenham ligando tudo, números contam |
| `conexao` | hub escuro no centro com até 7 cartões ligados por curvas + notificação final + frase manuscrita | hub cresce, nós aparecem, fio laranja até a notificação |
| `cta` | "COMENTA" + palavra em pílula, caixa de comentário digitando, cartão-isca girado (kit grátis) e frase manuscrita | digitação letra a letra, isca entra girando |

Ideal: capa, 1 slide `app` por item (agente, produto, etapa, serviço), `conexao` como "o segredo" e `cta`.
O `app` serve para qualquer coisa que "trabalha sozinha": agente de IA, sistema, rotina da empresa, serviço do cliente.

## Como gerar
1. Planejar o texto pela `ig-carousel-planner` (gancho na capa, uma ideia por slide, CTA no fim) e mostrar ao usuário.
2. Escrever o `plano.json` (formato completo no topo do `gerar.py`; exemplo em `exemplo/plano.json`). Cores e logo
   da marca do cliente em `marca` (`dest` = cor de ação do site; `app1/app2` = escuro do app; `logo_img` opcional).
3. `python3 SKILL_DIR/instagram/carrossel_motion/gerar.py plano.json <pasta>/carrossel_motion` gera `01.mp4`,
   `01.png`... (`--so 2,3` refaz só esses slides). **Abrir os PNGs e conferir** texto cortado e quebras.
4. Legenda do post pela `ig-caption-writer` + `ig-humanizer --mode audit`.

## Regras
- Título com 2 linhas curtas (até ~14 caracteres por linha em 98 px; use `titulo_tam` menor para frases longas).
- Cartões laterais: título até 2 linhas curtas; número do "decide" é o que aparece no app (bater os números).
- Lista do app: 3-4 itens, o último pode ficar sem check (`"feito": false`) com a etiqueta laranja (`tag_tipo: "al"`).
- Ícones: os do preset sketch + historico, caixa, mao, inbox, ok2, alerta, recibo, funil (`kit/icones.js`).
- Nunca copiar a marca da referência: logo, @ e cores são sempre do cliente.
