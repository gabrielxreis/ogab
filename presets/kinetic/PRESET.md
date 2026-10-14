# Preset KINETIC (tipografia cinética)

Cada batida da fala vira 1 a 3 palavras ENORMES na tela, trocando no ritmo da voz (0,4-1,2 s por batida). Letra
grotesca larga e pesada (Archivo 900, largura 125), fundo alternando **preto com brilho vermelho**, **vermelho chapado**
e **branco**; cada batida entra de um jeito (zoom com desfoque, chicote, pilha de linhas, letras caindo, máquina de
escrever, esticada, glitch RGB), ponto final na cor de destaque, etiqueta pequena que pula ("HA"), círculo de cor e
tremor no impacto. Estudado num reel de tipografia cinética (13/10/2026): "NO / FUCKING / WAY." -> "OKAY." -> "CAN YOU
BELIEVE THAT".

Serve para: gancho, reação, frase de efeito, lista rápida, anúncio de novidade, abertura de vídeo de tecnologia/negócio.
Não serve para: tema delicado, emocional ou religioso calmo (é agressivo de propósito).

Exemplo: `exemplo/exemplo.mp4` (6,6 s), plano em `exemplo/plano.json`.

## Como pedir
`/ogab faz um motion no preset kinetic com <frase ou trecho>` (ou `preset: kinetic` no estilo.md do cliente).
Funciona em tela cheia (com narração por baixo) ou como abertura de 3-6 s antes do apresentador.

## Processo (o que o Gab faz)
1. Pegar o trecho na transcrição palavra a palavra (`transcricao.json`). Quebrar em BATIDAS: 1-3 palavras por batida,
   cada batida começa na palavra falada (regra do motion na palavra). `dur` = início da próxima batida - início desta.
2. Variar: nunca a mesma `entrada` duas vezes seguidas, nunca o mesmo `fundo` duas vezes seguidas. Palavra de impacto
   (número, "NÃO", nome do produto): `zoom` + `flash`. Frase de 3 linhas: `pilha` com a linha do meio em `destaque`.
   Reação curta ("OKAY", "SÉRIO?"): `tag` "HA" ou "?!". Fechamento: `circulo` + `flash`.
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
