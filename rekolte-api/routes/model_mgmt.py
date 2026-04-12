import os
import datetime
from bson import ObjectId
from flask import Blueprint, request, jsonify
from db import get_db
from middleware.auth import require_auth
from routes.notifications import create_notification
from config import MODELS_DIR

model_mgmt_bp = Blueprint("model_mgmt", __name__)

@model_mgmt_bp.route("/models", methods=["GET"])
@require_auth
def get_models():
    db = get_db()
    docs = list(db.model_config.find({}))
    for d in docs:
        d["_id"] = str(d["_id"])
        if hasattr(d.get("uploaded_at"), "isoformat"):
            d["uploaded_at"] = d["uploaded_at"].isoformat()
    return jsonify(docs)

@model_mgmt_bp.route("/models/upload", methods=["POST"])
@require_auth
def upload_model():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    model_type = request.form.get("type")
    if model_type not in ["RandomForest", "XGBoost"]:
        return jsonify({"error": "type must be RandomForest or XGBoost"}), 400

    if not (file.filename.endswith(".joblib") or file.filename.endswith(".ubj")):
        return jsonify({"error": "File must be .joblib or .ubj"}), 400

    ext = ".ubj" if file.filename.endswith(".ubj") else ".joblib"
    filename = f"{model_type.lower()}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{ext}"
    filepath = os.path.join(MODELS_DIR, filename)
    file.save(filepath)

    db = get_db()

    # Delete the old file on disk if we're replacing an existing model of this type
    existing = db.model_config.find_one({"type": model_type})
    if existing and existing.get("filepath"):
        old_path = os.path.join(MODELS_DIR, existing["filepath"])
        if os.path.exists(old_path) and old_path != filepath:
            try:
                os.remove(old_path)
            except OSError:
                pass

    def _f(key, default=0.0):
        v = request.form.get(key, "")
        try: return float(v) if v != "" else default
        except (ValueError, TypeError): return default

    # Preserve feature_importance and holdout_predictions from the existing doc
    # (upload form doesn't send these; they come from the seed script or notebook export)
    prev_fi   = existing.get("feature_importance", [])   if existing else []
    prev_hp   = existing.get("holdout_predictions", [])  if existing else []

    update_fields = {
        "type": model_type,
        "filepath": filename,
        "loso_r2":   _f("loso_r2"),
        "loso_rmse": _f("loso_rmse"),
        "loso_mae":  _f("loso_mae"),
        "test_r2":   _f("test_r2"),
        "test_rmse": _f("test_rmse"),
        "test_mae":  _f("test_mae"),
        "r_squared": _f("loso_r2"),
        "rmse":      _f("loso_rmse"),
        "mae":       _f("loso_mae"),
        "feature_importance":  prev_fi,
        "holdout_predictions": prev_hp,
        "uploaded_at": datetime.datetime.utcnow(),
        "uploaded_by": request.user["email"],
    }
    # Upsert by type — one entry per model type, uploading a new version replaces the old one.
    # Preserve is_active: only set it on insert (new type), leave it unchanged on replace.
    result = db.model_config.update_one(
        {"type": model_type},
        {"$set": update_fields, "$setOnInsert": {"is_active": False}},
        upsert=True,
    )

    # Clear the model cache so the next prediction loads the new file
    from routes.predict import _model_cache
    _model_cache.clear()

    doc_id = str(existing["_id"]) if existing else str(result.upserted_id)

    create_notification(db, "model_uploaded",
        f"New {model_type} model uploaded by {request.user['email']}",
        {"model_type": model_type, "uploaded_by": request.user["email"]}
    )

    return jsonify({"message": "Model uploaded", "id": doc_id}), 201

@model_mgmt_bp.route("/models/<model_id>", methods=["DELETE"])
@require_auth
def delete_model(model_id):
    db = get_db()
    doc = db.model_config.find_one({"_id": ObjectId(model_id)})
    if not doc:
        return jsonify({"error": "Model not found"}), 404
    if doc.get("is_active"):
        return jsonify({"error": "Cannot delete the active model. Activate a different model first."}), 400

    # Remove file from disk
    filepath = os.path.join(MODELS_DIR, doc["filepath"])
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except OSError:
            pass

    # Clear cache entry
    from routes.predict import _model_cache
    _model_cache.pop(filepath, None)

    db.model_config.delete_one({"_id": ObjectId(model_id)})
    return jsonify({"message": "Model deleted"})


@model_mgmt_bp.route("/models/<model_id>/activate", methods=["POST"])
@require_auth
def activate_model(model_id):
    db = get_db()
    db.model_config.update_many({}, {"$set": {"is_active": False}})
    result = db.model_config.update_one(
        {"_id": ObjectId(model_id)},
        {"$set": {"is_active": True}}
    )
    if result.matched_count == 0:
        return jsonify({"error": "Model not found"}), 404

    doc = db.model_config.find_one({"_id": ObjectId(model_id)})
    create_notification(db, "model_activated",
        f"{doc['type']} model set as active by {request.user['email']}",
        {"model_type": doc["type"], "activated_by": request.user["email"]}
    )

    return jsonify({"message": "Model activated"})
