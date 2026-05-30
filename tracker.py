"""
Progress tracking module for the Study Planning system.

This module only tracks task progress. It does not generate schedules,
perform file operations, or contain any UI logic.
"""


def initialize_progress(schedule):
    """
    Create the initial progress structure from a study schedule.

    All scheduled tasks are copied into pending so later changes to schedule
    tasks do not accidentally affect the progress data.
    """
    return {
        "completed": [],
        "pending": [task.copy() for task in _get_all_scheduled_tasks(schedule)],
    }


def mark_task_complete(schedule, progress, date, task, actual_time_taken=None):
    """
    Mark a task as completed and store adaptive time feedback.

    The completed task records actual_time_taken. Its estimated time is then
    updated using:
        new_time = estimated_time * 0.7 + actual_time_taken * 0.3
    """
    progress.setdefault("completed", [])
    progress.setdefault("pending", [])

    target_task = _ensure_task_dict(task)
    matched_task = _find_task(schedule.get(date, []), target_task) or target_task.copy()
    completed_task = _apply_actual_time(matched_task, actual_time_taken)
    completed_task["date"] = date
    completed_task["planned_date"] = date

    if date in schedule:
        schedule[date] = _remove_task(schedule[date], completed_task)

    progress["completed"] = _remove_task(progress["completed"], completed_task)
    progress["completed"].append(completed_task)
    progress["pending"] = _remove_task(progress["pending"], completed_task)

    return schedule, progress


def get_pending_tasks(schedule, progress):
    """
    Return all tasks that are still pending.

    Pending tasks are collected from the current schedule and the progress
    data, then completed tasks and duplicates are removed.
    """
    completed_tasks = progress.get("completed", [])

    pending_tasks = []
    pending_tasks.extend(_get_all_scheduled_tasks(schedule))
    pending_tasks.extend(progress.get("pending", []))

    pending_tasks = [
        task.copy()
        for task in pending_tasks
        if not _task_exists(completed_tasks, task)
    ]

    return _remove_duplicate_tasks(pending_tasks)


def sync_pending_with_schedule(schedule, progress):
    """
    Replace pending progress with the current scheduled remaining tasks.
    """
    progress.setdefault("completed", [])
    progress["pending"] = [
        task.copy()
        for task in _get_all_scheduled_tasks(schedule)
        if not _task_exists(progress["completed"], task)
    ]

    return progress


def calculate_progress(progress):
    """
    Calculate basic completion metrics from progress data.
    """
    completed_tasks = progress.get("completed", [])
    pending_tasks = progress.get("pending", [])

    total_tasks = len(completed_tasks) + len(pending_tasks)
    completed_count = len(completed_tasks)

    if total_tasks == 0:
        completion_percentage = 0.0
    else:
        completion_percentage = (completed_count / total_tasks) * 100

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_count,
        "completion_percentage": round(completion_percentage, 2),
    }


def _apply_actual_time(task, actual_time_taken):
    """
    Store actual time and update adaptive estimated time fields.
    """
    updated_task = task.copy()
    actual_time = _to_float(actual_time_taken, None)

    if actual_time is None:
        return updated_task

    estimated_time = _to_float(
        updated_task.get("time_required", updated_task.get("weight", 1)),
        1.0,
    )
    new_time = round((estimated_time * 0.7) + (actual_time * 0.3), 2)

    updated_task["actual_time_taken"] = actual_time
    updated_task["estimated_time"] = estimated_time
    updated_task["time_required"] = max(new_time, 0.1)
    updated_task["weight"] = max(new_time, 0.1)

    return updated_task


def _get_all_scheduled_tasks(schedule):
    """
    Flatten all scheduled tasks into one list.
    """
    tasks = []

    for daily_tasks in schedule.values():
        for task in daily_tasks:
            tasks.append(task)

    return tasks


def _find_task(tasks, target_task):
    """
    Find a matching task in a list.
    """
    for task in tasks:
        if _same_task(task, target_task):
            return task.copy()

    return None


def _ensure_task_dict(task):
    """
    Normalize task input to a dictionary.
    """
    if isinstance(task, dict):
        return task

    return {"topic": str(task)}


def _remove_task(tasks, target_task):
    """
    Remove matching tasks from a task list.
    """
    return [task for task in tasks if not _same_task(task, target_task)]


def _task_exists(tasks, target_task):
    """
    Check whether a matching task exists in a task list.
    """
    for task in tasks:
        if _same_task(task, target_task):
            return True

    return False


def _remove_duplicate_tasks(tasks):
    """
    Remove duplicate tasks while keeping the original order.
    """
    unique_tasks = []

    for task in tasks:
        if not _task_exists(unique_tasks, task):
            unique_tasks.append(task)

    return unique_tasks


def _same_task(task1, task2):
    """
    Compare two tasks using stable planner identity fields.
    """
    return (
        task1.get("subject") == task2.get("subject")
        and task1.get("topic") == task2.get("topic")
    )


def _to_float(value, default):
    """
    Convert values to float with a fallback.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
