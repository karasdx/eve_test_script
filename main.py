"""
Usage:
    python main.py rat                                  # default profile
    python main.py rat --profile surt --profile boah    # two ratting bots at once
    python main.py autopilot --profile boah
    python main.py multi --bot surt=rat --bot boah=autopilot   # mix modes
    python main.py alarm --profile cez --profile luck --profile zhycnu
    python main.py alarm --window "EVE - Some Name" --once
    python main.py calibrate --profile surt             # suggest search regions

Several bots share ONE mouse and keyboard: they take turns for each short
burst of input, so keep the clients tiled side by side (not overlapping, not
minimised) and don't use the PC while they run.
"""
import argparse
import os

import cv2

import config
from bot import Actions, Controls, Screen, find_window, load_templates
from bot.input_lock import InputLock
from bot.modes import Alarm, Autopilot, Ratting, calibrate
from bot.runner import run_bots
from bot.window import overlapping

MODES = {"rat": Ratting, "autopilot": Autopilot}


def parse_args():
    p = argparse.ArgumentParser(description="EVE screen-reading helper")
    p.add_argument("mode", choices=["rat", "autopilot", "multi", "alarm", "calibrate"])
    p.add_argument("--profile", action="append", choices=sorted(config.PROFILES),
                   help="character from config.PROFILES (repeat for several clients)")
    p.add_argument("--window", action="append", help="exact window title instead of a profile")
    p.add_argument("--bot", action="append", metavar="PROFILE=MODE",
                   help="multi mode: e.g. --bot surt=rat --bot boah=autopilot")
    p.add_argument("--once", action="store_true", help="alarm: exit after the first alert")
    return p.parse_args()


def resolve_title(name):
    return config.PROFILES.get(name, name)


def bot_list(args):
    """[(window title, mode)] for the requested bots."""
    if args.mode == "multi":
        if not args.bot:
            raise SystemExit("multi mode needs at least one --bot PROFILE=MODE")
        pairs = []
        for spec in args.bot:
            name, _, mode = spec.partition("=")
            if mode not in MODES:
                raise SystemExit(f"--bot {spec}: mode must be one of {', '.join(MODES)}")
            pairs.append((resolve_title(name), mode))
        return pairs
    titles = [config.PROFILES[p] for p in (args.profile or [])] + (args.window or [])
    titles = titles or [config.PROFILES[config.DEFAULT_PROFILE]]
    return [(t, args.mode) for t in titles]


def warn_layout(windows):
    for problem in overlapping(windows):
        print("WARNING:", problem)


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    args = parse_args()
    bots = bot_list(args)
    # several bots in parallel -> keep each one's OpenCV to a single thread
    cv2.setNumThreads(1 if len(bots) > 1 else config.CV_THREADS)
    templates = load_templates(config.IMAGE_DIR, config.TEMPLATES)

    windows = {title: find_window(title) for title, _ in bots}
    warn_layout(list(windows.values()))

    if args.mode == "alarm":
        screens = {t: Screen(w, templates) for t, w in windows.items()}
        Alarm(screens, config, once=args.once).run()
        return

    if args.mode == "calibrate":
        calibrate(Screen(windows[bots[0][0]], templates), templates)
        return

    lock = InputLock()                       # shared by every bot
    runnables = []
    for title, mode in bots:
        name = title.removeprefix("EVE - ")
        controls = Controls(config.KEY_HOLD_SECONDS, config.KEY_GAP_SECONDS,
                            config.MOUSE_MOVE_SECONDS, config.USE_DIRECTINPUT)
        actions = Actions(Screen(windows[title], templates), controls,
                          config.KEYS, config.TIMING, lock=lock, name=name)
        runnables.append((name, MODES[mode](actions, config).run))

    print("Running", ", ".join(f"{n} ({m})" for (n, _), (_, m) in zip(runnables, bots)))
    print("Stop: Ctrl+C, or move the mouse into a screen corner.\n")
    run_bots(runnables)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nstopped")
