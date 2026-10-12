# Instala a parte do After Effects do Gab (/ogab) no Windows: extensao invisivel Gab Ponte AE e a permissao de scripts.
# Uso (PowerShell, com o After Effects FECHADO):
#   powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\ogab\aftereffects\instalar.ps1"
# OGAB_SEM_CONFIG=1 nao grava a escolha no config.json (o instalador principal ja gravou).

$ErrorActionPreference = "Continue"
$AQUI = Split-Path -Parent $MyInvocation.MyCommand.Path
function Ok($m)   { Write-Host "  [ok] $m" -ForegroundColor Green }
function Info($m) { Write-Host "`n$m" -ForegroundColor White }
function Warn($m) { Write-Host "  [!] $m" -ForegroundColor Yellow }

Info "1/4 After Effects"
$ae = Get-ChildItem (Join-Path $env:ProgramFiles "Adobe") -Directory -Filter "Adobe After Effects 20*" -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
if (-not $ae) { Warn "After Effects nao encontrado em Program Files\Adobe (instale pelo Creative Cloud)"; exit 1 }
$exe = Join-Path $ae.FullName "Support Files\AfterFX.exe"
$ver = if (Test-Path $exe) { (Get-Item $exe).VersionInfo.ProductVersion } else { "?" }
Ok "$($ae.Name) $ver"
if (Get-Process -Name "AfterFX" -ErrorAction SilentlyContinue) { Warn "feche o After Effects antes e rode de novo"; exit 1 }

Info "2/4 Extensao Gab Ponte AE (invisivel, sobe sozinha com o AE)"
foreach ($v in 9..14) {
  $k = "HKCU:\Software\Adobe\CSXS.$v"
  if (-not (Test-Path $k)) { New-Item -Path $k -Force | Out-Null }
  Set-ItemProperty -Path $k -Name "PlayerDebugMode" -Value "1"
}
$dst = Join-Path $env:APPDATA "Adobe\CEP\extensions\com.gabrielxreis.ogab.aeponte"
if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
Copy-Item (Join-Path $AQUI "cep") $dst -Recurse
Ok "extensao em %APPDATA%\Adobe\CEP\extensions (extensoes sem assinatura liberadas)"

Info "3/4 Permissao de scripts do AE (gravar arquivos: quadros, render, MOGRT)"
$maj = ($ver -split "\.")[0..1] -join "."
$n = 0
Get-ChildItem (Join-Path $env:APPDATA "Adobe\After Effects\$maj") -Filter *.txt -ErrorAction SilentlyContinue | ForEach-Object {
  $txt = [IO.File]::ReadAllText($_.FullName)
  if ($txt -match "Pref_SCRIPTING_FILE_NETWORK_SECURITY") {
    $txt = [regex]::Replace($txt, '("Pref_SCRIPTING_FILE_NETWORK_SECURITY" = )"?\w+"?', '$1"1"')
    [IO.File]::WriteAllText($_.FullName, $txt); $n++
  }
}
if ($n -gt 0) { Ok "'Permitir que scripts gravem arquivos e acessem a rede' ligado" }
else { Warn "abra o AE uma vez, feche e rode de novo (ou ligue em Preferencias > Scripts e expressoes)" }

Info "4/4 Fontes"
if (Test-Path (Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Fonts\Poppins-Bold.ttf")) { Ok "Poppins instalada" } else { Warn "rode o windows\install.ps1 da skill para instalar as fontes" }

if ($env:OGAB_SEM_CONFIG -ne "1") {
  $cfg = Join-Path $AQUI "..\config.json"
  if (-not (Test-Path $cfg)) { Copy-Item (Join-Path $AQUI "..\config.example.json") $cfg }
  & py -3 -c "import json,sys;p=sys.argv[1];c=json.load(open(p,encoding='utf-8'));c['motion']='aftereffects';json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)" $cfg
  Ok "config.json: motion = aftereffects"
}

Write-Host @"

Pronto. Abra o After Effects normalmente: a ponte sobe sozinha (nao tem painel para abrir).
Para voltar aos motions automaticos (HyperFrames):  /ogab config motion hyperframes
"@
