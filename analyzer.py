"""
Performance analysis module for the Study Planning system.

This module only calculates study metrics from schedule and progress data.
It does not generate plans, update progress, handle files, or contain UI code.
"""


def calculate_completion_rate(progress):
    """
    Calculate the overall percentage of completed tasks.

    Formula:
        completed tasks / total tasks * 100
    """
    completed_tasks = progress.get("completed", [])
    pending_tasks = progress.get("pending", [])

    total_tasks = len(completed_tasks) + len(pending_tasks)
    if total_tasks == 0:
        return 0.0

    completion_rate = (len(completed_tasks) / total_tasks) * 100
    return round(completion_rate, 2)


def calculate_subject_performance(progress):
    """
    Calculate completion percentage for each subject.

    Each subject score is weight-aware:
        completed subject workload / total subject workload * 100
    """
    subject_totals = {}
    subject_completed = {}

    for task in progress.get("completed", []):
        subject = task.get("subject", "")
        weight = task.get("weight", 1)
        subject_totals[subject] = subject_totals.get(subject, 0) + weight
        subject_completed[subject] = subject_completed.get(subject, 0) + weight

    for task in progress.get("pending", []):
        subject = task.get("subject", "")
        weight = task.get("weight", 1)
        subject_totals[subject] = subject_totals.get(subject, 0) + weight

    performance = {}
    for subject, total_weight in subject_totals.items():
        completed_weight = subject_completed.get(subject, 0)
        performance[subject] = round((completed_weight / total_weight) * 100, 2)

    return performance


def calculate_consistency(schedule, progress):
    """
    Measure how consistently planned daily work is completed.

    Completed tasks may be removed from schedule by the tracker. To estimate
    the original daily plan, this function checks both remaining scheduled
    tasks and completed tasks that carry date information.
    """
    if not schedule:
        return 0.0

    completed_tasks = progress.get("completed", [])
    daily_scores = []

    for date, planned_tasks in schedule.items():
        original_day_tasks = planned_tasks.copy()

        # If completed tasks store their planned date, add them back for this
        # day's metric because they may no longer exist in schedule[date].
        for task in completed_tasks:
            task_date = task.get("date") or task.get("planned_date")
            if task_date == date and not _task_exists(original_day_tasks, task):
                original_day_tasks.append(task)

        if not original_day_tasks:
            daily_scores.append(0.0)
            continue

        completed_count = 0
        for task in original_day_tasks:
            if _task_exists(completed_tasks, task):
                completed_count += 1

        daily_score = (completed_count / len(original_day_tasks)) * 100
        daily_scores.append(daily_score)

    consistency = sum(daily_scores) / len(daily_scores)
    return round(consistency, 2)


def calculate_delay(schedule, progress):
    """
    Estimate delay using the number of pending tasks.

    This is a simple delay model:
        low    = up to 25% pending
        medium = up to 50% pending
        high   = more than 50% pending
    """
    completed_tasks = progress.get("completed", [])
    pending_tasks = progress.get("pending", [])

    total_tasks = len(completed_tasks) + len(pending_tasks)
    pending_count = len(pending_tasks)

    if total_tasks == 0:
        delay_level = "low"
    else:
        pending_ratio = pending_count / total_tasks

        if pending_ratio <= 0.25:
            delay_level = "low"
        elif pending_ratio <= 0.5:
            delay_level = "medium"
        else:
            delay_level = "high"

    return {
        "pending_tasks": pending_count,
        "delay_level": delay_level,
    }


def generate_metrics(schedule, progress):
    """
    Generate all performance metrics in one dictionary.
    """
    return {
        "completion_rate": calculate_completion_rate(progress),
        "subject_performance": calculate_subject_performance(progress),
        "consistency": calculate_consistency(schedule, progress),
        "delay": calculate_delay(schedule, progress),
        "time_performance": calculate_time_performance(progress),
    }


def calculate_time_performance(progress):
    """
    Compare actual completion time against estimated task time.
    """
    completed_tasks = progress.get("completed", [])
    timed_tasks = [
        task for task in completed_tasks if task.get("actual_time_taken") is not None
    ]

    if not timed_tasks:
        return {
            "average_ratio": 1.0,
            "overrun_tasks": 0,
            "timed_tasks": 0,
        }

    ratios = []
    overrun_tasks = 0

    for task in timed_tasks:
        actual_time = _to_float(task.get("actual_time_taken"), 0)
        estimated_time = _to_float(
            task.get("estimated_time", task.get("time_required", task.get("weight", 1))),
            1,
        )
        if estimated_time <= 0:
            estimated_time = 1

        ratio = actual_time / estimated_time
        ratios.append(ratio)

        if ratio > 1.2:
            overrun_tasks += 1

    average_ratio = sum(ratios) / len(ratios)

    return {
        "average_ratio": round(average_ratio, 2),
        "overrun_tasks": overrun_tasks,
        "timed_tasks": len(timed_tasks),
    }


def _task_exists(tasks, target_task):
    """
    Check whether a matching task exists in a list.
    """
    for task in tasks:
        if _same_task(task, target_task):
            return True

    return False


def _same_task(task1, task2):
    """
    Compare two tasks using the standard task fields.
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
