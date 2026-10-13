# Tracking de texto e animação no editor (DaVinci, Premiere, After Effects)

Quando o usuário pedir "texto que segue a pessoa/o objeto", "tracking", "texto grudado no produto", ou "anima o
clipe" (punch-in, zoom, pan, giro, entrada/saída): fazer no EDITOR escolhido (`config.editor`), com keyframes
editáveis. Testado em 12/10/2026 nos três.

## 1. Rastrear (igual para todos): `scripts/rastrear.py`

```bash
python3 SKILL_DIR/scripts/rastrear.py <video> --rosto --de 0 --ate 8 --saida <pasta>/trilha.json
python3 SKILL_DIR/scripts/rastrear.py <video> --caixa X,Y,L,A --de 1 --ate 7.5 --saida <pasta>/trilha.json --previa <pasta>/previa.mp4
```
- **Rosto:** detector do OpenCV a cada quadro (o maior rosto). Para "texto em cima da cabeça", nome em cartela que acompanha etc.
- **Objeto:** tirar um quadro (`ffmpeg -ss T -i video -frames:v 1 q.png`), OLHAR e estimar a caixa em pixels do VÍDEO (X,Y canto superior esquerdo, L,A). Fluxo óptico nos pontos da caixa; se perder, reencontra pela imagem.
- **Sempre** gerar `--previa` e conferir 3 quadros (começo, meio, fim) antes de aplicar. Rastrear o trecho INTEIRO em que o texto aparece.
- Tempos da trilha = segundos do ARQUIVO (não da timeline). Escala acompanha o tamanho (objeto que se aproxima).

## 2. Aplicar no editor

| Editor | Texto que segue | Animar clipe |
|---|---|---|
| **DaVinci** | `R.texto_rastreado(item, trilha, "TEXTO", deslocamento=(0,-0.11), tamanho=0.07)` cria Text+ + Merge no Fusion DO CLIPE, com keyframes de Center (XYPath), dentro da área segura. `seguir_escala=True` acompanha o tamanho | `R.animar_clipe(item, [(t, {"zoom": 1.0}), (t2, {"zoom": 1.12, "x": .5, "y": .5, "giro": 0})])`: nó Transform "AnimGab" no Fusion do clipe |
| **Premiere** | `P.animar_rastreado(seq, trilha_do_gráfico, inicio_seq, trilha, inicio_no_arquivo, deslocamento=(0,-0.10))` move o gráfico/MOGRT/PNG (Movimento > Posição) | `P.animar(seq, trilha, inicio_seq, [(t, {"escala": 100}), (t2, {"escala": 115, "x": .5, "y": .5, "giro": 0, "opacidade": 100})])` |
| **After Effects** | `AE.seguir(comp, "CAMADA", trilha, inicio_no_arquivo, deslocamento=(0,-120))` cria o null "RASTREIO <camada>" com os keyframes e prende a camada nele (o usuário ajusta a distância arrastando o texto). `seguir_escala=True` faz crescer junto | `"anim"` do spec (formato GSAP) ou `AE.jsx(...)` |

Detalhes que já custaram tempo:
- **DaVinci:** dentro do Fusion de um clipe, o quadro conta na taxa do ARQUIVO (ex.: 23,976 numa timeline 30) e o quadro 0 é o ponto de entrada do clipe (`COMPN_GlobalStart` negativo = antes da entrada). O `_quadro_comp` já faz a conta. Coordenadas do Fusion: 0-1 com Y para CIMA. A timeline do DaVinci não grava keyframe pela API: animação sempre pelo Fusion do clipe.
- **Premiere:** posição em fração do quadro (`[0.5, 0.5]` = centro), escala em %, keyframes contados a partir do início do clipe na sequência (a função soma o ponto de entrada da mídia). A trilha precisa existir (V4 inexistente dá "invalid parameter").
- **Premiere e texto de MOGRT:** o Premiere 26.x NÃO troca texto de MOGRT pela API (o `MogrtText` só vem no 27). Para lettering com o texto do vídeo: `P.lettering_ae(seq, "<modelo da biblioteca>", {campos}, inicio, trilha, pasta=<vídeo>/motions, cores=...)` monta no After Effects, exporta um .mogrt só desse vídeo (~7 s) e insere (texto e cores seguem editáveis no Essential Graphics). Sem AE: render MOV com alfa.
- **Conferir sempre** com quadros exportados (DaVinci: `Project.ExportCurrentFrameAsStill` depois de `SetCurrentTimecode`; Premiere: `P.Exporter.exportSequenceFrame`; AE: `AE.quadro`). Escolher instantes em que nada cubra o clipe animado (motion por cima esconde o teste).

## O que os editores têm de nativo (e por que o Gab usa o próprio rastreador)

Pesquisado em 12/10/2026 (documentação e tipos da API):
- **Premiere 26:** "Máscara de objeto" com IA rastreia pessoas e objetos, mas só para MÁSCARA/efeito (desfocar, cor, texto atrás da pessoa); não prende texto ao objeto, e a API só tem `ObjectMaskUtils.hasObjectMask` (não cria nem roda o rastreio). Por isso: rastreador do Gab + keyframes de Movimento. Quando o pedido for "texto ATRÁS da pessoa" no Premiere, guiar o usuário na Máscara de objeto (é clique, não script) ou fazer pelo `docs/etapas/extras.md`.
- **After Effects:** tem rastreador de pontos, Mocha e câmera 3D, mas disparar a análise por script não é suportado (os comandos de menu de rastreio não aparecem para `app.findMenuCommandId`). Se o USUÁRIO rastrear no AE, o Gab pode ligar o texto ao resultado por expressão: `thisComp.layer("<camada rastreada>").motionTracker("Tracker 1")("Track Point 1").attachPoint`.
- **DaVinci:** o Tracker/Planar Tracker do Fusion existem, mas o rastreador do Gab + keyframes de Center é previsível e conferível por quadros; usar o nativo só se o usuário pedir.
