# Preset de estilo: igreja / culto

Flyer e story de culto, congresso de jovens, noite de louvor, avivamento e conferência. Aprendido em 16/10/2026 dissecando 7 templates PSD profissionais do gênero (feed 1080x1350, retrato 1440x1920, story 1080x1920 e 2160x3840, cartaz A4). Os templates em si não estão neste repositório (licença do banco de imagens); aqui ficam só as técnicas.

Duas variações:

| Variação | Quando | Cara |
|---|---|---|
| **Show gospel** (6 de 7 templates) | culto, congresso, noite de jovens, avivamento, conferência com preletor/cantores | palco escuro, feixes de luz, pessoa recortada no centro, título enorme com duas fontes misturadas, laranja/creme ou roxo/lilás |
| **Colagem** | culto de oração, devocional, evento mais "editorial" | fundo preto, recortes de papel coloridos (vetor), foto P&B pequena, título em fonte alta e estreita atravessando a peça |

## Árvore de camadas (show gospel)

Os templates repetem esta ordem quase idêntica (grupos em MAIÚSCULAS, de cima para baixo):

```
TAG / DELETE      selo "IMAGE NOT INCLUDED" (apagar na entrega)
AJUSTES / EFEITOS acabamento: Pesquisa de cores 10-50%, Curvas 20%, Brilho/Contraste,
                  Preenchimento de cor em Luz suave 70% ("LUZES + GAMA"), Níveis
LUZ               feixes/raios de luz em pixel: Sobrepor 30% ou Superexposição de cores 20%,
                  com Preenchimento de cor em Cor recortado para tingir a luz
TEXTURA / NOISE   ruído em Sobrepor 50% ou Luz linear; texturas em Tela; "plástico" em Luz suave
PRELETOR          "PRELETOR(A) NOME" pequeno, tracking 200, entre dois traços (formas)
TÍTULO            a palavra do tema, gigante, centralizada, sobre o peito/abaixo da pessoa
TEXTO / NOMES     cantores e preletores em linha: FUNÇÃO (cor de destaque) / NOME (branco), separados por "//"
DATA E HORA       pílula arredondada com degradê, ou números grandes nos cantos (22 / 03, 19 HRS)
RODAPÉ / LOCAL    endereço numa pílula escura com ícone de local, tracking 200
DEGRADÊ           1-2 Preenchimentos de cor com máscara de degradê (escurece embaixo para o texto ler)
IMAGEM / FOTOS    pessoa(s) recortada(s) + sombra em Multiplicação + luz recortada nela (Tela 59%, Sobrepor 40%)
                  + "Brilho interno" em Tela recortado + Preenchimento de cor em Luz direta 50% (cor da luz na pele)
SHAPE / GLOW      atrás da pessoa: anéis gigantes (a LETRA "O" da fonte do título, 4 cópias em 620-840 px
                  com Sobreposição de degradê + sombra) ou glow (Preenchimento de cor em Tela com máscara)
BACKGROUND        foto de palco/show (pode ser gerada por IA) como smart object + Preenchimento de cor
                  em Cor (recorte) para tingir tudo na paleta
```

## Técnicas que fazem o estilo

1. **Título com duas fontes na MESMA palavra.** Uma fonte "display" cheia de personalidade (Dirtyline 36 Days of Type) nas letras das pontas e uma serifa itálica (The Coffins Italic) no miolo: "**P**ro**fétic**O", "**F**evereir**O**", "Aviva / mentO". Cor de destaque só em algumas letras. Tracking -20 a -40.
2. **Palavra de apoio em script** atravessando o título ("Culto" em letra cursiva sobre "JOVENS"), ou fita/faixa inclinada com o subtítulo (smart object "FITA" + texto em cima).
3. **Título partido em duas linhas desalinhadas** ("AVIVA" / "MENTO"), centralizado, ~200 px de altura de letra num feed 1080.
4. **Pessoa no centro, recortada, iluminada pela cor do palco:** Preenchimento de cor em Luz direta 50% recortado na foto + luz em Tela/Sobrepor recortada + sombra suave atrás (Multiplicação).
5. **Anéis de luz atrás da pessoa feitos com tipografia:** a letra "O" da fonte do título, enorme, repetida 4 vezes em tamanhos diferentes, com Sobreposição de degradê. Barato e editável.
6. **Tingir o fundo inteiro:** foto de palco qualquer + Preenchimento de cor em modo **Cor** por cima = fica na paleta da peça. O mesmo truque em fitas e elementos (camada "COR" recortada em modo Cor).
7. **Linha de créditos padrão:** `FUNÇÃO` (pequeno, cor de destaque) em cima de `NOME` (branco), blocos separados por `//`, tudo numa grotesca larga (Stretch Pro) com tracking 40. Ex.: "PR. PRESIDENTE AUGUSTO MELO", "CANTORA / ANA SOARES".
8. **Data em pílula** com Sobreposição de degradê e texto escuro itálico, ou **números grandes nos cantos** (dia em cima, mês embaixo; hora do outro lado).
9. **Endereço em pílula escura** com ícone de local (smart object com Sobreposição de cor) e texto com tracking 200.
10. **Acabamento cinematográfico em pilha:** LUT 10-50% + Curvas 20% + Preenchimento de cor em Luz suave 70% + ruído em Sobrepor 50% + grão em Multiplicação. Nunca um ajuste forte.
11. **Luz de palco:** feixes em pixel em Superexposição de cores/Luz linear/Tela, alguns fora da prancheta (posições negativas) para entrar só a ponta.
12. Mesclagens mais usadas, em ordem: **Tela**, **Cor**, **Superexposição de cores**, Sobrepor, Luz suave, Luz linear, Multiplicação. Efeitos mais usados: **Sobreposição de degradê** (30x), Sombra projetada (15x), Sobreposição de cor (15x).

