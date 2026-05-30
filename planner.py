"""
Core scheduling engine for the Study Planning system.

This module only contains planning logic. It does not handle UI work,
file storage, or JSON operations. All functions work with normal Python
data structures and return a schedule dictionary.
"""

from datetime import date, datetime, timedelta


DEFAULT_SUBJECT_PERFORMANCE = 50.0
PENDING_PRIORITY_BOOST = 0.15


def generate_plan(
    subjects,
    exam_date,
    daily_hours,
    user_preference="balanced",
    subject_performance=None,
):
    """
    Generate a time-prioritized study plan from subject/topic input.

    Args:
        subjects (list): List of subjects with their topics and time_required.
        exam_date (str): Exam date in YYYY-MM-DD format.
        daily_hours (int | float): Maximum workload allowed per day.
        user_preference (str): Either "balanced" or "focus".
        subject_performance (dict): Optional subject score mapping.

    Returns:
        dict: Schedule in the format:
              {"YYYY-MM-DD": [{"subject": "...", "topic": "..."}]}
    """
    tasks = _flatten_subjects(subjects)
    days_left = _calculate_days_left(exam_date)
    tasks = _prepare_tasks(tasks, subject_performance, days_left)
    tasks = _sort_tasks_by_priority(tasks)

    available_days = _calculate_available_days(exam_date)
    schedule = _allocate_tasks(tasks, available_days, daily_hours, user_preference)

    return _balance_subjects(schedule, user_preference)


def rebalance_plan(
    pending_tasks,
    exam_date,
    daily_hours,
    user_preference="balanced",
    subject_performance=None,
):
    """
    Rebuild a schedule using only pending tasks.

    Pending tasks receive a small priority boost before the schedule is
    regenerated, so unfinished work moves earlier in the new plan.
    """
    boosted_tasks = []
    for task in pending_tasks:
        copied_task = task.copy()
        copied_task["priority_boost"] = (
            float(copied_task.get("priority_boost", 0)) + PENDING_PRIORITY_BOOST
        )
        boosted_tasks.append(copied_task)

    days_left = _calculate_days_left(exam_date)
    tasks = _prepare_tasks(boosted_tasks, subject_performance, days_left)
    tasks = _sort_tasks_by_priority(tasks)

    available_days = _calculate_available_days(exam_date)
    schedule = _allocate_tasks(tasks, available_days, daily_hours, user_preference)

    return _balance_subjects(schedule, user_preference)


def calculate_priority(task, subject_performance, days_left):
    """
    Calculate mandatory time-based priority.

    Formula:
        priority = (normalized_time * 0.5) + (urgency * 0.3) + (weakness * 0.2)
    """
    normalized_time = _clamp(float(task.get("normalized_time", 0)), 0.0, 1.0)
    urgency = _clamp(1 / max(int(days_left), 1), 0.0, 1.0)
    subject = task.get("subject", "")
    performance = _get_subject_performance(subject_performance, subject)
    weakness = _clamp(1 - (performance / 100), 0.0, 1.0)
    priority_boost = max(float(task.get("priority_boost", 0)), 0.0)

    return round(
        (normalized_time * 0.5)
        + (urgency * 0.3)
        + (weakness * 0.2)
        + priority_boost,
        4,
    )


def _flatten_subjects(subjects):
    """
    Convert nested subject input into a flat task list.

    Example:
        [{"name": "Math", "topics": [{"name": "Algebra", "time_required": 2}]}]

    Becomes:
        [{"subject": "Math", "topic": "Algebra", "time_required": 2}]
    """
    tasks = []

    for subject in subjects:
        subject_name = subject.get("name") or subject.get("subject", "")
        topics = subject.get("topics", [])

        for topic in topics:
            task = {
                "subject": subject_name,
                "topic": topic.get("name") or topic.get("topic", ""),
                "time_required": _read_time_required(topic),
            }

            if "difficulty" in topic:
                task["difficulty"] = topic.get("difficulty")
            if "actual_time_taken" in topic:
                task["actual_time_taken"] = topic.get("actual_time_taken")
            if "priority_boost" in topic:
                task["priority_boost"] = topic.get("priority_boost")

            tasks.append(task)

    return tasks


def _prepare_tasks(tasks, subject_performance, days_left):
    """
    Normalize time, calculate priority, and preserve scheduling fields.
    """
    normalized_tasks = []

    for task in tasks:
        copied_task = task.copy()
        if "topic" not in copied_task and "name" in copied_task:
            copied_task["topic"] = copied_task["name"]

        copied_task["time_required"] = _read_time_required(copied_task)
        copied_task["weight"] = copied_task["time_required"]
        normalized_tasks.append(copied_task)

    _normalize_task_times(normalized_tasks)

    for task in normalized_tasks:
        task["priority"] = calculate_priority(
            task,
            subject_performance or {},
            days_left,
        )

    return normalized_tasks


def _read_time_required(task):
    """
    Read task duration from modern and legacy fields.
    """
    for field in ("time_required", "estimated_time", "weight"):
        value = task.get(field)
        if value is not None:
            return max(_to_float(value, 1.0), 0.1)

    return max(_difficulty_to_weight(task.get("difficulty", 1)), 0.1)


def _normalize_task_times(tasks):
    """
    Scale each task time_required value into the 0-1 range.
    """
    if not tasks:
        return

    max_time = max(task.get("time_required", 0.1) for task in tasks)
    if max_time <= 0:
        for task in tasks:
            task["normalized_time"] = 0.0
        return

    for task in tasks:
        task["normalized_time"] = round(
            _clamp(task.get("time_required", 0.1) / max_time, 0.0, 1.0),
            4,
        )


