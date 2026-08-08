# CLAUDE.md — orientation for a cold session

This repo is **destiny_vault**: a local Python tool that reads a user's Destiny 2 vault via
the Bungie API, classifies items against god-roll rules in `rules.yaml`, and can lock keepers.
Read this before doing vault work.

## First moves in a fresh clone
- Run with the project venv. **The owner is on Windows**, so the interpreter is
  `./venv/Scripts/python.exe destiny_vault.py <cmd>` — there is no `venv/bin/`. (On
  macOS/Linux it's `./venv/bin/python`.) If there's no `venv/`, create one and
  `pip install pyyaml`. Scripts that `import destiny_vault` need `PYTHONPATH=<repo root>`
  (or run from the repo root).
- Console stdout is **cp1252** on this machine, so piping output through a file can mangle
  non-ASCII item names (`Mataiodoxía`). Set `PYTHONIOENCODING=utf-8` when redirecting.
- **`preferences.yaml` may not exist** (it's gitignored/personal). If it's missing, that's normal —
  copy `preferences.example.yaml` to it, or just ask the user about their playstyle. If it *does*
  exist, read it first: it says which class they play and how they build (this drives keep-rules).
- **Read `DESTINY_REFERENCE.md` before any keep/dismantle reasoning.** The Destiny sandbox changed
  a lot (Armor 3.0, weapon Gear Tiers) and model training is likely stale. `research/` holds the
  cited sources behind it.
- **`research/god-rolls.md` is the official per-weapon god-roll reference** (researched 2026-08-07,
  confidence-rated). `rules.yaml` is generated from its verdicts — update the doc first, then
  mirror into rules. Never dismantle on a LOW-confidence entry alone.

## Commands
Setup path: `setup` (creds) → `login` (OAuth) → `whoami`.
Read-only: `loadouts`, `scan`, `armor-scan [build]`, `armor-cleanup`.
Writes: `lock-keepers`, `unlock-all`, `armor-cleanup --lock` (lock state only);
`sync_locks.py` (repo root) diff-syncs lock state to the latest reports and is the
preferred path after re-classifying — flips only mismatches instead of the full
unlock-all → relock cycle (`--dry-run` previews);
`equip-armor <build>` and `apply-loadout <build> <slot>` write to the **live character**
(must be in orbit) — both take `--dry-run`, `--exotic`, `--weapon`, `--balance`.
Requires the user to have already run `setup`/`login` (needs their Bungie app + token).
`dismantle_all.py` chains the full pipeline (auto_vault --once → scan → armor-cleanup →
sync_locks → auto_dismantle --feed), aborting on any step failure; `--dry-run` previews
everything and skips the shred.
`dashboard.py` serves a button-panel web UI for all of the above (plus the auto_* loops)
at http://127.0.0.1:8765 — stdlib-only, streams output, stdin box for setup/login, and
Stop sends Ctrl+Break which `_job_runner.py` remaps to KeyboardInterrupt so `finally:`
cleanup (feed_dismantle's lock restore) still runs. Only registry-listed tools can run.

## How classification works
`rules.yaml`: each key is an exact in-game item name; `require` is a list of perk-name groups;
an item is KEEP only if it has ≥1 perk from **every** group. Perk names are case-sensitive and must
match in-game text. `scan` writes `vault_report.json`.

**Power-floor protection** (both scans, applied last): the highest-power item in each
bucket is never dismantled — max power counts your best item per slot, so shredding it
would lower it. Weapons: per Kinetic/Energy/Power slot; armor: per (class, slot). Ties
at the max all survive; they're promoted to KEEP with reason "highest power … never
dismantle". Vault weapons don't carry their slot, so `weapon_bucket_of()` resolves it
from the item def (cached in `.weapon_defs_cache.json`; pre-existing entries are
upgraded with one fetch each on first use).

Two perk sets, and they are **not** interchangeable:
- `TRAIT_PERKS` is **policy-scoped** — it drives sole-source coverage and duplicate collapse.
  Don't widen it just to make a rule match; that silently changes what gets dismantled.
- `rule_perks(rules)` folds every perk named in `rules.yaml` into god-roll matching only
  (`w["rule_pool"]`). This exists because rule perks outside `TRAIT_PERKS` used to be filtered
  out before matching, so those rules silently under-fired. `scan` now warns about rule perks
  found on no owned weapon (usually a typo — matching is exact and case-sensitive).

## Gotchas learned the hard way
- **Bungie profile component numbers:** vault=102, char inventory=201, equipped=205,
  **characters=200, loadouts=206**, instances=300 (this is where armor `gearTier` lives),
  **item stats=304**, sockets=305 (active plugs), **reusable plugs=310** (every perk an item
  *can* swap to — required for high-Gear-Tier weapons). Note `1100` is *Metrics*, not loadouts.
  Armor stats are **304, not 300** — 300 carries the instance/gearTier, not the stat block.
- **`def_name()`**: item defs store the label in `displayProperties.name`, but loadout
  name/color/icon defs use a top-level `name` field. The lookup falls back to that (don't "fix" it back).
- **Loadout items** reference gear only by `itemInstanceId`; map instanceId→itemHash from the
  102/201/205 inventories to name them. Subclass config (super/aspects/fragments) is in the
  subclass item's `plugItemHashes`. Some plug hashes are empty/invalid and error — guard the lookup.
- **`.manifest_cache.json`** caches hash→name. If you change lookup logic, purge stale entries
  (e.g. ones cached as the raw hash) or they'll persist.
- **The "phantom re-lock" root cause (proven 2026-08-08): Bungie-net/api#764**, an open-since-2018
  Bungie bug — a vault→character transfer can deliver the item LOCKED, inheriting the lock from
  another instance of the same itemHash (i.e. our locked keepers). Evidence: every wrongly-locked
  staged dismantle item had a locked same-hash sibling; zero locks appeared without one; vault
  items never affected. feed_dismantle works around it (drops keeper-sibling locks around each
  transfer, restores them in a `finally`, unlocks each arrival immediately). The in-game client
  renders the arrival's lock state once and won't refresh on API unlocks — a relog clears it.
- **SnapshotLoadout LOCKS every item it captures** (Destiny auto-locks in-game-loadout members) —
  a second, real lock path, though not the phantom one above. `plan_weapons` is report-aware:
  verdict (KEEP > REVIEW > unclassified > DISMANTLE) outranks location, ties break toward most
  matched god-roll perks. Don't "simplify" the rank back to location-only.

## Safety
Dismantles are irreversible; only exotics/curated rolls re-pull from Collections. The tool only
**locks** — never dismantles — but always show the KEEP/DISMANTLE report before the user mass-deletes.
Never commit `.destiny_config.json` / `.destiny_token.json` / `preferences.yaml` (all gitignored).

- **Asymmetry to know about:** `lock-keepers` locks KEEP+REVIEW but does **not** unlock items that
  became DISMANTLE candidates since a previous run, whereas `armor-cleanup --lock` locks survivors
  *and* unlocks its dismantle list. So a re-scan can leave stale locks on weapons you now want gone;
  `unlock-all` then `lock-keepers` is the clean-slate path. Left as-is deliberately — making
  `lock-keepers` auto-unlock would widen what an in-game mass-dismantle deletes.
- Any file that reveals inventory (`*_report.json`, ad-hoc dumps) must stay out of git — the GitHub
  repo is public. `.gitignore` covers these by pattern; put throwaway output in `scratch/`.
