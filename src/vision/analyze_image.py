from __future__ import annotations

import numpy as np
import cv2


def _clip01(value: float) -> float:
    return float(max(0.0, min(1.0, value)))


def analyze_image_array(image_bgr: np.ndarray) -> dict:
    if image_bgr is None or image_bgr.size == 0:
        raise ValueError("Imagem invalida para analise")

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    brightness = float(gray.mean())
    contrast = float(gray.std())
    saturation = float(hsv[:, :, 1].mean())
    blue_mean = float(image_bgr[:, :, 0].mean())
    green_mean = float(image_bgr[:, :, 1].mean())
    red_mean = float(image_bgr[:, :, 2].mean())

    edges = cv2.Canny(gray, threshold1=60, threshold2=120)
    edge_density = float((edges > 0).mean())

    # Ceu limpo tende a ser mais azul e mais saturado; nuvens densas reduzem isso.
    blue_dominance = _clip01((blue_mean - ((red_mean + green_mean) / 2.0)) / 75.0)
    saturation_factor = min(saturation / 110.0, 1.0)
    clear_sky_bonus = blue_dominance * saturation_factor

    cloudiness = _clip01(
        (brightness / 255.0) * 0.20
        + (1.0 - min(contrast / 64.0, 1.0)) * 0.35
        + (1.0 - min(edge_density / 0.15, 1.0)) * 0.25
        + (1.0 - blue_dominance) * 0.20
        - clear_sky_bonus * 0.28
    )

    rain_risk = _clip01(
        cloudiness * 0.6
        + (1.0 - saturation_factor) * 0.25
        + (1.0 - min(edge_density / 0.1, 1.0)) * 0.15
    )

    if cloudiness < 0.45:
        condition = "clear"
    elif cloudiness < 0.70:
        condition = "partly_cloudy"
    else:
        condition = "overcast"

    if rain_risk < 0.35:
        rain_alert = "low"
    elif rain_risk < 0.70:
        rain_alert = "moderate"
    else:
        rain_alert = "high"

    return {
        "condition": condition,
        "rain_alert": rain_alert,
        "cloudiness_score": round(cloudiness * 100.0, 2),
        "rain_risk_score": round(rain_risk * 100.0, 2),
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "edge_density": round(edge_density, 4),
    }


def analyze_image_bytes(image_bytes: bytes) -> dict:
    np_buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Nao foi possivel decodificar a imagem")
    return analyze_image_array(image)
