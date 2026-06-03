import json
from pathlib import Path

import pandas as pd

from src.api.reporting import build_summary_report
from src.vision.history import append_vision_history


def test_build_summary_report_bootstrapped(tmp_path: Path) -> None:
    report = build_summary_report(tmp_path)
    assert report["status"] == "bootstrapped"
    assert report["ml"]["model"] == "pending"
    assert report["vision"]["count"] == 0


def test_build_summary_report_with_artifacts(tmp_path: Path) -> None:
    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)

    metrics = {
        "model": "LinearRegression",
        "mae": 0.42,
        "rows_train": 10,
        "rows_test": 5,
    }
    (processed / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")

    pd.DataFrame(
        [
            {"timestamp": "2026-01-01 00:00:00", "target_real": 20.0, "target_pred": 19.7},
            {"timestamp": "2026-01-01 01:00:00", "target_real": 20.4, "target_pred": 20.1},
        ]
    ).to_csv(processed / "predictions.csv", index=False)

    pd.DataFrame([{"timestamp": "2026-01-01", "x": 1}]).to_csv(processed / "training_dataset.csv", index=False)

    append_vision_history(
        base_dir=tmp_path,
        source="test",
        filename="img.jpg",
        analysis={
            "condition": "overcast",
            "rain_alert": "high",
            "cloudiness_score": 85.0,
            "rain_risk_score": 80.0,
            "brightness": 120.0,
            "contrast": 15.0,
            "edge_density": 0.03,
        },
    )

    report = build_summary_report(tmp_path)
    assert report["status"] == "ready"
    assert report["ml"]["model"] == "LinearRegression"
    assert report["latest_prediction"] is not None
    assert report["vision"]["count"] == 1
