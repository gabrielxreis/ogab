# DaVinci Resolve: tudo que dá para fazer no Color pela API

Engenharia reversa feita em 29/10/2026 no DaVinci Resolve **Studio 21.1.1.10** (Mac), testando cada comando num projeto descartável ("Gab Teste Color API 172543"), nunca em projeto de cliente.

Fontes:
1. Documentação oficial: `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/` (README.md, DaVinciResolveScript.pyi, CHANGELOG.md). Na 21.1 o README ficou curto e a referência completa está no `.pyi`.
2. `dir()` de cada objeto vivo (Resolve, Project, Timeline, TimelineItem, Graph, ColorGroup, Gallery, GalleryStillAlbum).
3. Nomes de método no binário `DaVinci Resolve.app/Contents/MacOS/Resolve`: estão na tabela de exports como `cl_<Classe>ScriptProxy<Metodo>4FuncERNS_10ScriptArgs...` (os nomes não aparecem no `strings` comum porque ficam picotados na árvore de exports; dá para achar com busca binária por `4FuncERNS_10ScriptArgsEPNS_12ScriptSymbolEb`).

Legenda de status:
- **DOC ok**: documentado e funcionou no teste.
- **DOC falha**: documentado, mas não funcionou (ou só funciona em condição específica).
- **ESCONDIDO ok**: não está no README/.pyi nem no `dir()`, mas existe e respondeu.
- **ESCONDIDO sem efeito**: existe no binário (o atributo vem como `Remote Function`), mas devolve `None` e não muda nada que a API consiga ler.
- **LEGADO ok**: forma antiga (deprecated) que ainda funciona.

Conexão (a mesma do `resolve_lib.py`): `r = dvr.scriptapp("Resolve")`; `p = r.GetProjectManager().GetCurrentProject()`; `tl = p.GetCurrentTimeline()`; `it = tl.GetItemListInTrack("video", 1)[0]`.

---

## Resumo: o que dá e o que não dá sem clicar

**Dá para fazer pela API:**
- Configurar o Color Management do projeto (DaVinci YRGB, RCM v2 com espaços separados ou juntos, ACEScc/ACEScct com IDT, ODT e gamut compress) e o espaço de cor por timeline e por clipe.
- Pôr LUT em qualquer nó que já existe: clipe, camada 2 do clipe, pre-clip e post-clip do grupo.
- Aplicar CDL (slope, offset, power, saturação) num nó.
- Ligar e desligar nó, ler as ferramentas usadas em cada nó, ligar o cache do nó.
- Aplicar grade inteira (PowerGrade/still) de um `.drx`: é o jeito de levar **vários nós, rótulos, Resolve FX, máscaras e curvas** para o clipe.
- Copiar a grade de um clipe para outros, resetar a grade.
- Versões de cor (criar, carregar, renomear, apagar, local e remota).
- Grupos de cor (criar, pôr e tirar clipe, LUT no pre/post-clip, renomear, apagar).
- Galeria: pegar still de um clipe ou de todos, rotular, exportar (imagem + `.drx`), importar, apagar, criar álbum de stills e de PowerGrade.
- Exportar a grade do clipe como LUT `.cube` (17, 33, 65 pontos) ou VLUT.
- Conferir o resultado: exportar o quadro atual já com a cor (PNG/JPG em resolução cheia) ou pegar a miniatura.
- Exportar EDL com CDL (ASC_SOP), ALE com CDL e DRT.
- Estabilizar o clipe.

**Não dá (nenhum comando, nem escondido):**
- Criar ou apagar nó (serial, paralelo, layer, splitter), ligar nós, mudar a ordem.
- Escrever rótulo de nó (só lê com `GetNodeLabel`) ou cor do nó (só reseta).
- Mexer em rodas, curvas, HDR wheels, qualifier, power window, tracker, blur, key etc. (o `SetCDL` é o único controle de cor primária).
- Pôr Resolve FX ou OFX num nó (só lê o nome com `GetToolsInNode`).
- Magic Mask a partir do zero (`CreateMagicMask` falha num clipe sem nó de Magic Mask).
- Apagar álbum da galeria; aplicar `.drx` no pre/post-clip do grupo; LUT no grafo da timeline.
- Cache de cor do clipe (`SetColorOutputCache` voltou False).

