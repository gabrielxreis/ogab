<!-- Regra do usuário, 12/10/2026 (Bora Comunicação). Ler ao colocar SFX. -->

## 6. Efeitos sonoros: desenho de som que DÁ VIDA À CENA

> Take, cena ou animação inteira para sonorizar (ambiente, foley, pan, mixagem): ver `sonorizacao.md` (`scripts/sonorizar.py`).

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
5. Gravar o plano em `<vídeo>/sfx/plano_sfx.txt` SEMPRE pelo instante do evento: `scripts/plano_sfx_eventos.py <pasta_sfx> eventos.txt` (o ataque ou o pico cai no quadro do movimento; o script corta o respiro do começo do arquivo). Nunca escrever o início do arquivo à mão: porta, splash, riser e camas com silêncio no começo caem segundos atrasados (13/10/2026). Conferir com `sfx_conferir.py sincronia`.
6. Download: o Chrome às vezes não entrega SFX do Artlist ("direct download" sem arquivo). Plano B: o `playableUrl` do `search_sfx` é o clipe inteiro (AAC): curl + ffmpeg para WAV 48 kHz. Avisar o usuário e trocar pelo WAV quando liberar.
`sfx_auto.py` é só o básico (whoosh/pop genéricos): não basta para motion; usar este desenho.

## Desenho em CAMADAS e conferência sem ouvir (regra do usuário, 12/10/2026: "o sfx não tá preenchendo e dando imersão, tem whoosh e efeito que não combina")
O que deu errado no motion SUNPRIME (v3): sons escolhidos pelo TÍTULO do Artlist (o "shimmer" era impacto de terror, o "impact" era whoosh, o "logo" era coral), whooshes de 0,1-0,3 s cortados em 0,4 s para movimentos de 1 s, e nenhuma camada contínua (som em só 48% do tempo; a REF tinha 96%). Refeito (v4) assim:
1. **Nunca escolher pelo título.** Baixar candidatos e rodar `scripts/sfx_conferir.py arquivos <pasta>`: o que o CLAP disser é o que o som é. Descartar o que der "horror"/"choir" num vídeo de marca clara, ou rótulo diferente do esperado.
2. **Camadas, cada uma numa trilha com nome:** BASE (pad CLARO e contínuo o vídeo todo, -11 dB sobre -23 LUFS; drone "dark/space" soa terror), AMBIENTE DA CENA (o som do LUGAR que a imagem mostra: rua, jardim com pássaros, mar, gente conversando, sala/estúdio, lago), TRANSIÇÕES (swell reverso que termina no pico do movimento + whoosh com o tamanho do movimento), IMPACTOS (só corte seco e logo), DETALHES (digitação, obturador, clique, glitch). Ambientes cortam seco junto com o corte da imagem.
3. **Whoosh do tamanho do movimento:** medir início/pico/fim de cada movimento (diferença entre quadros) e o ataque/corpo de cada whoosh (envelope); pico do whoosh = pico do movimento; não cortar o som antes do movimento acabar.
4. **Normalizar antes:** camadas contínuas a -23 LUFS (loudnorm), one-shots a -1 dBFS de pico; o volume do clipe fica relativo a isso.
5. **Conferir antes de entregar:** `densidade` (meta ≥ 95% acima de -40 dB), `trechos` (cada cena soa como o que mostra; nada de "horror" no topo), `sincronia` (erro médio ≤ 0,1 s). Pad tonal: avisar que pode brigar com a música (trilha própria para baixar/mutar).

## SFX tonal no tom da música (14/10/2026, método da trilha cinematográfica do @iamjeff.ia)
Riser, drone, pad, impacto com nota, ping de piano e swell têm altura: fora do tom, desafinam por cima da música.
1. `python3 SKILL_DIR/scripts/musica.py medir <musica.wav> --bumbo INI FIM`: tom, relativo, afinação e o segundo da entrada da batida. Tom e relativo empatados ("CONFERIR") = confirmar no tunebat/songbpm antes de escolher.
2. Pacotes tonais vêm nos 12 tons (nome ou subpasta com a nota): pegar o do tom. Música **menor** aceita som menor no tom, som **maior no relativo maior** (3 semitons acima: Lá menor -> Dó maior) e som neutro. **Nunca** som maior na mesma tônica de música menor (Lá maior sobre Lá menor) nem o contrário: as terças brigam.
3. Afinação fora de +-20 cents: SFX tonal desafina; usar só som sem nota (whoosh, ar, ruído) ou outra música.
4. **Riser com o pico exato no corte ou na entrada da batida** (`alinhar: "pico"`); dois risers que começam ~5 s e ~3,7 s antes dão a subida. **Impacto tonal com passa-altas 60 Hz** para não brigar com o bumbo. Golpe de piano só no médio (passa-altas 150 Hz, passa-baixas 2,2 kHz): com sub embola.
5. **Entrada da batida seca:** tudo que vinha subindo corta no bumbo (fade de 20-60 ms), sem respiro antes; a força vem do contraste.
6. Menos é mais: cada camada tonal precisa de função; na dúvida, tira.
