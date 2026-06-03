from pathlib import Path

import pandas as pd

from src.ml.data_pipeline import build_training_dataset
from src.ml.train_baseline import train_baseline


def test_build_training_dataset_synthetic(tmp_path: Path) -> None:
    dataset = build_training_dataset(base_dir=tmp_path, use_api=False)
    assert not dataset.empty
    assert "target_temp_next_hour" in dataset.columns

    raw_file = tmp_path / "data" / "raw" / "open_meteo_hourly.csv"
    processed_file = tmp_path / "data" / "processed" / "training_dataset.csv"
    assert raw_file.exists()
    assert processed_file.exists()


def test_train_baseline_outputs_artifacts(tmp_path: Path) -> None:
    result = train_baseline(base_dir=tmp_path, use_api=False)

    model_path = Path(result["model_path"])
    metrics_path = Path(result["metrics_path"])
    predictions_path = Path(result["predictions_path"])

    assert model_path.exists()
    assert metrics_path.exists()
    assert predictions_path.exists()

    pred_df = pd.read_csv(predictions_path)
    assert not pred_df.empty
    assert {"target_real", "target_pred"}.issubset(set(pred_df.columns))