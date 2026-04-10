import io
import datetime
from bson import ObjectId
from flask import Blueprint, request, jsonify
from db import get_db
from middleware.auth import require_auth
from routes.notifications import create_notification
import config

bulletins_bp = Blueprint("bulletins", __name__)


def _upload_to_cloudinary(file_bytes: bytes, filename: str) -> str:
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=config.CLOUDINARY_CLOUD_NAME,
        api_key=config.CLOUDINARY_API_KEY,
        api_secret=config.CLOUDINARY_API_SECRET,
    )
    result = cloudinary.uploader.upload(
        io.BytesIO(file_bytes),
        resource_type="raw",
        folder="bulletins",
        use_filename=True,
        unique_filename=True,
        overwrite=False,
    )
    return result["secure_url"]


@bulletins_bp.route("/bulletins", methods=["GET"])
@require_auth
def get_bulletins():
    db = get_db()
    season = request.args.get("season")
    bulletin_type = request.args.get("type")

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


@bulletins_bp.route("/bulletins/upload", methods=["POST"])
@require_auth
def upload_bulletin():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are accepted"}), 400

    season = request.form.get("season")
    bulletin_type = request.form.get("type", "weekly")
    week = request.form.get("week")

    if bulletin_type not in ["weekly", "crop_report", "other"]:
        return jsonify({"error": "type must be weekly, crop_report, or other"}), 400

    if not config.CLOUDINARY_CLOUD_NAME:
        return jsonify({"error": "File storage not configured (CLOUDINARY_CLOUD_NAME missing)"}), 500

    try:
        file_bytes = file.read()
        cloudinary_url = _upload_to_cloudinary(file_bytes, file.filename)
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

    db = get_db()
    doc = {
        "filename": file.filename,
        "cloudinaryUrl": cloudinary_url,
        "type": bulletin_type,
        "season": int(season) if season else None,
        "week": int(week) if week else None,
        "uploaded_at": datetime.datetime.utcnow(),
        "uploaded_by": request.user["email"],
        "preview_url": cloudinary_url,
        "download_url": cloudinary_url,
    }
    result = db.bulletins.insert_one(doc)

    create_notification(db, "bulletin_uploaded",
        f"New bulletin uploaded: {file.filename}",
        {"filename": file.filename, "season": season, "uploaded_by": request.user["email"]}
    )

    return jsonify({"message": "Bulletin uploaded", "id": str(result.inserted_id)}), 201


@bulletins_bp.route("/bulletins/<bulletin_id>", methods=["DELETE"])
@require_auth
def delete_bulletin(bulletin_id):
    db = get_db()
    result = db.bulletins.delete_one({"_id": ObjectId(bulletin_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Bulletin not found"}), 404
    return jsonify({"message": "Bulletin deleted"})