**O caminho para o que não tem comando:** montar o look uma vez no Resolve (nós com rótulo, Resolve FX, máscaras), salvar como PowerGrade/`.drx` e aplicar pela API com `GetNodeGraph().ApplyGradeFromDRX(caminho, 0)`. O `.drx` também pode ser **editado por script** (ver a seção DRX): o Resolve aceita o arquivo alterado.

---

## 1. Color Management do projeto (Project.SetSettings)

`p.SetSettings({chave: valor})` -> Bool. Todo valor é string e precisa ser **o texto exato do menu**. Valor errado devolve False sem erro. Status: **DOC ok** para todas as chaves abaixo.

| Chave | Valores testados que funcionam | Observação |
|---|---|---|
| `colorScienceMode` | `davinciYRGB`, `davinciYRGBColorManagedv2`, `acescct` (também `davinciYRGBColorManaged`, `acescc` no .pyi) | |
| `isAutoColorManage` | `"0"` / `"1"` | `1` = RCM automático |
| `rcmPresetMode` | `Custom` (com auto=0); `SDR`/`HDR` com auto=1 | |
| `separateColorSpaceAndGamma` | `"0"` / `"1"` | muda o formato dos valores abaixo |
| `colorSpaceInput` / `colorSpaceOutput` (separate=0) | `Rec.709 Gamma 2.4` | `Rec.709` sozinho falha |
| `colorSpaceTimeline` (separate=0) | `DaVinci WG/Intermediate`, `Rec.709 (Scene)` | `DaVinci Wide Gamut` falha |
| `colorSpaceInput` / `colorSpaceOutput` (separate=1) | `Rec.709` | |
| `colorSpaceInputGamma` / `colorSpaceOutputGamma` (separate=1) | `Gamma 2.4` | |
| `colorSpaceTimeline` (separate=1) | `DaVinci WG`, `Rec.2020` | |
| `colorSpaceTimelineGamma` (separate=1) | `DaVinci Intermediate` | |
| `colorSpaceOutputToneMapping` | `None` (.pyi: `SDR 100`, `HDR 1000`...) | |
| `colorSpaceOutputGamutMapping` | `None` (.pyi: `Saturation Mapping`, `RED IPP2 Gamut Mapping`) | |
| `colorAcesIDT` (com ACES) | `No Input Transform`, `Apple Log 2 - CSC`, `Sony SLog3 SGamut3Cine - CSC`, `Blackmagic Design Film Gen 5`, `Apple Log` | `Rec.709` e `sRGB` falham |
| `colorAcesODT` (com ACES) | `No Output Transform`, `Rec.709 BT.1886`, `sRGB Piecewise`, `P3-D65` | `Rec.709` falha; a lista completa está no binário perto de `P3-D65` |
| `colorAcesGamutCompressType` | `None`, `ACES reference gamut compress` | `Reference Gamut Compress` falha |
| `nodeStackLayers` | `"2"` | libera `GetNodeGraph(2)` |
| `colorVersion1Name` ... `colorVersion10Name` | qualquer texto | nomes das versões rápidas |
| `colorGalleryStillsLocation` | caminho | pasta dos stills (padrão `~/Movies/.gallery`) |

Dica: para descobrir o texto exato de qualquer opção, mudar no menu do Resolve e ler `p.GetSettings()` antes e depois.

**Por timeline:** `tl.SetSettings({"useCustomSettings": "1"})` e depois `tl.SetSettings({"colorSpaceTimeline": "Rec.709"})` -> True (**DOC ok**).

