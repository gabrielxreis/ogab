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

**Como fazer** (ordem de trabalho: ver "3 passadas" no fim deste arquivo)
1. Listar os eventos do motion pelo próprio código (tempos do GSAP no build.py) e do lettering pelo template (Cinematic = blur, Palavra Por Palavra = letra a letra). Tabela: tempo | elemento | animação | som.
2. Medir cada som (ffmpeg -> envelope): `onset50` (primeiro ponto a 50% do máximo) e pico. Início na timeline = tempo do evento - onset (impacto de logo tem build-up antes do golpe).
3. Normalizar todos a -1 dBFS antes; volume no clipe: -12 (impacto/boom/logo), -14 a -16 (whoosh/swell), -16 a -20 (UI, HUD, brilho). Fade out no clipe.
4. Uma trilha livre por som: A3 "SFX", A4..A6 "SFX 2..4"; escolher a primeira trilha cujo último clipe termina antes (AppendToTimeline em cima de outro clipe corta/empurra).
5. Gravar o plano em `<vídeo>/sfx/plano_sfx.txt` SEMPRE pelo instante do evento: `scripts/plano_sfx_eventos.py <pasta_sfx> eventos.txt` (o ataque ou o pico cai no quadro do movimento; o script corta o respiro do começo do arquivo). Nunca escrever o início do arquivo à mão: porta, splash, riser e camas com silêncio no começo caem segundos atrasados (13/10/2026). Conferir com `sfx_conferir.py sincronia`.
6. Download: o Chrome às vezes não entrega SFX do Artlist ("direct download" sem arquivo). Plano B: o `playableUrl` do `search_sfx` é o clipe inteiro (AAC): curl + ffmpeg para WAV 48 kHz. Avisar o usuário e trocar pelo WAV quando liberar.
7. **Sem Artlist nem Envato (ou nada bom neles): Pixabay**, grátis, sem conta, uso comercial livre (inclusive anúncio). `python3 SKILL_DIR/scripts/sfx_pixabay.py busca "drawer close wood"` imprime a URL da busca e um JavaScript: abrir a URL no navegador (Claude in Chrome ou o do app), rodar o JavaScript (`javascript_tool`), salvar a lista JSON e `sfx_pixabay.py baixar lista.json <vídeo>/sfx --so 1,3 --nomes gaveta,papel`. Sai em WAV 48 kHz a -16 LUFS (som muito percussivo fica abaixo para o pico não passar de -1 dB) com título, página e licença em `CREDITOS.txt`. Ouvir antes de usar: o acervo é da comunidade e a qualidade varia; conferir com `sfx_conferir.py` como qualquer SFX.
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

## Ordem de trabalho em 3 passadas + risers de antecipação (15/10/2026, método da Ultimate Editors no curso "How to Edit VIRAL Reels with AI")
Complementa tudo acima (foley por objeto, camadas, conferência); não troca nada. Serve sobretudo para talking head com motion.
1. **Folha de eventos antes de qualquer som.** Percorrer o vídeo e classificar cada momento em uma de três famílias:
   **MOVIMENTO** (algo desliza, sobe, cai, câmera anda, painel entra, troca de cena) -> whoosh;
   **EVENTO** (algo acontece sem deslizar: pop, clique, revelação, cor mudando, letra a letra, número contando) -> textura;
   **VIRADA** (fim do gancho, troca de bloco/passo, A-roll -> B-roll, revelação grande) -> riser + hit.
   Whoosh para o que desliza e pop para o que estoura: nunca o contrário.
2. **Passada 1, whooshes** do começo ao fim: um por movimento, do tamanho e peso do movimento (lento = ar/vento, padrão =
   oco/sci-fi, rápido e pequeno = curto), pico no quadro mais rápido.
3. **Passada 2, texturas** do começo ao fim: pop (texto/elemento inteiro estourando), clique de UI (elemento de interface,
   passo acendendo, slider), clique sci-fi (algo muda dentro da animação, cor), engrenagem/tique (palavra por palavra,
   letra a letra; um toque por elemento), digitação (teclado), impacto sci-fi (objeto ou UI novo entrando), clique de
   câmera (flash, troca de clipe; no quadro exato), "success" curto (conclusão do vídeo), coro curto só na revelação
   grande. Cada uma no quadro do evento.
