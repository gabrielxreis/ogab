<!-- Regra do usuário, 12/10/2026 (Bora Comunicação). Ler ao colocar SFX. -->

## 6. Efeitos sonoros: desenho de som que DÁ VIDA À CENA

Não é "um whoosh por motion". Cada elemento que se mexe na tela ganha o som que combina com o TIPO de movimento, e o pico do som cai no instante do movimento. Coerência acima de tudo (o usuário reclamou de "pop em lettering que começa com blur").

**Som certo para cada animação**
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
