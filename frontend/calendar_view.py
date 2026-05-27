import datetime
from nicegui import ui

def build_calendar_tab(page):
    """Build the layout for the Calendar & Tasks Tab."""
    with ui.row().classes('w-full justify-between items-center mb-4'):
        with ui.row().classes('items-center gap-4'):
            ui.button(
                icon='chevron_left', 
                on_click=lambda: page.shift_month(-1)
            ).props('flat round color=emerald-600')
            
            page.month_title = ui.label("").classes('text-xl font-bold text-stone-800 dark:text-stone-100')
            
            ui.button(
                icon='chevron_right', 
                on_click=lambda: page.shift_month(1)
            ).props('flat round color=emerald-600')
        
        ui.button(
            "Add New Task", 
            icon='add', 
            on_click=lambda: page.open_day_dialog(datetime.date.today())
        ).classes('bg-emerald-600 text-white font-semibold')

    with ui.row().classes('w-full justify-center gap-6 wrap items-start'):
        # Left Grid calendar
        with ui.card().classes('w-full md:w-[650px] p-6 rounded-2xl forest-card shadow-none'):
            page.calendar_container = ui.grid(columns=7).classes('w-full gap-2 mt-2')
        
        # Right dashboard tasks
        with ui.card().classes('w-full md:w-[380px] p-6 rounded-2xl forest-card shadow-none'):
            ui.label("Tasks Dashboard").classes('text-lg font-bold text-stone-700 dark:text-stone-200 mb-2')
            page.today_tasks_container = ui.column().classes('w-full gap-3')
