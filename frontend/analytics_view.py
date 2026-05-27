from nicegui import ui

def build_analytics_tab(page):
    """Build the layout for the Analytics Tab."""
    with ui.row().classes('w-full justify-center gap-4 my-2 wrap'):
        # Aggregated metrics cards
        with ui.card().classes('w-44 p-4 rounded-xl forest-card items-center text-center shadow-none'):
            ui.label("Focused Today").classes('text-xs text-stone-400 font-bold uppercase tracking-wider')
            page.today_focus_h = ui.label("0.0 hrs").classes('text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1')
            
        with ui.card().classes('w-44 p-4 rounded-xl forest-card items-center text-center shadow-none'):
            ui.label("Focused This Week").classes('text-xs text-stone-400 font-bold uppercase tracking-wider')
            page.week_focus_h = ui.label("0.0 hrs").classes('text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1')
            
        with ui.card().classes('w-44 p-4 rounded-xl forest-card items-center text-center shadow-none'):
            ui.label("Focused This Month").classes('text-xs text-stone-400 font-bold uppercase tracking-wider')
            page.month_focus_h = ui.label("0.0 hrs").classes('text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1')
            
        with ui.card().classes('w-44 p-4 rounded-xl forest-card items-center text-center shadow-none'):
            ui.label("Active Streak").classes('text-xs text-stone-400 font-bold uppercase tracking-wider')
            page.streak_focus_days = ui.label("0 days").classes('text-2xl font-black text-orange-600 dark:text-orange-400 mt-1')

    # Interactive charts panels
    with ui.row().classes('w-full justify-center gap-6 mt-6 wrap'):
        with ui.card().classes('w-full md:w-[48%] p-4 rounded-xl forest-card shadow-none h-96'):
            page.chart1 = ui.echart(options={}).classes('w-full h-full')
            
        with ui.card().classes('w-full md:w-[48%] p-4 rounded-xl forest-card shadow-none h-96'):
            page.chart2 = ui.echart(options={}).classes('w-full h-full')
            
        with ui.card().classes('w-full md:w-full p-4 rounded-xl forest-card shadow-none h-96 mt-4'):
            page.chart3 = ui.echart(options={}).classes('w-full h-full')
