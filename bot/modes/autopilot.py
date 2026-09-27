"""Gate-to-gate travel (replaces auto_pilot.py)."""
import random
import time

from ..window import FocusError


class Autopilot:
    def __init__(self, actions, cfg):
        self.a = actions
        self.cfg = cfg
        self.misses = 0

    def run(self):
        self.a.log("autopilot started")
        while True:
            time.sleep(random.uniform(1, 3))
            try:
                if self.step():
                    return
            except FocusError as e:
                self.a.log(f"{e} - retrying")

    def step(self):
        """One check; returns True when the destination is reached."""
        t = self.cfg.TIMING
        if self.a.find_fresh("warping"):
            return False

        time.sleep(t["autopilot_settle"])      # jump / session change
        gate = self.a.find_fresh("target_gate")
        if gate:
            self.misses = 0
            self.a.click(gate)
            self.a.key("approach")
            time.sleep(1)
            self.a.key("dock")                 # D = jump on a gate
            self.a.log("jumping")
            return False

        self.misses += 1
        if self.misses > t["autopilot_max_misses"]:
            self.a.log("no more gates - destination reached")
            self.a.key("autopilot_end")
            return True
        return False
