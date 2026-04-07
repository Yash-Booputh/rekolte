import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.environ["MONGODB_URI"]
JWT_SECRET = os.environ["JWT_SECRET"]
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "yashvinbooputh2@gmail.com")
JWT_EXPIRY_DAYS = 7
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

# Google Drive bulletin folders
DRIVE_FOLDER_2008_2019 = "1QJsCzzW0iBOjEJWcOJYBIZmrX9Ki2lFJ"
DRIVE_FOLDER_2020_2026 = "1_NaQbkf7zDwkn1-I1Kn5APGLBklW6rrF"

# Service account: use JSON env var on Render, fall back to local file in dev
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_SERVICE_ACCOUNT_FILE = os.path.join(
    os.path.dirname(__file__), "rekolte-491422-3e97a23e3559.json"
)
