from __future__ import annotations

import threading
from datetime import datetime
from typing import Any

import joblib
import numpy as np
import pandas as pd
import requests
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from config import (
    BUDAPEST_LAT,
    BUDAPEST_LON,
    BUDAPEST_TIMEZONE,
    CHARGE_START_HOUR,
    DATA_DIR,
    FEATURE_COLUMNS,
    PIPELINE_FILE,
    PLUGIN_TIME,
    PLUGOUT_TIME,
    PRICE_FILE,
    SPREAD_THRESHOLD,
    SUPPORTED_END_YEAR,
    SUPPORTED_START_YEAR,
    WEATHER_COLUMNS,
    WEATHER_FILE,
)


_model_lock = threading.Lock()


def get_snapshot_end(start_hour: pd.Timestamp) -> pd.Timestamp:
    start_hour = pd.Timestamp(start_hour).floor("h")
    natural_24h_end = start_hour + pd.Timedelta(hours=23)
    next_day_cap_end = start_hour.normalize() + pd.Timedelta(days=1, hours=17)
    return min(natural_24h_end, next_day_cap_end)


def to_budapest_naive_timestamp(value: str | pd.Timestamp | datetime) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize(BUDAPEST_TIMEZONE)
    else:
        ts = ts.tz_convert(BUDAPEST_TIMEZONE)
    return ts.tz_localize(None)


def add_time_features(df: pd.DataFrame, datetime_col: str = "Datetime") -> pd.DataFrame:
    df = df.copy()
    dt = pd.to_datetime(df[datetime_col])
    iso = dt.dt.isocalendar()

    df["hour"] = dt.dt.hour
    df["weekday"] = dt.dt.weekday
    df["month"] = dt.dt.month
    df["year"] = dt.dt.year
    df["iso_week"] = iso.week.astype(int)
    df["day_of_year"] = dt.dt.dayofyear
    df["is_weekend"] = (dt.dt.weekday >= 5).astype(int)
    return df


def load_price_data() -> pd.DataFrame:
    price_df = pd.read_csv(DATA_DIR / PRICE_FILE)
    price_df = price_df.copy()

    if "Datetime (Local)" in price_df.columns:
        price_df["Datetime"] = pd.to_datetime(price_df["Datetime (Local)"], errors="coerce")
    elif "Datetime" in price_df.columns:
        price_df["Datetime"] = pd.to_datetime(price_df["Datetime"], errors="coerce")
    else:
        raise ValueError("No datetime column found in the price dataset.")

    if "Price (EUR/MWhe)" in price_df.columns:
        price_df["Price"] = pd.to_numeric(price_df["Price (EUR/MWhe)"], errors="coerce") / 1000.0
    elif "Price" in price_df.columns:
        price_df["Price"] = pd.to_numeric(price_df["Price"], errors="coerce")
    else:
        raise ValueError("No price column found in the price dataset.")

    price_df = price_df[["Datetime", "Price"]].dropna()
    price_df = (
        price_df.groupby("Datetime", as_index=False)["Price"]
        .mean()
        .sort_values("Datetime")
        .reset_index(drop=True)
    )
    return price_df


def load_weather_data() -> pd.DataFrame:
    weather_df = pd.read_csv(DATA_DIR / WEATHER_FILE, sep=";")
    weather_df = weather_df[["time", "temp", "clouds", "visibility", "precipitation"]].copy()
    weather_df["Datetime"] = pd.to_datetime(weather_df["time"], dayfirst=True, errors="coerce")

    clouds_mapping = {
        "no clouds": 0.0,
        "10%  or less, but not 0": 0.05,
        "20–30%.": 0.25,
        "40%.": 0.4,
        "50%.": 0.5,
        "60%.": 0.6,
        "70 – 80%.": 0.75,
        "90  or more, but not 100%": 0.95,
        "100%.": 1.0,
        "Sky obscured by fog and/or other meteorological phenomena.": 0.0,
    }

    weather_df["temp"] = pd.to_numeric(weather_df["temp"], errors="coerce")
    weather_df["clouds"] = weather_df["clouds"].map(clouds_mapping).fillna(0.0)

    weather_df["visibility"] = (
        weather_df["visibility"]
        .astype(str)
        .str.strip()
        .replace({"less than 0.1": "0", "": np.nan})
    )
    weather_df["visibility"] = pd.to_numeric(weather_df["visibility"], errors="coerce")

    weather_df["precipitation"] = (
        weather_df["precipitation"]
        .astype(str)
        .str.strip()
        .replace({"No precipitation": "0", "": np.nan})
    )
    weather_df["precipitation"] = pd.to_numeric(weather_df["precipitation"], errors="coerce")

    weather_features_df = weather_df[["Datetime", *WEATHER_COLUMNS]].dropna(subset=["Datetime"]).copy()
    weather_features_df = (
        weather_features_df.sort_values("Datetime")
        .drop_duplicates(subset=["Datetime"])
        .reset_index(drop=True)
    )
    return weather_features_df


