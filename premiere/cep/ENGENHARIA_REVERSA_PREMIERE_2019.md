# Premiere Pro 2019: engenharia reversa (o Gab editando sem olhar a tela)

Premiere Pro CC 2019 **13.1.5** (build 47), Windows 10, estudado em 26/10/2026 numa máquina de usuário do /ogab.
Objetivo: fazer no Premiere antigo o que o `premiere/premiere_lib.py` já faz no 26 (UXP), sem screenshot e sem clique,
para cobrir quem não tem o Premiere novo.

Legenda: ✅ testado e funciona · ❌ testado e não funciona · ⏳ falta testar.

## Resumo para quem tem pressa

- O 2019 **não tem UXP**. Tem **CEP + ExtendScript**: o mesmo sistema da ponte do After Effects
  (`aftereffects/`, `com.gabrielxreis.ogab.aeponte`). A solução é a mesma: uma extensão CEP invisível com servidor
  HTTP local que recebe ExtendScript e devolve JSON. ✅
- Protótipo completo e testado nesta pasta: `plugin/` (extensão), `jsx/gab_ppro.jsx` (funções de apoio),
  `premiere2019_lib.py` (mesma interface do `premiere_lib.py`), `instalar.ps1`, `teste/` (cada experimento + reflexão).
- Números medidos: **6 ms** por comando, colocar um clipe **50 a 250 ms**, timeline de Reels inteira (sequência
  1080x1920 30 fps, bruto, 3 takes só vídeo escalados, música a -10 dB, motion, 2 marcadores, salvar) **em 1,85 s
  num comando só**, render H.264 1080x1920 de 20 s **em 15 s, síncrono, sem Media Encoder**.
- Cuidado com a promessa "aprendeu no 2019, funciona em qualquer Premiere". **A ponte CEP serve do 2018 (12.x, CEP 8)
  até o 25.x**, mas a API muda entre versões. O 2019 não tem várias coisas que o 2020+ tem, e o 26 é UXP (já coberto
  pelo `premiere_lib.py`). A Adobe está aposentando CEP/ExtendScript no Premiere: confirmar no calendário dela até
  qual versão a ponte CEP abre. O caminho é ter as duas pontes e escolher pela versão (ver "Integração").

## Mapa das superfícies

| # | Superfície | O que expõe | Estado |
|---|---|---|---|
| 1 | DOM oficial (`ScriptLayerPPro.dll`) | projeto, bins, importar, sequência, `overwriteClip`/`insertClip`, in/out, subclipe, componentes e keyframes, marcadores, `importMGT`, `exportAsMediaDirect`, `openFCPXML`, `exportAsFinalCutProXML` | ✅ |
| 2 | QE DOM, sem documentação (`ScriptLayerPProQE.dll`, `app.enableQE()`) | `newProject`, `newSequence` (sem diálogo), `addTracks`, `razor`, `lift`/`extract`, `addVideoEffect`, `addTransition`, `setSpeed`, `exportFramePNG`, `undo`/`redo`, `getModalWindowID`, `executeConsoleCommand` | ✅ (parcial, ver tabela) |
| 3 | Reflexão do ExtendScript (`obj.reflect.methods/properties`) | assinatura de cada método do DOM (com tipos); na QE só os nomes | ✅ `teste/reflexao_13.1.5.json` |
| 4 | Strings das DLLs | lista bruta de métodos: `teste/dll_metodos_QE_13.1.5.txt`, `teste/dll_metodos_DOM_13.1.5.txt` | ✅ |
| 5 | Scripts de inicialização (`<instalação>\Scripts\Startup\*.jsx`) | eventos `onActiveSequenceChanged`, `onEncoderJobComplete`, `QESequence.onEncodeFinished` etc. Precisa de admin para escrever lá: não usar | lido |
| 6 | REA (`rea-agents` 6.7.0) | análise nativa no Windows exige Ghidra (`GHIDRA_INSTALL_DIR`); Hopper não roda em win32, Kuna só ELF/Mach-O. A reflexão (3) deu mais que o desmonte daria | ❌ sem Ghidra |

## Como a ponte funciona

```
Python (premiere2019_lib.py)   --POST /jsx-->  extensão CEP invisível (Node, 127.0.0.1:8767)  --evalScript-->  motor ExtendScript do Premiere
                               <---- JSON ----                                                <-- string --
```

