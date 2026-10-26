# Instala a extensão "Gab Ponte PPro" (CEP) para o Premiere Pro 2018 a 25.x. Sem admin: pasta do usuário.
# Depois disso, basta (re)abrir o Premiere: a ponte inicia sozinha.
$ErrorActionPreference = "Stop"
$origem = Join-Path $PSScriptRoot "plugin"
$destino = Join-Path $env:APPDATA "Adobe\CEP\extensions\com.gabrielxreis.ogab.ppronte"

# Extensão sem assinatura: liga o PlayerDebugMode nas versões do CEP que o Premiere usa (8 = 2018, 9 = 2019 ... 12 = 2024/25).
foreach ($v in 8..12) {
  $chave = "HKCU:\Software\Adobe\CSXS.$v"
  if (-not (Test-Path $chave)) { New-Item -Path $chave -Force | Out-Null }
  Set-ItemProperty -Path $chave -Name PlayerDebugMode -Value "1" -Type String
}

if (Test-Path $destino) { Remove-Item -Recurse -Force $destino }
Copy-Item -Recurse $origem $destino
Write-Host "Gab Ponte PPro instalada em $destino. Feche e abra o Premiere para ela iniciar."

# LUT do Gab: o Lumetri do 13.x só lista LUTs da pasta da instalação (não lê %APPDATA%\Adobe\Common\LUTs).
# Essa pasta fica em Program Files: precisa rodar este instalador como administrador.
$cubo = Join-Path $env:USERPROFILE ".claude\skills\ogab\premiere\assets\lut\LUT DO GAB.cube"
$pprs = Get-ChildItem (Join-Path $env:ProgramFiles "Adobe") -Directory -Filter "Adobe Premiere Pro*" -ErrorAction SilentlyContinue
foreach ($p in $pprs) {
  $dst = Join-Path $p.FullName "Lumetri\LUTs\Creative"
  if (-not (Test-Path $dst) -or -not (Test-Path $cubo)) { continue }
  try {
    Copy-Item $cubo $dst -Force -ErrorAction Stop
    Write-Host "LUT DO GAB copiado para $dst (reabra o Premiere)."
  } catch {
    Write-Host "Sem permissão para $dst. Rode de novo como administrador para o LUT do Gab aparecer no Lumetri." -ForegroundColor Yellow
  }
}
