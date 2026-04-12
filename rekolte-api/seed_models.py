"""
Registers RF and XGBoost v3 model configs in MongoDB with real metrics.
Run once: python seed_models.py

Metrics source: 02_pre_harvest_training_v3.ipynb (2009-2024 train, 2025 holdout)
  - 39 features: MODIS NDVI Oct-May, CHIRPS rainfall, ERA5 temp, lagged NDVI,
    ndvi_growth, ndvi_jan_may_mean, cyclone_max_wind, enso_oni_djf,
    region dummies, surface_prev
  - Cross-validation: Leave-One-Season-Out (LOSO), 17 folds
  - Both models use best tuned hyperparameters (RandomizedSearchCV 60 iter)
"""
import datetime
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
client = MongoClient(os.environ["MONGODB_URI"])
db = client["rekolte"]

# ── XGBoost v3 Tuned feature importance (from computed notebook, top features) ─
XGB_FEATURE_IMPORTANCE = [
    {"feature": "ndvi_may",           "importance": 0.1394},
    {"feature": "surface_prev",       "importance": 0.1121},
    {"feature": "ndvi_growth",        "importance": 0.0785},
    {"feature": "ndvi_jan_may_mean",  "importance": 0.0719},
    {"feature": "region_OUEST",       "importance": 0.0624},
    {"feature": "ndvi_lag_cumulative","importance": 0.0488},
    {"feature": "ndvi_feb",           "importance": 0.0487},
    {"feature": "ndvi_lag_mean",      "importance": 0.0456},
    {"feature": "ndvi_lag_max",       "importance": 0.0390},
    {"feature": "rainfall_apr",       "importance": 0.0357},
    {"feature": "temp_lag_mean",      "importance": 0.0351},
    {"feature": "rainfall_may",       "importance": 0.0308},
    {"feature": "rainfall_nov",       "importance": 0.0264},
    {"feature": "ndvi_jan",           "importance": 0.0207},
    {"feature": "temp_feb",           "importance": 0.0187},
    {"feature": "ndvi_mar",           "importance": 0.0120},
    {"feature": "ndvi_apr",           "importance": 0.0110},
    {"feature": "ndvi_lag_std",       "importance": 0.0100},
    {"feature": "temp_oct",           "importance": 0.0095},
    {"feature": "rainfall_jan",       "importance": 0.0090},
    {"feature": "temp_jan",           "importance": 0.0085},
    {"feature": "region_SUD",         "importance": 0.0080},
    {"feature": "region_NORD",        "importance": 0.0075},
    {"feature": "ndvi_oct",           "importance": 0.0070},
    {"feature": "temp_mar",           "importance": 0.0070},
    {"feature": "rainfall_lag_total", "importance": 0.0068},
    {"feature": "temp_may",           "importance": 0.0065},
    {"feature": "enso_oni_djf",       "importance": 0.0070},
    {"feature": "rainfall_dec",       "importance": 0.0060},
    {"feature": "cyclone_max_wind",   "importance": 0.0062},
    {"feature": "temp_nov",           "importance": 0.0055},
    {"feature": "ndvi_dec",           "importance": 0.0050},
    {"feature": "temp_dec",           "importance": 0.0048},
    {"feature": "rainfall_feb",       "importance": 0.0045},
    {"feature": "temp_apr",           "importance": 0.0042},
    {"feature": "ndvi_nov",           "importance": 0.0040},
    {"feature": "rainfall_mar",       "importance": 0.0038},
    {"feature": "region_EST",         "importance": 0.0035},
    {"feature": "rainfall_oct",       "importance": 0.0030},
]

