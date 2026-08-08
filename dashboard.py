"""dashboard.py — local button-panel web UI for the destiny_vault toolbox.

Serves a single page at http://127.0.0.1:8765 with one button per tool, live
console output, a stdin box (so interactive `setup`/`login` work), and
start/stop for the long-running loops (auto_vault, feed_dismantle, ...).

    ./venv/Scripts/python.exe dashboard.py            # start + open browser
    ./venv/Scripts/python.exe dashboard.py --no-open  # start only
    ./venv/Scripts/python.exe dashboard.py --port 9000

Zero new dependencies (stdlib http.server). Binds 127.0.0.1 only.

Stop semantics: children are spawned in their own process group through
_job_runner.py, and Stop sends CTRL_BREAK_EVENT, which the runner remaps to
KeyboardInterrupt — so `finally:` cleanup runs (feed_dismantle restores keeper
locks there). If a child ignores that for 10s it is force-killed.
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "dashboard.html")
RUNNER = os.path.join(HERE, "_job_runner.py")

VENV_PY = os.path.join(HERE, "venv", "Scripts", "python.exe")  # Windows layout
if not os.path.exists(VENV_PY):
    VENV_PY = os.path.join(HERE, "venv", "bin", "python")
if not os.path.exists(VENV_PY):
    VENV_PY = sys.executable

try:
    from destiny_vault import BUILDS
    BUILD_NAMES = list(BUILDS)
except Exception:
    BUILD_NAMES = ["super-class", "super-grenade", "super-melee",
                   "class-grenade", "grenade-class"]

# ---------------------------------------------------------------------------
# tool registry — the ONLY commands the server will run. The client sends a
# tool id + option values; argv is built here against this spec, never taken
# raw from the request.
#
# option spec: key, label, type (bool|num|text|select), flag (omitted for
# positionals), positional, default, choices, multi (text: one --flag per
# ';'-separated entry), min/max (num).
# tool spec: confirm (client shows a dialog; skipped while dry_run is on),
# interactive (show the stdin box), loop (expected to run until stopped).
# ---------------------------------------------------------------------------

def vault(*args):
    return ["destiny_vault.py"] + list(args)


GROUPS = [
    {
        "title": "Setup & account",
        "note": "One-time credentials + OAuth. Both prompt for input — type "
                "answers in the box under the console.",
        "tools": [
            {"id": "setup", "name": "setup", "cmd": vault("setup"),
             "desc": "Store Bungie app credentials (API key, client id/secret).",
             "interactive": True},
            {"id": "login", "name": "login", "cmd": vault("login"),
             "desc": "OAuth login — a browser tab opens; paste the redirect URL "
                     "into the input box below the console.",
             "interactive": True},
            {"id": "whoami", "name": "whoami", "cmd": vault("whoami"),
             "desc": "Show the linked account and characters."},
        ],
    },
    {
        "title": "Scans & reports",
        "note": "Read-only against the game — they only write local report files.",
        "tools": [
            {"id": "scan", "name": "scan", "cmd": vault("scan"),
             "desc": "Classify every weapon vs rules.yaml → vault_report.json."},
            {"id": "armor-scan", "name": "armor-scan", "cmd": vault("armor-scan"),
             "desc": "Rank armor for a build (blank = all builds).",
             "opts": [
                 {"key": "build", "label": "build", "type": "select",
                  "positional": True, "default": "",
                  "choices": [""] + BUILD_NAMES},
             ]},
            {"id": "armor-cleanup", "name": "armor-cleanup",
             "cmd": vault("armor-cleanup"),
             "desc": "Armor keep/dismantle report → armor_cleanup_report.json "
                     "(no lock changes)."},
            {"id": "loadouts", "name": "loadouts", "cmd": vault("loadouts"),
             "desc": "Dump in-game loadouts with full gear + subclass config."},
        ],
    },
    {
        "title": "Lock state",
        "note": "Locked = keep, unlocked = dismantle candidate. sync-locks is "
                "the preferred path after re-classifying: it flips only "
                "mismatches vs the latest reports.",
        "tools": [
            {"id": "sync-locks", "name": "sync-locks", "cmd": ["sync_locks.py"],
             "desc": "Diff lock state against vault_report.json + "
                     "armor_cleanup_report.json; flip only mismatches.",
             "confirm": "Apply lock flips to the live profile?",
             "opts": [
                 {"key": "dry_run", "label": "dry-run", "type": "bool",
                  "flag": "--dry-run", "default": True},
             ]},
            {"id": "lock-keepers", "name": "lock-keepers",
             "cmd": vault("lock-keepers"),
             "desc": "Re-scan weapons, then lock KEEP + REVIEW. Does NOT unlock "
                     "items that became DISMANTLE since last run.",
             "confirm": "Lock all KEEP/REVIEW weapons via the API?"},
            {"id": "unlock-all", "name": "unlock-all", "cmd": vault("unlock-all"),
             "desc": "Unlock every weapon (clean-slate before lock-keepers).",
             "confirm": "Unlock EVERY weapon? Locked-as-keep state will be lost "
                        "until you re-lock."},
            {"id": "armor-cleanup-lock", "name": "armor-cleanup --lock",
             "cmd": vault("armor-cleanup", "--lock"),
             "desc": "Armor report + lock survivors AND unlock its dismantle list.",
             "confirm": "Lock armor keepers and unlock the armor dismantle list?"},
        ],
    },
    {
        "title": "Character loadouts",
        "note": "Writes to the LIVE character — be in orbit. Dry-run is on by "
                "default; untick it to actually equip.",
        "tools": [
            {"id": "equip-armor", "name": "equip-armor",
             "cmd": vault("equip-armor"),
             "desc": "Equip the best-ranked armor set for a build.",
             "confirm": "Equip armor on the live character? (Must be in orbit.)",
             "opts": [
                 {"key": "build", "label": "build", "type": "select",
                  "positional": True, "default": BUILD_NAMES[0],
                  "choices": BUILD_NAMES, "required": True},
                 {"key": "dry_run", "label": "dry-run", "type": "bool",
                  "flag": "--dry-run", "default": True},
                 {"key": "balance", "label": "balance", "type": "bool",
                  "flag": "--balance", "default": False},
                 {"key": "exotic", "label": "exotic (name)", "type": "text",
                  "flag": "--exotic", "default": ""},
                 {"key": "weapons", "label": "weapons (a; b; c)", "type": "text",
                  "flag": "--weapon", "multi": True, "default": ""},
                 {"key": "loadout", "label": "snapshot to slot", "type": "num",
                  "flag": "--loadout", "default": "", "min": 1, "max": 10},
             ]},
            {"id": "apply-loadout", "name": "apply-loadout",
             "cmd": vault("apply-loadout"),
             "desc": "Equip a build AND snapshot it into an in-game loadout slot. "
                     "NOTE: the snapshot LOCKS every item it captures.",
             "confirm": "Equip + snapshot on the live character? The snapshot "
                        "locks every captured item.",
             "opts": [
                 {"key": "build", "label": "build", "type": "select",
                  "positional": True, "default": BUILD_NAMES[0],
                  "choices": BUILD_NAMES, "required": True},
                 {"key": "slot", "label": "loadout slot (1-10)", "type": "num",
                  "positional": True, "default": 1, "min": 1, "max": 10,
                  "required": True},
                 {"key": "dry_run", "label": "dry-run", "type": "bool",
                  "flag": "--dry-run", "default": True},
                 {"key": "balance", "label": "balance", "type": "bool",
                  "flag": "--balance", "default": False},
                 {"key": "exotic", "label": "exotic (name)", "type": "text",
                  "flag": "--exotic", "default": ""},
                 {"key": "weapons", "label": "weapons (a; b; c)", "type": "text",
                  "flag": "--weapon", "multi": True, "default": ""},
             ]},
        ],
    },
    {
        "title": "Full workflow",
        "note": "The whole factory line with one button. API steps run first; "
                "be at the character screen (Windowed Fullscreen) by the time "
                "the shred step starts — it waits for game focus.",
        "tools": [
            {"id": "dismantle-all", "name": "dismantle-all",
             "cmd": ["dismantle_all.py"],
             "desc": "Sweep gear to vault → scan → armor-cleanup → sync locks "
                     "→ feed + shred. Aborts the chain if any step fails. "
                     "Dry-run previews everything and skips the shred.",
             "loop": True,
             "confirm": "Run the FULL pipeline? It ends in real dismantling: "
                        "locks are synced to fresh reports first (locked = "
                        "safe), then the shredder feeds and destroys every "
                        "unlocked DISMANTLE candidate. Continue?",
             "opts": [
                 {"key": "dry_run", "label": "dry-run (no locks, no shred)",
                  "type": "bool", "flag": "--dry-run", "default": False},
                 {"key": "device", "label": "audio device (substring)",
                  "type": "text", "flag": "--device", "default": "Speakers"},
                 {"key": "threshold", "label": "threshold", "type": "num",
                  "flag": "--threshold", "default": 0.03, "min": 0.001, "max": 1},
                 {"key": "settle", "label": "settle (s)", "type": "num",
                  "flag": "--settle", "default": 4.0, "min": 0, "max": 60},
             ]},
        ],
    },
    {
        "title": "In-game automation",
        "note": "Loops that run alongside the game — Stop button sends the "
                "equivalent of Ctrl+C. Never run auto-vault and feed-dismantle "
                "at the same time (they fight over the same items).",
        "tools": [
            {"id": "auto-vault", "name": "auto-vault", "cmd": ["auto_vault.py"],
             "desc": "Sweep unequipped gear to the vault on a loop (engram "
                     "mass-claim companion).",
             "loop": True,
             "opts": [
                 {"key": "interval", "label": "interval (s)", "type": "num",
                  "flag": "--interval", "default": 7, "min": 1, "max": 600},
                 {"key": "once", "label": "single sweep", "type": "bool",
                  "flag": "--once", "default": False},
             ]},
            {"id": "feed-dismantle", "name": "feed-dismantle",
             "cmd": ["feed_dismantle.py"],
             "desc": "Pull unlocked DISMANTLE candidates from the vault into "
                     "free character slots while you shred. Run scan + "
                     "armor-cleanup first.",
             "loop": True,
             "confirm": "Start feeding dismantle candidates out of the vault?",
             "opts": [
                 {"key": "interval", "label": "interval (s)", "type": "num",
                  "flag": "--interval", "default": 3, "min": 1, "max": 600},
                 {"key": "dry_run", "label": "dry-run (first batch only)",
                  "type": "bool", "flag": "--dry-run", "default": False},
             ]},
            {"id": "auto-clicker", "name": "auto-clicker",
             "cmd": ["auto_clicker.py"],
             "desc": "Left-click at the parked cursor on a loop (engram "
                     "claiming). Stops when the mouse moves.",
             "loop": True,
             "opts": [
                 {"key": "interval", "label": "interval (s)", "type": "num",
                  "flag": "--interval", "default": 1.0, "min": 0.05, "max": 60},
                 {"key": "hold", "label": "hold (s)", "type": "num",
                  "flag": "--hold", "default": 0.03, "min": 0.01, "max": 2},
                 {"key": "delay", "label": "countdown (s)", "type": "num",
                  "flag": "--delay", "default": 3, "min": 0, "max": 30},
             ]},
            {"id": "auto-dismantle", "name": "auto-dismantle",
             "cmd": ["auto_dismantle.py"],
             "desc": "Hold-to-dismantle automation with audio-spike detection. "
                     "DESTROYS ITEMS in shred/feed modes — sync locks first. "
                     "Stops on mouse move or F9.",
             "loop": True,
             "confirm": "auto-dismantle DESTROYS items (that is the point). "
                        "Locked = safe, but make sure locks are synced "
                        "(sync-locks) before starting. Continue?",
             "opts": [
                 {"key": "mode", "label": "mode", "type": "select",
                  "default": "--feed",
                  "choices": ["", "--feed", "--calibrate", "--audio-test",
                              "--test-hold", "--list-devices"],
                  "labels": {"": "shred pre-filled buckets", "--feed": "feed + shred",
                             "--calibrate": "calibrate positions",
                             "--audio-test": "audio level test",
                             "--test-hold": "test F-key hold",
                             "--list-devices": "list audio devices"}},
                 {"key": "threshold", "label": "threshold", "type": "num",
                  "flag": "--threshold", "default": 0.03, "min": 0.001, "max": 1},
                 {"key": "settle", "label": "settle (s)", "type": "num",
                  "flag": "--settle", "default": 4.0, "min": 0, "max": 60},
                 {"key": "device", "label": "audio device (substring)",
                  "type": "text", "flag": "--device", "default": "Speakers"},
             ]},
        ],
    },
]

TOOLS = {t["id"]: t for g in GROUPS for t in g["tools"]}

# safe modes of a confirm-gated tool: calibrate/audio-test etc. never dismantle
SAFE_DISMANTLE_MODES = {"--calibrate", "--audio-test", "--test-hold",
                        "--list-devices"}


def build_argv(tool, opts):
    """Turn client option values into argv, validating against the spec."""
    positionals, flags = [], []
    for o in tool.get("opts", []):
        v = opts.get(o["key"], o.get("default"))
        typ = o["type"]
        if typ == "bool":
            if v:
                flags.append(o["flag"])
            continue
        if v is None or v == "":
            if o.get("required"):
                raise ValueError("missing required option: %s" % o["key"])
            continue
        if typ == "num":
            v = float(v)
            if not (o.get("min", -1e18) <= v <= o.get("max", 1e18)):
                raise ValueError("%s out of range" % o["key"])
            v = str(int(v)) if v == int(v) else str(v)
        elif typ == "select":
            if str(v) not in [str(c) for c in o["choices"]]:
                raise ValueError("bad choice for %s" % o["key"])
            v = str(v)
        elif typ == "text":
            v = str(v).strip()
            if not v:
                continue
            if o.get("multi"):
                for part in [p.strip() for p in v.split(";") if p.strip()]:
                    flags += [o["flag"], part]
                continue
        if o.get("positional"):
            positionals.append(v)
        elif "flag" in o:
            flags += [o["flag"], v]
        else:
            flags.append(v)          # bare select value, e.g. "--feed"
    return [VENV_PY, "-u", RUNNER] + tool["cmd"] + positionals + flags


# ---------------------------------------------------------------------------
# job management
# ---------------------------------------------------------------------------

MAX_LINES = 5000


class Job:
    _seq = 0
    _lock = threading.Lock()

    def __init__(self, tool, argv):
        with Job._lock:
            Job._seq += 1
            self.id = Job._seq
        self.tool_id = tool["id"]
        self.name = tool["name"]
        self.argv = argv
        self.lines = []           # rolling buffer
        self.first = 0            # global index of lines[0]
        self.buf_lock = threading.Lock()
        self.status = "running"
        self.rc = None
        self.started = time.time()
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        self.proc = subprocess.Popen(
            argv, cwd=HERE, env=env, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            creationflags=flags)
        threading.Thread(target=self._pump, daemon=True).start()

    def _append(self, line):
        with self.buf_lock:
            self.lines.append(line)
            if len(self.lines) > MAX_LINES:
                drop = len(self.lines) - MAX_LINES
                del self.lines[:drop]
                self.first += drop

    def _pump(self):
        for raw in iter(self.proc.stdout.readline, b""):
            self._append(raw.decode("utf-8", "replace").rstrip("\r\n"))
        rc = self.proc.wait()
        self.rc = rc
        self.status = "done" if rc == 0 else "failed"
        self._append("--- exited with code %s ---" % rc)

    def send_stdin(self, text):
        if self.proc.poll() is not None:
            raise ValueError("process already exited")
        self._append("> " + text)
        self.proc.stdin.write((text + "\n").encode("utf-8"))
        self.proc.stdin.flush()

    def stop(self):
        if self.proc.poll() is not None:
            return
        self.status = "stopping"
        self._append("--- stop requested (Ctrl+Break) ---")
        try:
            if os.name == "nt":
                self.proc.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self.proc.send_signal(signal.SIGINT)
        except Exception:
            self.proc.kill()
            return

        def enforce():
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._append("--- no exit after 10s, force-killing ---")
                self.proc.kill()
        threading.Thread(target=enforce, daemon=True).start()

    def output_since(self, start):
        with self.buf_lock:
            idx = max(0, start - self.first)
            return self.lines[idx:], self.first + len(self.lines)

    def summary(self):
        return {"id": self.id, "tool": self.tool_id, "name": self.name,
                "status": self.status, "rc": self.rc,
                "started": self.started,
                "cmd": " ".join(os.path.basename(a) for a in self.argv[2:])}


JOBS = {}          # id -> Job
JOBS_LOCK = threading.Lock()


def start_job(tool_id, opts):
    tool = TOOLS.get(tool_id)
    if not tool:
        raise ValueError("unknown tool: %s" % tool_id)
    with JOBS_LOCK:
        for j in JOBS.values():
            if j.tool_id == tool_id and j.status in ("running", "stopping"):
                raise ValueError("%s is already running (job %d)" % (tool_id, j.id))
        argv = build_argv(tool, opts or {})
        job = Job(tool, argv)
        JOBS[job.id] = job
        # cap history: keep the 50 most recent finished jobs
        finished = sorted((j for j in JOBS.values()
                           if j.status in ("done", "failed")),
                          key=lambda j: j.started)
        for j in finished[:-50]:
            del JOBS[j.id]
    return job


# ---------------------------------------------------------------------------
# http server
# ---------------------------------------------------------------------------

class Server(ThreadingHTTPServer):
    # On Windows SO_REUSEADDR lets a second instance bind the SAME port and
    # silently steal connections from the first. Turn it off so a duplicate
    # launch fails loudly (WinError 10048) instead.
    allow_reuse_address = os.name != "nt"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):      # keep the console quiet
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)
        if url.path == "/":
            try:
                with open(PAGE, "rb") as f:
                    body = f.read()
            except OSError:
                self.send_error(500, "dashboard.html missing")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif url.path == "/api/tools":
            self._json({"groups": GROUPS, "python": VENV_PY})
        elif url.path == "/api/jobs":
            with JOBS_LOCK:
                jobs = sorted(JOBS.values(), key=lambda j: -j.started)
                self._json({"jobs": [j.summary() for j in jobs]})
        elif url.path == "/api/output":
            try:
                job = JOBS[int(q["id"][0])]
            except (KeyError, ValueError):
                self._json({"error": "no such job"}, 404)
                return
            start = int(q.get("from", ["0"])[0])
            lines, nxt = job.output_since(start)
            self._json({"lines": lines, "next": nxt, "status": job.status,
                        "rc": job.rc})
        else:
            self.send_error(404)

    def do_POST(self):
        try:
            body = self._read_body()
            if self.path == "/api/run":
                job = start_job(body.get("tool"), body.get("opts"))
                self._json({"id": job.id})
            elif self.path == "/api/stop":
                JOBS[int(body["id"])].stop()
                self._json({"ok": True})
            elif self.path == "/api/stdin":
                JOBS[int(body["id"])].send_stdin(str(body.get("text", "")))
                self._json({"ok": True})
            else:
                self.send_error(404)
        except (ValueError, KeyError) as e:
            self._json({"error": str(e)}, 400)


def main():
    ap = argparse.ArgumentParser(description="destiny_vault web dashboard")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-open", action="store_true",
                    help="don't open the browser automatically")
    args = ap.parse_args()
    try:
        srv = Server(("127.0.0.1", args.port), Handler)
    except OSError as e:
        sys.exit("Port %d is already in use — is another dashboard running? (%s)"
                 % (args.port, e))
    url = "http://127.0.0.1:%d" % args.port
    print("destiny_vault dashboard: %s   (Ctrl+C to quit)" % url)
    print("python: %s" % VENV_PY)
    if not args.no_open:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down; stopping running jobs...")
        with JOBS_LOCK:
            for j in JOBS.values():
                j.stop()


if __name__ == "__main__":
    main()
