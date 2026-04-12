import io
import json
import datetime
from bson import ObjectId
from flask import Blueprint, request, jsonify
from db import get_db
from middleware.auth import require_auth
from routes.notifications import create_notification
import config

bulletins_bp = Blueprint("bulletins", __name__)


def _get_drive_service():
    from googleapiclient.discovery import build
    from google.oauth2 import service_account

    if not config.GOOGLE_SERVICE_ACCOUNT_JSON:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON not configured")

    creds = service_account.Credentials.from_service_account_info(
        json.loads(config.GOOGLE_SERVICE_ACCOUNT_JSON),
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    return build("drive", "v3", credentials=creds)


def _upload_to_drive(file_bytes: bytes, filename: str):
    """Upload PDF to Drive, make publicly readable.
    Returns (file_id, preview_url, download_url).
    """
    from googleapiclient.http import MediaIoBaseUpload

    service = _get_drive_service()

    metadata = {"name": filename}
    if config.DRIVE_BULLETINS_FOLDER_ID:
        metadata["parents"] = [config.DRIVE_BULLETINS_FOLDER_ID]

    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype="application/pdf")
    created = service.files().create(
        body=metadata, media_body=media, fields="id"
    ).execute()

    file_id = created["id"]

    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
        fields="id",
    ).execute()

    return (
        file_id,
        f"https://drive.google.com/file/d/{file_id}/preview",
        f"https://drive.google.com/uc?export=download&id={file_id}",
    )


def _delete_from_drive(file_id: str) -> None:
    try:
        _get_drive_service().files().delete(fileId=file_id).execute()
    except Exception:
        pass  # best-effort — don't fail the request if Drive delete fails


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

    if not config.GOOGLE_SERVICE_ACCOUNT_JSON:
        return jsonify({"error": "File storage not configured (GOOGLE_SERVICE_ACCOUNT_JSON missing)"}), 500

    try:
        file_bytes = file.read()
        file_id, preview_url, download_url = _upload_to_drive(file_bytes, file.filename)
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

    db = get_db()
    doc = {
        "filename": file.filename,
        "driveFileId": file_id,
        "type": bulletin_type,
        "season": int(season) if season else None,
        "week": int(week) if week else None,
        "uploaded_at": datetime.datetime.utcnow(),
        "uploaded_by": request.user["email"],
        "preview_url": preview_url,
        "download_url": download_url,
    }
    result = db.bulletins.insert_one(doc)

    create_notification(
        db,
        "bulletin_uploaded",
        f"New bulletin uploaded: {file.filename}",
        {"filename": file.filename, "season": season, "uploaded_by": request.user["email"]},
    )

    return jsonify({"message": "Bulletin uploaded", "id": str(result.inserted_id)}), 201


@bulletins_bp.route("/bulletins/<bulletin_id>", methods=["DELETE"])
@require_auth
def delete_bulletin(bulletin_id):
    db = get_db()
    doc = db.bulletins.find_one({"_id": ObjectId(bulletin_id)})
    if not doc:
        return jsonify({"error": "Bulletin not found"}), 404

    if doc.get("driveFileId"):
        _delete_from_drive(doc["driveFileId"])

    db.bulletins.delete_one({"_id": ObjectId(bulletin_id)})
    return jsonify({"message": "Bulletin deleted"})
