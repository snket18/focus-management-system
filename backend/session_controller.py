import datetime
from database import db

async def create_focus_session(duration_minutes: int, template_used: str, completed: bool = True):
    """Save a completed or abandoned focus session to the database."""
    return await db.focussession.create(
        data={
            "duration_minutes": duration_minutes,
            "template_used": template_used,
            "completed": completed
        }
    )

async def get_completed_sessions_since(since_datetime: datetime.datetime):
    """Retrieve completed sessions since a specific datetime."""
    return await db.focussession.find_many(
        where={
            "timestamp": {
                "gte": since_datetime
            },
            "completed": True
        }
    )

async def get_all_completed_sessions(order: str = "desc"):
    """Retrieve all completed focus sessions sorted by date."""
    return await db.focussession.find_many(
        where={"completed": True},
        order={"timestamp": order}
    )

async def get_sessions_for_day(day: datetime.date):
    """Retrieve all completed sessions for a specific day."""
    start_time = datetime.datetime.combine(day, datetime.time.min)
    end_time = datetime.datetime.combine(day, datetime.time.max)
    return await db.focussession.find_many(
        where={
            "timestamp": {
                "gte": start_time,
                "lte": end_time
            },
            "completed": True
        }
    )
