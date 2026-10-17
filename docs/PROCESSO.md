> Documento de referência detalhado (histórico de decisões e armadilhas). O passo a passo resumido que a IA segue está no `SKILL.md`; os valores configuráveis estão no `config.json`.

# Processo: vídeo para redes sociais com IA + DaVinci Resolve

Guia para uma IA (Claude Code ou similar) produzir um vídeo do roteiro até a timeline pronta no DaVinci, com duas paradas obrigatórias para o usuário decidir: **aprovar o roteiro** e **escolher a voz**. Nada que gaste crédito roda antes dessas aprovações.

Ferramentas (conectores MCP no Claude):
- **ElevenLabs:** voz (`creative_list_voices`, `creative_generate_speech`, `creative_transcribe_audio`).
- **Artlist:** só **busca** de música e efeitos (`search_music`, `search_sfx`, `get_track`). **Não gerar nada no Artlist.**
- **Envato:** banco de vídeo, música e efeitos (`search_stock_video`, `search_music`, `search_sound_effects`, `search_photos`).
- **Magnific:** a **única** ferramenta para gerar takes (imagem e vídeo), e **sempre nas versões ilimitadas, que não gastam crédito**: Nano Banana 2 em 1K e Kling 2.5 em 720p, **gerando pelo site no Chrome**. Pelo MCP a geração cobra crédito, então o MCP serve só para buscar e baixar.
- **DaVinci Resolve Studio** aberto, com scripting externo em **Local** (Preferences > System > General). Python 3, ffmpeg, Pillow.
- **Claude in Chrome**, para operar sites logados (Magnific, Envato ou Artlist, quando o download não vem pelo MCP).

---

## Regras fixas do usuário (ler antes de tudo)

1. **Pasta de trabalho: sempre na Mesa (`~/Desktop`)**, numa pasta com o **nome do vídeo** (`<Assunto> - <Empresa>`), com estas subpastas e arquivos:
   ```
   ~/Desktop/<Assunto> - <Empresa>/
     roteiro.txt        # roteiro aprovado, em texto puro
     links.txt          # de onde veio cada coisa: música, cada take, voz, notícia/fonte
     narracoes/         # áudio da voz (ElevenLabs)
     musica/            # trilha (Artlist/Envato)
     brolls/            # takes: baixados do Envato e gerados no Magnific (take_01.mp4...)
     videos/            # render/export final do vídeo
     legendas/          # SRT
   ```
   O projeto do DaVinci tem o mesmo nome da pasta.
2. **Tudo via MCP, exceto download.** Busca (Envato, Artlist), voz (ElevenLabs), leitura de criações (Magnific) e DaVinci (scripting) são feitos por MCP/API. **Baixar arquivos é sempre pelo navegador** (Claude in Chrome, logado nas contas do usuário), porque os conectores não baixam.
3. **Economizar créditos e tokens:** gerar só o necessário (1 take por vez, sem variações extras), usar as versões ilimitadas do Magnific, estimar custo antes no ElevenLabs; no navegador, uma chamada por item com script JS enxuto e sem screenshots desnecessários; buscas com `perPage` pequeno; não reler arquivos grandes.
4. **Pode usar skills** (ex.: de vídeo, imagem, legenda) quando facilitarem e economizarem passos.
5. **Legenda respeitando a métrica** (ver Etapa 6) e **sem misturar idiomas nem palavras erradas**: tudo em português correto; termos técnicos em inglês só quando são o nome oficial (green card, EB-2, Visa Bulletin), escritos certo e sempre do mesmo jeito; corrigir o que a transcrição errou (nome da empresa, siglas, datas como "1º de janeiro").

7. **Volumes no DaVinci (regra fixa): música sempre em -10 dB e narração em +5 dB** (ajuste de volume do clipe na timeline). Se a API não aceitar, aplicar o ganho no arquivo antes de importar (ffmpeg `volume=-10dB` / `volume=5dB`) e avisar.
6. **Evitar takes com green screen / fundo verde (chroma key)** e com canal alfa/elementos isolados: escolher só cenas reais e completas. Conferir a miniatura antes de baixar.

### Download no Envato pelo navegador (como funciona)
- A página `elements.envato.com/...` redireciona para `app.envato.com/stock-video/<id>` em ~10 s. O botão é "Baixar 4K" (ProRes, pesado). Abrir a setinha ao lado e clicar em **"1080P"**: isso já baixa (não clicar no botão principal depois, senão baixa duas vezes). Aparece "Licenciado automaticamente".
- O arquivo cai em `~/Downloads` com o nome do clipe; mover para `brolls/take_XX.mp4`.
- A aba só redireciona/renderiza depois de um screenshot ou zoom: tirar um zoom pequeno antes de rodar o JS.
- Não varrer o DOM inteiro com JS (`querySelectorAll('*')` congela a aba).

---

## Etapa 0. Briefing da empresa (antes de qualquer roteiro)

Pedir ao usuário, na primeira vez que for fazer vídeo para uma empresa:
- **Site da empresa** (obrigatório).
- **Material gráfico:** logo (de preferência PNG com fundo transparente, versão clara e escura), paleta de cores, fontes, e se existir, manual de marca, vinheta/assinatura de vídeo, fotos da equipe ou do produto.
- @ das redes sociais e exemplos de vídeos que a empresa gosta (ou não gosta).

Depois, **ler o site inteiro** (home, serviços, sobre, FAQ, depoimentos, rodapé) e montar `videos-redes/clientes/<empresa>/empresa.md` com:
- O que a empresa faz, serviços/produtos, para quem (público e dores), diferenciais.
- Tom de voz e palavras que ela usa; CTA principal e link (ex.: "link na bio", formulário, WhatsApp).
- Cores (hex), fontes e caminho do logo salvo em `clientes/<empresa>/logo/`.
- O que **não** dizer (promessas proibidas, regras do setor, ex.: imigração não pode prometer aprovação nem prazo).

Esse arquivo é a base para tudo: roteiro, escolha de takes, prompts de geração no Magnific (cenário, cores e clima da marca), legenda (cores/fonte) e tela final com logo. Em vídeos seguintes da mesma empresa, ler o `empresa.md` em vez de perguntar de novo (só confirmar se mudou algo).

## Etapa 1. Roteiro (PARAR para aprovação)

1. Perguntar ao usuário, se ele ainda não disse:
   - **Plataforma:** Instagram, YouTube ou anúncio no Meta Ads.
   - **Tema e objetivo** (informar, engajar, vender), **público** e **CTA** final.
   - Tom (sério, divertido, notícia, inspirador) e duração desejada.
2. Escrever o roteiro já no formato da plataforma (tabela abaixo):
   - **Gancho** nos primeiros 2 a 3 s (pergunta, dado forte ou promessa).
   - Frases curtas, uma ideia por frase, linguagem falada.
   - Para cada bloco, uma linha de **sugestão visual** (o que aparece na tela).
   - **CTA** claro no final.
   - Estimar a duração: cerca de **150 palavras por minuto** de fala.
3. Entregar o roteiro e **esperar o "aprovado"**. Ajustar quantas vezes ele pedir.

| Plataforma | Formato | Duração típica | Observações |
|---|---|---|---|
| 13/10/2026 | The Chosen: takes chegaram ao DaVinci já cortados e recortados em 9:16 (ffmpeg), sem como reajustar; e 22 s presos no mesmo assunto (diretor falando parado) | `montar_takes` só aceitava arquivo a partir do quadro 0, então os takes eram pré-cortados; plano de takes com blocos longos | `montar_takes` aceita `(arquivo, inicio_s, entrada_s)` e aplica zoom de preencher; regra 1h2 (material bruto) e ritmo de 1,5-3 s em `docs/etapas/takes.md` |
| Instagram (Reels) | 9:16, 1080x1920 | **mínimo 30 s, máximo 1:30** (regra do usuário) | Gancho forte, legenda grande, música em alta. |
| YouTube Shorts | 9:16, 1080x1920 | até 60 s | Loop no final ajuda. |
| YouTube (vídeo longo) | 16:9, 1920x1080 | 3 a 15 min | Introdução curta, capítulos, b-roll a cada 5 a 10 s. |
| Meta Ads | 9:16 (Reels e Stories) ou 4:5 (feed, 1080x1350) | **15 s, 30 s ou 60 s** (só essas três; perguntar qual) | Produto ou benefício nos 3 primeiros s, funcionar sem som (legenda obrigatória), CTA direto, sem promessas exageradas (regras de anúncio do Meta). |

