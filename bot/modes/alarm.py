"""Local alarm for one or more clients (replaces local_alarm.py / auto_run.py)."""
import time

from ..actions import beep, log


class Alarm:
    def __init__(self, screens, cfg, once=False):
        self.screens = screens          # {window title: Screen}
        self.cfg = cfg
        self.once = once

    def run(self):
        log(f"watching {len(self.screens)} client(s)")
        while True:
            for title, screen in self.screens.items():
                hit = screen.grab().find_any(self.cfg.DANGER)
                if hit:
                    beep(1000)
                    log(f"{title}: {hit.name} ({hit.score:.2f})")
                    if self.once:
                        return
                    time.sleep(self.cfg.TIMING["alarm_cooldown"])
            time.sleep(self.cfg.TICK_SECONDS)
