# Final Cut Pro: engenharia reversa (o que dá para automatizar e como)

Final Cut Pro "Creator Studio" 12.2 (`com.apple.FinalCutApp`), estudado em 13/10/2026 só pelo que o próprio app expõe
(dicionário de AppleScript, frameworks, plists, strings e símbolos Objective-C), sem quebrar proteção nenhuma.
Objetivo: chegar o mais perto possível do DaVinci (que tem API de script) para o Gab editar no Final Cut.

Legenda dos testes: ✅ testado e funciona · ❌ testado e não funciona · ⏳ falta testar · 🔒 depende de algo do usuário.

## Mapa das superfícies

| # | Superfície | O que expõe | Lê | Escreve | Estado |
|---|---|---|---|---|---|
| 1 | AppleScript (`ProEditor.sdef`) | 1 comando (`get`), classes library > event > project > sequence (nome, id, duração, início, quadro, timecode). Nada oculto. | sim | não | ⏳ (sem biblioteca aberta o `get` volta vazio) |
| 2 | Apple Event "abrir documento" (`open -a ... x.fcpxml`) | importa FCPXML (tipos "Final Cut Pro XML" e "XML Bundle") | não | sim | ✅ abre o import; ❌ sem biblioteca aberta ele IGNORA `library location` e pergunta em qual biblioteca (painel do sistema, só clique humano) |
| 3 | FCPXML 1.0-1.14 (DTDs em `Interchange.framework/.../Resources`) | projeto inteiro: clipes, cortes, camadas, títulos, legendas, volume/fades, efeitos, transições, cor | sim (Export XML) | sim | ✅ gerador `fcpxml.py` valida no DTD 1.11 oficial; ⏳ importar com biblioteca aberta |
| 4 | Área de transferência | tipos `com.apple.finalcutpro.xml.v1-10 ... v1-13` (Interchange `XMLPasteboardType`); a timeline lê com `FFAnchoredTimelineModule _anchoredClipsFromPasteboard`; comando `PasteAsConnected` | - | sim | ⏳ **chave**: colar FCPXML na timeline ABERTA no cabeçote (edição incremental sem reimportar) |
| 5 | Comandos (`NSProCommands.plist` + `NSProCommandsAdditional.plist`) | 563 comandos internos com seletor (ex. `BladeAtPlayhead` -> `blade:`), 391 com atalho padrão (`en.lproj/Default.commandset`) | - | sim (menu por acessibilidade ou atalho) | ⏳ |
| 6 | Acessibilidade (AX) | barra de menus inteira (781 itens) + **a timeline item por item**: cada clipe é um `AXLayoutItem`/`AXTimeline` com `AXDescription` = `Tipo:Nome` (`Video-Clip:ia_11_v.mp4`, `Title:Um mineiro que se chamava`, `Audio-Clip:...`, `Gap:Gap`), `AXValue` = duração em timecode, `AXHandles` = alças "Leading Edge"/"Trailing Edge" com o timecode de início/fim, `AXSelected` (selecionável por script), `AXFrame` (posição/camada) e ação `AXShowMenu`; a área "Project Timeline" (`AXLayoutArea`) tem `AXSelectedChildren` | sim | sim (selecionar + comando) | ✅ inventário e leitura dos clipes (`ax.py`); ❌ painéis de abrir/salvar são de outro processo; ❌ com o Final Cut em OUTRA mesa (Space) as janelas somem da AX (só a barra de menus) |
| 7 | Workflow Extensions (`ProExtensionHost.framework`) | classes `FCPXHost`, `FCPXTimeline` (`activeSequence`, `playheadTime`, `movePlayheadTo:`, `sequenceTimeRange`, observadores), `FCPXLibrary/Event/Project/Sequence` | sim | só cabeçote | 🔒 a parte de timeline usa o canal privado da extensão (`_setupRemoteDelegateWithRemoteExtensionContext:`, PlugInKit), NÃO Apple Event: só uma extensão de verdade (app assinado com `com.apple.FinalCut.WorkflowExtension`, dá para fazer no Xcode) |
| 8 | Notificações `com.apple.finalcut.timelineAction` / `timelineNotification` | nomes usados pela ponte da extensão | ? | ? | ⏳ ver se são distribuídas (qualquer processo escuta) |
| 9 | Catálogo de efeitos | 138 títulos, 35 geradores, 65 transições (Motion, `MotionEffect.fxp/.../PETemplates.localized`) + 261 filtros FxPlug com `uuid` (ex. Custom LUT `14B39AEF-607D-42DF-98DD-DB3DD345E925`, LUT File `A47270A6-...`, Color Curves `920273EF-...`) | - | sim (no FCPXML) | ⏳ parâmetros exatos: copiar de uma exportação |
| 10 | Biblioteca no disco (`.fcpbundle`, eventos `CurrentVersion.fcpevent`) | banco do projeto | talvez | não (nunca escrever) | ⏳ (nenhuma biblioteca existe ainda) |

