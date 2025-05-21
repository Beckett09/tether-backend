from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
import requests
import json
import os

# --- Backend Config ---
BASE_URL = 'http://127.0.0.1:5000'
TOKEN_FILE = 'user_token.json'


# --- Helper Functions ---
def save_token(token):
    with open(TOKEN_FILE, 'w') as f:
        json.dump({'token': token}, f)


def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
            return data.get('token')
    return None


class AccountTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)
        self.mode = 'signin'
        self.build_form()

    def build_form(self):
        self.clear_widgets()
        title = "Sign In" if self.mode == 'signin' else "Create Account"
        self.add_widget(Label(text=title, font_size=24, size_hint=(1, 0.1)))
        self.email_input = TextInput(hint_text="Email", multiline=False, size_hint=(1, 0.1))
        self.add_widget(self.email_input)
        self.pass_input = TextInput(hint_text="Password", password=True, multiline=False, size_hint=(1, 0.1))
        self.add_widget(self.pass_input)
        if self.mode == 'signup':
            self.confirm_input = TextInput(hint_text="Confirm Password", password=True, multiline=False,
                                           size_hint=(1, 0.1))
            self.add_widget(self.confirm_input)
        action_text = "Sign In" if self.mode == 'signin' else "Create Account"
        self.action_btn = Button(text=action_text, size_hint=(1, 0.1))
        self.action_btn.bind(on_press=self.do_action)
        self.add_widget(self.action_btn)
        switch_text = "No account? Sign Up" if self.mode == 'signin' else "Have account? Sign In"
        self.switch_btn = Button(text=switch_text, size_hint=(1, 0.1))
        self.switch_btn.bind(on_press=self.switch_mode)
        self.add_widget(self.switch_btn)
        self.status = Label(text="", size_hint=(1, 0.1))
        self.add_widget(self.status)

    def switch_mode(self, instance):
        self.mode = 'signup' if self.mode == 'signin' else 'signin'
        self.build_form()

    def do_action(self, instance):
        email = self.email_input.text.strip()
        pwd = self.pass_input.text.strip()
        if not email or not pwd:
            self.status.text = "Please enter email and password."
            return
        if self.mode == 'signin':
            resp = requests.post(f'{BASE_URL}/login', json={'email': email, 'password': pwd})
            if resp.status_code == 200:
                token = resp.json().get('token')
                save_token(token)
                self.status.text = f"Signed in as {email}"
            else:
                self.status.text = "Login failed"
        else:
            confirm = self.confirm_input.text.strip()
            if pwd != confirm:
                self.status.text = "Passwords do not match"
                return
            resp = requests.post(f'{BASE_URL}/signup', json={'email': email, 'password': pwd})
            if resp.status_code == 201:
                self.status.text = "Account created. Please sign in."
                self.mode = 'signin'
                self.build_form()
            else:
                self.status.text = "Sign-up failed"


class HomeTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)
        self.token = load_token()
        self.add_widget(Label(text="Welcome to Tether Home", font_size=24, size_hint=(1, 0.1)))
        self.status_lbl = Label(text="Status: Disconnected", size_hint=(1, 0.1))
        self.add_widget(self.status_lbl)
        self.connect_btn = Button(text="Connect to Device", size_hint=(1, 0.1))
        self.connect_btn.bind(on_press=self.connect_device)
        self.add_widget(self.connect_btn)

        self.sync_btn = Button(text="Sync Data with Server", size_hint=(1, 0.1))
        self.sync_btn.bind(on_press=self.sync_data)
        self.add_widget(self.sync_btn)

        self.sync_status = Label(text="Sync: N/A", size_hint=(1, 0.1))
        self.add_widget(self.sync_status)

        # Placeholder for more features

    def connect_device(self, instance):
        # Placeholder for BLE connection logic
        self.status_lbl.text = "Status: Device Connected (simulated)"

    def sync_data(self, instance):
        if not self.token:
            self.sync_status.text = "Not authenticated"
            return
        # gather local data
        local_data = {'dummy': 'example'}
        headers = {'Authorization': f'Bearer {self.token}'}
        resp = requests.post(f'{BASE_URL}/sync', json={'local_data': local_data}, headers=headers)
        if resp.status_code == 200:
            server_data = resp.json().get('server_data')
            self.sync_status.text = "Sync successful"
            # merge or update local storage as needed
        else:
            self.sync_status.text = "Sync failed"


class SettingsTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)
        self.add_widget(Label(text="Settings", font_size=24, size_hint=(1, 0.1)))
        self.sleep_toggle = ToggleButton(text="Sleep Mode: OFF", size_hint=(1, 0.1))
        self.sleep_toggle.bind(on_press=self.toggle_sleep)
        self.add_widget(self.sleep_toggle)

    def toggle_sleep(self, instance):
        if self.sleep_toggle.state == 'down':
            self.sleep_toggle.text = "Sleep Mode: ON"
        else:
            self.sleep_toggle.text = "Sleep Mode: OFF"


class TetherTabbedPanel(TabbedPanel):
    def __init__(self, **kwargs):
        super().__init__(do_default_tab=False, **kwargs)
        self.account_tab = TabbedPanelItem(text='Account')
        self.account_tab.add_widget(AccountTab())
        self.add_widget(self.account_tab)

        self.home_tab = TabbedPanelItem(text='Home')
        self.home_tab.add_widget(HomeTab())
        self.add_widget(self.home_tab)

        self.settings_tab = TabbedPanelItem(text='Settings')
        self.settings_tab.add_widget(SettingsTab())
        self.add_widget(self.settings_tab)


class TetherApp(App):
    def build(self):
        return TetherTabbedPanel()


if __name__ == '__main__':
    TetherApp().run()
