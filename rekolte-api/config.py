import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.environ["MONGODB_URI"]
JWT_SECRET = os.environ["JWT_SECRET"]
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "yashvinbooputh2@gmail.com")
JWT_EXPIRY_DAYS = 7
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

# Google Drive — bulletin PDF storage
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
DRIVE_BULLETINS_FOLDER_ID = os.environ.get("DRIVE_BULLETINS_FOLDER_ID", "")
