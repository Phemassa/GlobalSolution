from pathlib import Path

import pandas as pd
from sklearn.dummy import DummyRegressor


def train_baseline(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Baseline simples para validar o pipeline antes do modelo final.
    x = pd.DataFrame({"feature": [0, 1, 2, 3]})
    y = pd.Series([10.0, 10.5, 11.0, 11.5])

    model = DummyRegressor(strategy="mean")
    model.fit(x, y)

    model_path = output_dir / "baseline_model.txt"
    model_path.write_text("dummy_regressor_mean", encoding="utf-8")
    return model_path


if __name__ == "__main__":
    artifact = train_baseline(Path("data/processed"))
    print(f"Baseline treinado: {artifact}")