---

## Etapa 2. Voz (PARAR para o usuário escolher)

1. Listar opções com `creative_list_voices` (ElevenLabs) filtrando por idioma (`pt`), gênero, tom e uso (`social_media`, `advertisement`, `informative_educational`). Se o usuário tiver voz clonada, incluir.
2. Mostrar 3 a 5 vozes com nome e descrição (e o link de prévia, quando houver) e **esperar ele escolher**.
3. Antes de gerar, rodar `creative_generate_speech` com `estimate_only: true` e informar o custo em créditos.
4. Gerar com a voz escolhida, `model_id` `eleven_v4` (ou `eleven_v3` se o roteiro tiver marcações de emoção como `[sorrindo]`), `generations_count: 1`. **Não chamar de novo para "tentar outra vez"**: cada chamada cobra.
5. Acompanhar com `creative_get_flow_run_status` até concluir, baixar o áudio para `projeto/audio/narracao.mp3` (ou `.wav`).
6. Ouvir o resultado (ou transcrever) e conferir pronúncia de nomes e números. Se errar, corrigir o texto (grafia fonética, vírgulas para pausas) e gerar só o trecho problemático, com aprovação.

A voz é a única etapa que usa crédito fora do Magnific (créditos do ElevenLabs): sempre mostrar o custo antes e gerar só depois da voz escolhida.

---

## Etapa 3. Abrir o DaVinci e importar o áudio

**Nome do projeto no DaVinci: sempre `<Assunto> - <Empresa>`** (ex.: `Visa Bulletin Outubro 2026 - Empresa X`), para o usuário achar fácil. A pasta no disco tem o mesmo nome, dentro da pasta da empresa: `pasta_saida/<Empresa>/<Assunto> - <Empresa>/` (padrão `~/Desktop`). A pasta da empresa também guarda `marca/` (logos e identidade do site, via `scripts/marca.py`).

```bash
export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
export PYTHONPATH="$RESOLVE_SCRIPT_API/Modules/"
open -a "DaVinci Resolve"     # e esperar o scriptapp responder
```

```python
import DaVinciResolveScript as dvr
r = dvr.scriptapp("Resolve"); pm = r.GetProjectManager()
# NOME DO PROJETO (regra do usuário): "<Assunto> - <Empresa>", ex.: "Visa Bulletin Outubro 2026 - Empresa X"
p = pm.CreateProject("<Assunto> - <Empresa>") or pm.LoadProject("<Assunto> - <Empresa>")
mp = p.GetMediaPool(); root = mp.GetRootFolder()
for nome in ("AUDIO", "MUSICA", "TAKES"): mp.AddSubFolder(root, nome)

mp.SetCurrentFolder([f for f in root.GetSubFolderList() if f.GetName()=="AUDIO"][0])
narr = mp.ImportMedia(["/caminho/projeto/audio/narracao.wav"])[0]
t = mp.CreateEmptyTimeline("Timeline 1")
p.SetCurrentTimeline(t)
# formato da plataforma (por timeline): ligar custom settings e regravar resolução depois
t.SetSetting("useCustomSettings", "1")
t.SetSetting("timelineFrameRate", "30")                 # ou 24/25 conforme o usuário
t.SetSetting("timelineResolutionWidth", "1080")         # 9:16
t.SetSetting("timelineResolutionHeight", "1920")        # 4:5 = 1350; 16:9 = 1920x1080
mp.AppendToTimeline([{"mediaPoolItem": narr, "mediaType": 2, "trackIndex": 1, "recordFrame": t.GetStartFrame()}])
```

- **Evitar áudio travando no DaVinci:** (1) logo depois de `CreateProject`, ANTES de criar qualquer timeline, gravar `timelineFrameRate` **e** `timelinePlaybackFrameRate` iguais (ex.: '30'); depois que existe timeline a API não muda mais o playback (fica 24 e o áudio engasga numa timeline 30). (2) Takes 4K/ProRes pesados: converter antes para 1080x1920 H.264 (`ffmpeg -vf scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920 -c:v libx264 -crf 18 -an`). (3) Áudio todo em 48 kHz (música do Artlist vem em 44,1: `ffmpeg -ar 48000`).
- **Regra: ajustar já na criação da timeline.** Assim que `criar_timeline` roda (antes de importar narração, takes ou títulos), conferir playback = timeline. **Não ligar Render Cache (o usuário não quer; fica em None).** Não esperar o áudio picotar.
- **Se o áudio picotar mesmo assim (resolução validada):** conferir `p.GetSetting('timelinePlaybackFrameRate')` contra `timelineFrameRate` (`resolve_lib.checar_playback(p)`). Se diferente (ex.: playback 24 numa timeline 30, que acontece em projeto criado antes dessa regra ou aberto de outro modelo), a API devolve False no `SetSetting`; corrigir pela interface: **File > Project Settings > Master Settings > Playback frame rate = mesmo fps da timeline > Save** (por automação: `app_menu ["File","Project Settings…"]`, digitar no campo, clicar Save). Não ligar Render Cache (regra do usuário). Salvar o projeto.
- Gotcha: ligar `useCustomSettings` reseta a resolução para 1920x1080; por isso regravar largura/altura **depois**.
- Transcrever a narração para ter o tempo de cada palavra: `scripts/transcrever.py` (DaVinci 21.1+: `TranscribeAudio()` + `GetTranscription()`; abaixo da 21.1: Whisper local, escolhido sozinho pela versão). Esses tempos guiam música, takes e legenda.

---

## Etapa 4. Música (Artlist ou Envato)

### Preferência do usuário para música
- **Não precisa ser trilha de "notícia".** O padrão é música **emotiva, que faz a pessoa sonhar** (esperança, conquista, vida nova), mesmo em vídeo informativo.
- Priorizar o que está **em alta / mais baixado**: no Artlist `sortBy: TOP_DOWNLOADS` (ou `NEWEST` para tendências), no Envato `sortBy: popular`. Sempre instrumental.
- Termos de busca que funcionam: "emotional inspiring cinematic", "hopeful", "dreams", "new beginning", "uplifting piano strings", "ambient hope".

### Técnicas para a música trabalhar a emoção
- **Arco emocional casado com o roteiro:** começo mais contido (piano, pads) sob o problema/notícia; a música **cresce** quando o roteiro vira para a solução ("a estratégia certa é...") e chega no **ápice no CTA**.
- **Alinhar o pico com o CTA:** usar o trecho de "hook" da faixa (`hookStartSeconds`/`hookEndSeconds` do Artlist) e posicionar a música de trás para frente, para o drop/clímax cair exatamente na frase final. Cortar o início da faixa se precisar, e não o fim.
- **Primeiros 3 s:** entrar já com algo reconhecível (não 10 s de silêncio de introdução), para segurar o scroll.
- **Tom maior, 90 a 125 BPM**, instrumentos que soam "sonho": piano, cordas, pads ambientes, percussão leve que cresce. Evitar épico de trailer pesado sob a voz.
- **Mixagem:** voz sempre na frente; música por volta de -20 a -25 dB sob a fala, subindo 3 a 6 dB nas pausas e no final; fade out de 1 a 2 s depois do CTA (ou terminar no acorde final da faixa).
- Cortes dos takes podem cair nas batidas/acentos da música para dar ritmo.

