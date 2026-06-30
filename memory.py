import os
import struct
import math
import time

class Offsets:
    ALL_PLAYERS = 0x38
    LOCAL_PLAYER = 0x68

    TEAM = 0x79
    PLAYER_CHARACTER_VIEW = 0xD0
    PLAYER_MAIN_CAMERA = 0xE8
    TRANSFORM = 0x100
    PHOTON_PLAYER = 0x160

    BASE_TRANSFORM = 0x38
    BASE_PHOTON_PLAYER = 0x40
    HEALTH = 0x48
    MAX_HEALTH = 0x4C

    BIPED_MAP = 0x48
    HEAD = 0x20
    CAMERA = 0x20
    NAME_FIELD = 0x20
    POSITION = 0x90
    PLAYER_SIZE = 0x100


def get_pid():
    for pid in os.listdir("/proc"):
        try:
            with open(f"/proc/{pid}/cmdline", "r") as f:
                if "standoff2" in f.read():
                    return int(pid)
        except:
            pass
    return 0

def get_module_base(pid, module_name):
    try:
        with open(f"/proc/{pid}/maps", "r") as f:
            for line in f:
                if module_name in line:
                    return int(line.split("-")[0], 16)
    except:
        pass
    return 0

def read_memory(pid, address, size):
    try:
        with open(f"/proc/{pid}/mem", "rb") as mem:
            mem.seek(address)
            return mem.read(size)
    except:
        return b"\x00" * size

def write_memory(pid, address, data):
    try:
        with open(f"/proc/{pid}/mem", "r+b") as mem:
            mem.seek(address)
            mem.write(data)
    except:
        pass

def read_float(pid, address):
    return struct.unpack("f", read_memory(pid, address, 4))[0]

def read_int(pid, address):
    return struct.unpack("i", read_memory(pid, address, 4))[0]

def read_bool(pid, address):
    return read_memory(pid, address, 1)[0] == 1

def read_vector(pid, address):
    data = read_memory(pid, address, 12)
    return struct.unpack("fff", data)

def write_vector(pid, address, vec):
    write_memory(pid, address, struct.pack("fff", vec[0], vec[1], vec[2]))

def read_ptr(pid, address):
    data = read_memory(pid, address, 8)
    return struct.unpack("Q", data)[0]


def get_transform_position(pid, transform_addr):
    if not transform_addr:
        return (0.0, 0.0, 0.0)
    return read_vector(pid, transform_addr + Offsets.POSITION)

def get_player_head_position(pid, player_ptr):
    char_view = read_ptr(pid, player_ptr + Offsets.PLAYER_CHARACTER_VIEW)
    if not char_view:
        return (0.0, 0.0, 0.0)

    biped_map = read_ptr(pid, char_view + Offsets.BIPED_MAP)
    if not biped_map:
        return (0.0, 0.0, 0.0)

    head_transform = read_ptr(pid, biped_map + Offsets.HEAD)
    if not head_transform:
        return (0.0, 0.0, 0.0)

    return get_transform_position(pid, head_transform)

def get_player_root_position(pid, player_ptr):
    transform = read_ptr(pid, player_ptr + Offsets.BASE_TRANSFORM)
    if not transform:
        return (0.0, 0.0, 0.0)
    return get_transform_position(pid, transform)

def get_player_health(pid, player_ptr):
    return read_int(pid, player_ptr + Offsets.HEALTH)

def get_player_max_health(pid, player_ptr):
    return read_int(pid, player_ptr + Offsets.MAX_HEALTH)

def get_player_team(pid, player_ptr):
    return read_int(pid, player_ptr + Offsets.TEAM)

def get_player_name(pid, player_ptr):
    photon = read_ptr(pid, player_ptr + Offsets.BASE_PHOTON_PLAYER)
    if not photon:
        return "Bot"

    name_ptr = read_ptr(pid, photon + Offsets.NAME_FIELD)
    if not name_ptr:
        return "Unknown"

    length = read_int(pid, name_ptr + 0x08)
    if length <= 0 or length > 64:
        return "Unknown"

    data = read_memory(pid, name_ptr + 0x0C, length * 2)
    try:
        return data.decode('utf-16le')
    except:
        return "Unknown"

