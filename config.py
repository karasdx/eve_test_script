"""
All settings in one place. Edit this file instead of the code.

Template spec: name -> (file in images/, threshold, use_colour, region)
  use_colour : True  = match in colour (needed when icons differ ONLY by colour,
                       e.g. red/grey/orange standing icons in local)
               False = match in grayscale (about 3x cheaper, fine for shapes/text)
  region     : None = search the whole window, or (x0, y0, x1, y1) as fractions
               of the window, e.g. (0.0, 0.5, 0.3, 1.0) = bottom-left quarter-ish.
               Restricting the region is the biggest CPU saver - set it once you
               know where your local / overview / drone windows sit.
"""
from pathlib import Path

IMAGE_DIR = Path(__file__).parent / "images"

# --------------------------------------------------------------------------
# UI scaling (EVE: Settings > Display & Graphics > UI Scaling)
# --------------------------------------------------------------------------
UI_SCALE = 150              # your clients' UI scaling in %: 100, 125 or 150
IMAGES_UI_SCALE = 150       # the UI scaling the pictures in images/ were taken at
# The pictures are resized by UI_SCALE / IMAGES_UI_SCALE when the bot starts.
# For best accuracy put screenshots taken at that scaling in images/125/ or
# images/150/ (same file names) - those are used as-is instead of resizing.
# Not sure which scaling the pictures are at? Run calibrate: it tests each one.

# --------------------------------------------------------------------------
# Characters live in characters.txt (one per line: short name = character name).
# The first one is the default. Pick one with:  python main.py rat --profile surt
# --------------------------------------------------------------------------
CHARACTERS_FILE = Path(__file__).parent / "characters.txt"


def load_profiles(path=CHARACTERS_FILE):
    """{short name: window title} from characters.txt, in file order."""
    profiles = {}
    if not path.exists():
        raise SystemExit(f"{path.name} not found - create it with lines like: surt = Surt Boe Agalder")
    for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, sep, character = (part.strip() for part in line.partition("="))
        if not sep or not name or not character:
            raise SystemExit(f"{path.name} line {n}: expected 'short name = character name', got: {line}")
        if character.startswith("EVE - "):      # accept either form
            character = character[len("EVE - "):]
        profiles[name] = "EVE - " + character
    if not profiles:
        raise SystemExit(f"{path.name} has no characters in it")
    return profiles


PROFILES = load_profiles()
DEFAULT_PROFILE = next(iter(PROFILES))

# --------------------------------------------------------------------------
# Performance
# --------------------------------------------------------------------------
TICK_SECONDS = 1.0          # main loop interval (raise to 1.5-2 to use less CPU)
CV_THREADS = 2              # OpenCV threads; lower = smaller CPU spikes

# --------------------------------------------------------------------------
# Input  (see README "Why Shift+R sometimes fails")
# --------------------------------------------------------------------------
KEY_HOLD_SECONDS = 0.10     # how long a key/combination is held down
KEY_GAP_SECONDS = 0.05      # pause between pressing modifier and key
MOUSE_MOVE_SECONDS = 0.2
USE_DIRECTINPUT = True      # use pydirectinput (scan codes) if installed

KEYS = {
    "recall_drones": ("shift", "r"),
    "launch_drones": ("shift", "f"),
    "drones_engage": ("f",),
    "approach":      ("q",),
    "dock":          ("d",),       # dock / jump on the selected item
    "orbit":         ("w",),
    "stop_ship":     ("ctrl", "space"),
    "bookmark":      ("ctrl", "b"),
    "confirm":       ("enter",),
    "prop_module":   ("f1",),
    "tank_modules":  ("f2", "f3"),         # pressed one after another, after undock + stop
    "autopilot_end": ("ctrl", "s"),        # what the old auto_pilot pressed at the end
    "lock_modifier": "ctrl",               # ctrl+click = lock target
}