## Colagem (variação)

Fundo preto, um retângulo "papel" claro no centro, 10+ recortes vetoriais coloridos (smart objects com Sobreposição de cor: verde-limão, rosa, laranja, verde-escuro), textura de papel em Multiplicação 50% por cima, foto P&B da pessoa orando embaixo, título "SUNDAY / PRAYER" em **Six Caps** gigantesco (1769 px num A4) cor creme #F7EDD0, data em **Climate Crisis**.

## Variação "banco internacional" (8 templates de banco, 16/10/2026)

Mais simples e mais "limpa" que o show gospel. Árvore curta: `Logo / Social Media / Text / Design / Image / Background` (às vezes `Adjustments FX`, `Back Text`, `NOISE`). Técnicas:
- **Palavra repetida empilhada**: o tema 3x em condensada gigante (Bebas Neue), uma linha cheia e as outras vazadas/transparentes, pessoa recortada na frente.
- **Texto em arco** sobre a cabeça da pessoa ("SUNDAY WORSHIP SERVICE") com ícone pequeno no centro do arco.
- **Ícones de linha fina** (cruz, estrela de 4 pontas, raios) em branco, como ornamento.
- **Script por cima** de uma palavra em serifa/condensada ("worship", "santa"), em cor de destaque.
- **Caixa alta com tamanhos misturados** em serifa itálica (Playfair Display Italic) para frase acolhedora ("A PLACE WHERE YOU'RE WELCOME").
- Fitas de pincel coloridas (azul/vermelho) e rabiscos amarelos atrás da pessoa.
- Data e hora em Bebas Neue com script ao lado ("11TH September"), redes sociais em linha com ícones.
- Efeito mais usado: **Sombra projetada** (texto sobre foto). Fontes: Bebas Neue, Playfair Display Italic, DM Sans, Montserrat Black, Roboto (todas Google).

## Tipografia

| Papel | Fonte dos templates | Licença / alternativa |
|---|---|---|
| Título display | Dirtyline 36 Days of Type 2022, Establo, Billion Dreams | Dirtyline: gratuita (36 Days of Type). Alternativa Google: Bricolage Grotesque Black |
| Serifa itálica do título | The Coffins Italic | Alternativa Google: Playfair Display Italic, DM Serif Display Italic |
| Script de apoio | Alberobello Script, Flashback Records | Alternativa Google: Great Vibes, Allura |
| Créditos / data | **Stretch Pro** (35 usos) | Alternativa Google: Unbounded, Michroma |
| Texto corrido | **Sora** (Google), **Poppins** (Google) | gratuitas |
| Colagem | **Six Caps**, **Climate Crisis** | ambas Google Fonts |

## Paletas

- **Laranja quente:** fundo quase preto, laranja #FF8000 / salmão #FE9A68 / #F99967, creme #FFD8AC, branco #FFFFFF / #EEEEEE.
- **Roxo/lilás:** fundo roxo profundo, lilás, branco quente #DFDBD8, texto escuro #131431 em pílula clara.
- **Prata/grafite:** fundo cinza escuro, laranja de destaque, branco #F3F3F3.
- **Colagem:** preto, creme #F7EDD0, verde-limão, rosa, laranja, verde-escuro.

## Receita do Rick (show gospel, feed 1080x1350)

1. Pedir: tema (palavra do título), data/hora, local, preletor, cantores, foto(s) recortável(is), paleta (laranja, roxo ou da igreja).
2. Fundo: foto de palco/show (do banco do usuário ou **gerada por IA, só perguntando antes**) como smart object + Preenchimento de cor em modo Cor.
3. Pessoa: colocar como smart object, Selecionar assunto + máscara, sombra em Multiplicação atrás, luz recortada em Tela, Preenchimento de cor em Luz direta 50% recortado.
4. Anéis de "O" ou glow atrás da pessoa.
5. Degradê escuro embaixo, título em duas fontes com 2-3 letras na cor de destaque, linha de créditos, data em pílula, endereço em pílula.
6. Acabamento: grupo AJUSTES (LUT + Curvas + Preenchimento em Luz suave) e TEXTURA (ruído).
7. Exportar PNG, conferir com os olhos (texto legível no celular, nada em cima do rosto), entregar o PSD com a árvore acima.

Tokens em `preset.json`.
