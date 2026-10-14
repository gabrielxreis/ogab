# Preset KINETIC (tipografia cinética)

Cada batida da fala vira uma CENA curta (0,4-2 s) com palavras ENORMES numa grotesca larga e pesada (Archivo 900,
largura 125), trocando no ritmo da voz. O que faz o estilo (observado quadro a quadro no reel de referência):
- **Hierarquia**: linha pequena em cima ("E ANTES DE"), palavra gigante, linha na cor ("PERGUNTAR"), forma ao lado/acima.
- **Ecos**: a palavra repetida em contorno acima e abaixo; **pilha** de palavras que vira pirâmide de ecos.
- **Caixa vermelha** atrás de uma palavra ("ISSO NÃO É UM [PLUGIN]") e palavra em vermelho no meio da frase.
- **Faixa** vermelha inclinada com texto em itálico ("SÉRIO?").
- **Interface**: caixa de prompt digitando com tokens destacados e botão enter; RENDER com barra e ETA contando; ponto de
  gravação com anel tracejado girando; cantos de visor de câmera com REC piscando.
- **Formas**: cubo 3D girando, círculo que vira triângulo e quadrado, estrela de explosão, "?" gigante.
- **Peso da letra** muda (900 -> fina) no fim de uma frase de reação.
- **Fundos**: preto vivo (brilho vermelho, bokeh flutuando, grade de pontos), vermelho chapado com linhas, branco com
  grade fina, grafite para termos técnicos.
- **Transições** de 3-5 quadros: chicote com desfoque, glitch de barras, risco de luz vermelha, zoom através, vertical,
  flash. A câmera deriva o tempo todo (zoom + leve giro); nada fica parado. Estudado num reel de tipografia cinética (13/10/2026): "NO / FUCKING / WAY." -> "OKAY." -> "CAN YOU
BELIEVE THAT".

Serve para: gancho, reação, frase de efeito, lista rápida, anúncio de novidade, abertura de vídeo de tecnologia/negócio.
Não serve para: tema delicado, emocional ou religioso calmo (é agressivo de propósito).

Exemplo: `exemplo/exemplo.mp4` (17 s, 15 cenas com todos os tipos), plano em `exemplo/plano.json`. Campos de cada tipo: docstring do `gerar.py`.

## Como pedir
`/ogab faz um motion no preset kinetic com <frase ou trecho>` (ou `preset: kinetic` no estilo.md do cliente).
Funciona em tela cheia (com narração por baixo) ou como abertura de 3-6 s antes do apresentador.

## Processo (o que o Gab faz)
1. Pegar o trecho na transcrição palavra a palavra (`transcricao.json`). Quebrar em BATIDAS: 1-3 palavras por batida,
   cada batida começa na palavra falada (regra do motion na palavra). `dur` = início da próxima batida - início desta.
2. Escolher o TIPO de cada batida pelo sentido: palavra de impacto -> `palavra` (glitch/zoom + flash); pergunta ou frase
   em 3 partes -> `hierarquia` com forma; repetição/ênfase -> `eco`; negação/correção -> `caixa`; reação curta ->
   `faixa`; "você escreve/pede" -> `prompt`; espera/processo -> `rec` ou `render`; lista de termos -> `pilha_eco`;
   "3D", "forma", produto -> `forma`; indignação/surpresa -> `explosao`; câmera/gravação -> `visor`.
   Nunca o mesmo tipo nem o mesmo tema duas vezes seguidas; uma cena de grafite no máximo a cada 6.
3. Cor de destaque = cor da marca do cliente (`cor`; padrão vermelho #E8202A) e `brilho` do fundo preto na mesma cor.
4. `python3 presets/kinetic/gerar.py plano.json <pasta>/motions/kinetic --render <pasta>/motions/kinetic.mp4`
   (30 fps; ~1 min para 7 s). Conferir uma folha de quadros: nenhuma palavra cortada na borda.
5. Som (sonorização do Gab): cada batida ganha um golpe seco (hit/impacto curto), chicote = whoosh rápido, glitch =
   ruído digital curto, digitar = tecla; música com batida marcada e cortes NA batida.

## Regras de bom gosto
- No máximo 3 linhas por batida e 12 caracteres por linha; palavra longa encolhe sozinha (ajuste automático de largura).
- Batida mínima 0,35 s (menos que isso não dá para ler); segurar a última 1 s.
- Palavrão do original: trocar por ênfase limpa ("NÃO / DÁ PRA / ACREDITAR"), salvo se o cliente pedir.
- Legenda: em cima da tipografia cinética não vai legenda (o texto já é a fala); legenda volta no take seguinte.
