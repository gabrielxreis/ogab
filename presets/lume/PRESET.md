# Preset LUME (legenda que brilha + mesa vista de cima + luz vazada)

Talking head com cor teal e laranja, vinheta escura embaixo e uma legenda em duas camadas: uma **linha pequena e fina**
com a fala e a **palavra-chave grande que brilha** em amarelo, entrando letra a letra num leve ângulo 3D (às vezes atrás
da mão da pessoa). Entre as frases, o vídeo corta para **cenas de mesa vista de cima** (papel bege, sombra de janela,
folhas) onde objetos recortados com sombra real nascem desfocados e crescem nítidos, setas tracejadas se desenham e
anotações à mão se escrevem. A volta para o apresentador vem por **mergulho de foco** (a mesa desfoca e um objeto
cresce por cima) ou por **luz vazada quente** que esconde o corte para um close.

Estudado em 17/10/2026, quadro a quadro (2, 10 e 15 qps) e pelo áudio, no painel "After" de um Reels de antes e
depois de um editor de short-form (entrevista com um criador grande). A referência fica só na máquina
(`~/Documents/CLAUDE BRAIN/_referencias-video/reel-DdM89KRMPBJ/`), nunca no repo.

Exemplo pronto: `exemplo.gif` / `exemplo.mp4` (1080x1920, apresentador, mesa e objetos gerados por IA, fictícios).
Kit: `kit/lume.css` + `kit/lume.js`. Para abrir ou re-renderizar o exemplo: copiar os dois arquivos do kit para
`exemplo/` e `npx hyperframes render exemplo`.

## Quando usar
- Talking head de bastidor, processo, "como a gente faz", números de produção ("3 meses", "1,5 milhão por vídeo"),
  criador ou empresa contando o método. 20-60 s.
- Quando a fala cita uma etapa concreta que dá para mostrar como objeto (ideia = lâmpada, pensar = cérebro,
  roteiro = papéis com clipe, publicar = tablet com play, prazo = calendário, dinheiro = notas).
- Pedido de "legenda brilhando", "estilo antes e depois", "mesa vista de cima", "flat lay", "luz vazada".
- Não usar em vídeo emocional/religioso de luto, nem em marca que proíbe amarelo (trocar `--l-brilho`).

## Como pedir
`/ogab faz um reels da <empresa> no preset lume` ou, no `clientes/<empresa>/estilo.md`, `preset: lume`.
O preset troca só o que está aqui; V1 intocada, música bruta, pastas e conferências seguem o Gab.

## 1. Legenda que brilha (o coração do estilo)
| Item | Valor |
|---|---|
| Linha pequena | Inter 400, 44 px, branca com sombra, tracking -1 %; pode ser Playfair 800 (`serifPeq`) |
| Palavra-chave | Inter 800, 112 px, amarelo `--l-brilho` (`#ffe14a`) com halo em 3 camadas (6/22/48 px); ou Playfair 900 (`serif: true`) |
| Destaques | `^laranja^` Inter 800 56 px (`--l-quente`), `~fria~` azul desfocada (`--l-frio`), `=branca=` Inter 800 |
| Ângulo | bloco em `rotateX(14deg) rotateY(-10deg)` com perspectiva 900 px (`.reto` desliga; `.canto` vai para o canto de cima) |
| Posição | peito/cintura (Y 1050-1300); frase de contexto no canto de cima à direita; nunca no rosto |
| Ritmo | palavras pequenas a cada 0,16 s (ou `tempos` da transcrição), sobem 26 px com desfoque 10 px em 0,32 s; a chave entra **letra a letra** (0,035 s entre letras, desfoque 16 px, sobe 40 px, nasce 1,25x) |
| Vida | o bloco inteiro flutua 18 px em ~2,4 s (`sine.inOut`): nunca parado |
| Saída | desfoca 14 px e some em 0,25 s, logo antes da próxima frase |
| Atrás da pessoa | quando a mão/braço passa pela frase: recorte da pessoa (`presets/cena/recorte.py`) numa camada acima da legenda |

