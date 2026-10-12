# Instala a parte do Premiere do Gab (/ogab) no Windows: plugin Gab Ponte, LUT e letterings (.mogrt).
# Uso (PowerShell): powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\ogab\premiere\instalar.ps1"
# Rodar depois do windows\install.ps1. Pode rodar de novo quando quiser.

$ErrorActionPreference = "Continue"
$AQUI = Split-Path -Parent $MyInvocation.MyCommand.Path
function Ok($m)   { Write-Host "  [ok] $m" -ForegroundColor Green }
function Info($m) { Write-Host "`n$m" -ForegroundColor White }
function Warn($m) { Write-Host "  [!] $m" -ForegroundColor Yellow }

Info "1/4 Premiere Pro"
$pr = Get-ChildItem (Join-Path $env:ProgramFiles "Adobe") -Directory -Filter "Adobe Premiere Pro 20*" -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
if ($pr) {
  $exe = Join-Path $pr.FullName "Adobe Premiere Pro.exe"
  $ver = if (Test-Path $exe) { (Get-Item $exe).VersionInfo.ProductVersion } else { "?" }
  Ok "$($pr.Name) $ver"
  if ($ver -match "^(\d+)" -and [int]$Matches[1] -lt 26) { Warn "a ponte precisa do Premiere 2026 (26.x) ou mais novo: atualize pelo Creative Cloud" }
} else { Warn "Premiere Pro nao encontrado em Program Files\Adobe (instale o Premiere Pro 2026+ pelo Creative Cloud)" }

Info "2/4 Plugin Gab Ponte (liga o Premiere ao /ogab)"
$zip = Join-Path $env:TEMP "GabPonte.zip"; $ccx = Join-Path $env:TEMP "GabPonte.ccx"
Remove-Item $zip, $ccx -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $AQUI "plugin\*") -DestinationPath $zip -Force
Move-Item $zip $ccx -Force
$upia = Join-Path ${env:CommonProgramFiles} "Adobe\Adobe Desktop Common\RemoteComponents\UPI\UnifiedPluginInstallerAgent\UnifiedPluginInstallerAgent.exe"
$instalado = $false
if (Test-Path $upia) {
  & $upia /install $ccx | Out-Null
  $instalado = ($LASTEXITCODE -eq 0)
}
if ($instalado) { Ok "plugin instalado (Premiere: Window > UXP Plugins > Gab Ponte)" }
else { Warn "o instalador da Adobe nao aceitou o plugin. Alternativa: UXP Developer Tool (Creative Cloud) > Add Plugin > $AQUI\plugin\manifest.json > Load" }

Info "3/4 LUT de cor"
$n = 0
foreach ($d in "Technical", "Creative") {
  $dst = Join-Path $env:APPDATA "Adobe\Common\LUTs\$d"
  New-Item -ItemType Directory -Force -Path $dst | Out-Null
  Get-ChildItem (Join-Path $AQUI "assets\lut") -Filter *.cube -ErrorAction SilentlyContinue | ForEach-Object { Copy-Item $_.FullName $dst -Force; $n++ }
}
if ($n -gt 0) { Ok "LUT(s) em %APPDATA%\Adobe\Common\LUTs (Technical = Input LUT, Creative = Look)" }
else { Warn "nenhum .cube em premiere\assets\lut (coloque o LUT DO GAB.cube la e rode de novo)" }

Info "4/4 Lettering animado (.mogrt)"
$mg = Join-Path $env:APPDATA "Adobe\Common\Motion Graphics Templates"
New-Item -ItemType Directory -Force -Path $mg | Out-Null
$m = @(Get-ChildItem (Join-Path $AQUI "assets\mogrt") -Filter *.mogrt -ErrorAction SilentlyContinue)
$m | ForEach-Object { Copy-Item $_.FullName $mg -Force }
if ($m.Count -gt 0) { Ok "$($m.Count) MOGRT(s) instalados" } else { Warn "nenhum .mogrt em premiere\assets\mogrt ainda (lettering fica para quando existir)" }

# Quem roda este instalador escolheu o Premiere: grava no config.json (o Gab trabalha so nele).
$cfg = Join-Path $AQUI "..\config.json"
if (-not (Test-Path $cfg)) { Copy-Item (Join-Path $AQUI "..\config.example.json") $cfg }
& py -3 -c "import json,sys;p=sys.argv[1];c=json.load(open(p,encoding='utf-8'));c['editor']='premiere';json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)" $cfg
Ok "config.json: editor = premiere"

$cm = Join-Path $HOME ".claude\CLAUDE.md"; $marca = "ogab/premiere/README.md"
if (-not (Test-Path $cm) -or -not (Select-String -Path $cm -SimpleMatch $marca -Quiet)) {
  Add-Content -Path $cm -Encoding UTF8 -Value "`n- Premiere: quando o /ogab for editar no Adobe Premiere (config.json `"editor`": `"premiere`" ou pedido do usuario), ler antes ~/.claude/skills/$marca (premiere_lib.py no lugar do resolve_lib.py)."
  Ok "aviso do Premiere adicionado em ~/.claude/CLAUDE.md"
}

Write-Host @"

Pronto. No Premiere, uma vez: Window > UXP Plugins > Gab Ponte (deixe o painel encaixado; ele mostra "conectado").
Para o Gab editar no Premiere por padrao:  /ogab config editor premiere
"@
