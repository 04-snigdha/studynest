from pydantic import BaseModel
from typing import List, Optional

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