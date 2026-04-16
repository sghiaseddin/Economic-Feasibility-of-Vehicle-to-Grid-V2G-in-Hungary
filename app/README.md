# V2G Scheduler API

This app exposes a simple HTTP API that returns the hourly commands for an EV connected to a bidirectional charger over the active snapshot window.

## What it does

- On the **first** request, it trains the model pipeline from the CSV files in `data/` and saves the artifact to `models/v2g_pipeline.joblib`.
- On later requests, it loads the saved pipeline and skips retraining.
- For each request, it fetches the hourly weather forecast from Open-Meteo for the active snapshot window and uses that as input for prediction.
- It returns hourly commands in JSON:
  - `-1` = discharge
  - `0` = do nothing
  - `1` = charge

## Project structure

```text
app/
├── app.py
├── config.py
├── service.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── README.md
├── data/
└── models/
```

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn app:app --reload
```

## Run with Docker

Build the image:

```bash
docker build -t v2g-ev-app .
```

Run the container:

```bash
docker run --rm -p 8000:8000 \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/models:/app/models" \
  v2g-ev-app
```

This keeps the CSV files in `data/` and the trained pipeline in `models/` outside the container so they persist across container restarts.

## Endpoints

### Health check

```bash
curl http://127.0.0.1:8000/health
```

### Train or load the pipeline

```bash
curl -X POST http://127.0.0.1:8000/train
```

### Predict commands

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "request_timestamp": "2026-04-16T17:30:20",
    "lat": 47.4979,
    "lon": 19.0402
  }'
```

You can also call the endpoint directly from a browser or with a simple GET request:

```bash
curl http://127.0.0.1:8000/predict
```

You can also open `http://127.0.0.1:8000/predict` in your browser.

### Public demo endpoint

A public endpoint is currently available at:

```text
https://sghiaseddin.com/project/v2g/predict
```

This endpoint is intended as a live demonstration endpoint for the deployed service. Availability, response time, infrastructure limits, reverse-proxy settings, or future deployment changes may affect its behavior, so it should be treated as a public demo endpoint rather than a guaranteed production SLA endpoint.

## Important note about forecast timestamps

[Open-Meteo](https://open-meteo.com/en/docs) is a forecast API. In practice, the request timestamp should be current or near-current. If you send a far-future timestamp, the weather API may not have forecast data for that window, so production usage should normally rely on current or near-current request times.

## Decision logic in this app

- Single snapshot run starting from `request_timestamp.floor("h")`
- The snapshot window is capped before 18:00 on the next day
- Discharge hours are selected from the evening window starting at `PLUGIN_TIME`
- Charge window starts at `CHARGE_START_HOUR` and continues to `PLUGOUT_TIME` next morning
- The saved model pipeline is reused after the first training
- The app uses Budapest local time for request handling and scheduling

Adjust constants in `config.py` as needed.

## Train datasets

### Electricity Market Data

Source  
https://ember-energy.org/data/european-wholesale-electricity-price-data/


### Budapest Weather History

Source
https://www.kaggle.com/datasets/demetera/budapest-weather-history-from-2012