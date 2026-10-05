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
    def recall_drones(self, attempts=3, already_pressed=False):
        """Shift+R, then wait for the header to read (0/5); press it again if
        the drones aren't back in time. Returns True once they are all home."""
        for i in range(1, attempts + 1):
            if i > 1 or not already_pressed:
                self.retry(lambda: self.key("recall_drones"))
            if self.wait_drones("home", self.t["recall_wait"]) == "home":
                return True
            self.log(f"drones not back after recall attempt {i}/{attempts}")
        return False

    def drones_state(self, s=None):
        """Read the "Drones in Space" header: 'out' = (5/5), 'home' = (0/5),
        None = neither visible. The two differ by one digit, so both are
        checked and the closer match wins."""
        s = s or self.screen.grab()
        out, home = s.find("drones_out"), s.find("drones_home")
        if out and (not home or out.score > home.score):
            return "out"
        return "home" if home else None

    def wait_drones(self, want, seconds, watch_danger=False):
        """Poll until drones_state() == want. Returns want, 'danger' or None."""
        deadline = time.time() + seconds
        while True:
            s = self.screen.grab()
            if watch_danger and self.danger and s.find_any(self.danger):
                return "danger"
            if self.drones_state(s) == want:
                return want
            if time.time() >= deadline:
                return None
            time.sleep(self.t["danger_poll"])

    def launch_drones(self, attempts=3, already_pressed=False):
        """Shift+F, then check the header reads (5/5) and press it again if
        not. Returns 'ok', 'danger' or 'failed'."""
        for i in range(1, attempts + 1):
            if i > 1 or not already_pressed:
                self.retry(lambda: self.key("launch_drones"))
            state = self.wait_drones("out", self.t["drones_launch"], watch_danger=True)
            if state:
                return "ok" if state == "out" else "danger"
            self.log(f"drones not out (5/5) after launch attempt {i}/{attempts}")
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
        """Keep checking the "warping" image: first wait for it to show up (the
        ship aligns before it enters warp), then until it is gone, then
        settle for after_warp seconds. Returns (finished, danger seen meanwhile)."""
        danger = None
        started = False
        start_by = time.time() + self.t["warp_start"]
        deadline = time.time() + self.t["warp_timeout"]
        while time.time() < deadline:
            s = self.screen.grab()
            danger = danger or (s.find_any(self.danger) if self.danger else None)
            if s.find("warping"):
                started = True
            elif started:
                self.log("out of warp")
                break
            elif time.time() >= start_by:
                self.log("never saw the warp start - carrying on")
                break
            time.sleep(self.t["warp_poll"])
        else:
            self.log("warp did not finish in time")
            return False, danger
        hit = self.watch(self.t["after_warp"])
        return True, danger or hit

    def is_docked(self):
        return self.find_fresh("undock") is not None

    def dock_at_safe_station(self, recall=True):
        """Align to the safe station and recall drones at the same time, wait
        until the drones are home (0/5), then warp + dock. Confirms we really
        are docked (undock button visible), pressing dock again if needed."""
        station = self.find_fresh("safe_station")
        if not station:
            self.log("safe station not found in overview!")
            if recall:
                self.recall_drones()
            return False

        def start():
            with self.input():                      # one burst: select, prop, align, recall
                self.ctl.click(*station.center)
                self.ctl.hotkey(*self.keys["prop_module"])
                self.ctl.hotkey(*self.keys["approach"])
                if recall:
                    self.ctl.hotkey(*self.keys["recall_drones"])
        self.retry(start)
        self.log("aligning to safe station" + (", recalling drones" if recall else ""))

        if recall and not self.recall_drones(already_pressed=True):
            self.log("drones not back (0/5) - warping to station anyway")

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

    def undock(self):
        """Undock, stop, tank on - no drones (they launch at the site).
        Returns 'ok', 'danger' or 'failed'."""
        button = self.find_fresh("undock")
        if not button:
            self.log("undock button not found")
            return "failed"
        self.retry(lambda: self.click(button))
        self.log("undocking")
        if self.watch(self.t["after_undock"]):
            return "danger"

        def buttons():                              # one burst: stop, tank on
            with self.input():
                self.ctl.hotkey(*self.keys["stop_ship"])
                self.ctl.press_each(*self.keys["tank_modules"])
        self.retry(buttons)
        return "ok"

    def flee(self, stay_seconds):
        """Recall drones and dock - ahead of everything else, and nobody else
        gets routine input until we are docked. Then stay docked a while.
        Returns True once docked and the wait is over."""
        with self.operation(URGENT):
            docked = self.dock_at_safe_station()
            if not docked:                          # one more go before giving up
                docked = self.dock_at_safe_station(recall=self.drones_state() != "home")
        if docked:
            self.log(f"docked, waiting {stay_seconds}s")
            time.sleep(stay_seconds)
        return docked

    def undock_to_site(self):
        """Undock and, if no enemies, warp straight to a new site - one operation.
        Returns 'no_undock' or the result of change_site()."""
        with self.operation(SITE):
            result = self.undock()
            if result == "failed":
                return "no_undock"
            if result == "danger" or self.danger_on_screen():
                return "danger"
            return self.change_site(recall=False)

    def change_site(self, recall=True):
        """The whole site change as ONE operation: recall drones, warp, land,
        orbit, launch drones (checked). Other accounts only get routine input
        once it is finished. Danger is checked throughout.
        recall=False: drones are already in the bay (just undocked).

        Returns 'ok', 'danger', 'no_site', 'no_menu', 'no_orbit' or 'no_drones'.
        On 'no_menu' the drones are launched (no further warp attempts);
        on 'no_site' they are relaunched if they were out."""
        with self.operation(SITE):
            if recall:
                home = self.recall_drones()         # waits for (0/5)
                if self.watch(0 if home else self.t["drones_return"]):
                    return "danger"

            site = self.find_fresh("rat_site")
            if not site:
                if recall:
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
                self.launch_drones()                  # no warp: just fight here
                return "no_menu"
            self.log("warping to new site")

            _, seen = self.wait_for_warp()          # landed + after_warp seconds
            if seen:
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

            result = self.check_orbit()
            if result != "ok":
                return result
            self.log("arrived: orbiting, drones out")
            return "ok"

    def check_orbit(self, attempts=3):
        """Make sure the HUD says "Orbiting"; if not, click the orbit point and
        press orbit again. Returns 'ok', 'danger' or 'no_orbit'."""
        for i in range(1, attempts + 1):
            state, _ = self.wait_for("orbiting", self.t["orbit_check"])
            if state != "timeout":
                return "ok" if state == "found" else "danger"
            self.log(f"not orbiting - orbit again ({i}/{attempts})")
            point = self.find_fresh("orbit_point")
            if not point:
                return "no_orbit"

            def orbit():                            # orbit only: F1 would toggle prop off
                with self.input():
                    self.ctl.click(*point.center)
                    self.ctl.hotkey(*self.keys["orbit"])
            self.retry(orbit)
        state, _ = self.wait_for("orbiting", self.t["orbit_check"])
        return {"found": "ok", "danger": "danger"}.get(state, "no_orbit")