# --------------------------------------------------------------------------
# Timings (seconds)
# --------------------------------------------------------------------------
TIMING = {
    "lock_target": 10,          # wait after ctrl+click before sending drones
    "docked_wait_danger": 300,  # stay docked after a hostile appeared
    "docked_wait_fail": 60,     # stay docked after failing to find orbit point
    "dock_timeout": 60,         # keep pressing dock until docked, at most this long
    "dock_retry": 10,           # press dock again if not docked after this long
    "orbit_wait": 20,           # after landing, wait this long for the orbit point
    "orbit_check": 5,           # "Orbiting" must show this long after W, else orbit again (3 tries)
    "drones_launch": 8,         # header must read (5/5) this long after Shift+F, else press again
    "danger_poll": 1,           # how often to look for danger during long waits
    "site_retry": 30,           # no site / could not undock: try again after this long
    "after_undock": 10,         # after clicking undock: wait, then stop + tank modules, then warp
    "drones_return": 15,        # after recalling drones before warping off
    "warp_start": 30,           # give up waiting for the warp to START after this long
    "warp_poll": 0.5,           # how often to check the "warping" image
    "after_warp": 3,            # after "warping" disappears, wait this long, then orbit + drones
    "warp_timeout": 180,
    "menu_open": 0.6,           # right-click menu needs time to appear
    "recall_wait": 10,          # wait this long for (0/5) after Shift+R, then press it again (3 tries)
    "idle_ticks_limit": 20,     # ticks of idle drones before checking the site is done
    "autopilot_settle": 15,
    "autopilot_max_misses": 10,
    "alarm_cooldown": 5,
}

# --------------------------------------------------------------------------
# Templates
# --------------------------------------------------------------------------
TEMPLATES = {
    # danger - local standings (colour matters!)
    "enemy_red":     ("enemy(1).png", 0.82, True, None),
    "enemy_neutral": ("enemy(2).png", 0.82, True, None),
    "enemy_orange":  ("enemy(3).png", 0.82, True, None),
    "dread":         ("dread.png", 0.85, True, None),
    "warp_bubble":   ("babo.png", 0.82, False, None),   # "Mobile Small Warp..."
    # ewar on us -> kill that rat first
    "ewar_neut":     ("cap_neutralized.png", 0.82, False, None),
    "ewar_web":      ("web.png", 0.82, False, None),
    "ewar_disrupt":  ("disrupted.png", 0.82, False, None),
    "ewar_paint":    ("painted.png", 0.82, False, None),
    # status
    "drones_idle":   ("drone.png", 0.82, False, None),
    # "Drones in Space" header: (5/5) = all launched, (0/5) = all home.
    # They differ by one digit, so both are checked and the closer match wins.
    "drones_out":    ("drones_in_space_5.png", 0.85, False, None),
    "drones_home":   ("drones_in_space_0.png", 0.85, False, None),
    "boss_wreck":    ("boss_wreck(A).png", 0.82, False, None),
    "warping":       ("warping.png", 0.80, False, None),
    # targets
    "unlocked_1":    ("unlocked_target.png", 0.65, False, None),
    "unlocked_2":    ("unlocked_target_1.png", 0.65, False, None),
    "unlocked_3":    ("unlocked_target_2.png", 0.65, False, None),
    # navigation
    "safe_station":  ("target_structure(1).png", 0.80, False, None),
    "undock":        ("undock.png", 0.70, False, None),
    "rat_site":      ("rat_site(A).png", 0.70, False, None),
    "warp_to":       ("wrap_to_10.png", 0.65, False, None),
    "orbit_point":   ("orbit_point_new.png", 0.85, False, None),
    "orbiting":      ("orbiting.png", 0.80, False, None),    # HUD text after W
    "target_gate":   ("target_gate.png", 0.70, True, None),
}

DANGER = ["enemy_red", "enemy_neutral", "enemy_orange", "dread", "warp_bubble"]
EWAR = ["ewar_neut", "ewar_web", "ewar_disrupt", "ewar_paint"]
UNLOCKED = ["unlocked_1", "unlocked_2", "unlocked_3"]
