from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

PRICE_FILE = "ember-energy.org-electricity-price-hungary-20260308.csv"
WEATHER_FILE = "Budapest_01.02.2005-31.09.2025.csv"
PIPELINE_FILE = MODEL_DIR / "v2g_pipeline.joblib"

PLUGIN_TIME = 18
PLUGOUT_TIME = 7
CHARGE_START_HOUR = 23
SPREAD_THRESHOLD = 0.01

SUPPORTED_START_YEAR = 2021
SUPPORTED_END_YEAR = 2030

BUDAPEST_LAT = 47.4979
BUDAPEST_LON = 19.0402
BUDAPEST_TIMEZONE = "Europe/Budapest"

FEATURE_COLUMNS = [
    "hour",
    "weekday",
    "month",
    "year",
    "iso_week",
    "day_of_year",
    "is_weekend",
    "temp",
    "clouds",
    "visibility",
    "precipitation",
]

WEATHER_COLUMNS = ["temp", "clouds", "visibility", "precipitation"]
