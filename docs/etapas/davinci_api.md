<!-- Engenharia reversa do DaVinci Resolve Studio 21.1.1 (15/10/2026). Ler antes de prometer qualquer coisa "pela API"
     ou de automatizar uma etapa nova no DaVinci. -->

# O que dá para fazer no DaVinci por API, por MCP e pela tela

## As camadas de controle (da mais confiável para a menos)

| Camada | O que é | Quando usar |
|---|---|---|
| **API de scripting** (`resolve_lib.py`) | 416 funções documentadas em `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/DaVinciResolveScript.pyi` (a fonte oficial; o README manda para ele). Só no Studio. | Sempre que existir função. |
| **Fusion (`resolve.Fusion()`)** | 132 métodos sem documentação + `ActionManager` com 887 ações, **todas da página Fusion** (nenhuma de timeline/edição). | Composições, Text+, nós, keyframes dentro do Fusion. |
| **OGraf (títulos em HTML)** | Padrão EBU: título feito em HTML/CSS/JS (Web Component com `goToTime`), renderizado pelo DaVinci como Title do Edit, com parâmetros editáveis no Inspector. Docs e exemplos em `Developer/OGraf HTML Templates/`; instala em `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/Edit/Titles/OGraf/`. Exige `"supportsNonRealTime": true`. | Lettering/motion EDITÁVEL feito em HTML (mesma linguagem do HyperFrames) sem MOV. **Testado e funcionando (15/10/2026)** via nó `OGrafLoader` do Fusion; a API não insere OGraf pelo nome. Ver `ograf/README.md`. |
| **Workflow Integration** | Plugin Electron dentro do DaVinci (painel próprio) usando a mesma API em JavaScript. | Painel para o usuário; não dá poder novo. |
| **Menu pela tela** (`app_menu` do computer use ou System Events) | Qualquer item de menu, mesmo sem API. Age no projeto que estiver na frente e quebra se o layout mudar. | Só quando não houver API e o usuário quiser. Ex.: `Clip > Audio Operations > Ripple Delete Silence…`. |
| **MCP `samuelgursky/davinci-resolve-mcp`** | 3,5 mil estrelas, cobre 100% da API, servidor "advanced" que edita `.drp/.drt/.drx` OFFLINE, e uma lista de armadilhas verificadas (`docs/reference/api-limitations.md`). | Opcional; o Gab já fala direto com a API. A lista de armadilhas vale mais que o servidor. |

**Cuidado ao sondar a API:** `hasattr`/`getattr` não provam que uma função existe (a ponte Python pode devolver um
"callable" falso). Existência se confere com `dir()`, e comportamento chamando e lendo de volta.

## O que o Gab usa (103 das 416) e o que vale a pena usar

Usadas hoje: projeto/timeline/media pool, `AppendToTimeline`, títulos Fusion, legenda (`CreateSubtitlesFromAudio`),
transcrição (`TranscribeAudio`/`GetTranscription`), Voice Isolation, cor (`SetLUT`, `ApplyGradeFromDRX`), render.

Não usadas e úteis para edição (assinaturas do `.pyi`):

