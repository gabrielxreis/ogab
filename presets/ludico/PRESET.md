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
1. **O preset é o JEITO DE DESENHAR, não um catálogo.** Estilo fixo: cores do cliente, estúdio de fundo infinito grafite com luz suave (ver VISUAL = a referência Ludificando),
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
| `quique` | bola despenca e quica de volta (queda e reação); `cai_em`, `sobe_em` | Mercado reagindo |
| `bussola` | agulha sai de FATOS e aponta EXPECTATIVAS; `baixo`, `cima`, `em` | Mercado reagindo |
| `cofre` | cofre abre e as pilhas de US$ acendem (patrimônio); `rotulo`, `em` | Mercado reagindo |
| `escudo` | flechas vermelhas batem no escudo do RISCO e caem; `selo`, `em` | Mercado reagindo |
| `bifurcacao` | placa de estrada com dois caminhos e o "?" (CTA de escolha); `esq`, `dir`, `esq_em`, `dir_em` | Mercado reagindo |
| `seguir` | celular com o perfil: o dedo aperta SEGUIR e vira SEGUINDO; `perfil`, `bio`, `inicial`, `em` | todos os 6 de 27/10 ("me segue aqui") |
| `setas` | duas setas no mesmo dia, uma despenca e outra sobe; `lados: [{rotulo, valor, dir: sobe|desce, em}]` | Brasil despenca, Nasdaq sobe |
| `moeda` | moeda gigante gira: frente e verso (oportunidade x risco, sobe x cai); `frente`, `verso`, `em` | Brasil despenca / Washington (CTA) |
| `pilha` | pilha de moedas cresce (construir aos poucos); `rotulo3d`, `em`, `fim_em` | Brasil despenca |
| `instagram` | **CTA de seguir** ("me segue aqui"): celular 3D com o perfil igual ao app (modo escuro), foto com anel, posts/seguidores/seguindo, nome, bio, link, destaques e a grade com as capas REAIS; o toque aperta "Seguir" e vira "Seguindo". `perfil: {user, nome, posts, seguidores, seguindo, bio: [linhas], link, nota, destaques, fixados, foto, capas: [...]}`, `em` = palavra do "segue". Vídeo sem a fala de seguir: criar a cena no fim com ele | todos os de 27/10 (substituiu o `seguir`) |
| `martelo` | martelo da decisão bate no bloco; `placa`, `em` | Decisão em Washington |
| `ima` | ímã puxa as moedas de um lado para o outro (capital que sai/vai); `esq`, `dir`, `em` | Washington / Por que reagiu |
| `domino` | efeito dominó com rótulo em cada peça; `pecas: [{t, em}]` | Decisão em Washington |
| `escada` | boneco sobe degraus rotulados; `degraus: [{t, em}]` | Decisão em Washington |
| `leilao` | carimbo CANCELADO no leilão e os títulos voltam para a caixa; `cancela_em`, `recompra_em`, `placa`, `caixa` | Governo agiu |
| `sismografo` | agulha risca o papel e o tremor cresce na palavra; `rotulo3d`, `em` | Governo agiu |
| `cartao` | cartão de crédito e a etiqueta do juro que vira; `de_txt`, `para_txt`, `em` | Governo agiu |
| `foguete` | foguete sobe com chama e fumaça (ação disparou); `em`, `altura` | Celestica disparou |
| `chip` | chip de IA liga os servidores; `chip`, `em`, `servidores_em` | Celestica disparou |
| `planta` | planta cresce no vaso e brota moedas (tendência, tempo); `em`, `fim_em` | Celestica disparou |
| `dado` | dado rolando (não é garantia); `em` | Celestica disparou |
| `urna` | cédulas caem na urna e sobe o resultado; `titulo`, `resultado`, `em` | Por que o mercado reagiu |
| `alvo` | a aposta mirava o centro e o dardo cai fora (expectativa frustrada); `mira`, `em` | Por que o mercado reagiu |
| `balao` | balão que enche (gastos, dívida, desconfiança); `rotulo3d`, `em`, `raio` | Por que o mercado reagiu |
| `ponte` | boneco atravessa a ponte de um lado ao outro; `esq`, `dir`, `selo`, `em`, `fim_em` | Por que o mercado reagiu |
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

