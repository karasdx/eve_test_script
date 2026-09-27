"""Auto-ratting loop (replaces auto_rat.py / auto_rat_2.py / main.py).

Each tick takes ONE screenshot and decides, in priority order:
  1. danger in local / on grid   -> recall drones, dock, wait, undock
  2. a rat is applying ewar      -> lock it and send drones
  3. boss wreck (once per site)  -> bookmark it
  4. drones idle                 -> count; after N ticks lock remaining
                                    targets, or move to the next site
"""
import time

from ..actions import beep
from ..window import FocusError


class Ratting:
    def __init__(self, actions, cfg):
        self.a = actions
        self.screen = actions.screen
        self.cfg = cfg
        self.idle_ticks = 0
        self.boss_bookmarked = False
        self.limit = cfg.TIMING["idle_ticks_limit"]

    def run(self):
        self.a.log("ratting started")
        while True:
            try:
                self.tick()
            except FocusError as e:
                self.a.log(f"{e} - skipping this tick")
            time.sleep(self.cfg.TICK_SECONDS)

    def tick(self):
        s = self.screen.grab()

        hit = s.find_any(self.cfg.DANGER)
        if hit:
            beep()
            self.a.log(f"DANGER: {hit.name} ({hit.score:.2f}) - running to station")
            self.a.flee(self.cfg.TIMING["docked_wait_danger"])
            self.idle_ticks = self.limit + 1        # re-check targets right away
            return

        hit = s.find_any(self.cfg.EWAR)
        if hit:
            self.a.log(f"ewar on us: {hit.name}")
            self.a.lock_and_engage(hit)
            return

        if not self.boss_bookmarked and s.visible("boss_wreck"):
            self.a.log("boss wreck found - bookmarking")
            self.a.bookmark()
            self.boss_bookmarked = True

        if s.visible("drones_idle"):
            self.idle_ticks += 1
            if self.idle_ticks > self.limit:
                self.idle_ticks = 0
                self.on_drones_idle()

    def on_drones_idle(self):
        targets = self.screen.grab().find_all(self.cfg.UNLOCKED)
        if targets:
            for t in targets:
                self.a.lock_and_engage(t)
            return

        self.a.log("site cleared")
        self.boss_bookmarked = False
        self.a.recall_drones()
        time.sleep(self.cfg.TIMING["drones_return"])
        beep()

        result = self.a.warp_to_next_site()
        if result == "ok":
            return
        if result == "no_orbit":
            self.a.log("could not orbit - docking up")
            self.a.flee(self.cfg.TIMING["docked_wait_fail"])
            self.idle_ticks = self.limit + 1
        elif result == "no_menu":
            self.a.log("warp menu not found - relaunching drones")
            time.sleep(5)
            self.a.launch_drones()
            time.sleep(3)
            self.a.key("drones_engage")
        else:
            self.a.log("no new site found - relaunching drones")
            self.a.launch_drones()