| Função | Para quê |
|---|---|
| `TimelineItem.GetSpeed()` / `SetSpeed({...})` (21.1) | Ler/pôr velocidade em %. `GetSpeed` → `{'Percentage': 100.0, 'PitchCorrection': True}`. Speed ramp NÃO aparece. |
| `TimelineItem.GetFades()` / `SetFades({'FadeIn': n, 'FadeOut': n})` (21.1) | Fade de vídeo/áudio do clipe em quadros (música, transições suaves). |
| `TimelineItem.AddTransition({...})` (21.1) | Transição no começo/fim do clipe (antes só pela tela). |
| `TimelineItem.GetType()` | 'video', 'audio', 'generator' ou 'transition'. |
| `TimelineItem.SmartReframe()` | Reenquadrar horizontal → vertical com IA. |
| `TimelineItem.Stabilize()` | Estabilizar take tremido. |
| `TimelineItem.CopyGrades([itens])` | Copiar a cor de um take para outros (ver armadilha abaixo). |
| `TimelineItem.SetClipColor(nome)` | 16 nomes da paleta do Edit (Orange, Apricot, Yellow, Lime, Olive, Green, Teal, Navy, Blue, Purple, Violet, Pink, Tan, Beige, Brown, Chocolate); qualquer outro devolve False calado. |
| `Timeline/TimelineItem/MediaPoolItem.AddMarker(...)` | Marcadores para o usuário revisar (ex.: "conferir legenda aqui"). |
| `Timeline.DetectSceneCuts()` | Cortar um vídeo pronto nas trocas de cena (referência, material de cliente). |
| `Timeline.NormalizeAudioLevel(itens, opções)` | Normalizar nível dos clipes de áudio. |
| `Timeline.GetSelectedClips()` / `MediaPool.GetSelectedClips()` | Agir no que o usuário selecionou ("arruma esses aqui"). |
| `Timeline.Export(arq, tipo, subtipo)` | Exportar FCPXML, EDL, AAF, DRT, OTIO (CapCut/Premiere/Final Cut). |
| `Project.ExportCurrentFrameAsStill(arq)` | Tirar quadro para capa/conferência sem render. |
| `Project.RenderWithQuickExport(preset, {...})` | Prévia rápida. |
| `Project.GenerateSpeech({...})` | Voz por IA do próprio DaVinci (precisa do Extra "AI Speech Generator"). |
| `MediaPool.AutoSyncAudio(clipes, opções)` | Sincronizar áudio externo (lapela) com câmera. |
| `MediaPool.CreateMulticamClip(...)` + `TimelineItem.PerformMulticamSmartSwitch(...)` (21.1) | Podcast/entrevista com 2+ câmeras: troca de câmera automática por quem fala. |
| `MediaPoolItem.PerformAudioClassification()` | Classificar áudio (fala, música, ambiente). |
| `MediaPoolItem.AnalyzeForIntellisearch(rostos, melhor)` | Busca por conteúdo/rosto no Media Pool. |
| `MediaPoolItem.RemoveMotionBlur({...})` | Tirar borrão de movimento (cria mídia nova). |
| `Gallery.GetGalleryPowerGradeAlbums()` etc. | Ler/gerenciar PowerGrades e stills. |
| `Resolve.LoadLayoutPreset` / keyboard e preferências presets | Padronizar a interface do usuário. |

Funções escondidas que existem no binário (fora do `.pyi`): `Resolve.GetLicenseType()` (devolveu 1 = Studio),
`MediaPoolItem/Folder.GetLast...Speed()` (tempo da última análise de IA; "0.00" sem análise), `Resolve.Get/SetShowAllVideoFrames`,
`Resolve.Get/SetSourceViewerMode`, `Project.GetPlaybackSpeed`, `Graph/TimelineItem.ResetNode`, `Resolve.TriggerCtrKTest`
(gancho de teste interno: NÃO chamar). Só as duas primeiras foram confirmadas devolvendo valor real.

## O que a API NÃO faz (confirmado; fazer pela tela ou contornar)

- **Cortar (blade/razor) um clipe já na timeline, aparar, mover, slip/slide:** não existe. Contorno do Gab: montar
  os trechos já cortados com `AppendToTimeline` (é o que `cortes.py` e `silencios.py` fazem) numa timeline nova.
- **Insert/Overwrite/Replace/Fit-to-Fill:** só `AppendToTimeline` (com `recordFrame`/`trackIndex`). Sobreposição na
  mesma trilha: o item que entrou antes ganha, o novo é descartado sem erro.
- **EQ, automação, FairlightFX, AI Audio Assistant:** nada. MAS no 21.1 o clipe de áudio aceita pela API `AudioVolume`,
  `AudioPan`, tom (`AudioPitchSemiTones/Cents`), Voice Isolation e Dialogue Leveler por clipe (`SetProperties`/`GetProperty`,
  testado 15/10/2026: volume -8 dB e fades 24/72 quadros lidos de volta). A lista do MCP (feita no 21.0) ainda diz que não.
