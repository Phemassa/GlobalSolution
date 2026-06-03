import cv2
import numpy as np
import pytest

from src.vision.analyze_image import analyze_image_array, analyze_image_bytes


def test_analyze_image_array_returns_expected_keys() -> None:
    image = np.full((120, 160, 3), 220, dtype=np.uint8)
    result = analyze_image_array(image)

    assert "condition" in result
    assert "rain_alert" in result
    assert "cloudiness_score" in result
    assert "rain_risk_score" in result


def test_analyze_image_bytes_decodes_and_analyzes() -> None:
    image = np.zeros((120, 160, 3), dtype=np.uint8)
    image[:, :, 0] = 120
    image[:, :, 1] = 140
    image[:, :, 2] = 160

    ok, encoded = cv2.imencode(".jpg", image)
    assert ok

    result = analyze_image_bytes(encoded.tobytes())
    assert 0.0 <= result["cloudiness_score"] <= 100.0
    assert 0.0 <= result["rain_risk_score"] <= 100.0


def test_analyze_image_bytes_invalid_payload() -> None:
    with pytest.raises(ValueError):
        analyze_image_bytes(b"not-an-image")
