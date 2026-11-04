#!/bin/sh
# /ogab dashboard: liga o Meu Negócio do O Gab (CRM, projetos, planner, orçamentos e financeiro) neste
# computador e abre no navegador.
# Uso: negocio.sh [abrir [dashboard|crm|projetos|planner|financeiro]|status|parar|resumo]
# Dados: ~/.ogab/negocio (banco negocio.db + arquivos/). Painel: http://127.0.0.1:3200, só nesta máquina.
set -e
APP="$(cd "$(dirname "$0")/.." && pwd)"
HOME_GAB="$HOME/.ogab/negocio"
PORT="${OGAB_NEGOCIO_PORTA:-3200}"
BASE="http://127.0.0.1:$PORT"
PID="$HOME_GAB/servidor.pid"
LOG="$HOME_GAB/servidor.log"
mkdir -p "$HOME_GAB"

no_ar() { curl -fsS -m 2 "$BASE/api/ogab/saude" >/dev/null 2>&1; }
meu_pid() { [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; }

abrir_url() {
  if command -v open >/dev/null 2>&1; then open "$1" >/dev/null 2>&1 || true
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$1" >/dev/null 2>&1 || true
  fi
}

montar() {
  # monta o painel só quando falta web/dist (ou o código mudou depois da última montagem)
  cd "$APP/web"
  novo=$(find src index.html -type f -newer dist/index.html 2>/dev/null | head -1)
  [ -f dist/index.html ] && [ -z "$novo" ] && return 0
  [ -f package.json ] || { [ -f dist/index.html ] && return 0; echo "ERRO: painel não montado e sem código para montar"; exit 1; }
  command -v npm >/dev/null 2>&1 || { echo "ERRO: precisa do Node.js (npm) para montar o painel na primeira vez"; exit 1; }
  echo "montando o painel (uns 2 minutos na primeira vez)..."
  [ -d node_modules ] || npm ci --no-audit --no-fund --loglevel=error > "$HOME_GAB/npm.log" 2>&1 || { echo "ERRO ao instalar (veja $HOME_GAB/npm.log)"; exit 1; }
  npx vite build > "$HOME_GAB/build.log" 2>&1 || { echo "ERRO ao montar (veja $HOME_GAB/build.log)"; exit 1; }
  echo "painel montado"
}

ligar() {
  no_ar && return 0
  montar
  cd "$APP/servidor"
  DADOS="$HOME_GAB" PORTA="$PORT" WEB="$APP/web/dist" nohup python3 -u servidor.py >> "$LOG" 2>&1 &
  echo $! > "$PID"
  i=0; until no_ar; do i=$((i+1)); [ $i -gt 40 ] && { echo "ERRO: o Meu Negócio não ligou (veja $LOG)"; exit 1; }; sleep 0.5; done
  echo "Meu Negócio ligado"
}

status() {
  if no_ar; then
    echo "Meu Negócio: ligado ($BASE/dashboard)"
    meu_pid && echo "processo: $(cat "$PID")"
  else
    echo "Meu Negócio: desligado"
  fi
  echo "dados: $HOME_GAB"
}

parar() {
  if meu_pid; then
    kill "$(cat "$PID")" 2>/dev/null || true
    i=0; while meu_pid && [ $i -lt 20 ]; do i=$((i+1)); sleep 0.25; done
    rm -f "$PID"
    echo "Meu Negócio desligado."
  elif no_ar; then
    echo "Tem um Meu Negócio no ar na porta $PORT que não foi ligado por este script; não mexi nele."
  else
    rm -f "$PID"
    echo "Meu Negócio já estava desligado."
  fi
}

abrir() {
  case "${1:-dashboard}" in
    dashboard|crm|projetos|planner|financeiro) destino="${1:-dashboard}" ;;
    *) echo "destino desconhecido: $1 (use dashboard, crm, projetos, planner ou financeiro)"; exit 1 ;;
  esac
  ligar
  abrir_url "$BASE/$destino"
  echo "PRONTO: $BASE/$destino"
}

resumo() {
  ligar >/dev/null
  curl -fsS -m 15 "$BASE/api/ogab/resumo"
  echo
}

empresa() {
  # o Claude manda os dados do negócio que já conhece (nome, CNPJ/CPF, contatos, logo...) para o primeiro acesso
  [ -f "$1" ] || { echo "uso: negocio.sh empresa <arquivo.json>"; exit 1; }
  ligar >/dev/null
  curl -fsS -m 15 -H "Content-Type: application/json" --data-binary "@$1" "$BASE/api/ogab/empresa"
  echo
}

case "${1:-abrir}" in
  status) status ;;
  parar) parar ;;
  resumo) resumo ;;
  empresa) empresa "$2" ;;
  abrir) abrir "$2" ;;
  dashboard|crm|projetos|planner|financeiro) abrir "$1" ;;
  *) echo "uso: negocio.sh [abrir [dashboard|crm|projetos|planner|financeiro]|status|parar|resumo|empresa <arquivo.json>]"; exit 1 ;;
esac
