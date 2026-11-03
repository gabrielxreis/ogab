#!/usr/bin/env bash
# Motor de tráfego do Gab (/ogab trafego): instala ou atualiza o claude-ads (sub-skills ads-* e agentes audit-*) (macOS).
# Uso:  bash ~/.claude/skills/ogab/trafego/install.sh
# Pode rodar de novo quando quiser.
set -euo pipefail
# Pacote Python solto em ~/Library/Python (ex.: Pillow de outra versão) quebra a conferência das dependências do claude-ads.
export PYTHONNOUSERSITE=1

DEST="$(cd "$(dirname "$0")" && pwd)"

ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
info() { printf "\n\033[1m%s\033[0m\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }

info "1/2 Motor claude-ads (auditoria, plano, criativo: 33 sub-skills e 25 agentes)"
# O claude-ads só tem dependências conferidas (com hash) para Python 3.10 a 3.13.
PYDIR=""
for v in 3.13 3.12 3.11 3.10; do
  for b in "/opt/homebrew/bin/python$v" "/usr/local/bin/python$v" "$(command -v python$v 2>/dev/null || true)"; do
    if [ -n "$b" ] && [ -x "$b" ]; then PYDIR="$(mktemp -d)"; ln -s "$b" "$PYDIR/python3"; break 2; fi
  done
done
cd "$HOME"
if [ -n "$PYDIR" ]; then
  if PATH="$PYDIR:$PATH" bash "$DEST/vendor/claude-ads/install.sh" --source=local --repo-dir="$DEST/vendor/claude-ads" >/tmp/ogab_ads_install.log 2>&1; then
    ok "claude-ads com as dependências Python ($("$PYDIR/python3" --version))"
  else
    warn "dependências falharam; instalando só as skills (log: /tmp/ogab_ads_install.log)"
    bash "$DEST/vendor/claude-ads/install.sh" --source=local --repo-dir="$DEST/vendor/claude-ads" --no-deps >/dev/null && ok "claude-ads sem dependências"
  fi
  rm -rf "$PYDIR"
else
  bash "$DEST/vendor/claude-ads/install.sh" --source=local --repo-dir="$DEST/vendor/claude-ads" --no-deps >/dev/null && ok "claude-ads (sem dependências Python)"
  warn "sem Python 3.10 a 3.13: print de site, análise de landing, PDF e imagem do claude-ads não rodam. 'brew install python@3.12' e rode de novo."
fi

info "2/2 Conferência"
n=$(ls "$DEST/playbooks" 2>/dev/null | wc -l | tr -d ' '); ok "$n playbooks em $DEST/playbooks"
[ -f "$HOME/.claude/skills/ads/SKILL.md" ] && ok "/ads instalado" || warn "/ads não encontrado"
a=$(ls "$HOME/.claude/agents" 2>/dev/null | grep -c '^audit-' || true)
t=$(ls "$DEST/vendor/claude-ads/agents" 2>/dev/null | while read f; do [ -f "$HOME/.claude/agents/$f" ] && echo x; done | wc -l | tr -d ' ')
ok "$t agentes do claude-ads instalados ($a de auditoria por plataforma)"
echo
echo "Pronto. Reinicie o Claude Code e peça: /ogab trafego ajuda"
