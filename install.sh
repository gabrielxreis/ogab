#!/usr/bin/env bash
# Instalador do Gab (/ogab), o editor de vídeo com IA (macOS).
# Uso:  curl -fsSL https://raw.githubusercontent.com/gabrielxreis/video-redes-skill/main/install.sh | bash
# Pode rodar de novo quando quiser: só instala o que faltar e atualiza a skill.
set -euo pipefail

REPO="https://github.com/gabrielxreis/video-redes-skill"
DEST="$HOME/.claude/skills/ogab"

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

info "2/7 ffmpeg, yt-dlp, Node.js, Python 3 e git"
for pkg in ffmpeg yt-dlp node python git; do
  bin="$pkg"; [ "$pkg" = "python" ] && bin="python3"
  if command -v "$bin" >/dev/null 2>&1; then ok "$pkg já instalado"; else brew install "$pkg"; ok "$pkg instalado"; fi
done

info "3/7 Pillow (Python)"
if python3 -c "import PIL" 2>/dev/null; then ok "Pillow já instalado"
else
  python3 -m pip install --user --quiet pillow 2>/dev/null || python3 -m pip install --user --quiet --break-system-packages pillow
  ok "Pillow instalado"
fi

info "4/7 Gab (/ogab)"
if [ ! -e "$DEST" ] && [ -d "$HOME/.claude/skills/video-redes/.git" ]; then
  mv "$HOME/.claude/skills/video-redes" "$DEST" && ok "pasta antiga video-redes renomeada para ogab"
fi
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

info "5b/7 Skills de design e navegador (taste, web-design-guidelines, image-to-code, playwright-cli, awesome-design-md)"
npx --yes skills add leonxlnx/taste-skill -g -a claude-code -s design-taste-frontend -s image-to-code -y >/dev/null 2>&1 \
  && ok "taste-skill (design-taste-frontend, image-to-code) instaladas" \
  || warn "rode depois: npx skills add leonxlnx/taste-skill -g -a claude-code -s design-taste-frontend -s image-to-code -y"
npx --yes skills add vercel-labs/agent-skills -g -a claude-code -s web-design-guidelines -y >/dev/null 2>&1 \
  && ok "web-design-guidelines instalada" \
  || warn "rode depois: npx skills add vercel-labs/agent-skills -g -a claude-code -s web-design-guidelines -y"
if command -v playwright-cli >/dev/null 2>&1 || npm install -g @playwright/cli@latest >/dev/null 2>&1; then
  (cd "$HOME" && playwright-cli install --skills >/dev/null 2>&1) && ok "playwright-cli + skill instalados" \
    || warn "rode depois: cd ~ && playwright-cli install --skills"
else
  warn "não consegui instalar o playwright-cli; rode: npm install -g @playwright/cli@latest"
fi
mkdir -p "$HOME/.claude/referencias"
if [ -d "$HOME/.claude/referencias/awesome-design-md/.git" ]; then
  git -C "$HOME/.claude/referencias/awesome-design-md" pull -q >/dev/null 2>&1; ok "awesome-design-md atualizado"
else
  git clone --depth 1 -q https://github.com/voltagent/awesome-design-md.git "$HOME/.claude/referencias/awesome-design-md" >/dev/null 2>&1 \
    && ok "awesome-design-md (DESIGN.md de 70+ marcas) em ~/.claude/referencias" || warn "não consegui clonar o awesome-design-md"
fi

info "6/7 Fontes (Poppins, Playfair Display, Lobster, licença OFL)"
mkdir -p "$HOME/Library/Fonts"
n=0
while IFS= read -r -d '' f; do
  b="$(basename "$f")"
  [ -f "$HOME/Library/Fonts/$b" ] || { cp "$f" "$HOME/Library/Fonts/"; n=$((n+1)); }
