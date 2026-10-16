# Preset GLASS (16:9, YouTube, apresentador falando)

Enviado pela comunidade em 15/10/2026 (nome original: vidro violeta). Ao entrar na skill: `\b` da troca de cor (`cor`) consertado (tinha virado um caractere de controle), quebras de linha do Windows convertidas e HyperFrames fixo em 0.8.151. Prévia: `exemplo.gif` (os 7 motions do `exemplo/plano.json`, transparentes sobre cinza).

Motions premium em vidro escuro: aurora violeta, grão de filme, hairlines, título metálico (branco -> lilás), destaque em
Playfair itálico, números em Inter fina, revelação por máscara com desfoque, brilho que atravessa os cartões, anéis de
ícone girando. Abertura dinâmica: as cenas entram e saem com SLIDE em sincronia com a câmera da V1 (empurrão de câmera:
o vídeo anda 60%, a cena 100%, então nunca aparece buraco preto), mais punch-ins e zoom out nos takes. Stingers de
capítulo (painéis diagonais) e cartão de like + inscreva-se com a foto do canal e cursor clicando.
Estudado num vídeo de YouTube sobre estrutura de página de vendas (15/10/2026); ritmo da abertura inspirado em vídeos de
"agente de IA" com cenas de UI trocando a cada ~2 s.

Serve para: YouTube explicativo/tutorial com webcam e gravação de tela, marketing digital, negócio, tecnologia.
Não serve para: vertical 9:16 (layout é 1920x1080), vídeo emocional/religioso calmo.

## Arquivos
- `gerar.py plano.json <pasta> [--render] [--so ids] [--fps 24]`: todos os tipos e campos na docstring.
- `kit/base.py` (tipos de tela cheia, laterais, stinger, inscreva) e `kit/cenas.py` (cenas com slide e prints).
- `camera_davinci.py camera.json`: zoom/punch-in/slide na V1 pelo Fusion de cada clipe (motion blur). `--tirar` desfaz.
- `exemplo/plano.json`, `exemplo/camera.json`, `exemplo/imagens/` (imagens neutras de exemplo).
- `kit/fonts/`: Inter e Playfair Display Italic (licença SIL OFL 1.1, redistribuíveis).

## Processo
1. Tempos ABSOLUTOS da timeline, cada evento na palavra falada (âncoras na transcrição palavra a palavra).
2. Lateral sem BG na faixa livre da direita (webcam) ou abaixo do facecam (`"pos": "tela"`); tela cheia quando a ideia
   pede (número, comparação, lista, passos, print). Prints/fotos do usuário (Media Pool) SEMPRE no lugar de dado inventado,
   com `anel` e `caixa` (frações da imagem) marcando o número que importa.
3. Cenas com slide: alternar `dir` (1, -1, 1...) e passar os mesmos início/fim para `camera.json > slides`.
4. `cor` no plano troca o violeta pela cor da marca (gira o matiz só dos tons violeta).
5. Render: com BG = MP4; com slide e laterais = MOV ProRes 4444 com alfa. Prova no DaVinci em ProRes 422 LT.
6. Som: whoosh em cada slide (entrada e saída), clique no cursor, impacto em número e ✗, check nos itens, stinger = whoosh
   de transição + subdrop. Trilha de abertura ~12-13 LU abaixo da voz (ducking -8 dB, EQ -4 dB em 2,5 kHz na música).

## Armadilhas resolvidas (não repetir)
- Nunca animar `width`/`letterSpacing` (lint do HyperFrames): usar `scale`/`scaleX`.
- `fromTo` com `immediateRender` mostra o elemento antes da hora: usar `immediateRender:false` em piscas/partículas.
- Anel SVG com `vector-effect:non-scaling-stroke` quebra o "desenhar" (`pathLength`): não usar.
- Elementos fora da cena vazam no slide: `overflow:hidden` no contêiner `#sl`.
- Saída do stinger precisa terminar antes do fim do clipe (cascata até dur-0,1 s).
- Medir o cursor no layout real depois das fontes (`document.fonts.ready`), não por coordenada fixa.
- Nomes de arquivo com acento: comparar em NFC; nome de cópia por MD5 (o `hash()` do Python muda a cada execução).
