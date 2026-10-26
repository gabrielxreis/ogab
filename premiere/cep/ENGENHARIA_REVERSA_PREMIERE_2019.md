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
2. **O ExtendScript não aceita regex com `\u0000` ou ` `** ("Syntax error"). O `GAB.json` escapa por laço. ✅
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
    (`inPoint + t`). ✅ (só testei WAV mono; ⏳ conferir o padrão num clipe estéreo)
12. **A QE conta os vãos como itens da trilha** (`type "Empty"`): `getItemAt(0)` pegou o vão antes do take, e o
    `addVideoEffect` "não existia". Filtrar `type === "Clip"`. ✅
13. **Objeto da QE fica inválido depois de qualquer edição** ("Object is invalid"): buscar de novo a cada operação
    (`GAB.qeClipe`). ✅
14. **`setSpeed` recebe multiplicador**, não porcentagem: 200 virou 1 quadro (3,5 s / 200). 2 = 200%. ✅
15. `razor` da QE corta só a trilha pedida (V1 sem cortar A1) e usa timecode `"HH;MM;SS;FF"`. ✅
16. Legenda: SRT importado vira item que se coloca numa **trilha de vídeo** (o 13.x não cria trilha de legenda pela
    API). **O item começa na primeira fala**: colocado em 0, adianta tudo; colocar no início da 1ª legenda. Acentos ✅.
    Estilo da legenda (fonte, posição Y 724 do GAB USA) ⏳ não achei pela API.
17. **MOGRT do Gab (`premiere/assets/mogrt/*.mogrt`, feitos para o 26) travou o `importMGT` por 82 s** e terminou em
    exceção nativa. Não oferecer esses MOGRTs no 2019 (⏳ gerar uma versão pelo AE 2019 ou usar título nativo).
    MOGRT nativo do 2019 (`Essential Graphics\Basic Title.mogrt`) entra (✅), mas `getMGTComponent()` volta null. O
    texto fica em `components[3]` "Text [AE.ADBE Text]" > "Source Text": um blob binário com JSON (`mTextParam`).
    Editável em tese, ⏳ não testei escrever.
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
| `volume` / fades | `GAB.nivel` + escala 0,5 = 0 dB + keyframes `addKey/setValueAtKey` | ✅ (valor), ⏳ ouvir os fades no render |
| `envelope_volume` | igual ao volume, mais pontos | ⏳ (não portei) |
| `colocar_musica` | `colocar` com de/ate na A2 | ✅ |
| `montar_takes` | `colocar` só vídeo na V2 com `preencher=True` | ✅ |
| `transcrever` (Speech to Text) | **não existe no 2019** (chegou no 15.x/2021). Usar o motor whisper do `transcrever.py` | ❌ no Premiere |
| `isolar_voz` (Enhance Speech) | **não existe no 2019**. Tratar o áudio fora (ffmpeg/serviço) antes de importar | ❌ no Premiere |
| `importar_legenda` | `legenda()`: SRT direto numa trilha de vídeo, no início da 1ª fala | ✅ (estilo ⏳) |
| `aplicar_lut` | Lumetri ✅. "Look" é o parâmetro 30 e "Input LUT" o 6, ambos índice (como no 26). `aplicar_lut(seq, v, tempos)` + `_indice_lut` portam a calibração do 26 com `exportFramePNG` | ⏳ escrito, não rodou |
| `lettering` (MOGRT) | `importMGT(caminho, ticks, v, a)` ✅ com MOGRT nativo; MOGRT do Gab trava (armadilha 17) | ❌/⏳ |
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

⏳ Caminho alternativo para timelines enormes: gerar XML do Final Cut 7 (`xmeml`) e importar (`importFiles` com .xml
ou `app.openFCPXML`, que existe no 13.1.5). É o formato de troca que o Premiere importa há muitas versões e põe
centenas de clipes de uma vez. Não testei aqui.

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

- Calibração do LUT (índice do "Input LUT" do Lumetri no 2019).
- Escrever o texto de um título nativo (blob `mTextParam`) e gerar MOGRTs do Gab compatíveis com 2019.
- Estilo e posição da legenda.
- Fades do volume ouvidos no render; padrão do `Level` em clipe estéreo.
- Undo: cada chamada do ExtendScript vira um passo de Undo sem nome. A QE tem `undo()`/`undoStackIndex()`, mas não
  testei agrupar.
- Versões 2018, 2020 a 25.x (o manifesto aceita; a API muda). Rodar `P.descrever(...)` em cada uma e comparar com
  `teste/reflexao_13.1.5.json`.
- Importar `xmeml`.

## Arquivos deste pacote

| Arquivo | O que é | Estado |
|---|---|---|
| `plugin/CSXS/manifest.xml`, `plugin/index.html`, `plugin/main.js` | a extensão CEP (servidor 127.0.0.1:8767) | ✅ Windows |
| `jsx/gab_ppro.jsx` | funções de apoio no ExtendScript (`GAB.*`), carregado e recarregado sozinho | ✅ |
| `premiere2019_lib.py` | a biblioteca do Gab para o 13.x (mesma interface do `premiere_lib.py`) | ✅, menos `aplicar_lut` |
| `instalar.ps1` | instalador Windows (copia o plugin, liga PlayerDebugMode) | ✅ a cópia; o registro já estava ligado aqui |
| `instalar.sh` | instalador Mac | ⏳ **não testado** (feito sem Mac) |
| `teste/gerar_midia.py` | gera as mídias de teste com ffmpeg em `teste/midia` (não vão no zip: ~100 MB) | ✅ |
| `teste/t1_ponte.py` ... `teste/t11_ponta_a_ponta.py` | os experimentos, na ordem em que deram as armadilhas | ✅ |
| `teste/reflexao_13.1.5.json` | reflexão do DOM e da QE do 13.1.5 | ✅ |
| `teste/dll_metodos_*.txt` | nomes de métodos tirados das DLLs | ✅ |

**`aplicar_lut` / `_indice_lut`** (calibração do LUT do Gab no Look do Lumetri, parâmetro 30) foram escritas no fim e
**não rodaram ainda** (⏳). Já confirmado: o Lumetri do 13.1.5 tem "Look" no parâmetro 30 e "Input LUT" no 6, os dois
como índice. O `LUT DO GAB.cube` está em `%APPDATA%\Adobe\Common\LUTs\Creative`, mas **não sei se o 13.x lê essa
pasta de usuário**. A pasta da própria instalação (`<Premiere>\Lumetri\LUTs\Creative`) com certeza é lida, mas pede
admin. A calibração responde isso: se não achar o índice, o LUT não está no menu.

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