def _calculate_available_days(exam_date):
    """
    Calculate all study dates from today up to the day before the exam.
    """
    today = date.today()
    exam_day = datetime.strptime(exam_date, "%Y-%m-%d").date()

    total_days = (exam_day - today).days
    if total_days <= 0:
        return []

    days = []
    for day_offset in range(total_days):
        study_day = today + timedelta(days=day_offset)
        days.append(study_day.strftime("%Y-%m-%d"))

    return days


def _calculate_days_left(exam_date):
    """
    Return days from today until the exam, clamped to at least one.
    """
    exam_day = datetime.strptime(exam_date, "%Y-%m-%d").date()
    return max((exam_day - date.today()).days, 1)


def _difficulty_to_weight(difficulty):
    """
    Convert legacy difficulty into estimated study hours.
    """
    difficulty_weights = {
        1: 1,
        2: 1.5,
        3: 2,
        "1": 1,
        "2": 1.5,
        "3": 2,
        "easy": 1,
        "medium": 1.5,
        "hard": 2,
    }

    if isinstance(difficulty, str):
        difficulty = difficulty.lower().strip()

    return difficulty_weights.get(difficulty, 1)


def _sort_tasks_by_priority(tasks):
    """
    Sort tasks by calculated priority, highest first.
    """
    return sorted(
        tasks,
        key=lambda task: (
            task.get("priority", 0),
            task.get("time_required", task.get("weight", 1)),
        ),
        reverse=True,
    )


def _allocate_tasks(tasks, days, daily_hours, user_preference):
    """
    Allocate highest-priority tasks into dates without exceeding daily hours.
    """
    schedule = {day: [] for day in days}
    daily_hours = _to_float(daily_hours, 0)

    if not tasks or not days or daily_hours <= 0:
        return schedule

    ordered_tasks = _sort_tasks_by_priority(tasks)
    if user_preference == "focus":
        ordered_tasks = _order_tasks_for_focus(ordered_tasks)

    day_index = 0
    used_workload = 0.0

    while ordered_tasks and day_index < len(days):
        current_day = days[day_index]
        task = _select_task_for_day(
            ordered_tasks,
            daily_hours,
            used_workload,
            schedule[current_day],
            user_preference,
        )

        if task is None:
            day_index += 1
            used_workload = 0.0
            continue

        scheduled_task = _public_task_fields(task)
        schedule[current_day].append(scheduled_task)
        used_workload += task["weight"]
        ordered_tasks.remove(task)

    return schedule


def _balance_subjects(schedule, user_preference):
    """
    Keep balanced-mode days ordered by priority.
    """
    if user_preference != "balanced":
        return schedule

    balanced_schedule = {}
    for day, tasks in schedule.items():
        balanced_schedule[day] = _sort_tasks_by_priority(tasks)

    return balanced_schedule


def _order_tasks_for_focus(tasks):
    """
    Order tasks by subject weakness, then priority, for focused sessions.
    """
    grouped_tasks = _group_tasks_by_subject(tasks)
    subject_priorities = {}

    for subject, subject_tasks in grouped_tasks.items():
        subject_priorities[subject] = sum(
            task.get("priority", 0) for task in subject_tasks
        )

    subjects_by_priority = sorted(
        subject_priorities,
        key=subject_priorities.get,
        reverse=True,
    )

    ordered_tasks = []
    for subject in subjects_by_priority:
        ordered_tasks.extend(_sort_tasks_by_priority(grouped_tasks[subject]))

    return ordered_tasks


def _group_tasks_by_subject(tasks):
    """
    Group tasks by subject and keep high-priority topics first.
    """
    grouped_tasks = {}

    for task in tasks:
        subject = task.get("subject", "")
        grouped_tasks.setdefault(subject, []).append(task)

    for subject in grouped_tasks:
        grouped_tasks[subject] = _sort_tasks_by_priority(grouped_tasks[subject])

    return grouped_tasks


def _select_task_for_day(
    tasks,
    daily_hours,
    used_workload,
    current_day_tasks,
    user_preference,
):
    """
    Pick the highest-priority task that fits in the remaining day capacity.
    """
    remaining_capacity = daily_hours - used_workload
    if remaining_capacity <= 0:
        return None

    fitting_tasks = [
        task for task in tasks if task.get("weight", 1) <= remaining_capacity
    ]
    if not fitting_tasks:
        return None

    if user_preference == "balanced" and current_day_tasks:
        current_subjects = {task.get("subject", "") for task in current_day_tasks}
        alternate_subject_tasks = [
            task
            for task in fitting_tasks
            if task.get("subject", "") not in current_subjects
        ]
        if alternate_subject_tasks:
            best_task = _sort_tasks_by_priority(fitting_tasks)[0]
            best_alternate = _sort_tasks_by_priority(alternate_subject_tasks)[0]
            if best_alternate.get("priority", 0) >= best_task.get("priority", 0) - 0.05:
                return best_alternate

    return _sort_tasks_by_priority(fitting_tasks)[0]


def _public_task_fields(task):
    """
    Strip internal-only fields while preserving adaptive planning data.
    """
    fields = {
        "subject",
        "topic",
        "time_required",
        "weight",
        "normalized_time",
        "priority",
        "priority_boost",
        "actual_time_taken",
    }

    return {key: task[key] for key in fields if key in task}


def _get_subject_performance(subject_performance, subject):
    """
    Return subject performance score on a 0-100 scale.
    """
    if not subject_performance:
        return DEFAULT_SUBJECT_PERFORMANCE

    return _clamp(
        _to_float(subject_performance.get(subject), DEFAULT_SUBJECT_PERFORMANCE),
        0.0,
        100.0,
    )


def _to_float(value, default):
    """
    Convert values to float with a fallback.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _clamp(value, minimum, maximum):
    """
    Clamp numeric values to a closed range.
    """
    return max(min(value, maximum), minimum)
