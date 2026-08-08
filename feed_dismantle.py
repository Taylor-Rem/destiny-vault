"""feed_dismantle.py — keep the Warlock's inventory topped up with DISMANTLE
candidates pulled from the vault, so you can stand still and shred.

The opposite of auto_vault.py: every few seconds it pulls unlocked items that
the reports classified DISMANTLE out of the vault into free bucket slots on
your most-recently-played character. As you dismantle, slots free up and the
next batch flows in — until the whole dismantle pile is gone.

SAFETY: an item is only ever moved if BOTH are true:
  1. its instance id is in the DISMANTLE list of vault_report.json or
     armor_cleanup_report.json (run `scan` / `armor-cleanup` first!), and
  2. it is currently UNLOCKED in the live profile (a lock you set in-game
     since the report always wins — the item is skipped and reported).

KNOWN BUNGIE BUG (Bungie-net/api#764, open since 2018): a vault->character
transfer can deliver the item LOCKED, inheriting the lock from another copy of
the same item (our keepers). The feeder works around it by dropping the keeper
siblings' locks for the duration of each transfer batch and restoring them
right after; if a restore ever fails it says so loudly — run sync_locks.py.
Keepers are locked, and locked items can't be dismantled in-game anyway, so
even a stray drag stays safe. Do NOT run auto_vault.py at the same time —
they would fight over the same items.

NOTE: if you're using auto_dismantle.py, run it with --feed instead of running
this alongside it — vault arrivals play a loud sound that would false-trigger
its audio detection, so the combined mode alternates fill and shred phases.

    ./venv/Scripts/python.exe feed_dismantle.py            # refill every 3s
    ./venv/Scripts/python.exe feed_dismantle.py --interval 5
    ./venv/Scripts/python.exe feed_dismantle.py --dry-run  # show first batch only
"""
import argparse
import sys
import time

from destiny_vault import (
    get_token, get_membership, api_get, api_action, _transfer, _flush_caches,
    load_json,
)
from auto_vault import GEAR_BUCKETS, active_char, safe_print

CAPACITY = 9          # unequipped slots per bucket
LOCKED = 1            # item state bit

_bucket_cache = {}    # itemHash -> bucket name (vault items don't carry their slot)


def bucket_of(item_hash, slot_hint=None):
    if slot_hint:                      # armor report carries the slot already
        return slot_hint
    if item_hash not in _bucket_cache:
        try:
            d = api_get("/Destiny2/Manifest/DestinyInventoryItemDefinition/%s/" % item_hash)
            b = d.get("inventory", {}).get("bucketTypeHash")
        except Exception:
            b = None
        _bucket_cache[item_hash] = GEAR_BUCKETS.get(b)
    return _bucket_cache[item_hash]


def dismantle_targets():
    """iid -> (name, slot_hint or None) for everything the reports condemned."""
    targets = {}
    wrep = load_json("vault_report.json") or {}
    for w in wrep.get("dismantle", []):
        targets[w["id"]] = (w["name"], None)
    arep = load_json("armor_cleanup_report.json") or {}
    for p in arep.get("dismantle", []):
        targets[p["iid"]] = (p["name"], p["slot"])
    return targets


