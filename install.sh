#!/usr/bin/env bash
# Instalador da skill video-redes (macOS).
# Uso:  curl -fsSL https://raw.githubusercontent.com/gabrielxreis/video-redes-skill/main/install.sh | bash
# Pode rodar de novo quando quiser: só instala o que faltar e atualiza a skill.
set -euo pipefail

REPO="https://github.com/gabrielxreis/video-redes-skill"
DEST="$HOME/.claude/skills/video-redes"

ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
info() { printf "\n\033[1m%s\033[0m\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }

if [ "$(uname)" != "Darwin" ]; then
  echo "Esta skill foi feita para macOS (DaVinci Resolve Studio + scripting). Instalação cancelada."
  exit 1
fi

info "1/7 Homebrew"
if ! command -v brew >/dev/null 2>&1; then
  echo "  Instalando o Homebrew (vai pedir a senha do Mac)..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  [ -x /opt/homebrew/bin/brew ] && eval "$(/opt/homebrew/bin/brew shellenv)"
  [ -x /usr/local/bin/brew ] && eval "$(/usr/local/bin/brew shellenv)"
fi
ok "Homebrew $(brew --version | head -1 | awk '{print $2}')"

info "2/7 ffmpeg, Node.js, Python 3 e git"
for pkg in ffmpeg node python git; do
  bin="$pkg"; [ "$pkg" = "python" ] && bin="python3"
  if command -v "$bin" >/dev/null 2>&1; then ok "$pkg já instalado"; else brew install "$pkg"; ok "$pkg instalado"; fi
done

info "3/7 Pillow (Python)"
if python3 -c "import PIL" 2>/dev/null; then ok "Pillow já instalado"
else
  python3 -m pip install --user --quiet pillow 2>/dev/null || python3 -m pip install --user --quiet --break-system-packages pillow
  ok "Pillow instalado"
fi

info "4/7 Skill video-redes"
if [ -d "$DEST/.git" ]; then
  git -C "$DEST" pull --ff-only --quiet && ok "atualizada em $DEST"
else
  mkdir -p "$(dirname "$DEST")"
  git clone --quiet "$REPO" "$DEST" && ok "instalada em $DEST"
fi
if [ ! -f "$DEST/config.json" ]; then
  cp "$DEST/config.example.json" "$DEST/config.json"
  ok "config.json criado (fica só na sua máquina)"
else
  ok "config.json mantido"
fi

info "5/7 HyperFrames (motions, gráficos, edição dinâmica)"
npx --yes skills add heygen-com/hyperframes -g -a claude-code -s '*' -y >/dev/null 2>&1 \
  && ok "skills do HyperFrames instaladas" \
  || warn "não consegui instalar o HyperFrames agora; rode depois: npx skills add heygen-com/hyperframes -g -a claude-code -s '*' -y"
npx --yes hyperframes doctor >/dev/null 2>&1 && ok "hyperframes doctor ok" || warn "rode 'npx hyperframes doctor' para ver o que falta no HyperFrames"

info "6/7 Fontes (Poppins, Playfair Display, Lobster, licença OFL)"
mkdir -p "$HOME/Library/Fonts"
n=0
while IFS= read -r -d '' f; do
  b="$(basename "$f")"
  [ -f "$HOME/Library/Fonts/$b" ] || { cp "$f" "$HOME/Library/Fonts/"; n=$((n+1)); }
done < <(find "$DEST/assets/fontes" -type f \( -name '*.ttf' -o -name '*.otf' \) -print0)
ok "$n fonte(s) nova(s) instalada(s)"

info "7/7 DaVinci Resolve"
if [ -d "/Applications/DaVinci Resolve/DaVinci Resolve.app" ]; then
  ok "DaVinci Resolve encontrado"
  if [ -f "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so" ]; then
    ok "biblioteca de scripting encontrada"
  else
    warn "scripting não encontrado: a skill precisa do DaVinci Resolve STUDIO (a versão grátis não tem scripting externo)"
  fi
else
  warn "DaVinci Resolve não encontrado em /Applications. Instale o DaVinci Resolve Studio: https://www.blackmagicdesign.com/products/davinciresolve"
fi

cat <<'EOF'

Pronto. Falta só o que precisa de você (uma vez):
  1. No DaVinci: Preferences > System > General > External scripting using: Local (e reinicie o Resolve).
  2. Conectar as SUAS contas no Claude (Configurações > Conectores): ElevenLabs, Artlist, Envato, Magnific... só o que usar.
  3. Instalar a extensão Claude in Chrome e fazer login nos sites (downloads são pelo navegador).
  4. Opcional: seu pacote de lettering (.drfx) em
     ~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/
  5. Opcional: skill competitor-profiling (Personalização > Skills no Claude).

Reinicie o Claude Code e peça: "faz um vídeo para <empresa> sobre <tema>" ou digite /video-redes ajuda
EOF
