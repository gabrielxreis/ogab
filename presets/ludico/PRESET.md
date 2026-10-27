# Preset LÚDICO (explicador viral de notícia, no tema da marca)

Pedido do Rick, 26/10/2026: "use o mesmo motion da referência, nas cores do X-Trader; crie um preset para esse estilo e salve"
e depois "durante o vídeo todo não quero que fique no globo, tem que ter outros motions igual da referência; com a referência
abasteça o preset". Referência: @ludificando.br (12 reels estudados, de 16 mil a 4,7 mi de views).
Instalado na skill em 27/10/2026 (`presets/ludico/`). O tema do X-Trader (`temas/xtrader.json`) fica só nesta máquina (fora do git);
o material do cliente (regras, jeito de falar do Estéfano, roteiros, planos e vídeos) está em `CLAUDE BRAIN/X-Trader/Ludico/`.
**É um ESTILO, não um catálogo:** quem escolhe o Lúdico no menu ganha o vídeo inteiro nele, com cenários NOVOS inventados para
cada frase no mesmo jeito de desenhar (ver Regras do estilo). Nunca misturar com outro preset no mesmo vídeo.

- Por que viraliza, a gramática visual e a **fórmula de roteiro**: `GUIA_VIRAL.md` desta pasta (ler antes de escrever).
- Tema: `temas/padrao.json` (neutro, sem `--tema`); marca do cliente = `--tema <marca>` ou `--tema caminho/tema.json`.
- Tema do X-Trader (exemplo de marca): `temas/xtrader.json` = as cores do curso (site xtraderacademy.com): fundo #0B080D com vinheta roxa, globo, cone e chão
  em roxo #A053FD, luz quase branca, objetos brancos, destaque dourado #DEC37C, queda em vermelho #DC2626, candles verdes e vermelhos,
  ponto da pílula roxo, Montserrat + JetBrains Mono. O `tema3d` controla o estúdio inteiro (luz, cone, disco, queda, velas, vinheta).
  **O cenário inteiro na cor do cliente, não só o texto** (Rick, 26/10/2026: luz quente deixou o estúdio marrom e ele reprovou).
  Marca nova: copiar para `temas/<marca>.json` e trocar as cores. **Sempre no tema do cliente** (pedido do Rick).

## REGRAS DO ESTILO (pedidas pelo Rick em 26/10/2026, valem para todo vídeo deste preset)
1. **O preset é o JEITO DE DESENHAR, não um catálogo.** Estilo fixo: cores do cliente, estúdio escuro com holofote em cone,
   objetos low-poly claros, um destaque de cor, cartão no canto, câmera que viaja, carimbo e CTA. Os CENÁRIOS são inventados
   para cada vídeo: "as animações estão muito iguais, um vídeo igual ao outro; tem que ser criativo". Cada vídeo novo cria
   ambientes próprios para a metáfora daquele assunto (elevador que despenca e o freio trava; balança real x dólar;
   termômetro; gangorra da liquidez; semáforo da confirmação...). Cenários de vídeos anteriores só voltam se a frase pedir
   exatamente a mesma coisa (ex.: fotos dos candidatos no resultado da eleição) e nunca na mesma sequência.
2. **Centralizado.** O assunto de cada cena fica no centro da tela (eixo x = 0 do estúdio, câmera mirando o centro do
   conjunto); nada de objeto principal num canto e placa solta no outro. Grupos são simétricos ou empilhados no centro.
3. **No máximo 1 minuto por vídeo** (roteiro de ~140 palavras). Roteiro maior: cortar frases inteiras antes da voz; voz já
   gravada: cortar frases inteiras no DaVinci (arquivo original, emendas em fronteira de frase) e refazer os tempos do motion.
4. O cenário vem do sentido da frase (regra abaixo) e as cores são as do curso (o estúdio inteiro, não só o texto).

