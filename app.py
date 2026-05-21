import calendar
import datetime
import json
from fastapi import FastAPI
from nicegui import ui, app as nicegui_app

# Import DB and State Controller
from database import init_db, db
from state import TimerState, AMBIENT_AUDIO_URLS, NOTIFICATION_SOUND_URL

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
ui.add_head_html("""
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
""")

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
    # Instantiate page-local state
    state = TimerState()
    await state.load_from_db()
    
    current_calendar_date = {
        "year": datetime.date.today().year,
        "month": datetime.date.today().month
    }
    
    # Theme configuration
    dark_mode = ui.dark_mode()
    
    # App Header
    with ui.header().classes('bg-emerald-800 text-white p-4 flex justify-between items-center z-50'):
        with ui.row().classes('items-center gap-2'):
            ui.label("🌲").classes('text-2xl')
            ui.label("Focus Management System").classes('text-xl font-extrabold tracking-tight')
        
        with ui.row().classes('items-center gap-4'):
            with ui.row().classes('items-center gap-2 bg-emerald-900/50 px-3 py-1 rounded-full text-xs font-semibold'):
                streak_label = ui.label("🔥 Streak: 0d")
                ui.label("|")
                daily_goal_label = ui.label("Daily Target: 0.0 hrs")

            ui.button(
                icon='dark_mode',
                on_click=lambda: toggle_dark_theme()
            ).props('flat round color=white')

    async def toggle_dark_theme():
        dark_mode.toggle()
        try:
            settings = await db.setting.find_first()
            if settings:
                await db.setting.update(
                    where={"id": settings.id},
                    data={"dark_mode": dark_mode.value}
                )
        except Exception as e:
            print(f"Error saving theme: {e}")
        ui.notify(f"Dark mode {'enabled' if dark_mode.value else 'disabled'}", type="info")

    # --- MOTIVATIONAL QUOTE POPUP ---
    quote_dialog = ui.dialog()
    with quote_dialog, ui.card().classes('p-8 rounded-2xl bg-white dark:bg-zinc-800 text-center max-w-md border border-emerald-500/20'):
        ui.label("🌲 Focus Streak Complete!").classes('text-2xl font-black text-emerald-600 dark:text-emerald-400')
        quote_text_label = ui.label("").classes('text-base italic text-stone-600 dark:text-stone-300 my-5')
        ui.button("Close & Continue", on_click=quote_dialog.close).classes('bg-emerald-600 text-white font-bold w-full py-2.5 rounded-lg')

    # --- HONOR SYSTEM BLOCKER CONFIRMATION DIALOG ---
    confirm_cancel_dialog = ui.dialog()
    with confirm_cancel_dialog, ui.card().classes('p-6 rounded-xl bg-white dark:bg-zinc-800 text-center max-w-sm border border-red-500/20'):
        ui.label("Abandon Session?").classes('text-xl font-bold text-red-600')
        ui.label("Ending this session early will lose your focus progress. Are you sure you want to stop?").classes('text-sm text-stone-500 dark:text-stone-400 my-4')
        with ui.row().classes('justify-center gap-4 w-full'):
            ui.button("Keep Focusing", on_click=confirm_cancel_dialog.close).classes('bg-emerald-600 text-white px-4 py-2 rounded-lg font-semibold')
            ui.button("Yes, Quit", on_click=lambda: cancel_session_early()).classes('bg-red-600 text-white px-4 py-2 rounded-lg font-semibold')

    async def cancel_session_early():
        state.reset_timer()
        ui.run_javascript('pauseAmbient();')
        ui.run_javascript('setTimerState(false, "Focus");')
        ui.run_javascript('document.getElementById("blocker-overlay").style.display = "none";')
        confirm_cancel_dialog.close()
        ui.notify("Focus session abandoned.", type="warning")
        timer_svg_el.content = get_timer_svg(state.progress_percentage, state.time_formatted, state.current_mode)
        await refresh_analytics_tab()

    # --- HONOR SYSTEM BLOCKER OVERLAY CONTAINER ---
    with ui.element('div').classes('fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-stone-950/95 text-stone-100 p-8').style('display: none;').props('id="blocker-overlay"') as blocker_overlay:
        ui.label("🚫 Blocked Site!").classes('text-3xl font-black text-red-500 tracking-wider')
        ui.label("You are currently in Focus Mode. Distracting sites are honor-blocked.").classes('text-sm text-stone-400 mt-2 text-center max-w-md')
        
        with ui.row().classes('items-center my-8 bg-stone-900 px-6 py-4 rounded-2xl border border-stone-800'):
            ui.label("⏰ Remaining:").classes('text-xl font-semibold text-stone-300')
            overlay_countdown_label = ui.label("25:00").classes('text-3xl font-bold text-emerald-400 font-mono')
            overlay_countdown_label.bind_text_from(state, 'time_formatted')

        ui.button("End Session Early", on_click=confirm_cancel_dialog.open).props('id="end-session-btn"').classes('bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-8 rounded-lg shadow-lg transition')

    # --- TAB CONTROL LAYOUT ---
    with ui.tabs().classes('w-full') as main_tabs:
        timer_tab = ui.tab('Timer', icon='timer')
        calendar_tab = ui.tab('Calendar & Tasks', icon='calendar_month')
        analytics_tab = ui.tab('Analytics', icon='bar_chart')
        settings_tab = ui.tab('Settings', icon='settings')

    # Tab Panels
    with ui.tab_panels(main_tabs, value=timer_tab).classes('w-full bg-cream-earth p-4'):
        
        # ------------------ TIMER TAB ------------------
        with ui.tab_panel(timer_tab):
            with ui.row().classes('w-full justify-center gap-6 wrap'):
                
                # Left Card: Timer Displays
                with ui.card().classes('w-[350px] p-6 rounded-2xl forest-card items-center justify-center'):
                    ui.label("Timer Countdown").classes('text-lg font-bold text-stone-700 dark:text-stone-200 mb-2')
                    
                    timer_svg_el = ui.html(get_timer_svg(state.progress_percentage, state.time_formatted, state.current_mode)).classes('my-4')
                    
                    with ui.row().classes('justify-center gap-4 my-2'):
                        start_btn = ui.button(icon='play_arrow', on_click=lambda: trigger_start()).props('round size=lg').classes('bg-emerald-600 hover:bg-emerald-700 text-white')
                        pause_btn = ui.button(icon='pause', on_click=lambda: trigger_pause()).props('round size=lg').classes('bg-amber-600 hover:bg-amber-700 text-white')
                        reset_btn = ui.button(icon='refresh', on_click=lambda: trigger_reset()).props('round size=lg').classes('bg-stone-500 hover:bg-stone-600 text-white')
                    
                    ui.label("Ambient Background Loop").classes('text-xs font-semibold text-stone-400 mt-6 mb-1 uppercase tracking-wider')
                    ambient_select = ui.select(
                        ["None", "Rain", "Cafe", "White Noise"],
                        value=state.selected_ambient_sound,
                        on_change=lambda e: change_ambient_audio(e.value)
                    ).classes('w-full')

                # Right Card: Presets and Targets
                with ui.card().classes('w-[350px] p-6 rounded-2xl forest-card'):
                    ui.label("Timer Presets").classes('text-lg font-bold text-stone-700 dark:text-stone-200 mb-2')
                    
                    with ui.column().classes('w-full gap-3 mt-2'):
                        ui.button("🌲 Deep Work (50m Focus)", on_click=lambda: apply_preset(50, "Deep Work")).classes('w-full py-3 bg-emerald-700 text-white rounded-xl text-left justify-start capitalize')
                        ui.button("📚 Study Session (25m Focus)", on_click=lambda: apply_preset(25, "Study Session")).classes('w-full py-3 bg-emerald-600 text-white rounded-xl text-left justify-start capitalize')
                        ui.button("⚡ Quick Focus (15m Focus)", on_click=lambda: apply_preset(15, "Quick Focus")).classes('w-full py-3 bg-emerald-500 text-white rounded-xl text-left justify-start capitalize')
                    
                    ui.separator().classes('my-4')
                    ui.label("Today's Target Metrics").classes('text-xs font-bold text-stone-400 uppercase tracking-wider mb-2')
                    
                    with ui.row().classes('w-full justify-between items-center py-2 border-b border-stone-100 dark:border-stone-800'):
                        ui.label("Daily Target:").classes('text-stone-500 dark:text-stone-400 font-semibold')
                        target_goal_val = ui.label("2.0 hrs").classes('font-bold')
                        
                    with ui.row().classes('w-full justify-between items-center py-2 border-b border-stone-100 dark:border-stone-800'):
                        ui.label("Focused Completed:").classes('text-stone-500 dark:text-stone-400 font-semibold')
                        focused_completed_val = ui.label("0.0 hrs").classes('font-bold text-emerald-600 dark:text-emerald-400')
                        
                    with ui.row().classes('w-full justify-between items-center py-2'):
                        ui.label("Completion Status:").classes('text-stone-500 dark:text-stone-400 font-semibold')
                        goal_status_badge = ui.label("Incomplete").classes('px-2.5 py-0.5 rounded text-xs font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300')

        # ------------------ CALENDAR & TASKS TAB ------------------
        with ui.tab_panel(calendar_tab):
            with ui.row().classes('w-full justify-between items-center mb-4'):
                with ui.row().classes('items-center gap-4'):
                    ui.button(icon='chevron_left', on_click=lambda: shift_month(-1)).props('flat round color=emerald-600')
                    month_title = ui.label("May 2026").classes('text-xl font-bold text-stone-800 dark:text-stone-100')
                    ui.button(icon='chevron_right', on_click=lambda: shift_month(1)).props('flat round color=emerald-600')
                
                ui.button("Add New Task", icon='add', on_click=lambda: open_day_dialog(datetime.date.today())).classes('bg-emerald-600 text-white font-semibold')

            with ui.row().classes('w-full justify-center gap-6 wrap items-start'):
                # Left Grid calendar
                with ui.card().classes('w-full md:w-[650px] p-6 rounded-2xl forest-card shadow-none'):
                    calendar_container = ui.grid(columns=7).classes('w-full gap-2 mt-2')
                
                # Right dashboard tasks
                with ui.card().classes('w-full md:w-[380px] p-6 rounded-2xl forest-card shadow-none'):
                    ui.label("Tasks Dashboard").classes('text-lg font-bold text-stone-700 dark:text-stone-200 mb-2')
                    today_tasks_container = ui.column().classes('w-full gap-3')

        # ------------------ ANALYTICS TAB ------------------
        with ui.tab_panel(analytics_tab):
            with ui.row().classes('w-full justify-center gap-4 my-2 wrap'):
                # Aggregated metrics cards
                with ui.card().classes('w-44 p-4 rounded-xl forest-card items-center text-center shadow-none'):
                    ui.label("Focused Today").classes('text-xs text-stone-400 font-bold uppercase tracking-wider')
                    today_focus_h = ui.label("0.0 hrs").classes('text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1')
                with ui.card().classes('w-44 p-4 rounded-xl forest-card items-center text-center shadow-none'):
                    ui.label("Focused This Week").classes('text-xs text-stone-400 font-bold uppercase tracking-wider')
                    week_focus_h = ui.label("0.0 hrs").classes('text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1')
                with ui.card().classes('w-44 p-4 rounded-xl forest-card items-center text-center shadow-none'):
                    ui.label("Focused This Month").classes('text-xs text-stone-400 font-bold uppercase tracking-wider')
                    month_focus_h = ui.label("0.0 hrs").classes('text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1')
                with ui.card().classes('w-44 p-4 rounded-xl forest-card items-center text-center shadow-none'):
                    ui.label("Active Streak").classes('text-xs text-stone-400 font-bold uppercase tracking-wider')
                    streak_focus_days = ui.label("0 days").classes('text-2xl font-black text-orange-600 dark:text-orange-400 mt-1')

            # Interactive charts panels
            with ui.row().classes('w-full justify-center gap-6 mt-6 wrap'):
                with ui.card().classes('w-full md:w-[48%] p-4 rounded-xl forest-card shadow-none h-96'):
                    chart1 = ui.echart(options={}).classes('w-full h-full')
                with ui.card().classes('w-full md:w-[48%] p-4 rounded-xl forest-card shadow-none h-96'):
                    chart2 = ui.echart(options={}).classes('w-full h-full')
                with ui.card().classes('w-full md:w-full p-4 rounded-xl forest-card shadow-none h-96 mt-4'):
                    chart3 = ui.echart(options={}).classes('w-full h-full')

        # ------------------ SETTINGS TAB ------------------
        with ui.tab_panel(settings_tab):
            with ui.row().classes('w-full justify-center gap-6 wrap items-start'):
                # Settings configuration inputs
                with ui.card().classes('w-full md:w-[500px] p-6 rounded-2xl forest-card shadow-none'):
                    ui.label("Configuration Preferences").classes('text-lg font-bold text-stone-700 dark:text-stone-200 mb-4')
                    
                    focus_len_in = ui.number(value=25, label="Focus Session Duration (minutes)", min=1).classes('w-full mb-3')
                    short_break_in = ui.number(value=5, label="Short Break Duration (minutes)", min=1).classes('w-full mb-3')
                    long_break_in = ui.number(value=15, label="Long Break Duration (minutes)", min=1).classes('w-full mb-3')
                    daily_goal_in = ui.number(value=2.0, label="Daily Goal Target (hours)", min=0.1, step=0.1).classes('w-full mb-3')
                    sound_enabled_switch = ui.switch("Enable Notification Audio Pings").classes('mb-4')
                    
                    ui.button("Save Core Configurations", on_click=lambda: save_app_settings()).classes('bg-emerald-600 hover:bg-emerald-700 text-white w-full py-2.5 rounded-lg font-semibold')
                    
                    ui.separator().classes('my-6')
                    ui.label("System Utilities").classes('text-xs font-bold text-stone-400 uppercase tracking-wider mb-2')
                    ui.button("Export Database to JSON File", icon='download', on_click=lambda: trigger_data_export()).classes('bg-stone-600 hover:bg-stone-700 text-white w-full py-2.5 rounded-lg font-semibold')

                # Blocklist panels
                with ui.card().classes('w-full md:w-[450px] p-6 rounded-2xl forest-card shadow-none'):
                    ui.label("Honor Blocklist Websites").classes('text-lg font-bold text-stone-700 dark:text-stone-200 mb-1')
                    ui.label("Add distracting domains to block the app interface during focus sessions.").classes('text-xs text-stone-400 mb-4')
                    
                    with ui.row().classes('w-full items-center gap-2 mb-4'):
                        block_domain_in = ui.input(placeholder="e.g. facebook.com").classes('grow')
                        ui.button("Add Site", icon='add', on_click=lambda: append_blocked_domain()).classes('bg-red-600 hover:bg-red-700 text-white font-semibold')
                    
                    ui.label("Blocked Domains").classes('text-xs font-bold text-stone-500 dark:text-stone-400 uppercase tracking-wider mb-2')
                    blocked_domains_list_container = ui.column().classes('w-full gap-2')

    # --- DIALOG TO MANAGE DAY TASKS ---
    day_dialog = ui.dialog()

    def open_day_dialog(date_obj):
        day_dialog.clear()
        with day_dialog, ui.card().classes('w-[500px] max-w-full p-6 bg-white dark:bg-zinc-800 rounded-2xl'):
            # Dialog header
            with ui.row().classes('justify-between items-center w-full mb-4'):
                ui.label(f"Tasks for {date_obj.strftime('%A, %b %d, %Y')}").classes('text-lg font-bold text-stone-800 dark:text-stone-100')
                ui.icon('close').classes('cursor-pointer text-stone-400 hover:text-stone-600').on('click', day_dialog.close)
                
            # Task list container
            task_list_el = ui.column().classes('w-full gap-3 max-h-[300px] overflow-y-auto mb-4 pr-1')
            
            async def rebuild_task_list():
                task_list_el.clear()
                start_of_day = datetime.datetime.combine(date_obj, datetime.time.min)
                end_of_day = datetime.datetime.combine(date_obj, datetime.time.max)
                try:
                    tasks = await db.task.find_many(
                        where={
                            "due_date": {
                                "gte": start_of_day,
                                "lte": end_of_day
                            }
                        }
                    )
                    if not tasks:
                        with task_list_el:
                            ui.label("No tasks scheduled for this day.").classes('text-stone-400 italic text-sm py-4 text-center w-full')
                    else:
                        for task in tasks:
                            badge_color = "bg-green-100 text-green-800 dark:bg-green-950/40 dark:text-green-300"
                            if task.priority == "Medium":
                                badge_color = "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300"
                            elif task.priority == "High":
                                badge_color = "bg-red-100 text-red-800 dark:bg-red-950/40 dark:text-red-300"
                                
                            with task_list_el, ui.card().classes('w-full p-3 shadow-none border border-stone-100 dark:border-stone-700 bg-stone-50/50 dark:bg-zinc-900/50 flex flex-col gap-2'):
                                with ui.row().classes('justify-between items-center w-full'):
                                    with ui.row().classes('items-center gap-2'):
                                        ui.checkbox(value=task.completed).on('change', lambda e, t_id=task.id: toggle_task_completed_dialog(t_id, e.value))
                                        ui.label(task.title).classes(f'text-sm font-semibold {"line-through text-stone-400" if task.completed else "text-stone-700 dark:text-stone-200"}')
                                    ui.button(icon='delete', on_click=lambda _, t_id=task.id: delete_task_dialog(t_id)).props('flat dense').classes('text-red-500 hover:text-red-700 shrink-0')
                                
                                with ui.row().classes('justify-between items-center w-full text-xs text-stone-500 dark:text-stone-400'):
                                    with ui.row().classes('items-center gap-2'):
                                        ui.label(task.priority).classes(f'px-2 py-0.5 rounded text-[10px] font-bold {badge_color}')
                                        ui.label(f"⏱️ {task.time_estimate}m").classes('text-stone-400')
                                    with ui.row().classes('items-center gap-1'):
                                        ui.label("Move:").classes('text-[10px] text-stone-400')
                                        if date_obj != datetime.date.today():
                                            ui.button("Today", on_click=lambda _, t_id=task.id: reschedule_task_dialog(t_id, datetime.date.today())).props('flat dense').classes('text-emerald-600 hover:text-emerald-700 text-[10px] p-0 min-h-0 uppercase font-bold')
                                        
                                        date_in = ui.input(value=task.due_date.strftime("%Y-%m-%d")).props('type=date dense').classes('w-28 text-xs border-0')
                                        date_in.on('change', lambda e, t_id=task.id: reschedule_task_dialog_by_string(t_id, e.value))
                except Exception as e:
                    print(f"Error compiling task list inside modal: {e}")
                    
            async def toggle_task_completed_dialog(task_id, val):
                try:
                    await db.task.update(
                        where={"id": task_id},
                        data={"completed": val}
                    )
                except Exception as e:
                    print(e)
                await rebuild_task_list()
                await refresh_calendar()
                await refresh_today_tasks()
                await refresh_analytics_tab()
                
            async def delete_task_dialog(task_id):
                try:
                    await db.task.delete(where={"id": task_id})
                except Exception as e:
                    print(e)
                await rebuild_task_list()
                await refresh_calendar()
                await refresh_today_tasks()
                await refresh_analytics_tab()
                
            async def reschedule_task_dialog(task_id, new_date):
                try:
                    new_datetime = datetime.datetime.combine(new_date, datetime.time.min)
                    await db.task.update(
                        where={"id": task_id},
                        data={"due_date": new_datetime}
                    )
                    ui.notify(f"Rescheduled task to {new_date}", type="info")
                except Exception as e:
                    print(e)
                await rebuild_task_list()
                await refresh_calendar()
                await refresh_today_tasks()
                await refresh_analytics_tab()
                
            async def reschedule_task_dialog_by_string(task_id, date_str):
                if not date_str:
                    return
                try:
                    new_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                    await reschedule_task_dialog(task_id, new_date)
                except Exception as e:
                    ui.notify(f"Invalid date format: {e}", type="warning")

            # Append task form
            ui.separator().classes('my-4')
            ui.label("Add New Task").classes('text-xs font-bold text-stone-500 uppercase tracking-wider mb-2')
            
            dialog_task_title = ui.input(label="Task Title").classes('w-full')
            with ui.row().classes('w-full justify-between items-center gap-2 mt-2'):
                dialog_priority = ui.select(["Low", "Medium", "High"], value="Medium", label="Priority").classes('w-28')
                dialog_estimate = ui.number(value=25, label="Estimate (m)", min=1).classes('w-24')
                
            async def add_task_submit_dialog():
                title = dialog_task_title.value
                if not title:
                    ui.notify("Task title is required.", type="warning")
                    return
                priority = dialog_priority.value
                estimate = int(dialog_estimate.value or 25)
                
                due_datetime = datetime.datetime.combine(date_obj, datetime.time.min)
                try:
                    await db.task.create(
                        data={
                            "title": title,
                            "due_date": due_datetime,
                            "completed": False,
                            "time_estimate": estimate,
                            "priority": priority
                        }
                    )
                    ui.notify("Task added successfully!", type="positive")
                except Exception as e:
                    ui.notify(f"Error adding task: {e}", type="warning")
                    
                dialog_task_title.value = ""
                await rebuild_task_list()
                await refresh_calendar()
                await refresh_today_tasks()
                await refresh_analytics_tab()
                
            ui.button("Add Task", on_click=add_task_submit_dialog).classes('bg-emerald-600 hover:bg-emerald-700 text-white w-full py-2.5 rounded-lg mt-3 font-semibold')
            
            # Async trigger for rebuilding dialog
            ui.timer(0.1, lambda: rebuild_task_list(), once=True)
            day_dialog.open()

    # --- AUDIO & TIMER CONTROLLERS ---
    def change_ambient_audio(sound_name: str):
        state.selected_ambient_sound = sound_name
        if state.is_running and state.current_mode == "Focus" and sound_name != "None":
            ui.run_javascript(f'playAmbient("{AMBIENT_AUDIO_URLS[sound_name]}");')
        else:
            ui.run_javascript('pauseAmbient();')

    def apply_preset(minutes: int, name: str):
        state.set_preset(minutes, name)
        timer_svg_el.content = get_timer_svg(state.progress_percentage, state.time_formatted, state.current_mode)
        ui.run_javascript('pauseAmbient();')
        ui.run_javascript('setTimerState(false, "Focus");')
        ui.notify(f"Loaded {name} preset ({minutes}m)", type="info")

    def trigger_start():
        if not state.is_running:
            state.toggle_timer()
            ui.notify("Timer started! Keep focusing.", type="info")
            if state.current_mode == "Focus" and state.selected_ambient_sound != "None":
                ui.run_javascript(f'playAmbient("{AMBIENT_AUDIO_URLS[state.selected_ambient_sound]}");')
            ui.run_javascript(f'setTimerState(true, "{state.current_mode}");')
        timer_svg_el.content = get_timer_svg(state.progress_percentage, state.time_formatted, state.current_mode)

    def trigger_pause():
        if state.is_running:
            state.toggle_timer()
            ui.notify("Timer paused.", type="info")
            ui.run_javascript('pauseAmbient();')
            ui.run_javascript(f'setTimerState(false, "{state.current_mode}");')
        timer_svg_el.content = get_timer_svg(state.progress_percentage, state.time_formatted, state.current_mode)

    def trigger_reset():
        state.reset_timer()
        ui.notify("Timer reset.", type="info")
        ui.run_javascript('pauseAmbient();')
        ui.run_javascript(f'setTimerState(false, "{state.current_mode}");')
        timer_svg_el.content = get_timer_svg(state.progress_percentage, state.time_formatted, state.current_mode)

    # --- TICKING LOOP ---
    async def timer_tick_loop():
        if not state.is_running:
            return
        res = await state.tick()
        timer_svg_el.content = get_timer_svg(state.progress_percentage, state.time_formatted, state.current_mode)
        
        if res["status"] == "expired":
            ui.run_javascript('pauseAmbient();')
            ui.run_javascript(f'setTimerState(false, "{state.current_mode}");')
            ui.run_javascript('document.getElementById("blocker-overlay").style.display = "none";')
            
            if res["notification_sound"]:
                ui.run_javascript(f'new Audio("{res["notification_sound"]}").play();')
                
            quote_text_label.text = res["quote"]
            quote_dialog.open()
            
            await refresh_today_tasks()
            await refresh_calendar()
            await refresh_analytics_tab()
            
            if state.is_running and state.current_mode == "Focus" and state.selected_ambient_sound != "None":
                ui.run_javascript(f'playAmbient("{AMBIENT_AUDIO_URLS[state.selected_ambient_sound]}");')

    # Ticking loop callback
    ui.timer(1.0, timer_tick_loop)

    # --- CALENDAR DRAWING AND NAV ---
    async def shift_month(offset: int):
        m = current_calendar_date["month"] + offset
        y = current_calendar_date["year"]
        if m < 1:
            m = 12
            y -= 1
        elif m > 12:
            m = 1
            y += 1
        current_calendar_date["month"] = m
        current_calendar_date["year"] = y
        await refresh_calendar()

    async def refresh_calendar():
        calendar_container.clear()
        year = current_calendar_date["year"]
        month = current_calendar_date["month"]
        
        month_name = datetime.date(year, month, 1).strftime("%B %Y")
        month_title.text = month_name
        
        with calendar_container:
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for d in days:
                ui.label(d).classes('text-center font-bold text-stone-500 dark:text-stone-400 text-xs py-1 select-none')
                
            weeks = calendar.monthcalendar(year, month)
            try:
                month_start = datetime.datetime(year, month, 1, 0, 0, 0)
                if month == 12:
                    month_end = datetime.datetime(year + 1, 1, 1, 23, 59, 59) - datetime.timedelta(days=1)
                else:
                    month_end = datetime.datetime(year, month + 1, 1, 23, 59, 59) - datetime.timedelta(days=1)
                    
                tasks_in_month = await db.task.find_many(
                    where={
                        "due_date": {
                            "gte": month_start,
                            "lte": month_end
                        }
                    }
                )
            except Exception as e:
                print(f"Error fetching monthly tasks: {e}")
                tasks_in_month = []
                
            tasks_by_day = {}
            for task in tasks_in_month:
                day_num = task.due_date.day
                if day_num not in tasks_by_day:
                    tasks_by_day[day_num] = []
                tasks_by_day[day_num].append(task)
                
            for week in weeks:
                for day in week:
                    if day == 0:
                        ui.card().classes('bg-stone-100/30 dark:bg-stone-900/10 border border-stone-100/50 dark:border-stone-800/30 h-20 shadow-none')
                    else:
                        day_date = datetime.date(year, month, day)
                        is_today = (day_date == datetime.date.today())
                        day_tasks = tasks_by_day.get(day, [])
                        
                        with ui.card().classes(
                            f'h-20 p-1 cursor-pointer flex flex-col justify-between transition border shadow-none '
                            f'{"bg-emerald-50/40 border-emerald-500 dark:bg-emerald-950/20" if is_today else "bg-white dark:bg-zinc-800/80 border-stone-200 dark:border-stone-700 hover:bg-stone-100/50 dark:hover:bg-zinc-800"}'
                        ).on('click', lambda _, d=day_date: open_day_dialog(d)):
                            
                            ui.label(str(day)).classes(f'font-bold text-xs {"text-emerald-700 dark:text-emerald-400" if is_today else "text-stone-700 dark:text-stone-300"}')
                            
                            if day_tasks:
                                with ui.column().classes('gap-0.5 w-full overflow-hidden'):
                                    for task in day_tasks[:2]:
                                        color = "bg-green-500"
                                        if task.priority == "Medium":
                                            color = "bg-amber-500"
                                        elif task.priority == "High":
                                            color = "bg-red-500"
                                        
                                        text_style = "line-through text-stone-400" if task.completed else "text-stone-700 dark:text-stone-300"
                                        with ui.row().classes('items-center gap-1 w-full wrap-none overflow-hidden'):
                                            ui.element('span').classes(f'w-1.5 h-1.5 rounded-full {color} shrink-0')
                                            ui.label(task.title).classes(f'text-[9px] truncate max-w-full {text_style}')
                                    if len(day_tasks) > 2:
                                        ui.label(f"+{len(day_tasks) - 2} tasks").classes('text-[8px] text-stone-400 italic')

    # --- DASHBOARD & ANALYTICS DATA BINDINGS ---
    async def refresh_today_tasks():
        today_tasks_container.clear()
        today = datetime.date.today()
        today_start = datetime.datetime.combine(today, datetime.time.min)
        today_end = datetime.datetime.combine(today, datetime.time.max)
        
        try:
            overdue_tasks = await db.task.find_many(
                where={
                    "due_date": {
                        "lt": today_start
                    },
                    "completed": False
                },
                order={"due_date": "desc"}
            )
            
            today_tasks = await db.task.find_many(
                where={
                    "due_date": {
                        "gte": today_start,
                        "lte": today_end
                    }
                }
            )
        except Exception as e:
            print(f"Error fetching dashboard tasks: {e}")
            overdue_tasks = []
            today_tasks = []
            
        if overdue_tasks:
            with today_tasks_container:
                with ui.card().classes('w-full p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/60 rounded-xl shadow-none'):
                    with ui.row().classes('items-center gap-1.5 mb-2'):
                        ui.icon('warning', color='red-600').classes('text-base')
                        ui.label("Overdue Items").classes('text-red-700 dark:text-red-400 font-extrabold text-xs uppercase tracking-wider')
                    
                    with ui.column().classes('w-full gap-2'):
                        for task in overdue_tasks:
                            badge_color = "bg-green-100 text-green-800 dark:bg-green-950/40 dark:text-green-300"
                            if task.priority == "Medium":
                                badge_color = "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300"
                            elif task.priority == "High":
                                badge_color = "bg-red-100 text-red-800 dark:bg-red-950/40 dark:text-red-300"
                                
                            with ui.card().classes('w-full p-2 bg-white dark:bg-zinc-800 border border-red-100 dark:border-red-900/50 shadow-none flex flex-row items-center justify-between'):
                                with ui.column().classes('gap-0.5'):
                                    ui.label(task.title).classes('text-xs font-bold text-stone-800 dark:text-stone-100')
                                    with ui.row().classes('items-center gap-1.5 text-[10px]'):
                                        ui.label(task.priority).classes(f'px-1.5 py-0.5 rounded text-[8px] font-bold {badge_color}')
                                        ui.label(f"Due: {task.due_date.strftime('%b %d')}").classes('text-red-500 font-semibold')
                                
                                with ui.row().classes('items-center gap-1 shrink-0'):
                                    ui.button(icon='arrow_forward', on_click=lambda _, t_id=task.id: quick_reschedule_today(t_id)).props('flat dense').classes('text-emerald-600 hover:text-emerald-700 text-xs font-bold').tooltip("Reschedule to Today")
                                    ui.checkbox(value=task.completed).on('change', lambda e, t_id=task.id: quick_complete_task_dashboard(t_id, e.value))
                                    
        with today_tasks_container:
            ui.label("Today's Agenda").classes('font-bold text-stone-700 dark:text-stone-300 text-xs uppercase tracking-wider mt-1')
            if not today_tasks:
                ui.label("No tasks due today! 🌲").classes('text-stone-400 italic text-xs py-2 text-center w-full')
            else:
                with ui.column().classes('w-full gap-2'):
                    for task in today_tasks:
                        badge_color = "bg-green-100 text-green-800 dark:bg-green-950/40 dark:text-green-300"
                        if task.priority == "Medium":
                            badge_color = "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300"
                        elif task.priority == "High":
                            badge_color = "bg-red-100 text-red-800 dark:bg-red-950/40 dark:text-red-300"
                            
                        with ui.card().classes('w-full p-2 bg-white dark:bg-zinc-800/60 border border-stone-200 dark:border-stone-700 shadow-none flex flex-row items-center justify-between'):
                            with ui.column().classes('gap-0.5'):
                                ui.label(task.title).classes(f'text-xs font-bold {"line-through text-stone-400" if task.completed else "text-stone-800 dark:text-stone-100"}')
                                with ui.row().classes('items-center gap-1.5 text-[10px]'):
                                    ui.label(task.priority).classes(f'px-1.5 py-0.5 rounded text-[8px] font-bold {badge_color}')
                                    ui.label(f"⏱️ {task.time_estimate}m").classes('text-stone-400')
                                    
                            with ui.row().classes('items-center gap-1 shrink-0'):
                                date_in = ui.input(value=task.due_date.strftime("%Y-%m-%d")).props('type=date dense').classes('w-28 text-[10px] border-0')
                                date_in.on('change', lambda e, t_id=task.id: quick_reschedule_task_dashboard(t_id, e.value))
                                ui.checkbox(value=task.completed).on('change', lambda e, t_id=task.id: quick_complete_task_dashboard(t_id, e.value))

    async def quick_reschedule_today(task_id):
        try:
            today_mid = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
            await db.task.update(
                where={"id": task_id},
                data={"due_date": today_mid}
            )
            ui.notify("Moved task to Today", type="info")
        except Exception as e:
            print(e)
        await refresh_today_tasks()
        await refresh_calendar()
        await refresh_analytics_tab()

    async def quick_complete_task_dashboard(task_id, val):
        try:
            await db.task.update(
                where={"id": task_id},
                data={"completed": val}
            )
            ui.notify("Task updated", type="success")
        except Exception as e:
            print(e)
        await refresh_today_tasks()
        await refresh_calendar()
        await refresh_analytics_tab()

    async def quick_reschedule_task_dashboard(task_id, date_str):
        if not date_str:
            return
        try:
            new_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            new_datetime = datetime.datetime.combine(new_date, datetime.time.min)
            await db.task.update(
                where={"id": task_id},
                data={"due_date": new_datetime}
            )
            ui.notify(f"Rescheduled to {new_date}", type="info")
        except Exception as e:
            ui.notify(f"Invalid date: {e}", type="warning")
        await refresh_today_tasks()
        await refresh_calendar()
        await refresh_analytics_tab()

    # --- ANALYTICS DATA COMPILATION AND GRAPH UPDATES ---
    async def refresh_analytics_tab():
        try:
            # Today Focus
            today_start = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
            sessions_today = await db.focussession.find_many(
                where={
                    "timestamp": {
                        "gte": today_start
                    },
                    "completed": True
                }
            )
            today_mins = sum(s.duration_minutes for s in sessions_today)
            today_hours_val = round(today_mins / 60.0, 1)
            today_focus_h.text = f"{today_hours_val} hrs"
            focused_completed_val.text = f"{today_hours_val} hrs"
            
            # Streak calculations
            all_completed_sessions = await db.focussession.find_many(
                where={"completed": True},
                order={"timestamp": "desc"}
            )
            
            unique_dates = sorted(list(set(s.timestamp.date() for s in all_completed_sessions)), reverse=True)
            streak = 0
            if unique_dates:
                check_date = datetime.date.today()
                if unique_dates[0] == check_date:
                    streak = 1
                    check_date -= datetime.timedelta(days=1)
                    for d in unique_dates[1:]:
                        if d == check_date:
                            streak += 1
                            check_date -= datetime.timedelta(days=1)
                        else:
                            break
                elif unique_dates[0] == check_date - datetime.timedelta(days=1):
                    streak = 1
                    check_date -= datetime.timedelta(days=2)
                    for d in unique_dates[1:]:
                        if d == check_date:
                            streak += 1
                            check_date -= datetime.timedelta(days=1)
                        else:
                            break
            streak_focus_days.text = f"{streak} days"
            streak_label.text = f"🔥 Streak: {streak}d"
            
            # Settings bindings (daily goal, sound, etc.)
            settings = await db.setting.find_first()
            daily_target_h = settings.daily_goal_hours if settings else 2.0
            daily_goal_label.text = f"Daily Target: {daily_target_h} hrs"
            target_goal_val.text = f"{daily_target_h} hrs"
            
            if today_hours_val >= daily_target_h:
                goal_status_badge.text = "Goal Reached!"
                goal_status_badge.classes(replace='bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300')
            else:
                goal_status_badge.text = "Incomplete"
                goal_status_badge.classes(replace='bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300')

            # Weekly Focus
            today = datetime.date.today()
            start_of_week = today - datetime.timedelta(days=today.weekday())
            start_of_week_dt = datetime.datetime.combine(start_of_week, datetime.time.min)
            sessions_week = await db.focussession.find_many(
                where={
                    "timestamp": {
                        "gte": start_of_week_dt
                    },
                    "completed": True
                }
            )
            week_mins = sum(s.duration_minutes for s in sessions_week)
            week_focus_h.text = f"{round(week_mins / 60.0, 1)} hrs"

            # Monthly Focus
            start_of_month = datetime.datetime(today.year, today.month, 1, 0, 0, 0)
            sessions_month = await db.focussession.find_many(
                where={
                    "timestamp": {
                        "gte": start_of_month
                    },
                    "completed": True
                }
            )
            month_mins = sum(s.duration_minutes for s in sessions_month)
            month_focus_h.text = f"{round(month_mins / 60.0, 1)} hrs"

            # Trailing 7 days hours
            last_7_days = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
            focus_hours_7_days = []
            for d in last_7_days:
                d_start = datetime.datetime.combine(d, datetime.time.min)
                d_end = datetime.datetime.combine(d, datetime.time.max)
                day_sessions = await db.focussession.find_many(
                    where={
                        "timestamp": {
                            "gte": d_start,
                            "lte": d_end
                        },
                        "completed": True
                    }
                )
                day_mins = sum(s.duration_minutes for s in day_sessions)
                focus_hours_7_days.append(round(day_mins / 60.0, 2))

            # Chart 1: Bar chart (last 7 days)
            chart1.options.clear()
            chart1.options.update({
                'title': {'text': 'Focus Hours (Last 7 Days)', 'left': 'center', 'textStyle': {'fontFamily': 'Outfit', 'fontSize': 14}},
                'tooltip': {'trigger': 'axis', 'formatter': '{b}: {c} hrs'},
                'xAxis': {'type': 'category', 'data': [d.strftime("%a %b %d") for d in last_7_days]},
                'yAxis': {'type': 'value', 'name': 'Hours'},
                'series': [{'data': focus_hours_7_days, 'type': 'bar', 'itemStyle': {'color': '#2D6A4F', 'borderRadius': [4, 4, 0, 0]}}],
                'backgroundColor': 'transparent'
            })
            chart1.update()

            # Chart 2: Task Completion rates
            completed_tasks = await db.task.count(where={"completed": True})
            incomplete_tasks = await db.task.count(where={"completed": False})
            
            chart2.options.clear()
            chart2.options.update({
                'title': {'text': 'Task Completion Rates', 'left': 'center', 'textStyle': {'fontFamily': 'Outfit', 'fontSize': 14}},
                'tooltip': {'trigger': 'item', 'formatter': '{b}: {c} ({d}%)'},
                'legend': {'bottom': '0%', 'left': 'center'},
                'series': [{
                    'type': 'pie',
                    'radius': ['40%', '75%'],
                    'avoidLabelOverlap': False,
                    'itemStyle': {'borderRadius': 6, 'borderColor': '#fff', 'borderWidth': 1},
                    'data': [
                        {'value': completed_tasks, 'name': 'Completed', 'itemStyle': {'color': '#2D6A4F'}},
                        {'value': incomplete_tasks, 'name': 'Incomplete', 'itemStyle': {'color': '#D32F2F'}}
                    ]
                }],
                'backgroundColor': 'transparent'
            })
            chart2.update()

            # Chart 3: Focus Session hourly density distribution
            hour_density = [0] * 24
            all_sessions_density = await db.focussession.find_many(where={"completed": True})
            for s in all_sessions_density:
                h = s.timestamp.hour
                hour_density[h] += s.duration_minutes / 60.0
            hour_density = [round(h, 2) for h in hour_density]

            chart3.options.clear()
            chart3.options.update({
                'title': {'text': 'Focus Distribution Density (Hour of Day)', 'left': 'center', 'textStyle': {'fontFamily': 'Outfit', 'fontSize': 14}},
                'tooltip': {'trigger': 'axis', 'formatter': '{b}:00 : {c} hrs'},
                'xAxis': {'type': 'category', 'data': [f"{h:02d}:00" for h in range(24)]},
                'yAxis': {'type': 'value', 'name': 'Hours'},
                'series': [{
                    'data': hour_density,
                    'type': 'line',
                    'smooth': True,
                    'areaStyle': {'opacity': 0.25, 'color': '#52B788'},
                    'itemStyle': {'color': '#2D6A4F'},
                    'lineStyle': {'width': 2.5}
                }],
                'backgroundColor': 'transparent'
            })
            chart3.update()

        except Exception as e:
            print(f"Error compiling analytics dashboard: {e}")

    # --- CONFIGURATIONS AND UTILITIES MANAGEMENT ---
    async def load_app_settings_to_inputs():
        try:
            settings = await db.setting.find_first()
            if settings:
                focus_len_in.value = settings.focus_preset
                short_break_in.value = settings.short_break
                long_break_in.value = settings.long_break
                daily_goal_in.value = settings.daily_goal_hours
                sound_enabled_switch.value = settings.sound_enabled
        except Exception as e:
            print(f"Error loading settings configuration values: {e}")

    async def save_app_settings():
        focus_len = int(focus_len_in.value or 25)
        short_break = int(short_break_in.value or 5)
        long_break = int(long_break_in.value or 15)
        daily_goal = float(daily_goal_in.value or 2.0)
        sound_enabled = sound_enabled_switch.value
        
        try:
            settings = await db.setting.find_first()
            if settings:
                await db.setting.update(
                    where={"id": settings.id},
                    data={
                        "focus_preset": focus_len,
                        "short_break": short_break,
                        "long_break": long_break,
                        "daily_goal_hours": daily_goal,
                        "sound_enabled": sound_enabled
                    }
                )
                
                state.sound_enabled = sound_enabled
                if state.active_preset == "Study Session":
                    state.set_preset(focus_len, "Study Session")
                    
                ui.notify("Configurations saved successfully!", type="positive")
                timer_svg_el.content = get_timer_svg(state.progress_percentage, state.time_formatted, state.current_mode)
                await refresh_analytics_tab()
        except Exception as e:
            ui.notify(f"Error saving configurations: {e}", type="warning")

    # --- EXPORT DATA PAYLOAD COMPILER ---
    async def trigger_data_export():
        try:
            db_settings = await db.setting.find_many()
            db_sessions = await db.focussession.find_many()
            db_tasks = await db.task.find_many()
            db_blocked = await db.blockedsite.find_many()
            
            export_payload = {
                "metadata": {
                    "exported_at": datetime.datetime.now().isoformat(),
                    "system": "Focus Management System (Prisma)"
                },
                "settings": [
                    {
                        "focus_preset": s.focus_preset,
                        "short_break": s.short_break,
                        "long_break": s.long_break,
                        "daily_goal_hours": s.daily_goal_hours,
                        "dark_mode": s.dark_mode,
                        "sound_enabled": s.sound_enabled
                    } for s in db_settings
                ],
                "focus_sessions": [
                    {
                        "timestamp": s.timestamp.isoformat(),
                        "duration_minutes": s.duration_minutes,
                        "template_used": s.template_used,
                        "completed": s.completed
                    } for s in db_sessions
                ],
                "tasks": [
                    {
                        "title": s.title,
                        "due_date": s.due_date.isoformat(),
                        "completed": s.completed,
                        "time_estimate": s.time_estimate,
                        "priority": s.priority
                    } for s in db_tasks
                ],
                "blocked_sites": [
                    {
                        "domain": s.domain
                    } for s in db_blocked
                ]
            }
            
            json_bytes = json.dumps(export_payload, indent=2).encode('utf-8')
            ui.download(json_bytes, filename="focus_data_export.json")
            ui.notify("Data export compilation downloaded successfully!", type="positive")
        except Exception as e:
            ui.notify(f"Error exporting data: {e}", type="warning")

    # --- BLOCKLIST SYSTEM MANAGEMENT ---
    async def refresh_blocked_domains_list():
        blocked_domains_list_container.clear()
        try:
            domains = await db.blockedsite.find_many()
            state.blocked_sites_list = [d.domain for d in domains]
            
            if not domains:
                with blocked_domains_list_container:
                    ui.label("No blocked domains yet. Add one above.").classes('text-stone-400 italic text-xs py-2')
            else:
                for item in domains:
                    with blocked_domains_list_container, ui.card().classes('w-full px-3 py-1.5 bg-stone-50 dark:bg-zinc-900/60 border border-stone-100 dark:border-stone-800 shadow-none flex flex-row items-center justify-between'):
                        ui.label(item.domain).classes('text-xs font-semibold text-stone-700 dark:text-stone-300')
                        ui.button(icon='delete', on_click=lambda _, d_id=item.id: remove_blocked_domain(d_id)).props('flat dense').classes('text-red-500 hover:text-red-700')
        except Exception as e:
            print(f"Error compiling blocklist domains: {e}")

    async def append_blocked_domain():
        domain = block_domain_in.value
        if not domain:
            ui.notify("Please specify a valid domain.", type="warning")
            return
        domain = domain.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
        
        try:
            exists = await db.blockedsite.find_unique(where={"domain": domain})
            if exists:
                ui.notify("Domain already exists on blocklist.", type="warning")
                return
                
            await db.blockedsite.create(data={"domain": domain})
            ui.notify(f"Added {domain} to blocklist.", type="success")
            block_domain_in.value = ""
            await refresh_blocked_domains_list()
        except Exception as e:
            ui.notify(f"Error adding domain: {e}", type="warning")

    async def remove_blocked_domain(domain_id: int):
        try:
            await db.blockedsite.delete(where={"id": domain_id})
            ui.notify("Removed domain from blocklist.", type="info")
            await refresh_blocked_domains_list()
        except Exception as e:
            ui.notify(f"Error deleting domain: {e}", type="warning")

    # Connect client event updates
    await load_app_settings_to_inputs()
    await refresh_calendar()
    await refresh_today_tasks()
    await refresh_analytics_tab()
    await refresh_blocked_domains_list()

# Integrated FastAPI endpoint mapping NiceGUI
ui.run_with(fastapi_app, title="Focus Management System")
