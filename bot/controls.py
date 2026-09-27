"""Keyboard and mouse.

Why Shift+R sometimes did nothing in the old scripts:
  1. pyautogui.press() sends key-down and key-up back to back. EVE only reads
     input once per rendered frame, and background / low-FPS clients easily
     miss a key that was down for less than a frame.
  2. The old code "focused" the client by clicking its top-left corner, which
     can land on the title bar, a UI button or a chat box (Shift+R then types
     "R" into chat).
  3. pyautogui uses virtual-key codes; many games (EVE included) read scan
     codes more reliably, which is what pydirectinput sends.
This module holds keys down for KEY_HOLD_SECONDS and uses pydirectinput when
it is installed.
"""
import time

import pyautogui

pyautogui.PAUSE = 0.02
pyautogui.FAILSAFE = True   # slam the mouse into a screen corner to abort


def _keyboard_backend(use_directinput):
    if use_directinput:
        try:
            import pydirectinput
            pydirectinput.PAUSE = 0
            return pydirectinput
        except ImportError:
            print("pydirectinput not installed - falling back to pyautogui keys")
    return pyautogui


class Controls:
    def __init__(self, hold=0.1, gap=0.05, move_seconds=0.2, use_directinput=True):
        self.kb = _keyboard_backend(use_directinput)
        self.hold = hold
        self.gap = gap
        self.move_seconds = move_seconds

    # ---- keyboard -----------------------------------------------------
    def hotkey(self, *keys):
        """Press a combination like ("shift", "r") and hold it briefly."""
        pressed = []
        try:
            for k in keys:
                self.kb.keyDown(k)
                pressed.append(k)
                time.sleep(self.gap)
            time.sleep(self.hold)
        finally:
            for k in reversed(pressed):     # always release, even on error
                self.kb.keyUp(k)
                time.sleep(self.gap)

    def press_each(self, *keys):
        """Press single keys one after another, e.g. F2, F3, F4."""
        for k in keys:
            self.hotkey(k)

    # ---- mouse --------------------------------------------------------
    def move(self, x, y):
        pyautogui.moveTo(x, y, duration=self.move_seconds)

    def click(self, x, y, button="left", modifier=None):
        self.move(x, y)
        if modifier:
            self.kb.keyDown(modifier)
            time.sleep(self.gap)
        try:
            pyautogui.click(button=button)
        finally:
            if modifier:
                time.sleep(self.gap)
                self.kb.keyUp(modifier)