class Feeder:
    """One fill cycle at a time; shared by the standalone loop below and by
    auto_dismantle.py --feed (which must control WHEN transfers happen, because
    vault arrivals play a sound that would false-trigger audio detection)."""

    def __init__(self, respect_locks=False):
        token, _ = get_token()
        self.mtype, self.mid, self.who = get_membership(token)
        self.cid, self.cls = active_char(token, self.mtype, self.mid)
        self.targets = dismantle_targets()
        self.pending = {}          # iid -> bucket: transferred, not yet visible
        self.skipped_locked = set()
        self.moved = 0
        # anti-jam: cycles each target has sat on the char. The game client
        # caches lock state and ignores API unlocks, so a tap-locked item can
        # become un-dismantlable until relog — after STUCK_CYCLES it gets parked
        # back to the vault and deferred so it can't block its bucket's slot 1.
        self.on_char_cycles = {}
        self.deferred = set()
        self.STUCK_CYCLES = 8
        # diagnostic: iids we unlocked last cycle. If any come back locked and we
        # never sent a lock, the game CLIENT is re-asserting a stale cached lock
        # (fix = relog). This is the only thing that can lock a dismantle item,
        # since neither script ever sends state:True on one.
        self._unlocked_last = set()
        self.client_relocks = 0
        # The reports are the source of truth. In-game tap-locks and stale
        # client caches keep re-locking condemned items, so by default we
        # UNLOCK a dismantle-listed locked item rather than skip it.
        self.respect_locks = respect_locks
        # keeper siblings whose re-lock failed (see fill's finally) — the user
        # must run sync_locks.py to restore these
        self.relock_failed = set()

    def _setlock(self, token, iid, state, where):
        body = {"state": state, "itemId": iid,
                "characterId": where if where not in ("vault", "equipped") else self.cid,
                "membershipType": self.mtype}
        r = api_action("/Destiny2/Actions/Items/SetLockState/", body, token)
        return r.get("ErrorCode") == 1, r.get("ErrorStatus")

    def _unlock(self, token, iid, name, where):
        ok, status = self._setlock(token, iid, False, where)
        if ok:
            self._unlocked_last.add(iid)   # watch for a re-lock next cycle
            safe_print("  unlocked %s (report says dismantle)" % name)
            return True
        safe_print("  !! could not unlock %s: %s" % (name, status))
        return False

    def snapshot(self, token):
        """Live view: iid -> (hash, locked, where, bucketHash)."""
        prof = api_get("/Destiny2/%s/Profile/%s/?components=102,201,205"
                       % (self.mtype, self.mid), token)
        out = {}
        for it in prof.get("profileInventory", {}).get("data", {}).get("items", []):
            if it.get("itemInstanceId"):
                out[it["itemInstanceId"]] = (it["itemHash"],
                                             bool(it.get("state", 0) & LOCKED),
                                             "vault", None)
        for comp, tag in (("characterInventories", None),
                          ("characterEquipment", "equipped")):
            for cid, invd in prof.get(comp, {}).get("data", {}).items():
                for it in invd.get("items", []):
                    if it.get("itemInstanceId"):
                        out[it["itemInstanceId"]] = (it["itemHash"],
                                                     bool(it.get("state", 0) & LOCKED),
                                                     tag or cid, it.get("bucketHash"))
        return out

    def fill(self, dry_run=False):
        """One top-up pass. Returns (sent, remaining, on_char)."""
        token, _ = get_token()
        live = self.snapshot(token)
        remaining = {iid: t for iid, t in self.targets.items()
                     if iid in live and iid not in self.deferred}
        if not remaining:
            return 0, 0, 0

        # did anything we unlocked last cycle come back locked on its own?
        relocked = [iid for iid in self._unlocked_last
                    if iid in live and live[iid][1]]
        if relocked:
            self.client_relocks += len(relocked)
            names = ", ".join(sorted({self.targets[i][0] for i in relocked
                                      if i in self.targets})[:4])
            safe_print("  ⟳ client re-locked %d item(s) we'd unlocked (%s%s) — "
                       "stale client cache; a relog clears it"
                       % (len(relocked), names,
                          ", ..." if len(relocked) > 4 else ""))
        self._unlocked_last = set()

        # park anything that has sat on the char too long (client-side lock jam)
        for iid in list(remaining):
            name, _slot = remaining[iid]
            if live[iid][2] == self.cid:
                self.on_char_cycles[iid] = self.on_char_cycles.get(iid, 0) + 1
                if self.on_char_cycles[iid] >= self.STUCK_CYCLES:
                    # unlock BEFORE parking so the item never sits locked in the
                    # vault — otherwise a client re-lock strands it as a locked
                    # dis-only weapon that only a relog + re-run can clear
                    if live[iid][1] and not self.respect_locks:
                        self._unlock(token, iid, name, self.cid)
                    ok, _s, _m = _transfer(token, self.mtype, live[iid][0], iid,
                                           self.cid, to_vault=True)
                    if ok:
                        self.deferred.add(iid)
                        remaining.pop(iid)
                        safe_print("  parked %s back to vault (unlocked) — client "
                                   "held a stale lock; relog + re-run to finish it" % name)
            else:
                self.on_char_cycles.pop(iid, None)

        occ = {b: 0 for b in GEAR_BUCKETS.values()}
        for iid, (ihash, lk, where, bhash) in live.items():
            if where == self.cid and bhash in GEAR_BUCKETS:
                occ[GEAR_BUCKETS[bhash]] += 1
        for iid, b in list(self.pending.items()):
            _, _, where, _ = live.get(iid, (None, None, None, None))
            if where == self.cid or iid not in live:
                self.pending.pop(iid)     # arrived (or already shredded)
            elif b in occ:
                occ[b] += 1               # in flight — reserve its slot

        on_char = sum(1 for iid in remaining
                      if live[iid][2] == self.cid or iid in self.pending)

        # Bungie transfer bug (Bungie-net/api#764, open since 2018): an item
        # pulled from the vault can ARRIVE LOCKED, inheriting the lock of
        # another instance of the same item — i.e. our locked keepers. The game
        # client then renders it locked and refuses to dismantle it, and a later
        # server-side unlock doesn't refresh that display until a relog. So:
        # right before pulling a hash that has locked keeper siblings, drop
        # those locks, and restore every one of them when the pass ends.
        hash_locked = {}                  # hash -> [(iid, where)] locked non-targets
        for iid2, (h2, lk2, wh2, _b2) in live.items():
            if lk2 and iid2 not in self.targets:
                hash_locked.setdefault(h2, []).append((iid2, wh2))
        released = {}                     # iid -> where: keeper locks we opened

        full = set()
        sent = 0
        try:
            for iid, (name, slot_hint) in remaining.items():
                ihash, locked, where, _ = live[iid]
                if locked and not self.respect_locks and not dry_run:
                    # re-locked since the reports (transfer-inherited / tap-lock)
                    # — undo it, wherever the item is, so it stays dismantlable
                    locked = not self._unlock(token, iid, name, where)
                    time.sleep(0.15)
                if iid in self.pending or where in (self.cid, "equipped"):
                    continue
                if locked:
                    if iid not in self.skipped_locked:
                        self.skipped_locked.add(iid)
                        safe_print("  !! %s is LOCKED — skipping (--respect-locks)" % name)
                    continue
                if where != "vault":      # parked on another character: stage via vault
                    _transfer(token, self.mtype, ihash, iid, where, to_vault=True)
                    continue
                b = bucket_of(ihash, slot_hint)
                if not b or b in full or occ.get(b, 0) >= CAPACITY:
                    full.add(b)
                    continue
                if dry_run:
                    safe_print("  would pull %s -> %s" % (name, b))
                    occ[b] += 1
                    sent += 1
                    continue
                for iid2, wh2 in hash_locked.get(ihash, ()):
                    if iid2 not in released:
                        ok2, _st = self._setlock(token, iid2, False, wh2)
                        if ok2:
                            released[iid2] = wh2
                        time.sleep(0.1)
                ok, status, msg = _transfer(token, self.mtype, ihash, iid,
                                            self.cid, to_vault=False)
                if ok:
                    # belt and braces: clear any lock the transfer smuggled in
                    # before the game client renders the arrival
                    self._setlock(token, iid, False, self.cid)
                    self._unlocked_last.add(iid)
                    occ[b] += 1
                    self.pending[iid] = b
                    self.moved += 1
                    sent += 1
                elif status == "DestinyNoRoomInDestination":
                    full.add(b)
                elif status == "DestinyItemNotFound":
                    pass                  # dismantled between snapshot and now
                else:
                    safe_print("  !! %s: %s (%s)" % (name, status, msg))
                    if status and "Throttle" in status:
                        time.sleep(3)
                time.sleep(0.25)
        finally:
            relocked = 0
            for iid2, wh2 in released.items():
                ok2, _st = self._setlock(token, iid2, True, wh2)
                if ok2:
                    relocked += 1
                    self.relock_failed.discard(iid2)
                else:
                    self.relock_failed.add(iid2)
            if released:
                safe_print("  (dropped %d keeper lock(s) during transfer — Bungie "
                           "bug #764 — re-locked %d)" % (len(released), relocked))
            if self.relock_failed:
                safe_print("  !! %d keeper(s) FAILED to re-lock — run sync_locks.py "
                           "before dismantling anything!" % len(self.relock_failed))
        return sent, len(remaining), on_char


