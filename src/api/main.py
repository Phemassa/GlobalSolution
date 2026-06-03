from fastapi import FastAPI
import sys
from pathlib import Path

import pandas as pd
from fastapi import HTTPException
from joblib import load

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ml.train_baseline import FEATURE_COLUMNS, train_baseline

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
    model_path = processed_dir / "baseline_model.joblib"
    dataset_path = processed_dir / "training_dataset.csv"

    if not model_path.exists() or not dataset_path.exists():
        raise HTTPException(status_code=400, detail="Modelo/dataset ausentes. Execute POST /train primeiro.")

    model = load(model_path)
    dataset = pd.read_csv(dataset_path)
    if dataset.empty:
        raise HTTPException(status_code=400, detail="Dataset vazio.")

    latest = dataset.iloc[-1]
    features = latest[FEATURE_COLUMNS].to_frame().T
    prediction = float(model.predict(features)[0])

    return {
        "prediction_next_hour_temp": prediction,
        "latest_timestamp": str(latest["timestamp"]),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
