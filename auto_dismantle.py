"""auto_dismantle.py — hold-to-dismantle automation with audio-spike detection.

The problem: dismantle hold times vary (rarity, masterwork, exotic confirm
dialogs), so a fixed timer either wastes time or releases early. The solution:
Destiny plays a loud shatter on every dismantle, so we watch the SPEAKER OUTPUT
(WASAPI loopback — captures what's playing, mic not involved) and release F the
moment the spike lands, then re-hold. An exotic's confirm dialog just looks
like a silent hold: we time out, release, and the next hold completes it.

Positions: 16 points = 2 per bucket (Kinetic, Energy, Power, Helmet, Gauntlets,
Chest, Legs, Class Item). The unequipped flyout only appears while hovering the
EQUIPPED item's icon, so each bucket needs (1) the equipped icon to hover, then
(2) slot 1 of the flyout that opens. The cursor parks on the flyout slot and
bulk-dismantles there — items reflow into slot 1 until the bucket is empty.

Restocking: use --feed (NOT a parallel feed_dismantle.py — vault arrivals play
a loud sound that audio detection would mistake for dismantles). Feed mode
alternates phases: pull a batch from the vault, wait --settle seconds for the
arrival chimes to fade, then shred in silence; repeat until the pile is gone.

    ./venv/Scripts/python.exe auto_dismantle.py --calibrate   # record the 8 spots (F8)
    ./venv/Scripts/python.exe auto_dismantle.py --audio-test  # tune --threshold
    ./venv/Scripts/python.exe auto_dismantle.py --feed        # the full factory line
    ./venv/Scripts/python.exe auto_dismantle.py               # shred pre-filled buckets only

⚠️  THIS ONE ACTUALLY DESTROYS ITEMS (that's the point). Run it only with the
lock state synced (locked = keep) and ideally with feed_dismantle.py staging —
then everything reachable is a verified dismantle candidate, and locked items
physically can't be dismantled even if hovered. Use Windowed Fullscreen so
SetCursorPos reaches the game. STOP: move the mouse (>60px drift) or press F9.
"""
import argparse
import array
import ctypes
import json
import os
import sys
import threading
import time

import pyaudiowpatch as pyaudio

user32 = ctypes.windll.user32
POS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "dismantle_positions.json")

BUCKET_ORDER = ["Kinetic", "Energy", "Power",
                "Helmet", "Gauntlets", "Chest", "Legs", "Class Item"]
BUCKET_CAP = 9      # max unequipped items a bucket holds — after this many
                    # dismantles it MUST be empty, so advance without probing

SCAN_F = 0x21                 # keyboard scancode for F (games ignore plain VKs)
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
VK_F8, VK_F9 = 0x77, 0x78
INPUT_KEYBOARD = 1


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.c_size_t)]


class _INPUTU(ctypes.Union):
    # pad must make the union exactly 32 bytes (MOUSEINPUT's size) so that
    # sizeof(INPUT) == 40 on x64 — SendInput rejects any other cbSize (error 87)
    _fields_ = [("ki", KEYBDINPUT), ("pad", ctypes.c_byte * 32)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("u", _INPUTU)]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


VK_F = 0x46
INPUT_MODE = "vk"        # set from --input; see f_key


def f_key(down):
    """Send F down/up. Modes:
    vk       — wVk + wScan both set, no SCANCODE flag (what AHK sends; most
               compatible: games mapping by virtual key AND by scancode see it)
    scancode — hardware-scancode-only event (wVk=0); some games ignore these
    """
    if INPUT_MODE == "scancode":
        flags = KEYEVENTF_SCANCODE | (0 if down else KEYEVENTF_KEYUP)
        ki = KEYBDINPUT(0, SCAN_F, flags, 0, 0)
    else:
        flags = 0 if down else KEYEVENTF_KEYUP
        ki = KEYBDINPUT(VK_F, SCAN_F, flags, 0, 0)
    inp = INPUT(type=INPUT_KEYBOARD, u=_INPUTU(ki=ki))
    if user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT)) != 1:
        print("  !! SendInput rejected the event (error %d)"
              % ctypes.windll.kernel32.GetLastError())


def cursor_pos():
    p = POINT()
    user32.GetCursorPos(ctypes.byref(p))
    return p.x, p.y


def key_down(vk):
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def foreground_title():
    hwnd = user32.GetForegroundWindow()
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buf, 256)
    return buf.value


