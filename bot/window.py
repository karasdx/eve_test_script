"""Finding, focusing and laying out EVE client windows."""
import time


class FocusError(RuntimeError):
    """The client could not be brought to the front - input is skipped so
    keystrokes never land in another bot's client."""


def find_window(title):
    import pygetwindow as gw

    windows = gw.getWindowsWithTitle(title)
    exact = [w for w in windows if w.title == title]
    windows = exact or windows
    if not windows:
        raise SystemExit(f'No window titled "{title}" found - is the client running '
                         f"and logged in to that character?")
    return windows[0]


def _is_active(window):
    try:
        return bool(window.isActive)
    except Exception:
        return False


def _force_foreground(window):
    """Windows only lets the foreground process switch focus; tapping Alt first
    is the standard workaround when activate() is refused."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        user32.keybd_event(0x12, 0, 0, 0)        # Alt down
        user32.keybd_event(0x12, 0, 2, 0)        # Alt up
        user32.ShowWindow(window._hWnd, 5)       # SW_SHOW (keeps maximised state)
        user32.SetForegroundWindow(window._hWnd)
    except Exception:
        pass


def focus(window, tries=3):
    """Bring the client to the front and confirm it. Returns True on success."""
    for _ in range(tries):
        if _is_active(window):
            return True
        try:
            if window.isMinimized:
                window.restore()
            window.activate()
        except Exception:
            pass                    # pygetwindow sometimes raises even on success
        time.sleep(0.15)
        if _is_active(window):
            return True
        _force_foreground(window)
        time.sleep(0.15)
    return _is_active(window)


def overlapping(windows):
    """Pairs of windows whose rectangles overlap (screen capture would see the
    other client on top). Minimised windows are reported too."""
    problems = []
    for w in windows:
        if getattr(w, "isMinimized", False):
            problems.append(f'"{w.title}" is minimised - it cannot be captured')
    for i, a in enumerate(windows):
        for b in windows[i + 1:]:
            if (a.left < b.left + b.width and b.left < a.left + a.width and
                    a.top < b.top + b.height and b.top < a.top + a.height):
                problems.append(f'"{a.title}" overlaps "{b.title}"')
    return problems