**Por clipe (Input Color Space):** `mpi.SetClipProperty("Input Color Space", "Rec.709")` -> True e lê de volta `Rec.709 (Scene)` (**DOC ok**). `"Apple Log"` falhou (nome tem que ser o do menu do clipe). `SetClipProperty("Input LUT", ...)` -> False (**DOC falha**: não há como pôr Input LUT no clipe pela API).

`p.RefreshLUTList()` -> True (**DOC ok**). Rodar depois de copiar LUT nova para a pasta de LUTs.

---

## 2. Nós (Graph)

Pegar o grafo: `g = it.GetNodeGraph()` (camada 1) ou `it.GetNodeGraph(2)` (camada 2, precisa `nodeStackLayers >= 2`). **Sempre pegar o grafo de novo a cada chamada** (grafo velho já derrubou o Resolve, ver `aplicar_grade` no resolve_lib.py). Índice de nó começa em 1. Precisa estar na página Color (`r.OpenPage("color")`) para as operações de grade.

| Comando | Retorno | Status | Notas do teste |
|---|---|---|---|
| `g.GetNumNodes()` | int | DOC ok | clipe novo = 1 |
| `g.SetLUT(n, "Pasta/arquivo.cube")` | Bool | DOC ok | caminho relativo à pasta de LUTs ou absoluto; o arquivo tem que existir (nome errado = False). Ex.: `"Blackmagic Design/Blackmagic 4.6K Film to Video v4.cube"` |
| `g.GetLUT(n)` | str | DOC ok | devolve o caminho relativo |
| `g.GetNodeLabel(n)` | str | DOC ok | só leitura; `""` sem rótulo. **Não existe SetNodeLabel** |
| `g.GetToolsInNode(n)` | list[str] / None | DOC ok | ex.: `['LUT: Blackmagic 4.6K Film to Video v4', 'Primary Balance', 'Saturation, Hue & Lum Mix']`; nó vazio = None. Serve para ler se o nó tem Resolve FX, máscara etc. |
| `g.SetNodeEnabled(n, False/True)` | Bool | DOC ok | liga/desliga o nó |
| `g.GetNodeCacheMode(n)` / `g.SetNodeCacheMode(n, r.CACHE_ENABLED)` | int / Bool | DOC ok | `CACHE_AUTO_ENABLED=-1`, `CACHE_DISABLED=0`, `CACHE_ENABLED=1` |
| `g.ApplyGradeFromDRX(caminho, modo, todasCamadas=False)` | Bool | DOC ok | modo 0 = sem keyframes, 1 = alinhado pelo TC de origem, 2 = pelo primeiro quadro. `True` no 3º argumento aplica em todas as camadas |
| `g.ResetAllGrades()` | Bool | DOC ok | depois: `GetToolsInNode(1)` = None, LUT some |
| `g.ApplyArriCdlLut()` | Bool | DOC ok (sem efeito em clipe não ARRI) | devolveu True num ProRes comum; serve para clipe ARRI com CDL/LUT embutidos |
| `g.SetNodeActive(...)` | None | ESCONDIDO sem efeito | testado com `(1)`, `(1, True)`, `(True)`, `()` |
| `g.SetNodeLocked(...)` | None | ESCONDIDO sem efeito | nome deduzido do binário (`...Locked`); mesmo resultado |
| `g.ResetNode(n)` | None | ESCONDIDO sem efeito | a LUT e as ferramentas continuaram no nó |

Os mesmos `SetNodeActive`, `SetNodeLocked` e `ResetNode` existem no **TimelineItem** (também sem efeito).

**Legado no TimelineItem** (forma antiga, ainda funciona, LEGADO ok): `it.GetNumNodes()`, `it.SetLUT(n, lut)`, `it.GetLUT(n)`, `it.GetNodeLabel(n)`.

---

## 3. CDL

`it.SetCDL({"NodeIndex": "1", "Slope": "1.1 1.0 0.9", "Offset": "0.01 0 -0.01", "Power": "1 1 1", "Saturation": "1.2"})` -> True (**DOC ok**).
- Valores RGB vão como texto separado por espaço.
- Depois do SetCDL o nó mostra `Primary Balance` e `Saturation, Hue & Lum Mix` em `GetToolsInNode`.
- É o **único controle de cor primária** pela API. Não existe Lift/Gamma/Gain, curva ou contraste.
- O Graph do grupo/timeline não tem `SetCDL` (só o TimelineItem).

