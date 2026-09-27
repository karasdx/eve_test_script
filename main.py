"""
Usage:
    python main.py                                      # menu: pick function(s) + one or more characters
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
import subprocess
import sys

import cv2

import config
from bot import Actions, Controls, Screen, find_window, load_templates
from bot.input_lock import InputLock
from bot.modes import Alarm, Autopilot, Ratting, calibrate
from bot.runner import run_bots
from bot.window import overlapping

MODES = {"rat": Ratting, "autopilot": Autopilot}


MENU = [
    ("rat", "Ratting"),
    ("autopilot", "Autopilot"),
    ("alarm", "Local alarm"),
    ("calibrate", "Calibrate search regions (one character)"),
    ("multi", "Different function for each character (ratting / autopilot)"),
]


def pick(prompt, options, default=0):
    """Numbered menu; returns the index chosen (Enter = default)."""
    print(prompt)
    for i, label in enumerate(options, 1):
        print(f"  {i}. {label}" + ("  (default)" if i - 1 == default else ""))
    while True:
        answer = input("> ").strip()
        if not answer:
            return default
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer) - 1
        print(f"Enter a number from 1 to {len(options)}.")


def pick_characters(single=False):
    """Numbered list of characters; returns the short names chosen."""
    while True:
        names = list(config.PROFILES)
        print("\nWhich character?" if single else
              "\nWhich characters? e.g. 1  or  1 3 5  or  all")
        for i, n in enumerate(names, 1):
            print(f"  {i}. {n}  ({config.PROFILES[n]})" + ("  (default)" if i == 1 else ""))
        print(f"  E. Edit characters (opens {config.CHARACTERS_FILE.name})")
        answer = input("> ").strip().lower()
        if answer == "e":
            edit_characters()
            continue
        if not answer:
            return names[:1]
        if answer == "all" and not single:
            return names
        parts = answer.replace(",", " ").split()
        if parts and all(p.isdigit() and 1 <= int(p) <= len(names) for p in parts):
            chosen = list(dict.fromkeys(names[int(p) - 1] for p in parts))
            if single and len(chosen) > 1:
                print("Pick just one character here.")
                continue
            return chosen
        print(f"Enter numbers from 1 to {len(names)}" + ("" if single else ", or 'all'") + ", or E.")


def menu_args():
    """No command-line arguments: choose the function(s) and character(s)."""
    mode = MENU[pick("Which function to run?", [label for _, label in MENU])][0]
    profiles = pick_characters(single=(mode == "calibrate"))
    bots = None
    if mode == "multi":
        bots = []
        for name in profiles:
            m = list(MODES)[pick(f"\nFunction for {name}?", [dict(MENU)[k] for k in MODES])]
            bots.append(f"{name}={m}")
    print()
    return argparse.Namespace(mode=mode, profile=profiles, window=None, bot=bots, once=False)


def edit_characters():
    """Open characters.txt in Notepad, wait for it to close, then reload."""
    while True:
        print(f"Edit {config.CHARACTERS_FILE.name}, save, then close Notepad to continue.")
        subprocess.run(["notepad.exe", str(config.CHARACTERS_FILE)])
        try:
            config.PROFILES = config.load_profiles()
        except SystemExit as e:
            print(f"Problem: {e}\nOpening it again so you can fix it.\n")
            continue
        config.DEFAULT_PROFILE = next(iter(config.PROFILES))
        return


def parse_args():
    if len(sys.argv) == 1:
        return menu_args()
    p = argparse.ArgumentParser(description="EVE screen-reading helper")
    p.add_argument("mode", choices=["rat", "autopilot", "multi", "alarm", "calibrate"])
    p.add_argument("--profile", action="append", choices=sorted(config.PROFILES),
                   help="character from characters.txt (repeat for several clients)")
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
    from_menu = len(sys.argv) == 1          # e.g. double-clicked: keep the window open
    try:
        main()
    except KeyboardInterrupt:
        print("\nstopped")
    except SystemExit as e:
        if not from_menu:
            raise
        if e.code not in (None, 0):
            print(e)
    except BaseException:
        if not from_menu:
            raise
        import traceback
        traceback.print_exc()
    finally:
        if from_menu:
            try:
                input("\nPress Enter to close...")
            except (EOFError, KeyboardInterrupt):
                pass
