import streamlit as st
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

from src.ml.train_baseline import train_baseline
from src.api.reporting import build_summary_report
from src.vision.analyze_image import analyze_image_bytes
from src.vision.history import append_vision_history, load_vision_history

st.set_page_config(page_title="GS Climate Monitor", layout="wide")

st.title("Global Solution 2026.1")
st.subheader("Monitoramento Climatico Espacial - MVP")

summary = build_summary_report(ROOT)

st.markdown("### Resumo executivo")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Status", str(summary.get("status", "unknown")))
r2.metric("Modelo ativo", str(summary.get("ml", {}).get("model", "pending")))
r3.metric("MAE", str(summary.get("ml", {}).get("mae", "n/a")))
r4.metric("Analises de visao", int(summary.get("vision", {}).get("count", 0)))

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

st.markdown("### Modulo de visao computacional (MVP)")
uploaded_image = st.file_uploader(
	"Envie uma imagem do ceu para estimar cobertura de nuvens e risco de chuva",
	type=["png", "jpg", "jpeg"],
)

if uploaded_image is not None:
	image_bytes = uploaded_image.getvalue()
	st.image(image_bytes, caption="Imagem recebida", use_column_width=True)
	try:
		vision_result = analyze_image_bytes(image_bytes)
		append_vision_history(
			base_dir=ROOT,
			source="dashboard",
			filename=uploaded_image.name,
			analysis=vision_result,
		)
		v1, v2, v3 = st.columns(3)
		v1.metric("Condicao", vision_result["condition"])
		v2.metric("Risco de chuva", f"{vision_result['rain_risk_score']}%")
		v3.metric("Alerta", vision_result["rain_alert"])
		st.json(vision_result)
	except ValueError as exc:
		st.error(f"Falha na analise da imagem: {exc}")

history_df = load_vision_history(ROOT)
if not history_df.empty:
	st.markdown("### Historico de analises de imagem")
	history_sorted = history_df.sort_values("timestamp_utc")
	chart_df = history_sorted[["timestamp_utc", "cloudiness_score", "rain_risk_score"]].set_index("timestamp_utc")
	st.line_chart(chart_df)
	st.dataframe(history_sorted.tail(20), use_container_width=True)

st.markdown("### Relatorio consolidado (JSON)")
st.json(summary)
