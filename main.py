import threading
import requests
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen

SUPABASE_URL = "https://umjmcdvjdqlsjmphvsfc.supabase.co/rest/v1/rpc/check_key"
SUPABASE_APIKEY = "sb_publishable_4hpLHc_Wxl323Y5nGODAdQ_3vle6d2t"

KV = """
ScreenManager:
    LicenseScreen:
    MainScreen:

<LicenseScreen>:
    name: "license"
    BoxLayout:
        orientation: "vertical"
        padding: 40
        spacing: 20
        Label:
            text: "XenonStandoff"
            font_size: "28sp"
        Label:
            text: root.status_text
            color: (1,0,0,1)
        TextInput:
            id: key_input
            hint_text: "Введите лицензионный ключ"
            multiline: False
        Button:
            text: "Проверить ключ"
            size_hint_y: None
            height: "50dp"
            on_release:
                root.check_license(key_input.text)

<MainScreen>:
    name: "main"
    BoxLayout:
        orientation: "vertical"
        padding: 20
        spacing: 10
        Label:
            text: "XenonStandoff"
            font_size: "24sp"
        Label:
            id: analysis_status
            text: root.analysis_text
        Button:
            text: "Старт"
            on_release: root.start_analysis()
        Button:
            text: "Стоп"
            on_release: root.stop_analysis()
        Button:
            text: "🔫 Aimbot"
            on_release: root.toggle_aimbot()
        Button:
            text: "🧱 Wallhack"
            on_release: root.toggle_wallhack()
        Button:
            text: "👁️ ESP"
            on_release: root.toggle_esp()
        Button:
            text: "🔫 No Recoil"
            on_release: root.toggle_norecoil()
        Button:
            text: "🎯 Triggerbot"
            on_release: root.toggle_triggerbot()
"""

class LicenseScreen(Screen):
    status_text = ""
    def on_pre_enter(self):
        self.status_text = ""
    def check_license(self, key):
        if not key.strip():
            self.status_text = "Введите ключ"
            return
        self.status_text = "Проверка..."
        threading.Thread(target=self._check_license_thread, args=(key,), daemon=True).start()
    def _check_license_thread(self, key):
        try:
            headers = {"apikey": SUPABASE_APIKEY, "Content-Type": "application/json"}
            payload = {"key": key}
            response = requests.post(SUPABASE_URL, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                valid = False
                if isinstance(data, bool):
                    valid = data
                elif isinstance(data, dict):
                    valid = data.get("valid") or data.get("success") or data.get("result")
                if valid:
                    Clock.schedule_once(lambda dt: self.open_main())
                else:
                    Clock.schedule_once(lambda dt: self.set_status("Ключ недействителен"))
            else:
                Clock.schedule_once(lambda dt: self.set_status(f"Ошибка сервера: {response.status_code}"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.set_status(f"Ошибка: {str(e)}"))
    def set_status(self, text):
        self.status_text = text
    def open_main(self):
        self.manager.current = "main"

class MainScreen(Screen):
    analysis_text = "Ожидание запуска"
    aimbot_on = False
    wallhack_on = False
    esp_on = False
    norecoil_on = False
    triggerbot_on = False

    def start_analysis(self):
        self.analysis_text = "Чит активен"
        self.ids.analysis_status.text = self.analysis_text

    def stop_analysis(self):
        self.analysis_text = "Остановлен"
        self.ids.analysis_status.text = self.analysis_text

    def toggle_aimbot(self):
        self.aimbot_on = not self.aimbot_on
        self.ids.analysis_status.text = f"Aimbot: {'ON' if self.aimbot_on else 'OFF'}"

    def toggle_wallhack(self):
        self.wallhack_on = not self.wallhack_on
        self.ids.analysis_status.text = f"Wallhack: {'ON' if self.wallhack_on else 'OFF'}"

    def toggle_esp(self):
        self.esp_on = not self.esp_on
        self.ids.analysis_status.text = f"ESP: {'ON' if self.esp_on else 'OFF'}"

    def toggle_norecoil(self):
        self.norecoil_on = not self.norecoil_on
        self.ids.analysis_status.text = f"No Recoil: {'ON' if self.norecoil_on else 'OFF'}"

    def toggle_triggerbot(self):
        self.triggerbot_on = not self.triggerbot_on
        self.ids.analysis_status.text = f"Triggerbot: {'ON' if self.triggerbot_on else 'OFF'}"

class XenonStandoffApp(App):
    def build(self):
        return Builder.load_string(KV)

if __name__ == "__main__":
    XenonStandoffApp().run()
