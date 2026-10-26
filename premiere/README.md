# Gab (/ogab) no Adobe Premiere Pro

O mesmo método do `SKILL.md` (roteiro, voz, legenda, música, SFX, takes, cor, lettering, motions, QC), com o **Premiere Pro** no lugar do DaVinci. Nada do fluxo do DaVinci muda: esta pasta é uma camada à parte e funciona no Mac e no Windows.

**Duas pontes, uma interface.** O Premiere 26+ usa UXP; o Premiere 2018 a 25.x usa CEP + ExtendScript. O Gab não precisa saber a versão: usa `premiere/ponte.py`, que escolhe sozinho a ponte que estiver no ar (CEP na porta 8767 se o Premiere antigo estiver aberto; senão UXP na 8765). `P.qual()` diz qual pegou. Detalhes da ponte antiga e o que ela NÃO faz: seção "Premiere antigo (CEP)" mais abaixo e `cep/ENGENHARIA_REVERSA_PREMIERE_2019.md`.

Quando vale: `config.json` com `"editor": "premiere"` (`/ogab config editor premiere`) ou o usuário pedindo Premiere. Nesse caso, em toda etapa que o `SKILL.md` manda usar `resolve_lib.py`, usar **`premiere/ponte.py`** (que delega para `premiere_lib.py` no 26+ ou `cep/premiere2019_lib.py` no 2018–25).

## Instalar (uma vez por máquina)

**Premiere 26+ (UXP):**
- Mac: `bash ~/.claude/skills/ogab/premiere/instalar.sh`
- Windows (depois do `windows\install.ps1`): `powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\ogab\premiere\instalar.ps1"`

Instala o plugin **Gab Ponte**, o LUT (`assets/lut/*.cube` nas pastas de LUT do Premiere) e os letterings (`assets/mogrt/*.mogrt` em Motion Graphics Templates). No Premiere, uma vez: **Window > UXP Plugins > Gab Ponte**, e deixar o painel encaixado. Ele mostra "conectado" enquanto o Gab trabalha.

**Premiere 2018 a 25.x (CEP):**
- Windows: `powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\ogab\premiere\cep\instalar.ps1"`
- Mac: `bash ~/.claude/skills/ogab/premiere/cep/instalar.sh`

Instala a extensão **Gab Ponte PPro** (CEP) e liga o `PlayerDebugMode` (extensão sem assinatura). Esse passo escreve no registro do Windows e é do USUÁRIO: o Gab não faz isso sozinho. Depois é só reabrir o Premiere, a ponte inicia invisível. Se não iniciar, abrir **Window > Extensions > Gab Ponte**.

## Como o Gab fala com o Premiere

O Premiere não aceita script de fora como o DaVinci. Por isso o plugin Gab Ponte fica dentro dele e se conecta ao Python da skill, sem internet. No 26+ é UXP por WebSocket `127.0.0.1:8765`; no 2018–25 é CEP por HTTP `127.0.0.1:8767`. O plugin não tem lógica de edição: cada função manda o seu trecho de código (JS da API UXP no 26, ExtendScript no antigo). Para melhorar o Gab basta um `git pull`, sem reinstalar o plugin.

Sempre importe pela **ponte** (ela escolhe a versão certa):

```python
import sys, os; sys.path.insert(0, os.path.expanduser("~/.claude/skills/ogab/premiere")); import ponte as P
P.qual()                 # "uxp (Premiere 26.x)" ou "cep (Premiere 13.1.5)"
P.colocar(seq, arquivo, tempo, video=1)   # mesma interface nas duas pontes
```

Se der `O Premiere não conectou` / não responder na porta: o Premiere está fechado ou o painel Gab Ponte não foi aberto. Pedir ao usuário para abrir e tentar de novo.

## Etapa por etapa (o que muda em relação ao DaVinci)

