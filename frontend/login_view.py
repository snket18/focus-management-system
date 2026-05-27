from nicegui import ui, app
from backend import user_controller

class LoginView:
    def __init__(self, HEAD_HTML):
        self.HEAD_HTML = HEAD_HTML

    def build(self):
        """Construct the Login and Registration UI page."""
        ui.add_head_html(self.HEAD_HTML)
        ui.dark_mode()  # Support dark mode overrides automatically
        
        with ui.column().classes('w-full min-h-screen items-center justify-center p-4 bg-cream-earth'):
            with ui.card().classes('w-full max-w-[420px] p-8 rounded-2xl forest-card shadow-xl flex flex-col items-center border border-stone-200 dark:border-stone-800'):
                # Application Branding Logo
                with ui.row().classes('items-center gap-3 mb-6 select-none'):
                    ui.label("🌲").classes('text-4xl')
                    ui.label("Focus System").classes('text-2xl font-black text-emerald-800 dark:text-emerald-400 tracking-tight')

                # Log In / Register Tabs
                with ui.tabs().classes('w-full mb-6') as tabs:
                    login_tab = ui.tab('Log In', icon='login')
                    register_tab = ui.tab('Register', icon='person_add')

                with ui.tab_panels(tabs, value=login_tab).classes('w-full bg-transparent shadow-none'):
                    # --- LOGIN TAB PANEL ---
                    with ui.tab_panel(login_tab).classes('p-0 gap-4 flex flex-col'):
                        ui.label("Welcome back! Please sign in.").classes('text-stone-500 dark:text-stone-400 text-xs font-semibold uppercase tracking-wider mb-1 text-center')
                        
                        login_username = ui.input(
                            'Username'
                        ).classes('w-full').props('autofocus')
                        
                        login_password = ui.input(
                            'Password', 
                            password=True
                        ).classes('w-full')
                        
                        async def do_login():
                            username = login_username.value.strip()
                            password = login_password.value
                            
                            if not username or not password:
                                ui.notify('Username and password are required', type='warning')
                                return
                            
                            user = await user_controller.authenticate_user(username, password)
                            if user:
                                app.storage.user['user_id'] = user.id
                                app.storage.user['username'] = user.username
                                ui.notify(f'Welcome back, {user.username}!', type='positive')
                                ui.navigate.to('/')
                            else:
                                ui.notify('Invalid username or password', type='negative')

                        login_password.on('keydown.enter', do_login)
                        ui.button(
                            'Sign In', 
                            on_click=do_login
                        ).classes('bg-emerald-600 hover:bg-emerald-700 text-white w-full py-3 rounded-xl font-bold mt-2 shadow-md transition')

                    # --- REGISTRATION TAB PANEL ---
                    with ui.tab_panel(register_tab).classes('p-0 gap-4 flex flex-col'):
                        ui.label("Create an account to start focusing.").classes('text-stone-500 dark:text-stone-400 text-xs font-semibold uppercase tracking-wider mb-1 text-center')
                        
                        reg_username = ui.input('Choose Username').classes('w-full')
                        reg_password = ui.input('Choose Password', password=True).classes('w-full')
                        reg_password_confirm = ui.input('Confirm Password', password=True).classes('w-full')
                        
                        async def do_register():
                            username = reg_username.value.strip()
                            password = reg_password.value
                            password_confirm = reg_password_confirm.value
                            
                            if not username or not password or not password_confirm:
                                ui.notify('All fields are required', type='warning')
                                return
                            if len(password) < 6:
                                ui.notify('Password must be at least 6 characters long', type='warning')
                                return
                            if password != password_confirm:
                                ui.notify('Passwords do not match', type='warning')
                                return
                            
                            if await user_controller.username_exists(username):
                                ui.notify('Username is already taken', type='warning')
                                return
                            
                            try:
                                user = await user_controller.create_user(username, password)
                                app.storage.user['user_id'] = user.id
                                app.storage.user['username'] = user.username
                                ui.notify('Registration successful!', type='positive')
                                ui.navigate.to('/')
                            except Exception as e:
                                ui.notify(f'Registration failed: {e}', type='negative')

                        reg_password_confirm.on('keydown.enter', do_register)
                        ui.button(
                            'Register Account', 
                            on_click=do_register
                        ).classes('bg-emerald-600 hover:bg-emerald-700 text-white w-full py-3 rounded-xl font-bold mt-2 shadow-md transition')
