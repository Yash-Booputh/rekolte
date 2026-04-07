import os
import datetime
from bson import ObjectId
from flask import Blueprint, request, jsonify
from db import get_db
from middleware.auth import require_auth, require_admin
from config import MODELS_DIR

model_mgmt_bp = Blueprint("model_mgmt", __name__)

@model_mgmt_bp.route("/models", methods=["GET"])
@require_auth
def get_models():
    db = get_db()
    docs = list(db.model_config.find({}, {"_id": 1, "type": 1, "r_squared": 1, "rmse": 1, "mae": 1,
                                          "is_active": 1, "uploaded_at": 1, "filepath": 1}))
    for d in docs:
        d["_id"] = str(d["_id"])
        if hasattr(d.get("uploaded_at"), "isoformat"):
            d["uploaded_at"] = d["uploaded_at"].isoformat()
    return jsonify(docs)

@model_mgmt_bp.route("/models/upload", methods=["POST"])
@require_admin
def upload_model():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    model_type = request.form.get("type")
    if model_type not in ["RandomForest", "XGBoost"]:
        return jsonify({"error": "type must be RandomForest or XGBoost"}), 400

    if not file.filename.endswith(".joblib"):
        return jsonify({"error": "File must be a .joblib file"}), 400

    filename = f"{model_type.lower()}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.joblib"
    filepath = os.path.join(MODELS_DIR, filename)
    file.save(filepath)

    db = get_db()
    doc = {
        "type": model_type,
        "filepath": filename,
        "r_squared": float(request.form.get("r_squared", 0)),
        "rmse": float(request.form.get("rmse", 0)),
        "mae": float(request.form.get("mae", 0)),
        "is_active": False,
        "uploaded_at": datetime.datetime.utcnow(),
        "uploaded_by": request.user["email"],
    }
    result = db.model_config.insert_one(doc)
    return jsonify({"message": "Model uploaded", "id": str(result.inserted_id)}), 201

@model_mgmt_bp.route("/models/<model_id>/activate", methods=["POST"])
@require_admin
def activate_model(model_id):
    db = get_db()

    # Deactivate all models first
    db.model_config.update_many({}, {"$set": {"is_active": False}})

    # Activate the selected one
    result = db.model_config.update_one(
        {"_id": ObjectId(model_id)},
        {"$set": {"is_active": True}}
    )
    if result.matched_count == 0:
        return jsonify({"error": "Model not found"}), 404

    return jsonify({"message": "Model activated"})
