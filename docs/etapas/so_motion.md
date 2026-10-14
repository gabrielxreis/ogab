<!-- Regra do usuário, 12/10/2026 (Calverstone 07-10, Bora Comunicação 07-10, Bora Imigrar 06-09). Ler ao fazer vídeo SEM narração. -->

## Vídeo só motion + música (sem narração)

Quando o usuário pede "só motion e música": o texto anima na tela no ritmo da música, sem voz e sem legenda.

**Roteiro:** 5 a 6 cenas + CTA, ~30 s (Reels/Ads). Assunto quente ou viral com FONTE e data em letra pequena em cada cena com dado. Famosos: só fato público com fonte (onde mora, obra conhecida), nunca citação inventada, imagem ou insinuação de vínculo; marcar "exemplo público, sem relação com a marca" quando o famoso ilustrar o serviço.

**Batida:** escolher a música pelo Artlist (bpm e hookStartSeconds vêm no search_music) e, com o WAV baixado, **medir** com `python3 SKILL_DIR/scripts/musica.py medir <wav> --de <hookStart> --ate <hookStart+40>`: o bpm do catálogo é ponto de partida e erra (134 informado x 136 medido derrapa uma cena inteira em 30 s). Cenas definidas em BATIDAS da grade medida (a lista `batidas` dá o segundo de cada uma); a entrada da batida (`--bumbo INI FIM`) é onde cai o corte forte, o impacto e o pico do riser. A música entra em `hookStart - início do CTA` (clímax no CTA) e, como o hook começa no tempo forte, todas as trocas de cena caem na batida.

**Motion:** uma composição por vídeo com cenas (`.sc` com entrada/saída de 0,3 s), gerador em `~/Documents/videos/motion-only/build_mo.py` (temas por cliente: Bora Comunicação navy/laranja Poppins, Bora Imigrar verde-petróleo/laranja Inter) e `~/Documents/videos/calverstone-motions/lote3.py` (Calverstone). Fundo opaco do primeiro ao último quadro (`bgfade` desligado: nada de fade do preto).

**Render:** vídeo de tela cheia opaco = **MP4** (`--format mp4 -q delivery --workers 1`, ~16-24 MB em 30 s) e não MOV ProRes 4444 (~250 MB por 8 s). Com várias workers o HyperFrames grava cada quadro em disco (~8 GB para 30 s): com pouco espaço, sempre `--workers 1` (streaming).

**Timeline:** uma por vídeo no projeto do cliente, nome "Motion NN Assunto"; V1 = MOTIONS (o MP4), A2 música bruta -10 dB, A3..A7 SFX de foley pelo que a cena MOSTRA (contador, dinheiro, carimbo, papel, avião, digitação em chat, notificação). Sem legenda, sem cor (não há take), sem lettering (o texto está no motion): marcar essas etapas como puladas no `projeto.py`.

**Entrega:** `renderizar` (master -14 LUFS) e cópia na Área de Trabalho "<Cliente> - NN Assunto.mp4"; `videos/legenda_post.txt` com fontes e o aviso obrigatório do cliente.

**Presets:** vídeo só motion também pode sair inteiro num preset (ver "Quando usar cada preset" no SKILL.md): curiosidade/história em **point cloud**, frases de efeito/hábito em **vector motion** (escolher o estilo), interface em **vitrine**. As cenas continuam na batida da música.
