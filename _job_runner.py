"""_job_runner.py — exec a repo script so dashboard.py can stop it gracefully.

Windows can't deliver SIGINT to another process; the dashboard sends
CTRL_BREAK_EVENT to the child's process group instead. Python's default
SIGBREAK action terminates without unwinding the stack, which would skip
`finally:` cleanup (feed_dismantle.py restores keeper locks in one). This
wrapper remaps SIGBREAK to KeyboardInterrupt so a dashboard Stop behaves
exactly like Ctrl+C in a terminal.

Usage: python _job_runner.py <script.py> [args...]
"""
import runpy
import signal
import sys


def _to_kbint(signum, frame):
    raise KeyboardInterrupt


if hasattr(signal, "SIGBREAK"):
    signal.signal(signal.SIGBREAK, _to_kbint)

script = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(script, run_name="__main__")
