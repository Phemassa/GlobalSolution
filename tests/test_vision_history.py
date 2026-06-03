from pathlib import Path

from src.vision.history import append_vision_history, load_vision_history


def test_append_and_load_vision_history(tmp_path: Path) -> None:
    analysis = {
        "condition": "overcast",
        "rain_alert": "high",
        "cloudiness_score": 88.2,
        "rain_risk_score": 81.4,
        "brightness": 162.0,
        "contrast": 22.1,
        "edge_density": 0.043,
    }

    history_path = append_vision_history(
        base_dir=tmp_path,
        source="test",
        filename="sample.jpg",
        analysis=analysis,
    )

    assert history_path.exists()

    history_df = load_vision_history(tmp_path)
    assert not history_df.empty
    assert {"source", "filename", "condition", "rain_risk_score"}.issubset(history_df.columns)

    latest = history_df.iloc[-1]
    assert latest["source"] == "test"
    assert latest["filename"] == "sample.jpg"
    assert latest["condition"] == "overcast"
