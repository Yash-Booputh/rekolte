import datetime
from bson import ObjectId
from flask import Blueprint, request, jsonify
from db import get_db
from middleware.auth import require_auth, require_admin

bulletins_bp = Blueprint("bulletins", __name__)

@bulletins_bp.route("/bulletins", methods=["GET"])
@require_auth
def get_bulletins():
    db = get_db()
    season = request.args.get("season")
    bulletin_type = request.args.get("type")  # weekly / crop_report / other

    query = {}
    if season:
        query["season"] = int(season)
    if bulletin_type:
        query["type"] = bulletin_type

    docs = list(db.bulletins.find(query).sort("season", -1))
    for d in docs:
        d["_id"] = str(d["_id"])
        if hasattr(d.get("uploaded_at"), "isoformat"):
            d["uploaded_at"] = d["uploaded_at"].isoformat()

    return jsonify(docs)

@bulletins_bp.route("/bulletins", methods=["POST"])
@require_admin
def add_bulletin():
    data = request.get_json()
    required = ["filename", "driveFileId", "type"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    bulletin_type = data["type"]
    if bulletin_type not in ["weekly", "crop_report", "other"]:
        return jsonify({"error": "type must be weekly, crop_report, or other"}), 400

    db = get_db()
    doc = {
        "filename": data["filename"],
        "driveFileId": data["driveFileId"],
        "type": bulletin_type,
        "season": data.get("season"),
        "week": data.get("week"),
        "uploaded_at": datetime.datetime.utcnow(),
        "uploaded_by": request.user["email"],
    }
    result = db.bulletins.insert_one(doc)
    return jsonify({"message": "Bulletin added", "id": str(result.inserted_id)}), 201

@bulletins_bp.route("/bulletins/<bulletin_id>", methods=["DELETE"])
@require_admin
def delete_bulletin(bulletin_id):
    db = get_db()
    result = db.bulletins.delete_one({"_id": ObjectId(bulletin_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Bulletin not found"}), 404
    return jsonify({"message": "Bulletin deleted"})