## O que já se sabe (resultados)
- **AppleScript é só leitura** e só do modelo biblioteca/evento/projeto/sequência: não há clipes, cabeçote nem edição.
- **A ponte das extensões não é mágica**: o modelo da biblioteca vai por Apple Event `get` (o mesmo do AppleScript);
  a timeline (cabeçote, sequência ativa) vai por XPC privado da extensão.
- **Importar FCPXML sem biblioteca aberta** abre o painel "Which library do you want to import ... into?" (não dá
  para clicar por automação): a primeira biblioteca do Gab é criada uma vez pelo usuário; depois ela fica aberta.
- **Comandos internos** têm nome e seletor fixos (ex. `ExportXML`, `ImportXML`, `CreateCaptions`, `EnhanceAudio`,
  `BladeAtPlayhead`, `PasteAsConnected`, `RenderAll`): é a "API de ações" do Final Cut, acionável por menu (AX) ou atalho.

## Testes feitos (13/10/2026)
- ✅ **Vídeo do Vorcaro reconstruído no Final Cut** a partir da timeline do DaVinci ("01 O Estrangeiro"): 24 takes com
  gaps na linha principal, 18 motions em 2 camadas, 44 áudios (narração +5 dB, música -5,3 dB, 42 SFX em 4 camadas),
  58 legendas; o AppleScript confirma 1512/24 = 63,0 s, igual ao DaVinci.
- ✅ Título/legenda: o Final Cut mede **tamanho e posição** numa escala de 1080 de altura; no vertical 1080x1920
  converter px reais x1080/1920 (o gerador faz). Legenda do cliente: Playfair Display, minúsculas, y -490 px.
- ✅/⚠️ Import com `<library location=...>` da biblioteca aberta: às vezes entra direto, às vezes pergunta (parece
  depender do Final Cut estar ativo/na mesa atual); a janela de escolha é do Final Cut quando ele está na mesa atual.
- ✅ Teste 2 (AppleScript lê projeto e duração) para conferir o import.

## Testes a fazer (nesta ordem) e registrar aqui
1. ⏳ Com a biblioteca "Gab teste" aberta: `open -a` de um FCPXML vai direto para ela, sem perguntar?
2. ⏳ AppleScript lê o projeto importado (nome, duração) = conferência pós-import.
3. ⏳ Área de transferência: pôr um trecho FCPXML (`com.apple.finalcutpro.xml.v1-11`) e acionar Edit > Paste /
   `PasteAsConnected` com a timeline aberta: entra no cabeçote? (se sim, é o equivalente ao `AppendToTimeline` do DaVinci)
4. ⏳ Comandos por menu (AX): `Blade`, `Next Edit`, `Render All`, `Enhance Audio`, `Create Captions` (transcrição nativa).
5. ⏳ Export XML: o painel de salvar é de outro processo; achar caminho sem painel (preferência, compartilhamento
   "Export File" com destino fixo, ou ler a biblioteca no disco).
6. ⏳ Custom LUT: aplicar uma vez e exportar para copiar o formato do parâmetro do arquivo de LUT.
7. ⏳ Notificações da timeline: escutar `com.apple.finalcut.timelineNotification` (NSDistributedNotificationCenter).
8. 🔒 Workflow Extension mínima (Xcode): cabeçote e sequência ativa ao vivo + servidor local (como a Gab Ponte do Premiere).
