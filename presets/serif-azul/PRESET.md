# Preset SERIF AZUL (talking head + cenas em papel off-white)

Talking head escuro com a legenda em duas fontes (sans pequena + palavra-chave em **serifada itálica azul**, 2,2x maior),
um contador de passos 1-2-3 que acompanha o vídeo inteiro e cenas de motion em **papel off-white** (grade fina, luz de
janela, anéis) que sobem por cima do apresentador. Estudado em 15/10/2026, quadro a quadro (2 e 12 qps), no Reels
"3 things from beginner to pro" do curso "How to Edit VIRAL Reels with AI" (Ultimate Editors). A referência e as 178
imagens de inspiração ficam só na máquina (`~/Documents/CLAUDE BRAIN/_motions/referencias/viral-reels-ue/`), nunca no repo.

Exemplo pronto: `exemplo.gif` / `exemplo.mp4` (1080x1920, 21 s, apresentador e marcas fictícios). Kit: `kit/serif.css` + `kit/serif.js`.
Para abrir ou re-renderizar o exemplo: copiar os dois arquivos do kit para `exemplo/` e `npx hyperframes render exemplo`.

## Quando usar
- Talking head de lista ou método ("3 erros", "5 passos", "do iniciante ao profissional"), dica, opinião de especialista, 40-70 s.
- Marca que quer cara de editorial/premium (curso, consultoria, criador, estética, imigração, finanças).
- Pedido de "legenda com serifa", "estilo editorial", "estilo Ultimate Editors", "papel branco".
- Não usar em vídeo emocional/religioso (lá vale b-roll em tela cheia) nem quando o cliente tem fonte própria obrigatória
  na legenda (aí trocar só `--s-serif`).

## Como pedir
`/ogab faz um reels da <empresa> no preset serif azul` ou, no `clientes/<empresa>/estilo.md`, a linha `preset: serif-azul`.
O preset troca só o que está aqui; V1 intocada, música bruta, pastas e conferências seguem o Gab.

## 1. Legenda (o coração do estilo)
| Item | Valor |
|---|---|
| Sans | Inter 500, 46 px, branca sobre o vídeo, preta sobre o papel, tracking -1,5 % |
| Palavra-chave | Playfair Display **800 itálico**, 2,25x a sans, azul `--s-destaque` (`#3d6ff2`; sobre vídeo `#6f97ff`) |
| Título no papel | linha fina em Playfair 400 + linha de baixo na serifada itálica azul ("Cores apagadas parecem / *mais premium.*") |
| Posição | sobre o vídeo: Y ≈ 930-1000 (peito), centralizada; com passos na tela, a legenda vai para baixo deles (Y ≈ 1430) |
| Ritmo | **palavra por palavra no tempo da fala**, cada uma entra com desfoque 8 px e sobe 14 px em 0,26 s; a serifada entra maior (1,12x) e assenta em 0,42 s |
| Linhas | 1 ou 2 linhas; a serifada fica na linha que tem a ideia ("Esses *três erros* / deixam sua edição amadora") |
| Quantas serifadas | uma por legenda, só na palavra que carrega a frase (número, adjetivo, o "o quê"); nunca artigo nem verbo de ligação |

No kit: `S.legenda(tl, "#l1", t, "Esses *três erros* / deixam sua edição amadora", { tempos: [...] })`, com os
`tempos` vindo da transcrição do DaVinci (`GetTranscription`, uma entrada por palavra).
**No DaVinci:** a legenda nativa (GAB USA) não faz duas fontes na mesma linha. Nesse preset a legenda das falas-chave
vira motion (HyperFrames, alfa) e o resto segue com a legenda da trilha normal em Inter; avisar o usuário.

## 2. Elementos sobre o vídeo
- **Vinheta**: escurece os 40 % de baixo do quadro (onde moram legenda e passos). `div.s-vinheta`.
- **Passos 1-2-3** (`S.passos`, `S.passo`, `S.rotulo`): trilho de vidro escuro com 3 círculos ligados por linha.
  No gancho os 3 acendem **vermelhos com brilho** ("os erros"); depois ficam neutros e cada "Número N" acende o círculo N
  em branco, a linha até ele fica sólida e a próxima pontilhada. Fica no mesmo lugar (Y ≈ 1150) o vídeo todo.
- **Slider de nível** (`S.slider`): "Iniciante ... Profissional", a bolinha corre e o rótulo final acende em azul.

