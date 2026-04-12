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

REGIONS = ["NORD", "SUD", "EST", "OUEST", "CENTRE"]

# ── Feature order must match feature_cols_v3.json exactly (39 features) ─────
# 1.  ndvi_lag_mean, ndvi_lag_max, ndvi_lag_std, ndvi_lag_cumulative   (4)
# 2.  rainfall_lag_total, temp_lag_mean                                (2)
# 3.  ndvi_oct..ndvi_may                                               (8)
# 4.  rainfall_oct..rainfall_may                                       (8)
# 5.  temp_oct..temp_may                                               (8)
# 6.  region_EST, region_NORD, region_OUEST, region_SUD               (4)
# 7.  surface_prev                                                     (1)
# 8.  ndvi_growth, ndvi_jan_may_mean                                   (2)
# 9.  cyclone_max_wind, enso_oni_djf                                   (2)
#                                                                    = 39


def _build_feature_vector(doc, region):
    """Build the 39-element feature vector matching feature_cols_v3.json order."""
    features = [
        # Lagged NDVI (previous season Jun-Dec)
        doc["ndvi_lag_mean"],
        doc["ndvi_lag_max"],
        doc["ndvi_lag_std"],
        doc["ndvi_lag_cumulative"],
        # Lagged climate
        doc["rainfall_lag_total"],
        doc["temp_lag_mean"],
        # MODIS NDVI Oct-May
        doc["ndvi_oct"],
        doc["ndvi_nov"],
        doc["ndvi_dec"],
        doc["ndvi_jan"],
        doc["ndvi_feb"],
        doc["ndvi_mar"],
        doc["ndvi_apr"],
        doc["ndvi_may"],
        # CHIRPS monthly rainfall Oct-May
        doc["rainfall_oct"],
        doc["rainfall_nov"],
        doc["rainfall_dec"],
        doc["rainfall_jan"],
        doc["rainfall_feb"],
        doc["rainfall_mar"],
        doc["rainfall_apr"],
        doc["rainfall_may"],
        # ERA5 monthly temperature Oct-May
        doc["temp_oct"],
        doc["temp_nov"],
        doc["temp_dec"],
        doc["temp_jan"],
        doc["temp_feb"],
        doc["temp_mar"],
        doc["temp_apr"],
        doc["temp_may"],
        # Region one-hot (CENTRE = baseline)
        1 if region == "EST"   else 0,
        1 if region == "NORD"  else 0,
        1 if region == "OUEST" else 0,
        1 if region == "SUD"   else 0,
        # Previous season harvested area
        doc["surface_prev"],
        # Derived NDVI features
        doc["ndvi_growth"],
        doc["ndvi_jan_may_mean"],
        # External climate indicators
        doc["cyclone_max_wind"],
        doc["enso_oni_djf"],
    ]
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


def _get_true_base_score(db):
    """
    Recover the auto-estimated XGBoost base_score = mean(y_train).
    XGBoost trains with base_score=None so it estimates mean(TCH) from the
    training set (2009-2024, 80 rows). We recompute it from MongoDB so we
    don't need to hardcode it.
    """
    docs = list(db.harvest_data.find(
        {"season": {"$gte": 2009, "$lte": 2024}},
        {"tch": 1, "_id": 0}
    ))
    values = [d["tch"] for d in docs if d.get("tch")]
    return float(np.mean(values)) if values else 75.0


def _predict(model, X, db=None):
    """
    Unified predict. For XGBRegressor, applies a base_score correction.

    XGBoost 2.x with base_score=None auto-estimates it as mean(y). joblib
    serialisation goes through xgb.Booster.__setstate__ which calls load_model()
    internally — this silently resets the C++ base_score back to 0.5, and the
    Python attribute model.base_score stays None. So after joblib load both
    py_bs and booster_bs read as 0.5, correction = 0, raw prediction is ~2 TCH.

    Fix: recompute the true base_score as mean(y_train) from MongoDB and use
    that for the correction instead of the (broken) Python attribute.
    """
    if isinstance(model, XGBRegressor):
        py_bs = getattr(model, 'base_score', None)
        if py_bs is None or abs(float(py_bs) - 0.5) < 0.01:
            # base_score was auto-estimated and lost — recover from training data
            py_bs = _get_true_base_score(db) if db is not None else 75.0
            print(f"[INFO] XGB base_score recovered from training mean: {py_bs:.4f}", flush=True)
        else:
            py_bs = float(py_bs)
        cfg = _json.loads(model.get_booster().save_config())
        booster_bs = float(cfg['learner']['learner_model_param']['base_score'])
        correction = py_bs - booster_bs
        raw = model.get_booster().predict(xgb.DMatrix(X))
        print(f"[INFO] XGB correction: booster_bs={booster_bs:.4f} py_bs={py_bs:.4f} correction={correction:.4f} raw={raw[0]:.4f}", flush=True)
        return raw + correction
    return model.predict(X)


def _get_active_model():
    db = get_db()
    config = db.model_config.find_one({"is_active": True})
    if not config:
        return None, None
    filepath = os.path.join(MODELS_DIR, config["filepath"])
    if not os.path.exists(filepath):
        return None, None
    return _load_model(filepath), config


def _get_surface_prev(db, region, season_year):
    """Previous season's harvested area — fallback chain."""
    doc = db.harvest_data.find_one(
        {"region": region, "season": season_year - 1},
        {"surface_harvested": 1}
    )
    if doc and doc.get("surface_harvested"):
        return float(doc["surface_harvested"])
    doc_curr = db.harvest_data.find_one(
        {"region": region, "season": season_year},
        {"surface_harvested": 1}
    )
    if doc_curr and doc_curr.get("surface_harvested"):
        return float(doc_curr["surface_harvested"])
    return 5000.0


