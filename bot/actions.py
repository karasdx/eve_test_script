"""Game actions built from vision + controls. Each is one clear step.

All mouse/keyboard use goes through self.input(), which takes the shared
InputLock and focuses this bot's client first - so several bots can run at
once without their clicks and keys getting mixed up.

Multi-step operations (fleeing, changing site) run inside self.operation():
other accounts wait until the whole operation is finished, except one that
is fleeing from a hostile, which always goes first.
"""
import sys
import threading
import time
from contextlib import contextmanager

from .input_lock import SITE, URGENT, InputLock
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
    def __init__(self, screen, controls, keys, timing, lock=None, name="", danger=()):
        self.screen = screen
        self.ctl = controls
        self.keys = keys
        self.t = timing
        self.lock = lock or InputLock()
        self.name = name
        self.danger = list(danger)      # templates that mean "run" (config.DANGER)
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
    def operation(self, level):
        """Run a multi-step operation start to finish: other accounts don't get
        the mouse/keyboard until it ends, unless their need is more urgent
        (SITE = changing site, URGENT = fleeing; see input_lock.py)."""
        old, self.priority = self.priority, max(self.priority, level)
        try:
            with self.lock.session(level):
                yield
        finally:
            self.priority = old

    def retry(self, step, tries=3):
        """Run one input step; if the client couldn't be focused, try again
        instead of abandoning a half-finished operation."""
        for i in range(1, tries + 1):
            try:
                return step()
            except FocusError as e:
                if i == tries:
                    raise
                self.log(f"{e} - retrying ({i}/{tries})")
                time.sleep(1)

    # ---- helpers ------------------------------------------------------
    def key(self, action):
        """Send a hotkey by name from config.KEYS."""
        with self.input():
            self.ctl.hotkey(*self.keys[action])

    def keys_each(self, action):
        with self.input():
            self.ctl.press_each(*self.keys[action])

    def press_esc(self):
        with self.input():
            self.ctl.hotkey("esc")

    def click(self, match, button="left", modifier=None):
        with self.input():
            self.ctl.click(*match.center, button=button, modifier=modifier)

    def find_fresh(self, name):
        """Take a new screenshot and look for one template."""
        return self.screen.grab().find(name)

    # ---- danger -------------------------------------------------------
    def danger_on_screen(self):
        return self.screen.grab().find_any(self.danger) if self.danger else None

    def watch(self, seconds):
        """Wait, checking for danger the whole time. Returns the danger match
        (and stops waiting at once) or None."""
        deadline = time.time() + seconds
        while True:
            hit = self.danger_on_screen()
            if hit or time.time() >= deadline:
                return hit
            time.sleep(min(self.t["danger_poll"], max(0.0, deadline - time.time())))

    def wait_for(self, name, seconds):
        """Poll until a template shows up, checking for danger first each time.
        Returns ('found', match), ('danger', match) or ('timeout', None)."""
        deadline = time.time() + seconds
        while True:
            s = self.screen.grab()
            hit = s.find_any(self.danger) if self.danger else None
            if hit:
                return "danger", hit
            m = s.find(name)
            if m:
                return "found", m
            if time.time() >= deadline:
                return "timeout", None
            time.sleep(self.t["danger_poll"])

    # ---- drones -------------------------------------------------------
    def recall_drones(self, attempts=3):
        """Shift+R, then check the idle-drone list is gone and retry if not."""
        for i in range(1, attempts + 1):
            self.retry(lambda: self.key("recall_drones"))
            time.sleep(self.t["recall_retry"])
            if not self.find_fresh("drones_idle"):
                return True
            self.log(f"drones still out after recall attempt {i}/{attempts}")
        return False

    def launch_drones(self, attempts=3, already_pressed=False):
        """Shift+F, then check the drones are in space (idle-drone list shows
        up) and press it again if not. Returns 'ok', 'danger' or 'failed'."""
        for i in range(1, attempts + 1):
            if i > 1 or not already_pressed:
                self.retry(lambda: self.key("launch_drones"))
            state, _ = self.wait_for("drones_idle", self.t["drones_launch"])
            if state != "timeout":
                return "ok" if state == "found" else "danger"
            self.log(f"drones not out after launch attempt {i}/{attempts}")
        return "failed"

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
        """Wait until the warp ends. Returns (finished, danger seen meanwhile)."""
        danger = None
        deadline = time.time() + self.t["warp_timeout"]
        while time.time() < deadline:
            s = self.screen.grab()
            danger = danger or (s.find_any(self.danger) if self.danger else None)
            if not s.find("warping"):
                return True, danger
            time.sleep(self.t["warp_poll"])
        self.log("warp did not finish in time")
        return False, danger

    def is_docked(self):
        return self.find_fresh("undock") is not None

    def dock_at_safe_station(self):
        """Approach + dock, then wait until we really are docked (undock button
        visible), pressing dock again if needed."""
        station = self.find_fresh("safe_station")
        if not station:
            self.log("safe station not found in overview!")
            return False

        def start():
            with self.input():                      # one burst: select, prop, approach
                self.ctl.click(*station.center)
                self.ctl.hotkey(*self.keys["prop_module"])
                self.ctl.hotkey(*self.keys["approach"])
        self.retry(start)
        time.sleep(self.t["align_before_dock"])

        deadline = time.time() + self.t["dock_timeout"]
        while time.time() < deadline:
            self.retry(lambda: self.key("dock"))
            for _ in range(int(self.t["dock_retry"])):
                time.sleep(1)
                if self.is_docked():
                    self.log("docked")
                    return True
        self.log("still not docked - giving up on this attempt")
        return False

    def undock_and_prepare(self):
        """Undock, stop, launch drones, tank on - all before other accounts move."""
        with self.operation(SITE):
            button = self.find_fresh("undock")
            if not button:
                self.log("undock button not found")
                return False
            self.retry(lambda: self.click(button))
            self.log("undocking")
            time.sleep(self.t["after_undock"])
            self.retry(lambda: self.key("stop_ship"))
            time.sleep(self.t["before_modules"])
            self.launch_drones()
            self.retry(lambda: self.keys_each("tank_modules"))
            return True

    def flee(self, stay_seconds):
        """Recall drones and dock - ahead of everything else, and nobody else
        gets routine input until we are docked. Then wait and undock again."""
        with self.operation(URGENT):
            self.recall_drones()
            docked = self.dock_at_safe_station()
            if not docked:                          # one more go before giving up
                docked = self.dock_at_safe_station()
        if docked:
            self.log(f"docked, waiting {stay_seconds}s")
            time.sleep(stay_seconds)
            self.undock_and_prepare()

    def change_site(self):
        """The whole site change as ONE operation: recall drones, warp, land,
        orbit, launch drones (checked). Other accounts only get routine input
        once it is finished. Danger is checked throughout.

        Returns 'ok', 'danger', 'no_site', 'no_menu', 'no_orbit' or 'no_drones'.
        On 'no_site' / 'no_menu' the drones have been launched again."""
        with self.operation(SITE):
            self.recall_drones()
            if self.watch(self.t["drones_return"]):
                return "danger"

            site = self.find_fresh("rat_site")
            if not site:
                self.launch_drones()
                return "no_site"

            # right-click menu -> "Warp to" in one burst, so nothing can close the menu
            def warp():
                with self.input():
                    self.ctl.click(*site.center, button="right")
                    time.sleep(self.t["menu_open"])
                    item = self.find_fresh("warp_to")
                    if item:
                        self.ctl.click(*item.center)
                    return item is not None
            if not self.retry(warp):
                self.retry(lambda: self.press_esc())  # close the menu if it is open
                self.launch_drones()
                return "no_menu"
            self.log("warping to new site")

            danger = self.watch(self.t["warp_start"])
            _, seen = self.wait_for_warp()
            if danger or seen:
                return "danger"                     # landed - now run

            # landing: the overview can take a moment to show the orbit point
            state, orbit = self.wait_for("orbit_point", self.t["orbit_wait"])
            if state == "danger":
                return "danger"
            if state == "timeout":
                return "no_orbit"

            def arrive():                           # one burst, nothing in between
                with self.input():
                    self.ctl.click(*orbit.center)
                    self.ctl.hotkey(*self.keys["orbit"])
                    self.ctl.hotkey(*self.keys["prop_module"])
                    self.ctl.hotkey(*self.keys["launch_drones"])
            self.retry(arrive)

            result = self.launch_drones(already_pressed=True)
            if result != "ok":
                return "danger" if result == "danger" else "no_drones"
            self.log("arrived: orbiting, drones out")
            return "ok"
