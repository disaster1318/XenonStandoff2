from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.switch import Switch
from kivy.uix.slider import Slider
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
import subprocess
import webbrowser
import threading
import time

from memory import get_pid, get_module_base, get_all_players, enable_wallhack, Offsets
from esp import ESPOverlay


class LockedTab(TabbedPanelItem):
    def __init__(self, text, **kwargs):
        super().__init__(text=text, **kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        layout.add_widget(Label(text="🔒", font_size=60, color=(1, 0.42, 0.2, 1)))
        layout.add_widget(Label(
            text="[size=24][color=ff6b35]Купите подписку[/color][/size]\n[size=16][color=aaaaaa]для использования вкладки[/color][/size]",
            markup=True, halign='center'
        ))
        buy_btn = Button(
            text="КУПИТЬ ПОДПИСКУ",
            font_size=18,
            bold=True,
            background_color=(1, 0.42, 0.2, 1),
            background_normal='',
            size_hint=(0.6, 0.15),
            pos_hint={'center_x': 0.5}
        )
        buy_btn.bind(on_press=lambda x: webbrowser.open("https://t.me/xinatovs"))
        layout.add_widget(buy_btn)
        self.add_widget(layout)


class FloatingIcon(Widget):
    """Плавающая иконка для разворачивания меню"""
    def __init__(self, on_click, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (80, 40)
        self.pos = (Window.width - 90, 20)  # правый нижний угол
        self.on_click = on_click

        with self.canvas.before:
            Color(0.1, 0.1, 0.15, 0.9)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[10])
        self.bind(pos=self.update_rect, size=self.update_rect)

        self.label = Label(
            text="[b]XENON[/b]",
            markup=True,
            color=(1, 0.42, 0.2, 1),
            font_size=18,
            size=self.size,
            pos=self.pos
        )
        self.add_widget(self.label)

    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.label.pos = instance.pos
        self.label.size = instance.size

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.on_click()
            return True


class LaunchScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[20])
        self.bind(size=self.update_rect, pos=self.update_rect)

        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        layout.add_widget(Label(text="[b]XENON[/b]", font_size=80, color=(1, 0.42, 0.2, 1), markup=True))
        layout.add_widget(Label(text="[size=18][color=aaaaaa]ПОЛНЫЙ КОНТРОЛЬ НАД ИГРОЙ[/color][/size]", markup=True))

        start_btn = Button(
            text="⚡ СТАРТ ЧИТА",
            font_size=28,
            bold=True,
            background_color=(1, 0.42, 0.2, 1),
            background_normal='',
            size_hint=(1, 0.25)
        )
        start_btn.bind(on_press=self.start_cheat)
        layout.add_widget(start_btn)

        channel_btn = Button(
            text="📢 НАШ КАНАЛ",
            font_size=20,
            background_color=(0.15, 0.15, 0.2, 1),
            background_normal=''
        )
        channel_btn.bind(on_press=self.open_channel)
        layout.add_widget(channel_btn)

        layout.add_widget(Label(text="[size=14][color=666666]t.me/xenonst2 | v1.1[/color][/size]", markup=True))
        self.add_widget(layout)

    def update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos

    def start_cheat(self, instance):
        try:
            subprocess.Popen(["am", "start", "-n", "com.axlebolt.standoff2/com.unity3d.player.UnityPlayerActivity"])
        except:
            pass
        self.manager.current = 'menu'

    def open_channel(self, instance):
        webbrowser.open("https://t.me/xenonst2")


class CheatMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.esp_enabled = False
        self.running = False
        self.is_minimized = False
        self.floating_icon = None

        self.esp_overlay = ESPOverlay()
        self.add_widget(self.esp_overlay)

        with self.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[10])
        self.bind(size=self.update_rect, pos=self.update_rect)

        # ===== ОСНОВНОЙ ЛЕЙАУТ =====
        layout = BoxLayout(orientation='vertical', padding=10, spacing=5)

        # ===== HEADER =====
        header = BoxLayout(size_hint_y=0.1, padding=10)

        left_header = BoxLayout(orientation='horizontal', size_hint_x=0.5, spacing=10)
        left_header.add_widget(Label(text="XENON", font_size=32, color=(1, 0.42, 0.2, 1), bold=True))
        left_header.add_widget(Label(text="FREE", font_size=14, color=(0.5, 0.5, 0.5, 1), bold=True))
        header.add_widget(left_header)

        right_header = BoxLayout(orientation='horizontal', size_hint_x=0.5)
        right_header.add_widget(Label(text="t.me/xenonst2", font_size=12, color=(0.5, 0.5, 0.5, 1), halign='right'))

        # КНОПКА СВЕРНУТЬ
        minimize_btn = Button(
            text="—",
            font_size=24,
            size_hint=(None, None),
            size=(40, 40),
            background_color=(0.2, 0.2, 0.3, 1),
            background_normal='',
            pos_hint={'center_y': 0.5}
        )
        minimize_btn.bind(on_press=self.minimize)
        right_header.add_widget(minimize_btn)

        header.add_widget(right_header)
        layout.add_widget(header)

        # ===== TABS =====
        tabs = TabbedPanel(do_default_tab=False, size_hint_y=0.85)

        esp_tab = TabbedPanelItem(text="ESP")
        esp_layout = BoxLayout(orientation='vertical', spacing=5, padding=15)

        self.esp_switch = self.make_switch("Enable ESP", True)
        self.esp_switch.bind(active=self.toggle_esp)
        esp_layout.add_widget(self.esp_switch)

        for name, default in [
            ("Box", True),
            ("Head Dot", True),
            ("Snap Line", False),
            ("Health Bar", True),
            ("Name", True),
            ("Distance", True)
        ]:
            esp_layout.add_widget(self.make_switch(name, default))
        esp_tab.add_widget(esp_layout)

        tabs.add_widget(esp_tab)
        tabs.add_widget(LockedTab(text="Chams"))
        tabs.add_widget(LockedTab(text="World"))
        tabs.add_widget(LockedTab(text="AIM"))
        layout.add_widget(tabs)

        # ===== FOOTER =====
        footer = BoxLayout(size_hint_y=0.08, padding=10)
        footer.add_widget(Label(text="2.05 OBT", font_size=12, color=(0.5, 0.5, 0.5, 1)))
        footer.add_widget(Label(text="Написать сообщение v1.1 t.me/xenonst2", font_size=12, color=(0.5, 0.5, 0.5, 1)))
        layout.add_widget(footer)

        self.menu_layout = layout
        self.add_widget(layout)

    def update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos

    def make_switch(self, text, default):
        box = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        box.add_widget(Label(text=text, font_size=16, color=(1, 1, 1, 0.9)))
        sw = Switch(active=default, active_color=(1, 0.42, 0.2, 1))
        box.add_widget(sw)
        return box

    def toggle_esp(self, instance, value):
        self.esp_enabled = value
        if value:
            threading.Thread(target=self.esp_loop, daemon=True).start()
        else:
            self.running = False
            self.esp_overlay.clear()

    def esp_loop(self):
        self.running = True
        pid = get_pid()
        if pid == 0:
            return
        base = get_module_base(pid, "libil2cpp.so")
        if base == 0:
            return

        enable_wallhack(pid, base)

        while self.running:
            players = get_all_players(pid, base)
            self.esp_overlay.update_players(players)
            time.sleep(0.05)

    # ===== СВОРАЧИВАНИЕ / РАЗВОРАЧИВАНИЕ =====
    def minimize(self, instance=None):
        self.is_minimized = True
        self.menu_layout.opacity = 0
        self.menu_layout.disabled = True

        # Показываем плавающую иконку
        if not self.floating_icon:
            self.floating_icon = FloatingIcon(on_click=self.restore)
            self.add_widget(self.floating_icon)

    def restore(self):
        self.is_minimized = False
        self.menu_layout.opacity = 1
        self.menu_layout.disabled = False

        if self.floating_icon:
            self.remove_widget(self.floating_icon)
            self.floating_icon = None


class XenonApp(App):
    def build(self):
        Window.clearcolor = (0.05, 0.05, 0.08, 1)
        sm = ScreenManager()
        sm.add_widget(LaunchScreen(name='launch'))
        sm.add_widget(CheatMenu(name='menu'))
        return sm


if __name__ == '__main__':
    XenonApp().run()