## REGRA: o cenário vem do SENTIDO da frase, não do número (Rick, 26/10/2026)
"Quando fala que o Lula foi reeleito tem que aparecer a foto dos 2 candidatos e a porcentagem; o globo não faz sentido,
faz 0 sentido. Você tem sempre que analisar os contextos." Antes de escolher o cenário de cada cena, ler a frase e perguntar:
**o que a pessoa precisa VER para entender isso?**
- Pessoas disputando, resultado de eleição, A x B, quem ganhou → `duelo` (fotos dos dois + porcentagem de cada um).
- Lugar, de onde para onde, mercado lá fora → globo (`cidade`). O globo NUNCA é cenário padrão nem "tapa-buraco".
- Algo que parou, trava, pausa → `disjuntor`. Comparar valores no tempo → `barras`. Fração, "X de Y" → `blocos`.
- Lista de consequências → `placas`. O porquê, a lição, quem explica → `palco`.
Se nenhum cenário mostra o sentido, criar um cenário novo em vez de forçar um que existe. Conferir a tabela de cenas
(frase × cenário × "o que a pessoa vê") antes do storyboard.

## A linguagem da referência (o que o preset reproduz)
Cada vídeo da referência alterna CENÁRIOS 3D, todos com a mesma gramática: fundo escuro, um holofote em cone vindo de cima,
anel aceso no chão, objetos low-poly claros, um destaque de cor só, câmera que viaja de um cenário ao outro, e o mesmo cartão
no canto (linha da série, pílula da seção, fontes, etiqueta, número grande, tópicos) + carimbo + CTA.
Cenários vistos nos reels: globo com rotas (mercado no mundo), púlpito com boneco e holofote (quem falou/quem decide),
plenário/campo de blocos que acendem por porcentagem (votos, deputados, quantidade), barras comparando valores, placas
com etiqueta ("4 PROMESSAS"), relógio + barra de progresso (horário, apuração), documento com carimbo, caminho com etapas,
ringue com dois bonecos (A x B). Nunca o vídeo inteiro num cenário só: troca a cada bloco do roteiro (5 a 14 s).

## Cenários prontos (`"tipo"` da cena)
| tipo | o que é | quando usar |
|---|---|---|
| (padrão) `cidade` | globo do preset globo: gira até a cidade, rotas pontilhadas | lugar, mercado lá fora, de onde para onde |
| `disjuntor` | quadro com chave que desarma (faíscas), telão de candles que apaga, relógio que anda | circuit breaker, pausa, trava, "parou" |
| `barras` | colunas que sobem ou caem até o valor, linha do teto, valor em cima e nome no chão | comparar números, antes/depois, queda no dia |
| `blocos` | campo (grade ou arco tipo plenário) de blocos que ACENDEM (fração) ou CAEM (fração) | porcentagem, "X de Y", quem saiu, todos juntos |
| `palco` | boneco no púlpito com holofote e placa; ao lado, placas que trocam na palavra | o porquê, quem decide, a lição do mentor |
| `placas` | até 4 placas que sobem do chão na palavra | listas, "no seu bolso", promessas, etapas |
| `duelo` | fotos das pessoas em moldura sobre pedestais (altura pelo número), nome, valor e selo | eleição, A x B, quem ganhou, "a aposta x o resultado" |
| `grafico` | candles de um índice caindo/subindo até uma linha de limite, pausa com etiqueta, retomada, "?" no futuro | índice/ação/dólar no dia, circuit breaker, "e agora?" |
| `cta` | globo afastado + pergunta + botão; ou QUALQUER cenário 3D com `"cta": true` (ex.: o gráfico com o "?") | fim: o fundo do CTA também tem que fazer sentido |

**Fotos de pessoas reais (duelo):** só fotos oficiais com licença livre (Wikimedia Commons: foto oficial do Planalto, Agência Senado,
Câmara), crédito na tela (`sub` do cartão) e no `CREDITOS.txt` da pasta `fotos/`. Os dois lados com o mesmo enquadramento e tamanho
(neutralidade); só o dado decide o destaque.

Campos de cada um: docstring do `gerar.py`. Tempos (`em`, `desliga`, `religa`): segundo ou palavra da fala.


