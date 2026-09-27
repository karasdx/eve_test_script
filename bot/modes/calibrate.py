"""Print where each icon is on screen, as a region you can paste into config.py.

Open the windows you care about (local, overview, drones, a rat site) so the
icons are visible, then run:  python main.py calibrate --profile surt
"""


def calibrate(screen, templates, pad=0.08):
    screen.grab()
    H, W = screen.bgr.shape[:2]
    print(f"window {W}x{H}\n")
    for name in templates:
        m = screen.find(name, threshold=templates[name].threshold)
        if not m:
            print(f"{name:15s} not visible now")
            continue
        x0 = max(0.0, (m.x - screen.left) / W - pad)
        y0 = max(0.0, (m.y - screen.top) / H - pad)
        x1 = min(1.0, (m.x - screen.left + m.w) / W + pad)
        y1 = min(1.0, (m.y - screen.top + m.h) / H + pad)
        print(f"{name:15s} score {m.score:.2f}  region ({x0:.2f}, {y0:.2f}, {x1:.2f}, {y1:.2f})")
    print("\nTip: widen a region to cover the whole list/panel the icon can move in "
          "(e.g. the full height of local or the overview).")
