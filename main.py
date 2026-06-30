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
from kivy.clock import Clock
import subprocess
import webbrowser
import threading
import math
import time

# ============================================
# === ПОДКЛЮЧАЕМ МОДУЛИ ===
# ============================================

from memory import get_pid, read_vector, read_float, read_int, read_bool, write_vector, get_module_base
from esp import ESPOverlay

# ============================================
# === ОФФСЕТЫ ===
# ============================================

class Offsets:
    MOVEMENT_CONTROLLER = 0x98
    PLAYER_HIT_CONTROLLER = 0xA8
    PLAYER_MATERIAL = 0xB0
    PLAYER_OCCLUSION = 0xB8
    CAMERA = 0xE8
    PHOTON_PLAYER = 0x160
    AIM_CONTROLLER = 0x80
    WEAPON = 0x88
    TRANSFORM = 0x70
    POSITION = 0x24
    HEALTH = 0x20
    TEAM = 0x70
    VIEW_DIRECTION = 0x224   # или 0x230, 0x23C
    CAMERA_POSITION = 0x18
    FOV = 0x30
    PLAYER_SIZE = 0x100
    IS_VISIBLE = 0x18


# ============================================
# === ЛАУНЧЕР ===
# ============================================

class LaunchScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[20])
        self.bind(size=self.update_rect, pos=self.update_rect)

        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)

        logo = Label(text="[b]XENON[/b]", font_size=80, color=(1, 0.42, 0.2, 1), markup=True)
        layout.add_widget(logo)

        subtitle = Label(text="[size=18][color=aaaaaa]ПОЛНЫЙ КОНТРОЛЬ НАД ИГРОЙ[/color][/size]", markup=True)
        layout.add_widget(subtitle)

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

        footer = Label(text="[size=14][color=666666]t.me/xenonst2 | v1.1[/color][/size]", markup=True)
        layout.add_widget(footer)

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


# ============================================
# === МЕНЮ ЧИТА С ESP И AIM ===
# ============================================

class CheatMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # === ПЕРЕМЕННЫЕ ===
        self.esp_enabled = False
        self.aim_enabled = False
        self.silent_aim = False
        self.rage_mode = False
        self.fov_value = 15
        self.aim_smooth = 5
        self.aim_speed = 8
        self.running = False
        self.esp_overlay = ESPOverlay()
        self.add_widget(self.esp_overlay)

        # === ФОН ===
        with self.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[10])
        self.bind(size=self.update_rect, pos=self.update_rect)

        layout = BoxLayout(orientation='vertical', padding=10, spacing=5)

        # === ХЕДЕР ===
        header = BoxLayout(size_hint_y=0.1, padding=10)
        header.add_widget(Label(text="XENON", font_size=32, color=(1, 0.42, 0.2, 1), bold=True))
        header.add_widget(Label(text="t.me/xenonst2", font_size=14, color=(0.5, 0.5, 0.5, 1), halign='right'))
        layout.add_widget(header)

        # === ВКЛАДКИ ===
        tabs = TabbedPanel(do_default_tab=False, size_hint_y=0.85)

        # --- ESP ---
        esp_tab = TabbedPanelItem(text="ESP")
        esp_layout = BoxLayout(orientation='vertical', spacing=5, padding=15)

        self.esp_switch = self.make_switch("Enable ESP", True)
        self.esp_switch.bind(active=self.toggle_esp)
        esp_layout.add_widget(self.esp_switch)

        for name, default in [
            ("Box", True),
            ("Snap Line", False),
            ("Skeleton", True),
            ("Health Bar", True),
            ("Nickname", False)
        ]:
            esp_layout.add_widget(self.make_switch(name, default))
        esp_tab.add_widget(esp_layout)

        # --- Chams ---
        chams_tab = TabbedPanelItem(text="Chams")
        chams_layout = BoxLayout(orientation='vertical', spacing=5, padding=15)
        chams_layout.add_widget(self.make_switch("Enable Chams", True))
        chams_layout.add_widget(self.make_switch("Glass", False))
        chams_layout.add_widget(Label(text="Intensity", font_size=16, color=(1, 1, 1, 0.8)))
        chams_layout.add_widget(Slider(min=0, max=5, value=2.6))
        chams_layout.add_widget(self.make_switch("Enemy", True))
        chams_layout.add_widget(self.make_switch("Wallhack", True))
        chams_tab.add_widget(chams_layout)

        # --- World ---
        world_tab = TabbedPanelItem(text="World")
        world_layout = BoxLayout(orientation='vertical', spacing=5, padding=15)
        for name in ["Fog", "Sky Color", "World Color", "View Model"]:
            world_layout.add_widget(self.make_switch(name, False))
        world_tab.add_widget(world_layout)

        # --- AIM ---
        aim_tab = TabbedPanelItem(text="AIM")
        aim_layout = BoxLayout(orientation='vertical', spacing=5, padding=15)

        self.aim_switch = self.make_switch("Enable AIM", False)
        self.aim_switch.bind(active=self.toggle_aim)
        aim_layout.add_widget(self.aim_switch)

        self.silent_switch = self.make_switch("Silent Aim", False)
        self.silent_switch.bind(active=self.set_silent_aim)
        aim_layout.add_widget(self.silent_switch)

        self.rage_switch = self.make_switch("Rage Mode", False)
        self.rage_switch.bind(active=self.set_rage_mode)
        aim_layout.add_widget(self.rage_switch)

        aim_layout.add_widget(Label(text="FOV", font_size=16, color=(1, 1, 1, 0.8)))
        self.fov_slider = Slider(min=0, max=180, value=15)
        self.fov_slider.bind(value=self.set_fov)
        aim_layout.add_widget(self.fov_slider)

        aim_layout.add_widget(Label(text="Smooth", font_size=16, color=(1, 1, 1, 0.8)))
        self.smooth_slider = Slider(min=1, max=20, value=5)
        self.smooth_slider.bind(value=self.set_smooth)
        aim_layout.add_widget(self.smooth_slider)

        aim_layout.add_widget(Label(text="Speed", font_size=16, color=(1, 1, 1, 0.8)))
        self.speed_slider = Slider(min=1, max=20, value=8)
        self.speed_slider.bind(value=self.set_speed)
        aim_layout.add_widget(self.speed_slider)

        aim_tab.add_widget(aim_layout)

        tabs.add_widget(esp_tab)
        tabs.add_widget(chams_tab)
        tabs.add_widget(world_tab)
        tabs.add_widget(aim_tab)
        layout.add_widget(tabs)

        # === ФУТЕР ===
        footer = BoxLayout(size_hint_y=0.08, padding=10)
        footer.add_widget(Label(text="2.05 OBT", font_size=12, color=(0.5, 0.5, 0.5, 1)))
        footer.add_widget(Label(text="Написать сообщение v1.1 t.me/xenonst2", font_size=12, color=(0.5, 0.5, 0.5, 1)))
        layout.add_widget(footer)

        self.add_widget(layout)

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    def update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos

    def make_switch(self, text, default):
        box = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        box.add_widget(Label(text=text, font_size=16, color=(1, 1, 1, 0.9)))
        sw = Switch(active=default, active_color=(1, 0.42, 0.2, 1))
        box.add_widget(sw)
        return box

    # === ESP ===
    def toggle_esp(self, instance, value):
        self.esp_enabled = value
        if value:
            self.start_esp()
        else:
            self.stop_esp()

    def start_esp(self):
        self.running = True
        threading.Thread(target=self.esp_loop, daemon=True).start()

    def stop_esp(self):
        self.running = False
        self.esp_overlay.clear()

    def esp_loop(self):
        pid = get_pid()
        if pid == 0:
            return
        base = get_module_base(pid, "libil2cpp.so")
        if base == 0:
            return

        while self.running:
            players = []
            for i in range(10):
                player_ptr = base + i * Offsets.PLAYER_SIZE

                pos = read_vector(pid, player_ptr + Offsets.MOVEMENT_CONTROLLER + Offsets.TRANSFORM + Offsets.POSITION)
                health = read_float(pid, player_ptr + Offsets.PLAYER_HIT_CONTROLLER + Offsets.HEALTH)
                team = read_int(pid, player_ptr + Offsets.PHOTON_PLAYER + Offsets.TEAM)

                if health > 0:
                    players.append({"pos": pos, "health": health, "team": team})

            self.esp_overlay.update_players(players)
            time.sleep(0.05)

    # === AIM ===
    def toggle_aim(self, instance, value):
        self.aim_enabled = value
        if value:
            threading.Thread(target=self.aim_loop, daemon=True).start()

    def set_silent_aim(self, instance, value):
        self.silent_aim = value
        if value:
            self.rage_mode = False
            self.rage_switch.active = False

    def set_rage_mode(self, instance, value):
        self.rage_mode = value
        if value:
            self.silent_aim = False
            self.silent_switch.active = False

    def set_fov(self, instance, value):
        self.fov_value = value

    def set_smooth(self, instance, value):
        self.aim_smooth = value

    def set_speed(self, instance, value):
        self.aim_speed = value

    def aim_loop(self):
        pid = get_pid()
        if pid == 0:
            return
        base = get_module_base(pid, "libil2cpp.so")
        if base == 0:
            return

        local_player = base + 0x123456  # заменить на реальный адрес PlayerController
        my_team = read_int(pid, local_player + Offsets.PHOTON_PLAYER + Offsets.TEAM)

        while self.aim_enabled:
            # Получаем направление взгляда
            view_dir = read_vector(pid, local_player + Offsets.AIM_CONTROLLER + Offsets.VIEW_DIRECTION)

            # Получаем позицию камеры
            cam_pos = read_vector(pid, local_player + Offsets.CAMERA + Offsets.CAMERA_POSITION)

            best_angle = self.fov_value
            best_target = None

            for i in range(10):
                player_ptr = base + i * Offsets.PLAYER_SIZE

                enemy_pos = read_vector(pid, player_ptr + Offsets.MOVEMENT_CONTROLLER + Offsets.TRANSFORM + Offsets.POSITION)
                enemy_team = read_int(pid, player_ptr + Offsets.PHOTON_PLAYER + Offsets.TEAM)
                enemy_health = read_float(pid, player_ptr + Offsets.PLAYER_HIT_CONTROLLER + Offsets.HEALTH)

                if enemy_health <= 0 or enemy_team == my_team:
                    continue

                # Вектор до врага
                direction = (
                    enemy_pos[0] - cam_pos[0],
                    enemy_pos[1] - cam_pos[1],
                    enemy_pos[2] - cam_pos[2]
                )

                length = math.sqrt(direction[0]**2 + direction[1]**2 + direction[2]**2)
                if length == 0:
                    continue
                direction = (direction[0]/length, direction[1]/length, direction[2]/length)

                # Угол между взглядом и направлением на врага
                dot = view_dir[0]*direction[0] + view_dir[1]*direction[1] + view_dir[2]*direction[2]
                angle = math.degrees(math.acos(max(-1, min(1, dot))))

                if angle < best_angle:
                    best_angle = angle
                    best_target = enemy_pos

            if best_target:
                target_dir = (
                    best_target[0] - cam_pos[0],
                    best_target[1] - cam_pos[1],
                    best_target[2] - cam_pos[2]
                )

                if self.silent_aim:
                    write_vector(pid, local_player + Offsets.AIM_CONTROLLER + 0x230, target_dir)
                else:
                    write_vector(pid, local_player + Offsets.AIM_CONTROLLER + 0x224, target_dir)

            time.sleep(0.05)


# ============================================
# === ПРИЛОЖЕНИЕ ===
# ============================================

class XenonApp(App):
    def build(self):
        Window.clearcolor = (0.05, 0.05, 0.08, 1)
        sm = ScreenManager()
        sm.add_widget(LaunchScreen(name='launch'))
        sm.add_widget(CheatMenu(name='menu'))
        return sm


if __name__ == '__main__':
    XenonApp().run()
