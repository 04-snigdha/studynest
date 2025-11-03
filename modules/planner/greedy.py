from datetime import datetime, timedelta
from typing import List
from .schema import Assignment, Timetable, PlanBlock, PlanResponse

def _t(s: str) -> datetime:
    return datetime.strptime(s, "%H:%M")

def _f(t: datetime) -> str:
    return t.strftime("%H:%M")

def greedy_schedule(assignments: List[Assignment], tt: Timetable) -> PlanResponse:
    # Sort by earliest deadline, then priority (1 is highest)
    items = sorted(assignments, key=lambda a: (a.deadline, a.priority))
    blocks: List[PlanBlock] = []
    notes: List[str] = []

    # Map day -> list of (window_start, window_end)
    windows = {}
    for w in tt.preferred_study_windows:
        windows.setdefault(w.day, []).append((_t(w.start), _t(w.end)))

    # Allocate blocks
    for a in items:
        remaining = int(a.estimated_hours * 60)
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            if remaining <= 0:
                break
            for ws, we in windows.get(day, []):
                used_today = sum(b.minutes for b in blocks if b.day == day)
                capacity = max(0, tt.max_hours_per_day * 60 - used_today)
                if capacity <= 0:
                    continue
                take = min(remaining, capacity, tt.min_block_minutes)
                start = (ws + timedelta(minutes=used_today)) if used_today > 0 else ws
                end = start + timedelta(minutes=take)
                if end > we:
                    continue
                blocks.append(
                    PlanBlock(
                        day=day,
                        start=_f(start),
                        end=_f(end),
                        task=a.task,
                        course_id=a.course_id,
                        minutes=take,
                        rationale=(
                            f"Placed early for {a.deadline}, keep ≤{tt.max_hours_per_day}h/day, "
                            f"respect preferred windows."
                        ),
                    )
                )
                remaining -= take
        if remaining > 0:
            notes.append(
                f"Could not fully place '{a.task}' (remaining {remaining} min). "
                "Add study windows or increase max_hours_per_day."
            )

    return PlanResponse(blocks=blocks, notes=notes)