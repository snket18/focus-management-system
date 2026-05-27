import datetime
from nicegui import ui
from backend import task_controller

def build_quote_dialog(page):
    """Build the motivational quote popup dialog."""
    page.quote_dialog = ui.dialog()
    with page.quote_dialog, ui.card().classes('p-8 rounded-2xl bg-white dark:bg-zinc-800 text-center max-w-md border border-emerald-500/20'):
        ui.label("🌲 Focus Streak Complete!").classes('text-2xl font-black text-emerald-600 dark:text-emerald-400')
        page.quote_text_label = ui.label("").classes('text-base italic text-stone-600 dark:text-stone-300 my-5')
        ui.button("Close & Continue", on_click=page.quote_dialog.close).classes('bg-emerald-600 text-white font-bold w-full py-2.5 rounded-lg')

def build_confirm_cancel_dialog(page):
    """Build the honor system blocker cancel confirmation dialog."""
    page.confirm_cancel_dialog = ui.dialog()
    with page.confirm_cancel_dialog, ui.card().classes('p-6 rounded-xl bg-white dark:bg-zinc-800 text-center max-w-sm border border-red-500/20'):
        ui.label("Abandon Session?").classes('text-xl font-bold text-red-600')
        ui.label("Ending this session early will lose your focus progress. Are you sure you want to stop?").classes('text-sm text-stone-500 dark:text-stone-400 my-4')
        with ui.row().classes('justify-center gap-4 w-full'):
            ui.button("Keep Focusing", on_click=page.confirm_cancel_dialog.close).classes('bg-emerald-600 text-white px-4 py-2 rounded-lg font-semibold')
            ui.button("Yes, Quit", on_click=lambda: page.cancel_session_early()).classes('bg-red-600 text-white px-4 py-2 rounded-lg font-semibold')

def build_day_dialog(page, date_obj):
    """Build and display the dialog containing the checklist and form for a specific day."""
    page.day_dialog.clear()
    with page.day_dialog, ui.card().classes('w-[500px] max-w-full p-6 bg-white dark:bg-zinc-800 rounded-2xl'):
        # Dialog header
        with ui.row().classes('justify-between items-center w-full mb-4'):
            ui.label(f"Tasks for {date_obj.strftime('%A, %b %d, %Y')}").classes('text-lg font-bold text-stone-800 dark:text-stone-100')
            ui.icon('close').classes('cursor-pointer text-stone-400 hover:text-stone-600').on('click', page.day_dialog.close)
            
        # Task list container
        task_list_el = ui.column().classes('w-full gap-3 max-h-[300px] overflow-y-auto mb-4 pr-1')
        
        async def rebuild_task_list():
            task_list_el.clear()
            start_of_day = datetime.datetime.combine(date_obj, datetime.time.min)
            end_of_day = datetime.datetime.combine(date_obj, datetime.time.max)
            try:
                tasks = await task_controller.get_tasks_for_date_range(start_of_day, end_of_day)
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
                await task_controller.update_task_completed(task_id, val)
            except Exception as e:
                print(e)
            await rebuild_task_list()
            await page.refresh_calendar()
            await page.refresh_today_tasks()
            await page.refresh_analytics_tab()
            
        async def delete_task_dialog(task_id):
            try:
                await task_controller.delete_task(task_id)
            except Exception as e:
                print(e)
            await rebuild_task_list()
            await page.refresh_calendar()
            await page.refresh_today_tasks()
            await page.refresh_analytics_tab()
            
        async def reschedule_task_dialog(task_id, new_date):
            try:
                new_datetime = datetime.datetime.combine(new_date, datetime.time.min)
                await task_controller.reschedule_task(task_id, new_datetime)
                ui.notify(f"Rescheduled task to {new_date}", type="info")
            except Exception as e:
                print(e)
            await rebuild_task_list()
            await page.refresh_calendar()
            await page.refresh_today_tasks()
            await page.refresh_analytics_tab()
            
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
                await task_controller.create_task(title, due_datetime, priority, estimate)
                ui.notify("Task added successfully!", type="positive")
            except Exception as e:
                ui.notify(f"Error adding task: {e}", type="warning")
                
            dialog_task_title.value = ""
            await rebuild_task_list()
            await page.refresh_calendar()
            await page.refresh_today_tasks()
            await page.refresh_analytics_tab()
            
        ui.button("Add Task", on_click=add_task_submit_dialog).classes('bg-emerald-600 hover:bg-emerald-700 text-white w-full py-2.5 rounded-lg mt-3 font-semibold')
        
        # Async trigger for rebuilding dialog
        ui.timer(0.1, rebuild_task_list, once=True)
        page.day_dialog.open()