def wait_for_focus(window, first=False):
    """Block until the game window is foreground. Returns True if we had to wait.
    Keeps synthetic input from ever landing in another app (Discord, browser...)."""
    if window.lower() in foreground_title().lower():
        return False
    print("\n  waiting for %r to be the focused window%s..."
          % (window, " — click into the game" if first else " (paused)"))
    while window.lower() not in foreground_title().lower():
        if key_down(VK_F9):
            return None                   # user wants out while unfocused
        time.sleep(0.3)
    print("  focused — resuming in 2s")
    time.sleep(2)
    return True


def find_loopback(p, device_query=None):
    """Loopback device to monitor. With device_query, match an output device by
    name substring (case-insensitive); otherwise use the default output.
    Route Destiny to that device and Discord/music elsewhere (Windows Settings >
    System > Sound > App volume and device preferences) so we only hear the game."""
    if device_query:
        q = device_query.lower()
        for lb in p.get_loopback_device_info_generator():
            if q in lb["name"].lower():
                return lb
        sys.exit("No loopback device matching %r — see --list-devices." % device_query)
    wasapi = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    dev = p.get_device_info_by_index(wasapi["defaultOutputDevice"])
    if not dev.get("isLoopbackDevice"):
        for lb in p.get_loopback_device_info_generator():
            if dev["name"] in lb["name"]:
                return lb
    return dev


class SpeakerMonitor(threading.Thread):
    """Watches an output device's loopback; sets .spike when peak >= threshold."""

    def __init__(self, threshold, device_query=None):
        super().__init__(daemon=True)
        self.threshold = threshold
        self.device_query = device_query
        self.device_name = None
        self.spike = threading.Event()
        self.level = 0.0
        self._stop = threading.Event()

    def run(self):
        p = pyaudio.PyAudio()
        dev = find_loopback(p, self.device_query)
        self.device_name = dev["name"]
        rate, ch = int(dev["defaultSampleRate"]), dev["maxInputChannels"]
        chunk = int(rate * 0.03)          # ~30ms resolution
        stream = p.open(format=pyaudio.paInt16, channels=ch, rate=rate,
                        input=True, input_device_index=dev["index"],
                        frames_per_buffer=chunk)
        prev = 0.0
        while not self._stop.is_set():
            data = array.array("h", stream.read(chunk, exception_on_overflow=False))
            self.level = (max(abs(v) for v in data) / 32768.0) if len(data) else 0.0
            # RISING EDGE only: a long shatter tail that stays loud must not
            # re-trigger — only a fresh quiet->loud crossing counts as an event
            if self.level >= self.threshold and prev < self.threshold:
                self.spike.set()
            prev = self.level
        stream.close()
        p.terminate()

    def stop(self):
        self._stop.set()


def _capture_f8(prompt):
    print(prompt)
    while key_down(VK_F8):
        time.sleep(0.02)                  # wait out any previous press
    while not key_down(VK_F8):
        time.sleep(0.02)
    x, y = cursor_pos()
    print("    captured (%d, %d)" % (x, y))
    while key_down(VK_F8):
        time.sleep(0.02)
    return [x, y]


def calibrate():
    print("Calibration: in-game, open the character screen.")
    print("Two points per bucket, TAP F8 on each (this window need not be focused).\n")
    buckets = []
    for name in BUCKET_ORDER:
        hover = _capture_f8("  hover the EQUIPPED %s icon (flyout opens), press F8..." % name)
        slot = _capture_f8("  now hover slot 1 of the %s flyout, press F8..." % name)
        buckets.append({"name": name, "hover": hover, "slot": slot})
    with open(POS_FILE, "w") as f:
        json.dump({"buckets": buckets}, f, indent=2)
    print("\nSaved %d positions (%d buckets) to %s"
          % (2 * len(buckets), len(buckets), os.path.basename(POS_FILE)))


def list_devices():
    p = pyaudio.PyAudio()
    print("Monitorable output devices (pass a name substring via --device):")
    for lb in p.get_loopback_device_info_generator():
        print("  - %s" % lb["name"].replace(" [Loopback]", ""))
    p.terminate()


def audio_test(threshold, device):
    mon = SpeakerMonitor(threshold, device)
    mon.start()
    time.sleep(0.5)
    print("Monitoring: %s" % (mon.device_name or "(default output)"))
    print("Live peak (Ctrl+C to stop). Dismantle something and note the level;")
    print("pick --threshold between idle max and dismantle peak (current: %.2f)\n" % threshold)
    try:
        while True:
            bar = "#" * int(mon.level * 60)
            trip = "  <-- SPIKE" if mon.level >= threshold else ""
            print("\r  %.3f %-60s%s" % (mon.level, bar, trip), end="")
            mon.spike.clear()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print()
    finally:
        mon.stop()


