import streamlit as st
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

from src.ml.train_baseline import train_baseline

st.set_page_config(page_title="GS Climate Monitor", layout="wide")

st.title("Global Solution 2026.1")
st.subheader("Monitoramento Climatico Espacial - MVP")

processed_dir = ROOT / "data" / "processed"
metrics_file = processed_dir / "metrics.json"
predictions_file = processed_dir / "predictions.csv"
dataset_file = processed_dir / "training_dataset.csv"
leaderboard_file = processed_dir / "model_leaderboard.csv"

if st.button("Treinar baseline agora"):
	result = train_baseline(base_dir=ROOT, use_api=True)
	st.success(f"Treinamento concluido. Modelo salvo em {result['model_path']}")

mae_value = "Pending"
model_name = "Pending"
if metrics_file.exists():
	metrics_data = json.loads(metrics_file.read_text(encoding="utf-8"))
	mae_value = f"{metrics_data.get('mae', 0.0):.3f}"
	model_name = str(metrics_data.get("model", "Pending"))

col1, col2, col3 = st.columns(3)
col1.metric("Status pipeline", "Ready" if dataset_file.exists() else "Bootstrapped")
col2.metric("Melhor modelo", model_name)
col3.metric("MAE", mae_value)

st.caption("Modulo CV segue no backlog do proximo incremento.")

if dataset_file.exists():
	st.markdown("### Dataset processado (ultimas linhas)")
	st.dataframe(pd.read_csv(dataset_file).tail(10), use_container_width=True)

if predictions_file.exists():
	st.markdown("### Predicoes baseline")
	st.dataframe(pd.read_csv(predictions_file).tail(10), use_container_width=True)
else:
	st.info("Execute o treinamento baseline para gerar predicoes e metricas.")

if leaderboard_file.exists():
	st.markdown("### Comparativo de modelos")
	st.dataframe(pd.read_csv(leaderboard_file), use_container_width=True)
