from fastapi import FastAPI
from nicegui import ui, app as nicegui_app

# Import DB and FocusPage Controller
from database import init_db, db
from frontend.page import FocusPage

# Create FastAPI app
fastapi_app = FastAPI()

# Initialize Database on FastAPI startup
@fastapi_app.on_event("startup")
async def startup_db():
    if not db.is_connected():
        await db.connect()
    await init_db()

@fastapi_app.on_event("shutdown")
async def shutdown_db():
    if db.is_connected():
        await db.disconnect()

# --- CUSTOM CSS & SCRIPTS ---
HEAD_HTML = """
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
body {
    font-family: 'Outfit', sans-serif !important;
    background-color: #FAF9F6;
    color: #1B4332;
    transition: background-color 0.3s ease, color 0.3s ease;
}
.dark body {
    background-color: #0E1612 !important;
    color: #E8F5E9 !important;
}
/* Tab Styling overrides */
.q-tab__label {
    font-weight: 600 !important;
    letter-spacing: 0.05em;
    font-size: 0.875rem;
}
.q-tabs {
    border-bottom: 1px solid rgba(45, 106, 79, 0.15);
}
.dark .q-tabs {
    border-bottom: 1px solid rgba(232, 245, 233, 0.1);
}
.q-tab--active {
    color: #2D6A4F !important;
}
.dark .q-tab--active {
    color: #52B788 !important;
}
/* Cards styling */
.forest-card {
    background-color: #ffffff;
    border: 1px solid rgba(45, 106, 79, 0.15);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.dark .forest-card {
    background-color: #16251D;
    border: 1px solid rgba(82, 183, 136, 0.15);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}
.forest-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(45, 106, 79, 0.08);
}
.dark .forest-card:hover {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
}
/* Custom slider */
.q-slider__track {
    color: #95D5B2 !important;
}
.q-slider__thumb {
    color: #2D6A4F !important;
}
</style>
<script>
// Ambient Audio Manager
window.playAmbient = function(url) {
    let audio = document.getElementById('ambient-audio');
    if (!audio) {
        audio = document.createElement('audio');
        audio.id = 'ambient-audio';
        audio.loop = true;
        document.body.appendChild(audio);
    }
    if (!url) {
        audio.pause();
        return;
    }
    if (audio.src !== url) {
        audio.src = url;
    }
    audio.play().catch(e => console.log("Ambient autoplay delayed: ", e));
};

window.pauseAmbient = function() {
    let audio = document.getElementById('ambient-audio');
    if (audio) {
        audio.pause();
    }
};

window.setTimerState = function(running, mode) {
    window.isTimerRunning = running;
    window.timerMode = mode;
};

// Blocker Overlay interaction detector (Honor System)
document.addEventListener('click', (e) => {
    if (window.isTimerRunning && window.timerMode === 'Focus') {
        if (e.target.closest('#end-session-btn') || e.target.closest('.q-dialog') || e.target.closest('.q-menu') || e.target.closest('.q-notifications')) {
            return;
        }
        const overlay = document.getElementById('blocker-overlay');
        if (overlay) {
            overlay.style.display = 'flex';
        }
    }
});

document.addEventListener('mousemove', (e) => {
    if (window.isTimerRunning && window.timerMode === 'Focus') {
        if (e.target.closest('#end-session-btn') || e.target.closest('.q-dialog') || e.target.closest('.q-notifications')) {
            return;
        }
        const overlay = document.getElementById('blocker-overlay');
        if (overlay && overlay.style.display === 'none') {
            overlay.style.display = 'flex';
        }
    }
});
</script>
"""

# --- HELPER FUNCTIONS ---
def get_timer_svg(percentage: float, formatted_time: str, mode: str) -> str:
    r = 90
    circ = 2 * 3.14159265 * r
    offset = circ - (percentage / 100.0) * circ
    
    stroke_color = "#2D6A4F" if mode == "Focus" else "#E07A5F"
    text_color = "currentColor"
    
    svg = f"""
    <svg width="220" height="220" viewBox="0 0 220 220" class="mx-auto select-none">
        <circle cx="110" cy="110" r="{r}" stroke="rgba(149, 213, 178, 0.2)" stroke-width="10" fill="transparent" />
        <circle cx="110" cy="110" r="{r}" stroke="{stroke_color}" stroke-width="10" fill="transparent"
                stroke-dasharray="{circ}" stroke-dashoffset="{offset}" stroke-linecap="round"
                transform="rotate(-90 110 110)" style="transition: stroke-dashoffset 0.5s ease, stroke 0.3s ease;" />
        <text x="110" y="105" dominant-baseline="middle" text-anchor="middle" font-size="34" font-weight="800" fill="{text_color}" style="font-family: 'Outfit', sans-serif;">
            {formatted_time}
        </text>
        <text x="110" y="140" dominant-baseline="middle" text-anchor="middle" font-size="12" font-weight="700" fill="{stroke_color}" style="letter-spacing: 0.15em; font-family: 'Outfit', sans-serif;">
            {mode.upper()}
        </text>
    </svg>
    """
    return svg

@ui.page('/')
async def main_page():
    # Instantiate client FocusPage context and render layouts
    page = FocusPage(get_timer_svg, HEAD_HTML)
    await page.build()

# Integrated FastAPI endpoint mapping NiceGUI
ui.run_with(fastapi_app, title="Focus Management System")
