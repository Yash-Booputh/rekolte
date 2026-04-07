import io
import datetime
from bson import ObjectId
from flask import Blueprint, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
from db import get_db
from middleware.auth import require_auth
from routes.notifications import create_notification
import config
import json

bulletins_bp = Blueprint("bulletins", __name__)

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def _get_drive_service():
    if config.GOOGLE_SERVICE_ACCOUNT_JSON:
        info = json.loads(config.GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(info, scopes=DRIVE_SCOPES)
    else:
        creds = service_account.Credentials.from_service_account_file(
            config.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=DRIVE_SCOPES
        )
    return build("drive", "v3", credentials=creds)

def _get_folder_id(season):
    if season and int(season) <= 2019:
        return config.DRIVE_FOLDER_2008_2019
    return config.DRIVE_FOLDER_2020_2026

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
        # Build preview and download URLs from Drive file ID
        fid = d.get("driveFileId")
        if fid:
            d["preview_url"] = f"https://drive.google.com/file/d/{fid}/preview"
            d["download_url"] = f"https://drive.google.com/uc?export=download&id={fid}"

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

    folder_id = _get_folder_id(season)

    try:
        service = _get_drive_service()
        file_bytes = file.read()
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype="application/pdf")
        drive_file = service.files().create(
            body={"name": file.filename, "parents": [folder_id]},
            media_body=media,
            fields="id",
        ).execute()
        drive_file_id = drive_file.get("id")
    except Exception as e:
        return jsonify({"error": f"Drive upload failed: {str(e)}"}), 500

    db = get_db()
    doc = {
        "filename": file.filename,
        "driveFileId": drive_file_id,
        "type": bulletin_type,
        "season": int(season) if season else None,
        "week": int(week) if week else None,
        "uploaded_at": datetime.datetime.utcnow(),
        "uploaded_by": request.user["email"],
        "preview_url": f"https://drive.google.com/file/d/{drive_file_id}/preview",
        "download_url": f"https://drive.google.com/uc?export=download&id={drive_file_id}",
    }
    result = db.bulletins.insert_one(doc)

    create_notification(db, "bulletin_uploaded",
        f"New bulletin uploaded: {file.filename}",
        {"filename": file.filename, "season": season, "uploaded_by": request.user["email"]}
    )

    return jsonify({"message": "Bulletin uploaded to Drive", "id": str(result.inserted_id),
                    "driveFileId": drive_file_id}), 201

@bulletins_bp.route("/bulletins/<bulletin_id>", methods=["DELETE"])
@require_auth
def delete_bulletin(bulletin_id):
    db = get_db()
    result = db.bulletins.delete_one({"_id": ObjectId(bulletin_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Bulletin not found"}), 404
    return jsonify({"message": "Bulletin deleted"})