| Etapa do SKILL.md | No Premiere |
|---|---|
| 4. Projeto, pastas, sequência | `P.abrir_projeto("<pasta do vídeo>/<Assunto> - <Empresa>.prproj")` cria a árvore de bins (regra 1b). Um projeto por cliente/lote, uma **sequência** por vídeo (regra 1a): `P.criar_sequencia(nome, gravacao, 1080, 1920, fps)` |
| Transcrição | `P.transcrever(arquivo, ".../legendas/transcricao.json", "pt-br")` usa o **Speech to Text do próprio Premiere** e salva no mesmo formato que o `legendas.py` já lê (segundos, como o motor whisper). Sem Whisper. Precisa do pacote de idioma pt-BR (o Premiere baixa na 1ª vez) |
| 1d. Voice isolation | `P.isolar_voz(seq, 0)` aplica o **Enhance Speech** ("Aprimorador de voz" no Premiere em português) em todos os clipes da trilha. Testado no 26.5.2 |
| Cortes | `cortes.py` igual (ffmpeg). Montar os trechos com `P.colocar(seq, arq, tempo, video=0, audio=0, de=, ate=)` |
| 4b. Legenda | `legendas.py`/`legenda_auto.py` iguais até o `.srt`. `P.importar_legenda(seq, srt)` põe o SRT no bin Legendas. **A API do 26.5 não cria trilha de legenda**: pedir ao usuário para arrastar o SRT do bin para a timeline (1 movimento) e aplicar o estilo GAB USA na trilha (Properties > Track Style). Posição Y 724 vem do estilo |
| Legenda baixa (Y 390) | igual ao DaVinci: o `legenda_baixa.py (PROIBIDO sem pedido do usuário, SKILL.md 1h3: ajustar a legenda no editor)` gera os clipes transparentes, e o Gab coloca com `P.colocar(seq, clipe, t, video=<trilha do topo>, audio=None)` e tira a legenda original do trecho |
| 5. Música | `P.colocar_musica(seq, wav, inicio_faixa=hook - tempo_CTA, dur=, db=-10)`: WAV bruto na A2, fades no clipe (regra do usuário) |
| 6. SFX | arquivos como hoje; `P.colocar(seq, sfx, t, video=None, audio=<A3..>, db=)` |
| 7. Takes | `P.montar_takes(seq, [(arq, t0), ...], fim=, trilha=1)`: b-roll na V2, a V1 é intocável (regra 1j). Vídeo narrado (sem apresentador): `trilha=0`. O take entra **sem áudio** (subclipe "<take> (video)" criado no bin) |
| 7b. Cor | `P.aplicar_lut(seq, [takes], "LUT DO GAB")` põe um **Lumetri** em cada take com o LUT do Gab como Look. A API não aceita o LUT por nome (o Look é um índice do menu, que muda por máquina): na 1ª vez calibra sozinho (~1 min, compara quadros exportados com o `.cube` aplicado pelo ffmpeg) e guarda em `assets/lut/indice.json`. O conversor de iPhone do DaVinci não existe aqui: take de iPhone (HLG) o Premiere já converte para Rec.709 sozinho |
| 8. Lettering | MOGRTs da biblioteca de motions (`premiere/assets/mogrt/`, gerados no AE por `scripts/gerar_mogrts.py`: lista-checks, contador-barra, frase-duas-linhas...) + os que o usuário criar. `P.mogrts()` lista os instalados; `P.lettering(seq, "<nome do mogrt>", "TEXTO", inicio, dur, trilha=2)` insere, ajusta a duração e troca o texto. Devolve os parâmetros do template para conferir |
| 8. Motions (HyperFrames) | iguais: render MOV com alfa e `P.colocar(seq, mov, t, video=<trilha>, audio=None)` |
| 9. Render | `P.exportar(seq, ".../videos/<nome>.mp4")` com o preset H.264 Match Source do Premiere (ou `preset=<.epr>`). Só quando o usuário pedir. `qc.py` igual no arquivo exportado |

### Regras que mudam
- **1c (Stacked Timelines):** não existe no Premiere. Deixar as sequências dos vídeos abertas (`P.js("await (await proj()).openSequence(await seqPorNome(await proj(), args.n))", n=nome)`) e a do 01 ativa.
- **1g (retrato da timeline):** `retrato.py` é do DaVinci. No Premiere, antes de mexer: `P.js(...)` listando os itens de cada trilha (nome, início, fim) e salvar em `<pasta>/retrato_antes.json`. Depois, comparar e mexer só no alvo.
- **Undo:** cada função do `premiere_lib.py` é um passo de Undo com nome "Gab: ...". Mesmo assim, não usar Undo com o usuário dentro do Premiere.
- **`projeto.py status --timeline`** lê o DaVinci. No Premiere, usar `projeto.py status <pasta>` (sem `--timeline`) e marcar as etapas feitas à mão (`projeto.py marcar`).

## Armadilhas da API (aprendidas no teste de 12/10/2026, Premiere 26.5.2)

- Projeto: `Project.isProject()` diz true para qualquer caminho `.prproj`, mesmo inexistente; por isso `abrir_projeto` confere o arquivo no Python.
- `createOverwriteItemAction` recusa o `ClipProjectItem` ("Invalid parameter"): passar o item cru do projeto. `-1` na trilha de áudio NÃO tira o áudio do take (vai para a A1 e apaga a narração): usar subclipe só de vídeo.
- Componentes e parâmetros de efeito só valem dentro de `project.lockedAccess(...)` e sem `await` no meio (senão "script object is no longer valid"). A seleção de `TrackItemSelection.createEmptySelection` só vale dentro do callback.
- Overwrite numa trilha que não existe dá "invalid track index"; trilhas de áudio além das existentes são criadas só em alguns casos. Nunca usar a seleção do usuário (`remover()` usa seleção própria).
- O Premiere não grava quadro exportado na pasta temporária do sistema (`/var/folders`); a calibração usa `assets/lut/_calibracao`.
- **Premiere 26.0 (17/10/2026):** não tem `createSubClipAction`, então `colocar(..., audio=None)` e `montar_takes` param com erro claro. Motion MOV (sem áudio) entra com `createOverwriteItemAction(item, t, trilha, -1)` direto (conferir antes com ffprobe que o MOV não tem áudio). Desde 19/10/2026 o `colocar`/`montar_takes` já faz isso sozinho (`_tem_audio` pelo ffprobe): no 26.5 o subclipe de arquivo sem áudio dá "startTime must be less than endTime". Overwrite numa V acima da última CRIA a trilha nesse caso. Recolocar um motion mais longo que o vão cobre o começo do seguinte: recolocar os seguintes em ordem.
- O painel Gab Ponte carrega mesmo na tela inicial do Premiere; plugin atualizado só carrega depois de reiniciar o Premiere.

