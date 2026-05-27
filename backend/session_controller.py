import datetime
from database import db

async def create_focus_session(user_id: int, duration_minutes: int, template_used: str, completed: bool = True):
    """Save a completed or abandoned focus session to the database for a user."""
    return await db.focussession.create(
        data={
            "duration_minutes": duration_minutes,
            "template_used": template_used,
            "completed": completed,
            "userId": user_id
        }
    )

async def get_completed_sessions_since(user_id: int, since_datetime: datetime.datetime):
    """Retrieve completed sessions since a specific datetime for a user."""
    return await db.focussession.find_many(
        where={
            "userId": user_id,
            "timestamp": {
                "gte": since_datetime
            },
            "completed": True
        }
    )

async def get_all_completed_sessions(user_id: int, order: str = "desc"):
    """Retrieve all completed focus sessions sorted by date for a user."""
    return await db.focussession.find_many(
        where={
            "userId": user_id,
            "completed": True
        },
        order={"timestamp": order}
    )

async def get_sessions_for_day(user_id: int, day: datetime.date):
    """Retrieve all completed sessions for a specific day for a user."""
    start_time = datetime.datetime.combine(day, datetime.time.min)
    end_time = datetime.datetime.combine(day, datetime.time.max)
    return await db.focussession.find_many(
        where={
            "userId": user_id,
            "timestamp": {
                "gte": start_time,
                "lte": end_time
            },
            "completed": True
        }
    )
