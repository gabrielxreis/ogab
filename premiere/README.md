# Gab (/ogab) no Adobe Premiere Pro

O mesmo método do `SKILL.md` (roteiro, voz, legenda, música, SFX, takes, cor, lettering, motions, QC), com o **Premiere Pro 2026+** no lugar do DaVinci. Nada do fluxo do DaVinci muda: esta pasta é uma camada à parte e funciona no Mac e no Windows.

Quando vale: `config.json` com `"editor": "premiere"` (`/ogab config editor premiere`) ou o usuário pedindo Premiere. Nesse caso, em toda etapa que o `SKILL.md` manda usar `resolve_lib.py`, usar `premiere/premiere_lib.py`.

## Instalar (uma vez por máquina)

- Mac: `bash ~/.claude/skills/ogab/premiere/instalar.sh`
- Windows (depois do `windows\install.ps1`): `powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\ogab\premiere\instalar.ps1"`

Instala o plugin **Gab Ponte**, o LUT (`assets/lut/*.cube` nas pastas de LUT do Premiere) e os letterings (`assets/mogrt/*.mogrt` em Motion Graphics Templates). No Premiere, uma vez: **Window > UXP Plugins > Gab Ponte**, e deixar o painel encaixado. Ele mostra "conectado" enquanto o Gab trabalha.

## Como o Gab fala com o Premiere

O Premiere não aceita script de fora como o DaVinci. Por isso o plugin Gab Ponte fica dentro dele e se conecta ao Python da skill (WebSocket local `127.0.0.1:8765`, sem internet). O plugin não tem lógica de edição: cada função do `premiere_lib.py` manda o seu trecho de JavaScript da API UXP. Para melhorar o Gab basta um `git pull`, sem reinstalar o plugin.

```python
import sys, os; sys.path.insert(0, os.path.expanduser("~/.claude/skills/ogab/premiere")); import premiere_lib as P
P.js("return (await proj()).name")   # qualquer coisa da API: https://developer.adobe.com/premiere-pro/uxp/
```

Se der `O Premiere não conectou`: o Premiere está fechado ou o painel Gab Ponte não foi aberto. Pedir ao usuário para abrir e tentar de novo.

## Etapa por etapa (o que muda em relação ao DaVinci)

| Etapa do SKILL.md | No Premiere |
|---|---|
| 4. Projeto, pastas, sequência | `P.abrir_projeto("<pasta do vídeo>/<Assunto> - <Empresa>.prproj")` cria a árvore de bins (regra 1b). Um projeto por cliente/lote, uma **sequência** por vídeo (regra 1a): `P.criar_sequencia(nome, gravacao, 1080, 1920, fps)` |
| Transcrição | `P.transcrever(arquivo, ".../legendas/transcricao.json", "pt-br")` usa o **Speech to Text do próprio Premiere** e salva no mesmo formato que o `legendas.py` já lê (segundos, como o motor whisper). Sem Whisper. Precisa do pacote de idioma pt-BR (o Premiere baixa na 1ª vez) |
| 1d. Voice isolation | `P.isolar_voz(seq, 0)` tenta o **Enhance Speech** pela API. Se voltar `{"manual": true}` (a API desta versão não expõe o efeito), pedir ao usuário: selecionar os clipes da A1 > Essential Sound > Dialogue > Enhance, uma vez para todos |
| Cortes | `cortes.py` igual (ffmpeg). Montar os trechos com `P.colocar(seq, arq, tempo, video=0, audio=0, de=, ate=)` |
| 4b. Legenda | `legendas.py`/`legenda_auto.py` iguais até o `.srt`. Depois `P.importar_legenda(seq, srt)`. Estilo GAB USA: o usuário aplica uma vez o estilo de legenda salvo ("GAB USA") na trilha (Properties > Track Style). Posição Y 724 vem do estilo |
| Legenda baixa (Y 390) | igual ao DaVinci: o `legenda_baixa.py` gera os clipes transparentes, e o Gab coloca com `P.colocar(seq, clipe, t, video=<trilha do topo>, audio=None)` e tira a legenda original do trecho |
| 5. Música | `P.colocar_musica(seq, wav, inicio_faixa=hook - tempo_CTA, dur=, db=-10)`: WAV bruto na A2, fades no clipe (regra do usuário) |
| 6. SFX | arquivos como hoje; `P.colocar(seq, sfx, t, video=None, audio=<A3..>, db=)` |
| 7. Takes | `P.montar_takes(seq, [(arq, t0), ...], fim=, trilha=1)`: b-roll na V2, a V1 é intocável (regra 1j) |
| 7b. Cor | `P.aplicar_lut([takes], "LUT DO GAB")` aplica o LUT do Gab como Input LUT de cada take (confere lendo de volta). `P.luts_instalados()` lista os disponíveis. O conversor de iPhone do DaVinci não existe aqui: take de iPhone (HLG) o Premiere já converte para Rec.709 sozinho |
| 8. Lettering | `P.mogrts()` lista os instalados; `P.lettering(seq, "<nome do mogrt>", "TEXTO", inicio, dur, trilha=2)` insere, ajusta a duração e troca o texto. Devolve os parâmetros do template para conferir |
| 8. Motions (HyperFrames) | iguais: render MOV com alfa e `P.colocar(seq, mov, t, video=<trilha>, audio=None)` |
| 9. Render | `P.exportar(seq, ".../videos/<nome>.mp4")` com o preset H.264 Match Source do Premiere (ou `preset=<.epr>`). Só quando o usuário pedir. `qc.py` igual no arquivo exportado |

### Regras que mudam
- **1c (Stacked Timelines):** não existe no Premiere. Deixar as sequências dos vídeos abertas (`P.js("await (await proj()).openSequence(await seqPorNome(await proj(), args.n))", n=nome)`) e a do 01 ativa.
- **1g (retrato da timeline):** `retrato.py` é do DaVinci. No Premiere, antes de mexer: `P.js(...)` listando os itens de cada trilha (nome, início, fim) e salvar em `<pasta>/retrato_antes.json`. Depois, comparar e mexer só no alvo.
- **Undo:** cada função do `premiere_lib.py` é um passo de Undo com nome "Gab: ...". Mesmo assim, não usar Undo com o usuário dentro do Premiere.
- **`projeto.py status --timeline`** lê o DaVinci. No Premiere, usar `projeto.py status <pasta>` (sem `--timeline`) e marcar as etapas feitas à mão (`projeto.py marcar`).

## Arquivos

| Arquivo | O que é |
|---|---|
| `premiere_lib.py` | as funções acima (ponte WebSocket + JS da API UXP) |
| `plugin/` | o painel Gab Ponte (manifesto UXP v5, Premiere 25.6+) |
| `assets/lut/` | LUT do Gab (`LUT DO GAB.cube`) |
| `assets/mogrt/` | letterings animados exportados do Premiere |
| `instalar.sh` / `instalar.ps1` | instaladores Mac / Windows |
