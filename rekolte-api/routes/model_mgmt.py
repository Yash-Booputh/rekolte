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
    doc = {
        "type": model_type,
        "filepath": filename,
        "loso_r2":   float(request.form.get("loso_r2", 0)),
        "loso_rmse": float(request.form.get("loso_rmse", 0)),
        "loso_mae":  float(request.form.get("loso_mae", 0)),
        "test_r2":   float(request.form.get("test_r2", 0)),
        "test_rmse": float(request.form.get("test_rmse", 0)),
        "test_mae":  float(request.form.get("test_mae", 0)),
        "r_squared": float(request.form.get("loso_r2", 0)),
        "rmse":      float(request.form.get("loso_rmse", 0)),
        "mae":       float(request.form.get("loso_mae", 0)),
        "feature_importance": [],
        "holdout_predictions": [],
        "is_active": False,
        "uploaded_at": datetime.datetime.utcnow(),
        "uploaded_by": request.user["email"],
    }
    result = db.model_config.insert_one(doc)

    create_notification(db, "model_uploaded",
        f"New {model_type} model uploaded by {request.user['email']}",
        {"model_type": model_type, "uploaded_by": request.user["email"]}
    )

    return jsonify({"message": "Model uploaded", "id": str(result.inserted_id)}), 201

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