- **Cor primária (lift/gamma/gain, curvas, janelas) e criar/ligar nós:** não. Só LUT, CDL, DRX/PowerGrade, CopyGrades.
- **Texto e estilo de cada legenda:** não dá para editar texto/tempo de uma legenda nem o estilo da trilha pela API
  (o Gab usa SRT novo + timeline do modelo com o preset GAB USA).
- **Silêncio:** "Remove Silent Portions" (transcrição > ⋯) e "Ripple Delete Silence" (Clip > Audio Operations) só pela
  tela. O Gab corta silêncio pela transcrição (`silencios.py`).
- **Render in Place, gerar proxy/optimized media, Smart Bins, renomear pasta do Media Pool:** só pela tela.
- **Magic Mask:** `CreateMagicMask` só rastreia uma máscara que o usuário já marcou com cliques.

## Testado no Gab em 15/10/2026 (projeto NBA, Studio 21.1)

| Recurso | Resultado | Função |
|---|---|---|
| Fade e volume da música no clipe | `GetFades` {24, 72}, `AudioVolume` -8 lidos de volta | `colocar_musica` |
| Clipes selecionados pelo usuário | `GetSelectedClips` devolve vídeo + áudio ligado do clipe clicado | `selecionados` |
| Smart Reframe | só muda algo com o clipe em preencher (`Scaling` 3); seguiu a jogada num 16:9 em 9:16 | `reenquadrar_vertical` |
| Estabilizar | `Stabilize` True em ~6 s; nenhuma leitura de volta | `estabilizar` |
| Multicam + Smart Switch | 2 ângulos, 5 trechos alternando câmera (só pelo áudio, ~4 s) | `multicam_podcast` |
| Render do Fusion (`comp.Render`/Saver) | abre "Render completed!" e TRAVA a API até clicar OK (mesmo com Quiet) | não usar; render do DaVinci |

## Armadilhas verificadas (a função diz True e não fez)

- `AutoSyncAudio` e `CreateSubtitlesFromAudio`: as opções precisam das CONSTANTES (`resolve.AUDIO_SYNC_*`,
  `resolve.SUBTITLE_*`/`AUTO_CAPTION_*`); chave em texto é ignorada e o booleano não é confiável. Conferir lendo de volta.
- `SetClipColor` em título/gerador devolve True e não grava.
- `CopyGrades` pode devolver True sem copiar: conferir o nó/LUT do destino.
- `ProjectManager.CreateProject` descarta o projeto aberto se ele não estiver salvo: `salvar()` antes.
- Timecode das palavras da transcrição e de clipes de câmera vem com `Start TC` (ex.: `06:15:36;19`, drop frame):
  descontar (`silencios.tc_quadros`).
- `AppendToTimeline`: o retorno não prova nada e o SALVAR descarta trechos de um append que deu erro. Conferir a contagem DEPOIS de `salvar()` (`silencios.py` e `cortes.py` já fazem). Com fps da mídia diferente da timeline, cada trecho perde até 1 quadro (arredonda para baixo).
- `DeleteClips` só funciona na página Edit (no Fairlight/Color devolve False e não apaga): `R.pagina_edit()` antes (já nas funções da lib que apagam).
- `CreateProject` descarta o projeto atual se não estiver salvo: `criar_projeto` salva antes. `SaveProject` no "Untitled Project" falha (e TRAVA sem interface): `R.salvar()` pula esse caso.
- Render: `SetRenderSettings` aplica POR CIMA do preset carregado e uma chave recusada derruba o pacote inteiro (devolve False); o `StartRendering` às vezes devolve False e o job fica parado; `JobStatus` é texto traduzido. Vale `CompletionPercentage == 100` + arquivo existindo (`renderizar` confere). `ExportSubtitle`/`BurnIn` já foi visto sem efeito: conferir a legenda num quadro do MP4.
- `Project.GetCurrentRenderMode()` muda a tela para a página Deliver: não usar (ou ler a página antes e voltar).
- Importar `.drt`/XML num projeto com mídia parecida religa os clipes na mídia ERRADA sem avisar (mesma identidade grosseira): conferir o File Path de cada item depois (já era regra 1a).
- `Graph.SetLUT` só acha LUT na pasta MASTER de LUTs do DaVinci (o instalador do Gab já põe lá).
- Fusion: valor escrito com `SetInput` entre `comp.Lock()` e `Unlock()` aparece certo na leitura e NÃO sai no render; travar só para criar/ligar nós (a lib já faz assim). Composição criada pela API só renderiza se o MediaOut descender do MediaIn.
- Nunca fechar/apagar projeto com render rodando: trava a fila de render até sair do DaVinci.
- Lista completa (101 itens, MIT): `docs/referencia/davinci_limitacoes_mcp.md`, copiada do repositório do MCP; ler a seção da função antes de usar algo novo.

