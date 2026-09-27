"""One mouse + one keyboard, many bots.

Every burst of input (focus window -> click / press keys) must hold this
lock, so two bots can never interleave keystrokes. Bots only hold it for the
fraction of a second the input takes - screenshots, template matching and
all the long waits (docked, aligning, locking) happen outside the lock.

Waiting bots are served by priority first (a bot fleeing from a hostile goes
ahead of one that just wants to change site), then first-come-first-served.
The lock is re-entrant, so an action can call other actions while holding it.
"""
import heapq
import itertools
import threading
from contextlib import contextmanager


class InputLock:
    def __init__(self):
        self._cond = threading.Condition()
        self._owner = None
        self._depth = 0
        self._queue = []
        self._seq = itertools.count()

    @contextmanager
    def hold(self, priority=0):
        me = threading.get_ident()
        with self._cond:
            if self._owner == me:
                self._depth += 1
            else:
                ticket = (-priority, next(self._seq), me)
                heapq.heappush(self._queue, ticket)
                while self._owner is not None or self._queue[0] != ticket:
                    self._cond.wait()
                heapq.heappop(self._queue)
                self._owner, self._depth = me, 1
        try:
            yield
        finally:
            with self._cond:
                self._depth -= 1
                if self._depth == 0:
                    self._owner = None
                    self._cond.notify_all()