def run_all_predictions(db, model, config, user_email):
    """Re-run predictions for all 5 regions using the given model and store them."""
    for region in REGIONS:
        try:
            feat_doc = db.pre_harvest_features.find_one(
                {"region": region},
                sort=[("season", -1)]
            )
            if not feat_doc:
                continue

            season_year = feat_doc["season"]
            surface_prev = feat_doc.get("surface_prev") or _get_surface_prev(db, region, season_year)
            feat_doc["surface_prev"] = float(surface_prev)

            features      = _build_feature_vector(feat_doc, region)
            raw_pred      = _predict(model, features, db=db)
            predicted_tch = float(raw_pred[0])

            harvest_doc = db.harvest_data.find_one(
                {"region": region, "season": season_year},
                sort=[("week", -1)]
            )
            actual_tch = harvest_doc.get("tch") if harvest_doc else None

            db.predictions.update_one(
                {"region": region, "season": season_year, "model_used": config["type"]},
                {"$set": {
                    "predicted_tch": round(predicted_tch, 2),
                    "actual_tch":    actual_tch,
                    "model_used":    config["type"],
                    "model_id":      str(config["_id"]),
                    "feature_snapshot": {
                        "ndvi_may":          feat_doc.get("ndvi_may"),
                        "ndvi_growth":       feat_doc.get("ndvi_growth"),
                        "ndvi_jan_may_mean": feat_doc.get("ndvi_jan_may_mean"),
                        "cyclone_max_wind":  feat_doc.get("cyclone_max_wind"),
                        "enso_oni_djf":      feat_doc.get("enso_oni_djf"),
                        "surface_prev":      feat_doc.get("surface_prev"),
                    },
                    "created_by": user_email,
                    "created_at": datetime.datetime.utcnow(),
                }},
                upsert=True,
            )
        except Exception as e:
            print(f"[WARN] run_all_predictions skipped {region}: {e}", flush=True)


@predict_bp.route("/ndvi/latest", methods=["GET"])
@require_auth
def get_latest_ndvi():
    """Return latest pre-harvest feature summary per region."""
    db = get_db()
    results = {}
    for region in REGIONS:
        doc = db.pre_harvest_features.find_one(
            {"region": region},
            sort=[("season", -1)]
        )
        if doc:
            results[region] = {
                "region":            region,
                "season":            doc["season"],
                "ndvi_may":          doc.get("ndvi_may"),
                "ndvi_growth":       doc.get("ndvi_growth"),
                "ndvi_jan_may_mean": doc.get("ndvi_jan_may_mean"),
                "cyclone_max_wind":  doc.get("cyclone_max_wind"),
                "enso_oni_djf":      doc.get("enso_oni_djf"),
            }
    return jsonify(results)


@predict_bp.route("/predict", methods=["POST"])
@require_auth
def predict():
    data   = request.get_json()
    region = (data.get("region") or "").upper() if data else ""

    if region not in REGIONS:
        return jsonify({"error": f"region must be one of {REGIONS}"}), 400

    db = get_db()

    # Latest pre-harvest features for this region
    feat_doc = db.pre_harvest_features.find_one(
        {"region": region},
        sort=[("season", -1)]
    )
    if not feat_doc:
        return jsonify({"error": f"No pre-harvest feature data available for {region}"}), 404

    model, config = _get_active_model()
    if not model:
        return jsonify({"error": "No active model available"}), 503

    season_year = feat_doc["season"]

    # surface_prev: use value stored in doc (seeded from harvest_data)
    # or recompute as fallback
    surface_prev = feat_doc.get("surface_prev") or _get_surface_prev(db, region, season_year)
    feat_doc["surface_prev"] = float(surface_prev)

    features      = _build_feature_vector(feat_doc, region)
    raw_pred      = _predict(model, features, db=db)
    predicted_tch = float(raw_pred[0])

    print(f"[DEBUG] region={region} model_type={type(model).__name__} "
          f"filepath={config['filepath']} ndvi_may={feat_doc.get('ndvi_may'):.4f} "
          f"surface_prev={surface_prev:.1f} raw_pred={raw_pred[0]:.4f}", flush=True)

    # Actual TCH for comparison (if season is complete)
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
        "feature_snapshot": {
            "ndvi_may":          feat_doc.get("ndvi_may"),
            "ndvi_growth":       feat_doc.get("ndvi_growth"),
            "ndvi_jan_may_mean": feat_doc.get("ndvi_jan_may_mean"),
            "cyclone_max_wind":  feat_doc.get("cyclone_max_wind"),
            "enso_oni_djf":      feat_doc.get("enso_oni_djf"),
            "surface_prev":      feat_doc.get("surface_prev"),
        },
        "created_by": request.user["email"],
        "created_at": datetime.datetime.utcnow(),
    }
    db.predictions.update_one(
        {"region": region, "season": season_year, "model_used": config["type"]},
        {"$set": prediction_record},
        upsert=True,
    )

    from routes.notifications import create_notification
    create_notification(db, "prediction",
        f"Pre-harvest forecast for {region}: {round(predicted_tch, 2)} TCH (season {season_year})",
        {"region": region, "season": season_year, "predicted_tch": round(predicted_tch, 2)}
    )

    prediction_record.pop("_id", None)
    prediction_record["created_at"] = prediction_record["created_at"].isoformat()

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