## SFX: quando cada som cai (aprendido em 27/10/2026, timing revisado a pedido do Gabriel)
- **Troca de cena:** o pico do whoosh vai no MEIO do movimento, não no corte. Estúdio > estúdio: a câmera viaja 1,15 s (eio) a partir do `de` da cena, pico em `de + 0,55`. Globo <> estúdio: fade de `de - 0,12` a `de + 0,33`, pico em `de + 0,15`. Medido por diferença de quadros no render: o movimento cai entre +0,25 e +0,95 s, nunca antes do `de`.
- **Objeto que bate ou cai** (bola, flecha, peso no telhado, dardo, peça de dominó): o som vai no instante do contato, não na palavra (bola: `cai_em + 0,65`; flecha k: `em + 0,45 + 0,45k`; peso: `peso_em + 0,45`; dardo: `em + 0,5`; dominó: um som por peça em `em + 0,32`).
- **Arquivo com mais de uma batida** (martelo do juiz): cortar a duração para ficar com uma só.
- Os tempos de palavra da transcrição do DaVinci batem com o áudio (0,05 a 0,15 s); se o som parecer fora, o erro está no instante escolhido, não na transcrição.

## Cartão: topo limpo (Gabriel, 27/10/2026: "aqui em cima eu acho muito sujo, para um início tudo bem, mas seria legal depois sair")
A série, a pílula da seção e a linha de fontes aparecem só na primeira cena; depois somem e o cartão sobe, ficando só as palavras-chave (etiqueta, número, tópicos, carimbo). As fontes voltam discretas no CTA. `"topo_ate": <segundo>` muda quando some; `"topo_ate": false` mantém o topo o vídeo todo.

## Movimento contínuo (Gabriel, 27/10/2026: "achei todos os motions muito parados; ele termina o movimento, tem que entrar outra coisa, senão não retém a pessoa")
Nenhum quadro parado: terminou uma animação, entra outra. O kit faz sozinho:
- **Câmera viva:** órbita de 0,06 rad/s alternando o lado a cada cena (`"orbita"` na cena muda), aproximação contínua de 2,2%/s até 25% (`"aproxima"`), leve sobe e desce.
- **Batidas** (`gerar.py` > `batidas`): em cada cena, nos vãos sem evento, a palavra forte seguinte (4+ letras ou número, 0,9 s longe de outro evento, 1,3 s da batida anterior) ganha empurrão de câmera, pulso do cenário, onda no chão e estouro de faíscas na cor da marca; no globo, um leve zoom. `"batidas": false` desliga; uma lista de segundos manda. Cada batida leva um whoosh curto bem baixo (-24 dB).
- Ao criar um cenário novo, pensar também no que se mexe DEPOIS do movimento principal (respiração, segundo estágio), não só na entrada.

## Tela sempre mudando (Gabriel, 27/10/2026: "ele cai a bola e fica um tempão na bola, sendo que já poderia ir para outra coisa")
Cena = UM elemento por ideia da fala, de 2 a 4,5 s (CTA até 7 s). Frase longa vira 2-3 cenas seguidas, cada uma com um ambiente diferente (ex.: "queda histórica" > bola despenca; "sinais de recuperação" > candles voltando; "fatos x expectativas" > bússola e depois balança). O `gerar.py` para com `CENA_LONGA` e lista as cenas a quebrar; `"cena_max": <s>` no plano só com motivo.

## Iluminação variada (Gabriel, 27/10/2026: "não precisa ter aquele holofote de luz o tempo todo, pode explorar outras coisas")
O holofote em cone NÃO é a assinatura do estilo: cada cena alterna sozinha entre 6 iluminações (a luz de verdade, com sombra, vem do pool fixo; muda só o que se vê):
`neon` (aro grosso de neon no chão com reflexo), `contraluz` (halo grande atrás, objeto em silhueta com contorno), `feixes` (dois fachos cruzados dos lados), `grade` (chão com grade luminosa e brilho no horizonte), `janela` (fachos verticais atrás) e `cone` (o holofote clássico, ~1 a cada 6 cenas). `"luz": "<estilo>"` na cena força um; `"luzes": [...]` no plano define a sequência. Cenário novo: chamar `holofote(grupo, x, z, raio)` normalmente (ele desenha o estilo da cena) e pensar se a cena pede outra luz.