done < <(find "$DEST/assets/fontes" -type f \( -name '*.ttf' -o -name '*.otf' \) -print0)
ok "$n fonte(s) nova(s) instalada(s)"

info "7/7 DaVinci Resolve e transcrição"
APP="/Applications/DaVinci Resolve/DaVinci Resolve.app"
precisa_whisper=1
if [ -d "$APP" ]; then
  VER="$(defaults read "$APP/Contents/Info" CFBundleShortVersionString 2>/dev/null || echo 0)"
  MAJ="$(echo "$VER" | cut -d. -f1)"; MIN="$(echo "$VER" | cut -d. -f2)"; PAT="$(echo "$VER" | cut -d. -f3)"
  MAJ=${MAJ:-0}; MIN=${MIN:-0}; PAT=${PAT:-0}
  ok "DaVinci Resolve $VER encontrado"
  if [ -f "$APP/Contents/Libraries/Fusion/fusionscript.so" ]; then
    ok "biblioteca de scripting encontrada"
  else
    warn "scripting não encontrado: a skill precisa do DaVinci Resolve STUDIO (a versão grátis não tem scripting externo)"
  fi
  # A leitura da transcrição pela API (GetTranscription) só existe a partir da 21.1.
  if [ "$MAJ" -gt 21 ] || { [ "$MAJ" -eq 21 ] && [ "$MIN" -ge 1 ]; }; then
    precisa_whisper=0
    ok "o DaVinci $VER transcreve sozinho: Whisper não é necessário"
  else
    warn "DaVinci $VER: abaixo da 21.1 a API não devolve a transcrição; vou instalar o Whisper local (grátis)"
  fi
  # AppendToTimeline só com áudio numa trilha específica foi corrigido na 20.2.2.
  if [ "$MAJ" -lt 20 ] || { [ "$MAJ" -eq 20 ] && { [ "$MIN" -lt 2 ] || { [ "$MIN" -eq 2 ] && [ "$PAT" -lt 2 ]; }; }; }; then
    warn "abaixo da 20.2.2 o DaVinci pode errar a trilha ao colocar narração e música; a skill confere A1/A2, mas o ideal é atualizar para a 21.1+"
  fi
else
  warn "DaVinci Resolve não encontrado em /Applications. Instale o DaVinci Resolve Studio 21.1+: https://www.blackmagicdesign.com/products/davinciresolve"
fi

if [ "$precisa_whisper" -eq 1 ]; then
  if [ "$(uname -m)" = "arm64" ]; then WPKG="mlx-whisper"; WMOD="mlx_whisper"; else WPKG="faster-whisper"; WMOD="faster_whisper"; fi
  if python3 -c "import $WMOD" 2>/dev/null; then
    ok "Whisper local ($WPKG) já instalado"
  else
    python3 -m pip install --user --quiet "$WPKG" 2>/dev/null || python3 -m pip install --user --quiet --break-system-packages "$WPKG"
    python3 -c "import $WMOD" 2>/dev/null && ok "Whisper local ($WPKG) instalado; o modelo (~1,6 GB) baixa na primeira transcrição" \
      || warn "não consegui instalar o $WPKG; rode: python3 -m pip install --user $WPKG"
  fi
fi

cat <<'EOF'

Pronto. Falta só o que precisa de você (uma vez):
  1. No DaVinci: Preferences > System > General > External scripting using: Local (e reinicie o Resolve).
  2. Conectar as SUAS contas no Claude (Configurações > Conectores): ElevenLabs, Artlist, Envato, Magnific... só o que usar.
  3. Instalar a extensão Claude in Chrome e fazer login nos sites (downloads são pelo navegador).
  4. Opcional: seu pacote de lettering (.drfx) em
     ~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/
  5. Opcional: skill competitor-profiling (Personalização > Skills no Claude).

Reinicie o Claude Code e peça: "faz um vídeo para <empresa> sobre <tema>" ou digite /ogab ajuda (o Gab é o seu editor)
EOF
