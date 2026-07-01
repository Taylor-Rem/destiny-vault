# CLAUDE.md — orientation for a cold session

This repo is **destiny_vault**: a local Python tool that reads a user's Destiny 2 vault via
the Bungie API, classifies items against god-roll rules in `rules.yaml`, and can lock keepers.
Read this before doing vault work.

## First moves in a fresh clone
- Run with the project venv: `./venv/bin/python destiny_vault.py <cmd>`. If there's no `venv/`,
  create one and `pip install pyyaml`. Scripts that `import destiny_vault` need
  `PYTHONPATH=<repo root>` (or run from the repo root).
- **`preferences.yaml` may not exist** (it's gitignored/personal). If it's missing, that's normal —
  copy `preferences.example.yaml` to it, or just ask the user about their playstyle. If it *does*
  exist, read it first: it says which class they play and how they build (this drives keep-rules).
- **Read `DESTINY_REFERENCE.md` before any keep/dismantle reasoning.** The Destiny sandbox changed
  a lot (Armor 3.0, weapon Gear Tiers) and model training is likely stale. `research/` holds the
  cited sources behind it.

## Commands
`setup` (creds) → `login` (OAuth) → `whoami` → `loadouts` → `scan` → `lock-keepers`.
Requires the user to have already run `setup`/`login` (needs their Bungie app + token).

## How classification works
`rules.yaml`: each key is an exact in-game item name; `require` is a list of perk-name groups;
an item is KEEP only if it has ≥1 perk from **every** group. Perk names are case-sensitive and must
match in-game text. `scan` writes `vault_report.json`.

## Gotchas learned the hard way
- **Bungie profile component numbers:** vault=102, char inventory=201, equipped=205, instances=300,
  sockets=305, **characters=200, loadouts=206**. Note `1100` is *Metrics*, not loadouts.
- **`def_name()`**: item defs store the label in `displayProperties.name`, but loadout
  name/color/icon defs use a top-level `name` field. The lookup falls back to that (don't "fix" it back).
- **Loadout items** reference gear only by `itemInstanceId`; map instanceId→itemHash from the
  102/201/205 inventories to name them. Subclass config (super/aspects/fragments) is in the
  subclass item's `plugItemHashes`. Some plug hashes are empty/invalid and error — guard the lookup.
- **`.manifest_cache.json`** caches hash→name. If you change lookup logic, purge stale entries
  (e.g. ones cached as the raw hash) or they'll persist.

## Safety
Dismantles are irreversible; only exotics/curated rolls re-pull from Collections. The tool only
**locks** — never dismantles — but always show the KEEP/DISMANTLE report before the user mass-deletes.
Never commit `.destiny_config.json` / `.destiny_token.json` / `preferences.yaml` (all gitignored).
