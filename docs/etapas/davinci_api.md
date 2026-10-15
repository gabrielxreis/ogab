<!-- Engenharia reversa do DaVinci Resolve Studio 21.1.1 (15/10/2026). Ler antes de prometer qualquer coisa "pela API"
     ou de automatizar uma etapa nova no DaVinci. -->

# O que dá para fazer no DaVinci por API, por MCP e pela tela

## As camadas de controle (da mais confiável para a menos)

| Camada | O que é | Quando usar |
|---|---|---|
| **API de scripting** (`resolve_lib.py`) | 416 funções documentadas em `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/DaVinciResolveScript.pyi` (a fonte oficial; o README manda para ele). Só no Studio. | Sempre que existir função. |
| **Fusion (`resolve.Fusion()`)** | 132 métodos sem documentação + `ActionManager` com 887 ações, **todas da página Fusion** (nenhuma de timeline/edição). | Composições, Text+, nós, keyframes dentro do Fusion. |
| **OGraf (títulos em HTML)** | Padrão EBU: título feito em HTML/CSS/JS (Web Component com `goToTime`), renderizado pelo DaVinci como Title do Edit, com parâmetros editáveis no Inspector. Docs e exemplos em `Developer/OGraf HTML Templates/`; instala em `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/Edit/Titles/OGraf/`. Exige `"supportsNonRealTime": true`. | Candidato a motion/lettering EDITÁVEL feito em HTML (mesma linguagem do HyperFrames) sem MOV. Ainda não testado no Gab. |
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
- **Volume, pan, EQ, automação, FairlightFX, AI Audio Assistant:** nada (só Voice Isolation e normalização). O ganho
  da música/narração vem do arquivo ou da mão do usuário.
- **Cor primária (lift/gamma/gain, curvas, janelas) e criar/ligar nós:** não. Só LUT, CDL, DRX/PowerGrade, CopyGrades.
- **Texto e estilo de cada legenda:** não dá para editar texto/tempo de uma legenda nem o estilo da trilha pela API
  (o Gab usa SRT novo + timeline do modelo com o preset GAB USA).
- **Silêncio:** "Remove Silent Portions" (transcrição > ⋯) e "Ripple Delete Silence" (Clip > Audio Operations) só pela
  tela. O Gab corta silêncio pela transcrição (`silencios.py`).
- **Render in Place, gerar proxy/optimized media, Smart Bins, renomear pasta do Media Pool:** só pela tela.
- **Magic Mask:** `CreateMagicMask` só rastreia uma máscara que o usuário já marcou com cliques.

## Armadilhas verificadas (a função diz True e não fez)

- `AutoSyncAudio` e `CreateSubtitlesFromAudio`: as opções precisam das CONSTANTES (`resolve.AUDIO_SYNC_*`,
  `resolve.SUBTITLE_*`/`AUTO_CAPTION_*`); chave em texto é ignorada e o booleano não é confiável. Conferir lendo de volta.
- `SetClipColor` em título/gerador devolve True e não grava.
- `CopyGrades` pode devolver True sem copiar: conferir o nó/LUT do destino.
- `ProjectManager.CreateProject` descarta o projeto aberto se ele não estiver salvo: `salvar()` antes.
- Timecode das palavras da transcrição e de clipes de câmera vem com `Start TC` (ex.: `06:15:36;19`, drop frame):
  descontar (`silencios.tc_quadros`).
- Lista completa e atualizada: `docs/reference/api-limitations.md` do repositório do MCP acima (42 lacunas, 58 bugs).

## Próximos passos possíveis (ainda não feitos)

1. Motions/letterings como **OGraf** (HTML editável no Inspector) em vez de MOV, reaproveitando o HyperFrames.
2. `SetFades` na música (fade no clipe pela API, já é a regra da música bruta) e `AddTransition` onde o estilo pede.
3. Multicam + Smart Switch para podcast/entrevista com 2 câmeras.
4. `Timeline.Export` para FCPXML/OTIO quando o usuário quiser abrir no Final Cut/CapCut/Premiere.
5. Mapa completo dos menus do DaVinci (para o que só existe na tela), gerado com o DaVinci aberto.
