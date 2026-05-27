import datetime
from database import db

async def get_tasks_for_date_range(start_date: datetime.datetime, end_date: datetime.datetime):
    """Retrieve all tasks due within a specific datetime range."""
    return await db.task.find_many(
        where={
            "due_date": {
                "gte": start_date,
                "lte": end_date
            }
        }
    )

async def get_overdue_tasks(today_start: datetime.datetime):
    """Retrieve all incomplete tasks due before today."""
    return await db.task.find_many(
        where={
            "due_date": {
                "lt": today_start
            },
            "completed": False
        },
        order={"due_date": "desc"}
    )

async def create_task(title: str, due_date: datetime.datetime, priority: str = "Medium", time_estimate: int = 25):
    """Create a new task in the database."""
    return await db.task.create(
        data={
            "title": title,
            "due_date": due_date,
            "completed": False,
            "time_estimate": time_estimate,
            "priority": priority
        }
    )

async def delete_task(task_id: int):
    """Delete a task by its ID."""
    return await db.task.delete(where={"id": task_id})

async def update_task_completed(task_id: int, completed: bool):
    """Update the completion status of a task."""
    return await db.task.update(
        where={"id": task_id},
        data={"completed": completed}
    )

async def reschedule_task(task_id: int, new_datetime: datetime.datetime):
    """Reschedule a task to a new due date."""
    return await db.task.update(
        where={"id": task_id},
        data={"due_date": new_datetime}
    )

async def get_task_count(completed: bool):
    """Count tasks based on completion status."""
    return await db.task.count(where={"completed": completed})
