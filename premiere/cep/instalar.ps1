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