1. Definir o clima a partir do roteiro: gênero, energia (BPM), emoção, se pode ter vocal (normalmente **instrumental**, para não brigar com a narração).
2. Buscar: `search_music` do Artlist e/ou `search_music` do Envato, com termos do clima (ex.: "uplifting corporate", "tense documentary", "lofi chill").
3. Apresentar 3 opções ao usuário (nome, artista, link de prévia) e deixar ele escolher, ou escolher a melhor e justificar.
4. Baixar (pelo MCP quando houver link de download; se não, pelo site no Chrome logado) para `projeto/musica/`.
5. Importar na bin MUSICA e colocar na **A2**, a partir do início, cortada no fim da narração (com fade out de 1 a 2 s).
6. **Volume (regra do usuário):** música **-10 dB** e narração **+5 dB** no DaVinci.
7. Licença: usar só faixas cobertas pela assinatura do usuário (Artlist/Envato) e registrar o nome da faixa num `creditos.txt`.

---

## Etapa 5. Takes (Envato ou gerados)

1. Dividir a narração em blocos de 2 a 5 s usando os tempos da transcrição. Para cada bloco, definir o que mostrar (já vem da "sugestão visual" do roteiro).
2. **Primeiro procurar no Envato** (`search_stock_video`), com termos em inglês e o formato certo (vertical para Reels/Shorts/Ads 9:16). Baixar para `projeto/takes/take_XX.mp4`.
3. **Se não achar algo bom, gerar SOMENTE no Magnific, SOMENTE nas versões ilimitadas (que não gastam crédito):**
   - Gerar **pelo site no Chrome** (o MCP do Magnific cobra crédito; usar o MCP só para buscar e baixar).
   - Imagem: **Google Nano Banana 2, 1K** (só o 1K é ilimitado), na proporção da plataforma. Conferir o selo "Unlimited" no botão Generate e a proporção antes de cada lote.
   - Vídeo: página da criação > **Create video** > **Kling 2.5, 720p, 5 s** ("Unlimited videos for this resolution").
   - Conferir depois em `creations_get`: `metadata.credits` tem que ser `0`.
   - **Proibido:** gerar no Artlist, no ElevenLabs ou em qualquer modelo/resolução do Magnific que não seja ilimitado. Se o take ideal só sair num modelo pago, avisar o usuário e propor alternativa (outro take do Envato ou outro prompt no ilimitado).
   - Armadilhas do site: o clique em "Create video" só funciona depois de um screenshot/zoom da aba; a página leva 20 a 30 s para carregar; clicar Generate por JS pelo texto do botão; não varrer o DOM inteiro com JS (congela a aba).
4. Montar uma folha de contato com um quadro de cada take e revisar: formato certo, nada de logotipo de marca real, nada de **rosto realista de pessoa real em cena inventada**.
5. Colocar na timeline, só vídeo, na faixa V1 (ou V2 se houver base), no tempo exato do bloco:

```python
mp.AppendToTimeline([{"mediaPoolItem": take, "startFrame": 0, "endFrame": n-1,
                      "mediaType": 1, "trackIndex": 1, "recordFrame": inicio_do_bloco}])
clip.SetProperty("ZoomX", 1.01); clip.SetProperty("ZoomY", 1.01)   # se sobrar barra
```

- Sem buracos pretos: cada take vai até o início do próximo. Encadear pelo `GetEnd()` do anterior.
- Trocar um take depois: `t.DeleteClips([antigo], False)` e importar o novo com **nome de arquivo diferente** (o Resolve reaproveita item com o mesmo caminho).

---

## Etapa 6. Legenda e entrega

Gerar um SRT próprio a partir das palavras da transcrição (a legenda automática do Resolve deixa blocos longos e palavras soltas):

- **Legenda por FRASE, em UMA linha só (nunca quebrar linha):** cada legenda é um pedaço natural da frase (de vírgula a vírgula, ou até a pausa), sem terminar em artigo/preposição. No vertical, com o preset do usuário, **até ~25 caracteres** (testado: "E PODE AVANÇAR OU RECUAR." cabe com margem). Frase maior vira duas legendas seguidas, cortadas num ponto natural.
- **Preset de legenda do usuário (trilha de legenda do DaVinci):** fonte **Poppins Bold**, tamanho **40**, **CAIXA ALTA ligada (All Caps)**, texto branco, posição baixa centralizada (Y ~112). A API não aplica estilo: o estilo fica na **trilha** de legenda. Por isso: (1) num projeto que já tem a trilha com o preset, trocar só os itens (apagar os itens da trilha e importar o SRT novo) mantém o estilo; (2) em projeto novo, depois de importar o SRT, aplicar o preset na trilha pelo Inspector (Track > Presets) ou pedir para o usuário aplicar, e conferir no render. Para conferir o estilo por script: `ExportProject` > abrir o .drp (zip) > `SeqContainer/*.xml` > `SubtitleTrackVec` > `FieldsBlob` (zstd) contém "Poppins,13,...,Bold".
- **Método que funcionou:** escrever as legendas à mão num `legendas/frases.txt` (uma legenda por linha, ` / ` = quebra de linha, `#n` no fim quando a grafia corrigida muda o nº de palavras faladas) e sincronizar com os tempos das palavras da transcrição pelo script `sincronizar_frases.py` (fica na pasta `legendas/` do vídeo). O script confere se o nº de palavras bate com a narração.
- Quebrar na pontuação e nas pausas (> 0,6 s).
- Nunca terminar em artigo, preposição ou conjunção (a, o, de, da, do, e, em, na, que, com, por, para, à, ao, mas, ou, não, nem...).
- Número junto da unidade ("6 mil votos"); nome composto junto.
- Duração mínima 0,7 s.
- **Conferir nomes próprios e números na internet** e corrigir a grafia (a transcrição erra nomes).
- Importar: `mp.ImportMedia([srt])` (nome de arquivo único por versão), `t.AddTrack("subtitle")`, `mp.AppendToTimeline([item])`.

**Volume pela API:** `item.SetProperty('AudioVolume', 5)` na narração e `-10` na música (a chave `Volume` não funciona).
**Takes sem buraco:** encadear cada take pelo `GetEnd()` do anterior e usar `ceil` no número de frames da fonte (fontes 24/25 fps numa timeline 30 fps deixam 1 a 2 frames pretos se arredondar para baixo).
**Render final:** `SetCurrentRenderFormatAndCodec('mp4','H264')`, `SetRenderSettings({... 'TargetDir': <pasta>/videos, 'CustomName': <nome do vídeo>, 'FormatWidth':1080, 'FormatHeight':1920, 'ExportSubtitle': True, 'SubtitleFormat': 'BurnIn'})`, `AddRenderJob()`, `StartRendering()`. Conferir 3 quadros do MP4 (legenda inteira na tela, sem preto).

Antes de entregar:
- [ ] Roteiro aprovado e voz escolhida pelo usuário.
- [ ] Timeline no formato da plataforma (9:16, 4:5 ou 16:9).
- [ ] A1 narração, A2 música baixa com fade out, V1 takes sem buraco, trilha de legenda.
- [ ] Gancho nos 3 primeiros segundos e CTA no final.
- [ ] Logo da empresa na tela final (ou assinatura de marca), cores da marca na legenda quando fizer sentido.
- [ ] Todos os takes gerados vieram do Magnific em versão ilimitada (`credits: 0`); nada gerado no Artlist nem em modelo pago.
- [ ] Música e takes licenciados; créditos anotados em `creditos.txt`.
- [ ] Projeto salvo (`pm.SaveProject()`), DaVinci aberto na página Edit com a timeline pronta.
- [ ] Resumo para o usuário: o que foi usado (voz, música, takes gerados x banco), custo em créditos e o que ele ainda pode querer ajustar (volume da música, cor, render).

---

## Estrutura de pastas

