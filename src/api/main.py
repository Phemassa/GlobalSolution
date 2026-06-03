from fastapi import FastAPI
import sys
from pathlib import Path

import pandas as pd
from fastapi import File, HTTPException, UploadFile
from joblib import load

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ml.train_baseline import FEATURE_COLUMNS, train_baseline
from src.api.reporting import build_summary_report
from src.vision.analyze_image import analyze_image_bytes
from src.vision.history import append_vision_history, load_vision_history

app = FastAPI(title="GS Climate API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "api"}


@app.post("/train")
def train() -> dict:
    result = train_baseline(base_dir=ROOT, use_api=True)
    return {"status": "trained", **result}


@app.get("/predict")
def predict_stub() -> dict:
    processed_dir = ROOT / "data" / "processed"
    model_path = processed_dir / "best_model.joblib"
    dataset_path = processed_dir / "training_dataset.csv"
    metrics_path = processed_dir / "metrics.json"

    if not model_path.exists() or not dataset_path.exists():
        raise HTTPException(status_code=400, detail="Modelo/dataset ausentes. Execute POST /train primeiro.")

    model = load(model_path)
    dataset = pd.read_csv(dataset_path)
    if dataset.empty:
        raise HTTPException(status_code=400, detail="Dataset vazio.")

    latest = dataset.iloc[-1]
    features = latest[FEATURE_COLUMNS].to_frame().T
    prediction = float(model.predict(features)[0])

    model_name = "unknown"
    if metrics_path.exists():
        import json

        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        model_name = str(metrics.get("model", "unknown"))

    return {
        "prediction_next_hour_temp": prediction,
        "latest_timestamp": str(latest["timestamp"]),
        "model": model_name,
    }


@app.post("/vision/analyze")
async def vision_analyze(file: UploadFile = File(...)) -> dict:
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Arquivo de imagem vazio")

    try:
        analysis = analyze_image_bytes(image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    history_path = append_vision_history(
        base_dir=ROOT,
        source="api",
        filename=file.filename or "unknown",
        analysis=analysis,
    )

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "analysis": analysis,
        "history_path": str(history_path),
    }


@app.get("/vision/history")
def vision_history(limit: int = 50) -> dict:
    history_df = load_vision_history(ROOT)
    if history_df.empty:
        return {"count": 0, "items": []}

    limited = history_df.sort_values("timestamp_utc", ascending=False).head(limit)
    return {"count": int(len(limited)), "items": limited.to_dict(orient="records")}


@app.get("/report/summary")
def report_summary() -> dict:
    return build_summary_report(ROOT)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
