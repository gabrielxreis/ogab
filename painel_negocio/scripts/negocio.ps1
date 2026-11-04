# /ogab dashboard no Windows: liga o Meu Negócio do O Gab (CRM, projetos, planner, orçamentos e financeiro)
# neste computador e abre no navegador. Mesmo comportamento do negocio.sh.
# Uso: powershell -ExecutionPolicy Bypass -File negocio.ps1 [abrir [dashboard|crm|projetos|planner|financeiro]|status|parar|resumo|empresa <arquivo.json>]
# Dados: %USERPROFILE%\.ogab\negocio (banco negocio.db + arquivos\). Painel: http://127.0.0.1:3200, só nesta máquina.
param([string]$Acao = "abrir", [string]$Arg = "")
$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$OutputEncoding = [System.Text.Encoding]::UTF8

$App = Split-Path -Parent $PSScriptRoot
$Casa = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
$HomeGab = Join-Path $Casa ".ogab\negocio"
$Porta = if ($env:OGAB_NEGOCIO_PORTA) { $env:OGAB_NEGOCIO_PORTA } else { "3200" }
$Base = "http://127.0.0.1:$Porta"
$PidArq = Join-Path $HomeGab "servidor.pid"
$Log = Join-Path $HomeGab "servidor.log"
$LogErr = Join-Path $HomeGab "servidor.err.log"
New-Item -ItemType Directory -Force -Path $HomeGab | Out-Null

function Pedir([string]$Url, [string]$Metodo = "GET", [string]$Corpo = $null, [int]$Tempo = 15) {
  $p = @{ Uri = $Url; Method = $Metodo; TimeoutSec = $Tempo; UseBasicParsing = $true }
  if ($Corpo) { $p.Body = [System.Text.Encoding]::UTF8.GetBytes($Corpo); $p.ContentType = "application/json; charset=utf-8" }
  $r = Invoke-WebRequest @p
  # conteúdo em bytes para não estragar acento no PowerShell 5.1
  if ($r.RawContentStream) { $r.RawContentStream.Position = 0; return (New-Object IO.StreamReader($r.RawContentStream, [Text.Encoding]::UTF8)).ReadToEnd() }
  return $r.Content
}

function NoAr { try { Pedir "$Base/api/ogab/saude" -Tempo 2 | Out-Null; return $true } catch { return $false } }

function MeuPid {
  if (-not (Test-Path $PidArq)) { return $null }
  $id = (Get-Content $PidArq -Raw).Trim()
  if ($id -and (Get-Process -Id $id -ErrorAction SilentlyContinue)) { return [int]$id }
  return $null
}

function AcharPython {
  # py -3 primeiro; python/python3 só se não for o atalho da Microsoft Store (WindowsApps\python.exe)
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) { return @($py.Source, "-3") }
  foreach ($n in "python", "python3") {
    foreach ($c in @(Get-Command $n -All -ErrorAction SilentlyContinue)) {
      if ($c.Source -and $c.Source -notmatch "WindowsApps") { return @($c.Source) }
    }
  }
  return
}

function Ligar {
  if (NoAr) { return }
  $dist = Join-Path $App "web\dist\index.html"
  if (-not (Test-Path $dist)) { Write-Output "ERRO: painel não montado (falta web\dist)"; exit 1 }
  # @() segura a lista: com um item só o PowerShell devolveria a string e $py[0] seria a primeira letra
  $py = @(AcharPython)
  if ($py.Count -eq 0) { Write-Output "ERRO: precisa do Python 3 (instale pelo python.org ou rode o install.ps1 do Gab)"; exit 1 }
  $env:DADOS = $HomeGab; $env:PORTA = $Porta; $env:WEB = Join-Path $App "web\dist"; $env:PYTHONIOENCODING = "utf-8"
  $argsPy = @()
  if ($py.Count -gt 1) { $argsPy += $py[1..($py.Count - 1)] }
  $argsPy += @("-u", "servidor.py")
  $p = Start-Process -FilePath $py[0] -ArgumentList $argsPy -WorkingDirectory (Join-Path $App "servidor") `
    -WindowStyle Hidden -RedirectStandardOutput $Log -RedirectStandardError $LogErr -PassThru
  Set-Content -Path $PidArq -Value $p.Id -Encoding ascii
  for ($i = 0; $i -lt 40; $i++) { if (NoAr) { Write-Output "Meu Negócio ligado"; return }; Start-Sleep -Milliseconds 500 }
  Write-Output "ERRO: o Meu Negócio não ligou (veja $LogErr)"; exit 1
}

function Status {
  if (NoAr) {
    Write-Output "Meu Negócio: ligado ($Base/dashboard)"
    $id = MeuPid; if ($id) { Write-Output "processo: $id" }
  } else { Write-Output "Meu Negócio: desligado" }
  Write-Output "dados: $HomeGab"
}

function Parar {
  $id = MeuPid
  if ($id) {
    Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
    for ($i = 0; $i -lt 20 -and (MeuPid); $i++) { Start-Sleep -Milliseconds 250 }
    Remove-Item $PidArq -ErrorAction SilentlyContinue
    Write-Output "Meu Negócio desligado."
  } elseif (NoAr) {
    Write-Output "Tem um Meu Negócio no ar na porta $Porta que não foi ligado por este script; não mexi nele."
  } else {
    Remove-Item $PidArq -ErrorAction SilentlyContinue
    Write-Output "Meu Negócio já estava desligado."
  }
}

function Abrir([string]$Destino) {
  if (-not $Destino) { $Destino = "dashboard" }
  if ($Destino -notin @("dashboard", "crm", "projetos", "planner", "financeiro")) {
    Write-Output "destino desconhecido: $Destino (use dashboard, crm, projetos, planner ou financeiro)"; exit 1
  }
  Ligar
  try { Start-Process "$Base/$Destino" | Out-Null } catch {}
  Write-Output "PRONTO: $Base/$Destino"
}

function Resumo { Ligar | Out-Null; Write-Output (Pedir "$Base/api/ogab/resumo") }

function Empresa([string]$Arq) {
  # o Claude manda os dados do negócio que já conhece (nome, CNPJ/CPF, contatos, logo...) para o primeiro acesso
  if (-not $Arq -or -not (Test-Path $Arq)) { Write-Output "uso: negocio.ps1 empresa <arquivo.json>"; exit 1 }
  Ligar | Out-Null
  $corpo = [System.IO.File]::ReadAllText((Resolve-Path $Arq), [System.Text.Encoding]::UTF8)
  Write-Output (Pedir "$Base/api/ogab/empresa" "POST" $corpo)
}

switch ($Acao) {
  "status" { Status ; break }
  "parar" { Parar ; break }
  "resumo" { Resumo ; break }
  "empresa" { Empresa $Arg ; break }
  "abrir" { Abrir $Arg ; break }
  { $_ -in @("dashboard", "crm", "projetos", "planner", "financeiro") } { Abrir $Acao ; break }
  default { Write-Output "uso: negocio.ps1 [abrir [dashboard|crm|projetos|planner|financeiro]|status|parar|resumo|empresa <arquivo.json>]"; exit 1 }
}
