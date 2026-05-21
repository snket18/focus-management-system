from prisma import Prisma

db = Prisma()

async def init_db():
    """Ensure that default settings exist in the database."""
    connected_here = False
    if not db.is_connected():
        await db.connect()
        connected_here = True
        
    try:
        settings_row = await db.setting.find_first()
        if not settings_row:
            await db.setting.create(
                data={
                    "id": 1,
                    "focus_preset": 25,
                    "short_break": 5,
                    "long_break": 15,
                    "daily_goal_hours": 2.0,
                    "dark_mode": False,
                    "sound_enabled": True
                }
            )
    except Exception as e:
        print(f"Error seeding database default configurations: {e}")
    finally:
        if connected_here:
            await db.disconnect()
