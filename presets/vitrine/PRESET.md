# Preset VITRINE (edição + motion)

Estilo "interface limpa de luxo": cada frase vira um pedaço de interface (conversor, perfil, cartão, janela, pílula),
fundo branco ou preto, uma única cor de destaque, tudo entrando com desfoque. Estudado quadro a quadro (12 qps) nos
20 s iniciais de uma referência de mini documentário para criadora de luxo. Serve para Reels de marca, criador de
conteúdo, curso, lançamento, bastidores e qualquer vídeo em que a fala cita coisas concretas (valores, números, perfis,
arquivos, avisos).

Exemplo pronto: `exemplo.gif` / `exemplo.mp4` (1080x1920, 14 s, conteúdo fictício). Kit: `kit/vitrine.css` + `kit/vitrine.js`.
Para abrir ou re-renderizar o exemplo: copiar os dois arquivos do kit para `exemplo/` e `npx hyperframes render exemplo`.

## Como pedir

`/ogab faz um reels da <empresa> no preset vitrine` ou, no `clientes/<empresa>/estilo.md`, a linha `preset: vitrine`.
O preset troca só o que está aqui; legenda, V1 intocada, música bruta, pastas e conferências seguem o Gab.

## 1. Regra de ouro: a fala vira interface (literal)

Para cada frase, perguntar "que tela mostraria isso?" e montar essa tela. Nada de imagem genérica.

| A fala diz | O visual | Movimentos do kit |
|---|---|---|
| a frase do gancho | as palavras da fala sobem uma a uma no fundo branco | `palavras` + `chicote` |
| marcas, trabalhos, exemplos | carrossel de cartões 9:16 (Reels, fotos) andando | `carrossel` + `trocaImagem` |
| valor, preço, moeda ("600 €") | conversor ou campo de busca que digita e um resultado que conta | `cortina` + `cai` + `digita` + `conta` + `viraTema` |
| pessoa, perfil, seguidores | cartão de perfil que cresce com o número subindo | `zoomCartao` + `conta` + `someDesfocando` |
| bastidor, processo, "meus clientes" | b-roll REAL com foco puxando (mesa, notebook, mão) | `foco` |
| inscrever, seguir, canal | cartão do canal: banner escurece, nome digita, sino toca | `clarao` + `janela` + `letras` + `sino` |
| título de bloco ("dois avisos") | caixa de seleção com alças digitando o texto, fundo preto | `selecao` |
| arquivo, pasta, material | janela estilo macOS com a lista | `janela` |
| aviso, dica, atenção | pílula (ilha dinâmica) que nasce ícone e abre em texto | `pilula` + `fechaPilula` |
| tela do software, tutorial | gravação de tela dentro de uma janela arredondada, cabeçalho "1º ..." | `janela` |

## 2. Ritmo

- **Gancho (primeiros 8-10 s):** troca de visual a cada **1,2 a 1,8 s** (na referência: 1,3 / 1,4 / 1,4 / 1,3 / 1,7 s).
- **Blocos de informação:** segura **2 a 5 s** no mesmo cartão, mas **nunca parado**: o cartão respira (escala 1 → 0,97),
  um número conta, um cursor digita ou a pílula troca de texto.
- Corte na fala: o visual entra **junto com a palavra** que ele ilustra (até 2 quadros antes), nunca depois.
- Alterna fundo **branco ↔ preto por bloco** (abertura clara, dados escuros, social claro, avisos escuros).

## 3. Transições (só estas; nada de glitch, giro ou zoom de pacote)

| Transição | Quando | Tempo |
|---|---|---|
| Chicote lateral com desfoque | sair de texto | 0,28 s, `power3.in` |
| Cortina escura sobe de baixo | branco → preto | 0,38 s, `power4.inOut` |
| Clarão branco | b-roll → cartão claro | sobe 0,16 s, desce 0,3 s |
| Virar tema (escuro vira claro num quadro) | final de um cartão escuro, antes de cartão claro | 1 quadro |
| Some desfocando | sair de cartão | 0,3 s, desfoque 14 px |
| Corte seco no preto | antes de um título de bloco | 0 s |

## 4. Visual

- **Fundos:** branco puro `#ffffff` e preto puro `#000`; cartões escuros `#1c1c1e`, claros `#f2f2f4`.
- **Uma cor viva só** (`--v-destaque`): a cor de ação do cliente (padrão `#e5531a`, laranja avermelhado). Usada no
  resultado do conversor, na caixa de seleção, no número do cabeçalho ("1º") e em mais nada.
- **Tipografia:** SF Pro / Inter, peso 500-700, tracking levemente negativo nos títulos. Sem fonte decorativa.
- **Espaço vazio** é parte do estilo: cartões centrados, ocupando 80-90 % da largura no vertical, nada encostado na borda.
- **Entradas sempre com desfoque** (12-18 px → 0) e curvas `expo.out`/`power3.out`; nada de bounce exagerado
  (só `back.out` leve na pílula e na caixa de seleção).
- B-roll real com **profundidade de campo rasa**, tons quentes e escuros, foco puxando ao entrar.

## 5. Som

- **Trilha:** eletrônica/lofi discreta com pad escuro, contínua do início ao fim, -22 a -24 dB sob a voz (sobe 4 dB nos
  respiros sem fala).
- **Efeitos de interface, um por movimento** (o CLAP da referência achou exatamente estes):
  - clique/tique de interface em cada letra digitada (volume baixo) e em cada botão;
  - whoosh curto e seco ("swish") em cada chicote e cortina;
  - sino quando o "Inscrito" aparece;
  - "pop" suave de notificação em cada abertura de pílula;
  - riser curto + impacto grave só na virada de bloco grande.
- Densidade no gancho: um som a cada ~0,7 s. Nada de whoosh em cartão que só respira.

## 6. Montagem no Gab

1. Cortes e legenda como sempre (legenda do início ao fim; sob cartão, desce para Y 390 com `legenda_baixa.py (PROIBIDO sem pedido do usuário, SKILL.md 1h3: ajustar a legenda no editor)`).
2. Plano trecho a trecho com a tabela da seção 1: uma linha por frase (tempo da fala, visual, movimentos).
3. Motions no HyperFrames: copiar `kit/vitrine.css` e `kit/vitrine.js` para o projeto, trocar `--v-destaque` (e, se
   quiser, a fonte) pelo cliente, montar cada cena com as funções `V.*` (ver `exemplo/index.html` como modelo, cada
   bloco comentado). Vertical 1080x1920 ou horizontal 1920x1080: mesmo kit, ajustar posições.
4. B-roll real com `foco` (no HyperFrames) ou, no editor, um desfoque que zera em 0,5 s.
5. SFX pela seção 5, um por movimento, conferidos com `sfx_conferir.py sincronia`.
6. QC normal do Gab.

## 7. Referência dos movimentos (`kit/vitrine.js`)

`V.palavras` · `V.chicote` · `V.carrossel` · `V.trocaImagem` · `V.cortina` · `V.cai` · `V.digita` · `V.conta` ·
`V.viraTema` · `V.zoomCartao` · `V.someDesfocando` · `V.foco` · `V.clarao` · `V.letras` · `V.selecao` · `V.janela` ·
`V.pilula` · `V.fechaPilula` · `V.sino`. Todas recebem `(tl, seletor, tempo, ...)` e devolvem o tempo em que terminam.
