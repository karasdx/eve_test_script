"""One mouse + one keyboard, many bots.

Every burst of input (focus window -> click / press keys) must hold this
lock, so two bots can never interleave keystrokes. Bots only hold it for the
fraction of a second the input takes - screenshots, template matching and
all the long waits (docked, aligning, locking) happen outside the lock.

Waiting bots are served by priority first (a bot fleeing from a hostile goes
ahead of one that just wants to change site), then first-come-first-served.
The lock is re-entrant, so an action can call other actions while holding it.

A multi-step operation (changing site, fleeing) runs inside a session(): from
start to finish, other bots only get the mouse/keyboard if their priority is
HIGHER than the session's. So a site change is never interrupted by another
account's routine clicks, but a bot fleeing from a hostile still gets through.
Fleeing sessions (level >= URGENT) never block each other.
"""
import threading
from contextlib import contextmanager

SITE = 5        # changing site: finish it before other accounts get routine input
URGENT = 10     # fleeing from a hostile: goes ahead of everything


class InputLock:
    def __init__(self):
        self._cond = threading.Condition()
        self._owner = None
        self._depth = 0
        self._queue = []                # [(-priority, seq, thread id)]
        self._seq = 0
        self._sessions = {}             # thread id -> [levels] (nested sessions)

    # ---- sessions -----------------------------------------------------
    def _level(self, tid):
        return max(self._sessions.get(tid) or [-1])

    def _others(self, me):
        return [max(levels) for tid, levels in self._sessions.items() if tid != me and levels]

    def _blocked(self, priority, me):
        """True while another bot's session outranks this priority."""
        return priority < URGENT and any(priority <= lvl for lvl in self._others(me))

    @contextmanager
    def session(self, level):
        """Reserve the mouse/keyboard for a whole operation (see module doc)."""
        me = threading.get_ident()
        with self._cond:
            if self._level(me) < 0:     # a nested session doesn't wait again
                # one routine session at a time; urgent ones always start
                while level < URGENT and any(lvl >= level for lvl in self._others(me)):
                    self._cond.wait()
            self._sessions.setdefault(me, []).append(level)
        try:
            yield
        finally:
            with self._cond:
                levels = self._sessions[me]
                levels.pop()
                if not levels:
                    del self._sessions[me]
                self._cond.notify_all()

    # ---- single bursts ------------------------------------------------
    def _next_ticket(self):
        """Highest-priority waiting ticket that no session is holding back."""
        for ticket in sorted(self._queue):
            if not self._blocked(-ticket[0], ticket[2]):
                return ticket
        return None

    @contextmanager
    def hold(self, priority=0):
        me = threading.get_ident()
        with self._cond:
            if self._owner == me:
                self._depth += 1
            else:
                priority = max(priority, self._level(me))
                self._seq += 1
                ticket = (-priority, self._seq, me)
                self._queue.append(ticket)
                while self._owner is not None or self._next_ticket() != ticket:
                    self._cond.wait()
                self._queue.remove(ticket)
                self._owner, self._depth = me, 1
        try:
            yield
        finally:
            with self._cond:
                self._depth -= 1
                if self._depth == 0:
                    self._owner = None
                    self._cond.notify_all()
