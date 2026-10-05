"""Screen capture and template matching.

Resource savings compared with the old scripts:
  * mss captures only the game window and is much faster than pyautogui.screenshot
  * one capture per tick is shared by every search (no repeated screenshots)
  * grayscale matching for templates that don't need colour (~3x less work)
  * optional search regions per template (config.TEMPLATES)
  * searches stop at the first hit when checking a list (find_any)
  * templates are loaded and validated once at start-up
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Template:
    name: str
    bgr: np.ndarray
    gray: np.ndarray
    threshold: float
    colour: bool
    region: tuple | None

    @property
    def size(self):
        h, w = self.gray.shape[:2]
        return w, h


@dataclass
class Match:
    name: str
    x: int          # top-left, absolute screen coordinates
    y: int
    w: int
    h: int
    score: float

    @property
    def center(self):
        return self.x + self.w // 2, self.y + self.h // 2


def load_templates(image_dir, specs, ui_scale=100, images_scale=100):
    """Load every template, sized for the game's UI scaling.

    ui_scale     : the client's UI scaling in %, e.g. 100 / 125 / 150
    images_scale : the UI scaling the pictures in image_dir were taken at
    A picture in image_dir/<ui_scale>/ (e.g. images/125/drone.png) is used
    as-is; otherwise the normal picture is resized by ui_scale / images_scale.
    """
    factor = ui_scale / images_scale
    own_dir = image_dir / str(ui_scale)
    templates = {}
    missing = []
    for name, (filename, threshold, colour, region) in specs.items():
        own = own_dir / filename
        path, f = (own, 1.0) if own.exists() else (image_dir / filename, factor)
        bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if bgr is None:           # cv2.imread fails silently - check it here
            missing.append(str(path))
            continue
        if f != 1.0:
            h, w = bgr.shape[:2]
            bgr = cv2.resize(bgr, (max(1, round(w * f)), max(1, round(h * f))),
                             interpolation=cv2.INTER_AREA if f < 1 else cv2.INTER_CUBIC)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        templates[name] = Template(name, bgr, gray, threshold, colour, region)
    if missing:
        raise SystemExit("Missing template images:\n  " + "\n  ".join(missing))
    return templates


class Screen:
    """Holds the latest capture of one game window and searches it."""

    def __init__(self, window, templates):
        self.window = window
        self.templates = templates
        self._sct = None
        self.bgr = None
        self._gray = None
        self.left = self.top = 0

    # ---- capture ------------------------------------------------------
    def grab(self):
        w = self.window
        self.left, self.top = w.left, w.top
        box = {"left": w.left, "top": w.top, "width": w.width, "height": w.height}
        self.bgr = self._capture(box)
        self._gray = None
        return self

    def _capture(self, box):
        try:
            if self._sct is None:
                import mss
                self._sct = mss.mss()
            shot = np.asarray(self._sct.grab(box))          # BGRA
            return cv2.cvtColor(shot, cv2.COLOR_BGRA2BGR)
        except ImportError:
            import pyautogui
            shot = pyautogui.screenshot(region=(box["left"], box["top"],
                                                box["width"], box["height"]))
            return cv2.cvtColor(np.asarray(shot), cv2.COLOR_RGB2BGR)

    @property
    def gray(self):
        if self._gray is None:
            self._gray = cv2.cvtColor(self.bgr, cv2.COLOR_BGR2GRAY)
        return self._gray

    # ---- search -------------------------------------------------------
    def find(self, name, threshold=None):
        """Best match for one template, or None."""
        t = self.templates[name]
        img = self.bgr if t.colour else self.gray
        pat = t.bgr if t.colour else t.gray

        ox = oy = 0
        if t.region:
            H, W = img.shape[:2]
            x0, y0, x1, y1 = t.region
            ox, oy = int(x0 * W), int(y0 * H)
            img = img[oy:int(y1 * H), ox:int(x1 * W)]

        th, tw = pat.shape[:2]
        if img.shape[0] < th or img.shape[1] < tw:
            return None

        result = cv2.matchTemplate(img, pat, cv2.TM_CCOEFF_NORMED)
        _, score, _, (x, y) = cv2.minMaxLoc(result)
        if score < (t.threshold if threshold is None else threshold):
            return None
        return Match(name, self.left + ox + x, self.top + oy + y, tw, th, float(score))

    def find_any(self, names):
        """First template in the list that is on screen (priority order)."""
        for name in names:
            m = self.find(name)
            if m:
                return m
        return None

    def find_all(self, names):
        return [m for m in (self.find(n) for n in names) if m]

    def visible(self, name):
        return self.find(name) is not None
