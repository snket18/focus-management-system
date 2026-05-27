from fastapi import FastAPI
from nicegui import ui, app as nicegui_app

# Import DB and FocusPage Controller
from database import init_db, db
from frontend.page import FocusPage
from frontend.login_view import LoginView

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
HEAD_HTML = r"""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
body, div, span, p, a, input, button, select, textarea, label, .q-tab__label, .q-field__label, .q-field__native, .q-placeholder {
    font-family: 'Outfit', sans-serif !important;
}
body {
    background-color: #FAF9F6;
    color: #1B4332;
    transition: background-color 0.3s ease, color 0.3s ease;
}
.dark body, body.body--dark {
    background-color: #0A0E0C !important; /* Extremely polished dark charcoal/green forest background */
    color: #E8F5E9 !important;
}
.bg-cream-earth {
    background-color: #FAF9F6 !important;
}
.dark .bg-cream-earth, .body--dark .bg-cream-earth {
    background-color: #0A0E0C !important;
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
.dark .q-tabs, .body--dark .q-tabs {
    border-bottom: 1px solid rgba(232, 245, 233, 0.1);
}
.q-tab--active {
    color: #2D6A4F !important;
}
.dark .q-tab--active, .body--dark .q-tab--active {
    color: #52B788 !important;
}
.dark .q-tab, .body--dark .q-tab {
    color: #88A090 !important;
}
/* Cards styling */
.forest-card {
    background-color: #ffffff;
    border: 1px solid rgba(45, 106, 79, 0.15);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.dark .forest-card, .body--dark .forest-card {
    background-color: #121A16 !important; /* Premium dark forest card background */
    border: 1px solid rgba(82, 183, 136, 0.15) !important;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
}
.forest-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(45, 106, 79, 0.08);
}
.dark .forest-card:hover, .body--dark .forest-card:hover {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.6);
}
.dark .q-card.cursor-pointer:hover, .body--dark .q-card.cursor-pointer:hover {
    background-color: #1A2620 !important; /* Hover state for calendar cells */
}
/* Custom slider */
.q-slider__track {
    color: #95D5B2 !important;
}
.q-slider__thumb {
    color: #2D6A4F !important;
}
/* Global Quasar dark mode styles */
.dark .q-card, .body--dark .q-card {
    background-color: #121A16 !important;
    color: #E8F5E9 !important;
    border-color: rgba(82, 183, 136, 0.15) !important;
}
.dark .q-dialog .q-card, .body--dark .q-dialog .q-card {
    background-color: #121A16 !important;
    color: #E8F5E9 !important;
    border: 1px solid rgba(82, 183, 136, 0.25) !important;
}
/* Style all form fields inside dark mode */
.dark .q-field__control, .body--dark .q-field__control {
    background-color: rgba(20, 28, 24, 0.8) !important; /* Professional dark input fill */
    border-radius: 8px !important;
    color: #E8F5E9 !important;
}
.dark .q-field__label, .body--dark .q-field__label {
    color: #88A090 !important; /* Soft green-gray labels */
}
.dark .q-field__native, .body--dark .q-field__native,
.dark .q-field__input, .body--dark .q-field__input,
.dark .q-field__prefix, .body--dark .q-field__prefix,
.dark .q-field__suffix, .body--dark .q-field__suffix,
.dark .q-placeholder, .body--dark .q-placeholder,
.dark .q-field__marginal, .body--dark .q-field__marginal {
    color: #E8F5E9 !important;
}
.dark .q-field__control:before, .body--dark .q-field__control:before {
    border-color: rgba(82, 183, 136, 0.25) !important;
}
.dark .q-field__control:hover:before, .body--dark .q-field__control:hover:before {
    border-color: #52B788 !important;
}
.dark .q-field__control:after, .body--dark .q-field__control:after {
    border-color: #52B788 !important;
}
.dark .q-field__messages, .body--dark .q-field__messages {
    color: rgba(232, 245, 233, 0.6) !important;
}
/* Menus and drop-down selectors */
.dark .q-menu, .body--dark .q-menu,
.dark .q-item, .body--dark .q-item {
    background-color: #121A16 !important;
    color: #E8F5E9 !important;
    border: 1px solid rgba(82, 183, 136, 0.15) !important;
}
.dark .q-item--active, .body--dark .q-item--active,
.dark .q-item.q-manual-focusable--focused, .body--dark .q-item.q-manual-focusable--focused {
    background-color: #2D6A4F !important;
    color: #ffffff !important;
}
.dark .q-item:hover, .body--dark .q-item:hover {
    background-color: rgba(82, 183, 136, 0.1) !important;
}
/* Switches and Checkboxes */
.dark .q-toggle__label, .body--dark .q-toggle__label,
.dark .q-checkbox__label, .body--dark .q-checkbox__label {
    color: #E8F5E9 !important;
}
/* Calendar styling details in dark mode */
.dark .border-emerald-500, .body--dark .border-emerald-500 {
    border-color: #52B788 !important;
}
.dark .bg-emerald-950\/20, .body--dark .bg-emerald-950\/20 {
    background-color: rgba(82, 183, 136, 0.15) !important;
}
/* Checklist task items in calendar dialog */
.dark .text-stone-700, .body--dark .text-stone-700 {
    color: #E8F5E9 !important;
}
.dark .text-stone-500, .body--dark .text-stone-500 {
    color: #88A090 !important;
}
.dark .text-stone-400, .body--dark .text-stone-400 {
    color: #6E8576 !important;
}
.dark .bg-stone-50\/50, .body--dark .bg-stone-50\/50 {
    background-color: rgba(20, 28, 24, 0.6) !important;
}
.dark .border-stone-100, .body--dark .border-stone-100 {
    border-color: rgba(82, 183, 136, 0.15) !important;
}
/* Sleek custom scrollbars */
.dark ::-webkit-scrollbar, .body--dark ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
.dark ::-webkit-scrollbar-track, .body--dark ::-webkit-scrollbar-track {
    background: #0A0E0C;
}
.dark ::-webkit-scrollbar-thumb, .body--dark ::-webkit-scrollbar-thumb {
    background: #1C2B22;
    border-radius: 4px;
}
.dark ::-webkit-scrollbar-thumb:hover, .body--dark ::-webkit-scrollbar-thumb:hover {
    background: #2D4A39;
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
    user_id = nicegui_app.storage.user.get('user_id')
    if not user_id:
        return ui.navigate.to('/login')
    # Instantiate client FocusPage context and render layouts
    page = FocusPage(get_timer_svg, HEAD_HTML, user_id=user_id)
    await page.build()

@ui.page('/login')
async def login_page():
    # If already logged in, redirect to home
    if nicegui_app.storage.user.get('user_id'):
        return ui.navigate.to('/')
    view = LoginView(HEAD_HTML)
    view.build()

# Integrated FastAPI endpoint mapping NiceGUI with user session support
ui.run_with(fastapi_app, title="Focus Management System", storage_secret="a_super_secret_focus_system_key_12345")
