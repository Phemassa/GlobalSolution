from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import requests


RAW_COLUMNS = [
    "timestamp",
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
]


def fetch_open_meteo_hourly(
    latitude: float = -23.5505,
    longitude: float = -46.6333,
    timezone: str = "America/Sao_Paulo",
) -> pd.DataFrame:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "forecast_days": 3,
        "timezone": timezone,
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    hourly = payload.get("hourly", {})

    df = pd.DataFrame(
        {
            "timestamp": hourly.get("time", []),
            "temperature_2m": hourly.get("temperature_2m", []),
            "relative_humidity_2m": hourly.get("relative_humidity_2m", []),
            "precipitation": hourly.get("precipitation", []),
            "wind_speed_10m": hourly.get("wind_speed_10m", []),
        }
    )
    if df.empty:
        raise ValueError("Open-Meteo retornou dataset vazio")

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=False)
    return df[RAW_COLUMNS]


def generate_synthetic_hourly_data(periods: int = 72) -> pd.DataFrame:
    rng = np.random.default_rng(seed=42)
    timestamps = pd.date_range("2026-01-01", periods=periods, freq="h")

    base_temp = 22 + 5 * np.sin(np.linspace(0, 3 * np.pi, periods))
    temperature = base_temp + rng.normal(0, 0.8, periods)
    humidity = np.clip(65 - (temperature - 22) * 2 + rng.normal(0, 2, periods), 30, 95)
    precipitation = np.clip(rng.gamma(shape=0.7, scale=1.0, size=periods) - 0.4, 0, None)
    wind = np.clip(rng.normal(11, 2.5, periods), 1, None)

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "temperature_2m": temperature,
            "relative_humidity_2m": humidity,
            "precipitation": precipitation,
            "wind_speed_10m": wind,
        }
    )


def build_training_dataset(base_dir: Path, use_api: bool = True) -> pd.DataFrame:
    data_dir_raw = base_dir / "data" / "raw"
    data_dir_processed = base_dir / "data" / "processed"
    data_dir_raw.mkdir(parents=True, exist_ok=True)
    data_dir_processed.mkdir(parents=True, exist_ok=True)

    if use_api:
        try:
            source_df = fetch_open_meteo_hourly()
        except Exception:
            source_df = generate_synthetic_hourly_data()
    else:
        source_df = generate_synthetic_hourly_data()

    source_df = source_df.sort_values("timestamp").reset_index(drop=True)
    source_df["hour"] = source_df["timestamp"].dt.hour
    source_df["day_of_week"] = source_df["timestamp"].dt.dayofweek
    source_df["is_weekend"] = source_df["day_of_week"].isin([5, 6]).astype(int)

    # Features ciclicas para capturar sazonalidade diaria sem descontinuidade.
    source_df["hour_sin"] = np.sin(2 * np.pi * source_df["hour"] / 24)
    source_df["hour_cos"] = np.cos(2 * np.pi * source_df["hour"] / 24)

    source_df["temp_lag_1"] = source_df["temperature_2m"].shift(1)
    source_df["humidity_lag_1"] = source_df["relative_humidity_2m"].shift(1)
    source_df["target_temp_next_hour"] = source_df["temperature_2m"].shift(-1)
    source_df = source_df.dropna().reset_index(drop=True)

    source_df.to_csv(data_dir_raw / "open_meteo_hourly.csv", index=False)
    source_df.to_csv(data_dir_processed / "training_dataset.csv", index=False)
    return source_df