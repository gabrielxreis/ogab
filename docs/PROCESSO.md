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
