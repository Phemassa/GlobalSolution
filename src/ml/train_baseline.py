from pathlib import Path
import json

import pandas as pd
from joblib import dump
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.ensemble import RandomForestRegressor

try:
    from .data_pipeline import build_training_dataset
except ImportError:
    from data_pipeline import build_training_dataset


FEATURE_COLUMNS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "hour",
    "day_of_week",
    "is_weekend",
    "hour_sin",
    "hour_cos",
    "temp_lag_1",
    "humidity_lag_1",
]


def train_baseline(base_dir: Path, use_api: bool = True) -> dict:
    processed_dir = base_dir / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    dataset = build_training_dataset(base_dir=base_dir, use_api=use_api)
    x = dataset[FEATURE_COLUMNS]
    y = dataset["target_temp_next_hour"]

    split_idx = int(len(dataset) * 0.8)
    if split_idx < 2:
        split_idx = max(1, len(dataset) - 1)

    x_train, x_test = x.iloc[:split_idx], x.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    if x_test.empty:
        x_test = x_train.tail(1)
        y_test = y_train.tail(1)

    models = {
        "LinearRegression": LinearRegression(),
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=120,
            max_depth=8,
            random_state=42,
        ),
    }

    leaderboard = []
    best_name = None
    best_mae = float("inf")
    best_predictions = None
    best_model = None

    for model_name, model in models.items():
        model.fit(x_train, y_train)
        pred = model.predict(x_test)
        mae = float(mean_absolute_error(y_test, pred))
        leaderboard.append({"model": model_name, "mae": mae})

        if mae < best_mae:
            best_mae = mae
            best_name = model_name
            best_predictions = pred
            best_model = model

    model_path = processed_dir / "best_model.joblib"
    metrics_path = processed_dir / "metrics.json"
    predictions_path = processed_dir / "predictions.csv"
    leaderboard_path = processed_dir / "model_leaderboard.csv"

    if best_model is None or best_predictions is None or best_name is None:
        raise RuntimeError("Falha ao selecionar melhor modelo")

    dump(best_model, model_path)

    leaderboard_df = pd.DataFrame(leaderboard).sort_values("mae").reset_index(drop=True)
    leaderboard_df.to_csv(leaderboard_path, index=False)

    metrics_payload = {
        "model": best_name,
        "mae": best_mae,
        "rows_train": int(len(x_train)),
        "rows_test": int(len(x_test)),
        "features": FEATURE_COLUMNS,
        "best_model_path": str(model_path),
    }
    metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    pred_df = pd.DataFrame(
        {
            "timestamp": dataset.iloc[x_test.index]["timestamp"].astype(str).values,
            "target_real": y_test.values,
            "target_pred": best_predictions,
        }
    )
    pred_df.to_csv(predictions_path, index=False)

    return {
        "model_path": str(model_path),
        "metrics_path": str(metrics_path),
        "predictions_path": str(predictions_path),
        "leaderboard_path": str(leaderboard_path),
    }


if __name__ == "__main__":
    artifact = train_baseline(base_dir=Path("."), use_api=True)
    print(f"Baseline treinado: {artifact['model_path']}")