Exportar o CDL da timeline: `tl.Export(arq.edl, r.EXPORT_EDL, r.EXPORT_CDL)` -> True, gera `*ASC_SOP (1.100000 1.000000 0.900000)...` por evento (**DOC ok**). `tl.Export(arq.ale, r.EXPORT_ALE_CDL, r.EXPORT_NONE)` -> True (**DOC ok**).

---

## 4. Copiar, resetar e exportar grade

| Comando | Status | Notas |
|---|---|---|
| `itA.CopyGrades([itB, itC])` | DOC ok | copia a camada ativa do A para os outros; conferido: C ficou com as mesmas ferramentas |
| `it.GetNodeGraph().ResetAllGrades()` | DOC ok | |
| `it.ResetAllNodeColors()` | DOC ok | só a cor de identificação dos nós |
| `it.ExportLUT(r.EXPORT_LUT_33PTCUBE, "/caminho/grade.cube")` | DOC ok | 17PT (115 KB), 33PT (549 KB), 65PT (6,6 MB), `EXPORT_LUT_PANASONICVLUT` (.vlt). Bom para levar o look para fora (Premiere, CapCut, câmera) |
| `it.SetColorOutputCache(True)` / `it.GetIsColorOutputCacheEnabled()` | DOC falha | devolveu False / 0 no teste |

---

## 5. Versões de cor (TimelineItem)

`versionType`: 0 = local, 1 = remota. Tudo **DOC ok**:

| Comando | Resultado no teste |
|---|---|
| `it.GetCurrentVersion()` | `{'versionName': 'Version 1', 'versionType': 0}` |
| `it.GetVersionNameList(0)` | `['Version 1']` |
| `it.AddVersion("v2", 0)` | True. **Já troca para a versão nova**, e ela nasce com a grade atual (copiada) |
| `it.RenameVersionByName("v2", "quente", 0)` | True |
| `it.LoadVersionByName("Version 1", 0)` | True |
| `it.DeleteVersionByName("quente", 0)` | True (não apagar a versão ativa) |
| `it.AddVersion("remota1", 1)` / `GetVersionNameList(1)` | True / `['Version 1', 'remota1']` |
| `it.GetVersionNames(0)` | LEGADO ok: `{1: 'Version 1'}` |
| `it.ResetCurrentVersion()` | ESCONDIDO sem efeito (None, grade continuou) |

Uso no Gab: criar versões `"neutro"`, `"quente"`, `"frio"` com looks diferentes para o cliente escolher, e carregar a escolhida.

---

## 6. Grupos de cor

Tudo **DOC ok**, menos onde indicado:

| Comando | Notas |
|---|---|
| `grp = p.AddColorGroup("Nome")` | nome único |
| `p.GetColorGroupsList()` | lista de ColorGroup |
| `it.AssignToColorGroup(grp)` / `it.GetColorGroup()` / `it.RemoveFromColorGroup()` | |
| `grp.GetName()` / `grp.SetName("novo")` | |
| `grp.GetClipsInTimeline(tl)` | lista de TimelineItem |
| `grp.GetPreClipNodeGraph()` / `grp.GetPostClipNodeGraph()` | Graph com 1 nó; `SetLUT`/`GetLUT` funcionam |
| `grp.GetPreClipNodeGraph().ApplyGradeFromDRX(...)` | **DOC falha**: False (confirma a nota do `aplicar_grade`) |
| `p.DeleteColorGroup(grp)` | clipes voltam a ficar sem grupo |

Uso no Gab: grupo "iPhone" com LUT de conversão no pre-clip, e o look geral no post-clip.

---

## 7. Grafo da timeline

