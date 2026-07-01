# Vault Cleanup Plan

> The keep/dismantle methodology `destiny_vault.py` will implement, encoding the owner's policy
> (see `preferences.yaml`). Weapons only for now (armor keep-value needs archetype/tier logic — see
> `DESTINY_REFERENCE.md` §17). The tool only ever **locks** keepers; you dismantle in-game.

## Policy (from preferences.yaml)
- Perk priority: **boss DPS / ad-clear > ability regen > handling / awkward**.
- Keep weapons with their own identity (chain-reaction payoffs) over boring utility.
- **Coverage:** keep ≥1 copy of any weapon that is the *only* source of a perk you own (vault-relative).
- **Duplicates:** keep meaningfully-different rolls; dismantle only *exact* duplicate rolls (or dupes
  that don't fit the priorities).
- **Exotics:** keep ≥1 of each; dismantle exotic dupes (except random-roll exotics like Ergo Sum, where
  distinct frames count as distinct rolls).

## Classification passes (run in order; first KEEP wins)
An item is **KEEP** if any pass keeps it; otherwise it falls through to DISMANTLE.

**Pass 0 — Never touch (hard protect)**
- Anything equipped in an in-game **loadout** (component 206) or currently equipped.
- Crafted weapons / weapons with a pattern you rely on (flag, don't auto-dismantle).

**Pass 1 — God-roll KEEP**
- Per-weapon rules (from `research/weapons-pve-perks.md`): keep if it has ≥1 perk from each desired
  column. This is today's `rules.yaml` logic, seeded with PvE boss-DPS / ad-clear rolls.

**Pass 2 — Sole-source / rare-perk coverage**
- For every trait perk present in the vault, if **exactly one** weapon has it, KEEP that weapon —
  even if the perk is weak. (Preserves options. Vault-relative, so no global rarity table needed.)
- Tiebreak with global rarity (light.gg "Randomly Rolls On") only when choosing which of several
  copies to keep.

**Pass 3 — Exotic coverage**
- Keep ≥1 copy of each unique exotic. For fixed-perk exotics, extras are DISMANTLE.
- For **random-roll exotics** (Ergo Sum, etc.), treat distinct frames/perk-sets as distinct rolls
  (Pass 4 logic) rather than flat dupes.

**Pass 4 — Duplicate collapse**
- Group remaining copies by (weapon name + perk signature). Within a group:
  keep the best copy (highest Gear Tier, then enhanced perks); extras with the **same signature** =
  DISMANTLE. Distinct signatures are kept (your multiple-Mountaintops/Psychopomps case).

**Pass 5 — Fall-through**
- Anything not kept by 0–4 → **DISMANTLE candidate**, unless it's the last copy of a weapon you have
  no other option for in that role/element (safety net; surfaced as REVIEW, not auto-dismantle).

## Output
- Three lists: **KEEP**, **DISMANTLE**, **REVIEW** (ambiguous — needs a human call).
- Write to `vault_report.json` (already gitignored).

## Safe execution order
1. `scan` — dry run, produces the three lists. **Change nothing.**
2. Review the report (esp. REVIEW + the DISMANTLE list). Adjust `rules.yaml` / policy as needed.
3. `lock-keepers` — locks every KEEP via the API (asks for confirmation first).
4. In-game: dismantle everything **not** locked (locked items are safe from mass-dismantle).
5. Re-`scan` to confirm.

## First concrete targets for this vault (see VAULT_REPORT.md)
- ~254 duplicate copies — the bulk of the win.
- Flat exotic dupes (Outbreak ×2, Riskrunner ×2, Lord of Wolves ×2, etc.) → 1 each.
- Ergo Sum ×14 → keep a few distinct frames, trim the rest.
- **Protect:** Taipan (Triple Tap + Focused Fury), Envious Arsenal / Collective Action sole sources,
  and everything in your loadouts.
