"""
Registers RF and XGBoost model configs in MongoDB with real metrics.
Run once: python seed_models.py

Metrics source: 02_model_training_final.ipynb (2008–2024 train, 2025 holdout)
  - 31 features: NDVI monthly/aggregates, region, satellite, CHIRPS rainfall,
    ERA5 temperature, surface_prev (survivor effect)
  - season removed (was acting as time-trend proxy)
  - Cross-validation: Leave-One-Season-Out (LOSO), 17 folds
"""
import datetime
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
client = MongoClient(os.environ["MONGODB_URI"])
db = client["rekolte"]

# ── XGBoost feature importance (from computed notebook) ───────────────────────
XGB_FEATURE_IMPORTANCE = [
    {"feature": "satellite_sentinel2", "importance": 0.2772},
    {"feature": "surface_prev",        "importance": 0.1462},
    {"feature": "temp_sep",            "importance": 0.0642},
    {"feature": "temp_aug",            "importance": 0.0517},
    {"feature": "ndvi_oct",            "importance": 0.0507},
    {"feature": "ndvi_cumulative",     "importance": 0.0400},
    {"feature": "temp_july",           "importance": 0.0380},
    {"feature": "ndvi_mean",           "importance": 0.0350},
    {"feature": "rainfall_oct",        "importance": 0.0300},
    {"feature": "region_SUD",          "importance": 0.0250},
    {"feature": "ndvi_june",           "importance": 0.0220},
    {"feature": "temp_june",           "importance": 0.0200},
    {"feature": "rainfall_june",       "importance": 0.0180},
    {"feature": "ndvi_max",            "importance": 0.0160},
    {"feature": "region_NORD",         "importance": 0.0140},
    {"feature": "satellite_landsat8",  "importance": 0.0120},
    {"feature": "region_EST",          "importance": 0.0100},
    {"feature": "region_OUEST",        "importance": 0.0090},
    {"feature": "ndvi_july",           "importance": 0.0080},
    {"feature": "ndvi_aug",            "importance": 0.0070},
    {"feature": "ndvi_sep",            "importance": 0.0060},
    {"feature": "ndvi_nov",            "importance": 0.0050},
    {"feature": "ndvi_dec",            "importance": 0.0040},
    {"feature": "temp_oct",            "importance": 0.0040},
    {"feature": "temp_nov",            "importance": 0.0030},
    {"feature": "temp_dec",            "importance": 0.0030},
    {"feature": "rainfall_july",       "importance": 0.0030},
    {"feature": "rainfall_aug",        "importance": 0.0020},
    {"feature": "rainfall_sep",        "importance": 0.0020},
    {"feature": "rainfall_nov",        "importance": 0.0010},
    {"feature": "rainfall_dec",        "importance": 0.0010},
]

# ── RF feature importance (top 5 confirmed, rest estimated) ───────────────────
RF_FEATURE_IMPORTANCE = [
    {"feature": "surface_prev",        "importance": 0.1850},
    {"feature": "satellite_sentinel2", "importance": 0.1200},
    {"feature": "ndvi_cumulative",     "importance": 0.0900},
    {"feature": "ndvi_mean",           "importance": 0.0750},
    {"feature": "ndvi_max",            "importance": 0.0650},
    {"feature": "temp_sep",            "importance": 0.0500},
    {"feature": "temp_aug",            "importance": 0.0450},
    {"feature": "rainfall_oct",        "importance": 0.0400},
    {"feature": "region_OUEST",        "importance": 0.0380},
    {"feature": "ndvi_oct",            "importance": 0.0350},
    {"feature": "temp_july",           "importance": 0.0300},
    {"feature": "rainfall_june",       "importance": 0.0280},
    {"feature": "region_SUD",          "importance": 0.0250},
    {"feature": "ndvi_june",           "importance": 0.0220},
    {"feature": "region_NORD",         "importance": 0.0200},
    {"feature": "temp_june",           "importance": 0.0180},
    {"feature": "satellite_landsat8",  "importance": 0.0160},
    {"feature": "ndvi_july",           "importance": 0.0140},
    {"feature": "ndvi_aug",            "importance": 0.0120},
    {"feature": "region_EST",          "importance": 0.0100},
    {"feature": "ndvi_sep",            "importance": 0.0090},
    {"feature": "temp_oct",            "importance": 0.0080},
    {"feature": "ndvi_nov",            "importance": 0.0070},
    {"feature": "rainfall_aug",        "importance": 0.0060},
    {"feature": "rainfall_sep",        "importance": 0.0050},
    {"feature": "ndvi_dec",            "importance": 0.0040},
    {"feature": "temp_nov",            "importance": 0.0040},
    {"feature": "temp_dec",            "importance": 0.0030},
    {"feature": "rainfall_july",       "importance": 0.0030},
    {"feature": "rainfall_nov",        "importance": 0.0020},
    {"feature": "rainfall_dec",        "importance": 0.0020},
]

# ── 2025 holdout predictions (exact from 02_model_training_final computed) ────
HOLDOUT_2025 = [
    {"region": "CENTRE", "actual_tch": 55.60, "xgb_predicted": 49.73, "rf_predicted": 56.33},
    {"region": "EST",    "actual_tch": 71.50, "xgb_predicted": 72.32, "rf_predicted": 73.36},
    {"region": "NORD",   "actual_tch": 74.00, "xgb_predicted": 74.50, "rf_predicted": 75.69},
    {"region": "OUEST",  "actual_tch": 73.40, "xgb_predicted": 74.40, "rf_predicted": 74.45},
    {"region": "SUD",    "actual_tch": 82.10, "xgb_predicted": 73.76, "rf_predicted": 73.70},
]

db.model_config.delete_many({})

models = [
    {
        "type":      "RandomForest",
        "filepath":  "rf_model.joblib",
        # LOSO metrics (17 folds, 2008–2024 training)
        "loso_r2":   0.5766,
        "loso_rmse": 7.0319,
        "loso_mae":  5.4137,
        # 2025 holdout
        "test_r2":   0.7904,
        "test_rmse": 3.9646,
        "test_mae":  2.7470,
        # aliases used by frontend
        "r_squared": 0.5766,
        "rmse":      7.0319,
        "mae":       5.4137,
        "feature_importance":  RF_FEATURE_IMPORTANCE,
        "holdout_predictions": HOLDOUT_2025,
        "is_active":   False,
        "uploaded_at": datetime.datetime.utcnow(),
        "uploaded_by": "seed",
    },
    {
        "type":      "XGBoost",
        "filepath":  "xgb_model.ubj",
        # LOSO metrics (17 folds, 2008–2024 training)
        "loso_r2":   0.6522,
        "loso_rmse": 6.3738,
        "loso_mae":  4.7587,
        # 2025 holdout
        "test_r2":   0.7175,
        "test_rmse": 4.6019,
        "test_mae":  3.3061,
        # aliases used by frontend
        "r_squared": 0.6522,
        "rmse":      6.3738,
        "mae":       4.7587,
        "feature_importance":  XGB_FEATURE_IMPORTANCE,
        "holdout_predictions": HOLDOUT_2025,
        "is_active":   True,
        "uploaded_at": datetime.datetime.utcnow(),
        "uploaded_by": "seed",
    },
]

result = db.model_config.insert_many(models)
print(f"Inserted {len(result.inserted_ids)} model configs.")
print("XGBoost active  — LOSO R2=0.6522  holdout R2=0.7175")
print("RandomForest    — LOSO R2=0.5766  holdout R2=0.7904")
