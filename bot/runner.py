"""Run several bots at once, one thread per client.

Threads (not processes) so they can share one InputLock. Screen capture and
OpenCV matching release the GIL, so the bots really do look at their screens
in parallel; only mouse/keyboard bursts take turns.
"""
import threading
import time
import traceback

from .actions import log


def run_bots(bots, stagger=0.7):
    """bots: list of (name, callable). Returns when all finish, one crashes the
    fail-safe, or Ctrl+C is pressed."""
    stop = threading.Event()

    def worker(name, fn):
        try:
            fn()
            log("finished", name)
        except Exception as e:
            if type(e).__name__ == "FailSafeException":
                log("mouse moved to a screen corner - stopping ALL bots", name)
                stop.set()
            else:
                log(f"crashed: {e!r} (other bots keep running)", name)
                traceback.print_exc()

    threads = []
    for name, fn in bots:
        t = threading.Thread(target=worker, args=(name, fn), name=name, daemon=True)
        t.start()
        threads.append(t)
        time.sleep(stagger)     # spread the ticks so bots don't all wake together

    while not stop.is_set() and any(t.is_alive() for t in threads):
        stop.wait(0.5)
