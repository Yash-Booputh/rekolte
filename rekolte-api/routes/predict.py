import os
import json as _json
import datetime
import joblib
import numpy as np
import xgboost as xgb
from xgboost import XGBRegressor
from flask import Blueprint, request, jsonify
from db import get_db
from middleware.auth import require_auth
from config import MODELS_DIR

predict_bp = Blueprint("predict", __name__)

REGIONS      = ["NORD", "SUD", "EST", "OUEST", "CENTRE"]
MONTH_SUFFIX = ["june", "july", "aug", "sep", "oct", "nov", "dec"]

# ── Feature order must match 02_model_training_final.ipynb exactly (31 features) ──
# 1.  ndvi_june..ndvi_dec          (7)   monthly NDVI
# 2.  ndvi_mean, ndvi_max,         (3)   season NDVI aggregates
#     ndvi_cumulative
# 3.  region_EST, region_NORD,     (4)   one-hot region (CENTRE = baseline)
#     region_OUEST, region_SUD
# 4.  satellite_landsat8,          (2)   one-hot sensor (landsat7 = baseline)
#     satellite_sentinel2
# 5.  rainfall_june..rainfall_dec  (7)   CHIRPS monthly rainfall (mm)
# 6.  temp_june..temp_dec          (7)   ERA5 monthly temperature (°C)
# 7.  surface_prev                 (1)   previous season harvested area (ha)


def _build_feature_vector(ndvi_doc, region, surface_prev):
    """Build the 31-element feature vector matching training feature order."""
    # Monthly NDVI — fall back to ndvi_mean if a month is missing
    ndvi_monthly = [
        ndvi_doc.get(f"ndvi_{m}") or ndvi_doc["ndvi_mean"]
        for m in MONTH_SUFFIX
    ]
    ndvi_agg = [ndvi_doc["ndvi_mean"], ndvi_doc["ndvi_max"], ndvi_doc["ndvi_cumulative"]]

    # Region one-hot (alphabetical: EST, NORD, OUEST, SUD — CENTRE baseline)
    region_dummies = [
        1 if region == "EST"   else 0,
        1 if region == "NORD"  else 0,
        1 if region == "OUEST" else 0,
        1 if region == "SUD"   else 0,
    ]

    # Satellite one-hot (alphabetical: landsat8, sentinel2 — landsat7 baseline)
    satellite = ndvi_doc.get("satellite") or ndvi_doc.get("satellite_source", "sentinel2")
    sat_dummies = [
        1 if satellite == "landsat8"  else 0,
        1 if satellite == "sentinel2" else 0,
    ]

    # Monthly rainfall — fall back to 0 if missing (CHIRPS complete for 2008-2025)
    rain_monthly = [
        float(ndvi_doc.get(f"rainfall_{m}") or 0.0)
        for m in MONTH_SUFFIX
    ]

    # Monthly temperature — fall back to 25°C if missing (ERA5 complete for 2008-2025)
    temp_monthly = [
        float(ndvi_doc.get(f"temp_{m}") or 25.0)
        for m in MONTH_SUFFIX
    ]

    features = (
        ndvi_monthly        # 7
        + ndvi_agg          # 3
        + region_dummies    # 4
        + sat_dummies       # 2
        + rain_monthly      # 7
        + temp_monthly      # 7
        + [surface_prev]    # 1
    )                       # = 31
    return np.array([features], dtype=float)


_model_cache = {}

def _load_model(filepath):
    if filepath not in _model_cache:
        if filepath.endswith(".ubj"):
            model = XGBRegressor()
            model.load_model(filepath)
        else:
            model = joblib.load(filepath)
        _model_cache[filepath] = model
    return _model_cache[filepath]

def _predict(model, X):
    """
    Unified predict. For XGBRegressor, applies a base_score correction.

    XGBoost 2.x serialisation (joblib or save_model) loses the auto-estimated
    base_score from the booster's internal init-prediction, resetting it to 0.5.
    The Python wrapper attribute (model.base_score) IS correctly preserved by
    joblib. We compute the correction from those two values — no hardcoding.
    """
    if isinstance(model, XGBRegressor):
        py_bs = float(getattr(model, 'base_score', 0.5) or 0.5)
        cfg = _json.loads(model.get_booster().save_config())
        booster_bs = float(cfg['learner']['learner_model_param']['base_score'])
        correction = py_bs - booster_bs
        raw = model.get_booster().predict(xgb.DMatrix(X))
        if abs(correction) > 0.1:
            print(f"[INFO] XGBoost base_score correction: {booster_bs:.4f} -> {py_bs:.6f} (+{correction:.4f})", flush=True)
        return raw + correction
    return model.predict(X)

def _get_active_model():
    db = get_db()
    config = db.model_config.find_one({"is_active": True})
    if not config:
        print("[DEBUG] No active model found in DB", flush=True)
        return None, None
    filepath = os.path.join(MODELS_DIR, config["filepath"])
    print(f"[DEBUG] Active model: type={config['type']} filepath={config['filepath']} abs={filepath} exists={os.path.exists(filepath)}", flush=True)
    if not os.path.exists(filepath):
        return None, None
    return _load_model(filepath), config

