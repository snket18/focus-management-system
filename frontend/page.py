import datetime
import calendar
import json
from nicegui import ui, app

from state import TimerState, AMBIENT_AUDIO_URLS, NOTIFICATION_SOUND_URL
from backend import task_controller, session_controller, settings_controller
from frontend import dialogs, timer_view, calendar_view, analytics_view, settings_view

class FocusPage:
    def __init__(self, get_timer_svg_func, HEAD_HTML, user_id: int):
        self.get_timer_svg = get_timer_svg_func
        self.HEAD_HTML = HEAD_HTML
        self.user_id = user_id
        self.state = TimerState(user_id=user_id)
        
        # State indicators
        self.current_calendar_date = {
            "year": datetime.date.today().year,
            "month": datetime.date.today().month
        }
        
        # UI Component references (instantiated on build)
        self.dark_mode = None
        self.streak_label = None
        self.daily_goal_label = None
        self.timer_svg_el = None
        self.ambient_select = None
        self.target_goal_val = None
        self.focused_completed_val = None
        self.goal_status_badge = None
        
        # Calendar & Dashboard references
        self.month_title = None
        self.calendar_container = None
        self.today_tasks_container = None
        
        # Analytics references
        self.today_focus_h = None
        self.week_focus_h = None
        self.month_focus_h = None
        self.streak_focus_days = None
        self.chart1 = None
        self.chart2 = None
        self.chart3 = None
        
        # Settings & Blocklist references
        self.focus_len_in = None
        self.short_break_in = None
        self.long_break_in = None
        self.daily_goal_in = None
        self.sound_enabled_switch = None
        self.block_domain_in = None
        self.blocked_domains_list_container = None
        
        # Dialog references
        self.quote_dialog = None
        self.quote_text_label = None
        self.confirm_cancel_dialog = None
        self.day_dialog = None

    async def build(self):
        """Asynchronously load configurations, construct UI components, and attach events."""
        # Add head HTML
        ui.add_head_html(self.HEAD_HTML)
        
        # Load local state from DB
        await self.state.load_from_db()
        
        # Initialize dark mode theme tracker
        self.dark_mode = ui.dark_mode()
        
        # 1. Dialog components
        dialogs.build_quote_dialog(self)
        dialogs.build_confirm_cancel_dialog(self)
        self.day_dialog = ui.dialog()  # Empty shell to be populated dynamically
        
        # 2. Blocklist confirmation and overlay logic
        with ui.element('div').classes('fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-stone-950/95 text-stone-100 p-8').style('display: none;').props('id="blocker-overlay"'):
            ui.label("🚫 Blocked Site!").classes('text-3xl font-black text-red-500 tracking-wider')
            ui.label("You are currently in Focus Mode. Distracting sites are honor-blocked.").classes('text-sm text-stone-400 mt-2 text-center max-w-md')
            
            with ui.row().classes('items-center my-8 bg-stone-900 px-6 py-4 rounded-2xl border border-stone-800'):
                ui.label("⏰ Remaining:").classes('text-xl font-semibold text-stone-300')
                overlay_countdown_label = ui.label("25:00").classes('text-3xl font-bold text-emerald-400 font-mono')
                overlay_countdown_label.bind_text_from(self.state, 'time_formatted')
                
            ui.button("End Session Early", on_click=self.confirm_cancel_dialog.open).props('id="end-session-btn"').classes('bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-8 rounded-lg shadow-lg transition')

        # 3. Header layout
        with ui.header().classes('bg-emerald-800 text-white p-4 flex justify-between items-center z-50'):
            with ui.row().classes('items-center gap-2'):
                ui.label("🌲").classes('text-2xl')
                ui.label("Focus Management System").classes('text-xl font-extrabold tracking-tight')
            
            with ui.row().classes('items-center gap-4'):
                with ui.row().classes('items-center gap-2 bg-emerald-900/50 px-3 py-1 rounded-full text-xs font-semibold'):
                    self.streak_label = ui.label("🔥 Streak: 0d")
                    ui.label("|")
                    self.daily_goal_label = ui.label("Daily Target: 0.0 hrs")
                
                ui.button(
                    icon='dark_mode', 
                    on_click=lambda: self.toggle_dark_theme()
                ).props('flat round color=white')

                ui.button(
                    icon='logout', 
                    on_click=self.logout
                ).props('flat round color=white tooltip="Logout"')

        # 4. Tab selection structure
        with ui.tabs().classes('w-full') as main_tabs:
            timer_tab = ui.tab('Timer', icon='timer')
            calendar_tab = ui.tab('Calendar & Tasks', icon='calendar_month')
            analytics_tab = ui.tab('Analytics', icon='bar_chart')
            settings_tab = ui.tab('Settings', icon='settings')

        with ui.tab_panels(main_tabs, value=timer_tab).classes('w-full bg-cream-earth p-4'):
            with ui.tab_panel(timer_tab):
                timer_view.build_timer_tab(self, self.get_timer_svg)
                
            with ui.tab_panel(calendar_tab):
                calendar_view.build_calendar_tab(self)
                
            with ui.tab_panel(analytics_tab):
                analytics_view.build_analytics_tab(self)
                
            with ui.tab_panel(settings_tab):
                settings_view.build_settings_tab(self)

        # 5. Connect initial client layout data bindings
        await self.load_app_settings_to_inputs()
        await self.refresh_calendar()
        await self.refresh_today_tasks()
        await self.refresh_analytics_tab()
        await self.refresh_blocked_domains_list()
        
        # 6. Begin background timer ticking callback loop
        ui.timer(1.0, self.timer_tick_loop)

    # --- APP EVENT HANDLERS ---
    def logout(self):
        app.storage.user.clear()
        ui.navigate.to('/login')

    async def toggle_dark_theme(self):
        self.dark_mode.toggle()
        try:
            settings = await settings_controller.get_app_settings(self.user_id)
            if settings:
                await settings_controller.update_dark_mode(settings.id, self.dark_mode.value)
        except Exception as e:
            print(f"Error saving theme: {e}")
        ui.notify(f"Dark mode {'enabled' if self.dark_mode.value else 'disabled'}", type="info")

    async def cancel_session_early(self):
        self.state.reset_timer()
        ui.run_javascript('pauseAmbient();')
        ui.run_javascript('setTimerState(false, "Focus");')
        ui.run_javascript('document.getElementById("blocker-overlay").style.display = "none";')
        self.confirm_cancel_dialog.close()
        ui.notify("Focus session abandoned.", type="warning")
        self.timer_svg_el.content = self.get_timer_svg(self.state.progress_percentage, self.state.time_formatted, self.state.current_mode)
        await self.refresh_analytics_tab()

    def change_ambient_audio(self, sound_name: str):
        self.state.selected_ambient_sound = sound_name
        if self.state.is_running and self.state.current_mode == "Focus" and sound_name != "None":
            ui.run_javascript(f'playAmbient("{AMBIENT_AUDIO_URLS[sound_name]}");')
        else:
            ui.run_javascript('pauseAmbient();')

    def apply_preset(self, minutes: int, name: str):
        self.state.set_preset(minutes, name)
        self.timer_svg_el.content = self.get_timer_svg(self.state.progress_percentage, self.state.time_formatted, self.state.current_mode)
        ui.run_javascript('pauseAmbient();')
        ui.run_javascript('setTimerState(false, "Focus");')
        ui.notify(f"Loaded {name} preset ({minutes}m)", type="info")

    def trigger_start(self):
        if not self.state.is_running:
            self.state.toggle_timer()
            ui.notify("Timer started! Keep focusing.", type="info")
            if self.state.current_mode == "Focus" and self.state.selected_ambient_sound != "None":
                ui.run_javascript(f'playAmbient("{AMBIENT_AUDIO_URLS[self.state.selected_ambient_sound]}");')
            ui.run_javascript(f'setTimerState(true, "{self.state.current_mode}");')
        self.timer_svg_el.content = self.get_timer_svg(self.state.progress_percentage, self.state.time_formatted, self.state.current_mode)

    def trigger_pause(self):
        if self.state.is_running:
            self.state.toggle_timer()
            ui.notify("Timer paused.", type="info")
            ui.run_javascript('pauseAmbient();')
            ui.run_javascript(f'setTimerState(false, "{self.state.current_mode}");')
        self.timer_svg_el.content = self.get_timer_svg(self.state.progress_percentage, self.state.time_formatted, self.state.current_mode)

    def trigger_reset(self):
        self.state.reset_timer()
        ui.notify("Timer reset.", type="info")
        ui.run_javascript('pauseAmbient();')
        ui.run_javascript(f'setTimerState(false, "{self.state.current_mode}");')
        self.timer_svg_el.content = self.get_timer_svg(self.state.progress_percentage, self.state.time_formatted, self.state.current_mode)

    async def timer_tick_loop(self):
        if not self.state.is_running:
            return
        res = await self.state.tick()
        self.timer_svg_el.content = self.get_timer_svg(self.state.progress_percentage, self.state.time_formatted, self.state.current_mode)
        
        if res["status"] == "expired":
            ui.run_javascript('pauseAmbient();')
            ui.run_javascript(f'setTimerState(false, "{self.state.current_mode}");')
            ui.run_javascript('document.getElementById("blocker-overlay").style.display = "none";')
            
            if res["notification_sound"]:
                ui.run_javascript(f'new Audio("{res["notification_sound"]}").play();')
                
            self.quote_text_label.text = res["quote"]
            self.quote_dialog.open()
            
            await self.refresh_today_tasks()
            await self.refresh_calendar()
            await self.refresh_analytics_tab()
            
            if self.state.is_running and self.state.current_mode == "Focus" and self.state.selected_ambient_sound != "None":
                ui.run_javascript(f'playAmbient("{AMBIENT_AUDIO_URLS[self.state.selected_ambient_sound]}");')

    # --- CALENDAR DRAWING AND NAV ---
    async def shift_month(self, offset: int):
        m = self.current_calendar_date["month"] + offset
        y = self.current_calendar_date["year"]
        if m < 1:
            m = 12
            y -= 1
        elif m > 12:
            m = 1
            y += 1
        self.current_calendar_date["month"] = m
        self.current_calendar_date["year"] = y
        await self.refresh_calendar()

    async def refresh_calendar(self):
        self.calendar_container.clear()
        year = self.current_calendar_date["year"]
        month = self.current_calendar_date["month"]
        
        month_name = datetime.date(year, month, 1).strftime("%B %Y")
        self.month_title.text = month_name
        
        with self.calendar_container:
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
                    
                tasks_in_month = await task_controller.get_tasks_for_date_range(self.user_id, month_start, month_end)
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
                        ).on('click', lambda _, d=day_date: self.open_day_dialog(d)):
                            
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

    # --- DASHBOARD AGENDA PANEL ---
    async def refresh_today_tasks(self):
        self.today_tasks_container.clear()
        today = datetime.date.today()
        today_start = datetime.datetime.combine(today, datetime.time.min)
        today_end = datetime.datetime.combine(today, datetime.time.max)
        
        try:
            overdue_tasks = await task_controller.get_overdue_tasks(self.user_id, today_start)
            today_tasks = await task_controller.get_tasks_for_date_range(self.user_id, today_start, today_end)
        except Exception as e:
            print(f"Error fetching dashboard tasks: {e}")
            overdue_tasks = []
            today_tasks = []
            
        if overdue_tasks:
            with self.today_tasks_container:
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
                                    ui.button(icon='arrow_forward', on_click=lambda _, t_id=task.id: self.quick_reschedule_today(t_id)).props('flat dense').classes('text-emerald-600 hover:text-emerald-700 text-xs font-bold').tooltip("Reschedule to Today")
                                    ui.checkbox(value=task.completed).on('change', lambda e, t_id=task.id: self.quick_complete_task_dashboard(t_id, e.value))
                                    
        with self.today_tasks_container:
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
                                date_in.on('change', lambda e, t_id=task.id: self.quick_reschedule_task_dashboard(t_id, e.value))
                                ui.checkbox(value=task.completed).on('change', lambda e, t_id=task.id: self.quick_complete_task_dashboard(t_id, e.value))

    async def quick_reschedule_today(self, task_id):
        try:
            today_mid = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
            await task_controller.reschedule_task(task_id, today_mid)
            ui.notify("Moved task to Today", type="info")
        except Exception as e:
            print(e)
        await self.refresh_today_tasks()
        await self.refresh_calendar()
        await self.refresh_analytics_tab()

    async def quick_complete_task_dashboard(self, task_id, val):
        try:
            await task_controller.update_task_completed(task_id, val)
            ui.notify("Task updated", type="success")
        except Exception as e:
            print(e)
        await self.refresh_today_tasks()
        await self.refresh_calendar()
        await self.refresh_analytics_tab()

    async def quick_reschedule_task_dashboard(self, task_id, date_str):
        if not date_str:
            return
        try:
            new_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            new_datetime = datetime.datetime.combine(new_date, datetime.time.min)
            await task_controller.reschedule_task(task_id, new_datetime)
            ui.notify(f"Rescheduled to {new_date}", type="info")
        except Exception as e:
            ui.notify(f"Invalid date: {e}", type="warning")
        await self.refresh_today_tasks()
        await self.refresh_calendar()
        await self.refresh_analytics_tab()

    # --- ANALYTICS CALCULATIONS AND GRAPHS ---
    async def refresh_analytics_tab(self):
        try:
            # Today Focus
            today_start = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
            sessions_today = await session_controller.get_completed_sessions_since(self.user_id, today_start)
            today_mins = sum(s.duration_minutes for s in sessions_today)
            today_hours_val = round(today_mins / 60.0, 1)
            self.today_focus_h.text = f"{today_hours_val} hrs"
            self.focused_completed_val.text = f"{today_hours_val} hrs"
            
            # Streak calculations
            all_completed_sessions = await session_controller.get_all_completed_sessions(self.user_id, order="desc")
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
            self.streak_focus_days.text = f"{streak} days"
            self.streak_label.text = f"🔥 Streak: {streak}d"
            
            # Settings bindings
            settings = await settings_controller.get_app_settings(self.user_id)
            daily_target_h = settings.daily_goal_hours if settings else 2.0
            self.daily_goal_label.text = f"Daily Target: {daily_target_h} hrs"
            self.target_goal_val.text = f"{daily_target_h} hrs"
            
            if today_hours_val >= daily_target_h:
                self.goal_status_badge.text = "Goal Reached!"
                self.goal_status_badge.classes(replace='bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300')
            else:
                self.goal_status_badge.text = "Incomplete"
                self.goal_status_badge.classes(replace='bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300')

            # Weekly Focus
            today = datetime.date.today()
            start_of_week = today - datetime.timedelta(days=today.weekday())
            start_of_week_dt = datetime.datetime.combine(start_of_week, datetime.time.min)
            sessions_week = await session_controller.get_completed_sessions_since(self.user_id, start_of_week_dt)
            week_mins = sum(s.duration_minutes for s in sessions_week)
            self.week_focus_h.text = f"{round(week_mins / 60.0, 1)} hrs"

            # Monthly Focus
            start_of_month = datetime.datetime(today.year, today.month, 1, 0, 0, 0)
            sessions_month = await session_controller.get_completed_sessions_since(self.user_id, start_of_month)
            month_mins = sum(s.duration_minutes for s in sessions_month)
            self.month_focus_h.text = f"{round(month_mins / 60.0, 1)} hrs"

            # Trailing 7 days hours
            last_7_days = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
            focus_hours_7_days = []
            for d in last_7_days:
                day_sessions = await session_controller.get_sessions_for_day(self.user_id, d)
                day_mins = sum(s.duration_minutes for s in day_sessions)
                focus_hours_7_days.append(round(day_mins / 60.0, 2))

            # Chart 1: Bar chart (last 7 days)
            self.chart1.options.clear()
            self.chart1.options.update({
                'title': {'text': 'Focus Hours (Last 7 Days)', 'left': 'center', 'textStyle': {'fontFamily': 'Outfit', 'fontSize': 14}},
                'tooltip': {'trigger': 'axis', 'formatter': '{b}: {c} hrs'},
                'xAxis': {'type': 'category', 'data': [d.strftime("%a %b %d") for d in last_7_days]},
                'yAxis': {'type': 'value', 'name': 'Hours'},
                'series': [{'data': focus_hours_7_days, 'type': 'bar', 'itemStyle': {'color': '#2D6A4F', 'borderRadius': [4, 4, 0, 0]}}],
                'backgroundColor': 'transparent'
            })
            self.chart1.update()

            # Chart 2: Task Completion rates
            completed_tasks = await task_controller.get_task_count(self.user_id, completed=True)
            incomplete_tasks = await task_controller.get_task_count(self.user_id, completed=False)
            
            self.chart2.options.clear()
            self.chart2.options.update({
                'title': {'text': 'Task Completion Rates', 'left': 'center', 'textStyle': {'fontFamily': 'Outfit', 'fontSize': 14}},
                'tooltip': {'trigger': 'item', 'formatter': '{b}: {c} ({d}%)'},
                'legend': {'bottom': '0%', 'left': 'center'},
                'series': [{
                    'type': 'pie',
                    'radius': ['35%', '65%'],
                    'center': ['50%', '55%'],
                    'avoidLabelOverlap': False,
                    'itemStyle': {'borderRadius': 6, 'borderColor': '#fff', 'borderWidth': 1},
                    'data': [
                        {'value': completed_tasks, 'name': 'Completed', 'itemStyle': {'color': '#2D6A4F'}},
                        {'value': incomplete_tasks, 'name': 'Incomplete', 'itemStyle': {'color': '#D32F2F'}}
                    ]
                }],
                'backgroundColor': 'transparent'
            })
            self.chart2.update()

            # Chart 3: Focus Session hourly density distribution
            hour_density = [0] * 24
            all_sessions_density = await session_controller.get_all_completed_sessions(self.user_id)
            for s in all_sessions_density:
                h = s.timestamp.hour
                hour_density[h] += s.duration_minutes / 60.0
            hour_density = [round(h, 2) for h in hour_density]

            self.chart3.options.clear()
            self.chart3.options.update({
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
            self.chart3.update()

        except Exception as e:
            print(f"Error compiling analytics dashboard: {e}")

    # --- CONFIGURATIONS AND UTILITIES MANAGEMENT ---
    async def load_app_settings_to_inputs(self):
        try:
            settings = await settings_controller.get_app_settings(self.user_id)
            if settings:
                self.focus_len_in.value = settings.focus_preset
                self.short_break_in.value = settings.short_break
                self.long_break_in.value = settings.long_break
                self.daily_goal_in.value = settings.daily_goal_hours
                self.sound_enabled_switch.value = settings.sound_enabled
        except Exception as e:
            print(f"Error loading settings configuration values: {e}")

    async def save_app_settings(self):
        focus_len = int(self.focus_len_in.value or 25)
        short_break = int(self.short_break_in.value or 5)
        long_break = int(self.long_break_in.value or 15)
        daily_goal = float(self.daily_goal_in.value or 2.0)
        sound_enabled = self.sound_enabled_switch.value
        
        try:
            settings = await settings_controller.get_app_settings(self.user_id)
            if settings:
                await settings_controller.save_configurations(
                    settings.id, focus_len, short_break, long_break, daily_goal, sound_enabled
                )
                
                self.state.sound_enabled = sound_enabled
                if self.state.active_preset == "Study Session":
                    self.state.set_preset(focus_len, "Study Session")
                    
                ui.notify("Configurations saved successfully!", type="positive")
                self.timer_svg_el.content = self.get_timer_svg(self.state.progress_percentage, self.state.time_formatted, self.state.current_mode)
                await self.refresh_analytics_tab()
        except Exception as e:
            ui.notify(f"Error saving configurations: {e}", type="warning")

    async def trigger_data_export(self):
        try:
            data = await settings_controller.get_export_payload(self.user_id)
            
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
                    } for s in data["settings"]
                ],
                "focus_sessions": [
                    {
                        "timestamp": s.timestamp.isoformat(),
                        "duration_minutes": s.duration_minutes,
                        "template_used": s.template_used,
                        "completed": s.completed
                    } for s in data["focus_sessions"]
                ],
                "tasks": [
                    {
                        "title": s.title,
                        "due_date": s.due_date.isoformat(),
                        "completed": s.completed,
                        "time_estimate": s.time_estimate,
                        "priority": s.priority
                    } for s in data["tasks"]
                ],
                "blocked_sites": [
                    {
                        "domain": s.domain
                    } for s in data["blocked_sites"]
                ]
            }
            
            json_bytes = json.dumps(export_payload, indent=2).encode('utf-8')
            ui.download(json_bytes, filename="focus_data_export.json")
            ui.notify("Data export compilation downloaded successfully!", type="positive")
        except Exception as e:
            ui.notify(f"Error exporting data: {e}", type="warning")

    # --- BLOCKLIST SYSTEM MANAGEMENT ---
    async def refresh_blocked_domains_list(self):
        self.blocked_domains_list_container.clear()
        try:
            domains = await settings_controller.get_blocked_sites(self.user_id)
            self.state.blocked_sites_list = [d.domain for d in domains]
            
            if not domains:
                with self.blocked_domains_list_container:
                    ui.label("No blocked domains yet. Add one above.").classes('text-stone-400 italic text-xs py-2')
            else:
                for item in domains:
                    with self.blocked_domains_list_container, ui.card().classes('w-full px-3 py-1.5 bg-stone-50 dark:bg-zinc-900/60 border border-stone-100 dark:border-stone-800 shadow-none flex flex-row items-center justify-between'):
                        ui.label(item.domain).classes('text-xs font-semibold text-stone-700 dark:text-stone-300')
                        ui.button(icon='delete', on_click=lambda _, d_id=item.id: self.remove_blocked_domain(d_id)).props('flat dense').classes('text-red-500 hover:text-red-700')
        except Exception as e:
            print(f"Error compiling blocklist domains: {e}")

    async def append_blocked_domain(self):
        domain = self.block_domain_in.value
        if not domain:
            ui.notify("Please specify a valid domain.", type="warning")
            return
        domain = domain.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
        
        try:
            exists = await settings_controller.check_blocked_site_exists(self.user_id, domain)
            if exists:
                ui.notify("Domain already exists on blocklist.", type="warning")
                return
                
            await settings_controller.add_blocked_site(self.user_id, domain)
            ui.notify(f"Added {domain} to blocklist.", type="success")
            self.block_domain_in.value = ""
            await self.refresh_blocked_domains_list()
        except Exception as e:
            ui.notify(f"Error adding domain: {e}", type="warning")

    async def remove_blocked_domain(self, domain_id: int):
        try:
            await settings_controller.remove_blocked_site(domain_id)
            ui.notify("Removed domain from blocklist.", type="info")
            await self.refresh_blocked_domains_list()
        except Exception as e:
            ui.notify(f"Error deleting domain: {e}", type="warning")

    def open_day_dialog(self, date_obj):
        dialogs.build_day_dialog(self, date_obj)
