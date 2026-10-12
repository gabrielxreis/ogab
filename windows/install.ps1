# Instalador do Gab (/ogab), o editor de video com IA (Windows 10/11).
# Uso (PowerShell, usuario normal):
#   irm https://raw.githubusercontent.com/gabrielxreis/video-redes-skill/main/windows/install.ps1 | iex
# Pode rodar de novo quando quiser: so instala o que faltar e atualiza a skill.
# A versao Mac (install.sh) nao e tocada; tudo do Windows fica em windows/.

$ErrorActionPreference = "Continue"   # Stop + stderr de programa externo derruba o PowerShell 5.1
$REPO = "https://github.com/gabrielxreis/video-redes-skill"
$DEST = Join-Path $HOME ".claude\skills\ogab"

function Ok($m)   { Write-Host "  [ok] $m" -ForegroundColor Green }
function Info($m) { Write-Host "`n$m" -ForegroundColor White }
function Warn($m) { Write-Host "  [!] $m" -ForegroundColor Yellow }
function Tem($c)  { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function AtualizaPath {
  $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
}
function Py { & py -3 @args }

if ($env:OS -ne "Windows_NT") { Write-Host "Este instalador e para Windows. No Mac use o install.sh."; exit 1 }

Info "1/8 winget"
if (-not (Tem winget)) {
  Warn "winget nao encontrado. Instale o 'App Installer' pela Microsoft Store e rode de novo."
  exit 1
}
Ok "winget disponivel"

Info "2/8 ffmpeg, yt-dlp, Node.js, Python 3 e git"
$pacotes = @(
  @{ bin = "ffmpeg"; id = "Gyan.FFmpeg" },
  @{ bin = "yt-dlp"; id = "yt-dlp.yt-dlp" },
  @{ bin = "node";   id = "OpenJS.NodeJS.LTS" },
  @{ bin = "py";     id = "Python.Python.3.12" },
  @{ bin = "git";    id = "Git.Git" }
)
foreach ($p in $pacotes) {
  if (Tem $p.bin) { Ok "$($p.bin) ja instalado"; continue }
  winget install --id $p.id -e --silent --accept-package-agreements --accept-source-agreements --scope user 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) { winget install --id $p.id -e --silent --accept-package-agreements --accept-source-agreements | Out-Null }
  AtualizaPath
  if (Tem $p.bin) { Ok "$($p.bin) instalado" } else { Warn "nao consegui instalar $($p.id); rode: winget install --id $($p.id) -e" }
}
if (-not (Tem py)) { Warn "sem Python ('py'): instale o Python 3.12 e rode de novo."; exit 1 }

Info "3/8 Pillow (Python)"
Py -c "import PIL" 2>$null
if ($LASTEXITCODE -eq 0) { Ok "Pillow ja instalado" } else { Py -m pip install --user --quiet pillow; Ok "Pillow instalado" }

Info "4/8 Gab (/ogab)"
if (Test-Path (Join-Path $DEST ".git")) {
  git -C $DEST pull --ff-only --quiet
  if ($LASTEXITCODE -eq 0) { Ok "atualizada em $DEST" } else { Warn "nao consegui atualizar (mudanca local?); segue com a versao local" }
} else {
  New-Item -ItemType Directory -Force -Path (Split-Path $DEST) | Out-Null
  git clone --quiet $REPO $DEST
  Ok "instalada em $DEST"
}
$cfg = Join-Path $DEST "config.json"
if (-not (Test-Path $cfg)) { Copy-Item (Join-Path $DEST "config.example.json") $cfg; Ok "config.json criado (fica so na sua maquina)" }
else { Ok "config.json mantido" }

Info "5/8 Ambiente do Windows (Resolve, Python, atalho python3)"
$api  = Join-Path $env:PROGRAMDATA "Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
$appd = Join-Path $env:ProgramFiles "Blackmagic Design\DaVinci Resolve"
$lib  = Join-Path $appd "fusionscript.dll"
$winpy  = Join-Path $DEST "windows\py"
$winbin = Join-Path $DEST "windows\bin"
[Environment]::SetEnvironmentVariable("RESOLVE_SCRIPT_API", $api, "User")
[Environment]::SetEnvironmentVariable("RESOLVE_SCRIPT_LIB", $lib, "User")
[Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "User")
$pp = [Environment]::GetEnvironmentVariable("PYTHONPATH", "User")
$partes = @($winpy, (Join-Path $api "Modules")) + @(($pp -split ";") | Where-Object { $_ -and $_ -ne $winpy -and $_ -ne (Join-Path $api "Modules") })
[Environment]::SetEnvironmentVariable("PYTHONPATH", ($partes -join ";"), "User")
$up = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not (($up -split ";") -contains $winbin)) {
  [Environment]::SetEnvironmentVariable("Path", "$winbin;$up", "User")
}
$env:RESOLVE_SCRIPT_API = $api; $env:RESOLVE_SCRIPT_LIB = $lib; $env:PYTHONUTF8 = "1"
$env:PYTHONPATH = ($partes -join ";"); AtualizaPath
Ok "variaveis RESOLVE_SCRIPT_API, RESOLVE_SCRIPT_LIB, PYTHONPATH e PYTHONUTF8 gravadas"
Ok "python3 -> py -3 (windows\bin no comeco do PATH)"