`tl.GetNodeGraph()` devolve um Graph (**DOC**), mas no teste `GetNumNodes()` = 0 e `SetLUT(1, ...)` = False (**DOC falha**). `ApplyGradeFromDRX` devolveu True, mas sem nós para conferir. Na prática: não usar; para look geral, usar grupo (post-clip) ou aplicar em todos os clipes.

---

## 8. Galeria, stills e PowerGrades

`g = p.GetGallery()` (ou `r.GetGallery()`). Tudo **DOC ok**:

| Comando | Notas |
|---|---|
| `g.GetCurrentStillAlbum()` / `g.SetCurrentStillAlbum(album)` | o still pego vai para o **álbum atual**, inclusive se ele for de PowerGrade |
| `g.GetAlbumName(album)` / `g.SetAlbumName(album, "nome")` | |
| `g.GetGalleryStillAlbums()` / `g.GetGalleryPowerGradeAlbums()` | |
| `g.CreateGalleryStillAlbum()` / `g.CreateGalleryPowerGradeAlbum()` | o de PowerGrade nasce como "PowerGrade N"; **não existe comando para apagar álbum** |
| `tl.GrabStill()` | still do clipe no playhead (página Color) |
| `tl.GrabAllStills(1 ou 2)` | um still por clipe: 1 = primeiro quadro, 2 = meio |
| `album.GetStills()` / `album.GetLabel(st)` / `album.SetLabel(st, "look gab")` | |
| `album.ExportStills([st], pasta, "prefixo", formato)` | formatos que funcionaram: `dpx`, `cin`, `tif`, `jpg`, `png`, `ppm`, `bmp`, `xpm`, `drx`. **Sempre grava o `.drx` junto** (nome `prefixo_1.1.1.drx`) |
| `album.ImportStills([arquivo.drx])` | |
| `album.DeleteStills([st])` | |

**ATENÇÃO: os álbuns de PowerGrade são globais** (aparecem em todos os projetos do banco). No teste, `GetGalleryPowerGradeAlbums()[0]` era o álbum "LUT DO GAB" do Gabriel, e não um álbum novo: renomear ou importar "no primeiro álbum" mexe no álbum real. Regra: sempre achar o álbum **pelo nome** e nunca mexer em álbum de PowerGrade que o Gab não criou. Observação: logo depois de abrir o Resolve, no "Untitled Project", `GetGalleryPowerGradeAlbums()` voltou vazio mesmo indo à página Color; num projeto salvo a lista apareceu inteira. Com a lista vazia, não concluir que não há PowerGrades.

Fluxo para salvar um look e reaproveitar em outro projeto: `tl.GrabStill()` -> `album.ExportStills([st], pasta, "look", "drx")` -> no outro projeto, `it.GetNodeGraph().ApplyGradeFromDRX(pasta + "/look_1.1.1.drx", 0)`.

---

## 9. Conferir o quadro (render do frame)

| Comando | Status | Notas |
|---|---|---|
| `tl.SetCurrentTimecode("01:00:05:00")` | DOC ok | mover o playhead |
| `tl.GetCurrentVideoItem()` | DOC ok | qual clipe está no playhead |
| `p.ExportCurrentFrameAsStill("/caminho/quadro.png")` | DOC ok | quadro atual **já com a cor**, resolução cheia (PNG 1080p = 6 MB; `.jpg` também funciona). É o jeito de o Gab "ver" a grade e comparar antes/depois |
| `tl.GetCurrentClipThumbnailImage()` | DOC ok | `{'width': 576, 'height': 324, 'format': 'RGB 8 bit', 'data': base64}`: rápido, sem gravar arquivo |

---

## 10. IA, estabilização e outros do Color

