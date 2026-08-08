"""auto_clicker.py — click the left mouse button at the current cursor position
on a fixed interval. Zero dependencies (Windows ctypes only).

Companion to auto_vault.py for mass-claiming Hawthorne engrams: park the cursor
over the engram tile, alt-tab back to the game, and let it click.

    ./venv/Scripts/python.exe auto_clicker.py              # 1 click/sec
    ./venv/Scripts/python.exe auto_clicker.py --interval 0.5
    ./venv/Scripts/python.exe auto_clicker.py --hold 0.3   # press-and-hold clicks

Starts after a 3s countdown (time to focus the game window).
STOP by moving the mouse — any drift over ~40px ends the script instantly.
"""
import argparse
import ctypes
import time

user32 = ctypes.windll.user32

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def cursor_pos():
    p = POINT()
    user32.GetCursorPos(ctypes.byref(p))
    return p.x, p.y


def click(hold):
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(hold)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def main():
    ap = argparse.ArgumentParser(description="Left-click at the cursor on a loop.")
    ap.add_argument("--interval", type=float, default=1.0,
                    help="seconds between clicks (default 1.0)")
    ap.add_argument("--hold", type=float, default=0.03,
                    help="seconds to hold the button down each click (default "
                         "0.03; raise to ~0.3+ if the game wants press-and-hold)")
    ap.add_argument("--delay", type=float, default=3,
                    help="countdown before the first click (default 3s)")
    args = ap.parse_args()

    print("Clicking every %.2gs. Park the cursor and focus the game." % args.interval)
    for i in range(int(args.delay), 0, -1):
        print("  starting in %d..." % i)
        time.sleep(1)

    home = cursor_pos()
    print("Running at (%d, %d). MOVE THE MOUSE to stop (or Ctrl+C here)." % home)

    clicks = 0
    try:
        while True:
            x, y = cursor_pos()
            if abs(x - home[0]) + abs(y - home[1]) > 40:
                print("Mouse moved — stopping.")
                break
            click(args.hold)
            clicks += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    print("Done. %d click(s) sent." % clicks)


if __name__ == "__main__":
    main()
