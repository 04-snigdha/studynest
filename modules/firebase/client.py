import os
from typing import Optional
import firebase_admin
from firebase_admin import credentials, auth, firestore
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
KEY_PATH   = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
DEV_UID    = os.getenv("DEV_UID")

# Resolve absolute path and validate
if not KEY_PATH:
    raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS not set in env/.env")
KEY_PATH = os.path.abspath(KEY_PATH)
if not os.path.exists(KEY_PATH):
    raise RuntimeError(f"Service account file not found at: {KEY_PATH}")

if not firebase_admin._apps:
    cred = credentials.Certificate(KEY_PATH)  # <-- force service account, never ADC
    firebase_admin.initialize_app(cred)

_db = firestore.client()

def get_db():
    return _db

def verify_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    # Dev-friendly: if no header or verification fails, fall back to DEV_UID
    try:
        if authorization_header and authorization_header.lower().startswith("bearer "):
            id_token = authorization_header.split(" ", 1)[1].strip()
            decoded = auth.verify_id_token(id_token, check_revoked=False)
            return decoded["uid"]
    except Exception:
        pass
    return DEV_UID  # may be None in prod; fine for dev