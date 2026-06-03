#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  echo "[demo] criando ambiente virtual..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "[demo] instalando dependencias..."
pip install -r requirements.txt >/dev/null

echo "[demo] treinando baseline e gerando artefatos..."
python src/ml/train_baseline.py

echo "[demo] exibindo resumo consolidado local..."
python - <<'PY'
from pathlib import Path
from src.api.reporting import build_summary_report

report = build_summary_report(Path('.'))
print(report)
PY

echo "[demo] pronto. execute em terminais separados:"
echo "  1) source .venv/bin/activate && python src/api/main.py"
echo "  2) source .venv/bin/activate && streamlit run src/dashboard/app.py"
