#!/usr/bin/env bash
# Instala a parte do Premiere do Gab (/ogab) no Mac: plugin Gab Ponte, LUT e letterings (.mogrt).
# Uso: bash ~/.claude/skills/ogab/premiere/instalar.sh     (rodar de novo quando quiser; não mexe no fluxo do DaVinci)
set -uo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
info() { printf "\n\033[1m%s\033[0m\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }

info "1/4 Premiere Pro"
PR="$(ls -d /Applications/Adobe\ Premiere\ Pro\ 20*/Adobe\ Premiere\ Pro\ 20*.app 2>/dev/null | sort | tail -1)"
if [ -n "$PR" ]; then
  VER="$(defaults read "$PR/Contents/Info" CFBundleShortVersionString 2>/dev/null || echo 0)"
  ok "$(basename "$PR" .app) $VER"
  [ "${VER%%.*}" -lt 26 ] 2>/dev/null && warn "a ponte precisa do Premiere 2026 (26.x) ou mais novo: atualize pelo Creative Cloud"
else
  warn "Premiere Pro não encontrado em /Applications (instale o Premiere Pro 2026+ pelo Creative Cloud)"
fi

info "2/4 Plugin Gab Ponte (liga o Premiere ao /ogab)"
CCX="${TMPDIR:-/tmp}/GabPonte.ccx"
rm -f "$CCX"; (cd "$AQUI/plugin" && zip -qr "$CCX" . -x '.*')
UPIA="/Library/Application Support/Adobe/Adobe Desktop Common/RemoteComponents/UPI/UnifiedPluginInstallerAgent/UnifiedPluginInstallerAgent.app/Contents/MacOS/UnifiedPluginInstallerAgent"
if [ -x "$UPIA" ] && "$UPIA" --install "$CCX" >/tmp/ogab_upia.log 2>&1; then
  ok "plugin instalado (Premiere: Window > UXP Plugins > Gab Ponte)"
else
  warn "o instalador da Adobe não aceitou o plugin (ver /tmp/ogab_upia.log). Alternativa: UXP Developer Tool (Creative Cloud) > Add Plugin > $AQUI/plugin/manifest.json > Load"
fi

info "3/4 LUT de cor"
n=0
for d in Technical Creative; do
  dst="$HOME/Library/Application Support/Adobe/Common/LUTs/$d"; mkdir -p "$dst"
  for f in "$AQUI"/assets/lut/*.cube; do [ -f "$f" ] && cp "$f" "$dst/" && n=$((n+1)); done
done
[ "$n" -gt 0 ] && ok "LUT(s) em ~/Library/Application Support/Adobe/Common/LUTs (Technical = Input LUT, Creative = Look)" \
  || warn "nenhum .cube em premiere/assets/lut (coloque o LUT DO GAB.cube lá e rode de novo)"

info "4/4 Lettering animado (.mogrt)"
MG="$HOME/Library/Application Support/Adobe/Common/Motion Graphics Templates"; mkdir -p "$MG"
n=0; for f in "$AQUI"/assets/mogrt/*.mogrt; do [ -f "$f" ] && cp "$f" "$MG/" && n=$((n+1)); done
[ "$n" -gt 0 ] && ok "$n MOGRT(s) instalados" || warn "nenhum .mogrt em premiere/assets/mogrt ainda (lettering fica para quando existir)"

# Quem roda este instalador escolheu o Premiere: grava no config.json (o Gab trabalha só nele).
CFG="$AQUI/../config.json"; [ -f "$CFG" ] || cp "$AQUI/../config.example.json" "$CFG"
python3 - "$CFG" <<'PY' && ok "config.json: editor = premiere"
import json, sys
c = json.load(open(sys.argv[1])); c["editor"] = "premiere"
json.dump(c, open(sys.argv[1], "w"), ensure_ascii=False, indent=2)
PY

# Aviso para o Gab ler o guia do Premiere (no CLAUDE.md do usuário, fora do repositório).
CM="$HOME/.claude/CLAUDE.md"; MARCA="ogab/premiere/README.md"
if ! grep -qs "$MARCA" "$CM"; then
  printf '\n- Premiere: quando o /ogab for editar no Adobe Premiere (config.json "editor": "premiere" ou pedido do usuário), ler antes ~/.claude/skills/%s (premiere_lib.py no lugar do resolve_lib.py).\n' "$MARCA" >> "$CM"
  ok "aviso do Premiere adicionado em ~/.claude/CLAUDE.md"
fi

cat <<'EOF'

Pronto. No Premiere, uma vez: Window > UXP Plugins > Gab Ponte (deixe o painel encaixado; ele mostra "conectado").
Para o Gab editar no Premiere por padrão:  /ogab config editor premiere
EOF
