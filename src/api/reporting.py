from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.vision.history import load_vision_history


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_summary_report(base_dir: Path) -> dict:
    processed_dir = base_dir / "data" / "processed"
    metrics_path = processed_dir / "metrics.json"
    predictions_path = processed_dir / "predictions.csv"
    dataset_path = processed_dir / "training_dataset.csv"

    model_info = {
        "model": "pending",
        "mae": None,
        "rows_train": 0,
        "rows_test": 0,
    }
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        model_info = {
            "model": str(metrics.get("model", "unknown")),
            "mae": _safe_float(metrics.get("mae"), default=0.0),
            "rows_train": int(metrics.get("rows_train", 0)),
            "rows_test": int(metrics.get("rows_test", 0)),
        }

    latest_prediction = None
    if predictions_path.exists():
        pred_df = pd.read_csv(predictions_path)
        if not pred_df.empty:
            latest = pred_df.iloc[-1]
            latest_prediction = {
                "timestamp": str(latest.get("timestamp", "")),
                "target_real": _safe_float(latest.get("target_real"), default=0.0),
                "target_pred": _safe_float(latest.get("target_pred"), default=0.0),
            }

    dataset_rows = 0
    if dataset_path.exists():
        ds = pd.read_csv(dataset_path)
        dataset_rows = int(len(ds))

    vision_df = load_vision_history(base_dir)
    vision_summary = {
        "count": 0,
        "avg_cloudiness": 0.0,
        "avg_rain_risk": 0.0,
        "last_condition": None,
        "last_alert": None,
    }
    if not vision_df.empty:
        ordered = vision_df.sort_values("timestamp_utc")
        last = ordered.iloc[-1]
        vision_summary = {
            "count": int(len(ordered)),
            "avg_cloudiness": round(_safe_float(ordered["cloudiness_score"].mean()), 2),
            "avg_rain_risk": round(_safe_float(ordered["rain_risk_score"].mean()), 2),
            "last_condition": str(last.get("condition", "")),
            "last_alert": str(last.get("rain_alert", "")),
        }

    return {
        "status": "ready" if model_info["model"] != "pending" else "bootstrapped",
        "ml": model_info,
        "dataset_rows": dataset_rows,
        "latest_prediction": latest_prediction,
        "vision": vision_summary,
    }