## Premiere antigo (2018 a 25.x): ponte CEP

Quando `P.qual()` começa com **`cep`**, a ponte ativa é a do Premiere antigo (`cep/premiere2019_lib.py`, ExtendScript). A interface é a mesma para o que importa (`colocar`, `volume`, `colocar_musica`, `montar_takes`, `legenda`, `marcador`, `cortar`, `efeito`, `transicao`, `velocidade`, `aplicar_lut`, `quadro`, `exportar`, `retrato`, `salvar`), com estas diferenças (testadas no 13.1.5; detalhes e armadilhas em `cep/ENGENHARIA_REVERSA_PREMIERE_2019.md`):

- **Transcrição e Enhance Speech NÃO existem na API** do Premiere antigo. Transcrever com o whisper do `transcrever.py` e tratar o áudio (isolar voz) com ffmpeg/serviço **antes** de importar. Chamar `P.transcrever`/`P.isolar_voz` pela ponte CEP dá erro claro.
- **Sequência:** `P.criar_sequencia(nome, w, h, fps)` cria pela QE (sem diálogo). Ela ainda **não herda a mídia base** como no 26; o portão do menu (`portao_menu`) continua valendo no fluxo da skill, não na lib.
- **Legenda com estilo GAB USA:** `P.legenda_gab(seq, srt, y=724)` faz a legenda no estilo GAB USA criando **um título nativo por fala** (Poppins Bold, caixa alta, branca, sombra leve, centro em Y 724; `y=390` para a legenda baixa). As Open Captions do 13.x não deixam trocar fonte/tamanho pela API, por isso vai por títulos. `P.legenda(seq, srt)` continua para a Open Caption simples.
- **Título e lettering:** `P.titulo(seq, texto, inicio, dur, fonte, tamanho, cor, y)` escreve um **título nativo editável** (reescreve o `mTextParam` do Basic Title). `P.lettering_ae(seq, modelo, valores, inicio)` faz o **lettering animado** da biblioteca do Gab montando no After Effects e colocando o MOV com alfa. O **MOGRT do Gab (importMGT) ainda não entra no 2019** (trava); por isso o caminho é `titulo`/`lettering_ae`.
- **LUT:** `P.aplicar_lut` funciona (Lumetri; "Look" é o parâmetro 30 e "Input LUT" o 6, índices calibrados e guardados em `lut_indice.json`). O `cep/instalar.ps1` **copia o `LUT DO GAB.cube` para a pasta Lumetri do Premiere** (Program Files, por isso roda como administrador); o Lumetri do 13.x só lê LUT de lá, não do `%APPDATA%`.
- **envelope_volume** não foi portado: usar `P.volume` com mais pontos, ou deixar para o 26.
- **Timeline inteira num comando:** para Reels, montar o "plano" e mandar de uma vez é ~2x mais rápido que função por função (o ExtendScript reimporta/salva a cada chamada). Ver `cep/teste/t10_lote.py`.
- **Conferir sem tela:** `P.quadro(seq, t, png)` e o render do `P.exportar` vão direto para o `qc.py`, sem screenshot.
- **Instalação/registro:** a extensão CEP precisa do `PlayerDebugMode` ligado (`cep/instalar.ps1`), que é passo do USUÁRIO no Windows. O Gab nunca escreve no registro.
- **CEP está sendo aposentado pela Adobe:** confirmar no calendário dela até qual versão a ponte abre antes de prometer "qualquer Premiere".

## Arquivos

| Arquivo | O que é |
|---|---|
| `ponte.py` | **o que o Gab importa**: escolhe a ponte (UXP 26+ ou CEP 2018–25) e expõe a interface comum |
| `premiere_lib.py` | ponte UXP (WebSocket 8765 + JS da API UXP), Premiere 26+ |
| `cep/` | ponte CEP (HTTP 8767 + ExtendScript), Premiere 2018–25: `premiere2019_lib.py`, `jsx/gab_ppro.jsx`, `plugin/` (extensão), `instalar.ps1/.sh`, `teste/`, `ENGENHARIA_REVERSA_PREMIERE_2019.md` |
| `plugin/` | o painel Gab Ponte (manifesto UXP v5, Premiere 25.6+) |
| `assets/lut/` | LUT do Gab (`LUT DO GAB.cube`) |
| `assets/mogrt/` | letterings animados exportados do Premiere |
| `instalar.sh` / `instalar.ps1` | instaladores Mac / Windows |
- **Volume (19/10/2026):** o Nível do Premiere vai de 0 a 1.0 = +15 dB; 0 dB = 0.17782794 (padrão de todo clipe). `P.volume` converte com 10^((dB-15)/20). Quem ler o Nível pela API: converter de volta com 20·log10(v) + 15.
