"""Auto-ratting loop (replaces auto_rat.py / auto_rat_2.py / main.py).

Each tick takes ONE screenshot and decides, in priority order:
  1. danger in local / on grid   -> recall drones, dock, wait, undock and
                                    warp straight to a new site (drones are
                                    launched only after landing there)
  2. a rat is applying ewar      -> lock it and send drones
  3. boss wreck (once per site)  -> bookmark it
  4. drones idle                 -> count; after N ticks lock remaining
                                    targets, or move to the next site

Changing site is one uninterrupted operation (recall -> warp -> land -> orbit
-> drones out, checked). Danger is still watched the whole time and wins:
if it shows up, the site change stops and the bot flees.
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
        self.pending = None             # "undock" / "site": try again at pending_at
        self.pending_at = 0.0

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
            self.a.log(f"DANGER: {hit.name} ({hit.score:.2f})")
            self.handle("danger")
            return

        hit = s.find_any(self.cfg.EWAR)
        if hit:
            self.a.log(f"ewar on us: {hit.name}")
            self.a.lock_and_engage(hit)
            return

        if self.pending:                            # undock / warp that couldn't happen yet
            if time.time() >= self.pending_at:
                action, self.pending = self.pending, None
                self.handle(self.a.undock_to_site() if action == "undock"
                            else self.a.change_site(recall=False), drones_out=False)
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

        self.a.log("site cleared - changing site")
        self.boss_bookmarked = False
        beep()

        # one uninterrupted operation; returns only when it is finished
        self.handle(self.a.change_site(), drones_out=True)

    def later(self, action):
        wait = self.cfg.TIMING["site_retry"]
        self.a.log(f"trying again in {wait}s")
        self.pending, self.pending_at = action, time.time() + wait

    def handle(self, result, drones_out=True):
        """Act on the result of a site change. Danger / failed landing -> dock,
        wait, then undock and warp straight to a new site (no drones until we
        land there); repeats if the same happens again."""
        t = self.cfg.TIMING
        while result != "ok":
            if result in ("danger", "no_orbit", "no_drones"):
                beep()
                self.a.log({"danger": "DANGER - running to station",
                            "no_orbit": "orbit point not found after landing - docking up",
                            "no_drones": "drones did not launch - docking up"}[result])
                stay = t["docked_wait_danger"] if result == "danger" else t["docked_wait_fail"]
                if not self.a.flee(stay):
                    self.a.log("could not dock - will warp to a site once it is clear")
                    self.later("site")
                    return
                self.idle_ticks = 0
                self.boss_bookmarked = False
                result = self.a.undock_to_site()
                drones_out = False
            elif result == "no_undock":
                self.a.log("could not undock")
                self.later("undock")
                return
            elif result == "no_menu":               # drones launched where we are - no retry
                self.a.log("warp menu not found - drones launched, staying here")
                self.a.key("drones_engage")
                return
            elif drones_out:                        # still at the old site, drones relaunched
                self.a.log("new site not found - drones relaunched")
                return
            else:                                   # just undocked: no drones out yet
                self.a.log("new site not found")
                self.later("site")
                return
