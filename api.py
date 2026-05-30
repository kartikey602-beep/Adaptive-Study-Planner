"""
FastAPI backend for the connected Study Planning system.
"""

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

import analyzer
import planner
import recommender
import storage
import tracker


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "study_data.json"
FRONTEND_FILE = BASE_DIR / "studyflow.html"

DEFAULT_STATE = {
    "subjects": [],
    "exam_date": None,
    "daily_hours": 0,
    "preference": "balanced",
    "schedule": {},
    "progress": {
        "completed": [],
        "pending": [],
    },
}

app = FastAPI(title="Adaptive Study Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlanRequest(BaseModel):
    subjects: List[Dict[str, Any]]
    exam_date: str
    daily_hours: float
    preference: str = "balanced"
    user_preference: Optional[str] = None


class CompleteTaskRequest(BaseModel):
    date: str
    task: Union[Dict[str, Any], str]
    actual_time_taken: float


@app.get("/", response_class=HTMLResponse)
def index():
    """
    Serve the connected frontend.
    """
    if FRONTEND_FILE.exists():
        return FileResponse(FRONTEND_FILE)

    return HTMLResponse("<h1>Adaptive Study Planner API</h1>")


@app.post("/create-plan")
def create_plan(request: PlanRequest):
    """
    Create a new adaptive study plan and initialize progress.
    """
    previous_state = _load_state()
    previous_progress = previous_state.get("progress", {})
    subject_performance = analyzer.calculate_subject_performance(previous_progress)
    preference = request.user_preference or request.preference

    schedule = planner.generate_plan(
        request.subjects,
        request.exam_date,
        request.daily_hours,
        preference,
        subject_performance,
    )
    progress = tracker.initialize_progress(schedule)

    state = {
        "subjects": request.subjects,
        "exam_date": request.exam_date,
        "daily_hours": request.daily_hours,
        "preference": preference,
        "schedule": schedule,
        "progress": progress,
    }
    _save_state(state)

    return {
        "schedule": schedule,
        "progress": progress,
    }


@app.get("/plan")
def get_plan():
    """
    Return current schedule and progress.
    """
    state = _load_state()
    return {
        "schedule": state.get("schedule", {}),
        "progress": state.get("progress", DEFAULT_STATE["progress"]),
    }


@app.put("/complete-task")
def complete_task(request: CompleteTaskRequest):
    """
    Mark a task complete and record actual time taken.
    """
    state = _load_state()
    schedule = state.get("schedule", {})
    progress = state.get("progress", deepcopy(DEFAULT_STATE["progress"]))
    task = _resolve_task(schedule, request.date, request.task)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    schedule, progress = tracker.mark_task_complete(
        schedule,
        progress,
        request.date,
        task,
        request.actual_time_taken,
    )
    progress = tracker.sync_pending_with_schedule(schedule, progress)

    state["schedule"] = schedule
    state["progress"] = progress
    _save_state(state)

    return {
        "schedule": schedule,
        "progress": progress,
    }


@app.get("/metrics")
def get_metrics():
    """
    Return analyzer metrics for the current plan.
    """
    state = _load_state()
    metrics = analyzer.generate_metrics(
        state.get("schedule", {}),
        state.get("progress", DEFAULT_STATE["progress"]),
    )

    return {"metrics": metrics}


@app.get("/recommendations")
def get_recommendations():
    """
    Return adaptive study recommendations.
    """
    state = _load_state()
    schedule = state.get("schedule", {})
    progress = state.get("progress", DEFAULT_STATE["progress"])
    metrics = analyzer.generate_metrics(schedule, progress)
    suggestions = recommender.generate_recommendations(metrics, progress)

    return {"recommendations": suggestions}


@app.post("/rebalance")
def rebalance():
    """
    Rebalance the remaining pending tasks using current performance data.
    """
    state = _load_state()
    exam_date = state.get("exam_date")

    if not exam_date:
        raise HTTPException(status_code=400, detail="Create a plan before rebalancing")

    schedule = state.get("schedule", {})
    progress = state.get("progress", deepcopy(DEFAULT_STATE["progress"]))
    pending_tasks = tracker.get_pending_tasks(schedule, progress)
    subject_performance = analyzer.calculate_subject_performance(progress)

    updated_schedule = planner.rebalance_plan(
        pending_tasks,
        exam_date,
        state.get("daily_hours", 0),
        state.get("preference", "balanced"),
        subject_performance,
    )
    progress = tracker.sync_pending_with_schedule(updated_schedule, progress)

    state["schedule"] = updated_schedule
    state["progress"] = progress
    _save_state(state)

    return {
        "schedule": updated_schedule,
        "progress": progress,
    }


def _load_state():
    """
    Load persisted app state with defaults for missing keys.
    """
    state = deepcopy(DEFAULT_STATE)
    saved_state = storage.load_study_data(str(DATA_FILE))

    if isinstance(saved_state, dict):
        for key, value in saved_state.items():
            state[key] = value

    state.setdefault("progress", deepcopy(DEFAULT_STATE["progress"]))
    state["progress"].setdefault("completed", [])
    state["progress"].setdefault("pending", [])

    return state


def _save_state(state):
    """
    Persist app state to JSON storage.
    """
    if not storage.save_data(str(DATA_FILE), state):
        raise HTTPException(status_code=500, detail="Unable to save study data")


def _resolve_task(schedule, task_date, task_input):
    """
    Resolve task input from the API into a scheduled task dictionary.
    """
    if isinstance(task_input, dict):
        candidate = task_input
    else:
        candidate = {"topic": str(task_input)}

    day_tasks = schedule.get(task_date, [])
    for task in day_tasks:
        if _same_task(task, candidate):
            return task.copy()

    for tasks in schedule.values():
        for task in tasks:
            if _same_task(task, candidate):
                return task.copy()

    return candidate.copy() if isinstance(task_input, dict) else None


def _same_task(task1, task2):
    """
    Compare API task inputs by stable identity fields.
    """
    subject_matches = (
        not task2.get("subject")
        or task1.get("subject") == task2.get("subject")
    )
    topic_matches = task1.get("topic") == task2.get("topic")

    return subject_matches and topic_matches