def get_player_distance(local_pos, player_pos):
    dx = local_pos[0] - player_pos[0]
    dy = local_pos[1] - player_pos[1]
    dz = local_pos[2] - player_pos[2]
    return math.sqrt(dx*dx + dy*dy + dz*dz)


def get_all_players(pid, base, local_player=None):
    players = []

    if local_player:
        local_team = get_player_team(pid, local_player)
        local_pos = get_player_root_position(pid, local_player)
    else:
        local_team = -1
        local_pos = (0.0, 0.0, 0.0)

    for i in range(32):
        player_ptr = base + i * Offsets.PLAYER_SIZE

        if local_player and player_ptr == local_player:
            continue

        health = get_player_health(pid, player_ptr)
        if health <= 0:
            continue

        pos = get_player_root_position(pid, player_ptr)
        if pos == (0.0, 0.0, 0.0):
            continue

        team = get_player_team(pid, player_ptr)
        name = get_player_name(pid, player_ptr)
        head = get_player_head_position(pid, player_ptr)
        distance = get_player_distance(local_pos, pos) if local_pos else 0.0

        players.append({
            "ptr": player_ptr,
            "pos": pos,
            "head": head,
            "health": health,
            "max_health": get_player_max_health(pid, player_ptr),
            "team": team,
            "name": name,
            "distance": distance,
            "is_enemy": team != local_team if local_team != -1 else False
        })

    return players


def world_to_screen(pid, world_pos, camera_addr, screen_width, screen_height):
    if not camera_addr:
        return (-1.0, -1.0)

    cam_pos = read_vector(pid, camera_addr + 0x18)

    dx = world_pos[0] - cam_pos[0]
    dy = world_pos[1] - cam_pos[1]
    dz = world_pos[2] - cam_pos[2]

    if dz <= 0:
        return (-1.0, -1.0)

    scale = 1.0 / dz * 100.0
    screen_x = screen_width / 2 + dx * scale
    screen_y = screen_height / 2 - dy * scale

    if screen_x < 0 or screen_x > screen_width or screen_y < 0 or screen_y > screen_height:
        return (-1.0, -1.0)

    return (screen_x, screen_y)


def aim_at_target(pid, base, local_player, fov, silent_aim=False):
    if not local_player:
        return False

    camera = read_ptr(pid, local_player + Offsets.PLAYER_MAIN_CAMERA)
    if not camera:
        return False

    cam_comp = read_ptr(pid, camera + Offsets.CAMERA)
    if not cam_comp:
        return False

    cam_pos = read_vector(pid, cam_comp + 0x18)
    view_dir = read_vector(pid, cam_comp + 0x24)

    players = get_all_players(pid, base, local_player)

    best_angle = fov
    best_target = None

    for player in players:
        if not player["is_enemy"]:
            continue

        target_pos = player["head"] if player["head"] != (0.0, 0.0, 0.0) else player["pos"]

        dx = target_pos[0] - cam_pos[0]
        dy = target_pos[1] - cam_pos[1]
        dz = target_pos[2] - cam_pos[2]

        length = math.sqrt(dx*dx + dy*dy + dz*dz)
        if length == 0:
            continue

        direction = (dx/length, dy/length, dz/length)

        dot = view_dir[0]*direction[0] + view_dir[1]*direction[1] + view_dir[2]*direction[2]
        angle = math.degrees(math.acos(max(-1, min(1, dot))))

        if angle < best_angle:
            best_angle = angle
            best_target = target_pos

    if best_target:
        target_dir = (
            best_target[0] - cam_pos[0],
            best_target[1] - cam_pos[1],
            best_target[2] - cam_pos[2]
        )

        write_vector(pid, cam_comp + 0x24, target_dir)
        return True

    return False
