import random
import datetime
from database import db

MOTIVATIONAL_QUOTES = [
    "The best way to predict the future is to create it. - Abraham Lincoln",
    "Focus is a matter of deciding what things you're not going to do. - John Carmack",
    "It is during our darkest moments that we must focus to see the light. - Aristotle",
    "Your focus determines your reality. - Qui-Gon Jinn",
    "Work hard in silence, let your success be your noise. - Frank Ocean",
    "Keep your eyes on the stars, and your feet on the ground. - Theodore Roosevelt",
    "Only the paranoid survive. - Andy Grove",
    "Deep work is the superpower of the 21st century. - Cal Newport",
    "Do not wait for unique circumstances to do good; try to use ordinary situations. - Charles Spurjeet"
]

AMBIENT_AUDIO_URLS = {
    "None": "",
    "Rain": "https://www.soundjay.com/nature/sounds/rain-07.mp3",
    "Cafe": "https://www.soundjay.com/misc/sounds/bar-ambience-1.mp3",
    "White Noise": "https://www.soundjay.com/misc/sounds/wind-weather-01.mp3"
}

NOTIFICATION_SOUND_URL = "https://www.soundjay.com/buttons/sounds/button-10.mp3"

class TimerState:
    def __init__(self):
        self.time_remaining = 1500  # 25 minutes default in seconds
        self.total_duration = 1500
        self.is_running = False
        self.current_mode = "Focus"  # "Focus" or "Break"
        self.active_preset = "Study Session"  # "Deep Work", "Study Session", "Quick Focus", "Custom"
        
        # Audio states
        self.selected_ambient_sound = "None"
        self.sound_enabled = True
        
        # Blocking state
        self.blocked_sites_list = []
        
        # Quote Popup
        self.show_quote_popup = False
        self.current_quote = ""

    async def load_from_db(self):
        """Asynchronously load settings and blocked sites from SQLite via Prisma."""
        if not db.is_connected():
            await db.connect()
            
        try:
            settings = await db.setting.find_first()
            if settings:
                self.sound_enabled = settings.sound_enabled
                # Apply preset defaults
                if self.active_preset == "Study Session":
                    self.set_preset(settings.focus_preset)
                elif self.active_preset == "Deep Work":
                    self.set_preset(50)
                elif self.active_preset == "Quick Focus":
                    self.set_preset(15)
            
            sites = await db.blockedsite.find_many()
            self.blocked_sites_list = [site.domain for site in sites]
        except Exception as e:
            print(f"Error loading configuration in TimerState: {e}")

    def set_preset(self, minutes: int, label: str = "Custom"):
        self.active_preset = label
        self.total_duration = minutes * 60
        self.time_remaining = self.total_duration
        self.is_running = False

    def toggle_timer(self):
        self.is_running = not self.is_running
        return self.is_running

    def reset_timer(self):
        self.is_running = False
        self.time_remaining = self.total_duration

    @property
    def time_formatted(self) -> str:
        mins, secs = divmod(self.time_remaining, 60)
        return f"{mins:02d}:{secs:02d}"

    @property
    def progress_percentage(self) -> float:
        if self.total_duration <= 0:
            return 100.0
        elapsed = self.total_duration - self.time_remaining
        return (elapsed / self.total_duration) * 100.0

    async def tick(self) -> dict:
        """Ticks the timer down by 1 second. Performs async DB tasks when expiring."""
        if not self.is_running:
            return {"status": "idle"}

        if self.time_remaining > 0:
            self.time_remaining -= 1
            return {"status": "ticking", "time_remaining": self.time_remaining}
        else:
            # Timer expired!
            self.is_running = False
            prev_mode = self.current_mode
            
            session_saved = False
            duration_mins = self.total_duration // 60
            
            if prev_mode == "Focus":
                try:
                    await db.focussession.create(
                        data={
                            "duration_minutes": duration_mins,
                            "template_used": self.active_preset,
                            "completed": True
                        }
                    )
                    session_saved = True
                except Exception as e:
                    print(f"Error saving session via Prisma: {e}")

                # Transition to break
                try:
                    settings = await db.setting.find_first()
                    break_mins = settings.short_break if settings and duration_mins < 50 else (settings.long_break if settings else 15)
                except:
                    break_mins = 5
                
                self.current_mode = "Break"
                self.total_duration = break_mins * 60
                self.time_remaining = self.total_duration
                self.active_preset = "Break"
            else:
                # Transition back to focus
                try:
                    settings = await db.setting.find_first()
                    focus_mins = settings.focus_preset if settings else 25
                except:
                    focus_mins = 25
                
                self.current_mode = "Focus"
                self.total_duration = focus_mins * 60
                self.time_remaining = self.total_duration
                self.active_preset = "Study Session"

            # Set a random motivational quote
            self.current_quote = random.choice(MOTIVATIONAL_QUOTES)
            self.show_quote_popup = True

            return {
                "status": "expired",
                "prev_mode": prev_mode,
                "session_saved": session_saved,
                "quote": self.current_quote,
                "notification_sound": NOTIFICATION_SOUND_URL if self.sound_enabled else None
            }
