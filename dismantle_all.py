"""dismantle_all.py — the whole dismantle workflow, start to finish.

Runs, in order, ABORTING IMMEDIATELY if any step fails (a failed scan must
never be followed by a lock sync against stale reports, and a failed sync
must never be followed by the shredder):

  1. auto_vault.py --once          sweep unequipped gear into the vault
  2. destiny_vault.py scan         classify weapons  -> vault_report.json
  3. destiny_vault.py armor-cleanup  armor verdicts  -> armor_cleanup_report.json
  4. sync_locks.py                 locked = keep, unlocked = dismantle
  5. auto_dismantle.py --feed      pull candidates from the vault + shred

    ./venv/Scripts/python.exe dismantle_all.py             # the real thing
    ./venv/Scripts/python.exe dismantle_all.py --dry-run   # preview only

--dry-run: steps 1 and 4 run in their own --dry-run modes, the report steps
run for real (they only write local files), and the shred is skipped.

Steps 1-4 are pure API work; the game only needs to be focused (character
screen, Windowed Fullscreen) once step 5 starts — it waits for 'Destiny 2'
focus before sending any input, so you can alt-tab in when you hear it beep
through steps. Calibrate positions first (auto_dismantle.py --calibrate) if
dismantle_positions.json doesn't exist yet.

Each step runs through _job_runner.py in this process's group, so one Ctrl+C
(or the dashboard Stop button) interrupts the current step gracefully —
finally-cleanup like feed's keeper-lock restore still runs — and no later
step starts.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "_job_runner.py")


def run_step(idx, total, title, script_args):
    print()
    print("=" * 62)
    print("[%d/%d] %s" % (idx, total, title))
    print("      %s" % " ".join(script_args))
    print("=" * 62)
    sys.stdout.flush()
    p = subprocess.Popen([sys.executable, "-u", RUNNER] + script_args, cwd=HERE)
    try:
        rc = p.wait()
    except KeyboardInterrupt:
        # The interrupt went to the whole process group, so the child is
        # already shutting down too — give its cleanup time to finish.
        try:
            p.wait(timeout=15)
        except Exception:
            p.kill()
        raise
    if rc != 0:
        sys.exit("\nStep %d (%s) exited with code %s — ABORTED, no later "
                 "step was run." % (idx, title, rc))


def main():
    ap = argparse.ArgumentParser(
        description="sweep -> scan -> armor-cleanup -> sync locks -> feed+shred")
    ap.add_argument("--dry-run", action="store_true",
                    help="preview: dry sweep, real reports, dry lock sync, no shred")
    ap.add_argument("--device", default="Speakers",
                    help="output device auto_dismantle monitors (default Speakers)")
    ap.add_argument("--threshold", type=float, default=0.03,
                    help="dismantle-sound peak threshold (default 0.03)")
    ap.add_argument("--settle", type=float, default=4.0,
                    help="seconds for vault-arrival sounds to fade per feed batch")
    args = ap.parse_args()

    dry = ["--dry-run"] if args.dry_run else []
    steps = [
        ("Sweep gear to vault",   ["auto_vault.py", "--once"] + dry),
        ("Scan weapons",          ["destiny_vault.py", "scan"]),
        ("Armor cleanup report",  ["destiny_vault.py", "armor-cleanup"]),
        ("Sync lock state",       ["sync_locks.py"] + dry),
    ]
    if not args.dry_run:
        steps.append(("Feed + shred",
                      ["auto_dismantle.py", "--feed",
                       "--device", args.device,
                       "--threshold", str(args.threshold),
                       "--settle", str(args.settle)]))

    try:
        for i, (title, sargs) in enumerate(steps, 1):
            run_step(i, len(steps), title, sargs)
    except KeyboardInterrupt:
        sys.exit("\nWorkflow interrupted — later steps were NOT run.")

    print()
    if args.dry_run:
        print("Dry-run complete. Reports are fresh; no locks flipped, nothing "
              "moved or dismantled.")
    else:
        print("Workflow complete.")


if __name__ == "__main__":
    main()
