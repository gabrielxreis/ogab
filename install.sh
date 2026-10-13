#!/usr/bin/env bash
# Instalador do Gab (/ogab), o editor de vídeo com IA (macOS).
# Uso:  curl -fsSL https://raw.githubusercontent.com/gabrielxreis/ogab/main/install.sh | bash
# Pode rodar de novo quando quiser: só instala o que faltar e atualiza a skill.
set -euo pipefail

REPO="https://github.com/gabrielxreis/ogab"
DEST="$HOME/.claude/skills/ogab"

ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
info() { printf "\n\033[1m%s\033[0m\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }

if [ "$(uname)" != "Darwin" ]; then
  echo "Esta skill foi feita para macOS (DaVinci Resolve Studio + scripting). Instalação cancelada."
  exit 1
fi

info "1/9 Homebrew"
if ! command -v brew >/dev/null 2>&1; then
  echo "  Instalando o Homebrew (vai pedir a senha do Mac)..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  [ -x /opt/homebrew/bin/brew ] && eval "$(/opt/homebrew/bin/brew shellenv)"
  [ -x /usr/local/bin/brew ] && eval "$(/usr/local/bin/brew shellenv)"
fi
ok "Homebrew $(brew --version | head -1 | awk '{print $2}')"

info "2/9 ffmpeg, yt-dlp, Node.js, Python 3 e git"
for pkg in ffmpeg yt-dlp node python git; do
  bin="$pkg"; [ "$pkg" = "python" ] && bin="python3"
  if command -v "$bin" >/dev/null 2>&1; then ok "$pkg já instalado"; else brew install "$pkg"; ok "$pkg instalado"; fi
done

info "3/9 Pacotes Python (Pillow, numpy, OpenCV para o rastreio; OCR da Apple para a legenda no DaVinci; requests e dotenv para o Instagram)"
for par in "PIL:pillow" "numpy:numpy" "cv2:opencv-python" "Vision:pyobjc-framework-Vision" "Quartz:pyobjc-framework-Quartz" "requests:requests" "dotenv:python-dotenv"; do
  mod="${par%%:*}"; pac="${par#*:}"
  if python3 -c "import $mod" 2>/dev/null; then ok "$pac já instalado"
  else
    python3 -m pip install --user --quiet "$pac" 2>/dev/null || python3 -m pip install --user --quiet --break-system-packages "$pac" 2>/dev/null
    python3 -c "import $mod" 2>/dev/null && ok "$pac instalado" || warn "não consegui instalar $pac (o doctor tenta de novo no fim)"
  fi
done

info "3b/9 Blender (3D de verdade nos motions)"
if [ -d "/Applications/Blender.app" ]; then ok "Blender já instalado"
else brew install --cask blender >/dev/null 2>&1 && ok "Blender instalado" || warn "não consegui instalar o Blender: brew install --cask blender"; fi

info "3c/9 cc-blender-skill (30 skills de Blender: objetos 3D, materiais, luz, câmera; MIT)"
CCB="$HOME/.claude/referencias/cc-blender-skill"; mkdir -p "$HOME/.claude/referencias" "$HOME/.claude/skills"
if [ -d "$CCB/.git" ]; then git -C "$CCB" pull -q >/dev/null 2>&1; else git clone -q --depth 1 https://github.com/RobLe3/cc-blender-skill.git "$CCB" >/dev/null 2>&1; fi
n=0
for d in "$CCB"/plugin/skills/*/; do
  nome="$(basename "$d")"; [ -f "$d/SKILL.md" ] || continue
  if [ -e "$HOME/.claude/skills/$nome" ] && [ ! -f "$HOME/.claude/skills/$nome/.cc-blender" ]; then continue; fi   # não sobrescreve skill de outro dono
  rm -rf "$HOME/.claude/skills/$nome"; cp -R "$d" "$HOME/.claude/skills/$nome"; touch "$HOME/.claude/skills/$nome/.cc-blender"; n=$((n+1))
done
[ "$n" -gt 0 ] && ok "$n skills de Blender instaladas" || warn "não consegui instalar o cc-blender-skill (rode o instalador de novo)"

info "4/9 Gab (/ogab)"
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

# Editor: cada usuário escolhe UM (DaVinci ou Premiere) e o Gab trabalha só nele (config.json "editor").
EDITOR_ATUAL="$(python3 -c "import json;print(json.load(open('$DEST/config.json')).get('editor',''))" 2>/dev/null || true)"
OGAB_EDITOR="${OGAB_EDITOR:-$EDITOR_ATUAL}"
if [ -z "$OGAB_EDITOR" ] && [ -r /dev/tty ]; then
  printf "\n  Em qual editor o Gab vai montar seus vídeos?\n    1) DaVinci Resolve Studio\n    2) Adobe Premiere Pro\n  Escolha [1/2]: "
  read -r esc < /dev/tty || true
  [ "${esc:-1}" = "2" ] && OGAB_EDITOR="premiere" || OGAB_EDITOR="davinci"
fi
OGAB_EDITOR="${OGAB_EDITOR:-davinci}"
python3 - "$DEST/config.json" "$OGAB_EDITOR" <<'PY'
import json, sys
c = json.load(open(sys.argv[1])); c["editor"] = sys.argv[2]
json.dump(c, open(sys.argv[1], "w"), ensure_ascii=False, indent=2)
PY
ok "editor: $OGAB_EDITOR (para trocar: /ogab config editor davinci|premiere)"

# Motions: automático (HyperFrames) ou no After Effects (camadas editáveis). Tudo é instalado; a escolha só diz qual o Gab usa.
MOTION_ATUAL="$(python3 -c "import json;print(json.load(open('$DEST/config.json')).get('motion',''))" 2>/dev/null || true)"
OGAB_MOTION="${OGAB_MOTION:-$MOTION_ATUAL}"
if [ -z "$OGAB_MOTION" ] && [ -r /dev/tty ]; then
  printf "\n  Como o Gab faz os motions?\n    1) Automático (HyperFrames, rápido)\n    2) No After Effects (camadas editáveis: texto, números, checks, cores)\n  Escolha [1/2]: "
  read -r escm < /dev/tty || true
  [ "${escm:-1}" = "2" ] && OGAB_MOTION="aftereffects" || OGAB_MOTION="hyperframes"
fi
OGAB_MOTION="${OGAB_MOTION:-hyperframes}"
python3 - "$DEST/config.json" "$OGAB_MOTION" <<'PY'
import json, sys
c = json.load(open(sys.argv[1])); c["motion"] = sys.argv[2]
json.dump(c, open(sys.argv[1], "w"), ensure_ascii=False, indent=2)
PY
ok "motions: $OGAB_MOTION (para trocar: /ogab config motion hyperframes|aftereffects)"

info "5/9 HyperFrames (motions, gráficos, edição dinâmica)"
npx --yes skills add heygen-com/hyperframes -g -a claude-code -s '*' -y >/dev/null 2>&1 \
  && ok "skills do HyperFrames instaladas" \
  || warn "não consegui instalar o HyperFrames agora; rode depois: npx skills add heygen-com/hyperframes -g -a claude-code -s '*' -y"
npx --yes hyperframes doctor >/dev/null 2>&1 && ok "hyperframes doctor ok" || warn "rode 'npx hyperframes doctor' para ver o que falta no HyperFrames"
python3 "$DEST/instagram/carrossel/carrossel.py" instalar >/dev/null 2>&1 && ok "carrossel do Instagram pronto (slides PNG/PDF)" \
  || warn "rode depois: python3 $DEST/instagram/carrossel/carrossel.py instalar"

info "5b/9 Skills de design, navegador e engenharia reversa (taste, web-design-guidelines, image-to-code, playwright-cli, REA, awesome-design-md)"
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
npx --yes skills add morluto/rea -g -a claude-code -s reverse-engineer-anything -y >/dev/null 2>&1 \
  && ok "REA (reverse-engineer-anything) skill instalada" || warn "rode depois: npx skills add morluto/rea -g -a claude-code -s reverse-engineer-anything -y"
npx --yes rea-agents setup --client claude_code --yes >/dev/null 2>&1 \
  && ok "REA MCP registrado no Claude Code (backup em ~/.claude.json.rea.backup)" || warn "rode depois: npx rea-agents setup --client claude_code"
mkdir -p "$HOME/.claude/referencias"
if [ -d "$HOME/.claude/referencias/awesome-design-md/.git" ]; then
  git -C "$HOME/.claude/referencias/awesome-design-md" pull -q >/dev/null 2>&1; ok "awesome-design-md atualizado"
else
  git clone --depth 1 -q https://github.com/voltagent/awesome-design-md.git "$HOME/.claude/referencias/awesome-design-md" >/dev/null 2>&1 \
    && ok "awesome-design-md (DESIGN.md de 70+ marcas) em ~/.claude/referencias" || warn "não consegui clonar o awesome-design-md"
fi
if [ -d "$HOME/.claude/referencias/awesome-opus5-5-videos/.git" ]; then
  git -C "$HOME/.claude/referencias/awesome-opus5-5-videos" pull -q >/dev/null 2>&1; ok "awesome-opus5-5-videos atualizado"
else
  git clone --depth 1 -q https://github.com/yihui-dev/awesome-opus5-5-videos.git "$HOME/.claude/referencias/awesome-opus5-5-videos" >/dev/null 2>&1 \
    && ok "awesome-opus5-5-videos (inspiração de motions, 850+ prompts) em ~/.claude/referencias" || warn "não consegui clonar o awesome-opus5-5-videos"
fi

info "6/9 Fontes (Poppins, Playfair Display, Lobster, licença OFL)"
mkdir -p "$HOME/Library/Fonts"
n=0
while IFS= read -r -d '' f; do
  b="$(basename "$f")"
  [ -f "$HOME/Library/Fonts/$b" ] || { cp "$f" "$HOME/Library/Fonts/"; n=$((n+1)); }
done < <(find "$DEST/assets/fontes" -type f \( -name '*.ttf' -o -name '*.otf' \) -print0)
ok "$n fonte(s) nova(s) instalada(s)"

# Lettering animado: pacote @gabrielxreis_ Text Presets (títulos do Fusion) na pasta de Templates do DaVinci
TPL="$HOME/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates"
mkdir -p "$TPL"
for f in "$DEST"/assets/lettering/*.drfx; do
  [ -f "$f" ] && cp -f "$f" "$TPL/" && ok "lettering $(basename "$f") instalado (reinicie o DaVinci)"
done

info "7/9 DaVinci Resolve e transcrição"
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

# Tudo é instalado em toda máquina; config.json (editor e motion) só diz qual app o Gab usa.
info "8/9 Adobe Premiere Pro (plugin Gab Ponte, LUT e letterings)"
OGAB_SEM_CONFIG=1 bash "$DEST/premiere/instalar.sh" | sed -n '/^ /p' || true

info "9/9 After Effects (extensão Gab Ponte AE, motions editáveis)"
OGAB_SEM_CONFIG=1 bash "$DEST/aftereffects/instalar.sh" | sed -n '/^ /p' || true   # sem AE (ou AE aberto) só avisa


info "Conferência final (doctor: confere tudo e corrige o que der)"
python3 "$DEST/scripts/doctor.py" --corrigir || true

cat <<EOF

Pronto. Seu Gab vai editar no: $OGAB_EDITOR   |   motions: $OGAB_MOTION
(trocar a qualquer hora: /ogab config editor davinci|premiere  e  /ogab config motion hyperframes|aftereffects)

Falta só o que precisa de você (uma vez), no app que você usa:
  DaVinci:        Preferences > System > General > External scripting using: Local (e reinicie o Resolve).
                  Reinicie o DaVinci para carregar o lettering (@gabrielxreis_ Text Presets, já instalado em Fusion/Templates).
  Premiere:       Window > UXP Plugins > Gab Ponte (deixe o painel encaixado).
  After Effects:  nada: a ponte sobe sozinha (se o AE estava aberto durante a instalação, feche e rode o instalador de novo).
  Todos:          conecte as SUAS contas no Claude (Configurações > Conectores): ElevenLabs, Artlist, Envato, Magnific...
                  e a extensão Claude in Chrome logada nos sites (downloads são pelo navegador).

Reinicie o Claude Code e digite:  /ogab comecar
EOF