- `plugin/CSXS/manifest.xml`: host `PPRO [12.0,99.9]`, CSXS 8.0, `--enable-nodejs --mixed-context`. Duas entradas
  com o mesmo código: um "servidor" `Custom` invisível com `StartOn` (✅ **iniciou sozinho com o Premiere**) e um
  painel de reserva (Window > Extensions > Gab Ponte). A segunda só não pega a porta.
- `plugin/main.js`: o mesmo `main.js` do AE (fila de um script por vez), sem a checagem do aerender.
- Envelope de cada chamada (`_ENVELOPE` no Python): carrega o `gab_ppro.jsx` só quando o arquivo muda (mtime), roda o
  código dentro de `eval()` e devolve `{ok, resultado|erro}` com `GAB.json` (o ES3 não tem `JSON`).
- Extensão sem assinatura: precisa de `PlayerDebugMode = "1"` em `HKCU\Software\Adobe\CSXS.<n>` (8 = 2018,
  9 = 2019 ... 12 = 2024/25). Nesta máquina já estava ligado. O `instalar.ps1` liga sozinho, mas o modo automático do
  Claude Code **barrou** essa escrita no registro ("Security Weaken"): o instalador do /ogab deve rodar como passo do
  usuário (como o `windows\install.ps1`), não por dentro de uma sessão do Claude.

## Armadilhas encontradas (todas testadas no 13.1.5)

1. **Erro de sintaxe trava o Premiere.** Erro de sintaxe no topo de um `evalScript` abre a janela modal
   "Run Script Error: Syntax error" e o motor para até alguém clicar OK (a chamada fica pendurada, e o Node fecha a
   conexão em 2 min). Dentro de `eval()` vira exceção comum. Por isso o envelope põe tudo em `eval()`. ✅
2. **O ExtendScript não aceita regex com `\u0000` ou `U+2028`** ("Syntax error"). O `GAB.json` escapa por laço. ✅
3. **Caractere U+2028/U+2029 dentro de comentário quebra o arquivo**, porque o JS trata como fim de linha. ✅
4. `$.evalFile` dentro de função deixa o `var GAB` local: usar `$.global.GAB`. ✅
5. **Sem projeto aberto** (tela Home), ler `app.project.*` gera exceção nativa que **escapa do try/catch** (a resposta
   chega como `"Uncaught exception "`). Guarda: `app.isDocumentOpen()`. ✅
6. O 13.x **não tem** `app.newProject`, `createNewSequenceFromClips` nem `createCaptionTrack`. O `createNewSequence`
   do DOM abre diálogo (proibido: trava). Usar a QE: `qe.newProject(caminho)` só **cria** o arquivo (abrir depois com
   `app.openDocument`) e `qe.project.newSequence(nome, preset.sqpreset)`. ✅
