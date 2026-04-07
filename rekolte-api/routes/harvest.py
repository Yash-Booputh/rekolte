import datetime
from flask import Blueprint, request, jsonify
from db import get_db
from middleware.auth import require_auth, require_admin

harvest_bp = Blueprint("harvest", __name__)

REGIONS = ["NORD", "SUD", "EST", "OUEST", "CENTRE"]

@harvest_bp.route("/harvest", methods=["GET"])
@require_auth
def get_harvest():
    db = get_db()
    region = request.args.get("region", "").upper() or None
    season = request.args.get("season")

    query = {}
    if region and region in REGIONS:
        query["region"] = region
    if season:
        query["season"] = int(season)

    docs = list(db.harvest_data.find(query, {"_id": 0}).sort([("season", -1), ("week", -1)]))
    return jsonify(docs)

@harvest_bp.route("/harvest/<region>", methods=["GET"])
@require_auth
def get_harvest_by_region(region):
    region = region.upper()
    if region not in REGIONS:
        return jsonify({"error": f"region must be one of {REGIONS}"}), 400

    db = get_db()
    docs = list(db.harvest_data.find({"region": region}, {"_id": 0}).sort([("season", -1), ("week", -1)]))
    return jsonify(docs)

@harvest_bp.route("/harvest", methods=["POST"])
@require_admin
def add_harvest():
    data = request.get_json()
    required = ["season", "week", "region", "tch"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    region = data["region"].upper()
    if region not in REGIONS:
        return jsonify({"error": f"region must be one of {REGIONS}"}), 400

    db = get_db()
    doc = {
        "season": int(data["season"]),
        "week": int(data["week"]),
        "region": region,
        "surface_harvested": data.get("surface_harvested"),
        "cane_production": data.get("cane_production"),
        "sugar_production": data.get("sugar_production"),
        "extraction_rate": data.get("extraction_rate"),
        "tch": float(data["tch"]),
        "tsh": data.get("tsh"),
        "source_bulletin": data.get("source_bulletin", ""),
        "added_by": request.user["email"],
        "added_at": datetime.datetime.utcnow(),
    }

    # Upsert to avoid duplicates
    db.harvest_data.update_one(
        {"season": doc["season"], "week": doc["week"], "region": doc["region"]},
        {"$set": doc},
        upsert=True,
    )
    return jsonify({"message": "Harvest record saved"}), 201
