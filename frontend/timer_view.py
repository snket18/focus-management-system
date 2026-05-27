from nicegui import ui

def build_timer_tab(page, get_timer_svg_func):
    """Build the layout for the Timer Tab."""
    with ui.row().classes('w-full justify-center gap-6 wrap'):
        
        # Left Card: Timer Displays
        with ui.card().classes('w-[350px] p-6 rounded-2xl forest-card items-center justify-center'):
            ui.label("Timer Countdown").classes('text-lg font-bold text-stone-700 dark:text-stone-200 mb-2')
            
            # Initial content render
            initial_svg = get_timer_svg_func(page.state.progress_percentage, page.state.time_formatted, page.state.current_mode)
            page.timer_svg_el = ui.html(initial_svg).classes('my-4')
            
            with ui.row().classes('justify-center gap-4 my-2'):
                ui.button(
                    icon='play_arrow', 
                    on_click=lambda: page.trigger_start()
                ).props('round size=lg').classes('bg-emerald-600 hover:bg-emerald-700 text-white')
                
                ui.button(
                    icon='pause', 
                    on_click=lambda: page.trigger_pause()
                ).props('round size=lg').classes('bg-amber-600 hover:bg-amber-700 text-white')
                
                ui.button(
                    icon='refresh', 
                    on_click=lambda: page.trigger_reset()
                ).props('round size=lg').classes('bg-stone-500 hover:bg-stone-600 text-white')
            
            ui.label("Ambient Background Loop").classes('text-xs font-semibold text-stone-400 mt-6 mb-1 uppercase tracking-wider')
            page.ambient_select = ui.select(
                ["None", "Rain", "Cafe", "White Noise"],
                value=page.state.selected_ambient_sound,
                on_change=lambda e: page.change_ambient_audio(e.value)
            ).classes('w-full')

        # Right Card: Presets and Targets
        with ui.card().classes('w-[350px] p-6 rounded-2xl forest-card'):
            ui.label("Timer Presets").classes('text-lg font-bold text-stone-700 dark:text-stone-200 mb-2')
            
            with ui.column().classes('w-full gap-3 mt-2'):
                ui.button("🌲 Deep Work (50m Focus)", on_click=lambda: page.apply_preset(50, "Deep Work")).classes('w-full py-3 bg-emerald-700 text-white rounded-xl text-left justify-start capitalize')
                ui.button("📚 Study Session (25m Focus)", on_click=lambda: page.apply_preset(25, "Study Session")).classes('w-full py-3 bg-emerald-600 text-white rounded-xl text-left justify-start capitalize')
                ui.button("⚡ Quick Focus (15m Focus)", on_click=lambda: page.apply_preset(15, "Quick Focus")).classes('w-full py-3 bg-emerald-500 text-white rounded-xl text-left justify-start capitalize')
            
            ui.separator().classes('my-4')
            ui.label("Today's Target Metrics").classes('text-xs font-bold text-stone-400 uppercase tracking-wider mb-2')
            
            with ui.row().classes('w-full justify-between items-center py-2 border-b border-stone-100 dark:border-stone-800'):
                ui.label("Daily Target:").classes('text-stone-500 dark:text-stone-400 font-semibold')
                page.target_goal_val = ui.label("2.0 hrs").classes('font-bold')
                
            with ui.row().classes('w-full justify-between items-center py-2 border-b border-stone-100 dark:border-stone-800'):
                ui.label("Focused Completed:").classes('text-stone-500 dark:text-stone-400 font-semibold')
                page.focused_completed_val = ui.label("0.0 hrs").classes('font-bold text-emerald-600 dark:text-emerald-400')
                
            with ui.row().classes('w-full justify-between items-center py-2'):
                ui.label("Completion Status:").classes('text-stone-500 dark:text-stone-400 font-semibold')
                page.goal_status_badge = ui.label("Incomplete").classes('px-2.5 py-0.5 rounded text-xs font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300')
