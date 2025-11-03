from typing import List
from .schema import Assignment, Timetable, PlanResponse
from .greedy import greedy_schedule

def plan_week(assignments: List[Assignment], timetable: Timetable) -> PlanResponse:
    # Placeholder for future: bandit/risk models.
    return greedy_schedule(assignments, timetable)