| Comando | Status | Notas |
|---|---|---|
| `it.Stabilize()` | DOC ok | True |
| `it.GetLastStabilizeFPS()` | ESCONDIDO ok | `150.23` (velocidade da última estabilização) |
| `it.CreateMagicMask("F"/"B"/"BI")` | DOC falha | False nos dois sentidos: precisa de um nó com Magic Mask já criado (o que não dá pela API). Caminho: `.drx` com nó de Magic Mask, aplicar e depois `CreateMagicMask` / `RegenerateMagicMask` (não testado) |
| `it.GetLastMagicMaskFPS()` | ESCONDIDO ok | `0.00` sem máscara |
| `it.SmartReframe()` | DOC (não testado aqui) | |
| `r.ValidateDCTL(caminho)` / `r.EncryptDCTL(...)` | DOC ok | valida DCTL; com arquivo inválido devolve o texto do erro |
| `r.GetKeyframeMode()` / `r.SetKeyframeMode(r.KEYFRAME_MODE_COLOR)` | DOC | `KEYFRAME_MODE_COLOR = 1` |
| `r.GetLicenseType()` | ESCONDIDO ok | `1` (Studio) |
| `r.IsStudio()` | DOC ok | True |
| `p.GetTimelineFromUniqueId(id)`, `p.GetPlaybackSpeed()`, `r.GetSourceViewerMode()`, `r.GetShowAllVideoFrames()` | ESCONDIDO sem efeito | devolvem None |

Também existem no binário (fora do Color, não testados): `r.DeactivateLicense` (não chamar), `r._ExportTableToString`, `r._ImportTableFromString`, `r.TriggerCtrKTest`, `MediaStorage.RevealInStorage`, `MediaStorage.AddClipMattesToMediaPool`, `AddTimelineMattesToMediaPool`, `Folder.GetIsFolderStale` e vários `GetLast...Speed`.

---

## 11. DRX por dentro (editar grade sem clicar)

O `.drx` é XML (`<Gallery::GyStill>`), com a grade em `<pClipFullVer><ListMgt::LmVersion><Body>`:
- `Body` = hex de: 1 byte `0x81` + um quadro **zstd** (`28 b5 2f fd`).
- Descomprimido, é **protobuf** sem schema público. Os parâmetros aparecem como pares `id` + float32 (ex.: `0x3f99999a` = 1.2).
- Teste de ida e volta: descomprimir, trocar um float, recomprimir com `zstd -19`, pôr `0x81` na frente, voltar para hex, gravar o .drx e aplicar com `ApplyGradeFromDRX` -> **True e a imagem mudou** (quadro exportado conferido). O campo trocado não era a saturação, então falta mapear qual id é qual controle.

```python
import re, binascii, subprocess
t = open("look.drx").read()
corpo = re.search(r"<Body>([0-9a-f]+)</Body>", t).group(1)
raw = binascii.unhexlify(corpo); prefixo, z = raw[:1], raw[1:]
pb = subprocess.run(["zstd", "-d", "-c"], input=z, capture_output=True).stdout
# ... editar pb (floats em little-endian) ...
z2 = subprocess.run(["zstd", "-c", "-19"], input=pb, capture_output=True).stdout
open("look_editado.drx", "w").write(t.replace(corpo, binascii.hexlify(prefixo + z2).decode(), 1))
```

Próximo passo, se quiser abrir esse caminho: exportar vários `.drx` mudando **um** controle por vez no Resolve (Lift, Gamma, Gain, Contraste, Sat, Temperatura) e comparar os protobufs para montar o mapa id -> controle. Com o mapa, o Gab poderia gerar grades com valores exatos (e até vários nós) sem clicar.

---

## Armadilhas encontradas

- `SetSettings` devolve False sem erro quando o texto do valor não é exatamente o do menu.
- `SetLUT` devolve False se o arquivo não existe. Conferir com `os.path.exists` na pasta de LUTs (`/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/`) e rodar `RefreshLUTList()`.
- `ImportMedia` de arquivo em `/private/tmp` voltou None; de `~/Movies` funcionou.
- Álbum de PowerGrade é global: achar sempre pelo nome (ver seção 8).
- Métodos escondidos que devolvem `None` não dão erro: não confiar neles.
- `dir()` mostra só o que é público. Nome inventado vira atributo `None`; nome escondido real vira `Remote Function`.