# Aviso para o Gab ler o guia do Windows (no CLAUDE.md do usuario, fora do repositorio).
$claudeMd = Join-Path $HOME ".claude\CLAUDE.md"
$marca = "ogab/windows/README.md"
$linha = "- Windows: ao usar a skill /ogab, ler antes ~/.claude/skills/$marca (diferencas do Windows: legenda_ui.py nao roda, movimentos.mjs da pasta windows, Alt+2 em vez de Option+2, sem screenshot do DaVinci)."
if (-not (Test-Path $claudeMd) -or -not (Select-String -Path $claudeMd -SimpleMatch $marca -Quiet)) {
  Add-Content -Path $claudeMd -Value "`n$linha" -Encoding UTF8
  Ok "aviso do Windows adicionado em ~/.claude/CLAUDE.md"
} else { Ok "aviso do Windows ja esta no ~/.claude/CLAUDE.md" }

Info "6/8 HyperFrames e skills de design"
function Npx($desc, $cmd) {
  cmd /c "$cmd >nul 2>&1"
  if ($LASTEXITCODE -eq 0) { Ok $desc } else { Warn "rode depois: $cmd" }
}
Npx "skills do HyperFrames instaladas" "npx --yes skills add heygen-com/hyperframes -g -a claude-code -s * -y"
Npx "hyperframes doctor ok" "npx --yes hyperframes doctor"
Npx "taste-skill (design-taste-frontend, image-to-code) instaladas" "npx --yes skills add leonxlnx/taste-skill -g -a claude-code -s design-taste-frontend -s image-to-code -y"
Npx "web-design-guidelines instalada" "npx --yes skills add vercel-labs/agent-skills -g -a claude-code -s web-design-guidelines -y"
if ((Tem playwright-cli) -or ((cmd /c "npm install -g @playwright/cli@latest >nul 2>&1"); $LASTEXITCODE -eq 0)) {
  AtualizaPath
  Push-Location $HOME; Npx "playwright-cli + skill instalados" "playwright-cli install --skills"; Pop-Location
} else { Warn "nao consegui instalar o playwright-cli; rode: npm install -g @playwright/cli@latest" }
Npx "REA (reverse-engineer-anything) skill instalada" "npx --yes skills add morluto/rea -g -a claude-code -s reverse-engineer-anything -y"
Npx "REA MCP registrado no Claude Code" "npx --yes rea-agents setup --client claude_code --yes"
$ref = Join-Path $HOME ".claude\referencias\awesome-design-md"
if (Test-Path (Join-Path $ref ".git")) { git -C $ref pull -q 2>$null | Out-Null; Ok "awesome-design-md atualizado" }
else {
  New-Item -ItemType Directory -Force -Path (Split-Path $ref) | Out-Null
  git clone --depth 1 -q https://github.com/voltagent/awesome-design-md.git $ref 2>$null | Out-Null
  if ($LASTEXITCODE -eq 0) { Ok "awesome-design-md em ~/.claude/referencias" } else { Warn "nao consegui clonar o awesome-design-md" }
}