def _get_surface_prev(db, region, season_year):
    """Previous season's harvested area — captures the survivor effect.
    Falls back to current season area, then a global default."""
    doc = db.harvest_data.find_one(
        {"region": region, "season": season_year - 1},
        {"surface_harvested": 1}
    )
    if doc and doc.get("surface_harvested"):
        return float(doc["surface_harvested"])
    # Fallback: use current season's own area (e.g. first season in DB)
    doc_curr = db.harvest_data.find_one(
        {"region": region, "season": season_year},
        {"surface_harvested": 1}
    )
    if doc_curr and doc_curr.get("surface_harvested"):
        return float(doc_curr["surface_harvested"])
    return 5000.0  # conservative global default


@predict_bp.route("/ndvi/latest", methods=["GET"])
@require_auth
def get_latest_ndvi():
    db = get_db()
    results = {}
    for region in REGIONS:
        doc = db.satellite_features.find_one(
            {"region": region},
            sort=[("season", -1)]
        )
        if doc:
            results[region] = {
                "region":            region,
                "season":            doc["season"],
                "satellite":         doc.get("satellite") or doc.get("satellite_source"),
                "ndvi_mean":         doc["ndvi_mean"],
                "ndvi_max":          doc["ndvi_max"],
                "ndvi_cumulative":   doc["ndvi_cumulative"],
                "observation_count": doc.get("observation_count", 0),
                "extracted_at":      str(doc.get("extracted_at", "")),
            }
    return jsonify(results)


@predict_bp.route("/predict", methods=["POST"])
@require_auth
def predict():
    data = request.get_json()
    region = (data.get("region") or "").upper() if data else ""

    if region not in REGIONS:
        return jsonify({"error": f"region must be one of {REGIONS}"}), 400

    db = get_db()

    # Latest NDVI + climate row for this region
    ndvi_doc = db.satellite_features.find_one(
        {"region": region},
        sort=[("season", -1)]
    )
    if not ndvi_doc:
        return jsonify({"error": f"No NDVI data available for {region}"}), 404

    model, config = _get_active_model()
    if not model:
        return jsonify({"error": "No active model available"}), 503

    season_year  = ndvi_doc["season"]
    surface_prev = _get_surface_prev(db, region, season_year)

    features      = _build_feature_vector(ndvi_doc, region, surface_prev)
    raw_pred      = _predict(model, features)
    predicted_tch = float(raw_pred[0])

    print(f"[DEBUG] region={region} model_type={type(model).__name__} "
          f"filepath={config['filepath']} ndvi_mean={ndvi_doc.get('ndvi_mean'):.4f} "
          f"surface_prev={surface_prev:.1f} satellite={ndvi_doc.get('satellite') or ndvi_doc.get('satellite_source')} "
          f"raw_pred={raw_pred[0]:.4f}", flush=True)

    # Check if we have actual TCH for comparison
    harvest_doc = db.harvest_data.find_one(
        {"region": region, "season": season_year},
        sort=[("week", -1)]
    )
    actual_tch = harvest_doc.get("tch") if harvest_doc else None

    prediction_record = {
        "region":        region,
        "season":        season_year,
        "predicted_tch": round(predicted_tch, 2),
        "actual_tch":    actual_tch,
        "model_used":    config["type"],
        "model_id":      str(config["_id"]),
        "ndvi_snapshot": {
            "ndvi_mean":         ndvi_doc["ndvi_mean"],
            "ndvi_max":          ndvi_doc["ndvi_max"],
            "ndvi_cumulative":   ndvi_doc["ndvi_cumulative"],
            "observation_count": ndvi_doc.get("observation_count", 0),
            "extracted_at":      ndvi_doc.get("extracted_at"),
        },
        "created_by": request.user["email"],
        "created_at": datetime.datetime.utcnow(),
    }
    db.predictions.insert_one(prediction_record)

    from routes.notifications import create_notification
    create_notification(db, "prediction",
        f"Prediction run for {region}: {round(predicted_tch, 2)} TCH (season {season_year})",
        {"region": region, "season": season_year, "predicted_tch": round(predicted_tch, 2)}
    )

    prediction_record.pop("_id", None)
    prediction_record["created_at"] = prediction_record["created_at"].isoformat()
    if prediction_record["ndvi_snapshot"].get("extracted_at"):
        prediction_record["ndvi_snapshot"]["extracted_at"] = str(
            prediction_record["ndvi_snapshot"]["extracted_at"]
        )

    return jsonify(prediction_record)


@predict_bp.route("/predictions", methods=["GET"])
@require_auth
def get_predictions():
    db = get_db()
    region = request.args.get("region", "").upper() or None
    season = request.args.get("season")

    query = {}
    if region and region in REGIONS:
        query["region"] = region
    if season:
        query["season"] = int(season)

    docs = list(db.predictions.find(query, {"_id": 0}).sort("created_at", -1).limit(200))
    for d in docs:
        if hasattr(d.get("created_at"), "isoformat"):
            d["created_at"] = d["created_at"].isoformat()

    return jsonify(docs)