4. **Passada 3, risers e hits** perguntando "onde quero que a pessoa sinta a subida para o próximo trecho?":
   - **riser ~5 s depois do gancho**, terminando no corte que entra no corpo do vídeo, com um **hit embaixo** no quadro do corte;
   - um riser + hit em cada virada de bloco/passo e em A-roll -> B-roll que precisa de costura;
   - **pelo menos 2 risers por vídeo** de 40 s ou mais, alternando um grave seco ("sharp bass") e um metálico; riser
     de sucção (suck-back) bem baixo ou bem alto, nunca no meio;
   - riser com nota segue "SFX tonal no tom da música" acima; o que vinha subindo corta seco no hit.
5. **Uma trilha por família** com nome (WHOOSH, TEXTURA, RISER, HIT, além das camadas BASE/AMBIENTE quando houver).
   Antes de pôr, ouvir/conferir as variações da mesma pasta e escolher a que tem o tamanho certo (`sfx_conferir.py arquivos`).
6. **Hierarquia de volume** (relativa, com os one-shots a -1 dBFS): whoosh é o mais baixo (-14 a -16 dB no clipe),
   textura um pouco acima (-12 a -14), riser + hit é o ponto mais alto de cada virada (-10 a -12), e só UM momento mais
   alto por cena. Nada passa a voz; se o empilhamento riser + hit estourar, baixar o hit, nunca a voz.
7. Relatar ao usuário a folha de eventos e o que entrou em cada passada (tempo | família | som | por quê).

## Biblioteca local, DaVinci 21.0 e mixagem que não encobre a voz (relato 16/10/2026, Windows)
- **Pacote de SFX sem pasta "whoosh"** (ex.: organizado por Transform, Friction, Music Transition): escolher pelo movimento, não pelo nome da pasta. Entrada/deslize = Friction/Movement; subida antes de revelar = Power Up curto ou Riser; papel = Paper Flip; clique de interface = Granular/Button/Select.
- **Cada arquivo tem um respiro diferente antes do golpe** (0 a 2 s). Medir o envelope de cada candidato (ataque = primeiro ponto a 50% do pico; e a posição do pico) e alinhar o ATAQUE (golpe, clique, carimbo) ou o PICO (riser) no quadro exato do movimento.
- **DaVinci 21.0 não tem `AudioVolume` nem `SetFades` pela API** (só no 21.1): gravar ganho e fade numa CÓPIA de cada som (`sfx/arquivos/`, o original fica intacto) e deixar os faders das trilhas livres para o ajuste fino do usuário.
- **"Sem exagerar nem encobrir a voz":** um som por movimento principal, nada nas microanimações; picos entre -17 dBFS (impacto) e -27 dBFS; a soma dos SFX perto de -35 LUFS com a voz em -14, e a mistura continua em -14.
- **Uma trilha por família** (riser/whoosh, impacto, UI, foley); se dois da mesma família se sobrepõem, o segundo vai para a próxima trilha livre.
- **O usuário mexeu na timeline entre um pedido e outro** (duplicou um som, criou trilha): tirar um retrato novo antes do próximo passo e trabalhar em cima dele; nunca desfazer o que ele fez.

### Música nessas condições
- **Sem conector de música** (Artlist/Envato desligados): procurar primeiro na biblioteca local do usuário (pasta de trilhas dele) e mostrar 2-3 opções já mixadas com a voz, sem gastar crédito.
- **Faixa masterizada muito alta** (ex.: -7 LUFS) num DaVinci sem volume pela API: cópia INTEIRA da faixa (regra da música bruta: sem cortar) só com o ganho (ex.: -24 dB) e o fade de saída gravados, para o trecho usado ficar ~16 dB abaixo da voz. Com 21.1+, nada disso: `colocar_musica(..., db=...)`.
- Música abaixo dos SFX: trilha própria na ÚLTIMA posição de áudio ("MUSICA").

