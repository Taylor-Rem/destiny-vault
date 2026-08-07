# Vault Cleanup Plan

> The keep/dismantle methodology `destiny_vault.py` implements, encoding the owner's policy
> (see `preferences.yaml`). The tool only ever **locks** keepers; you dismantle in-game.
>
> **Status: shipped.** Weapons run through the passes below (`scan` / `lock-keepers`). Armor is
> also done, but on a *separate* track — archetype + Gear Tier + stats rather than perk rules
> (`armor-cleanup`, `classify_armor()`; see `DESTINY_REFERENCE.md` §13 and §17). This doc describes
> the **weapon** passes.

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
- **Crafted weapons — ALWAYS KEEP & LOCK, no exceptions** (detected via item `state`
  flag 8). Crafted rolls can't be re-obtained by pulling from Collections, so they are
  never dismantle candidates regardless of roll. `scan` marks them "crafted (never
  dismantle)" and `lock-keepers` locks them.

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
- Group remaining copies by weapon name, best copy first. The best copy always survives.
- A lesser copy is only a DISMANTLE when a **kept copy strictly covers it**: the kept copy can roll
  every *valued* perk this one can (pool subset, not just the slotted perk) **and** is at an equal or
  higher Gear Tier. Comparing can-roll pools rather than perk signatures means a copy is never
  trashed merely because its god roll wasn't the perk currently slotted.
- Anything not strictly covered is a **distinct roll → REVIEW**, never an auto-dismantle
  (your multiple-Mountaintops/Psychopomps case).
- **Exotics are stricter still:** only a byte-identical roll counts as a duplicate, because
  random-rolled exotics (Ergo Sum frames) carry distinguishing perks outside `TRAIT_PERKS` that
  subset logic would wrongly collapse.

**Pass 5 — Fall-through**
- Anything not kept by 0–4 → **DISMANTLE candidate**, unless it's the last copy of a weapon you have
  no other option for in that role/element (safety net; surfaced as REVIEW, not auto-dismantle).

## Output
- Three lists: **KEEP**, **DISMANTLE**, **REVIEW** (ambiguous — needs a human call).
- Write to `vault_report.json` (already gitignored).

## Safe execution order
1. `unlock-all` — clean slate. Do this if you've locked keepers before, because `lock-keepers`
   locks survivors but does **not** unlock items that have since become DISMANTLE candidates,
   so stale locks would otherwise survive your purge.
2. `scan` — dry run, produces the three lists. **Changes nothing.**
3. Review the report (esp. REVIEW + the DISMANTLE list). Adjust `rules.yaml` / policy as needed.
4. `lock-keepers` — locks every KEEP **and REVIEW** via the API (asks for confirmation first),
   so the only unlocked weapons left are the DISMANTLE candidates.
5. In-game: dismantle everything **not** locked (locked items are safe from mass-dismantle).
6. Re-`scan` to confirm.

Armor is the same shape but one command: `armor-cleanup` to review, then `armor-cleanup --lock`,
which locks keep+review+off-class *and* unlocks its dismantle list in a single pass.
