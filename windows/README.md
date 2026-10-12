# Gab (/ogab) no Windows

Esta pasta é a camada Windows da skill. **Nenhum arquivo da versão Mac foi alterado:** o mesmo `SKILL.md`, os mesmos docs e os mesmos scripts de `scripts/` valem no Windows, com as diferenças abaixo. O `install.ps1` deixa a máquina pronta e põe no `~/.claude/CLAUDE.md` do usuário um aviso para o Gab ler este arquivo quando estiver no Windows.

## Instalar

No PowerShell (usuário normal, não precisa ser administrador):

```powershell
irm https://raw.githubusercontent.com/gabrielxreis/video-redes-skill/main/windows/install.ps1 | iex
```

Instala pelo `winget` o que faltar (ffmpeg, yt-dlp, Node.js LTS, Python 3.12, Git), Pillow, as skills do HyperFrames e de design, as fontes, e confere o DaVinci Resolve Studio. Pode rodar de novo quando quiser.

## Como funciona por baixo

| Peça | O que faz |
|---|---|
| `windows/py/sitecustomize.py` | Entra no `PYTHONPATH` (só no Windows). Aponta a API do Resolve para os caminhos do Windows e traduz `open -a "DaVinci Resolve"` (abre o `Resolve.exe`) e `defaults read` (vazio; a versão sai pela API). Assim `resolve_lib.py`, `transcrever.py` e todos os outros scripts rodam sem mudança. |
| Variáveis de usuário | `RESOLVE_SCRIPT_API`, `RESOLVE_SCRIPT_LIB`, `PYTHONPATH` (Modules do Resolve + `windows/py`) e `PYTHONUTF8=1` (sem isso o Python do Windows lê e grava os .json/.srt em cp1252 e estraga acentos). |
| `windows/bin/python3` e `python3.cmd` | Os docs chamam `python3`; no Windows isso vira `py -3` (Git Bash, cmd e PowerShell). A pasta entra no começo do PATH do usuário, antes do atalho da Microsoft Store. |
| `windows/scripts/movimentos.mjs` | Versão Windows do `scripts/movimentos.mjs` (acha o puppeteer no cache do npx e o Chrome/Edge do Windows). |
| `~/Library/Fonts/Poppins-Bold.ttf` | Cópia que o `legenda_baixa.py` procura nesse caminho fixo (as fontes também são instaladas normalmente no Windows). |

## O que muda no fluxo (o Gab segue isto no Windows)

1. **Python:** usar `python3` normalmente (o atalho resolve). Se aparecer `ModuleNotFoundError: DaVinciResolveScript`, o Claude Code foi aberto antes do instalador: fechar e abrir de novo para pegar as variáveis.
2. **`node scripts/movimentos.mjs` -> `node windows/scripts/movimentos.mjs`** (mesmos argumentos).
3. **`legenda_ui.py` NÃO roda no Windows** (é automação de tela do macOS: Quartz, System Events e OCR da Apple). No lugar dele:
   - **Y 724 da trilha e estilo GAB USA:** vêm do preset de legenda. O usuário aplica o preset **uma vez por timeline** (seleciona a trilha de legenda > Inspector > aba Track > menu de presets do estilo > "GAB USA"; se o preset ainda não existe na máquina, importar o arquivo `GAB USA Subtitle.preset`). Pedir isso a ele na etapa da legenda e esperar o "feito".
   - **Descer legenda para Y 390 sob motion/CTA/lettering:** `legenda_baixa.py` (já é o padrão e não clica em nada; funciona igual).
   - **`--conferir`** (render + altura do texto): conferir pelo `qc.py` e por quadros extraídos com ffmpeg.
4. **Título na V2 (Option+2 no Mac):** não mandar tecla. Usar `timeline_com_letterings()` em timeline nova, ou pedir ao usuário para apertar **Alt+2** na timeline (destino de vídeo na V2) e então rodar `inserir_letterings_na_trilha(t, 2, ...)`.
5. **Conferências por screenshot do DaVinci** (Stacked Timelines ligado, barra de abas): o computer-use do Claude só existe no Mac. No Windows, perguntar ao usuário ("Stacked Timelines está ligado? as abas X, Y, Z estão abertas?") e marcar com `projeto.py marcar <pasta> abas` depois da resposta.
6. **Pacote de lettering (.drfx):** vem no repositório (`assets/lettering/`) e o `install.ps1` copia para `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Templates\` (reiniciar o Resolve depois).
7. **Pastas:** `pasta_saida` em `config.json` pode ficar `~/Desktop`; se a Área de Trabalho estiver no OneDrive, trocar por uma pasta local fixa (ex.: `C:/Videos`) para o OneDrive não deixar mídia "só online" e o DaVinci achar offline. Usar `/` nos caminhos do `config.json`.
8. **Temporários:** não passar caminho `/tmp/...` do Git Bash para o Python (são pastas diferentes no Windows). Usar a pasta do vídeo ou o scratchpad.
9. **Transcrição:** igual (DaVinci 21.1+ pela API). Abaixo disso o Whisper local é o `faster-whisper` (CPU; com placa NVIDIA dá para trocar para CUDA).
10. **Downloads pelo navegador:** iguais (Claude in Chrome); os arquivos caem em `%USERPROFILE%\Downloads`.

## Requisitos

| Item | Versão |
|---|---|
| Windows | 10 ou 11, 64 bits |
| DaVinci Resolve **Studio** | 21.1+ (a versão grátis não tem scripting externo). Preferences > System > General > External scripting using: **Local** |
| Claude Code | com Git Bash (o próprio instalador do Claude Code pede) |
| Google Chrome | com a extensão Claude in Chrome logada |
| Docker Desktop | **não precisa** (o aviso do `hyperframes doctor` pode ser ignorado) |
