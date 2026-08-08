"""sync_locks.py — bring in-game lock state in line with the latest reports,
touching ONLY items whose state actually differs.

Replaces the unlock-all -> lock-keepers -> armor-cleanup --lock cycle (~1600
SetLockState calls) with a diff: desired state is computed from the reports,
current state is read from the profile, and only mismatches get an API call.
The Bungie API has no bulk lock endpoint (one call per item, same as DIM), so
minimizing the number of flips is the only real optimization available.

Desired state:
  weapons (vault_report.json):        KEEP + REVIEW -> locked, DISMANTLE -> unlocked
  armor (armor_cleanup_report.json):  KEEP + REVIEW -> locked, DISMANTLE -> unlocked,
                                      any armor NOT in the report (= off-class,
                                      which armor-cleanup skips) -> locked
  everything else (ghosts, ships, subclasses...): untouched

Run `scan` and `armor-cleanup` first so the reports are fresh.

    ./venv/Scripts/python.exe sync_locks.py            # apply
    ./venv/Scripts/python.exe sync_locks.py --dry-run  # show the flip list only
"""
import argparse
import json
import sys

from destiny_vault import (
    get_token, fetch_profile, api_action, item_meta, _item_char_map,
    _any_char_id, _flush_caches, load_json,
)

LOCKED = 1  # item state bit


def safe_print(s):
    enc = sys.stdout.encoding or "utf-8"
    print(s.encode(enc, "replace").decode(enc))


def desired_state():
    """iid -> True (locked) / False (unlocked), from the two reports."""
    want = {}
    wrep = load_json("vault_report.json") or {}
    for bucket, state in (("keep", True), ("review", True), ("dismantle", False)):
        for w in wrep.get(bucket, []):
            want[w["id"]] = state
    arep = load_json("armor_cleanup_report.json") or {}
    armor_seen = set()
    for bucket, state in (("keep", True), ("review", True), ("dismantle", False)):
        for p in arep.get(bucket, []):
            want[p["iid"]] = state
            armor_seen.add(p["iid"])
    return want, armor_seen


def live_items(prof):
    """Every instanced item we can see: iid -> (hash, currently_locked)."""
    out = {}
    src = [prof.get("profileInventory", {}).get("data", {}).get("items", [])]
    for comp in ("characterInventories", "characterEquipment"):
        for invd in prof.get(comp, {}).get("data", {}).values():
            src.append(invd.get("items", []))
    for items in src:
        for it in items:
            iid = it.get("itemInstanceId")
            if iid:
                out[iid] = (it["itemHash"], bool(it.get("state", 0) & LOCKED))
    return out


def main():
    ap = argparse.ArgumentParser(description="Diff-sync item lock state to the reports.")
    ap.add_argument("--dry-run", action="store_true", help="list flips, change nothing")
    args = ap.parse_args()

    token, _ = get_token()
    mtype, mid, prof = fetch_profile(token)
    default_char = _any_char_id(prof)
    char_of = _item_char_map(prof)

    want, armor_in_report = desired_state()
    if not want:
        sys.exit("No reports found — run 'scan' and 'armor-cleanup' first.")
    live = live_items(prof)

    flips = []   # (iid, hash, to_state)
    stats = {"already_ok": 0, "lock": 0, "unlock": 0, "offclass_lock": 0}
    for iid, (ihash, is_locked) in live.items():
        if iid in want:
            target = want[iid]
        else:
            # Not classified. Off-class armor is deliberately skipped by
            # armor-cleanup but must stay locked (protect Titan/Hunter gear).
            meta = item_meta(ihash)
            if meta.get("itemType") == 2 and not is_locked:  # 2 = Armor
                flips.append((iid, ihash, True))
                stats["offclass_lock"] += 1
            continue
        if target == is_locked:
            stats["already_ok"] += 1
        else:
            flips.append((iid, ihash, target))
            stats["lock" if target else "unlock"] += 1
    _flush_caches()

    safe_print("Lock sync plan: %d already correct, %d to lock, %d to unlock, "
               "%d unclassified armor to lock (off-class protection)."
               % (stats["already_ok"], stats["lock"], stats["unlock"],
                  stats["offclass_lock"]))
    if args.dry_run:
        for iid, ihash, to in flips:
            safe_print("  %s %s" % ("LOCK  " if to else "UNLOCK",
                                    item_meta(ihash)["name"]))
        _flush_caches()
        return
    if not flips:
        safe_print("Nothing to do.")
        return

    ok = fail = 0
    for i, (iid, ihash, to) in enumerate(flips, 1):
        body = {"state": to, "itemId": iid,
                "characterId": char_of.get(iid, default_char),
                "membershipType": mtype}
        resp = api_action("/Destiny2/Actions/Items/SetLockState/", body, token)
        if resp.get("ErrorCode") == 1:
            ok += 1
        else:
            fail += 1
            safe_print("  FAILED %s %s: %s" % ("lock" if to else "unlock",
                                               item_meta(ihash)["name"],
                                               resp.get("Message")))
        if i % 50 == 0:
            safe_print("  ...%d/%d" % (i, len(flips)))
    _flush_caches()
    safe_print("Done: %d flipped, %d failed. Locked = keep, unlocked = dismantle."
               % (ok, fail))


if __name__ == "__main__":
    main()