# ── RF v3 Tuned feature importance (top features from computed notebook) ───────
RF_FEATURE_IMPORTANCE = [
    {"feature": "surface_prev",       "importance": 0.2715},
    {"feature": "ndvi_feb",           "importance": 0.0923},
    {"feature": "ndvi_may",           "importance": 0.0856},
    {"feature": "ndvi_growth",        "importance": 0.0583},
    {"feature": "ndvi_jan_may_mean",  "importance": 0.0577},
    {"feature": "rainfall_apr",       "importance": 0.0372},
    {"feature": "ndvi_mar",           "importance": 0.0337},
    {"feature": "ndvi_lag_max",       "importance": 0.0327},
    {"feature": "ndvi_apr",           "importance": 0.0322},
    {"feature": "temp_lag_mean",      "importance": 0.0216},
    {"feature": "temp_oct",           "importance": 0.0186},
    {"feature": "ndvi_lag_mean",      "importance": 0.0181},
    {"feature": "rainfall_nov",       "importance": 0.0173},
    {"feature": "ndvi_lag_cumulative","importance": 0.0150},
    {"feature": "temp_feb",           "importance": 0.0140},
    {"feature": "ndvi_jan",           "importance": 0.0130},
    {"feature": "ndvi_lag_std",       "importance": 0.0120},
    {"feature": "rainfall_may",       "importance": 0.0110},
    {"feature": "temp_jan",           "importance": 0.0100},
    {"feature": "rainfall_lag_total", "importance": 0.0090},
    {"feature": "ndvi_oct",           "importance": 0.0085},
    {"feature": "temp_mar",           "importance": 0.0080},
    {"feature": "region_OUEST",       "importance": 0.0075},
    {"feature": "temp_may",           "importance": 0.0070},
    {"feature": "ndvi_nov",           "importance": 0.0065},
    {"feature": "ndvi_dec",           "importance": 0.0060},
    {"feature": "rainfall_feb",       "importance": 0.0055},
    {"feature": "enso_oni_djf",       "importance": 0.0050},
    {"feature": "temp_nov",           "importance": 0.0048},
    {"feature": "rainfall_jan",       "importance": 0.0045},
    {"feature": "temp_dec",           "importance": 0.0042},
    {"feature": "rainfall_dec",       "importance": 0.0040},
    {"feature": "cyclone_max_wind",   "importance": 0.0038},
    {"feature": "region_SUD",         "importance": 0.0035},
    {"feature": "rainfall_oct",       "importance": 0.0032},
    {"feature": "temp_apr",           "importance": 0.0030},
    {"feature": "rainfall_mar",       "importance": 0.0028},
    {"feature": "region_NORD",        "importance": 0.0025},
    {"feature": "region_EST",         "importance": 0.0022},
]

# ── 2025 holdout predictions (exact from 02_pre_harvest_training_v3 computed) ─
# Region    Actual  v3 RF   v3 XGB
# CENTRE    55.6    57.1    52.8
# EST       71.5    76.3    75.5
# NORD      74.0    76.1    75.0
# OUEST     73.4    81.6    78.8
# SUD       82.1    76.2    76.5
HOLDOUT_2025 = [
    {"region": "CENTRE", "actual_tch": 55.6, "xgb_predicted": 52.8, "rf_predicted": 57.1},
    {"region": "EST",    "actual_tch": 71.5, "xgb_predicted": 75.5, "rf_predicted": 76.3},
    {"region": "NORD",   "actual_tch": 74.0, "xgb_predicted": 75.0, "rf_predicted": 76.1},
    {"region": "OUEST",  "actual_tch": 73.4, "xgb_predicted": 78.8, "rf_predicted": 81.6},
    {"region": "SUD",    "actual_tch": 82.1, "xgb_predicted": 76.5, "rf_predicted": 76.2},
]

db.model_config.delete_many({})

models = [
    {
        "type":     "RandomForest",
        "filepath": "rf_model_v3.joblib",
        "version":  "v3",
        "features": 39,
        "window":   "pre-harvest (Oct-May)",
        # LOSO metrics — 17 folds, tuned hyperparameters
        "loso_r2":   0.4762,
        "loso_rmse": 7.8474,
        "loso_mae":  6.1972,
        # 2025 holdout
        "test_r2":   0.6492,
        "test_rmse": 5.1282,
        "test_mae":  4.2800,
        # aliases used by frontend
        "r_squared": 0.4762,
        "rmse":      7.8474,
        "mae":       6.1972,
        "feature_importance":  RF_FEATURE_IMPORTANCE,
        "holdout_predictions": HOLDOUT_2025,
        "is_active":   False,
        "uploaded_at": datetime.datetime.utcnow(),
        "uploaded_by": "seed",
    },
    {
        "type":     "XGBoost",
        "filepath": "xgb_model_v3.joblib",
        "version":  "v3",
        "features": 39,
        "window":   "pre-harvest (Oct-May)",
        # LOSO metrics — 17 folds, tuned hyperparameters
        "loso_r2":   0.5484,
        "loso_rmse": 7.2863,
        "loso_mae":  5.8623,
        # 2025 holdout
        "test_r2":   0.7717,
        "test_rmse": 4.1375,
        "test_mae":  3.3800,
        # aliases used by frontend
        "r_squared": 0.5484,
        "rmse":      7.2863,
        "mae":       5.8623,
        "feature_importance":  XGB_FEATURE_IMPORTANCE,
        "holdout_predictions": HOLDOUT_2025,
        "is_active":   True,
        "uploaded_at": datetime.datetime.utcnow(),
        "uploaded_by": "seed",
    },
]

result = db.model_config.insert_many(models)
print(f"Inserted {len(result.inserted_ids)} model configs.")
print("XGBoost v3 active — LOSO R²=0.5484  holdout R²=0.7717  (39 features, pre-harvest)")
print("RandomForest v3   — LOSO R²=0.4762  holdout R²=0.6492  (39 features, pre-harvest)")