## Próximos passos possíveis (ainda não feitos)

1. Mais templates OGraf (CTA, lower third, número animado) e motions HyperFrames convertidos para OGraf (GSAP em modo seek).
2. `SetFades` na música (fade no clipe pela API, já é a regra da música bruta) e `AddTransition` onde o estilo pede.
3. Multicam + Smart Switch para podcast/entrevista com 2 câmeras.
4. `Timeline.Export` para FCPXML/OTIO quando o usuário quiser abrir no Final Cut/CapCut/Premiere.
5. Mapa completo dos menus do DaVinci (para o que só existe na tela), gerado com o DaVinci aberto.

## AppendToTimeline com take de outro fps (aprendido em 15/10/2026, trailers de 25 e 23,976 fps em timeline 24)
- `startFrame`/`endFrame` são quadros DA FONTE e o `endFrame` é exclusivo. O item na timeline fica com floor(n x fps_timeline / fps_fonte) quadros, n = endFrame - startFrame.
- Por isso, para preencher D quadros da timeline, calcular n = ceil(D x fps_fonte / fps_timeline) e conferir o fim do item depois (`GetEnd`). Sem isso, sobra 1 a 2 quadros de buraco preto entre os cortes.
- `GetLeftOffset()` vem em quadros da timeline: segundos da fonte = LeftOffset / fps_timeline.
- Trocar um clipe por outro trecho: `DeleteClips` + `AppendToTimeline` no mesmo `recordFrame`, e depois refazer Smart Reframe, zoom de letterbox e grade (o item novo vem cru).


## Armadilhas achadas em 19/10/2026 (dublagem Tamanhos de Plano)
- Vídeo 23,976 numa timeline de 24: o DaVinci toca quadro a quadro (0,1% mais rápido; ~0,7 s em 12 min). Narração/música em tempo real descolam aos poucos. Posição na timeline = quadro_da_fonte (t*23.976) / 24; música/áudio externo do original: `atempo=1.001001`.
- **Mas nem sempre (19/10/2026, ep. 2 no mesmo projeto):** o vídeo posto por `AppendToTimeline` com `startFrame`/`endFrame` entrou no TEMPO REAL (12253 quadros da fonte viraram 12266 na timeline), e a conversão acima adiantou tudo 0,5 s no fim. Antes de converter tempos, comparar `GetDuration()` do item com `endFrame - startFrame` (iguais = quadro a quadro; maior = tempo real) ou comparar quadros do export com o original em 3 pontos. No tempo real: posição = t do original e música sem `atempo`.
- Mudança pela API numa timeline que NÃO está aberta pode sumir ao salvar: sempre `p.SetCurrentTimeline(t)` antes de mexer, e conferir as trilhas DEPOIS de `salvar`.
- `AppendToTimeline`: `endFrame` é exclusivo (passar `sf + n`, não `sf + n - 1`, senão sobra vão de 1 quadro entre clipes).
- Imagem parada (PNG) ignora `endFrame` e entra com 5 s: para overlay com duração exata, converter em MOV (QuickTime Animation `qtrle` com alfa; "PNG dentro de MOV" falha no render).
- Arquivo substituído no mesmo caminho fica "quebrado" na timeline (o DaVinci guarda a duração antiga): usar `MediaPoolItem.ReplaceClip(novo_caminho)` com nome novo; troca a mídia sem mexer nos cortes do usuário.
- Cartão e tarja na mesma trilha: quando se encostam, o append corta o começo do outro. Overlays de tipos diferentes em trilhas próprias.
