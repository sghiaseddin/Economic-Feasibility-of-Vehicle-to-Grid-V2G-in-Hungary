from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

from fastapi import Body

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from config import BUDAPEST_LAT, BUDAPEST_LON
from service import get_app_response, get_or_train_artifact

app = FastAPI(title="V2G Scheduler API", version="1.0.0")


class PredictRequest(BaseModel):
    request_timestamp: Optional[datetime] = Field(
        default=None,
        description="If omitted, the API uses the current server time.",
    )
    lat: float = Field(default=BUDAPEST_LAT)
    lon: float = Field(default=BUDAPEST_LON)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def root() -> dict:
    return {
        "status": "ok",
        "message": "V2G Scheduler API is running. Use POST /predict or POST /train.",
    }


@app.post("/predict")
def predict(payload: Optional[PredictRequest] = Body(default=None)) -> dict:
    try:
        payload = payload or PredictRequest()
        request_timestamp = payload.request_timestamp or datetime.now(ZoneInfo("Europe/Budapest"))
        return get_app_response(
            request_timestamp=request_timestamp,
            lat=payload.lat,
            lon=payload.lon,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/predict")
def predict_get(
    request_timestamp: Optional[datetime] = Query(
        default=None,
        description="If omitted, the API uses the current server time.",
    ),
    lat: float = Query(default=BUDAPEST_LAT),
    lon: float = Query(default=BUDAPEST_LON),
) -> dict:
    try:
        request_timestamp = request_timestamp or datetime.now(ZoneInfo("Europe/Budapest"))
        return get_app_response(
            request_timestamp=request_timestamp,
            lat=lat,
            lon=lon,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/train")
def train() -> dict:
    try:
        artifact = get_or_train_artifact()
        return {
            "status": "ready",
            "pipeline_file": artifact.get("trained_at") and "models/v2g_pipeline.joblib",
            "trained_at": artifact.get("trained_at"),
            "training_start": artifact.get("training_start"),
            "training_end": artifact.get("training_end"),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