## Ambientes já inventados (exemplos de criatividade, NÃO catálogo: cada vídeo novo inventa os seus)
Todos centrados no x = 0, simétricos, com holofote e anel no chão; campos na docstring/código do `kit/ludico.js`.
| tipo | metáfora | usado em |
|---|---|---|
| `pregao` | prédio da bolsa com letreiro de cotações; luzes apagam e cai "PREGÃO SUSPENSO" | Circuit Breaker |
| `elevador` | o índice despenca andar por andar (%), o freio de emergência trava, depois volta a cair | Circuit Breaker |
| `placar` | placar de LED com linhas que viram (rótulo + valor) | Circuit Breaker |
| `calculadora` | o mercado refazendo a conta no visor | Circuit Breaker |
| `barco` | ondas da notícia crescem, o barco da disciplina segue firme | Circuit Breaker |
| `skyline` | duas cidades: uma apagada (fechada), outra acesa, lua no meio | Nova York avisou |
| `cesta` | a cesta do fundo perde empresas e o preço vira | Nova York avisou |
| `relogios` | relógios de cidades com o status de cada mercado | Nova York avisou |
| `gangorra` | pouca gente = um empurrão vira balanço enorme (liquidez) | Nova York avisou |
| `semaforo` | vermelho = não opera o susto, verde = confirmou | Nova York avisou |
| `balanca` | real x dólar, pende para o lado mais pesado | Dólar disparou |
| `cambio` | letreiro de palhetas da casa de câmbio vira o preço | Dólar disparou |
| `termometro` | sobe até o limite, o limite é ampliado, continua subindo | Dólar disparou |
| `carrinho` | produtos caem no carrinho com a etiqueta ▲ | Dólar disparou |
| `luneta` | o mentor olha para o que o investidor espera | Dólar disparou |
Para o próximo vídeo: ler o roteiro, perguntar "qual objeto do dia a dia mostra isso?" e criar o ambiente novo no `ludico.js`
(mesmo jeito de desenhar), registrando aqui. Repetir só o que a frase pedir igual (ex.: fotos no resultado da eleição).

## Como fazer
1. Roteiro na fórmula do LUDICO.md (85-90 s, número exato com hora e lugar, fonte com data) > aprovação.
2. Voz: a do cliente (X-Trader = voz clonada "Estéfano Santos" no ElevenLabs, sempre `eleven_v4`), partes de até ~1.000 caracteres,
   números por extenso no texto da voz ("cinquenta e um vírgula setenta e nove por cento", "ê dáblio zê"). Baixar pelo site
   (o conector não devolve o arquivo): botão de download do nó no fluxo.
3. Transcrever a narração com tempo por palavra (`segments[].words[]`).
4. `plano.json`: uma cena por bloco, alternando cenários (no máximo 2 cenas seguidas no globo).
   - Número que a transcrição quebra em dois ("51" + ",79%"): usar o segundo exato.
   - Cidades perto (Brasília e São Paulo) empilham os nomes quando o globo afasta (igual à referência). Nas cenas com 3 tópicos, zoom 1,1-1,2.
5. `python3 SKILL_DIR/presets/ludico/gerar.py plano.json <pasta> [--tema <marca>] [--render saida.mp4 --gif]`. Exemplo neutro: `exemplo/plano.json`.
6. Conferir quadros: `npx --yes hyperframes@<versão> snapshot <pasta> --at 0,3,...` (`npx.cmd` no Windows) (o quadro 0 já com cenário, nada
   cruzando texto, placa cabendo, carimbo fora dos objetos). No Windows o `centro.py preto` do Gab falha (não acha o `npx`).
7. Storyboard > aprovação > render > DaVinci (motion na V1, narração na A1, legenda GAB USA no software, música e SFX).

## Primeiro vídeo feito com ele
`CLAUDE BRAIN/X-Trader/Ludico/planos_dos_videos/plano_Circuit_Breaker.json` (26/10/2026): disjuntor > globo > blocos caindo > barras >
globo NY > palco > placas > plenário acendendo > CTA no globo. 9 cenas, 88,8 s.