def build_training_frame() -> pd.DataFrame:
    price_df = load_price_data()
    weather_df = load_weather_data()

    training_start = max(price_df["Datetime"].min(), weather_df["Datetime"].min())
    training_end = min(price_df["Datetime"].max(), weather_df["Datetime"].max())

    if pd.isna(training_start) or pd.isna(training_end) or training_start > training_end:
        raise ValueError("No overlap found between price and weather datasets.")

    price_overlap_df = price_df[price_df["Datetime"].between(training_start, training_end)].copy()
    weather_overlap_df = weather_df[weather_df["Datetime"].between(training_start, training_end)].copy()

    train_df = price_overlap_df.merge(weather_overlap_df, on="Datetime", how="inner")
    train_df = add_time_features(train_df, "Datetime")
    train_df = train_df.sort_values("Datetime").reset_index(drop=True)
    train_df[WEATHER_COLUMNS] = train_df[WEATHER_COLUMNS].ffill().bfill()
    return train_df


def train_and_store_pipeline() -> dict[str, Any]:
    train_df = build_training_frame()

    pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=200,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    pipeline.fit(train_df[FEATURE_COLUMNS], train_df["Price"])

    artifact = {
        "pipeline": pipeline,
        "feature_columns": FEATURE_COLUMNS,
        "weather_medians": {col: float(train_df[col].median()) for col in WEATHER_COLUMNS},
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "training_start": str(train_df["Datetime"].min()),
        "training_end": str(train_df["Datetime"].max()),
    }
    joblib.dump(artifact, PIPELINE_FILE)
    return artifact


def get_or_train_artifact() -> dict[str, Any]:
    if PIPELINE_FILE.exists():
        return joblib.load(PIPELINE_FILE)

    with _model_lock:
        if PIPELINE_FILE.exists():
            return joblib.load(PIPELINE_FILE)
        return train_and_store_pipeline()


def get_open_meteo_hourly_weather_for_request(
    request_timestamp: str | pd.Timestamp | datetime,
    latitude: float = BUDAPEST_LAT,
    longitude: float = BUDAPEST_LON,
    timezone: str = BUDAPEST_TIMEZONE,
) -> pd.DataFrame:
    request_timestamp = to_budapest_naive_timestamp(request_timestamp)
    start_hour = request_timestamp.floor("h")
    end_hour = get_snapshot_end(start_hour)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,cloud_cover,visibility,precipitation",
        "timezone": timezone,
        "start_hour": start_hour.strftime("%Y-%m-%dT%H:%M"),
        "end_hour": end_hour.strftime("%Y-%m-%dT%H:%M"),
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "hourly" not in data:
        raise ValueError("Open-Meteo response does not contain 'hourly' data.")

    hourly = data["hourly"]
    weather_df = pd.DataFrame(
        {
            "Datetime": pd.to_datetime(hourly["time"]),
            "temp": pd.to_numeric(hourly["temperature_2m"], errors="coerce"),
            "clouds": pd.to_numeric(hourly["cloud_cover"], errors="coerce") / 100.0,
            "visibility": pd.to_numeric(hourly["visibility"], errors="coerce") / 1000.0,
            "precipitation": pd.to_numeric(hourly["precipitation"], errors="coerce"),
        }
    )

    expected_hours = pd.date_range(start=start_hour, end=end_hour, freq="h")
    weather_df = (
        pd.DataFrame({"Datetime": expected_hours})
        .merge(weather_df, on="Datetime", how="left")
        .sort_values("Datetime")
        .reset_index(drop=True)
    )
    weather_df[WEATHER_COLUMNS] = weather_df[WEATHER_COLUMNS].ffill().bfill()
    return weather_df