7. **A QE só aceita caminho com `\`** no Windows: com `/`, o `newSequence` devolve false sem erro. `app.path` já termina
   em `\` (`GAB.instalacao()` cuida disso). ✅
8. O preset "DSLR 1080p30" é **29,97**. fps exato: `settings.videoFrameRate = Time com ticks = 254016000000 / fps` e
   `setSettings`. O tamanho vai em `videoFrameWidth/Height`. ✅
9. `Sequence.overwriteClip(item, t, v, -1)` dá **"Bad argument"**: não existe "sem áudio" por índice -1.
   `Track.overwriteClip` numa trilha de vídeo **leva o áudio para a trilha de áudio de mesmo índice** (o take na V2
   pôs áudio na A2). Só vídeo = subclipe com `createSubClip(nome, 0, fim, 0, takeVideo=1, takeAudio=0)`. ✅
10. **O subclipe e o overwrite herdam o in/out que estiver marcado no item.** Sempre `clearInPoint/clearOutPoint(4)`
    antes de marcar e depois de colocar (um teste anterior que falhou deixou 2–3,5 s marcado, e o subclipe nasceu
    com 3,5 s). ✅
11. **Volume: a escala do 13.x é outra.** Medido com render WAV pelo Premiere e `volumedetect` do ffmpeg:
    `Level = 0,5 × 10^(dB/20)`. 0,5 = 0 dB (padrão do clipe), 1,0 = +6 dB (teto; 2,0 vira 1,0), 0,1778 = -9 dB.
    O `premiere_lib.py` do 26 usa 0,1778 = 0 dB e teto +15 dB. **A mesma fórmula no 2019 deixa todo ganho 9 dB baixo.**
    Clipe mono numa sequência estéreo cai -3 dB (lei de pan). Keyframes de fade vão em **tempo da fonte**
    (`inPoint + t`). ✅ Clipe **estéreo** (`teste/t15_volume_estereo.py`): padrão também 0,5 = 0 dB, sem a perda de
    pan (saída = fonte); -10 dB pedido saiu -10,005 dB no render. **Fades conferidos no WAV renderizado**: sobe do
    silêncio a -10 dB em 0,5 s e desce ao silêncio no fim, também com ponto de entrada (de=2 s). A rampa é linear na
    amplitude (no meio do fade: -6 dB abaixo do alvo). ✅
12. **A QE conta os vãos como itens da trilha** (`type "Empty"`): `getItemAt(0)` pegou o vão antes do take, e o
    `addVideoEffect` "não existia". Filtrar `type === "Clip"`. ✅
13. **Objeto da QE fica inválido depois de qualquer edição** ("Object is invalid"): buscar de novo a cada operação
    (`GAB.qeClipe`). ✅
14. **`setSpeed` recebe multiplicador**, não porcentagem: 200 virou 1 quadro (3,5 s / 200). 2 = 200%. ✅
15. `razor` da QE corta só a trilha pedida (V1 sem cortar A1) e usa timecode `"HH;MM;SS;FF"`. ✅
16. Legenda: SRT importado vira item que se coloca numa **trilha de vídeo** (o 13.x não cria trilha de legenda pela
    API). **O item começa na primeira fala**: colocado em 0, adianta tudo; colocar no início da 1ª legenda. Acentos ✅.
    O 13.x trata o SRT como **"Open Captions"**. Pela QE (`qeItem.clip.getCaptioningStreamAt(0).getCaptionAt(i)`) dá
    para ler e mudar posição X/Y (em pixels; `setPositionY` muda também a âncora), âncora e alinhamento, e o texto
    (`getParagraphAt(i).text`). As cores são nomes de uma lista fixa ("White (Bright)"); `setTextColor(número)` dá
    "Bad argument list". **Fonte e tamanho não existem na API.** Por isso o estilo GAB USA vai por títulos (armadilha 20). ✅
17. **MOGRT do Gab (`premiere/assets/mogrt/*.mogrt`, feitos para o 26) travou o `importMGT` por 82 s** e terminou em
    exceção nativa. Não oferecer esses MOGRTs no 2019. MOGRT nativo do 2019 (`Essential Graphics\Basic Title.mogrt`)
    entra (✅), mas `getMGTComponent()` volta null. O texto fica no componente "Text" (`AE.ADBE Text`) >
    `properties[0]` "Source Text": **4 caracteres de prefixo (o 1º vale 2 × tamanho do JSON, os outros 3 são \0) + JSON
    `mTextParam`**. Reescrever esse valor funciona (✅ `P.titulo`): `mStyleSheet.mText` (texto; quebra de linha =
    `\r`), `mFontName` (nome PostScript, ex. `Poppins-Bold`), `mFontSize`, `mFillColor` (**0xRRGGBB**), sombra
    (`mShadowVisible/Opacity/Offset/Blur/Angle/Color`), `mAlignment` (2 = centro). `properties[2]` = Position
    normalizada (0..1), que marca a **linha de base** da 1ª linha. A duração se muda escrevendo `trackItem.end`. ✅
20. **Legenda GAB USA no 2019 = um título nativo por fala** (`P.legenda_gab`). Calibrado contra a medida do DaVinci
    (`legenda_baixa.py`: "NÃO FOI O MOVIMENTO" com 414 px no 1080×1920): `mFontSize` **63,53** dá 414 px exatos. Centro
    do texto em Y 724 contado de baixo: linha de base = `1920 - 724 + 0,26 × tamanho`; com N linhas, sobe
    `(N-1) × 0,614 × tamanho / 2` (entrelinha medida: 39 px). Medido no quadro exportado: centro em 1196 px (1 linha) e
    1197,5 px (2 linhas), alvo 1196. 3 falas em 0,78 s (duas chamadas: importa todas, depois escreve todas). ✅
21. **LUT: o 13.x NÃO lê `%APPDATA%\Adobe\Common\LUTs`** (a pasta que o `premiere/instalar.ps1` usa). A calibração
    testou todos os índices do Look e nenhum bateu (melhor diferença 12,95). Com os LUTs da própria instalação ela acha
    na hora: "Kodak 5218 Kodak 2383 (by Adobe)" = índice 11 e "Fuji F125 Kodak 2393 (by Adobe)" = 7, com diferença
    < 1,5 (~5 s cada). O LUT do Gab precisa ir para `<Premiere>\Lumetri\LUTs\Creative` e o Premiere precisa reabrir.
    Essa pasta pede administrador: aqui foi copiado com `Start-Process powershell -Verb RunAs` (o usuário aprova no
    UAC). Depois disso: **LUT DO GAB = índice 13** no 13.1.5 desta máquina, diferença 1,27 (o 2º melhor deu 13,47),
    em 8 s. `aplicar_lut` pôs o Look nos 2 takes e o quadro exportado mostra o look do Gab. A amostra da calibração tem
    que **cobrir o quadro inteiro**: com a amostra pequena e preto em volta, um índice errado (5) "ganhou" por pouco. ✅
22. O After Effects que o `ae_lib` acha (`Adobe After Effects 20*`) pode ser uma pasta que sobrou de desinstalação
    (aqui: `Adobe After Effects 2023` só com `Support Files`, sem `AfterFX.exe`), e o `conectar()` quebra com
    FileNotFoundError. Conferir o executável antes. ✅ (achado; `lettering_ae` ⏳ sem AE nesta máquina)
18. `exportFramePNG` volta antes de gravar o arquivo: esperar o arquivo aparecer (`P.quadro` espera). ✅
19. Tamanho da fonte não está no TrackItem: vem de `projectItem.getProjectMetadata()`, campo
    `Column.Intrinsic.VideoInfo` ("1920 x 1080 (1,0)"). Escala para cobrir = `max(W/w, H/h) × 100` em Motion > Scale
    (`components[1].properties[1]`). ✅

## O que o Gab faz no 26 e como fica no 2019

| Etapa (`premiere_lib.py`) | No 2019 (`premiere2019_lib.py`) | Estado |
|---|---|---|
| `abrir_projeto` | `qe.newProject` + `app.openDocument`, bins da regra 1b | ✅ |
| `criar_sequencia` | `qe.project.newSequence` + `setSettings` (w, h, fps exatos), vai para o bin Timelines | ✅ (a sequência ainda não herda a mídia base como no 26) |
| `colocar` (V/A, de/ate, só vídeo, só áudio) | `Sequence.overwriteClip` / `Track.overwriteClip` + subclipe só vídeo + `preencher` | ✅ |
| `volume` / fades | `GAB.nivel` + escala 0,5 = 0 dB + keyframes `addKey/setValueAtKey` | ✅ medido no render (mono e estéreo, com e sem ponto de entrada) |
| `envelope_volume` | igual ao volume, mais pontos | ⏳ (não portei) |
| `colocar_musica` | `colocar` com de/ate na A2 | ✅ |
| `montar_takes` | `colocar` só vídeo na V2 com `preencher=True` | ✅ |
| `transcrever` (Speech to Text) | **não existe no 2019** (chegou no 15.x/2021). Usar o motor whisper do `transcrever.py` | ❌ no Premiere |
| `isolar_voz` (Enhance Speech) | **não existe no 2019**. Tratar o áudio fora (ffmpeg/serviço) antes de importar | ❌ no Premiere |
| `importar_legenda` + estilo GAB USA | `legenda_gab(seq, srt, trilha, y=724)`: um título por fala, Poppins Bold, caixa alta, branca, sombra leve, centro em Y 724 (y=390 para a legenda baixa). `legenda()` continua para a Open Caption simples | ✅ |
| `aplicar_lut` | Lumetri ✅. "Look" = parâmetro 30, "Input LUT" = 6 (índices). `aplicar_lut(seq, v, tempos)` + `_indice_lut` calibram e guardam em `lut_indice.json` por versão | ✅ LUT do Gab = índice 13 aqui, aplicado e conferido (o .cube vai para a pasta da instalação, como admin: armadilha 21) |
| `lettering` (texto) | `titulo(seq, texto, inicio, dur, trilha, fonte, tamanho, cor, y)`: título nativo com o Source Text reescrito | ✅ |
| `lettering_ae` (animado) | modelo da biblioteca montado no AE → `ae_lib.renderizar` (MOV com alfa) → `colocar`. Não vira MOGRT: o 13.x não importa MOGRT do AE novo | ⏳ sem AE nesta máquina (armadilha 22). Sem AE, lettering animado = motion HyperFrames em MOV, que já entra ✅ |
| `animar` (keyframes Motion) | `addKey/setValueAtKey` em `components[1]` (mesmo mecanismo do volume) | ⏳ |
| `marcador` | `markers.createMarker` | ✅ |
| `exportar` | `exportAsMediaDirect` síncrono, preset H.264 Match Source - High bitrate | ✅ 15 s para 20 s 1080x1920 |
| retrato da timeline (regra 1g) | `retrato()` | ✅ |
| — (novo) | `cortar` (razor), `transicao`, `velocidade`, `remover`, `quadro` (PNG para conferir sem tela), `descrever` (reflexão) | ✅ |

## Velocidade: o jeito rápido

Cada chamada custa ~6 ms de ida e volta. O tempo real é o que o Premiere faz: importar (1,5 s para 5 arquivos),
salvar (~1 s), overwrite (20 a 150 ms). Duas regras:

1. **Mandar a timeline inteira num comando** (`teste/t10_lote.py`): 1,85 s para a montagem completa, contra ~4,2 s
   chamando função por função (`teste/t11_ponta_a_ponta.py`), porque cada função reimporta, procura item e salva.
   Sugestão: o Gab monta um "plano" (JSON) e um `P.montar(plano)` executa tudo no ExtendScript.
2. **Conferir sem tela**: `P.quadro(seq, t, png)` (QE `exportFramePNG`) e o render do `exportar` vão direto para o
   `qc.py`. Não precisa de screenshot em nenhum passo.

**Timeline inteira por XML do Final Cut 7** (`P.xmeml(plano, saida)` + `P.importar_xml(xml)`, `teste/t16_xmeml.py`):
o Gab descreve a timeline num dicionário (trilhas de vídeo e de áudio, cada clipe com arquivo, início, de/ate, escala,
dB), o Python gera o xmeml v4 e o Premiere importa com `importFiles`. Conferido no 13.1.5: sequência 1080×1920 a
30 fps exatos, 3 trilhas de vídeo e 2 de áudio nos tempos certos, take **só vídeo** (clipe de vídeo sem par de áudio
no XML não leva o áudio do take, sem precisar de subclipe), ponto de entrada da música, escala (Basic Motion > scale)
e volume (Audio Levels > level, **ganho linear: 1 = 0 dB**, que o Premiere converte para a escala dele: 0,316 virou
Level 0,158 = -10 dB). Gerar 1,2 s (quase tudo é o ffprobe de cada arquivo) e importar 1,3 s. ✅

Quando usar: montagem inicial grande (muitos clipes) num passo só, e que tende a funcionar igual em outras versões
do Premiere, porque o xmeml é formato de troca antigo e estável. Depois, os ajustes finos (LUT, legenda GAB USA,
títulos, fades) vão pela ponte. ⏳ Fades por keyframe dentro do XML e transições no XML não testei.

## Integração sugerida no /ogab

- Pasta `premiere/cep/` (ou `premiere/legado/`) com `plugin/`, `jsx/gab_ppro.jsx`, `premiere2019_lib.py`,
  `instalar.ps1`/`.sh`.
- Escolha da ponte pela versão: tentar `GET 127.0.0.1:8767/ping` (CEP) e o WebSocket 8765 (UXP), ou ler a versão
  instalada. Expor as duas com a mesma interface (`P.colocar`, `P.volume`...) para o `SKILL.md` não mudar.
- **Não reaproveitar constantes do UXP**: escala de volume (armadilha 11), `-1` como "sem trilha" (9), MOGRTs (17).
- Porta 8767 (8765 é a UXP do Premiere, 8766 é a do AE).
- O bundle ID que usei, `com.gabrielxreis.ogab.ppronte`, é provisório: renomear à vontade.
- Mac: o mesmo código deve rodar (CEP é igual). ⏳ Testar caminhos com `/` na QE do Mac.

## O que falta testar

- O instalador do /ogab precisa copiar o LUT para `<Premiere>\Lumetri\LUTs\Creative` no 13.x (como admin; o
  `instalar.ps1` daqui tenta e avisa).
- `lettering_ae` com um After Effects instalado de verdade.
- Legenda GAB USA: a sombra foi ligada (27%, deslocamento 2) mas não comparei com o render do DaVinci.
- Undo: cada chamada do ExtendScript vira um passo de Undo sem nome. A QE tem `undo()`/`undoStackIndex()`, mas não
  testei agrupar.
- Versões 2018, 2020 a 25.x (o manifesto aceita; a API muda). Rodar `P.descrever(...)` em cada uma e comparar com
  `teste/reflexao_13.1.5.json`.
- xmeml com keyframes (fades) e transições dentro do XML.

## Arquivos deste pacote

| Arquivo | O que é | Estado |
|---|---|---|
| `plugin/CSXS/manifest.xml`, `plugin/index.html`, `plugin/main.js` | a extensão CEP (servidor 127.0.0.1:8767) | ✅ Windows |
| `jsx/gab_ppro.jsx` | funções de apoio no ExtendScript (`GAB.*`), carregado e recarregado sozinho | ✅ |
| `premiere2019_lib.py` | a biblioteca do Gab para o 13.x (mesma interface do `premiere_lib.py`) | ✅, menos `lettering_ae` (sem AE aqui) |
| `instalar.ps1` | instalador Windows (copia o plugin, liga PlayerDebugMode) | ✅ a cópia; o registro já estava ligado aqui |
| `instalar.sh` | instalador Mac | ⏳ **não testado** (feito sem Mac) |
| `teste/gerar_midia.py` | gera as mídias de teste com ffmpeg em `teste/midia` (não vão no zip: ~100 MB) | ✅ |
| `teste/t1_ponte.py` ... `teste/t11_ponta_a_ponta.py` | os experimentos, na ordem em que deram as armadilhas | ✅ |
| `teste/t12_texto.py`, `teste/t13_legenda.py`, `teste/t14_legenda_gab.py` | texto do título nativo, Open Captions + calibração do tamanho GAB USA, legenda GAB USA com medida do centro | ✅ |
| `teste/t15_volume_estereo.py`, `teste/t16_xmeml.py` | volume e fades de clipe estéreo medidos no render; timeline inteira por xmeml | ✅ |
| `teste/reflexao_13.1.5.json` | reflexão do DOM e da QE do 13.1.5 | ✅ |
| `teste/dll_metodos_*.txt` | nomes de métodos tirados das DLLs | ✅ |


## Como reproduzir

1. `powershell -ExecutionPolicy Bypass -File instalar.ps1` (ou copiar `plugin/` para
   `%APPDATA%\Adobe\CEP\extensions\com.gabrielxreis.ogab.ppronte` com o PlayerDebugMode ligado) e reabrir o Premiere.
   Depois `python teste/gerar_midia.py`.
2. `python teste/t1_ponte.py`: versão, latência e erros capturados.
3. `python teste/t11_ponta_a_ponta.py`: projeto de teste, sequência, mídia, efeito, transição, corte, quadro e render
   em `teste/render/`. As mídias de teste (`teste/midia/`) foram geradas com ffmpeg (barras, mandelbrot, seno).
4. `teste/t2...t10`: os experimentos que deram as armadilhas acima, na ordem em que foram feitos.

REA: o MCP do `rea-agents` não conectava porque o `.claude.json` usava `npx -y rea-agents@6.7.0 mcp`, que baixa 174
pacotes (cerca de 2 min) a cada início e passa do limite de 30 s. Instalar global (`npm i -g rea-agents@6.7.0`) e
registrar `rea-agents mcp` resolve. O REA pede Node 24.22.1 ou mais; a máquina tinha 24.20.
