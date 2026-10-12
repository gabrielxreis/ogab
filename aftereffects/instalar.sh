#!/usr/bin/env bash
# Instala a parte do After Effects do Gab (/ogab) no Mac: extensão invisível Gab Ponte AE e a permissão de scripts.
# Uso: bash ~/.claude/skills/ogab/aftereffects/instalar.sh   (rodar com o After Effects FECHADO; pode rodar de novo)
set -uo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
info() { printf "\n\033[1m%s\033[0m\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }

info "1/4 After Effects"
AE="$(ls -d /Applications/Adobe\ After\ Effects\ 20* 2>/dev/null | sort | tail -1)"
if [ -z "$AE" ]; then warn "After Effects não encontrado em /Applications (instale pelo Creative Cloud)"; exit 1; fi
VER="$(defaults read "$AE/$(basename "$AE").app/Contents/Info" CFBundleShortVersionString 2>/dev/null || echo 0)"
ok "$(basename "$AE") $VER"
if pgrep -f "$(basename "$AE").app/Contents/MacOS" >/dev/null; then
  warn "feche o After Effects antes (a preferência de scripts só é gravada com ele fechado) e rode de novo"; exit 1
fi

info "2/4 Extensão Gab Ponte AE (invisível, sobe sozinha com o AE)"
for v in 9 10 11 12 13 14; do defaults write com.adobe.CSXS.$v PlayerDebugMode 1; done
DST="$HOME/Library/Application Support/Adobe/CEP/extensions/com.gabrielxreis.ogab.aeponte"
rm -rf "$DST"; mkdir -p "$(dirname "$DST")"; cp -R "$AQUI/cep" "$DST"
ok "extensão em ~/Library/Application Support/Adobe/CEP/extensions (extensões sem assinatura liberadas)"

info "3/4 Permissão de scripts do AE (gravar arquivos: quadros, render, MOGRT)"
MAJ="$(echo "$VER" | cut -d. -f1-2)"
n=0
for P in "$HOME/Library/Preferences/Adobe/After Effects/$MAJ"/*.txt; do
  grep -q "Pref_SCRIPTING_FILE_NETWORK_SECURITY" "$P" 2>/dev/null || continue
  python3 - "$P" <<'PY' && n=$((n+1))
import re, sys
p = sys.argv[1]; s = open(p, encoding="utf-8", errors="surrogateescape").read()
s = re.sub(r'("Pref_SCRIPTING_FILE_NETWORK_SECURITY" = )"?\w+"?', r'\1"1"', s)
open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
PY
done
[ "$n" -gt 0 ] && ok "\"Permitir que scripts gravem arquivos e acessem a rede\" ligado" \
  || warn "abra o AE uma vez, feche e rode de novo (ou ligue em Ajustes > Scripts e expressões)"

info "4/4 Fontes"
[ -f "$HOME/Library/Fonts/Poppins-Bold.ttf" ] && ok "Poppins instalada" || warn "rode o install.sh da skill para instalar as fontes"

# Quem roda este instalador escolheu motions no After Effects: grava no config.json.
# (OGAB_SEM_CONFIG=1 pula: o install.sh principal já gravou a escolha, ou é só um teste)
CFG="$AQUI/../config.json"; [ -f "$CFG" ] || cp "$AQUI/../config.example.json" "$CFG"
if [ "${OGAB_SEM_CONFIG:-0}" != "1" ]; then
python3 - "$CFG" <<'PY' && ok "config.json: motion = aftereffects"
import json, sys
c = json.load(open(sys.argv[1])); c["motion"] = "aftereffects"
json.dump(c, open(sys.argv[1], "w"), ensure_ascii=False, indent=2)
PY
fi

cat <<'EOF'

Pronto. Abra o After Effects normalmente: a ponte sobe sozinha (não tem painel para abrir).
Para voltar aos motions automáticos (HyperFrames):  /ogab config motion hyperframes
EOF