def build_prediction_frame(
    request_timestamp: str | pd.Timestamp | datetime,
    artifact: dict[str, Any],
    latitude: float = BUDAPEST_LAT,
    longitude: float = BUDAPEST_LON,
    timezone: str = BUDAPEST_TIMEZONE,
) -> pd.DataFrame:
    request_timestamp = to_budapest_naive_timestamp(request_timestamp)
    start_hour = request_timestamp.floor("h")
    end_hour = get_snapshot_end(start_hour)
    schedule_hours = pd.date_range(start=start_hour, end=end_hour, freq="h")

    future_df = pd.DataFrame({"Datetime": schedule_hours})
    future_df = add_time_features(future_df, "Datetime")

    weather_df = get_open_meteo_hourly_weather_for_request(
        request_timestamp=request_timestamp,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
    )

    future_df = future_df.merge(weather_df, on="Datetime", how="left")
    future_df[WEATHER_COLUMNS] = future_df[WEATHER_COLUMNS].ffill().bfill()

    for col in WEATHER_COLUMNS:
        future_df[col] = future_df[col].fillna(artifact["weather_medians"][col])

    future_df["PredictedPrice"] = artifact["pipeline"].predict(future_df[artifact["feature_columns"]])
    future_df["date"] = future_df["Datetime"].dt.normalize()
    future_df["hour"] = future_df["Datetime"].dt.hour
    return future_df


def get_snapshot_metrics(prediction_frame: pd.DataFrame, snapshot_start: str | pd.Timestamp | datetime) -> dict[str, Any]:
    snapshot_start = to_budapest_naive_timestamp(snapshot_start).floor("h")
    snapshot_end = get_snapshot_end(snapshot_start)
    snapshot_day = snapshot_start.normalize()
    next_day = snapshot_day + pd.Timedelta(days=1)

    horizon_df = prediction_frame[
        prediction_frame["Datetime"].between(snapshot_start, snapshot_end)
    ].copy().sort_values("Datetime")

    day_df = horizon_df[horizon_df["date"] == snapshot_day].copy()
    next_day_df = horizon_df[horizon_df["date"] == next_day].copy()

    if day_df.empty:
        raise ValueError(f"No predicted price data available for {snapshot_day.date()}.")

    # If the request arrives during the overnight charging window
    # (for example 01:00), keep charging until PLUGOUT_TIME.
    if snapshot_start.hour < PLUGOUT_TIME:
        forced_charge_df = horizon_df[
            (horizon_df["Datetime"] >= snapshot_start) &
            (horizon_df["date"] == snapshot_day) &
            (horizon_df["hour"] < PLUGOUT_TIME)
        ].copy().sort_values("Datetime")

        return {
            "snapshot_start": snapshot_start,
            "snapshot_end": snapshot_end,
            "evening_avg_price": None,
            "avg_discharge_price": None,
            "avg_charge_price": None,
            "spread": None,
            "is_profitable": True,
            "discharge_hours": set(),
            "charge_hours": set(forced_charge_df["Datetime"]),
        }

    evening_df = day_df[day_df["hour"] >= max(PLUGIN_TIME, snapshot_start.hour)].copy()
    evening_avg_price = evening_df["PredictedPrice"].mean() if not evening_df.empty else np.nan

    discharge_hours_df = evening_df[
        evening_df["PredictedPrice"] > evening_avg_price
    ].copy().sort_values("Datetime")

    same_night_start = max(CHARGE_START_HOUR, snapshot_start.hour)
    same_night_df = day_df[day_df["hour"] >= same_night_start].copy()
    next_morning_df = next_day_df[next_day_df["hour"] < PLUGOUT_TIME].copy()
    charge_window_df = (
        pd.concat([same_night_df, next_morning_df], ignore_index=True)
        .sort_values("Datetime")
        .drop_duplicates(subset=["Datetime"])
    )

    avg_discharge_price = discharge_hours_df["PredictedPrice"].mean() if not discharge_hours_df.empty else np.nan
    avg_charge_price = charge_window_df["PredictedPrice"].mean() if not charge_window_df.empty else np.nan

    spread = (
        avg_discharge_price - avg_charge_price
        if pd.notna(avg_discharge_price) and pd.notna(avg_charge_price)
        else np.nan
    )
    is_profitable = pd.notna(spread) and spread >= SPREAD_THRESHOLD

    if not is_profitable:
        discharge_hours_df = discharge_hours_df.iloc[0:0].copy()
        charge_window_df = charge_window_df.iloc[0:0].copy()

    return {
        "snapshot_start": snapshot_start,
        "snapshot_end": snapshot_end,
        "evening_avg_price": None if pd.isna(evening_avg_price) else float(evening_avg_price),
        "avg_discharge_price": None if pd.isna(avg_discharge_price) else float(avg_discharge_price),
        "avg_charge_price": None if pd.isna(avg_charge_price) else float(avg_charge_price),
        "spread": None if pd.isna(spread) else float(spread),
        "is_profitable": bool(is_profitable),
        "discharge_hours": set(discharge_hours_df["Datetime"]),
        "charge_hours": set(charge_window_df["Datetime"]),
    }


