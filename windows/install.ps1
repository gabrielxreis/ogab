# Instalador do Gab (/ogab), o editor de video com IA (Windows 10/11).
# Uso (PowerShell, usuario normal):
#   irm https://raw.githubusercontent.com/gabrielxreis/ogab/main/windows/install.ps1 | iex
# Pode rodar de novo quando quiser: so instala o que faltar e atualiza a skill.
# A versao Mac (install.sh) nao e tocada; tudo do Windows fica em windows/.

& {
$ErrorActionPreference = "Continue"   # Stop + stderr de programa externo derruba o PowerShell 5.1
# Log ao vivo (quem roda pelo Claude Code nao ve a saida ate o fim): Get-Content $env:TEMP\ogab-install.log -Wait
$LOG = Join-Path $env:TEMP "ogab-install.log"
try { Start-Transcript -Path $LOG -Force | Out-Null } catch {}
$REPO = "https://github.com/gabrielxreis/ogab"
$DEST = Join-Path $HOME ".claude\skills\ogab"

function Ok($m)   { Write-Host "  [ok] $m" -ForegroundColor Green }
function Info($m) { Write-Host "`n$m" -ForegroundColor White }
function Warn($m) { Write-Host "  [!] $m" -ForegroundColor Yellow }
function Tem($c)  { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function AtualizaPath {
  $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
}
# py.exe com extensao: no PowerShell nome de comando nao diferencia maiuscula, e "& py" dentro de "function Py"
# chamava a propria funcao para sempre (instalador travado em 100% de CPU, relato de 15/10/2026)
function Py { & py.exe -3 @args }

if ($env:OS -ne "Windows_NT") { Write-Host "Este instalador e para Windows. No Mac use o install.sh."; return }

Info "1/10 winget"
if (-not (Tem winget)) {
  Warn "winget nao encontrado. Instale o 'App Installer' pela Microsoft Store e rode de novo."
  return
}
Ok "winget disponivel"

Info "2/10 ffmpeg, yt-dlp, Node.js, Python 3 e git"
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
Info "3/10 Pacotes Python (Pillow, numpy, OpenCV para o rastreio, requests e dotenv para o Instagram, fontTools para morph e sketch)"
foreach ($par in @(@("PIL", "pillow"), @("numpy", "numpy"), @("cv2", "opencv-python"), @("requests", "requests"), @("dotenv", "python-dotenv"), @("fontTools", "fonttools"))) {
  Py -c "import $($par[0])" 2>$null
  if ($LASTEXITCODE -eq 0) { Ok "$($par[1]) ja instalado" }
  else {
    Py -m pip install --user --quiet $par[1]
    Py -c "import $($par[0])" 2>$null
    if ($LASTEXITCODE -eq 0) { Ok "$($par[1]) instalado" } else { Warn "nao consegui instalar $($par[1]) (o doctor tenta de novo no fim)" }
  }
}

Info "3b/10 Blender (3D de verdade nos motions)"
if (Get-ChildItem (Join-Path $env:ProgramFiles "Blender Foundation") -Directory -ErrorAction SilentlyContinue) { Ok "Blender ja instalado" }
else { winget install --id BlenderFoundation.Blender -e --silent --accept-package-agreements --accept-source-agreements | Out-Null; if ($LASTEXITCODE -eq 0) { Ok "Blender instalado" } else { Warn "nao consegui instalar o Blender: winget install --id BlenderFoundation.Blender -e" } }

Info "3c/10 cc-blender-skill (30 skills de Blender: objetos 3D, materiais, luz, camera; MIT)"
$ccb = Join-Path $HOME ".claude\referencias\cc-blender-skill"; $sk = Join-Path $HOME ".claude\skills"
New-Item -ItemType Directory -Force -Path (Split-Path $ccb), $sk | Out-Null
if (Test-Path (Join-Path $ccb ".git")) { git -C $ccb pull -q 2>$null | Out-Null } else { git clone -q --depth 1 https://github.com/RobLe3/cc-blender-skill.git $ccb 2>$null | Out-Null }
$n = 0
Get-ChildItem (Join-Path $ccb "plugin\skills") -Directory -ErrorAction SilentlyContinue | ForEach-Object {
  if (-not (Test-Path (Join-Path $_.FullName "SKILL.md"))) { return }
  $dst = Join-Path $sk $_.Name
  if ((Test-Path $dst) -and -not (Test-Path (Join-Path $dst ".cc-blender"))) { return }
  if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
  Copy-Item $_.FullName $dst -Recurse; New-Item -ItemType File -Path (Join-Path $dst ".cc-blender") -Force | Out-Null; $n++
}
if ($n -gt 0) { Ok "$n skills de Blender instaladas" } else { Warn "nao consegui instalar o cc-blender-skill (rode o instalador de novo)" }

Info "4/10 Gab (/ogab)"
if (Test-Path (Join-Path $DEST ".git")) {
  git -C $DEST pull --ff-only --quiet
  if ($LASTEXITCODE -eq 0) { Ok "atualizada em $DEST" } else { Warn "nao consegui atualizar (mudanca local?); segue com a versao local" }
} else {
  New-Item -ItemType Directory -Force -Path (Split-Path $DEST) | Out-Null
  git clone --quiet $REPO $DEST
  if (-not (Test-Path (Join-Path $DEST "config.example.json"))) { Warn "nao consegui baixar a skill do GitHub ($REPO). Confira a internet e rode de novo."; return }
  Ok "instalada em $DEST"
}
$cfg = Join-Path $DEST "config.json"
if (Test-Path $cfg) {
  try { Get-Content $cfg -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null }
  catch { Move-Item $cfg "$cfg.quebrado" -Force; Warn "config.json estava invalido: guardei como config.json.quebrado e criei outro" }
}
if (-not (Test-Path $cfg)) { Copy-Item (Join-Path $DEST "config.example.json") $cfg; Ok "config.json criado (fica so na sua maquina)" }
else { Ok "config.json mantido" }

# Editor: cada usuario escolhe UM (DaVinci ou Premiere; CapCut e Final Cut so no Mac) e o Gab trabalha so nele (config.json "editor").
$cfgJ = Get-Content $cfg -Raw -Encoding UTF8 | ConvertFrom-Json
$editor = if ($env:OGAB_EDITOR) { $env:OGAB_EDITOR } elseif ($cfgJ.editor) { $cfgJ.editor } else { "" }
if (-not $editor) {
  Write-Host "`n  Em qual editor o Gab vai montar seus videos?`n    1) DaVinci Resolve Studio`n    2) Adobe Premiere Pro"
  $esc = Read-Host "  Escolha [1/2]"
  $editor = if ($esc -eq "2") { "premiere" } else { "davinci" }
}
if ($editor -notin @("davinci", "premiere")) {
  Warn "CapCut e Final Cut sao so no Mac (beta); no Windows o Gab usa DaVinci ou Premiere. Usando davinci."
  $editor = "davinci"
}
Py -c "import json,sys;p=sys.argv[1];c=json.load(open(p,encoding='utf-8'));c['editor']=sys.argv[2];json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)" $cfg $editor
Ok "editor: $editor (para trocar: /ogab config editor davinci|premiere)"

# Motions: automatico (HyperFrames) ou no After Effects (camadas editaveis). Tudo e instalado; a escolha so diz qual o Gab usa.
$motion = if ($env:OGAB_MOTION) { $env:OGAB_MOTION } elseif ($cfgJ.motion) { $cfgJ.motion } else { "" }
$temAE = Get-ChildItem (Join-Path $env:ProgramFiles "Adobe") -Directory -Filter "Adobe After Effects 20*" -ErrorAction SilentlyContinue
if (-not $motion) {
  Write-Host "`n  Como o Gab faz os motions?`n    1) Automatico (HyperFrames, rapido)`n    2) No After Effects (camadas editaveis: texto, numeros, checks, cores)"
  $escm = Read-Host "  Escolha [1/2]"
  $motion = if ($escm -eq "2") { "aftereffects" } else { "hyperframes" }
}
if (-not $motion) { $motion = "hyperframes" }
Py -c "import json,sys;p=sys.argv[1];c=json.load(open(p,encoding='utf-8'));c['motion']=sys.argv[2];json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)" $cfg $motion
Ok "motions: $motion (para trocar: /ogab config motion hyperframes|aftereffects)"

# Relatos de erro anonimos (pergunta UMA vez; sem resposta "sim" nada sai da maquina). Ver relatos/LEIA.md.
$cfgJ = Get-Content $cfg -Raw -Encoding UTF8 | ConvertFrom-Json
if (($null -eq $cfgJ.relatos) -or (($cfgJ.relatos -eq $true) -and ([int]($cfgJ.relatos_v) -lt 2))) {
  $rel = if ($env:OGAB_RELATOS) { $env:OGAB_RELATOS } else {
    Write-Host "`n  Posso mandar ao Gabriel, de forma ANONIMA, os erros da skill que o Gab corrigir e a estrutura`n  dos motions novos que voce salvar, para ele melhorar o Gab e publicar os melhores para todos?`n  (nada de video, roteiro, texto do cliente, cor da marca, nome ou pasta)."
    Read-Host "  Enviar? [S/n]" }
  if ($rel -match "^[nN]") { Py (Join-Path $DEST "scripts\relatar.py") consentir nao | Out-Null; Ok "relatos: nao (para ligar: /ogab config relatos sim)" }
  else { Py (Join-Path $DEST "scripts\relatar.py") consentir sim | Out-Null; Ok "relatos anonimos: sim (para desligar: /ogab config relatos nao)" }
}

Info "5/10 Ambiente do Windows (Resolve, Python, atalho python3)"
$api  = Join-Path $env:PROGRAMDATA "Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
$appd = Join-Path $env:ProgramFiles "Blackmagic Design\DaVinci Resolve"
# DaVinci fora do C:\Program Files (ex.: D:\DaVinci, relato de 15/10/2026): acha pelo processo aberto, pelo atalho do
# Menu Iniciar ou pelo registro de desinstalacao; fica a primeira pasta que tem o fusionscript.dll.
if (-not (Test-Path (Join-Path $appd "fusionscript.dll"))) {
  $cands = @()
  $proc = Get-Process Resolve -ErrorAction SilentlyContinue | Where-Object { $_.Path } | Select-Object -First 1
  if ($proc) { $cands += Split-Path $proc.Path }
  $sh = New-Object -ComObject WScript.Shell
  foreach ($menu in (Join-Path $env:ProgramData "Microsoft\Windows\Start Menu\Programs"), (Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs")) {
    Get-ChildItem $menu -Recurse -Filter "DaVinci Resolve*.lnk" -ErrorAction SilentlyContinue | ForEach-Object {
      $alvo = $sh.CreateShortcut($_.FullName).TargetPath; if ($alvo) { $cands += Split-Path $alvo } }
  }
  foreach ($k in "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*", "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*") {
    Get-ItemProperty $k -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -like "DaVinci Resolve*" -and $_.InstallLocation } |
      ForEach-Object { $cands += $_.InstallLocation.TrimEnd("\") }
  }
  $achou = $cands | Where-Object { $_ -and (Test-Path (Join-Path $_ "fusionscript.dll")) } | Select-Object -First 1
  if ($achou) { $appd = $achou; Ok "DaVinci encontrado fora do padrao: $appd" }
}
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

Info "6/10 HyperFrames e skills de design"
function Npx($desc, $cmd) {
  cmd /c "$cmd >nul 2>&1"
  if ($LASTEXITCODE -eq 0) { Ok $desc } else { Warn "rode depois: $cmd" }
}
Npx "skills do HyperFrames instaladas" "npx --yes skills add heygen-com/hyperframes -g -a claude-code -s * -y"
Npx "hyperframes doctor ok" "npx --yes hyperframes doctor"
Py (Join-Path $DEST "instagram\carrossel\carrossel.py") instalar *> $null
if ($LASTEXITCODE -eq 0) { Ok "carrossel do Instagram pronto (slides PNG/PDF)" } else { Warn "rode depois: py -3 $DEST\instagram\carrossel\carrossel.py instalar" }
Npx "taste-skill (design-taste-frontend, image-to-code) instaladas" "npx --yes skills add leonxlnx/taste-skill -g -a claude-code -s design-taste-frontend -s image-to-code -y"
Npx "web-design-guidelines instalada" "npx --yes skills add vercel-labs/agent-skills -g -a claude-code -s web-design-guidelines -y"
$temPw = Tem playwright-cli
if (-not $temPw) { cmd /c "npm install -g @playwright/cli@latest >nul 2>&1"; $temPw = ($LASTEXITCODE -eq 0) }
if ($temPw) {
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
$insp = Join-Path $HOME ".claude\referencias\awesome-opus5-5-videos"
if (Test-Path (Join-Path $insp ".git")) { git -C $insp pull -q 2>$null | Out-Null; Ok "awesome-opus5-5-videos atualizado" }
else {
  git clone --depth 1 -q https://github.com/yihui-dev/awesome-opus5-5-videos.git $insp 2>$null | Out-Null
  if ($LASTEXITCODE -eq 0) { Ok "awesome-opus5-5-videos (inspiracao de motions) em ~/.claude/referencias" } else { Warn "nao consegui clonar o awesome-opus5-5-videos" }
}

Info "7/10 Fontes (Poppins, Playfair Display, Lobster, licenca OFL)"
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

# Lettering animado: pacote @gabrielxreis_ Text Presets (titulos do Fusion) na pasta de Templates do DaVinci
$tpl = Join-Path $env:APPDATA "Blackmagic Design\DaVinci Resolve\Support\Fusion\Templates"
New-Item -ItemType Directory -Force -Path $tpl | Out-Null
Get-ChildItem -Path (Join-Path $DEST "assets\lettering") -Filter *.drfx -ErrorAction SilentlyContinue | ForEach-Object {
  Copy-Item $_.FullName (Join-Path $tpl $_.Name) -Force
  Ok "lettering $($_.Name) instalado (reinicie o DaVinci)"
}
# Titulos OGraf do Gab (HTML editavel no Inspector, DaVinci 21+): cada pasta de ograf\ vira um titulo em Titles\OGraf
$ogd = Join-Path $tpl "Edit\Titles\OGraf"; New-Item -ItemType Directory -Force -Path $ogd | Out-Null
Get-ChildItem -Path (Join-Path $DEST "ograf") -Directory -ErrorAction SilentlyContinue | ForEach-Object {
  if (Get-ChildItem -Path $_.FullName -Filter *.ograf.json -ErrorAction SilentlyContinue) {
    Copy-Item -Recurse -Force $_.FullName $ogd; Ok "titulo OGraf $($_.Name) instalado (reinicie o DaVinci)"
  }
}


# LUT DO GAB na pasta de LUTs do DaVinci (ProgramData)
$lutD = Join-Path $env:PROGRAMDATA "Blackmagic Design\DaVinci Resolve\Support\LUT\LUT DO GAB"
$lutS = Join-Path $DEST "premiere\assets\lut\LUT DO GAB.cube"
if (Test-Path $lutS) {
  try { New-Item -ItemType Directory -Force -Path $lutD -ErrorAction Stop | Out-Null; Copy-Item $lutS $lutD -Force -ErrorAction Stop; Ok "LUT DO GAB na pasta de LUTs do DaVinci" }
  catch { Warn "nao consegui copiar a LUT para o DaVinci (sem permissao em ProgramData); copie '$lutS' para '$lutD' como administrador" }
}

Info "8/10 DaVinci Resolve e transcricao"
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
  } else { Warn "DaVinci ${ver}: abaixo da 21.1 a API nao devolve a transcricao; vou instalar o Whisper local (gratis)" }
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
  # Placa NVIDIA: bibliotecas CUDA do Whisper na GPU (sem elas: "cublas64_12.dll not found"; relato de 15/10/2026).
  # A camada windows\py registra as pastas bin delas sozinha; sem NVIDIA o Whisper roda na CPU.
  $nv = Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "NVIDIA" }
  if ($nv) {
    Py -m pip install --user --quiet nvidia-cublas-cu12 nvidia-cudnn-cu12
    if ($LASTEXITCODE -eq 0) { Ok "Whisper na GPU ($($nv[0].Name)): bibliotecas CUDA instaladas" }
    else { Warn "Whisper vai rodar na CPU (mais lento); para a GPU: py -3 -m pip install --user nvidia-cublas-cu12 nvidia-cudnn-cu12" }
  }
}

# Teste rapido: a camada do Windows carrega e acha a API do Resolve.
Py -c "import os, DaVinciResolveScript; print('  [ok] API do Resolve importada (', os.environ['RESOLVE_SCRIPT_LIB'], ')')" 2>$null
if ($LASTEXITCODE -ne 0) { Warn "a API do Resolve ainda nao importa; confira o Resolve Studio instalado e abra um terminal novo" }

# Tudo e instalado em toda maquina; config.json (editor e motion) so diz qual app o Gab usa.
$env:OGAB_SEM_CONFIG = "1"
Info "9/10 Adobe Premiere Pro (plugin Gab Ponte, LUT e letterings)"
& powershell -ExecutionPolicy Bypass -File (Join-Path $DEST "premiere\instalar.ps1")
Info "10/10 After Effects (extensao Gab Ponte AE, motions editaveis)"
& powershell -ExecutionPolicy Bypass -File (Join-Path $DEST "aftereffects\instalar.ps1")
$env:OGAB_SEM_CONFIG = ""

Info "Conferencia final (doctor: confere tudo e corrige o que der)"
Py (Join-Path $DEST "scripts\doctor.py") --corrigir

Write-Host @"

Pronto. Seu Gab vai editar no: $editor   |   motions: $motion
(trocar a qualquer hora: /ogab config editor davinci|premiere  e  /ogab config motion hyperframes|aftereffects)

Falta so o que precisa de voce (uma vez), no app que voce usa:
  DaVinci:        Preferences > System > General > External scripting using: Local (e reinicie o Resolve).
                  Reinicie o DaVinci para carregar o lettering (@gabrielxreis_ Text Presets, ja instalado em %APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Templates\).
                  Preset de legenda GAB USA: vem junto (assets\davinci\GAB USA Subtitle.preset); o Gab importa no DaVinci na 1a legenda.
  Premiere:       Window > UXP Plugins > Gab Ponte (deixe o painel encaixado).
  After Effects:  nada: a ponte sobe sozinha (se o AE estava aberto durante a instalacao, feche e rode o instalador de novo).
  Todos:          conecte as SUAS contas no Claude (Configuracoes > Conectores): ElevenLabs, Artlist, Envato, Magnific...
                  e a extensao Claude in Chrome logada nos sites (downloads sao pelo navegador).

FECHE e abra de novo o Claude Code (para pegar as variaveis novas) e digite:  /ogab comecar
Diferencas do Windows: ~/.claude/skills/ogab/windows/README.md
Log desta instalacao: $LOG
"@
try { Stop-Transcript | Out-Null } catch {}
}
