from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


HISTORY_COLUMNS = [
    "timestamp_utc",
    "source",
    "filename",
    "condition",
    "rain_alert",
    "cloudiness_score",
    "rain_risk_score",
    "brightness",
    "contrast",
    "edge_density",
]


def get_history_path(base_dir: Path) -> Path:
    processed_dir = base_dir / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir / "vision_history.csv"


def append_vision_history(base_dir: Path, source: str, filename: str, analysis: dict) -> Path:
    history_path = get_history_path(base_dir)

    row = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "filename": filename,
        "condition": analysis.get("condition"),
        "rain_alert": analysis.get("rain_alert"),
        "cloudiness_score": analysis.get("cloudiness_score"),
        "rain_risk_score": analysis.get("rain_risk_score"),
        "brightness": analysis.get("brightness"),
        "contrast": analysis.get("contrast"),
        "edge_density": analysis.get("edge_density"),
    }

    row_df = pd.DataFrame([row], columns=HISTORY_COLUMNS)
    if history_path.exists():
        history_df = pd.read_csv(history_path)
        if history_df.empty:
            history_df = row_df
        else:
            history_df = pd.concat([history_df, row_df], ignore_index=True)
    else:
        history_df = row_df
    history_df.to_csv(history_path, index=False)
    return history_path


def load_vision_history(base_dir: Path) -> pd.DataFrame:
    history_path = get_history_path(base_dir)
    if not history_path.exists():
        return pd.DataFrame(columns=HISTORY_COLUMNS)

    history_df = pd.read_csv(history_path)
    if "timestamp_utc" in history_df.columns:
        history_df["timestamp_utc"] = pd.to_datetime(history_df["timestamp_utc"], errors="coerce")
    return history_df
