#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
API_URL="http://$API_HOST:$API_PORT"
MAX_RETRIES="${MAX_RETRIES:-30}"
RETRY_DELAY_SEC="${RETRY_DELAY_SEC:-1}"

if [[ ! -d ".venv" ]]; then
  echo "[smoke] ambiente .venv nao encontrado. execute: bash scripts/setup.sh"
  exit 1
fi

source .venv/bin/activate

started_api=0
api_pid=""

cleanup() {
  if [[ "$started_api" == "1" ]] && [[ -n "$api_pid" ]] && kill -0 "$api_pid" 2>/dev/null; then
    echo "[smoke] encerrando API iniciada pelo script..."
    kill "$api_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

wait_for_health() {
  local attempt
  for ((attempt = 1; attempt <= MAX_RETRIES; attempt++)); do
    if curl -fsS "$API_URL/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$RETRY_DELAY_SEC"
  done
  return 1
}

if ! curl -fsS "$API_URL/health" >/dev/null 2>&1; then
  echo "[smoke] API nao encontrada em $API_URL. iniciando localmente..."
  python src/api/main.py >/tmp/gs_smoke_api.log 2>&1 &
  api_pid=$!
  started_api=1
fi

echo "[smoke] aguardando API ficar saudavel..."
if ! wait_for_health; then
  echo "[smoke][erro] API nao respondeu em $API_URL/health"
  if [[ -f /tmp/gs_smoke_api.log ]]; then
    echo "[smoke] ultimas linhas do log da API:"
    tail -n 20 /tmp/gs_smoke_api.log || true
  fi
  exit 1
fi

echo "[smoke] PASS health"
curl -fsS "$API_URL/health" >/tmp/gs_smoke_health.json

echo "[smoke] executando treino via POST /train"
curl -fsS -X POST "$API_URL/train" >/tmp/gs_smoke_train.json
echo "[smoke] PASS train"

echo "[smoke] validando GET /predict"
curl -fsS "$API_URL/predict" >/tmp/gs_smoke_predict.json
echo "[smoke] PASS predict"

echo "[smoke] validando GET /report/summary"
curl -fsS "$API_URL/report/summary" >/tmp/gs_smoke_report.json
echo "[smoke] PASS report"

echo "[smoke] smoke test concluido com sucesso"