def decide_snapshot_command(ts: str | pd.Timestamp | datetime, snapshot_metrics: dict[str, Any]) -> str:
    ts = to_budapest_naive_timestamp(ts).floor("h")
    if ts < snapshot_metrics["snapshot_start"] or ts > snapshot_metrics["snapshot_end"]:
        raise ValueError("Timestamp is outside the snapshot window.")

    if not snapshot_metrics["is_profitable"]:
        return "0"
    if ts in snapshot_metrics["discharge_hours"]:
        return "-1"
    if ts in snapshot_metrics["charge_hours"]:
        return "1"
    return "0"


def build_command_schedule(
    request_timestamp: str | pd.Timestamp | datetime,
    artifact: dict[str, Any],
    latitude: float = BUDAPEST_LAT,
    longitude: float = BUDAPEST_LON,
) -> tuple[list[dict[str, str]], pd.DataFrame, dict[str, Any]]:
    request_timestamp = to_budapest_naive_timestamp(request_timestamp)
    start_hour = request_timestamp.floor("h")
    year = start_hour.year

    if year < SUPPORTED_START_YEAR or year > SUPPORTED_END_YEAR:
        raise ValueError(
            f"Year {year} is outside the supported model range {SUPPORTED_START_YEAR}-{SUPPORTED_END_YEAR}."
        )

    prediction_df = build_prediction_frame(
        request_timestamp=request_timestamp,
        artifact=artifact,
        latitude=latitude,
        longitude=longitude,
        timezone=BUDAPEST_TIMEZONE,
    )

    snapshot_metrics = get_snapshot_metrics(prediction_df, snapshot_start=start_hour)
    schedule_hours = pd.date_range(start=start_hour, end=snapshot_metrics["snapshot_end"], freq="h")

    commands: list[dict[str, str]] = []
    for ts in schedule_hours:
        command = decide_snapshot_command(ts, snapshot_metrics)
        commands.append({ts.strftime("%Y-%m-%d %H:%M:%S"): command})

    return commands, prediction_df, snapshot_metrics


def get_app_response(
    request_timestamp: str | pd.Timestamp | datetime | None = None,
    lat: float = BUDAPEST_LAT,
    lon: float = BUDAPEST_LON,
) -> dict[str, Any]:
    if request_timestamp is None:
        request_timestamp = datetime.now()

    artifact = get_or_train_artifact()
    ts = to_budapest_naive_timestamp(request_timestamp)
    snapshot_start = ts.floor("h")
    snapshot_end = get_snapshot_end(snapshot_start)
    schedule, _, snapshot_metrics = build_command_schedule(
        request_timestamp=request_timestamp,
        artifact=artifact,
        latitude=lat,
        longitude=lon,
    )

    return {
        "request_timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "snapshot_start": snapshot_start.strftime("%Y-%m-%d %H:%M:%S"),
        "snapshot_end": snapshot_end.strftime("%Y-%m-%d %H:%M:%S"),
        "model_year": int(ts.year),
        "pipeline_file": str(PIPELINE_FILE.name),
        "pipeline_trained_at": artifact["trained_at"],
        "commands": schedule,
        "spread": snapshot_metrics["spread"],
        "is_profitable": snapshot_metrics["is_profitable"],
    }
