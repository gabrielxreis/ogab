#!/usr/bin/env bash
# Instalador do Gab (/ogab), o editor de vídeo com IA (macOS).
# Uso:  curl -fsSL https://raw.githubusercontent.com/gabrielxreis/ogab/main/install.sh | bash
# Pode rodar de novo quando quiser: só instala o que faltar e atualiza a skill.
set -euo pipefail

REPO="https://github.com/gabrielxreis/ogab"
DEST="$HOME/.claude/skills/ogab"

tem_tty() { ( : < /dev/tty ) 2>/dev/null; }   # o Claude roda o instalador sem terminal: /dev/tty existe mas não abre
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
info() { printf "\n\033[1m%s\033[0m\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }

if [ "$(uname)" != "Darwin" ]; then
  echo "Esta skill foi feita para macOS (DaVinci Resolve Studio + scripting). Instalação cancelada."
  exit 1
fi

info "1/3 Homebrew"
if ! command -v brew >/dev/null 2>&1 && ! [ -x /opt/homebrew/bin/brew ] && ! [ -x /usr/local/bin/brew ] && ! tem_tty; then
  echo "  PRECISA_DO_USUARIO: o Homebrew ainda não está instalado e pede a senha do Mac, que só você pode digitar."
  echo "  Abra o app Terminal, cole o comando abaixo, digite a senha quando pedir e depois rode o instalador de novo:"
  echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  exit 2
fi
if ! command -v brew >/dev/null 2>&1; then
  echo "  Instalando o Homebrew (vai pedir a senha do Mac)..."
  # no "curl | bash" o stdin é o próprio script: o instalador do Homebrew precisa ler do terminal (senha, Enter)
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" < /dev/tty || true
fi
for B in /opt/homebrew/bin/brew /usr/local/bin/brew; do
  if [ -x "$B" ]; then
    eval "$("$B" shellenv)"
    # sem isto o Terminal e o Claude Code não acham brew, ffmpeg, node... nas próximas vezes
    grep -qs "brew shellenv" "$HOME/.zprofile" || echo "eval \"\$($B shellenv)\"" >> "$HOME/.zprofile"
    break
  fi
done
if ! command -v brew >/dev/null 2>&1; then
  echo "  Não consegui instalar o Homebrew. Instale à mão (https://brew.sh) e rode este instalador de novo."; exit 1
fi
ok "Homebrew $(brew --version | head -1 | awk '{print $2}')"

info "2/3 Python 3.10+ e git (o resto é instalado pelo painel em Python)"
command -v git >/dev/null 2>&1 || brew install git
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  # Python do macOS (Ferramentas de Linha de Comando) é o 3.9: velho para a skill. "python" cria o comando python3.
  brew install python >/dev/null 2>&1 || brew upgrade python >/dev/null 2>&1 || true
  hash -r
fi
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null \
  && ok "Python $(python3 -c 'import platform; print(platform.python_version())')" \
  || { warn "o python3 continua abaixo do 3.10; rode: brew install python, abra um Terminal novo e rode o instalador de novo"; exit 1; }

info "3/3 Gab (/ogab)"
if [ ! -e "$DEST" ] && [ -d "$HOME/.claude/skills/video-redes/.git" ]; then
  mv "$HOME/.claude/skills/video-redes" "$DEST" && ok "pasta antiga video-redes renomeada para ogab"
fi
if [ -d "$DEST/.git" ]; then
  if git -C "$DEST" pull --ff-only --quiet 2>/dev/null; then ok "atualizada em $DEST"
  else warn "não consegui atualizar agora (mudança local ou sem internet); o doctor no fim guarda as mudanças e atualiza"; fi
else
  mkdir -p "$(dirname "$DEST")"
  if [ -e "$DEST" ]; then mv "$DEST" "$DEST.antiga.$(date +%s)" && warn "pasta $DEST sem git renomeada para .antiga"; fi
  git clone --quiet "$REPO" "$DEST" && ok "instalada em $DEST" \
    || { echo "  Não consegui baixar a skill do GitHub ($REPO). Confira a internet e rode de novo."; exit 1; }
fi
if [ -f "$DEST/config.json" ] && ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$DEST/config.json" 2>/dev/null; then
  mv "$DEST/config.json" "$DEST/config.json.quebrado.$(date +%s)" && warn "config.json estava inválido: guardei uma cópia e criei outro"
fi
if [ ! -f "$DEST/config.json" ]; then
  cp "$DEST/config.example.json" "$DEST/config.json"
  ok "config.json criado (fica só na sua máquina)"
else
  ok "config.json mantido"
fi

# Daqui em diante: painel ao vivo em Python (perguntas, o que baixa, MB/s, o que já tem e o que falta).
info "Instalando o resto (painel ao vivo; log em ~/.claude/ogab-instalacao.log)"
if tem_tty; then exec python3 "$DEST/scripts/instalador.py" < /dev/tty
else exec python3 "$DEST/scripts/instalador.py"; fi