Uma chave por frase, na palavra que carrega a ideia (o número, o verbo forte, o "o quê"). O resto da fala fica na linha
pequena. **No DaVinci:** a legenda nativa não faz isso; nas falas-chave a legenda vira motion (HyperFrames com alfa) e o
resto segue a legenda normal.

No kit: `L.brilho(tl, "#l1", t, "uns três ou / =quatro meses= / ^antes^")`, `L.sai(tl, "#l1", t)`.

## 2. Cena de mesa vista de cima
- **Fundo:** foto de mesa vazia (papel bege, sombra de janela na diagonal, folhas entrando pelos cantos), empurrando
  devagar 1 -> 1,05 durante a cena (`L.mesa`). Entra no **corte seco**, sem transição (como na referência).
- **Objetos:** PNG recortado com sombra (`.l-obj` já põe sombra de contato). Cada um nasce com escala 0,12 e desfoque
  14 px e cresce nítido em 0,45 s (`L.objeto`), um a cada 0,25-0,5 s, seguindo a fala. Depois respiram 2 %.
- **Papel colado:** post-it com checklist manuscrito (`.l-postit`, Caveat Brush), etiqueta amarela (`.l-etiqueta`).
- **Traços:** rascunho de storyboard que se desenha sobre o papel (`L.traco`), seta tracejada em curva que se desenha
  com a ponta aparecendo no fim (`L.seta`, 0,7 s), anotação à mão no topo ("1-2 MESES") que se escreve (`L.manuscrito`).
- **Frase da cena:** laranja Inter 800, palavra a palavra, nascendo de um rascunho fantasma à mão (`L.frase`).
- **Objetos de sempre (metáforas):** ideia = lâmpada acesa; pensar/planejar = cérebro; roteiro = papéis com clipe;
  gravar = câmera; editar/publicar = tablet com play; tempo = relógio ou calendário; dinheiro = notas; tarefa = post-it.
  Gerar no Nano Banana Pro ilimitado (folha de objetos em fundo branco, vista de cima, sem texto) e recortar.

## 3. Transições
| Transição | Como | Quando |
|---|---|---|
| Corte seco | vídeo -> mesa vazia, objetos nascem logo depois | entrar na mesa |
| Mergulho de foco | mesa desfoca 16 px, escurece 28 % e cresce 8 % (0,55 s) enquanto um objeto cresce nítido do centro (0,6 s) com a frase em brilho | resumo da cena ("3 a 4 meses só na ideia") |
| Luz vazada | onda roxa > amarela > laranja em modo tela subindo pela tela em 0,75 s; o corte (médio -> close) fica no pico (`L.luz` devolve o pico) | virada da fala, número final |
| Punch-in | `L.camera` 1 -> 1,08 em 0,5 s, ou corte para close no pico da luz | entre frases do mesmo plano |

## 4. Acabamento do vídeo
Cor teal e laranja (PowerGrade do Gab + um pouco de laranja na pele), vinheta preta nos 45 % de baixo (`.l-vinheta`),
retícula de pontos fina (`.l-reticula`, 10 %) e grão (`.l-grao`, 7 %).

## 5. Som (medido no áudio da referência)
Brilho fino (shimmer/chime curto) quando a palavra-chave acende; pop suave de papel em cada objeto que nasce;
risco de lápis na seta e no manuscrito; whoosh macio no mergulho de foco; swell/whoosh quente na luz vazada.
Música baixa e calma por baixo da entrevista. Picos no instante do movimento (ver `docs/etapas/sfx.md`).

## 6. Ritmo (do estudo)
Uma mudança a cada 1-3 s: frase em brilho (1-2 s), cena de mesa (3-4 s, 3-5 objetos), volta ao vídeo, luz vazada
no fim para o número que fecha. A mesa aparece 2-3 vezes num vídeo de 20-30 s; o resto é o apresentador com o brilho.