## VISUAL = a referência Ludificando, igual (Gabriel, 27/10/2026: "esse tá muito mais bonito e lapidado, o lúdico não precisa ter o holofote o tempo todo"; depois: "exatamente igual, olhe todos os detalhes")
Referência: instagram.com/p/De56numApif (Ludificando, 22 s), medida quadro a quadro. O estilo de luz `estudio` reproduz e é o PADRÃO de todas as cenas:
- **Fundo infinito:** grafite uniforme (#1E1E1C) com um clarão leve atrás do assunto, sem parede nem linha de horizonte. O canvas 3D fica transparente e o fundo é pintado no `#root`; o chão vira só sombra (`ShadowMaterial`).
- **Argila:** objetos cinza quente (#7A7870 / #4E4D48 / #5E5D57 no tema padrão), caixas com canto arredondado (`"cantos": false` volta ao cubo), luz-chave branca de frente-alto e sombra macia.
- **Destaque aceso:** tudo que está na cor da marca sai saturado e emissivo (fora do tone mapping) e vaza brilho em volta (bloom em 2D). Campos: `"brilho": 0.4` (0 desliga) e `"acesos": false`.
- **Lente longa e composição da referência:** `"lente": 22` (graus), `"folga": 0.8` (o cenário ocupa ~60% da largura), `"elevacao": 26` (câmera olhando de cima, mostra o topo das peças) e o assunto no meio da tela entre o cartão e a legenda.
- **Legenda (quando o plano pede):** caixa escura arredondada, a palavra falada agora na cor, a já dita branca, a que vem cinza; quebra em 2 linhas.
- **Montagem:** as peças do cenário nascem pequenas e crescem passando do ponto, da esquerda para a direita, enquanto a câmera chega (`"montagem": false` na cena ou no plano desliga).
- **Poeira bokeh:** poucas bolas grandes e bem desfocadas (`"poeira": 18`).
- **Cartão:** kicker `• SÉRIE` em mono branco com ponto na cor, fixo o vídeo todo; sem pílula de seção (ela só aparece se alguma cena tiver `secao`).
  `"manchete": "A *IA*:"` = título bold, palavra entre asteriscos na cor (não confundir com `titulo`, que é o texto 3D de placar/câmbio/cartão/urna).
  `"chips": [{"texto": "PESQUISOU", "em": 4.1}, ...]` = pílulas na cor que vão se SOMANDO.
  `"continua": true` = a cena segue a ideia da anterior: o cartão fica e só ganha os chips/tópicos novos (o "A IA: PESQUISOU > ESCREVEU > NARROU > MONTOU EM 3D" da referência).
- **Glow (bloom):** só o que é ACESO brilha (limiar pela média dos canais: amarelo da marca e ícone branco passam; ouro e cinza não; `"brilho_limiar": 0.74`). Feito em 1/4 da resolução, com o fundo virando transparência e o halo somado só como luz.
- **30 qps** como a referência (24 deixa o movimento picotado). Tecla/peça que acende entra com transição de 0,28 s e pulso, nunca de um quadro para o outro. NÃO usar `mix-blend-mode` (o render do HyperFrames ignora e o quadro escurece). `"brilho": 0.3`.
- **`continua` também no 3D:** a cena que continua a ideia fica no MESMO cenário (sem viagem de câmera) e o cenário evolui com os campos da continuação. Réplica fiel da referência: cenário `mesa` (monitor com play aceso, monte de moedas douradas que chovem e empilham, teclas com ícone que acendem em fases: `"acesas"`, `"acende_em"`, `"teclas"`, `"pilhas"`). Plano de teste: 3 cenas "A IA: PESQUISOU > ESCREVEU, NARROU > MONTOU EM 3D" com `continua`.
- Conferir quadros: o PRIMEIRO quadro de um `snapshot` às vezes sai antes da cena carregar; pedir um tempo descartável primeiro (`--at 0.05,...`) ou conferir no MP4.
- As outras luzes (`contraluz`, `neon`, `janela`, `feixes`, `grade`, `cone`) ficam para quando a frase pedir: `"luz": "<estilo>"` na cena ou `"luzes": [...]` no plano.
- Marca de cliente: o tema dela troca as cores (fundo, objetos, destaque); a luz, a montagem e o cartão continuam os da referência.
- Ao criar cenário novo, pensar como a referência: o cenário **acumula** entre frases da mesma ideia (o monitor fica, chegam as moedas, depois o teclado, depois o celular na frente), chuva de objetos que empilham, e um campo de peças acesas desfocadas ao fundo para dar densidade.