Ver "Regras fixas" no topo: `~/Desktop/<Assunto> - <Empresa>/` com `roteiro.txt`, `links.txt`, `narracoes/`, `musica/`, `brolls/`, `videos/`, `legendas/`. Perfis das empresas ficam em `~/.claude/skills/ogab/clientes/<empresa>/`.

- **Fade dos letterings:** a curva de opacidade é gravada com `SetKeyFrames(kf, True)` (substitui tudo). `SetInput(valor, quadro)` soma com keyframes antigos e o texto reaparecia depois do fade em alguns. Antes de entregar, rodar `checar_fades(t)`: todo lettering tem que cair para 0 e não voltar.

## Bugs encontrados e corrigidos (registro; não repetir)

| Data | Bug | Causa | Correção |
|---|---|---|---|
| 16/10/2026 | `transcrever.py` e `silencios.py` sem transcrição; `silencios.py` remontava em 24 fps uma timeline de 30 (relatos de usuários) | `TranscribeAudio` volta False fora da Media/Cut/Edit e o resultado chega segundos depois; a timeline nova vinha do modelo GAB USA (24 fps) e o fps não pega por `SetSetting` | abre a Edit e espera até 3 min; `silencios.py` duplica a PRÓPRIA timeline, esvazia V1/A1 e para se o fps mudar |
| 16/10/2026 | Letterings na V2 não saíam no export (relato) | a V2 do modelo GAB USA vem desligada | `timeline_do_modelo` liga todas as trilhas; `renderizar` avisa de trilha com clipes desligada |
| 16/10/2026 | Motions encaixados por script saíam 1 quadro mais curtos e abriam vãos de 1 quadro (relato de usuário, Windows, DaVinci 21.0) | `endFrame` do `AppendToTimeline` é EXCLUSIVO, mas 8 pontos ainda usavam `- 1` | sem `- 1` em `cortes.py`, `silencios.py`, `broll.py`, `sfx_auto.py`, `legenda_baixa.py`, `colocar_musica` e `montar_takes` (resolve_lib) |
| 16/10/2026 | Reimportar um arquivo duplicava o clipe no Media Pool | `ImportMedia` sempre cria item novo | `importar()` procura antes (em todas as pastas) um item com o mesmo File Path e reaproveita; testado: 2ª importação devolve o mesmo item |
| 16/10/2026 | `medir_rosto` quebrou: `cv2 has no attribute CascadeClassifier` | dois pacotes do OpenCV instalados juntos (opencv-python + headless/contrib) | `medir_rosto`, `rastrear.py`, `cena/rosto.py` e `tela-dividida/layout.py` avisam em vez de quebrar; o `doctor --corrigir` reinstala só o `opencv-python` |
| 16/10/2026 | Regra antiga "neon na palavra-chave" (13/10) brigava com os clichês proibidos (16/10) | duas regras vivas no `lettering_motions.md` | neon e glow só com pedido ou preset; palavra-chave acende na cor da marca. Armadilhas de HyperFrames do relato (máscara, `svgOrigin`, carimbo, `<br>`, legenda gravada) no mesmo arquivo |
| 16/10/2026 | Render sem disco no C: e `-vsync` inexistente; SFX/música sem volume no DaVinci 21.0; paleta tirada do vermelho do Instagram | máquina com pouco disco, ffmpeg novo, DaVinci 21.0, só print do perfil | `render.md` (`--frames-cache-dir`, `-fps_mode passthrough`), `sfx.md` (ganho/fade na cópia, alinhar ataque/pico, trilha por família, música local), `cliente.md` (cores da interface do Instagram) |
| 13/10/2026 | `colar_motions` deixou 10 motions colados até 5 quadros ADIANTADOS da fala (vídeo A Grande Missão) | fechava cada vão de 1 quadro puxando o motion SEGUINTE para trás, e o atraso acumulava; o ramo antigo também usava endFrame com '-1' (é exclusivo), recriando o vão | agora estica o motion ANTERIOR até o próximo quando a mídia tem sobra (o próximo fica na palavra) e só puxa o seguinte se não houver sobra; endFrame sem '-1'. Motion encaixado à mão: `endFrame = quadros do trecho` (exclusivo) |
| 12/10/2026 | SFX do motion SUNPRIME sem imersão e com whoosh/efeito que não combinava | sons escolhidos pelo título do Artlist (arquivo era outra coisa), whoosh curto demais cortado, sem camada contínua, drone sombrio | `sfx_conferir.py` (CLAP + densidade + sincronia) e desenho em camadas em `docs/etapas/sfx.md` |
| 12/10/2026 | Projeto 23,976 fps (Sunprime) ficou com playback 24 e `SetSetting('timelinePlaybackFrameRate','23.976')` devolve False até em projeto novo, sem timeline | a API não aceita playback fracionado (só inteiros) | `criar_projeto`/`criar_timeline` avisam; corrigir pela interface (File > Project Settings > Master Settings > Playback frame rate = 23.976) e avisar o usuário logo na criação |
| 11/10/2026 | `transcrever.py` (motor davinci) devolveu a MESMA transcrição para 3 vídeos | buscava o item do Media Pool só pelo nome (`narracoes/audio.wav` em todos) | compara o caminho completo; gravação de apresentador: `transcrever.py saida.json --clipe "<clipe>"` lê a transcrição que o usuário já fez no DaVinci |
| 11/10/2026 | Whisper perdeu retakes e bagunçou tempos em gravação de rua | Whisper funde palavras e pula repetições | usar a transcrição do DaVinci (`--clipe`); Whisper só como último recurso |
| 11/10/2026 | `cortes.py` comeu palavras curtas ("não", "quanto") e inverteu o sentido de uma frase | o detector de silêncio corta palavra falada baixo | silêncio só é cortado fora das palavras da transcrição; o plano avisa "palavras fora dos cortes" |
| 11/10/2026 | sobrou o fim de uma palavra removida ("Porque") | a margem de 0,1 s antes do trecho invadia a palavra cortada | margem limitada pela palavra removida vizinha |
| 11/10/2026 | timeline nova saiu 1920x1080 | `CreateEmptyTimeline` usa o padrão do projeto (horizontal) | `cortes.py montar` copia resolução/fps da "<nome> - bruto" |
| 11/10/2026 | Voice Isolation não ligou | `SetVoiceIsolationState` só vale para a timeline ATUAL | `p.SetCurrentTimeline(t)` antes e conferir com `GetVoiceIsolationState` |
| 11/10/2026 | música não entrou na A2 (sem erro) | timeline de gravação só tem A1 | `colocar_musica` cria a trilha (`garantir_trilhas_audio`) e para com erro se não entrar |
| 11/10/2026 | música pré-cortada no ffmpeg não dava para ajustar | o usuário quer mexer na timeline | `colocar_musica(..., inicio_faixa=)` põe o WAV original com ponto de entrada e fades no clipe |
| 11/10/2026 | b-roll sumiu calado / ficou com 0,9 s | `AppendToTimeline` falha em silêncio quando não cabe no vão, e apara clipes sobrepostos | `broll.py` encurta ao vão livre, confere se entrou e avisa |
| 11/10/2026 | foto (still) ocupou 5 s e bloqueou o clipe seguinte | still entra com 5 s e a API não apara | `broll.py` coloca fotos por último, encaixadas no vão |
| 11/10/2026 | legenda/b-roll em tempo errado depois do usuário editar | tempos da fonte != tempos da timeline | `broll.transcricao_na_timeline(t, ...)` converte pela `GetSourceStartTime` de cada corte da V1 |
| 11/10/2026 | Magnific Kling cobrou/recusou ilimitado | o gerador abre com 1080p e ∞ OFF | 720p + ∞ ON e só gerar se aparecer "Unlimited videos for this resolution" (ver navegador/downloads.md) |
| 11/10/2026 | SKILL.md não carregava no `npx skills` | YAML: ":" sem aspas na description | description entre aspas |
| 12/10/2026 | preset de legenda (GAB USA) só entrava pela interface | a API não aplica estilo de legenda; o `.preset` é protobuf+zstd e só o DaVinci lê | o estilo vai junto quando a timeline é duplicada/importada: `resolve_lib.timeline_do_modelo()` cria a timeline a partir de "MODELO GAB USA" (ou importa `assets/davinci/modelo_gab_usa.drt`); `cortes.py montar` já usa |
| 12/10/2026 | `legenda_ui.py` leu o chat do Claude e clicou fora | a janela do Claude fica por cima do Inspector | `coberta()` para com erro claro; `--preset "GAB USA"` carrega o preset pela interface quando precisar |
| 12/10/2026 | régua da timeline não achada pelo OCR | painéis com outra altura | área de busca da régua ampliada (`TIMELINE`) |
| 12/10/2026 | download em lote do Magnific não chegou (zip e avulso) | Chrome segurando downloads seguidos do site | liberar "downloads automáticos" para magnific.com no Chrome (ícone de download da barra) |
| 12/10/2026 | b-roll caiu no tempo errado (0 s) | a frase também existia num retake cortado e o script usava a 1ª ocorrência | `broll.py` pula para a 1ª ocorrência que ficou na timeline |
| 12/10/2026 | "NÃO ENTROU" falso | a conferência exigia o quadro exato; o DaVinci desloca 1-2 quadros | confere pelo nome do arquivo com tolerância de 1 s |
| 12/10/2026 | 4 takes offline na timeline | o usuário tinha usado os arquivos direto de ~/Downloads e eu movi/renomeei para a pasta do vídeo | `resolve_lib.mover_e_relinkar(mp, origem, destino)`: move e faz ReplaceClip; sempre usar ao organizar arquivos que podem já estar no projeto |
| 12/10/2026 | troca de motions apagou um take do usuário (V3 do VIDEO 1) | o script apagou a trilha inteira achando que só tinha motions; o usuário também põe b-roll nela | trocar SÓ os itens pelo nome (`x0*`), nunca a trilha inteira; nunca usar Undo do DaVinci com o usuário editando (desfaz a ação dele) |
| 12/10/2026 | `DeleteClips` voltou sem apagar e o novo clipe entrou curto ao lado do antigo | `DeleteClips` só funciona na timeline atual | `p.SetCurrentTimeline(t)` + pausa ANTES de apagar/colocar; depois listar a trilha para conferir |
| 12/10/2026 | busca no Media Pool virou atalho de teclado no DaVinci (D liga/desliga clipe) | digitei sem o campo de busca focado, com o usuário editando | nunca digitar na interface do DaVinci com o usuário dentro; tudo pela API (regra 1g: retrato da timeline antes e depois) |
| 12/10/2026 | `colocar_legendas` podia não apagar as legendas antigas | apagava antes de abrir a timeline (DeleteClips só vale na atual) | abre a timeline primeiro e levanta erro se DeleteClips falhar |
| 12/10/2026 | legenda "passou na métrica" mas com frase picotada | o `metrica` só checa tamanho, palavra fraca e duração | revisão manual obrigatória das quebras (lista de proibidos no SKILL.md); "o que mais" no fim deixou de contar como palavra fraca |
| 12/10/2026 | legenda "sem a métrica" (Bora Comunicação): piscava e sumia nas pausas | o `sincronizar` deixava buraco entre legendas (pausa da fala, até 0,6 s); as aprovadas são contínuas | `legendas.colar()` roda no fim do `sincronizar`: fecha buracos de até 1,2 s esticando o fim da anterior |
| 12/10/2026 | `legenda_ui.py` não achava nada (ST1, régua, aba Track) | macOS 27: o OCR Vision nível Accurate falha (e5rtError) e volta vazio; o playhead em cima do "01:00:00:00" atrapalhava a leitura | fallback para o nível Fast, novas tentativas e início da timeline calculado pela escala das marcas da régua. **Mas evitar a UI:** desenhar motions e lettering acima da faixa da legenda (y < 1150) e a legenda fica toda em 724, sem mexer legenda por legenda |
| 12/10/2026 | lettering não entrava na V2 (`InsertFusionTitleIntoTimeline` só insere na V1, com ripple; com V1 travada volta None) | a API não muda a trilha de destino | lettering SEM UI: inserir o preset numa timeline auxiliar, `ajustar_titulo`, render ProRes 4444 com alfa (`ExportAlpha`) para `motions/lNN-*.mov` e `AppendToTimeline` na trilha LETTERING; apagar a auxiliar |
| 12/10/2026 | lettering não aparecia no render | a timeline do modelo GAB USA veio com a V2 DESLIGADA; `SetTrackEnable` devolve True mas não liga | conferir `GetIsTrackEnabled` de todas as trilhas antes do render; se alguma estiver desligada, um clique no ícone de filme do cabeçalho |
| 12/10/2026 | lettering editável (Fusion Title) entrava SECO no render, mesmo com `trocar_pela_copia` | a timeline em que o título foi inserido pela API renderiza sem a animação; `trocar_pela_copia` APAGAVA a original e a cópia voltava a sair seca | `trocar_pela_copia` agora mantém a original renomeada "(titulos via API)" e a cópia vira a principal: renderiza animado (conferido quadro 9/25/60). Títulos na V2 sem UI: `timeline_com_letterings()` (insere na V1 vazia e sobe com AddTrack index 1) ou atalho **Option+2** (destino V2) pelo System Events. Nunca render MOV no lugar do título: o usuário quer o título editável |
| 12/10/2026 | `legenda_ui.py` não achava a régua/início da timeline | OCR da régua instável (playhead em cima do 01:00:00:00, nível Fast) | sem OCR: playhead pela API no meio da 1ª legenda e o x dele pela COR da linha vermelha (`playhead_x`); campo Position Y da trilha com rolagem; índices das legendas que cruzam os MOTIONS calculados pela API e passados com `--indices` |
| 12/10/2026 | motion fora do centro (advogados, y≈880) | conteúdo subido para fugir da legenda | `scripts/centro.py corrigir/medir` antes de todo render (snapshots sem fundo, união do alfa, fit.json no wrapper #fit); motion nunca foge da legenda, a legenda desce |
| 12/10/2026 | depois de juntar os projetos (Export .drt + ImportTimelineFromFile), takes e NARRAÇÃO de outro vídeo nas timelines | a importação religa a mídia PELO NOME do arquivo e os nomes se repetiam entre vídeos (take_03_dyn.mov, narracao.wav) | conferir o File Path de todo item contra a pasta do vídeo e trocar (apagar sem ripple + AppendToTimeline no mesmo lugar e corte). Prevenção: nomes de arquivo únicos por vídeo (prefixo do vídeo) e, num lote, tudo no mesmo projeto desde o início |
| 12/10/2026 | lote Calverstone entregue com só 1 timeline aberta (Stacked ligado, mas sem as abas) | as timelines foram trocadas pela cópia (`trocar_pela_copia`) e a regra 1c não tinha função: abrir as abas dependia de lembrar | `resolve_lib.abrir_em_abas(p, nomes)` no fim de toda etapa e depois de cada troca pela cópia; regra 1c do SKILL.md manda conferir a barra de abas num zoom |
| 12/10/2026 | Calverstone: motion da gaveta com som de HUD (sem coerência) | o desenho de som escolhia pelo TIPO de animação (blip, whoosh), sem olhar o OBJETO que o motion mostra | `docs/etapas/sfx.md`: primeiro o objeto/ação representado (tabela de foley: gaveta, papel, carimbo, martelo, avião, relógio, batimento...), HUD só em interface; `colocar_plano_sfx` aceita duração por linha (`-NNdB D.Ds`) |
| 12/10/2026 | Calverstone: takes sem cor (PowerGrade) e respostas sem barra de progresso | a cor e a barra eram regras soltas no texto; `projeto.py` nem tinha a etapa "cor" e marcava motions por nome (os k0x não batiam) | etapas novas cor/letterings/abas detectadas na timeline (cor = nós > 1 em todo take da V1; motions = trilha MOTIONS); `projeto.py lote` e `projeto.py checklist` obrigatório antes de entregar (regras 1m e 1n); 7b: aplicar_grade logo depois de montar_takes |
| 12/10/2026 | Calverstone: quadros pretos no MP4 quando o motion entra (6,67 s e 42,33 s) | o BG do motion faz fade-in de 0,25 s e a V1 por baixo estava vazia (take tirado / take curto) | V1 nunca vazia sob motion: preencher o vão com o resto de um take (AppendToTimeline com startFrame) e aplicar a cor de novo; motions emendados sem fade do BG |
| 12/10/2026 | Calverstone: capa com letras borradas (Cinematic aos 3,3 s) e capa preta com seg_quadro 4,8 | o Cinematic ainda está no blur; a capa só põe 4 s de take | capa com "Palavra Por Palavra" em seg_quadro 3,6 (texto firme, dentro dos 4 s do take); take escuro atrás de texto branco; apagar as timelines "CAPA ..." depois |
| 12/10/2026 | Calverstone 04-06: take do espelho entrou em 19,5 s em vez de 33,1 s | `montar_takes` encadeia pelo fim REAL do take anterior; take curto adianta todos os seguintes | `montar_takes(..., respeitar_inicio=True)` quando há motions de tela cheia entre os takes (o vão fica sob o motion) |
| 12/10/2026 | render do HyperFrames falhou nos 4 vídeos só motion: "Disk capture may need ~7.9 GB" (1,4 GB livres) | MOV ProRes 4444 com várias workers grava cada quadro em disco; os MOV de motion (~250 MB cada) estavam duplicados em renders/ e nas pastas dos vídeos | vídeo opaco de tela cheia em MP4 `--workers 1` (streaming, ~20 MB); apagar renders/*.mov depois de copiar para a pasta do vídeo; conferir `df -h /` antes de render em lote |
| 12/10/2026 | Calverstone: usuário pediu som em cada movimento dos motions (havia ~11 sons em 30 s de motion) | o plano só cobria os momentos principais | `scripts/movimentos.mjs` lista todos os tweens; regra 'cada movimento tem som' em docs/etapas/sfx.md (cobertura de 0,4 s, batida `.in` no fim do tween, até 8 trilhas SFX) |
| 12/10/2026 | Calverstone: take de baixo aparecendo entre motions em sequência | motions com fade de 0,25 s no fundo (bgfade) entrando colados em outro motion ou sobre o CTA antigo, e vãos de 1-3 quadros pelo arredondamento do render em MP4 | `colar_motions(t, mp)` depois de colocar os motions (fecha vãos de até 0,6 s); motion colado em motion e CTA com `bgfade=False`; regra em docs/etapas/lettering_motions.md |
| 12/10/2026 | Calverstone 11-12: legendas desativadas sob motion voltaram por cima dos motions | `legenda_baixa.py` descia para Y 390 também as legendas DESATIVADAS (cobertas por motion) e criava clipes ativos na trilha LEGENDA BAIXA | `legenda_baixa.py` ignora legenda desativada (o motion fala por si só; quem desativa é o usuário) |
| 12/10/2026 | usuários instalando: "Docker não está instalado" no `hyperframes doctor`, sem dizer se é opcional | o instalador não instalava o Docker Desktop | `install.sh` (passo 2b, brew cask) e `windows/install.ps1` (winget) instalam o Docker Desktop como OBRIGATÓRIO, abrem e esperam o `docker info` responder; README nos requisitos |
| 12/10/2026 | Docker obrigatório travava a instalação (senha do Mac, WSL 2 no Windows) sem ser usado | o HyperFrames só usa Docker no render `--docker`, que o Gab não usa; o aviso do `hyperframes doctor` assustava | Docker saiu do install.sh, do install.ps1 e do doctor (vira informativo); regra em docs/etapas/lettering_motions.md para explicar o aviso |
| 12/10/2026 | Sonorização: carro salta em câmera lenta e o som segue em velocidade normal ("o áudio não passa essa sensação") | a análise só olhava quando algo se mexe, não a VELOCIDADE da imagem | `sonorizar.py analisar` detecta câmera lenta (fluxo óptico); plano ganha `camera_lenta` (abafa grave + reverb e volta seco no impacto) e eventos com `velocidade`, `reverso` e `livre` (`docs/etapas/sonorizacao.md` 2b) |
| 12/10/2026 | Sonorização: carro salta e CAI na terra, e o som era pneu cantando no asfalto ("isso é bizarro, não pode acontecer") | ação lida como freada/derrapagem e som escolhido pelo título ("drift car sliding to stop"), sem conferir o chão | `docs/etapas/sonorizacao.md` 1b: nomear ação (queda x freada) e chão; plano com `superficie`; `sonorizar.py conferir` (CLAP) roda no `mixar` e PARA com som do chão errado; rótulos de superfície em `sfx_conferir.py`; `de_arquivo`/`ate_arquivo` para usar só o trecho certo |
| 12/10/2026 | Sonorização: "som de avião no fundo sem necessidade" | ambiente de vento grave ("Desolate Desert: Harsh Wind") soa como turbina; CLAP dava "jet engine roar" em 1º e ninguém olhou o ambiente | `sonorizar.py`: avião/jato proibidos por padrão (`FORA_DE_CENA`, liberar com `permitidos`) e o `mixar` SEMPRE roda `conferir` (com aviso se faltar o CLAP); vento trocado; `sonorizacao.md` 1b |
| 12/10/2026 | 3D da Bora (bi10): "o vídeo do 3D sai de um lugar quadrado do nada" | objeto renderizado num quadrado 1080x1080 e colado por cima: notas e objetos cortados na borda do quadrado | 3D SEMPRE em tela cheia 1080x1920 com alfa e `deslocar_camera()` para pôr o objeto abaixo do texto (`tresd/cena_base.py`) |
| 12/10/2026 | 3D: "objetos com aberrações de luz e de polígonos", "carimbo zoado na folha" | EEVEE + luzes de área fortes, primitivas simples (caixa/cilindro) e boolean de carimbo | Cycles na GPU + HDRI de estúdio do Poly Haven (`gpu_cycles`, `hdri`, `tresd/polyhaven.py`), sólido de revolução (`torno`) e textura PBR real; detalhe gráfico (carimbo, etiqueta, texto) fica no 2D, não no 3D |
| 12/10/2026 | 3D: "não precisa ser tudo em 3D, o 3D é para complementar" | as 6 cenas viraram 3D e o motion 2D aprovado sumiu | base continua o motion 2D; 3D só em 2-3 momentos de impacto (objeto real: martelo, green card, logo) |
| 13/10/2026 | "esse render em 3D tem que ter barra de progresso, demora demais"; "parece que não tá renderizando" | render 3D em segundo plano sem nenhum andamento visível; Cycles levou ~50 min para 3 objetos | `tresd.cena` mostra a barra (quadros, %, tempo restante) e grava `<saida>.progresso`; `tresd.py progresso <pasta>`; EEVEE com `eevee_qualidade()` é o padrão, Cycles só a pedido |
| 13/10/2026 | "parece que os sfx tá fora do tempo" | plano escrito com o início do ARQUIVO; porta_slam (pico em 2,4 s), splash (4 s), cidade/lago/ovelhas (minutos de silêncio no começo), riser (pico em 11 s) caíam atrasados ou mudos | `scripts/plano_sfx_eventos.py`: linha = instante do evento + alinhar por ataque/pico/cama; mede, corta o começo e escreve o plano; conferir com `sfx_conferir.py sincronia` |
| 13/10/2026 | "você só colocou foto, tem que ser vídeo" | imagens de IA viraram clipe de push-in no ffmpeg e entraram como takes | toda imagem é animada no Magnific com ação ligada à frase; cortes pela legenda (takes.md) |
| 13/10/2026 | legenda fora do tempo em timeline 24 fps | `legendas.py` lia o timecode da transcrição do DaVinci sempre a 30 fps | `--fps` (ou 'fps' no json); padrão 30 só sem informação |
| 13/10/2026 | "apaga os takes que você renderizou e coloque os originais, garanta que isso nunca mais aconteça" | foto virou vídeo com push-in no ffmpeg e vídeos de IA ganharam cópias aceleradas (2x e por fluxo óptico) | cópias apagadas; trava `checar_take_original` em `importar`/`montar_takes` recusa vídeo re-encodado aqui |
| 13/10/2026 | prévia saiu só com legenda, sem os motions | a timeline do modelo (MODELO GAB USA) tem a V2 DESLIGADA e `SetTrackEnable("video", 2, True)` devolve True mas não liga | conferir `GetIsTrackEnabled` de cada trilha antes do render; se não ligar, pôr os clipes numa trilha ligada (V1) ou o usuário liga o olho da trilha |
| 13/10/2026 | quadros pretos entre os cortes de um vídeo só de motion | o motion renderizado sai 1 quadro mais curto que o trecho, e o fade de entrada/saída sem trilha por baixo vai para o preto | emendar cada corte no `GetEnd()` real do anterior e, sem trilha por baixo, corte seco (fade 0); conferir com `blackdetect` no render |
| 13/10/2026 | Instalador Mac travava em "OGAB_RELATOS: unbound variable" logo depois de escolher editor e motions (todo usuário novo) | variável de ambiente opcional lida sem padrão com `set -u` | `${OGAB_RELATOS:-}`; conferido rodando o install.sh do zero numa pasta pessoal falsa (saída 0) |
| 13/10/2026 | Instalador Mac morria no meio por falha de rede, pip ou git (sem mensagem útil) | `set -e`: `pip ... \|\| pip ...` (o último falha), `git pull` de referências sem `\|\| true`, `brew install` sem aviso | toda falha não essencial vira aviso; clone da skill que falha para com mensagem clara; config.json inválido é guardado e recriado |
| 13/10/2026 | Mac sem Homebrew: instalação do Homebrew falhava no `curl \| bash` e o brew sumia no Terminal seguinte | o instalador do Homebrew lia o próprio script como entrada; o PATH não ia para o ~/.zprofile | Homebrew lê do `/dev/tty`; `brew shellenv` gravado no ~/.zprofile; aborta com instrução se o brew não existir |
| 13/10/2026 | Scripts quebrando com Python 3.9 (o do macOS) e preset sketch/morph sem fontTools | o instalador só instalava Python se não houvesse nenhum; fontTools nunca era instalado | instalador garante Python 3.10+ (`brew install python`), instala fonttools; doctor confere versão e fonttools; scripts do Instagram com `from __future__ import annotations` |
| 13/10/2026 | Windows: instalador não rodava ou fechava a janela | `((cmd ...); $LASTEXITCODE -eq 0)` é erro de sintaxe (o `iex` lê tudo antes e nada roda); `exit 1` dentro do `irm \| iex` fecha o PowerShell | corpo dentro de `& { }` com `return`; teste do playwright reescrito; fonttools; clone que falha para com mensagem; config.json inválido recriado |
| 13/10/2026 | Usuários sem LUT, lettering e preset de legenda no DaVinci | lettering: o instalador morria no passo 4 (unbound variable), antes do passo das fontes/lettering; LUT: nunca foi instalada para o DaVinci (só no Premiere) e o PowerGrade (.drx) é pessoal, fora do git, então o config dos usuários vinha com a cor desligada; preset GAB USA: não existe arquivo global no DaVinci (fica dentro dos projetos) | instaladores copiam a LUT DO GAB para a pasta de LUTs do DaVinci (Mac pede a senha se precisar); `aplicar_grade(..., lut=)` aplica a LUT no nó 1 (Graph.SetLUT, testado) quando não há .drx; config de exemplo com a LUT ligada; doctor confere/copia a LUT e liga a cor de quem estava sem; projeto.py aceita LUT no nó 1 como cor feita; a legenda sai no estilo pelo modelo `assets/davinci/modelo_gab_usa.drt` |
| 13/10/2026 | Takes do Kling 10 s chegando com cara de câmera lenta (sem render nosso) | Kling espalha ação curta por 10 s | Prompt sempre com "real-time speed... no slow motion" + várias ações; ação curta gera em 5 s; conferir velocidade antes da timeline (takes.md) |
| 14/10/2026 | SFX estranhos e fora de tempo (carimbo sem carimbo batendo, xícara em mesa vazia, passos fora da pisada) | Som escolhido pelo assunto da cena, sem olhar os quadros | Tira de quadros por corte com o tempo da timeline, som só do que acontece, pisada/impacto no quadro do contato (sonorizacao.md, seção 0) |
| 14/10/2026 | SFX em vermelho (offline) e SFX antigos do usuário apagados | Pasta de SFX recriada no meio (DaVinci não religa) e `colocar_plano_sfx` apagava TUDO nas trilhas-alvo, que tinham mudado de número com AddTrack | `colocar_plano_sfx` só apaga clipes da própria pasta e só usa trilha sem nada no intervalo; nunca apagar/recriar a pasta de SFX já importada (gerar em pasta nova) |
| 14/10/2026 | SFX tocando antes da ação (passos 2,7 s antes, riser vazando 3 cenas) e sons que não eram o que o título dizia | `_segmento` incluía tudo antes do ataque; arquivos usados sem conferir | Sobra antes do ataque cortada; `sfx_conferir.py arquivos` obrigatório com rótulos de foley; camadas para ação grande |
| 14/10/2026 | Script de montagem no AE jogou fora alterações do usuário (relato do Rick, Windows) | `GAB.projeto` fechava o projeto aberto com `DO_NOT_SAVE_CHANGES` (sem nome) ou salvava por cima; `GAB.fechar` idem | `GAB.projeto` e `GAB.fechar` param com erro se `app.project.dirty`; `AE.fechar()` repassa o erro; README do AE com a regra e as armadilhas do ExtendScript; `principios_animacao.md` novo |
| 14/10/2026 | Vídeo postado com 10 takes sem cor | Takes novos entraram (outras trilhas) depois da etapa de cor e ninguém reaplicou | `renderizar` recusa exportar se `takes_sem_cor` achar take ligado sem grade em qualquer trilha |
| 15/10/2026 | `transcrever.py --clipe` quebrava ou dava tempos em horas em clipe de câmera (NBA, Start TC 06:15:36;19) | Palavras vêm no timecode da câmera, com `;` de drop frame; o script não descontava o Start TC e o split por `:` falhava | `via_clipe` converte com `silencios.tc_quadros` (drop frame) e desconta o Start TC; conferido: 1ª palavra em 0,17 s, última em 27,8 s num arquivo de 29 s |
| 15/10/2026 | Trailers 16:9 em Reels 9:16 com tarja preta, título cortado e legenda queimada depois do Smart Reframe | Smart Reframe segue a ação mas não tira letterbox nem avisa de texto cortado; ninguém conferia os quadros | Regra em `takes.md` (Horizontal em timeline vertical): cropdetect para o zoom, folha de stills de cada clipe conferida de olho e troca do trecho ruim antes de dizer pronto |
| 15/10/2026 | `timeline_do_modelo` trocou o fps do projeto (29,97 virou 24) (relato) | O `modelo_gab_usa.drt` é 24 fps e `ImportTimelineFromFile` grava o fps no projeto | Só importa o .drt se o projeto já é 24 fps; senão devolve None e quem chama cria timeline vazia (preset por `legenda_ui.py`) |
| 15/10/2026 | `renderizar` recusava por lettering "sem cor" (relato) | `takes_sem_cor` contava título do Fusion (sem MediaPoolItem) como take | Item sem MediaPoolItem é pulado |
| 15/10/2026 | Motion com texto encostando na borda, cortado no feed do Instagram | `centro.py` limitava à tela inteira (1000x1400); o feed corta o Reels em 4:5 (1080x1350) | Área segura 900x1200 no `centro.py` e regra em `lettering_motions.md` |
| 15/10/2026 | Vídeos exportados e agendados sem SFX | "exporta e agenda" foi tratado como pular etapas; o checklist não rodou | `renderizar` recusa timeline sem SFX (A3+) salvo `sem_sfx=True`; regra em `render.md` |
| 15/10/2026 | Buraco de 1-2 quadros entre cortes ao trocar trecho de trailer | `AppendToTimeline` com fonte 25/23,976 fps em timeline 24: endFrame exclusivo e duração arredondada para baixo | Fórmula em `davinci_api.md` (n = ceil(D x fps_fonte / fps_tl)) + conferir `GetEnd` |
| 15/10/2026 | `movimentos.mjs` quebrava em kit com `const tl` dentro de função | Só lia o `tl` global | Cai para `window.__timelines` |
| 15/10/2026 | `plano_sfx_eventos.py` lia 0 sons | Regex exigia "dB" colado no volume | "dB" opcional |
| 15/10/2026 | Barra de progresso marcava motions como faltando | Detecção só pela trilha "MOTIONS" ou pelo nome | Também pela pasta `motions/` e trilha "MOTIONS ..." |
| 15/10/2026 | Instalador do Windows travado em 100% de CPU depois dos pré-requisitos (usuário Windows) | `function Py { & py -3 @args }`: PowerShell não diferencia maiúscula em nome de comando, então `py` chamava a própria função em loop | `& py.exe -3 @args`; README com `-ExecutionPolicy Bypass -File` para quem roda o arquivo baixado |
| 15/10/2026 | Instalador do Windows travado no passo 9/10 (plugin do Premiere) numa máquina sem Premiere | O instalador da Adobe (UnifiedPluginInstallerAgent) rodava mesmo sem Premiere e sem limite de tempo, e fica parado | `premiere/instalar.ps1` e `.sh`: só chama o instalador da Adobe com o Premiere instalado e com limite de 2 min (encerra e segue) |
| 15/10/2026 | Instalador do Windows nem começava: 'Referência de variável inválida' (relato de instalação, Windows 11, PowerShell 5.1) | `"DaVinci $ver: ..."`: dentro de aspas, `$ver:` é lido como variável com escopo e o script inteiro falha na análise | `${ver}`; GitHub Actions analisa todo `.ps1` no Windows PowerShell 5.1 a cada push (`.github/workflows/powershell.yml`); log ao vivo em `%TEMP%\ogab-install.log`; README com instalação pelo Claude Code (variáveis OGAB_EDITOR/MOTION/RELATOS) |
| 15/10/2026 | Etapa de silêncios pulada em vídeo de narração (voz gerada) | `silencios.py` só lia a V1; com a narração na A1 e a V1 vazia não havia o que cortar | Modo narração: V1 vazia = corta as pausas da A1 (mantém o volume do clipe); regra 1f0 e davinci.md: rodar logo depois de `colocar_narracao` |
| 15/10/2026 | Windows: API não conectava com o DaVinci em D:\DaVinci (`DLL load failed ... fusionscript`) (relato de uso, Windows 11) | Instalador e sitecustomize só olhavam C:\Program Files | install.ps1 acha pelo processo/atalho/registro; sitecustomize pelo registro e pela RESOLVE_SCRIPT_LIB válida |
| 15/10/2026 | `colocar_plano_sfx`/`colocar_musica` quebravam no DaVinci 21.0 (`SetFades`) | SetFades/GetFades só existem no 21.1+ | `set_fades`/`get_fades` com aviso; aviso também quando o AudioVolume é recusado |
| 15/10/2026 | Prova de render apagou a fila de render do usuário | `renderizar`, `renderizar_trecho`, `gerar_capa` e a conferência de títulos apagavam TODOS os jobs | Só apagam o próprio job depois do render |
| 15/10/2026 | V2-V4 ficaram desligadas depois de uma prova | `SetTrackEnable` não religa na página Deliver | `renderizar_trecho` volta à página Edit antes de religar e confere |
| 15/10/2026 | DaVinci fechou no render da prova (Windows) | Encoder H.264 do Media Foundation ("Fail to create output buffer") | Prova no Windows em ProRes 422 LT (.mov) |
| 15/10/2026 | Whisper quebrava (`metadata_errors`) e não usava a GPU (`cublas64_12.dll`, `bad allocation`) | PyAV incompatível; faltavam DLLs CUDA; DaVinci ocupando a VRAM | transcrever.py decodifica com ffmpeg, tenta GPU int8_float16 e cai para CPU; instalador põe nvidia-cublas/cudnn com placa NVIDIA e sitecustomize registra as pastas |
| 15/10/2026 | `legenda_auto.py --gerar` quebrava (IndexError) com a trilha de legenda vazia (vídeo Violet Jessop) | DaVinci recém-aberto fora da página Edit: `CreateSubtitlesFromAudio` devolve True e as legendas só aparecem depois; o script lia na hora | Vai para a página Edit, espera até 120 s a trilha parar de crescer e para com erro claro; trilha vazia sem `--gerar` também para |
| 15/10/2026 | `montar_takes(..., permitir_render=True)` recusava o motion ("TAKE RE-RENDERIZADO RECUSADO") | o parâmetro era checado mas não ia para o `importar`, que checava de novo sem ele | `importar(mp, arq, "BROLLS", permitir_render)` |
| 15/10/2026 | `legenda_ui.py --preset` falhou com o DaVinci em janela menor | as regiões do Inspector e da timeline são medidas com o DaVinci maximizado | `frente()` maximiza a janela principal na tela útil (System Events), sem tela cheia |
| 15/10/2026 | `sfx_conferir.py` quebrava sem `torch` (relato de usuário) | torch/transformers não instalados no Python que rodou o script (ou rodado com o `/usr/bin/python3` do macOS) | o script diz se outro `python3` da máquina já tem e, se não, o comando de instalar (~2 GB); o `doctor` mostra torch + transformers sem instalar sozinho |
| 15/10/2026 | 1 quadro preto entre cenas coladas; flash/queima antes da hora; caixa vazia antes da digitação; filmagem P&B sépia | arredondamento de quadro no render; `immediateRender` do `fromTo`; LUT do Gab em filmagem de arquivo P&B | regras em `lettering_motions.md` (0,15 s de folga, `immediateRender:false`, caixa nasce com a 1ª letra) e no 7b do SKILL.md (P&B sem LUT) |
| 17/10/2026 | "TAKE RE-RENDERIZADO RECUSADO" em vídeo baixado pelo `baixar_video.py` | o download re-encodava tudo com libx264 e a trava reconhece a libavcodec local | H.264 yuv420p vira remux; download inteiro leva `comment=ogab:download-integral`, que `take_renderizado_aqui` aceita |
| 17/10/2026 | legendas não desciam debaixo dos motions de tela cheia | `legenda_ui.dados()` só olhava trilhas LETTERING; `colocar_motions` cria a trilha MOTIONS | considera LETTERING e MOTION |
| 17/10/2026 | export travava com "takes sem cor" em filmagem de arquivo P&B | a regra 7b manda P&B sem LUT, mas `takes_sem_cor` exigia grade em todo take | `take_pb()` (quadro do meio sem croma) libera P&B na trava |
| 17/10/2026 | storyboard no Windows: FileNotFoundError ao rodar npm (relato) | subprocess sem shell não acha npm.cmd | `shutil.which("npm")` no navegador.py |
| 17/10/2026 | instalador do Premiere não acha Premiere fora do C: (relato) | só procurava em ProgramFiles\Adobe | procura também pelo processo aberto do Premiere |
| 17/10/2026 | Premiere 26.0: createSubClipAction is not a function (relato) | API UXP do 26.0 não tem subclipe | erro claro no soVideo + receita no README |
