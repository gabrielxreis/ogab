# Deixa o /ogab disponivel no Codex do Windows (CLI e app). Uma instalacao so: o Codex usa a mesma pasta do Claude Code.
#   powershell -ExecutionPolicy Bypass -File $HOME\.claude\skills\ogab\codex\instalar.ps1
# Copia o carregador do Codex para %USERPROFILE%\.codex\skills\ogab\SKILL.md (copia de verdade: o Codex ignora link;
# o atualizar.py renova a copia a cada update do Gab). Nao mexe no sandbox do Codex.
$SKILL = Join-Path $HOME ".claude\skills\ogab"
$CODEX = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$DEST = Join-Path $CODEX "skills\ogab"
$FONTE = Join-Path $SKILL "codex\SKILL.md"

if (-not (Test-Path $FONTE)) { Write-Host "  [!] /ogab nao esta em $SKILL (rode o install.ps1 do Gab antes)" -ForegroundColor Yellow; exit 1 }
New-Item -ItemType Directory -Force -Path $DEST | Out-Null
Copy-Item $FONTE (Join-Path $DEST "SKILL.md") -Force
Write-Host "  [ok] instalado no Codex (chame com `$ogab)" -ForegroundColor Green
if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
  Write-Host "  [!] comando codex nao encontrado; instale o Codex (o app ja serve) e abra de novo" -ForegroundColor Yellow
}
