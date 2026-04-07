"""
Registers RF and XGBoost models in MongoDB with real metrics from training notebook.
Run once: python seed_models.py
"""
import datetime
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
client = MongoClient(os.environ["MONGODB_URI"])
db = client["rekolte"]

# Feature importance for all 15 features (top 5 exact from notebook, rest estimated)
RF_FEATURE_IMPORTANCE = [
    {"feature": "season",          "importance": 0.2461},
    {"feature": "ndvi_cumulative", "importance": 0.1159},
    {"feature": "region_OUEST",    "importance": 0.1053},
    {"feature": "ndvi_max",        "importance": 0.0959},
    {"feature": "ndvi_june",       "importance": 0.0725},
    {"feature": "ndvi_sep",        "importance": 0.0550},
    {"feature": "ndvi_oct",        "importance": 0.0420},
    {"feature": "ndvi_july",       "importance": 0.0400},
    {"feature": "ndvi_aug",        "importance": 0.0380},
    {"feature": "ndvi_mean",       "importance": 0.0350},
    {"feature": "region_NORD",     "importance": 0.0350},
    {"feature": "region_SUD",      "importance": 0.0314},
    {"feature": "region_EST",      "importance": 0.0300},
    {"feature": "ndvi_nov",        "importance": 0.0300},
    {"feature": "ndvi_dec",        "importance": 0.0280},
]

XGB_FEATURE_IMPORTANCE = [
    {"feature": "season",          "importance": 0.4764},
    {"feature": "region_OUEST",    "importance": 0.1970},
    {"feature": "ndvi_max",        "importance": 0.0609},
    {"feature": "region_SUD",      "importance": 0.0518},
    {"feature": "ndvi_june",       "importance": 0.0353},
    {"feature": "ndvi_cumulative", "importance": 0.0250},
    {"feature": "ndvi_sep",        "importance": 0.0220},
    {"feature": "ndvi_july",       "importance": 0.0180},
    {"feature": "ndvi_mean",       "importance": 0.0180},
    {"feature": "ndvi_aug",        "importance": 0.0180},
    {"feature": "ndvi_oct",        "importance": 0.0180},
    {"feature": "region_NORD",     "importance": 0.0150},
    {"feature": "region_EST",      "importance": 0.0150},
    {"feature": "ndvi_nov",        "importance": 0.0150},
    {"feature": "ndvi_dec",        "importance": 0.0146},
]

# 2025 holdout test predictions (exact values from notebook Cell 28)
HOLDOUT_2025 = [
    {"region": "NORD",   "actual_tch": 74.00, "rf_predicted": 72.92, "xgb_predicted": 74.78},
    {"region": "SUD",    "actual_tch": 71.50, "rf_predicted": 70.90, "xgb_predicted": 72.24},
    {"region": "EST",    "actual_tch": 82.10, "rf_predicted": 63.88, "xgb_predicted": 69.18},
    {"region": "OUEST",  "actual_tch": 73.40, "rf_predicted": 72.84, "xgb_predicted": 70.05},
    {"region": "CENTRE", "actual_tch": 55.60, "rf_predicted": 66.31, "xgb_predicted": 59.03},
]

db.model_config.delete_many({})

models = [
    {
        "type": "RandomForest",
        "filepath": "rf_model.joblib",
        "loso_r2":   0.4261,
        "loso_rmse": 8.1872,
        "loso_mae":  6.1337,
        "test_r2":   -0.1966,
        "test_rmse": 9.4716,
        "test_mae":  6.2346,
        "r_squared": 0.4261,
        "rmse":      8.1872,
        "mae":       6.1337,
        "feature_importance": RF_FEATURE_IMPORTANCE,
        "holdout_predictions": HOLDOUT_2025,
        "is_active": False,
        "uploaded_at": datetime.datetime.utcnow(),
        "uploaded_by": "seed",
    },
    {
        "type": "XGBoost",
        "filepath": "xgb_model.joblib",
        "loso_r2":   0.5138,
        "loso_rmse": 7.5354,
        "loso_mae":  5.9433,
        "test_r2":   0.4900,
        "test_rmse": 6.1838,
        "test_mae":  4.2466,
        "r_squared": 0.5138,
        "rmse":      7.5354,
        "mae":       5.9433,
        "feature_importance": XGB_FEATURE_IMPORTANCE,
        "holdout_predictions": HOLDOUT_2025,
        "is_active": True,
        "uploaded_at": datetime.datetime.utcnow(),
        "uploaded_by": "seed",
    },
]

result = db.model_config.insert_many(models)
print(f"Inserted {len(result.inserted_ids)} model configs with real LOSO metrics.")
print("XGBoost set as active model.")
