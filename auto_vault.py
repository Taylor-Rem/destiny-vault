"""auto_vault.py — repeatedly sweep unequipped gear off your character into the vault.

Use case: mass-claiming engrams (e.g. 200+ from Hawthorne). Rewards pile up in
your character's weapon/armor buckets (9 slots each); once full they overflow
to the postmaster. Run this alongside the game and it vaults everything
unequipped every few seconds so the buckets stay empty.

    ./venv/Scripts/python.exe auto_vault.py            # sweep every 7s until Ctrl+C
    ./venv/Scripts/python.exe auto_vault.py --interval 5
    ./venv/Scripts/python.exe auto_vault.py --once     # single sweep, then exit

Only touches the 3 weapon + 5 armor buckets on the most-recently-played
character. Equipped gear lives in component 205, not 201, so it's never seen.
Consumables, mods, quests, engrams, and postmaster items are untouched.
Requires setup/login to have been run already (same as every other command).
"""
import argparse
import sys
import time

from destiny_vault import (
    get_token, get_membership, api_get, def_name, _transfer, _flush_caches,
)

# Equippable gear buckets that engram rewards land in.
GEAR_BUCKETS = {
    1498876634: "Kinetic",
    2465295065: "Energy",
    953998645:  "Power",
    3448274439: "Helmet",
    3551918588: "Gauntlets",
    14239492:   "Chest",
    20886954:   "Legs",
    1585787867: "Class Item",
}

# transferStatus bit 2 = NotTransferrable (bit 1 = equipped, absent in 201).
NOT_TRANSFERRABLE = 2


def safe_print(s):
    # Console stdout is cp1252 on this machine; don't crash on Mataiodoxía et al.
    enc = sys.stdout.encoding or "utf-8"
    print(s.encode(enc, "replace").decode(enc))


def active_char(token, mtype, mid):
    """Most-recently-played character — the one you're on while claiming."""
    prof = api_get("/Destiny2/%s/Profile/%s/?components=200" % (mtype, mid), token)
    chars = prof["characters"]["data"]
    cid = max(chars, key=lambda c: chars[c].get("dateLastPlayed", ""))
    c = chars[cid]
    cls = {0: "Titan", 1: "Hunter", 2: "Warlock"}.get(c.get("classType"), "?")
    return cid, cls


def sweep(token, mtype, mid, cid, done, dry_run=False):
    """Vault every transferrable item in a gear bucket on character cid.

    `done` is the session-wide set of itemInstanceIds already vaulted. Bungie's
    profile endpoint serves cached data, so an item we just transferred can
    still appear on the character for a few sweeps — without this we'd re-send
    the transfer (and log a spurious failure) until the cache caught up.
    Returns (moved, vault_full)."""
    prof = api_get("/Destiny2/%s/Profile/%s/?components=201" % (mtype, mid), token)
    items = prof["characterInventories"]["data"].get(cid, {}).get("items", [])
    todo = [i for i in items
            if i.get("bucketHash") in GEAR_BUCKETS
            and "itemInstanceId" in i
            and i["itemInstanceId"] not in done
            and not (i.get("transferStatus", 0) & NOT_TRANSFERRABLE)]
    moved, vault_full = 0, False
    for it in todo:
        name = def_name("DestinyInventoryItemDefinition", it["itemHash"])
        if dry_run:
            safe_print("  would vault %s (%s)" % (name, GEAR_BUCKETS[it["bucketHash"]]))
            done.add(it["itemInstanceId"])
            moved += 1
            continue
        ok, status, msg = _transfer(token, mtype, it["itemHash"],
                                    it["itemInstanceId"], cid, to_vault=True)
        if ok:
            done.add(it["itemInstanceId"])
            moved += 1
            safe_print("  -> vaulted %s (%s)" % (name, GEAR_BUCKETS[it["bucketHash"]]))
        elif status == "DestinyNoRoomInDestination":
            vault_full = True
            safe_print("  !! VAULT FULL — could not move %s" % name)
            break  # no point hammering the rest this cycle
        elif status == "DestinyItemNotFound":
            # Already gone from the character (e.g. a prior transfer landed but
            # the cached profile hadn't caught up) — count it as done.
            done.add(it["itemInstanceId"])
        else:
            safe_print("  !! %s: %s (%s)" % (name, status, msg))
            if status and "Throttle" in status:
                time.sleep(3)
        time.sleep(0.5)  # be polite to the API between transfers
    return moved, vault_full


def main():
    ap = argparse.ArgumentParser(description="Auto-vault unequipped gear on a loop.")
    ap.add_argument("--interval", type=float, default=7,
                    help="seconds between sweeps (default 7)")
    ap.add_argument("--once", action="store_true", help="run one sweep and exit")
    ap.add_argument("--dry-run", action="store_true",
                    help="list what would be vaulted without transferring")
    args = ap.parse_args()

    token, _ = get_token()
    mtype, mid, who = get_membership(token)
    cid, cls = active_char(token, mtype, mid)
    safe_print("Sweeping unequipped gear to vault for %s (%s, char %s)" % (who, cls, cid))
    safe_print("Interval: %ss. Ctrl+C to stop.\n" % args.interval)

    total = 0
    done = set()  # instance ids vaulted this session (Bungie's cache lags)
    try:
        while True:
            token, _ = get_token()  # auto-refreshes when the hour is up
            try:
                moved, vault_full = sweep(token, mtype, mid, cid, done, args.dry_run)
            except Exception as e:  # transient network/API hiccup: log and retry
                safe_print("  !! sweep failed (%s), retrying next cycle" % e)
                moved, vault_full = 0, False
            total += moved
            if moved:
                safe_print("  (%d this sweep, %d total)" % (moved, total))
            if vault_full:
                safe_print("Vault is full — free up space, sweeps will keep retrying.")
            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        _flush_caches()
        verb = "would be vaulted" if args.dry_run else "vaulted"
        safe_print("\nDone. %d item(s) %s." % (total, verb))


if __name__ == "__main__":
    main()
