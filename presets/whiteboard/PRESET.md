# Preset WHITEBOARD (lousa com a mão desenhando)

Uma **ilustração vira animação de lousa**: a mão de verdade (foto, com punho, dedos e sombra mexendo) traça primeiro
todas as linhas com a caneta, depois pinta os **personagens** cor por cor e por último o **fundo**. O resultado mantém
as cores e a sombra da imagem original. Sai em MP4, pronto para entrar na timeline como motion.

Serve para explicação, aula, mapa, infográfico, personagem ilustrado, "como funciona", história contada em desenho.
Não serve para foto real (o recorte e as linhas são feitos para desenho) nem para texto corrido sem imagem.

Exemplo: `exemplo.gif` / `exemplo/exemplo.mp4` (mapa dos EUA por região, 10 s), imagem em `exemplo/mapa.png`.

Motor: [whiteboard-animation-vi](https://github.com/letuandat131/whiteboard-animation-vi) (código CC0; grade derivada
do SRT Whiteboard, MIT; recorte ISNet, Apache-2.0). Fica FORA da skill, em `~/.claude/ogab_ferramentas/whiteboard`
(~1,1 GB com o PyTorch), instalado pelo instalador do Gab e, para quem já tinha o Gab, sozinho no passo zero depois do
update (`whiteboard.py garantir`). As mãos e o modelo são baixados do projeto original: não copiar para o repo.

## Como pedir
`/ogab faz um vídeo no preset whiteboard sobre <tema>`, "anima essa ilustração na lousa", ou marcar **Whiteboard** no
passo de estilo do `/ogab menu`.

## Processo (o que o Gab faz)
1. Conferir: `python3 SKILL_DIR/presets/whiteboard/whiteboard.py checar` (sai 1 = falta instalar: rodar `instalar`,
   ~5 min na primeira vez, ou esperar a instalação em segundo plano terminar; log em
   `~/.claude/ogab_ferramentas/whiteboard/instalacao.log`).
2. Uma imagem por cena. A melhor entrada é **desenho com contorno escuro e cor chapada** (ilustração, mapa, ícone
   grande, personagem estilo cartoon/anime). Imagem da pessoa ou do cliente: usar a ilustração que ele mandou; gerar
   uma por IA só perguntando antes. Mapa ou diagrama: montar em HTML/SVG com contorno de 2-3 px e tirar o PNG
   (foi assim o exemplo). Fundo branco liso; o texto da imagem também é desenhado à mão.
3. Gerar cada cena:
   `python3 SKILL_DIR/presets/whiteboard/whiteboard.py gerar <imagem.png> <pasta>/motions/wb_01.mp4 --formato vertical --duracao 8`
   - `--formato vertical|horizontal|quadrado|original` (o desenho é encaixado inteiro no quadro, sem corte);
   - `--duracao` total da cena; `--desenho 70` = 70% desenhando e o resto segurando a imagem pronta;
   - `--modo detalhado` (padrão) ou `rapido` (o fundo é pintado por blocos, da esquerda para a direita);
   - `--fundo #ffffff` cor do papel; `--sem-mao` só o traço aparecendo.
   Tempo: ~3 s de render por segundo de vídeo no processador do Mac (1080x1920, 30 qps); com NVIDIA, bem menos.
4. Na timeline entra como motion (vídeo renderizado do preset, como os outros motions), cortado na fala que explica
   aquela imagem. Cena com pelo menos 6 s: a pessoa precisa ver o desenho pronto antes do corte.
5. Som: caneta de quadro raspando enquanto traça, pincel/marcador macio na pintura; música leve de explicação.

## Regras de bom gosto
- Uma ideia por imagem; até 3 palavras de título na própria ilustração.
- Contorno escuro e contínuo: linha clara ou foto viram rabisco sujo.
- Entre as cenas, corte seco ou a mão saindo do quadro; nada de fade.
- Créditos: o motor não exige; imagem de terceiros (mapa, ícone) segue a licença dela (o mapa do exemplo é CC0).
