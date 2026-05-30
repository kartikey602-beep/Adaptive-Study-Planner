"""
JSON storage module for the Study Planning system.

This module only handles saving, loading, and updating JSON data.
It does not contain planning, tracking, analysis, recommendation, or UI logic.
"""

import json
import os


DEFAULT_STUDY_DATA = {
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


def save_data(file_path, data):
    """
    Save data to a JSON file.

    If the file or parent folder does not exist, it will be created.
    Existing file content is overwritten.
    """
    try:
        folder_path = os.path.dirname(file_path)
        if folder_path:
            os.makedirs(folder_path, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        return True
    except (OSError, TypeError):
        return False


def load_data(file_path):
    """
    Load data from a JSON file.

    If the file does not exist or cannot be decoded, an empty dictionary is
    returned so the application can continue safely.
    """
    if not os.path.exists(file_path):
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}


def load_study_data(file_path):
    """
    Load study data with defaults for adaptive planning fields.
    """
    return ensure_study_data(load_data(file_path))


def ensure_study_data(data):
    """
    Ensure persisted JSON can hold schedules, progress, and learned time data.
    """
    normalized_data = DEFAULT_STUDY_DATA.copy()
    normalized_data["progress"] = {
        "completed": [],
        "pending": [],
    }

    if isinstance(data, dict):
        normalized_data.update(data)

    progress = normalized_data.get("progress")
    if not isinstance(progress, dict):
        progress = {}

    progress.setdefault("completed", [])
    progress.setdefault("pending", [])
    normalized_data["progress"] = progress

    return normalized_data


def update_data(file_path, key, value):
    """
    Update one key in the JSON data file.

    Existing data is loaded first, the key is updated, and the full dictionary
    is saved back to the same file.
    """
    data = load_data(file_path)
    data[key] = value

    return save_data(file_path, data)
