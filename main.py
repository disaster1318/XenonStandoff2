import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
import requests
import json
import os

CONFIG_FILE = "xenon.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"activated": False}

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)

def check_key(key):
    url = "https://umjmcdvjdqlsjmphvsfc.supabase.co/rest/v1/rpc/check_key"
    headers = {"Content-Type": "application/json", "apikey": "sb_publishable_4hpLHc_Wxl323Y5nGODAdQ_3vle6d2t"}
    try:
        r = requests.post(url, json={"key": key}, headers=headers)
        return r.json().get("valid", False)
    except:
        return False

class KeyScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=50)
        layout.add_widget(Label(text="Введите ключ:", font_size=28))
        self.inp = TextInput(multiline=False, font_size=24)
        layout.add_widget(self.inp)
        btn = Button(text="Активировать", font_size=24)
        btn.bind(on_press=self.activate)
        layout.add_widget(btn)
        self.status = Label(text="", font_size=20)
        layout.add_widget(self.status)
        self.add_widget(layout)

    def activate(self, instance):
        key = self.inp.text.strip()
        if not key:
            self.status.text = "Введи ключ!"
            return
        self.status.text = "Проверка..."
        if check_key(key):
            config = load_config()
            config["activated"] = True
            save_config(config)
            self.status.text = "✅ Готово"
            self.manager.current = 'main'
        else:
            self.status.text = "❌ Неверный ключ"

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=50)
        layout.add_widget(Label(text="Xenon Standoff", font_size=34))
        self.status = Label(text="Нажми Старт", font_size=24)
        layout.add_widget(self.status)
        btn_start = Button(text="Старт", font_size=24)
        btn_start.bind(on_press=lambda x: setattr(self.status, 'text', 'Чит активен!'))
        layout.add_widget(btn_start)
        btn_stop = Button(text="Стоп", font_size=24)
        btn_stop.bind(on_press=lambda x: setattr(self.status, 'text', 'Остановлен'))
        layout.add_widget(btn_stop)
        self.add_widget(layout)

class XenonApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(KeyScreen(name='key'))
        sm.add_widget(MainScreen(name='main'))
        if load_config().get("activated", False):
            sm.current = 'main'
        return sm

if __name__ == '__main__':
    XenonApp().run()
