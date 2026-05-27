from database import db

async def get_app_settings(user_id: int):
    """Retrieve the application settings for a specific user. Create if not exists."""
    settings = await db.setting.find_unique(where={"userId": user_id})
    if not settings:
        settings = await db.setting.create(
            data={
                "userId": user_id,
                "focus_preset": 25,
                "short_break": 5,
                "long_break": 15,
                "daily_goal_hours": 2.0,
                "dark_mode": False,
                "sound_enabled": True
            }
        )
    return settings

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

async def get_blocked_sites(user_id: int):
    """Retrieve all blocked site records from the database for a user."""
    return await db.blockedsite.find_many(where={"userId": user_id})

async def check_blocked_site_exists(user_id: int, domain: str):
    """Check if a site already exists on the blocklist for a user."""
    return await db.blockedsite.find_unique(
        where={
            "userId_domain": {
                "userId": user_id,
                "domain": domain
            }
        }
    )

async def add_blocked_site(user_id: int, domain: str):
    """Add a new domain to the blocklist for a user."""
    return await db.blockedsite.create(
        data={
            "domain": domain,
            "userId": user_id
        }
    )

async def remove_blocked_site(site_id: int):
    """Remove a domain from the blocklist by ID."""
    return await db.blockedsite.delete(where={"id": site_id})

async def get_export_payload(user_id: int):
    """Retrieve all database tables for JSON export for a user."""
    db_settings = await db.setting.find_many(where={"userId": user_id})
    db_sessions = await db.focussession.find_many(where={"userId": user_id})
    db_tasks = await db.task.find_many(where={"userId": user_id})
    db_blocked = await db.blockedsite.find_many(where={"userId": user_id})
    
    return {
        "settings": db_settings,
        "focus_sessions": db_sessions,
        "tasks": db_tasks,
        "blocked_sites": db_blocked
    }
