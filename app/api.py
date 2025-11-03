from fastapi import FastAPI, Depends, Header, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


app = FastAPI(title="StudyNest 2.0 API")

@app.get("/health")
def health():
    return {"ok": True, "service": "studynest2", "version": "0.1.0"}

def get_uid(authorization: Optional[str] = Header(default=None, convert_underscores=False)) -> str:
    # Local import to avoid circulars
    from modules.firebase.client import verify_bearer_token
    uid = verify_bearer_token(authorization)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized: missing or invalid token (set DEV_UID for local dev).")
    return uid

# ==== Planner models (API schema) ====
class ClassBlock(BaseModel):
    course_id: str
    day: str
    start: str
    end: str

class StudyWindow(BaseModel):
    day: str
    start: str
    end: str

class Timetable(BaseModel):
    weekly_classes: List[ClassBlock] = []
    preferred_study_windows: List[StudyWindow] = []
    max_hours_per_day: int = 4
    min_block_minutes: int = 50
    break_policy: str = "50/10"

class Assignment(BaseModel):
    course_id: str
    task: str
    estimated_hours: float
    deadline: str
    priority: int = 2

class PlanBlock(BaseModel):
    day: str
    start: str
    end: str
    task: str
    course_id: str
    minutes: int
    rationale: Optional[str] = None

class PlanResponse(BaseModel):
    blocks: List[PlanBlock]
    notes: List[str] = []

@app.post("/plan", response_model=PlanResponse)
def plan(assignments: List[Assignment], timetable: Timetable):
    # Local import avoids circular imports during early dev
    from modules.planner.service import plan_week
    # Convert pydantic models to planner models (same fields, so reuse)
    return plan_week(assignments, timetable)

from pydantic import BaseModel

@app.post("/assignments/upsert")
def assignments_upsert(payload: list[Assignment], uid: str = Depends(get_uid)):
    from modules.firebase.storage import upsert_assignments
    upsert_assignments(uid, [p.dict() for p in payload])
    return {"ok": True, "count": len(payload)}

@app.get("/assignments")
def assignments_list(uid: str = Depends(get_uid)):
    from modules.firebase.storage import list_assignments
    return {"items": list_assignments(uid)}

class TimetablePut(BaseModel):
    week_id: str
    data: Timetable

@app.post("/timetable/put")
def timetable_put(body: TimetablePut, uid: str = Depends(get_uid)):
    from modules.firebase.storage import put_timetable
    put_timetable(uid, body.week_id, body.data.dict())
    return {"ok": True, "week_id": body.week_id}

@app.get("/timetable/{week_id}")
def timetable_get(week_id: str, uid: str = Depends(get_uid)):
    from modules.firebase.storage import get_timetable
    return {"week_id": week_id, "data": get_timetable(uid, week_id)}

# ---- RAG helpers (Firestore-only) ----
def _chunk(text: str, size: int = 800, overlap: int = 200):
    n = len(text); i = 0; out = []
    while i < n:
        j = min(i + size, n)
        out.append({"text": text[i:j], "span": [i, j]})
        if j == n:
            break
        i = j - overlap
    return out

@app.post("/notes/ingest")
async def notes_ingest(
    doc_id: str = Form(...),
    file: UploadFile = File(...),
    uid: str = Depends(get_uid),
):
    from modules.firebase.storage import put_note_chunks
    raw = (await file.read()).decode("utf-8", errors="ignore")
    chunks = _chunk(raw, 800, 200)
    meta = {"title": file.filename, "chunk_size": 800, "overlap": 200}
    put_note_chunks(uid, doc_id, meta, chunks)
    return {"ok": True, "doc_id": doc_id, "chunks": len(chunks)}

@app.get("/notes/list")
def notes_list(uid: str = Depends(get_uid)):
    from modules.firebase.storage import list_notes
    return {"items": list_notes(uid)}

class RagQuery(BaseModel):
    doc_id: str
    question: str
    k: int = 6

@app.post("/rag/answer")
def rag_answer(q: RagQuery, uid: str = Depends(get_uid)):
    from modules.firebase.storage import load_note_chunks
    chunks = load_note_chunks(uid, q.doc_id)
    if not chunks:
        return {"answer": "No chunks found for this doc_id.", "citations": []}
    corpus = [c["text"] for c in chunks]
    vec = TfidfVectorizer(stop_words="english")
    X = vec.fit_transform(corpus)
    qs = vec.transform([q.question])
    sims = cosine_similarity(qs, X)[0]
    idxs = sims.argsort()[::-1][:q.k]
