from nicegui import ui

def build_settings_tab(page):
    """Build the layout for the Settings Tab."""
    with ui.row().classes('w-full justify-center gap-6 wrap items-start'):
        # Settings configuration inputs
        with ui.card().classes('w-full md:w-[500px] p-6 rounded-2xl forest-card shadow-none'):
            ui.label("Configuration Preferences").classes('text-lg font-bold text-stone-700 dark:text-stone-200 mb-4')
            
            page.focus_len_in = ui.number(value=25, label="Focus Session Duration (minutes)", min=1).classes('w-full mb-3')
            page.short_break_in = ui.number(value=5, label="Short Break Duration (minutes)", min=1).classes('w-full mb-3')
            page.long_break_in = ui.number(value=15, label="Long Break Duration (minutes)", min=1).classes('w-full mb-3')
            page.daily_goal_in = ui.number(value=2.0, label="Daily Goal Target (hours)", min=0.1, step=0.1).classes('w-full mb-3')
            page.sound_enabled_switch = ui.switch("Enable Notification Audio Pings").classes('mb-4')
            
            ui.button(
                "Save Core Configurations", 
                on_click=lambda: page.save_app_settings()
            ).classes('bg-emerald-600 hover:bg-emerald-700 text-white w-full py-2.5 rounded-lg font-semibold')
            
            ui.separator().classes('my-6')
            ui.label("System Utilities").classes('text-xs font-bold text-stone-400 uppercase tracking-wider mb-2')
            ui.button(
                "Export Database to JSON File", 
                icon='download', 
                on_click=lambda: page.trigger_data_export()
            ).classes('bg-stone-600 hover:bg-stone-700 text-white w-full py-2.5 rounded-lg font-semibold')

        # Blocklist panels
        with ui.card().classes('w-full md:w-[450px] p-6 rounded-2xl forest-card shadow-none'):
            ui.label("Honor Blocklist Websites").classes('text-lg font-bold text-stone-700 dark:text-stone-200 mb-1')
            ui.label("Add distracting domains to block the app interface during focus sessions.").classes('text-xs text-stone-400 mb-4')
            
            with ui.row().classes('w-full items-center gap-2 mb-4'):
                page.block_domain_in = ui.input(placeholder="e.g. facebook.com").classes('grow')
                ui.button(
                    "Add Site", 
                    icon='add', 
                    on_click=lambda: page.append_blocked_domain()
                ).classes('bg-red-600 hover:bg-red-700 text-white font-semibold')
            
            ui.label("Blocked Domains").classes('text-xs font-bold text-stone-500 dark:text-stone-400 uppercase tracking-wider mb-2')
            page.blocked_domains_list_container = ui.column().classes('w-full gap-2')
