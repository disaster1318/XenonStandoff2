import os
import struct
import math
import time

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
    VIEW_DIRECTION = 0x224
    CAMERA_POSITION = 0x18
    FOV = 0x30
    PLAYER_SIZE = 0x100
    IS_VISIBLE = 0x18


# ============================================
# === РАБОТА С ПАМЯТЬЮ ===
# ============================================

def get_pid():
    """Находит PID процесса Standoff 2"""
    for pid in os.listdir("/proc"):
        try:
            with open(f"/proc/{pid}/cmdline", "r") as f:
                cmd = f.read()
                if "standoff2" in cmd:
                    return int(pid)
        except:
            pass
    return 0

def get_module_base(pid, module_name):
    """Находит базовый адрес модуля в памяти процесса"""
    try:
        with open(f"/proc/{pid}/maps", "r") as f:
            for line in f:
                if module_name in line:
                    return int(line.split("-")[0], 16)
    except:
        pass
    return 0

def read_memory(pid, address, size):
    """Читает память процесса"""
    try:
        with open(f"/proc/{pid}/mem", "rb") as mem:
            mem.seek(address)
            return mem.read(size)
    except:
        return b"\x00" * size

def write_memory(pid, address, data):
    """Записывает данные в память процесса"""
    try:
        with open(f"/proc/{pid}/mem", "r+b") as mem:
            mem.seek(address)
            mem.write(data)
    except:
        pass

def read_float(pid, address):
    data = read_memory(pid, address, 4)
    return struct.unpack("f", data)[0]

def read_int(pid, address):
    data = read_memory(pid, address, 4)
    return struct.unpack("i", data)[0]

def read_bool(pid, address):
    data = read_memory(pid, address, 1)
    return data[0] == 1

def read_vector(pid, address):
    data = read_memory(pid, address, 12)
    return struct.unpack("fff", data)

def write_vector(pid, address, vec):
    data = struct.pack("fff", vec[0], vec[1], vec[2])
    write_memory(pid, address, data)


# ============================================
# === ESP ===
# ============================================

def get_all_players(pid, base):
    """Возвращает список всех игроков с их данными"""
    players = []
    for i in range(10):
        player_ptr = base + i * Offsets.PLAYER_SIZE

        pos = read_vector(pid, player_ptr + Offsets.MOVEMENT_CONTROLLER + Offsets.TRANSFORM + Offsets.POSITION)
        health = read_float(pid, player_ptr + Offsets.PLAYER_HIT_CONTROLLER + Offsets.HEALTH)
        team = read_int(pid, player_ptr + Offsets.PHOTON_PLAYER + Offsets.TEAM)
        is_visible = read_bool(pid, player_ptr + Offsets.PLAYER_OCCLUSION + Offsets.IS_VISIBLE)

        if health > 0:
            players.append({
                "pos": pos,
                "health": health,
                "team": team,
                "visible": is_visible
            })
    return players


# ============================================
# === AIM ===
# ============================================

def aim_at_target(pid, base, local_player, my_team, fov, silent_aim=False):
    """Наводит на ближайшего врага в зоне FOV"""
    # Получаем направление взгляда
    view_dir = read_vector(pid, local_player + Offsets.AIM_CONTROLLER + Offsets.VIEW_DIRECTION)

    # Получаем позицию камеры
    cam_pos = read_vector(pid, local_player + Offsets.CAMERA + Offsets.CAMERA_POSITION)

    best_angle = fov
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

        if silent_aim:
            # Silent Aim — пишем в другое поле (не дёргает камеру)
            write_vector(pid, local_player + Offsets.AIM_CONTROLLER + 0x230, target_dir)
        else:
            # Rage Mode — дёргает камеру
            write_vector(pid, local_player + Offsets.AIM_CONTROLLER + 0x224, target_dir)

        return True
    return False


# ============================================
# === WALLHACK ===
# ============================================

def enable_wallhack(pid, base):
    """Принудительно включает видимость всех игроков"""
    for i in range(10):
        player_ptr = base + i * Offsets.PLAYER_SIZE
        # Пишем True (1) в isVisible
        write_memory(pid, player_ptr + Offsets.PLAYER_OCCLUSION + Offsets.IS_VISIBLE, b"\x01")


# ============================================
# === CHAMS ===
# ============================================

def set_chams_color(pid, player_ptr, color):
    """Меняет цвет модели игрока (Chams)"""
    # Записываем цвет в материал
    write_memory(pid, player_ptr + Offsets.PLAYER_MATERIAL + 0x20, struct.pack("fff", color[0], color[1], color[2]))


# ============================================
# === НАСТРОЙКА ОРУЖИЯ ===
# ============================================

def set_no_recoil(pid, player_ptr):
    """Отключает отдачу"""
    write_memory(pid, player_ptr + Offsets.WEAPON + 0x24, struct.pack("f", 0.0))

def set_no_spread(pid, player_ptr):
    """Отключает разброс"""
    write_memory(pid, player_ptr + Offsets.WEAPON + 0x28, struct.pack("f", 0.0))
