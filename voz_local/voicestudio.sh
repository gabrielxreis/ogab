#!/bin/zsh
# Clonador de voz local do Gab: só o motor do VoiceStudio (backend Python, sem o app visual), opcional.
# Só Mac Apple Silicon por enquanto.
#   voicestudio.sh instalar        baixa só backend/ e omnivoice/ do repositório (versão fixa) e monta o Python com uv
#   voicestudio.sh modelo          baixa o modelo OmniVoice (~3,3 GB, licença NÃO comercial) com 16 conexões
#   voicestudio.sh motor <id>      instala outro motor no ambiente isolado dele (voxcpm2, confucius4-tts, ...)
#   voicestudio.sh start           sobe o backend (API + MCP em http://127.0.0.1:3900/mcp/)
#   voicestudio.sh stop | status | log | atualizar
# O Gab pede o "sim" do usuário antes de `instalar`, `modelo` e `motor` (tamanho e licença). Ver voz_local/README.md.
set -u
VERSAO="${OGAB_VOZ_VERSAO:-v0.5.6}"   # versão revisada; `atualizar` troca para a última
PROJ="$HOME/Library/Application Support/GabVoz/VoiceStudio"
PY="$PROJ/.venv/bin/python"
BASE="${OGAB_VOZ_BASE:-$HOME/Documents/Gab Voz Local}"
LOG="$BASE/backend.log"
PIDF="$BASE/backend.pid"
PORT=3900
REPO=debpalash/VoiceStudio
HFC="$HOME/.cache/huggingface/hub/models--k2-fsa--OmniVoice"

health() { curl -s -m 3 "http://127.0.0.1:$PORT/health"; }
mkdir -p "$BASE/referencias" "$BASE/saida"

case "${1:-}" in
  instalar|atualizar)
    [ "$(uname -m)" = arm64 ] && [ "$(uname)" = Darwin ] || { echo "!! O clonador local só roda em Mac Apple Silicon (M1 ou mais novo)."; exit 1; }
    command -v uv >/dev/null || brew install uv || { echo "!! preciso do uv: brew install uv"; exit 1; }
    if [ "$1" = atualizar ]; then
      VERSAO=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" | python3 -c "import json,sys;print(json.load(sys.stdin)['tag_name'])")
      "$0" stop >/dev/null; rm -rf "$PROJ.novo"
    fi
    if [ ! -f "$PROJ/pyproject.toml" ] || [ "$1" = atualizar ]; then
      DEST="$PROJ"; [ "$1" = atualizar ] && DEST="$PROJ.novo"
      echo "Baixando o código do motor ($VERSAO, só backend/ e omnivoice/)..."
      mkdir -p "$(dirname "$DEST")"; rm -rf "$DEST"
      git clone -q --depth 1 --filter=blob:none --sparse -b "$VERSAO" "https://github.com/$REPO.git" "$DEST" \
        && git -C "$DEST" sparse-checkout set backend omnivoice || { echo "!! download do código falhou"; exit 1; }
      if [ "$1" = atualizar ]; then [ -d "$PROJ/.venv" ] && mv "$PROJ/.venv" "$DEST/.venv"; rm -rf "$PROJ"; mv "$DEST" "$PROJ"; fi
    fi
    echo "Montando o Python do motor (PyTorch e dependências, ~2 GB na 1ª vez)..."
    cd "$PROJ" && uv sync --frozen --no-dev --managed-python --python 3.11 || { echo "!! uv sync falhou"; exit 1; }
    echo "ok: motor instalado ($VERSAO) em $PROJ" ;;

  motor)
    [ -n "${2:-}" ] || { echo "uso: $0 motor <id>   (lista: python3 voz.py motores)"; exit 1; }
    python3 "$(dirname "$0")/voz.py" instalar-motor "$2" ;;

  modelo)
    "$0" start >/dev/null || exit 1
    INST=$(curl -s -m 20 "http://127.0.0.1:$PORT/models" | python3 -c "import json,sys;print([m['installed'] and not m['incomplete'] for m in json.load(sys.stdin)['models'] if m['repo_id']=='k2-fsa/OmniVoice'][0])")
    if [ "$INST" = True ] && ls "$HFC"/snapshots/*/model.safetensors >/dev/null 2>&1; then echo "ok: modelo já instalado"; exit 0; fi
    # O download do próprio backend sai a ~0,6 MB/s; aria2c com 16 conexões no arquivo grande e o hub completa o resto.
    "$0" stop >/dev/null
    URL="https://huggingface.co/k2-fsa/OmniVoice/resolve/main/model.safetensors"
    HASH=$(curl -sI "$URL" | tr -d '\r' | awk -F': ' 'tolower($1)=="x-linked-etag"{gsub(/"/,"",$2);print $2}')
    command -v aria2c >/dev/null || brew install aria2 >/dev/null 2>&1 || true
    if command -v aria2c >/dev/null && [ -n "$HASH" ]; then
      mkdir -p "$HFC/blobs"; rm -f "$HFC/blobs/$HASH.part"
      aria2c -x16 -s16 -k4M --file-allocation=none --summary-interval=0 --console-log-level=warn \
        -d "$HFC/blobs" -o "$HASH.dl" "$URL" || { echo "!! download falhou"; exit 1; }
      [ "$(shasum -a 256 "$HFC/blobs/$HASH.dl" | cut -d' ' -f1)" = "$HASH" ] || { echo "!! SHA-256 não confere"; rm -f "$HFC/blobs/$HASH.dl"; exit 1; }
      mv "$HFC/blobs/$HASH.dl" "$HFC/blobs/$HASH"
    fi
    HF_XET_HIGH_PERFORMANCE=1 "$PY" -I -c "from huggingface_hub import snapshot_download as s; s('k2-fsa/OmniVoice')" || exit 1
    echo "ok: modelo OmniVoice instalado" ;;

  start)
    if health | grep -q '"status"'; then echo "já rodando: $(health)"; exit 0; fi
    [ -x "$PY" ] || { echo "!! clonador não instalado: voicestudio.sh instalar"; exit 1; }
    cd "$PROJ" || exit 1
    PYTHONUNBUFFERED=1 OMNIVOICE_PORT=$PORT OMNIVOICE_MCP_OUTPUT_MODE=files OMNIVOICE_MCP_BASE_PATH="$BASE" \
      nohup "$PY" -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port $PORT >"$LOG" 2>&1 &
    echo $! >"$PIDF"
    for i in {1..60}; do
      S=$(health); if echo "$S" | grep -q '"status":"ok"'; then echo "$S"; exit 0; fi; sleep 2
    done
    echo "!! backend não subiu em 120 s; veja $LOG"; exit 1 ;;

  stop)
    [ -f "$PIDF" ] && kill "$(cat "$PIDF")" 2>/dev/null; pkill -f "uvicorn main:app --app-dir backend" 2>/dev/null
    rm -f "$PIDF"; echo "parado" ;;
  status) health || echo "parado"; echo ;;
  log) tail -n 50 "$LOG" ;;
  *) echo "uso: $0 instalar|modelo|start|stop|status|log"; exit 1 ;;
esac
