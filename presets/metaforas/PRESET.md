# Preset METÁFORAS ("1 prompt, 1 vídeo")

Réplica do processo dos 5 vídeos "1 prompt · 1 vídeo" da página "O Minimalista com IA" (estudados quadro a quadro em
13/10/2026): **roteiro curto de 4-6 frases; cada frase vira UMA metáfora visual; tudo em preto e branco; o protagonista
é o único elemento claro/brilhante, o resto em cinza.** O mesmo roteiro pode sair em estilos diferentes (na referência,
os vídeos 1 e 3 são o mesmo texto em duas estéticas; 4 e 5 também). Lá eles saem de um gerador de vídeo (e vêm com erro
de texto); aqui saem em código (HyperFrames + canvas), com o texto sempre certo e editável.

Exemplos (11-12 s cada) em `exemplos/`: `a_destaque_previa.mp4`, `b_bolhas_previa.mp4`, `c_grade_previa.mp4`, `d_objetos_previa.mp4` (prévias leves) + os planos `.json`.

## Estilos
| Estilo | Referência | Visual | Texto | Transição |
|---|---|---|---|---|
| `destaque` | vídeo 1 | formas e ícones chapados cinza, protagonista branco com brilho | legenda condensada em caixa alta embaixo; frase grande no meio | íris: a cena seguinte nasce de dentro do protagonista |
| `bolhas` | vídeo 3 | bokeh no fundo, personagens-bolinha (com olhos e boca) | digitado letra a letra, caixa alta | fade |
| `grade` | vídeos 4 e 5 | piso de grade em perspectiva andando, cartões de vidro, silhueta em salão branco | palavras sobem uma a uma no topo | empurra a câmera |
| `objetos` | vídeo 2 | objetos com volume sobre piso com reflexo (quadrado vira esfera, digital, aviões) | letras caem | desliza |

## Catálogo de metáforas (frase -> cena)
| A frase fala de... | `metafora` |
|---|---|
| ser um entre muitos, destacar-se, "enquanto todos..." | `um_entre_muitos` (bolas ou `icone`, `alvo` = qual brilha) |
| trabalhar, executar, fazer em silêncio | `trabalhando` (monitor com código digitando, pessoa de costas) |
| as pessoas reclamam, opinam, julgam | `multidao` (cinzas com balões, protagonista à parte) |
| a conclusão, a virada, "você resolve" | `frase` (texto grande + check desenhando) |
| subir, se separar, crescer acima | `sobe_da_pilha` |
| esforço, insistir, empurrar | `empurra` |
| transformar, moldar, virar outra coisa | `forma_vira` (quadrado vira esfera) |
| ser autêntico, identidade | `identidade` (fila de peças, uma com digital) |
| mudar de rumo, ir contra a maré | `revoada` (aviões de papel, um vira) |
| oportunidade, novo começo | `porta` (porta de luz com escada) |
| planejar, rotina, progresso | `caminho` (corredor e o caminho se montando) |
| data, prazo, todo dia | `calendario` (`dia`, `mes`, check) |
| hábitos, tarefas, áreas da vida | `cartoes` (`icones`: 3 nomes de Material Symbols) |
| resultado, nova vida, conquista | `heroi` (silhueta no salão branco) |

## Processo (o que o Gab faz)
1. Roteiro: 4-6 frases curtas (2-3 s cada; 10-15 s no total) ou o texto do usuário quebrado assim. Uma ideia por frase.
2. Para cada frase escolher a metáfora da tabela (a pergunta: "o que a pessoa precisa ver para entender isso?").
   Faltou metáfora? Criar a função nova no `kit/metaforas.js` (mesma assinatura) e acrescentar na tabela.
3. Estilo: o que o usuário pedir; sem pedido, `destaque`. Cor da marca: `"cores": {"hi": "#fd7f3b"}` troca o branco do protagonista.
4. `python3 presets/metaforas/gerar.py plano.json <pasta>/motions/metaforas --render <pasta>/motions/metaforas.mp4` (~2 min).
5. Som: piano/ambiente minimalista, whoosh leve nas transições, "ding" no check, sem impacto pesado. Narração opcional
   (com narração, cada cena dura o tempo da frase falada; legenda GAB USA sai, porque o texto já está na tela).
