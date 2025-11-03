import os
from typing import Optional
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
from dotenv import load_dotenv

load_dotenv()  # loads .env in project root

# ENV expected:
# FIREBASE_PROJECT_ID=...
# FIREBASE_STORAGE_BUCKET=...
# GOOGLE_APPLICATION_CREDENTIALS=./firebase-admin-key.json
PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
DEV_UID = os.getenv("DEV_UID")  # optional convenience for local dev

if not firebase_admin._apps:
    cred = credentials.Certificate(KEY_PATH) if KEY_PATH else credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {"storageBucket": BUCKET} if BUCKET else None)

_db = firestore.client()
_bucket = storage.bucket() if BUCKET else None

def get_db():
    return _db

def get_bucket():
    return _bucket

def verify_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    """
    Returns uid if a valid Firebase ID token is provided in Authorization: Bearer <token>.
    If no token and DEV_UID is set, returns DEV_UID (dev mode).
    """
    if authorization_header and authorization_header.lower().startswith("bearer "):
        id_token = authorization_header.split(" ", 1)[1].strip()
        decoded = auth.verify_id_token(id_token, check_revoked=False)
        return decoded["uid"]
    # Dev fallback (no auth)
    if DEV_UID:
        return DEV_UID
    return None