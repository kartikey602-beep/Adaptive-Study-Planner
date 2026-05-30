"""
Recommendation module for the Study Planning system.

This module uses analyzer metrics and progress data to generate simple,
rule-based study suggestions. It does not use machine learning, file I/O,
UI logic, or scheduling logic.
"""


def generate_recommendations(metrics, progress=None):
    """
    Generate study recommendations from performance metrics.

    Args:
        metrics (dict): Analyzer output containing completion rate,
                        subject performance, consistency, and delay data.
        progress (dict): Optional progress data with actual completion times.

    Returns:
        list: Recommendation messages.
    """
    recommendations = []

    _add_completion_recommendation(recommendations, metrics)
    _add_subject_recommendation(recommendations, metrics)
    _add_consistency_recommendation(recommendations, metrics)
    _add_delay_recommendation(recommendations, metrics)
    _add_time_recommendation(recommendations, metrics)

    return recommendations


def generate_revision_plan(schedule, progress):
    """
    Suggest completed tasks that should be revised.

    High-weight completed tasks are selected first because they usually
    represent difficult or important topics. If no high-weight tasks exist,
    the most recently completed tasks are suggested.
    """
    completed_tasks = progress.get("completed", [])

    high_weight_tasks = [
        task.copy()
        for task in completed_tasks
        if task.get("weight", 1) >= 2
    ]

    if high_weight_tasks:
        return _remove_duplicate_tasks(high_weight_tasks)

    recent_tasks = [task.copy() for task in completed_tasks[-3:]]
    return _remove_duplicate_tasks(recent_tasks)


def _add_completion_recommendation(recommendations, metrics):
    """
    Add recommendation based on overall completion rate.
    """
    completion_rate = metrics.get("completion_rate", 0)

    if completion_rate < 50:
        recommendations.append(
            "Your completion rate is low. Try reducing daily workload or improving focus."
        )
    elif completion_rate <= 80:
        recommendations.append(
            "You are making progress, but there is room for improvement."
        )
    else:
        recommendations.append("Great job maintaining high completion!")


def _add_subject_recommendation(recommendations, metrics):
    """
    Add recommendation based on subject-wise performance.
    """
    subject_performance = metrics.get("subject_performance", {})
    if not subject_performance:
        return

    lowest_subject = min(subject_performance, key=subject_performance.get)
    lowest_score = subject_performance[lowest_subject]

    if lowest_score < 50:
        recommendations.append(
            f"Focus more on {lowest_subject}, it needs attention."
        )
        return

    if all(score > 70 for score in subject_performance.values()):
        recommendations.append("You are performing well across all subjects.")


def _add_consistency_recommendation(recommendations, metrics):
    """
    Add recommendation based on daily study consistency.
    """
    consistency = metrics.get("consistency", 0)

    if consistency < 50:
        recommendations.append(
            "Your study consistency is low. Plan fewer tasks per day until the habit stabilizes."
        )
    elif consistency <= 80:
        recommendations.append(
            "You are somewhat consistent. Try improving daily discipline."
        )
    else:
        recommendations.append("Excellent consistency!")


def _add_delay_recommendation(recommendations, metrics):
    """
    Add recommendation based on delay level.
    """
    delay = metrics.get("delay", {})
    delay_level = delay.get("delay_level", "low")

    if delay_level == "high":
        recommendations.append(
            "You are falling behind. Consider switching to focus mode."
        )
    elif delay_level == "medium":
        recommendations.append(
            "You have some pending work. Stay consistent."
        )
    else:
        recommendations.append("You are on track.")


def _add_time_recommendation(recommendations, metrics):
    """
    Add recommendation based on estimated time versus actual time.
    """
    time_performance = metrics.get("time_performance", {})
    average_ratio = time_performance.get("average_ratio", 1)
    overrun_tasks = time_performance.get("overrun_tasks", 0)
    timed_tasks = time_performance.get("timed_tasks", 0)

    if timed_tasks >= 2 and (average_ratio > 1.2 or overrun_tasks >= 2):
        recommendations.append(
            "Tasks are taking longer than planned. Use a lighter schedule for the next rebalance."
        )


def _remove_duplicate_tasks(tasks):
    """
    Remove duplicate revision tasks while preserving order.
    """
    unique_tasks = []

    for task in tasks:
        if not _task_exists(unique_tasks, task):
            unique_tasks.append(task)

    return unique_tasks


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
    Compare tasks using the standard planner task fields.
    """
    return (
        task1.get("subject") == task2.get("subject")
        and task1.get("topic") == task2.get("topic")
    )
