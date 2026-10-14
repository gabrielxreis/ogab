# Princípios de animação, ritmo e recriação de referência

Aprendido com o Rick (@rick.motion_, motion designer) usando o /ogab no After Effects, 12 a 14/10/2026. Vale para
QUALQUER motion (HyperFrames ou After Effects). Ler ao planejar motions (etapa 8) e ao receber uma referência.

## 1. Referência = linguagem, não elementos

- Ao receber referências, o primeiro passo é tirar a **ideia central e de 5 a 8 princípios** que unem todas
  (papel da tipografia, grid, ritmo, paleta, de onde vêm as formas, hierarquia de profundidade). Listar "o que
  aparece em cada vídeo" não serve.
- A receita de um cliente não vai para outro. Os princípios vão para o `estilo.md` do cliente.
- **"Recriar" quer dizer fiel:** mesmos tempos, poses-chave, câmera e transições; muda só identidade e conteúdo.
  Nada de "inspirado em". Método na seção 5.

## 2. Os 12 princípios da animação (Disney): regra em TODO motion

| Princípio | No motion do Gab |
|---|---|
| Squash & stretch | objeto que bate achata e volta mantendo a massa (área constante) |
| Antecipação | recua um pouco antes de partir; começa 2 a 4 quadros antes para o pico cair na batida |
| Encenação | um foco por vez; o resto espera ou some |
| Pose a pose | definir as poses-chave primeiro, depois os intermediários |
| Follow-through / overlap | partes chegam em tempos diferentes (stagger), o que é solto continua depois de parar |
| Slow in / slow out | nunca linear (exceto giro contínuo e rolagem) |
| Arcos | trajetória curva com rotação que assenta, não linha reta |
| Ação secundária | brilho, partícula, sombra que reage à ação principal |
| Timing | 3 durações por cliente (curta, média, longa), não valor diferente em cada camada |
| Exagero | overshoot leve (`back`) na chegada |
| Volume sólido | em marca chapada vem da sobreposição coerente de camadas e do squash que mantém a massa, não de sombra e degradê |
| Apelo | formas claras, silhueta legível |

Padrões prontos: **impacto** (squash ao bater + follow-through), **chega** (entra esticado, passa do ponto e assenta),
**parte** (antecipa recuando e sai acelerando), **arco** (curva com rotação que assenta).

**Checklist antes de renderizar:** tem antecipação? algum keyframe linear sem motivo? chegadas em cascata ou tudo
junto? impacto cai na batida? saída tem direção (não só fade)?

## 3. Os 12 princípios de UX em motion (uxinmotion.net)

easing, offset & delay, parenting, transformation, value change, masking, overlay, cloning, obscuration, parallax,
dimensionality, dolly & zoom. Usar como vocabulário para escolher transições: um elemento vira o outro
(transformation), número sobe (value change), revela pela forma (masking), camadas em velocidades diferentes
(parallax), cartão vira em 3D (dimensionality).

**Dolly zoom em camada de forma:** âncora e posição ficam em espaços diferentes. Âncora nova =
âncora + (alvo − posição) / escala.

## 4. Ritmo, música e consistência

- **A música dita o vídeo.** Marcar a grade (batidas e compassos) antes de animar. Estrutura: intro, build, drop e
  final parado.
- **Corte:** um por compasso como padrão (mediana medida num lineup de festival: 3,9 batidas).
- **Sincronia de ação (Baby Driver):** o que cai no acento é a AÇÃO (impacto, pop, número batendo), não
  necessariamente o corte.
- **Tokens de motion por cliente** (vão no `estilo.md`): 3 durações; 1 curva de entrada, 1 de saída, 1 overshoot;
  1 stagger; direção fixa; distâncias no grid; 2 ou 3 transições que se repetem.
- **Tracking que prende o olho:** gráfico grudado na filmagem (ver `tracking_animacao.md`).

## 5. Recriar uma referência com fidelidade (método)

1. Folha de quadros a 4–6 qps do vídeo todo, mais quadro a quadro nas janelas críticas. Cortes por
   `ffmpeg -vf "select='gt(scene,0.3)',showinfo"`.
2. **Mapa temporal** de cada cena: início, fim, entradas, saídas, poses-chave e transições.
3. **Câmera medida, não estimada:** correlacionar o perfil de uma faixa do fundo entre quadros (numpy) e somar os
   deslocamentos. Num caso real a câmera andava em arrancadas, não em panorâmica constante. A curva vira keyframes.
4. Posição no quadro + curva da câmera = coordenada do mundo.
5. Comparação lado a lado (referência em cima, recriação embaixo) nos mesmos instantes antes do render, corrigindo
   escala, posição, proporção da fonte e contraste.

**Limite honesto:** animação 2D desenhada à mão vira vetor com as mesmas poses e tempos, mas não com o mesmo traço.
Avisar antes de começar.

**Economia:** uma folha de quadros por referência; medir por script (cortes, BPM, câmera) em vez de olhar quadro a
quadro; um script de montagem, uma conferência e um render.

## 6. Personagem (rig sem plugin)

- IK de dois ossos pela lei dos cossenos com L1 e L2 fixos (evita referência circular). Por isso **mudar o tamanho
  é refazer com outra escala**; escalar o pai quebra o IK.
- Olhar para o outro lado: precomp espelhado (escala −100). Virar a cabeça: troca de desenho com um in-between
  espremido e overshoot.
- Secundária: overlap (atraso), inércia, piscar, olhar, respiração.
- DUIK Angela instala sem administrador na pasta `ScriptUI Panels` do usuário e abre por
  `app.executeCommand(app.findMenuCommandId("Duik Angela.jsx"))`.
- Recorte de pessoa/atleta: `rembg` com `u2net_human_seg`.

## 7. Perfil de cliente

- Identidade da fonte oficial: logo pelo site/Linktree, cores medidas por pixel nas artes do próprio cliente, fontes
  comparadas com as instaladas (fonte ausente: a mais próxima instalada, registrada no `estilo.md`).
- `estilo.md` = linguagem (princípios), tokens de motion, fonte dos títulos, modelos prontos. `empresa.md` = fatos.
- Dados de terceiros (mapa, escudo de adversário): avisar que a resolução pode ser baixa.
