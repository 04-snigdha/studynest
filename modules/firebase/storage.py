from typing import List, Dict, Any
from google.cloud.firestore_v1 import SERVER_TIMESTAMP
from .client import get_db

def _users(db, uid): 
    return db.collection("users").document(uid)

# Assignments
def upsert_assignments(uid: str, items: List[Dict[str, Any]]):
    db = get_db()
    batch = db.batch()
    col = _users(db, uid).collection("assignments")
    for it in items:
        doc_id = it.get("id") or f"{it['task'].lower()}_{it['deadline']}".replace(" ", "_")
        doc = col.document(doc_id)
        payload = {
            "course_id": it["course_id"],
            "task": it["task"],
            "est_hours": float(it["estimated_hours"]),
            "deadline": it["deadline"],
            "priority": int(it.get("priority", 2)),
            "status": it.get("status", "Not Started"),
            "updatedAt": SERVER_TIMESTAMP,
        }
        if it.get("createdAt") is None:
            payload["createdAt"] = SERVER_TIMESTAMP
        batch.set(doc, payload, merge=True)
    batch.commit()

def list_assignments(uid: str) -> List[Dict[str, Any]]:
    db = get_db()
    col = _users(db, uid).collection("assignments").order_by("deadline")
    return [{**d.to_dict(), "id": d.id} for d in col.stream()]

# Timetable
def put_timetable(uid: str, week_id: str, doc: Dict[str, Any]):
    db = get_db()
    _users(db, uid).collection("timetables").document(week_id).set(
        {**doc, "createdAt": SERVER_TIMESTAMP}, merge=True
    )

def get_timetable(uid: str, week_id: str) -> Dict[str, Any]:
    db = get_db()
    snap = _users(db, uid).collection("timetables").document(week_id).get()
    return snap.to_dict() or {}

# Notes (for RAG) — Firestore only: store chunks as subcollection
def put_note_chunks(uid: str, doc_id: str, meta: Dict[str, Any], chunks: List[Dict[str, Any]]):
    db = get_db()
    note_ref = _users(db, uid).collection("notes").document(doc_id)
    note_ref.set({**meta, "updatedAt": SERVER_TIMESTAMP}, merge=True)
    batch = db.batch()
    col = note_ref.collection("chunks")
    for i, ch in enumerate(chunks):
        batch.set(col.document(f"{i:05d}"), ch, merge=True)
    batch.commit()

def load_note_chunks(uid: str, doc_id: str) -> List[Dict[str, Any]]:
    db = get_db()
    col = _users(db, uid).collection("notes").document(doc_id).collection("chunks")
    return [d.to_dict() for d in col.stream()]

def list_notes(uid: str) -> List[Dict[str, Any]]:
    db = get_db()
    col = _users(db, uid).collection("notes")
    return [{**d.to_dict(), "id": d.id} for d in col.stream()]
