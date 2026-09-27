# eve_bot

A tidied-up version of `eve_test_script`: one entry point, with the logic split into modules and every setting in `config.py`.

```
eve_bot/
├── main.py              entry point: python main.py <mode> --profile <name>
├── characters.txt       your characters: short name = character name (edit freely)
├── config.py            hotkeys, timings, thresholds, search regions
├── requirements.txt
├── images/              icon templates in use (images/unused/ = old variants)
└── bot/
    ├── window.py        find + focus the client window
    ├── vision.py        screen capture (mss) and template matching
    ├── controls.py      keyboard/mouse with held keys (fixes Shift+R)
    ├── actions.py       game steps: recall drones, dock, undock, warp, engage…
    ├── input_lock.py    one bot at a time on mouse/keyboard (priority queue)
    ├── runner.py        runs several bots in parallel threads
    └── modes/
        ├── ratting.py   replaces auto_rat.py / auto_rat_2.py / main.py
        ├── autopilot.py replaces auto_pilot.py
        ├── alarm.py     replaces local_alarm.py / auto_run.py (multi-client)
        └── calibrate.py prints search regions for config.py
```

## Setup

```
pip install -r requirements.txt
python main.py                            # menu: pick one function + one character
python main.py calibrate --profile surt   # optional, see "Save CPU"
python main.py rat --profile surt
python main.py alarm --profile cez --profile luck --profile zhycnu
```

Stop with Ctrl+C, or move the mouse into a screen corner. That triggers pyautogui's fail-safe.

## Characters

Edit `characters.txt` (or pick **Edit characters** in the menu). One character per line:

```
surt = Surt Boe Agalder
```

The left side is the short name you type after `--profile`. The right side is the character name exactly as shown in the EVE window title. The first line is the default.

## Running several bots at once

```
python main.py rat --profile surt --profile boah          # two ratters
python main.py multi --bot surt=rat --bot boah=autopilot  # mixed modes
```

Each client gets its own thread. They share a single **input lock** (`bot/input_lock.py`):

- A bot takes the lock, brings its own client to the front, clicks or presses keys, then releases it. A burst like that lasts well under a second.
- Screenshots, matching and all the long waits (docked 300 s, aligning, locking targets) happen **without** holding the lock. The bots only queue up for the moments they need the mouse or keyboard.
- A bot that is **fleeing** from a hostile goes to the front of the queue.
- If a client can't be brought to the front, that input is skipped rather than sent to another bot's window.
- The right-click → "Warp to" and bookmark → Enter steps each keep the lock for the whole step, so another bot can't close the menu partway through.
- A crash in one bot is logged and the others keep running. Moving the mouse into a screen corner stops **all** bots.

Rules for multi-client:
1. **Tile the clients side by side.** They must not overlap and must not be minimised, because the bot reads the screen itself and would otherwise see the wrong client. It warns you at start-up if windows overlap.
2. **Don't use the PC while bots run.** Your own mouse and keyboard aren't part of the lock.
3. Each bot's image matching runs single-threaded, so CPU grows with the number of clients. Setting search regions matters even more here.

## Why Shift+R sometimes failed

1. `pyautogui.press()` releases the key almost instantly. EVE reads input once per frame, and background or low-FPS clients often miss a key that was held for less than one frame. Keys are now held for `KEY_HOLD_SECONDS` (0.1 s).
2. The old scripts focused the client by clicking its top-left corner. That click could land on the title bar, a UI element or the chat box, where Shift+R just types "R". The bot now activates the window properly instead.
3. `pydirectinput` sends hardware scan codes, which games pick up more reliably. It is used when installed.
4. After Shift+R the bot checks that the idle-drone list has gone, and presses it again (up to 3 times) if it hasn't.

If a key still gets missed, raise `KEY_HOLD_SECONDS` to 0.15–0.2.

## Save CPU

| per tick, 1080p, 11 icons | relative cost |
|---|---|
| old scripts (colour, whole window) | 100 % |
| new (grayscale where colour isn't needed) | ~43 % |
| new + search regions set | ~8 % |

- Screenshots are taken with `mss`, one per tick, and every search reuses that one image.
- Local standing icons (`enemy_*`) are still matched **in colour**, because a red and a grey icon have the same shape. Everything else is matched in grayscale.
- Setting regions is the biggest saving. Run `calibrate` with local, the overview and the drone window visible, then paste the regions into `config.TEMPLATES`. Widen each one to cover the whole panel the icon can move around in.
- If CPU use is still too high, raise `TICK_SECONDS` in `config.py`.

## Bugs fixed from the original

- Click positions: `shape[:-1]` gives (height, width), not (width, height), and some clicks used another template's size. Clicks now go to the centre of the matched icon.
- The right-click menu is given time to open before the bot looks for "Warp to".
- `cv2.imread` returns `None` silently when a file is missing. All images are now checked at start-up.
- The wait for a warp to finish now has a timeout, so it can't loop forever.
- `auto_run.py` had a syntax error and `local_alarm.py` was cut off. Both are replaced by `alarm` mode.

Note: automating the EVE client is against CCP's EULA and can get accounts banned.
