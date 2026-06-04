#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
DASH_PORT="${DASH_PORT:-8501}"

if [[ ! -d ".venv" ]]; then
  echo "[stack] ambiente .venv nao encontrado. execute: bash scripts/setup.sh"
  exit 1
fi

source .venv/bin/activate

LOG_DIR="$ROOT_DIR/data/processed/runtime_logs"
mkdir -p "$LOG_DIR"

API_LOG="$LOG_DIR/api.log"
DASH_LOG="$LOG_DIR/dashboard.log"

cleanup() {
  echo "[stack] encerrando processos..."
  if [[ -n "${API_PID:-}" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
  fi
  if [[ -n "${DASH_PID:-}" ]] && kill -0 "$DASH_PID" 2>/dev/null; then
    kill "$DASH_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

echo "[stack] iniciando API em http://$API_HOST:$API_PORT"
python src/api/main.py >"$API_LOG" 2>&1 &
API_PID=$!

echo "[stack] iniciando dashboard em http://127.0.0.1:$DASH_PORT"
streamlit run src/dashboard/app.py --server.port "$DASH_PORT" >"$DASH_LOG" 2>&1 &
DASH_PID=$!

echo "[stack] API log: $API_LOG"
echo "[stack] Dashboard log: $DASH_LOG"
echo "[stack] pressione Ctrl+C para encerrar os dois servicos"

wait "$API_PID" "$DASH_PID"
