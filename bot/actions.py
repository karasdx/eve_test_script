"""Game actions built from vision + controls. Each is one clear step.

All mouse/keyboard use goes through self.input(), which takes the shared
InputLock and focuses this bot's client first - so several bots can run at
once without their clicks and keys getting mixed up.
"""
import sys
import threading
import time
from contextlib import contextmanager

from .input_lock import InputLock
from .window import FocusError, focus

_print_lock = threading.Lock()


def beep(ms=200):
    try:
        import winsound
        winsound.Beep(1000, ms)
    except ImportError:
        sys.stdout.write("\a")
        sys.stdout.flush()


def log(msg, name=""):
    prefix = f"[{name}] " if name else ""
    with _print_lock:
        print(time.strftime("[%H:%M:%S]"), prefix + msg, flush=True)


class Actions:
    def __init__(self, screen, controls, keys, timing, lock=None, name=""):
        self.screen = screen
        self.ctl = controls
        self.keys = keys
        self.t = timing
        self.lock = lock or InputLock()
        self.name = name
        self.priority = 0

    def log(self, msg):
        log(msg, self.name)

    # ---- input gate ---------------------------------------------------
    @contextmanager
    def input(self):
        """Exclusive use of mouse + keyboard, with this client focused."""
        with self.lock.hold(self.priority):
            if not focus(self.screen.window):
                raise FocusError(f"could not focus {self.screen.window.title}")
            yield

    @contextmanager
    def urgent(self):
        """Jump the input queue (used when fleeing)."""
        old, self.priority = self.priority, 10
        try:
            yield
        finally:
            self.priority = old

    # ---- helpers ------------------------------------------------------
    def key(self, action):
        """Send a hotkey by name from config.KEYS."""
        with self.input():
            self.ctl.hotkey(*self.keys[action])

    def keys_each(self, action):
        with self.input():
            self.ctl.press_each(*self.keys[action])

    def click(self, match, button="left", modifier=None):
        with self.input():
            self.ctl.click(*match.center, button=button, modifier=modifier)

    def find_fresh(self, name):
        """Take a new screenshot and look for one template."""
        return self.screen.grab().find(name)

    # ---- drones -------------------------------------------------------
    def recall_drones(self, attempts=3):
        """Shift+R, then check the idle-drone list is gone and retry if not."""
        for i in range(1, attempts + 1):
            self.key("recall_drones")
            time.sleep(self.t["recall_retry"])
            if not self.find_fresh("drones_idle"):
                return True
            self.log(f"drones still out after recall attempt {i}/{attempts}")
        return False

    def launch_drones(self):
        self.key("launch_drones")

    def lock_and_engage(self, match):
        self.click(match, modifier=self.keys["lock_modifier"])
        time.sleep(self.t["lock_target"])          # no input lock held while waiting
        self.key("drones_engage")
        self.log(f"drones engaging {match.name}")

    def bookmark(self):
        with self.input():                          # dialog must not lose focus
            self.ctl.hotkey(*self.keys["bookmark"])
            time.sleep(0.3)
            self.ctl.hotkey(*self.keys["confirm"])

    # ---- travel -------------------------------------------------------
    def wait_for_warp(self):
        deadline = time.time() + self.t["warp_timeout"]
        while time.time() < deadline:
            if not self.find_fresh("warping"):
                return True
            time.sleep(self.t["warp_poll"])
        self.log("warp did not finish in time")
        return False

    def dock_at_safe_station(self):
        station = self.find_fresh("safe_station")
        if not station:
            self.log("safe station not found in overview!")
            return False
        self.click(station)
        self.key("prop_module")
        self.key("approach")
        time.sleep(self.t["align_before_dock"])
        self.key("dock")
        return True

    def undock_and_prepare(self):
        button = self.find_fresh("undock")
        if not button:
            self.log("undock button not found")
            return False
        self.click(button)
        self.log("undocking")
        time.sleep(self.t["after_undock"])
        self.key("stop_ship")
        time.sleep(self.t["before_modules"])
        self.launch_drones()
        self.keys_each("tank_modules")
        return True

    def flee(self, stay_seconds):
        """Recall drones and dock (ahead of other bots), wait, undock again."""
        with self.urgent():
            self.recall_drones()
            docked = self.dock_at_safe_station()
        if docked:
            self.log(f"docking, waiting {stay_seconds}s")
            time.sleep(stay_seconds)
            self.undock_and_prepare()

    def warp_to_next_site(self):
        """Returns 'ok', 'no_site', 'no_menu' or 'no_orbit'."""
        site = self.find_fresh("rat_site")
        if not site:
            return "no_site"

        # right-click menu -> "Warp to": hold input the whole time so another
        # bot switching focus can't close the menu
        with self.input():
            self.ctl.click(*site.center, button="right")
            time.sleep(self.t["menu_open"])
            warp = self.find_fresh("warp_to")
            if not warp:
                return "no_menu"
            self.ctl.click(*warp.center)
        self.log("warping to new site")
        time.sleep(self.t["warp_start"])
        self.wait_for_warp()

        orbit = self.find_fresh("orbit_point")
        if not orbit:
            return "no_orbit"
        self.click(orbit)
        self.key("orbit")
        self.key("prop_module")
        self.launch_drones()
        self.log("arrived, orbiting and drones launched")
        return "ok"