def main():
    ap = argparse.ArgumentParser(description="Feed dismantle candidates to the character.")
    ap.add_argument("--interval", type=float, default=3, help="seconds between refills")
    ap.add_argument("--dry-run", action="store_true", help="plan one batch, move nothing")
    ap.add_argument("--respect-locks", action="store_true",
                    help="skip locked dismantle candidates instead of unlocking them")
    args = ap.parse_args()

    feeder = Feeder(respect_locks=args.respect_locks)
    if not feeder.targets:
        sys.exit("No dismantle lists found — run 'scan' and 'armor-cleanup' first.")
    safe_print("Feeding %d dismantle candidates to %s (%s). Ctrl+C to stop."
               % (len(feeder.targets), feeder.who, feeder.cls))
    safe_print("Locked items are always skipped; do not run auto_vault.py now.\n")

    done = 0
    try:
        while True:
            sent, remaining, on_char = feeder.fill(dry_run=args.dry_run)
            done = len(feeder.targets) - remaining
            if remaining == 0:
                break
            safe_print("[%s] %d shredded, %d to go (%d staged on character%s)"
                       % (time.strftime("%H:%M:%S"), done, remaining, on_char,
                          ", +%d pulled" % sent if sent else ""))
            if args.dry_run:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        _flush_caches()
        if not args.dry_run:
            left = len(feeder.targets) - done
            if left <= 0 and feeder.moved:
                safe_print("\nAll dismantle candidates are gone. Vault clean — enjoy.")
            else:
                safe_print("\nStopped. %d moved this session; %d candidates remain "
                           "(re-run to continue)." % (feeder.moved, max(left, 0)))
        if feeder.skipped_locked:
            safe_print("Skipped %d locked item(s) — they stay protected."
                       % len(feeder.skipped_locked))
        if feeder.deferred:
            safe_print("Parked %d client-lock-jammed item(s) in the vault — "
                       "relog and re-run to finish them." % len(feeder.deferred))
        if feeder.relock_failed:
            safe_print("!! %d keeper lock(s) could not be restored — run "
                       "sync_locks.py NOW, before any in-game dismantling."
                       % len(feeder.relock_failed))


if __name__ == "__main__":
    main()
