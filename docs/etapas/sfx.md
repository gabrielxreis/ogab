<!-- Regra do usuário, 12/10/2026 (Bora Comunicação). Ler ao colocar SFX. -->

## 6. Efeitos sonoros: desenho de som que DÁ VIDA À CENA

Não é "um whoosh por motion". Cada elemento que se mexe na tela ganha o som que combina com o TIPO de movimento, e o pico do som cai no instante do movimento. Coerência acima de tudo (o usuário reclamou de "pop em lettering que começa com blur").


**PRIMEIRO o que o motion REPRESENTA, depois o tipo de animação (regra do usuário, 12/10/2026: "ele fala de gaveta com som de hud, tem que ter coerência; sempre veja do que se trata o motion e recrie a experiência sonora").**
Antes de escolher o som, ler o motion/take e perguntar: que OBJETO ou AÇÃO real está na tela? Recriar o som dele (foley), e só usar som de interface (HUD, blip, UI select) quando o elemento for de fato uma interface (tela, app, dado digital).
| Na tela | Som (foley real) | Arquivo já baixado (Artlist) |
|---|---|---|
| gaveta abrindo/fechando | gaveta de madeira desliza e bate (alinhar a BATIDA) | drawer_close (pico 2,17 s) |
| diploma, documento, cartão de papel | papel deslizando | paper_slide |
| selo, carimbo, aprovação, "reconhecido" | carimbo de borracha | rubber_stamp |
| check numa lista | caneta marcando | pen_tick |
| assinatura, "por escrito", prova | caneta escrevendo | pen_sign |
| juiz, decisão judicial, "barrada" | martelo do juiz | gavel |
| dinheiro, valor em US$ | notas de dinheiro | banknotes (cash_register tem pré-roll de 2,8 s) |
| viagem, Brasil > EUA, rota | avião passando | airplane (pico 1,76 s) |
| tempo, anos, prazo longo | relógio | clock_tick |
| médico, estetoscópio | batimento no estetoscópio | heartbeat |
| notícia, jornal, manchete | página de jornal | newspaper |
| celular | vibração | phone_vibe |
| pedra, "pedra sobre pedra", bloco | martelo em pedra | stone_hit |
| contador de número | contador | counter |
| conquista, "chegou", resultado positivo | chime positivo | chime_positivo |
| take com ação real (limpar, dobrar roupa) | foley da ação, baixo, sob a voz | cloth_wipe, cloth_whoosh |
Biblioteca: `~/Desktop/<Empresa>/_sfx_artlist/` (normalizada a -16 LUFS, 48 kHz) e o `playableUrl` do `search_sfx` como plano B de download. No plano, `-NNdB D.Ds` define a duração do som (ex.: `drawer_close -12dB 3.0s`); sem isso vale o SFX_DMAX.

**CADA MOVIMENTO TEM SOM (regra do usuário, 12/10/2026: "os sfx eu quero que cada movimento tenha som").**
Não basta som nos momentos principais: toda entrada, saída, batida, check, brilho, contador e troca de cena do motion ganha som. Como garantir sem esquecer nenhum:
1. `OUT=mov.json node SKILL_DIR/scripts/movimentos.mjs <pasta>/motions <id...>` lista cada tween (início, duração, alvo, propriedades, ease).
2. Tempo absoluto = posição do motion na timeline - offset do clipe + início do tween. Batida com ease `.in` (carimbo `power4.in`) soa no FIM do tween; entrada com `.out`/`back.out` soa no INÍCIO.
3. Cada movimento sem som a até 0,4 s ganha um, pelo objeto (tabela acima) e senão pelo tipo: troca de cena = swish; card/papel = paper_slide; ícone/pino/ponto com back.out = pop; número grande = stone_hit; linha/barra crescendo = whoosh_info; brilho = stardust curto (1-1,5 s); cor acendendo = ui_select; texto subindo = swish baixo (-21 dB); botão = click. Ignorar fundo (#bg), respiração (sine longo) e tremidinha (<0,06 s).
4. O início do arquivo no plano = instante do movimento - ataque do som (`HIT` em sfx: swish 0,09, paper_slide 0,42, rubber_stamp 0,34, logo_impact 1,18, stardust 0,1, pop 0, whoosh_info 0,24, ui_select 0,05, stone_hit 0,06).
5. Plano denso passa de 5 trilhas: `colocar_plano_sfx(..., trilhas=tuple(range(3, 11)))`.

**Som certo para cada animação (só depois de decidir o objeto/ação acima)**
| Animação | Som | Exemplo do Artlist (já testado) |
|---|---|---|
| Entrada com blur / revelação suave / fade | swell, riser oco curto, ar | Serious Whooshes - Hollow Riser; Air Motion - Short Swoosh 02 |
| Elemento desliza (card, slide, wipe) | whoosh curto de infográfico | Infographics - Stereo Whoosh |
| Saída rápida / texto que abre espaçamento | swish | Video Editor - Fast Whoosh |
| Pílula, etiqueta, dado aparecendo (HUD) | blip de interface | Cyberpunk - UI, HUD Loading Data |
| Check, selo, item marcado | UI select suave | Soft UI - Digital Button Select |
| Botão / clique / CTA | click | Modern UI - Perfect Click |
| Palavra de impacto, número grande | boom/impacto | Cinematic Elements - One Boom with Atmospheric Note |
| Logo entrando | impacto de logo (alinhar o ONSET, não o pico) | Cinematic Logos - Soft Synth and Drum Impact |
| Estrelas, brilho, shine | chime/sparkle | Practical Magic - Stardust Chimes; Sparkly Logos |
| Pop/scale com back.out | pop (SÓ aqui) | biblioteca_sfx/pop.wav |

**Como fazer**
1. Listar os eventos do motion pelo próprio código (tempos do GSAP no build.py) e do lettering pelo template (Cinematic = blur, Palavra Por Palavra = letra a letra). Tabela: tempo | elemento | animação | som.
2. Medir cada som (ffmpeg -> envelope): `onset50` (primeiro ponto a 50% do máximo) e pico. Início na timeline = tempo do evento - onset (impacto de logo tem build-up antes do golpe).
3. Normalizar todos a -1 dBFS antes; volume no clipe: -12 (impacto/boom/logo), -14 a -16 (whoosh/swell), -16 a -20 (UI, HUD, brilho). Fade out no clipe.
4. Uma trilha livre por som: A3 "SFX", A4..A6 "SFX 2..4"; escolher a primeira trilha cujo último clipe termina antes (AppendToTimeline em cima de outro clipe corta/empurra).
5. Gravar o plano em `<vídeo>/sfx/plano_sfx.txt`.
6. Download: o Chrome às vezes não entrega SFX do Artlist ("direct download" sem arquivo). Plano B: o `playableUrl` do `search_sfx` é o clipe inteiro (AAC): curl + ffmpeg para WAV 48 kHz. Avisar o usuário e trocar pelo WAV quando liberar.
`sfx_auto.py` é só o básico (whoosh/pop genéricos): não basta para motion; usar este desenho.
