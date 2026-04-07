import datetime
from bson import ObjectId
from flask import Blueprint, request, jsonify
from db import get_db
from middleware.auth import require_auth

notifications_bp = Blueprint("notifications", __name__)

def create_notification(db, notif_type, message, metadata=None):
    """Call this from any route to broadcast a notification to all users."""
    db.notifications.insert_one({
        "type": notif_type,
        "message": message,
        "metadata": metadata or {},
        "read_by": [],
        "created_at": datetime.datetime.utcnow(),
    })

@notifications_bp.route("/notifications", methods=["GET"])
@require_auth
def get_notifications():
    db = get_db()
    docs = list(db.notifications.find({}).sort("created_at", -1).limit(50))
    user_email = request.user["email"]
    result = []
    for d in docs:
        result.append({
            "id": str(d["_id"]),
            "type": d["type"],
            "message": d["message"],
            "metadata": d.get("metadata", {}),
            "read": user_email in d.get("read_by", []),
            "created_at": d["created_at"].isoformat() if hasattr(d["created_at"], "isoformat") else str(d["created_at"]),
        })
    return jsonify(result)

@notifications_bp.route("/notifications/<notif_id>/read", methods=["POST"])
@require_auth
def mark_read(notif_id):
    db = get_db()
    db.notifications.update_one(
        {"_id": ObjectId(notif_id)},
        {"$addToSet": {"read_by": request.user["email"]}}
    )
    return jsonify({"message": "Marked as read"})

@notifications_bp.route("/notifications/read-all", methods=["POST"])
@require_auth
def mark_all_read():
    db = get_db()
    db.notifications.update_many(
        {},
        {"$addToSet": {"read_by": request.user["email"]}}
    )
    return jsonify({"message": "All marked as read"})