## 3. Cenas no papel off-white
Fundo `--s-papel` `#f2f1ee` com grade de 90 px quase invisível, faixas diagonais de luz de janela desfocadas no topo e
dois anéis finos no centro (um azulado contínuo, um pontilhado). Tudo com sombra longa e macia (nada flutua sem sombra).
| A fala diz | Visual | Kit |
|---|---|---|
| "o que mais entrega o iniciante", exemplo de vídeo | print do Reels num celular de borda branca que cai do alto inclinado e flutua | `S.painel` + `S.cartao` |
| "deixe X% menor", tamanho, proporção | ícone 3D de app que nasce em pop e encolhe com caixa tracejada, selo "-25%" e partículas | `S.icone` + `S.encolhe` |
| intensidade, "menos é mais", dosar | barra de segmentos que enche e recua até o meio | `S.graus` |
| cores, paleta, "sempre usam" | amostras de cor com nome e código, uma por vez | `S.amostras` |
| marcas, ferramentas, exemplos | nuvem de pílulas brancas em volta da frase, cada uma na fonte da marca | `S.nuvem` |
| olhar, atenção, "elementos que você quer destacar" | objeto no centro (olho, produto) com cartões de UI (timeline, onda de áudio) em órbita | `S.orbita` |
| conclusão | título serifado sozinho no papel | `S.legenda` com `_fina_` + `*itálica*` |
Marca citada = logo/fonte oficial da marca na pílula (regra de logos do Gab); no exemplo as marcas são fictícias.

## 4. Montagem e ritmo
- **Alterna vídeo e papel** a cada 2-4 s. O papel entra de três jeitos: **cheio** (sobe de baixo como cartão
  arredondado que encaixa na tela, `S.painel`), **metade de cima** (tela dividida: papel em 0-890, apresentador embaixo,
  desce do alto) e **troca de conteúdo no mesmo papel** (o que estava sai desfocando e o novo nasce no lugar).
- O apresentador volta sempre que ele fala o "Número N" ou dá a dica de cada passo (rosto na hora do ponto principal).
- Visual entra **junto com a palavra** (até 2 quadros antes), nunca depois.
- Nada parado: celular flutua, ícone respira, pílulas boiam.
- Cor: grade fria e escura no vídeo (fundo azul petróleo, pele preservada), papel neutro quente. Só uma cor viva: o azul.

## 5. Som (método das 3 passadas, `docs/etapas/sfx.md`)
- Whoosh em cada painel que sobe/desce e cada celular que cai (pico no quadro mais rápido).
- Textura em cada evento: pop na palavra serifada de impacto e em cada amostra/pílula, clique de UI em cada passo que
  acende e na bolinha do slider, engrenagem/tique nas palavras que entram uma a uma, impacto sci-fi no ícone 3D.
- Riser + hit ~5 s depois do gancho (entrada do "Número 1") e em cada troca de passo grande; "success" curto no fim.
- Música: cama discreta o vídeo todo, sob a voz.

## 6. Montagem no Gab
1. Cortes, silêncios e transcrição como sempre (`GetTranscription` dá os tempos de cada palavra).
2. Plano trecho a trecho com as tabelas 1 e 3: uma linha por frase (tempo, legenda com a serifada marcada, cena).
3. Motions no HyperFrames: copiar `kit/serif.css` e `kit/serif.js`, trocar `--s-destaque` (e, se quiser, `--s-serif`)
   pelo cliente, montar com as funções `S.*` (ver `exemplo/index.html`, cada bloco comentado). Legenda, passos e slider
   são overlay (MOV ProRes 4444 com alfa, `--format mov`): é a exceção da regra "motion tem fundo próprio", porque fazem
   papel de legenda. As cenas de papel têm fundo próprio, como todo motion.
4. Tela dividida: papel renderizado só com a metade de cima; no DaVinci o apresentador fica no V1 e o motion por cima.
5. SFX pelas 3 passadas, conferidos com `sfx_conferir.py sincronia`.
6. QC normal do Gab (centro, área segura do Instagram, legenda até o fim).

## 7. Referência dos movimentos (`kit/serif.js`)
`S.legenda` · `S.sai` · `S.passos` · `S.passosLimpa` · `S.passo` · `S.rotulo` · `S.slider` · `S.painel` · `S.painelSai` ·
`S.cartao` · `S.icone` · `S.encolhe` · `S.graus` · `S.amostras` · `S.nuvem` · `S.orbita`. Todas recebem
`(tl, seletor, tempo, ...)` e devolvem o tempo em que terminam. Painel começa fora da tela por `tl.set(..., { yPercent: 100 }, 0)`,
nunca por `transform` no CSS (o GSAP lê o translate em px e soma).
