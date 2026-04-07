import jwt
import datetime
import requests
from flask import Blueprint, request, jsonify
from db import get_db
from config import JWT_SECRET, GOOGLE_CLIENT_ID, ADMIN_EMAIL, JWT_EXPIRY_DAYS

auth_bp = Blueprint("auth", __name__)

GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"

@auth_bp.route("/auth/google", methods=["POST"])
def google_login():
    data = request.get_json()
    id_token = data.get("idToken") if data else None

    if not id_token:
        return jsonify({"error": "idToken required"}), 400

    # Verify token with Google
    resp = requests.get(GOOGLE_TOKEN_INFO_URL, params={"id_token": id_token}, timeout=10)
    if resp.status_code != 200:
        return jsonify({"error": "Invalid Google token"}), 401

    google_data = resp.json()

    # Verify audience matches our client ID
    if google_data.get("aud") != GOOGLE_CLIENT_ID:
        return jsonify({"error": "Token audience mismatch"}), 401

    email = google_data["email"]
    role = "admin" if email == ADMIN_EMAIL else "agronomist"

    db = get_db()
    db.users.update_one(
        {"googleId": google_data["sub"]},
        {"$set": {
            "googleId": google_data["sub"],
            "email": email,
            "name": google_data.get("name", ""),
            "picture": google_data.get("picture", ""),
            "role": role,
        },
        "$setOnInsert": {"createdAt": datetime.datetime.utcnow()}},
        upsert=True,
    )

    payload = {
        "sub": google_data["sub"],
        "email": email,
        "name": google_data.get("name", ""),
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXPIRY_DAYS),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    return jsonify({
        "token": token,
        "user": {
            "email": email,
            "name": google_data.get("name", ""),
            "picture": google_data.get("picture", ""),
            "role": role,
        }
    })
