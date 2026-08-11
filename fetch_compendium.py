"""Mirror the community Destiny Data Compendium spreadsheet into research/compendium/.

The Compendium (docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4)
is a community-maintained reference for perk/mod/subclass behavior — far more current than
model training data or wikis. The sheet's owner has disabled the normal /export download
(it 401s), but the per-tab gviz CSV endpoint is open; each tab's gid was captured from the
htmlview tab switcher on 2026-08-11.

Output is one CSV per tab. The CSVs are gitignored (public repo — the data is the
Compendium authors' work, and a committed snapshot would silently go stale); run this
script to (re)build them locally.

Usage:
    ./venv/Scripts/python.exe fetch_compendium.py            # current tabs
    ./venv/Scripts/python.exe fetch_compendium.py --all      # also the OLD * archive tabs
    ./venv/Scripts/python.exe fetch_compendium.py --tab "Weapon Perks"
"""
import argparse
import csv
import io
import json
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

SHEET_ID = "1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
OUT_DIR = Path(__file__).parent / "research" / "compendium"

# name -> gid. "Landing" (gid 1038486120) is skipped: decorative cover page, no data.
TABS = {
    "Weapon Perks": "1662574278",
    "Armor Perks": "1287885342",
    "Artifact Perks": "473308249",
    "Armor Mods": "1934379638",
    "Arc": "618967225",
    "Solar": "1186062409",
    "Void": "1907852650",
    "Stasis": "1088259962",
    "Strand": "1870531554",
    "Prismatic": "1918152785",
    "Exotic Class": "20898389",
    "Class Abilities": "527596209",
    "Exotic Weapons": "441434520",
    "Exotic Armors": "1500097863",
    "Game Mechanics": "1800463143",
}
OLD_TABS = {
    "OLD Episodic Artifact Perks": "715236319",
    "OLD Seasonal Artifact Perks": "70425171",
    "OLD Nether Mechanics": "333521426",
    "OLD Armor Mods": "1925335732",
    "OLD Game Mechanics": "135237481",
}


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def fetch_tab(gid: str) -> str:
    url = f"{SHEET_URL}/gviz/tq?tqx=out:csv&gid={gid}"
    req = urllib.request.Request(url, headers={"User-Agent": "destiny-vault-compendium-mirror"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8")
    if body.lstrip()[:1] in ("<", "{"):  # HTML auth wall or gviz error JSON, not CSV
        raise RuntimeError("endpoint returned non-CSV (sheet permissions may have changed)")
    return body


def tidy(raw_csv: str) -> list[list[str]]:
    """Drop fully-empty rows/columns (the sheet uses blank cells as visual spacing)."""
    rows = list(csv.reader(io.StringIO(raw_csv)))
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        return []
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    live_cols = [i for i in range(width) if any(r[i].strip() for r in rows)]
    return [[r[i] for i in live_cols] for r in rows]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--all", action="store_true", help="include the OLD * archive tabs")
    ap.add_argument("--tab", help="fetch a single tab by exact name")
    args = ap.parse_args()

    tabs = {**TABS, **OLD_TABS} if args.all else dict(TABS)
    if args.tab:
        pool = {**TABS, **OLD_TABS}
        if args.tab not in pool:
            print(f"unknown tab {args.tab!r}; choose from: {', '.join(pool)}")
            return 1
        tabs = {args.tab: pool[args.tab]}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fetched, failed = {}, []
    for name, gid in tabs.items():
        try:
            rows = tidy(fetch_tab(gid))
        except Exception as e:
            print(f"  FAIL {name}: {e}")
            failed.append(name)
            continue
        path = OUT_DIR / f"{slug(name)}.csv"
        with open(path, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows(rows)
        fetched[name] = {"gid": gid, "file": path.name, "rows": len(rows)}
        print(f"  ok   {name}: {len(rows)} rows -> {path.name}")
        time.sleep(0.5)  # be polite to the endpoint

    meta_path = OUT_DIR / "_meta.json"
    meta = {"source": SHEET_URL, "fetched": str(date.today()), "tabs": {}}
    if meta_path.exists():
        try:
            meta.update(json.loads(meta_path.read_text(encoding="utf-8")))
            meta["fetched"] = str(date.today())
        except Exception:
            pass
    meta["tabs"].update(fetched)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"{len(fetched)} tab(s) fetched" + (f", {len(failed)} FAILED: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