Info "7/8 Fontes (Poppins, Playfair Display, Lobster, licenca OFL)"
$fontesUser = Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Fonts"
New-Item -ItemType Directory -Force -Path $fontesUser | Out-Null
$reg = "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts"
if (-not (Test-Path $reg)) { New-Item -Path $reg -Force | Out-Null }
$n = 0
Get-ChildItem -Path (Join-Path $DEST "assets\fontes") -Recurse -Include *.ttf, *.otf | ForEach-Object {
  $alvo = Join-Path $fontesUser $_.Name
  if (-not (Test-Path $alvo)) {
    Copy-Item $_.FullName $alvo
    $tipo = if ($_.Extension -eq ".otf") { "OpenType" } else { "TrueType" }
    New-ItemProperty -Path $reg -Name "$($_.BaseName) ($tipo)" -Value $alvo -PropertyType String -Force | Out-Null
    $n++
  }
}
Ok "$n fonte(s) nova(s) instalada(s) (reabra o DaVinci para ele ver)"
# O legenda_baixa.py procura a Poppins Bold num caminho fixo do Mac (~/Library/Fonts); a copia fica la tambem.
$libFonts = Join-Path $HOME "Library\Fonts"
New-Item -ItemType Directory -Force -Path $libFonts | Out-Null
Copy-Item (Join-Path $DEST "assets\fontes\Poppins\Poppins-Bold.ttf") (Join-Path $libFonts "Poppins-Bold.ttf") -Force
Ok "Poppins-Bold tambem em ~/Library/Fonts (usada pelo legenda_baixa.py)"

Info "8/8 DaVinci Resolve e transcricao"
$exe = Join-Path $appd "Resolve.exe"
$precisaWhisper = $true
if (Test-Path $exe) {
  $ver = (Get-Item $exe).VersionInfo.ProductVersion
  $v = @(($ver -split "[^\d]+") | Where-Object { $_ -ne "" } | ForEach-Object { [int]$_ }) + @(0, 0, 0)
  Ok "DaVinci Resolve $ver encontrado"
  if (Test-Path $lib) { Ok "biblioteca de scripting encontrada" }
  else { Warn "fusionscript.dll nao encontrado: a skill precisa do DaVinci Resolve STUDIO" }
  if (-not (Test-Path (Join-Path $api "Modules"))) { Warn "pasta da API nao encontrada em $api (reinstale o Resolve Studio)" }
  if ($v[0] -gt 21 -or ($v[0] -eq 21 -and $v[1] -ge 1)) {
    $precisaWhisper = $false; Ok "o DaVinci $ver transcreve sozinho: Whisper nao e necessario"
  } else { Warn "DaVinci $ver: abaixo da 21.1 a API nao devolve a transcricao; vou instalar o Whisper local (gratis)" }
  if ($v[0] -lt 20 -or ($v[0] -eq 20 -and ($v[1] -lt 2 -or ($v[1] -eq 2 -and $v[2] -lt 2)))) {
    Warn "abaixo da 20.2.2 o DaVinci pode errar a trilha ao colocar narracao e musica; o ideal e a 21.1+"
  }
} else {
  Warn "DaVinci Resolve nao encontrado em $appd. Instale o DaVinci Resolve Studio 21.1+: https://www.blackmagicdesign.com/products/davinciresolve"
}
if ($precisaWhisper) {
  Py -c "import faster_whisper" 2>$null
  if ($LASTEXITCODE -eq 0) { Ok "Whisper local (faster-whisper) ja instalado" }
  else {
    Py -m pip install --user --quiet faster-whisper
    Py -c "import faster_whisper" 2>$null
    if ($LASTEXITCODE -eq 0) { Ok "faster-whisper instalado; o modelo (~1,6 GB) baixa na primeira transcricao" }
    else { Warn "nao consegui instalar o faster-whisper; rode: py -3 -m pip install --user faster-whisper" }
  }
}

# Teste rapido: a camada do Windows carrega e acha a API do Resolve.
Py -c "import os, DaVinciResolveScript; print('  [ok] API do Resolve importada (', os.environ['RESOLVE_SCRIPT_LIB'], ')')" 2>$null
if ($LASTEXITCODE -ne 0) { Warn "a API do Resolve ainda nao importa; confira o Resolve Studio instalado e abra um terminal novo" }

Write-Host @"

Pronto. Falta so o que precisa de voce (uma vez):
  1. No DaVinci: Preferences > System > General > External scripting using: Local (e reinicie o Resolve).
  2. Conectar as SUAS contas no Claude (Configuracoes > Conectores): ElevenLabs, Artlist, Envato, Magnific... so o que usar.
  3. Instalar a extensao Claude in Chrome e fazer login nos sites (downloads sao pelo navegador).
  4. Opcional: seu pacote de lettering (.drfx) em
     %APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Templates\
  5. Opcional: Higgsfield e Magnific logados no Chrome (imagem e video de IA no ilimitado, pelo site).

FECHE e abra de novo o Claude Code (para pegar as variaveis novas) e digite:  /ogab comecar
Diferencas do Windows: ~/.claude/skills/ogab/windows/README.md
"@
