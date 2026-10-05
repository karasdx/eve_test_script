"""Print where each icon is on screen, as a region you can paste into config.py.

Open the windows you care about (local, overview, drones, a rat site) so the
icons are visible, then run:  python main.py calibrate --profile surt
It also tests which UI scaling (100 / 125 / 150 %) fits the pictures best.
"""
from ..vision import load_templates


def detect_scale(screen, cfg, scales=(100, 125, 150)):
    """Try each UI scaling against the current screen and recommend one."""
    screen.grab()
    original = screen.templates
    results = []
    print("UI scaling test (needs some icons on screen: local, overview, drones...)")
    try:
        for scale in scales:
            screen.templates = load_templates(cfg.IMAGE_DIR, cfg.TEMPLATES,
                                              scale, cfg.IMAGES_UI_SCALE)
            found, best = 0, []
            for name, t in screen.templates.items():
                m = screen.find(name, threshold=-1)
                score = m.score if m else 0.0
                found += score >= t.threshold
                best.append(score)
            top = sorted(best, reverse=True)[:5]
            avg = sum(top) / len(top)
            results.append((found, avg, scale))
            print(f"  {scale:3d}%: {found:2d} icons found, best scores avg {avg:.2f}")
    finally:
        screen.templates = original
    found, avg, scale = max(results)
    if found == 0:
        print("  no icons recognised at any scaling - open local / overview / drones and retry")
    elif scale == cfg.UI_SCALE:
        print(f"  -> UI_SCALE = {scale} in config.py is right")
    else:
        print(f"  -> set UI_SCALE = {scale} in config.py (it is {cfg.UI_SCALE} now)")
    print()
    return scale


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