def main():
    ap = argparse.ArgumentParser(description="Audio-triggered auto-dismantler.")
    ap.add_argument("--calibrate", action="store_true", help="record the 16 hover spots")
    ap.add_argument("--audio-test", action="store_true", help="live level meter")
    ap.add_argument("--list-devices", action="store_true",
                    help="list output devices that can be monitored")
    ap.add_argument("--device", default=None,
                    help="output device to monitor, by name substring (route Destiny "
                         "there and Discord elsewhere via Windows per-app audio). "
                         "Default: the default output device")
    ap.add_argument("--threshold", type=float, default=0.03,
                    help="speaker peak that counts as a dismantle (default 0.03; "
                         "measure with --audio-test — the shatter should clear it, "
                         "the soft exotic-hold noise should not)")
    ap.add_argument("--min-hold", type=float, default=1.0,
                    help="ignore spikes during the first N seconds of each hold — "
                         "prevents transients from causing tap-releases, which "
                         "toggle the item's LOCK in-game (default 1.0)")
    ap.add_argument("--timeout", type=float, default=6.0,
                    help="hard ceiling in seconds to hold F waiting for the spike "
                         "(default 6.0). Only the first holds run this long: once a "
                         "real dismantle has been heard, silent holds give up after "
                         "~2 measured dismantle times, so empty buckets advance fast")
    ap.add_argument("--empty-passes", type=int, default=2,
                    help="consecutive silent holds on a bucket before moving to the "
                         "next (default 2). An exotic's confirm step is one silent "
                         "hold, so never set this below 2 — and a too-early abandon "
                         "is cheap anyway, since every round revisits every bucket")
    ap.add_argument("--window", default="Destiny 2",
                    help="foreground window title that must be focused before any "
                         "input is sent (default 'Destiny 2')")
    ap.add_argument("--input", choices=["vk", "scancode"], default="vk",
                    help="key injection style (default vk = virtual-key + scancode, "
                         "AHK-style; 'scancode' = hardware-scancode-only)")
    ap.add_argument("--test-hold", action="store_true",
                    help="diagnostic: 5s countdown, then hold F for 3s wherever the "
                         "focus is. Try it focused on Notepad (should type fffff...) "
                         "and then in-game (dismantle radial should fill)")
    ap.add_argument("--max-idle", type=int, default=5,
                    help="stop after this many full silent passes (default 5)")
    ap.add_argument("--feed", action="store_true",
                    help="also pull dismantle candidates from the vault, alternating "
                         "fill and shred phases (vault arrivals are loud — never run "
                         "feed_dismantle.py alongside audio detection)")
    ap.add_argument("--settle", type=float, default=4.0,
                    help="seconds after a fill batch for arrival sounds to fade (default 4)")
    args = ap.parse_args()

    global INPUT_MODE
    INPUT_MODE = args.input

    if args.test_hold:
        print("Focus the target window (Notepad or the game). Holding F in:")
        for i in (5, 4, 3, 2, 1):
            print("  %d..." % i)
            time.sleep(1)
        print("  holding F for 3s (%s mode)..." % INPUT_MODE)
        f_key(True)
        try:
            time.sleep(3)
        finally:
            f_key(False)
        print("  released. In Notepad you should see fff...; in-game the radial "
              "should have filled (and likely dismantled the hovered item).")
        return
    if args.calibrate:
        return calibrate()
    if args.list_devices:
        return list_devices()
    if args.audio_test:
        return audio_test(args.threshold, args.device)

    if not os.path.exists(POS_FILE):
        sys.exit("No %s — run --calibrate first." % os.path.basename(POS_FILE))
    with open(POS_FILE) as f:
        cfg = json.load(f)
    if "buckets" not in cfg:
        sys.exit("%s is the old 8-point format — re-run --calibrate "
                 "(now 16 points: equipped icon + flyout slot per bucket)."
                 % os.path.basename(POS_FILE))
    buckets = cfg["buckets"]

    feeder = None
    if args.feed:
        from feed_dismantle import Feeder
        feeder = Feeder()
        if not feeder.targets:
            sys.exit("No dismantle lists found — run 'scan' and 'armor-cleanup' first.")
        print("Feed mode: %d dismantle candidates queued for %s (%s)."
              % (len(feeder.targets), feeder.who, feeder.cls))

    mon = SpeakerMonitor(args.threshold, args.device)
    mon.start()
    time.sleep(0.5)
    print("Monitoring audio from: %s" % (mon.device_name or "(default output)"))
    print("Auto-dismantler armed: threshold %.2f, min hold %.1fs, timeout %.1fs, "
          "%d silent holds to advance a bucket." %
          (args.threshold, args.min_hold, args.timeout, args.empty_passes))
    print("Open the character screen. Input is only sent while %r is focused."
          % args.window)
    print("STOP: move the mouse, or press F9.")
    if wait_for_focus(args.window, first=True) is None:
        sys.exit("Aborted before start.")

    shredded = 0
    idle_rounds = 0
    aborted = False
    avg_hold = None      # EMA of hold-start -> shatter, measured off real dismantles;
                         # silent holds give up at 2x this instead of the full --timeout
    try:
        while idle_rounds < args.max_idle and not aborted:
            sent = 0
            if feeder:
                # FILL phase: transfers only happen here, never during a hold —
                # each vault arrival plays a loud sound that audio detection
                # would otherwise mistake for a dismantle.
                sent, remaining, _on_char = feeder.fill()
                if remaining == 0:
                    print("\nDismantle pile exhausted.")
                    break
                if sent:
                    time.sleep(args.settle)   # let arrival chimes fade
            round_hits = 0
            for b in buckets:
                name = b["name"]
                (hx, hy), (x, y) = b["hover"], b["slot"]
                # open this bucket's flyout: hover the equipped icon first,
                # then park on flyout slot 1 and bulk-dismantle from there
                user32.SetCursorPos(hx, hy)
                time.sleep(0.4)
                dry = 0
                hits = 0             # successful dismantles in this bucket this round
                while dry < args.empty_passes and hits < BUCKET_CAP and not aborted:
                    focus = wait_for_focus(args.window)
                    if focus is None:
                        aborted = True
                        break
                    if focus:             # we were away — reopen this bucket's flyout
                        user32.SetCursorPos(hx, hy)
                        time.sleep(0.4)
                    user32.SetCursorPos(x, y)
                    time.sleep(0.15)
                    f_key(True)
                    t0 = time.time()
                    spiked = False
                    stop = None           # 'abort' (F9 / mouse moved) | 'unfocus' (alt-tab)
                    # a silent slot isn't worth the full --timeout once we know how
                    # long a dismantle actually takes: give up after ~2 of them
                    limit = args.timeout
                    if avg_hold is not None:
                        limit = min(args.timeout, max(args.min_hold + 0.5, 2 * avg_hold))

                    def check():
                        if key_down(VK_F9):
                            return "abort"
                        if args.window.lower() not in foreground_title().lower():
                            return "unfocus"
                        cx, cy = cursor_pos()
                        if abs(cx - x) + abs(cy - y) > 60:
                            return "abort"
                        return None

                    while time.time() - t0 < args.min_hold and not stop:
                        time.sleep(0.05)     # spikes here are noise — hold through them
                        stop = check()
                    # wait for the room to go quiet (previous shatter tail) before
                    # arming, so only a genuinely new sound can release this hold
                    while not stop and mon.level >= mon.threshold \
                            and time.time() - t0 < limit:
                        time.sleep(0.05)
                        stop = check()
                    mon.spike.clear()        # arm detection only after the min hold
                    while not stop and time.time() - t0 < limit:
                        if mon.spike.wait(0.05):
                            spiked = True
                            break
                        stop = check()
                    f_key(False)
                    if spiked:
                        dur = time.time() - t0
                        avg_hold = dur if avg_hold is None else 0.7 * avg_hold + 0.3 * dur
                    if stop == "abort":
                        aborted = True
                        break
                    if stop == "unfocus":
                        continue          # F released; next pass pauses until refocus
                    if spiked:
                        shredded += 1
                        round_hits += 1
                        hits += 1
                        dry = 0
                        print("\r  %d dismantled (last: %s slot)      "
                              % (shredded, name), end="")
                        if hits >= BUCKET_CAP:
                            break             # bucket must be empty now — next bucket
                        time.sleep(0.8)       # reflow + let the shatter tail fade
                    else:
                        dry += 1              # empty slot, locked, or confirm dialog
                        time.sleep(0.2)
            if round_hits == 0 and sent == 0:
                idle_rounds += 1
                time.sleep(4)                 # maybe a restock is still in flight
            else:
                idle_rounds = 0
    except KeyboardInterrupt:
        pass
    finally:
        f_key(False)                          # never leave F held down
        mon.stop()
        if feeder:
            from destiny_vault import _flush_caches
            _flush_caches()
    print("\n%s. %d item(s) dismantled." %
          ("Stopped by you" if aborted else "No more dismantle sounds — pile looks done",
           shredded))


if __name__ == "__main__":
    main()
