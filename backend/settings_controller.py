from database import db

async def get_app_settings():
    """Retrieve the application settings."""
    return await db.setting.find_first()

async def update_dark_mode(settings_id: int, dark_mode: bool):
    """Save the dark mode theme preference."""
    return await db.setting.update(
        where={"id": settings_id},
        data={"dark_mode": dark_mode}
    )

async def save_configurations(settings_id: int, focus_preset: int, short_break: int, long_break: int, daily_goal_hours: float, sound_enabled: bool):
    """Update focus preset and timing configurations in the database."""
    return await db.setting.update(
        where={"id": settings_id},
        data={
            "focus_preset": focus_preset,
            "short_break": short_break,
            "long_break": long_break,
            "daily_goal_hours": daily_goal_hours,
            "sound_enabled": sound_enabled
        }
    )

async def get_blocked_sites():
    """Retrieve all blocked site records from the database."""
    return await db.blockedsite.find_many()

async def check_blocked_site_exists(domain: str):
    """Check if a site already exists on the blocklist."""
    return await db.blockedsite.find_unique(where={"domain": domain})

async def add_blocked_site(domain: str):
    """Add a new domain to the blocklist."""
    return await db.blockedsite.create(data={"domain": domain})

async def remove_blocked_site(site_id: int):
    """Remove a domain from the blocklist by ID."""
    return await db.blockedsite.delete(where={"id": site_id})

async def get_export_payload():
    """Retrieve all database tables for JSON export."""
    db_settings = await db.setting.find_many()
    db_sessions = await db.focussession.find_many()
    db_tasks = await db.task.find_many()
    db_blocked = await db.blockedsite.find_many()
    
    return {
        "settings": db_settings,
        "focus_sessions": db_sessions,
        "tasks": db_tasks,
        "blocked_sites": db_blocked
    }
