# Destiny 2 Vault Reference — Weapons & Armor (Keep/Dismantle)

> **Purpose:** A standing reference for `destiny_vault.py`, so future sessions can make
> keep-vs-dismantle decisions against the *current* Destiny 2 sandbox instead of relying
> on model training (which is likely stale). This tool classifies items by **perk/stat
> names**, so the perk and archetype names below are the authoritative vocabulary for
> writing `rules.yaml`.
>
> **Compiled:** 2026-07-01, from live web research (multiple independent sources).
> **Confidence:** Mechanics (tier system, stats, archetypes, perk pools) are cross-verified
> across several outlets. Specific *tier-list rankings* and some exact numbers are from
> third-party guide sites (Bungie's own pages are JS-rendered and couldn't be fetched
> directly) — treat those as directional and flagged inline.

---

## 0. TL;DR — the single most important context

**Destiny 2 reached its final major live-service update, "Monument of Triumph" (Update 9.7.0),
on 2026-06-09.** The sandbox is now effectively **frozen** — perk pools, archetypes, and meta
described here are expected to be permanent, with only hotfixes going forward. This is an
unusually stable moment to lock in vault decisions; there is no "wait for the next re-tune" risk.

**⚠️ Dismantling is irreversible.** Sunsetting is gone (old gear is usable at cap), BUT a
dismantled random-rolled weapon/armor piece is *gone* — it cannot be reacquired from Collections.
Only **exotics** and **curated** rolls come back from Collections. Build rules conservatively.

**Two systems changed everything since the model's likely knowledge:**
1. **Armor 3.0 / new stat system** (The Edge of Fate, ~2025-07-15) — six new stats, 0–200 scale,
   armor archetypes, Gear Tiers 1–5, set bonuses, stat tuning.
2. **Gear Tier system for weapons** (Edge of Fate → Monument of Triumph) — weapons now drop at
   Tier 1–5 and are upgraded through a tier track that folds in enhanced perks.

**Content timeline for reference:**
- **The Edge of Fate** (~2025-07-15): Armor 3.0, new stats, Gear Tiers, deterministic ammo economy.
- **Renegades** (~2025-12-02, Update 9.5.0): vault → 1000 slots, +6 armor archetypes (→12 total),
  ammo-economy refinements, exotic reworks.
- **Monument of Triumph** (2026-06-09, Update 9.7.0): FINAL major update — weapon tier-upgrading for
  world drops, ~25 new catalysts, set bonuses on every set, exotic armor → Tier 5.

---

# PART I — WEAPONS

## 1. Weapon roll structure

| Slot | Contents | Notes |
|------|----------|-------|
| Column 1 | Barrels / Blades / Bowstrings / Scopes / Launcher Barrels | Stat-shaping (range, handling) |
| Column 2 | Magazines / Arrows / Batteries / Guards | Ammo capacity, stability, handling |
| **Column 3** | **Trait 1** | First god-roll trait column |
| **Column 4** | **Trait 2** | Second god-roll trait column |
| Origin Trait | Passive tied to source/foundry | Since Witch Queen (S16); older weapons lack one |
| Masterwork | +stat, generates Orbs on multikills | — |
| Weapon Mod | Utility (backup mag, boss spec, etc.) | — |

**The god roll = the Column 3 × Column 4 pairing**, matched to the weapon's role. This is what
`rules.yaml` should key on.

### Weapon Gear Tiers (1–5)
Weapons now drop at a tier and are upgraded via the upgrade-mod socket (costs Glimmer, Ascendant
Alloys, Enhancement Prisms):
- **Tier 1** — baseline
- **Tier 2** — ~two pre-enhanced perks
- **Tier 3** — *first meaningful threshold*; enhanced perks in trait columns
- **Tier 4** — enhanced barrels/mags/mods
- **Tier 5** — ceiling: up to 3 enhanced perks per trait column, enhanced origin trait, ornament,
  Combat Flair (kill-effect) mod slot

> **Keep implication:** higher tier = strictly better shell of the same roll. Prefer the highest-tier
> copy of a given roll; a low-tier duplicate of a roll you already own at high tier is a safe dismantle.
> But **perks > tier**: a Tier 3 god roll beats a Tier 5 mediocre roll. Tier-upgrading a world drop
> **cannot add new perks** — it only enhances the perks already rolled.

## 2. Top PvE trait perks

**Damage / DPS (usually Col 4):**
| Perk | Effect |
|------|--------|
| **Bait and Switch** | Hit with all 3 weapons in a short window → +35% dmg ~10s. Dominant DPS perk. |
| **Vorpal Weapon** | Flat +dmg vs bosses/vehicles/minibosses; no ramp. |
| **Target Lock** | Dmg scales the longer you keep hitting one target (great on high-RPM). |
| **Killing Tally** | Stacking dmg per kill. |
| **Golden Tricorn** | Weapon kill +15%; matching-element ability kill → +50% for 10s. |
| **Frenzy** | After 12s in combat: +dmg/reload/handling, no babysitting. |

**Reload / ammo economy (usually Col 3, feeds the damage perk):**
| Perk | Effect |
|------|--------|
| **Reconstruction** | Auto-refills mag to double capacity while stowed. Pairs w/ Bait and Switch. |
| **Envious Assassin** | Kills before drawing overflow the mag. |
| **Envious Arsenal** | Kills with *other* weapons overflow this one (newer). |
| **Fourth Time's the Charm** | Precision hits return rounds to the mag. |

**Add-clear / ability-loop (element verbs):**
| Perk | Element | Effect |
|------|---------|--------|
| **Incandescent** | Solar | Kill → scorch/ignition spread. Premier Solar add-clear. |
| **Voltshot** | Arc | Reload after kill → jolt next target (chain lightning). |
| **Destabilizing Rounds** | Void | Kills make targets volatile. |
| **Hatchling** | Strand | Precision/final blows spawn Threadlings. |
| **Chill Clip** | Stasis | Slows/freezes; strong CC + major stopper. |
| **Jolting Feedback** | Arc | Sustained arc dmg → jolt, no reload needed (new). |
| **Repulsor Brace** | Void | Kill a Void-debuffed target → Void overshield. Elite w/ Destabilizing. |
| **Attrition Orbs** | — | Sustained dmg generates Orbs of Power (new, Renegades). |
| **Onslaught** | — | Bonus dmg striking multiple targets (Renegades). |

## 3. Top PvP perks
| Perk | Effect |
|------|--------|
| **Opening Shot** | First shot: bonus range + accuracy. Top HC perk. |
| **Eye of the Storm** | Lower health → better handling/accuracy. Clutch. |
| **Snapshot Sights** | Much faster ADS. Near-mandatory on shotguns. |
| **Moving Target** | +movement speed & aim assist while ADS-strafing. |
| **Headseeker** | Body shots buff follow-up precision (pulses/scouts). |
| **Zen Moment** | Damage reduces recoil / boosts stability. |
| **Precision Instrument** | Consecutive precision hits ramp precision dmg. |
| **Slideshot / Slickdraw / Threat Detector** | Slide reload+range / instant handling / proximity handling. |
| **Explosive Payload / Timed Payload** | Splash dmg → consistency + flinch. |

PvP meta: Hand Cannons, Pulses, Scouts lead primaries; Shotguns & Fusions lead specials.
High **Health** stat (old Resilience) is considered mandatory for flinch reduction.

## 4. Origin traits (notable)
| Trait | Effect | Best for |
|-------|--------|----------|
| Veist Stinger | Kills chance to auto-refill mag from reserves | PvE economy |
| Vanguard's Vindication | Final blows heal | PvE survivability |
| Omolon Fluid Dynamics | Top half of mag reloads faster/more stable | Both |
| Suros Synergy | Reload boosts handling, reduces flinch | Best PvP trait |
| Bitterspite | Taking damage speeds next reload | PvE |
| Souldrinker | Hits before reload restore health | PvE survivability |
| Alacrity | Last fireteam member alive → big range/AA/reload/stability | Solo/PvP |

## 5. Meta weapons (mid-2026) — *directional, third-party tier lists*
- **PvE legendary:** Zaouli's Bane (Solar HC), Cataclysmic (Solar LFR), Forbearance (Wave GL).
- **PvE exotic S-tier:** Fafnir (new Void LFR — top new exotic), Witherhoard, Trinity Ghoul,
  Gjallarhorn, Microcosm, Whisper of the Worm, Buried Bloodline, Still Hunt, Sunshot, Choir of One,
  Tractor Cannon (debuff).
- **PvP exotic:** Ace of Spades, The Chaperone, Conditional Finality, Le Monarque.
- **New final-year exotics:** Fafnir (Void LFR), The Turncoat (Void HC), Cull's Shadow (Poison Fusion).

## 6. Sandbox changes affecting weapon keep-value
- **Primary dmg +30–40% vs minors** (PvE) → strong primaries with element verbs are worth keeping.
- **Special +20% vs elites** (excl. snipers, rocket pulses, rocket sidearms, swords, Choir of One).
- **Deterministic ammo economy:** Special/Heavy ammo meters fill from kills → guaranteed brick; scales
  with the new **Ammo Generation** stat. Favor ammo-efficient specials.
- **Rocket Pulse Rifles nerfed** out of endgame DPS (deprioritize, don't delete).
- **Auto Rifles → 400 RPM** baseline.
- **Every exotic now has a catalyst** (Monument added ~25 new / reworked ~9) + exotic primaries +40%
  vs minors → most exotics are viable and worth keeping.

## 7. Weapon keep/dismantle framework
1. **Perk pairing first.** A setup perk (Col 3) + a payoff perk (Col 4) that stack for the weapon's role.
2. **Tier second.** Prefer highest-tier copy; low-tier dup of an owned high-tier god roll = dismantle.
3. **Element coverage.** Keep ≥1 strong option per element (match 200% shield dmg + subclass verbs).
4. **Role coverage by ammo type.** One reliable Primary add-clear, one Special, one Heavy DPS.
5. **Crafted vs world drop:**
   - Craftable → keep **one** crafted copy (or just the pattern); dismantle random dups.
   - Non-craftable god roll → worth keeping **distinct perk-combo drops**, since tier-upgrading can't
     add perks (can't reshape a world drop's columns).
6. **Exotics → keep essentially all** (catalysts + Collections re-pull; low vault cost).

**God-roll patterns by role:**
| Role | KEEPER | DISMANTLE |
|------|--------|-----------|
| Heavy DPS | Reconstruction/Envious + Bait and Switch (or Vorpal) | No Col-4 damage perk; low-tier dup |
| PvE add-clear primary | Element verb (Incandescent/Voltshot/Destabilizing/Hatchling) + feeder | Two pure-stat perks; off-element |
| PvE special (CC/debuff) | Chill Clip / Repulsor+Destabilizing / Voltshot fusion | PvP-only perks on a PvE weapon |
| PvP primary | Opening Shot/Eye of the Storm/Zen/Precision + Snapshot/Moving Target | Slow PvE traits, bad range |
| PvP special | Snapshot + Opening Shot/Threat Detector/Slickdraw | No handling/consistency perk |

---

# PART II — ARMOR (Armor 3.0)

## 8. The new stat system

Six new stats replace the old six (convert **1:1** on existing armor):

| New stat | Replaces | 0–100 (primary effect) | 101–200 (bonus effect) |
|----------|----------|------------------------|------------------------|
| **Weapons** | Mobility | +reload/handling, +15% dmg vs minors/majors | +15% dmg vs bosses; double-ammo bricks (guaranteed @200) |
| **Health** | Resilience | +HP per Orb, +flinch resist | +shield capacity, faster shield recharge |
| **Class** | Recovery | −65% class-ability cooldown, +ability energy | Overshield on class-ability cast (+40 PvE/+20 PvP) |
| **Grenade** | Discipline | −65% grenade cooldown, +energy | +65% grenade dmg PvE / +20% PvP |
| **Super** | Intellect | +Super energy (NOT base cooldown) | +45% Super dmg PvE / +15% PvP |
| **Melee** | Strength | −65% melee cooldown, +energy | +30% melee dmg PvE / +20% PvP |

- **Range is now 0–200** (was 0–100). **Linear per-point scaling — no tier breakpoints** ("145 beats 143").
- **100 ≈ old maxed stat.** Crossing **100 unlocks a distinct second benefit** per stat (the 101–200 column).
- **Health is widely considered the weakest PvE stat**, often skippable. Base survivability DR (~30% PvE,
  old Resilience 100) is now **fixed/baked in** for all Guardians, independent of the Health stat.
- Damage-resistance sources stack **multiplicatively** (diminishing returns).

## 9. Armor archetypes (12 total)

Every Edge-of-Fate+ armor piece has a randomly-assigned **archetype** biasing two stats. Renegades
doubled the count from 6 → **12**. Each piece rolls exactly 3 stats: **primary (+30 max) / secondary
(+25) / tertiary (+20, random from the remaining four)**.

| Archetype | Primary | Secondary | Era |
|-----------|---------|-----------|-----|
| Gunner | Weapons | Grenade | Edge of Fate |
| Bulwark | Health | Class | Edge of Fate |
| Specialist | Class | Weapons | Edge of Fate |
| Paragon | Super | Melee | Edge of Fate |
| Grenadier | Grenade | Super | Edge of Fate |
| Brawler | Melee | Health | Edge of Fate |
| Siegebreaker | Health | Grenade | Renegades |
| Skirmisher | Melee | Weapons | Renegades |
| Demolitionist | Grenade | Class | Renegades |
| Colossus | Super | Health | Renegades |
| Reaver | Class | Melee | Renegades |
| Powerhouse | Weapons | Super | Renegades |

### ⚠️ Reconciled analysis — which stat pairs are STILL unobtainable on new armor
Older guides say "keep legacy armor with impossible stat combos like **Weapons+Super**." **That is now
outdated** — Powerhouse (Renegades) provides Weapons+Super. Cross-referencing the full 12-archetype
list, of the 15 possible stat pairs, **only 3 are NOT available** as an armor's top-two stats:

- **Weapons + Health**
- **Class + Super**
- **Grenade + Melee**

So the *only* legacy (pre-Edge-of-Fate) armor worth keeping for a rare stat spread is a piece whose two
highest converted stats form one of those three pairs (and even then, only if the totals are genuinely
high). Everything else is reproducible on modern, higher-ceiling gear. *(Derived from the archetype
table above; verify in-game if a borderline piece is at stake.)*

## 10. Gear Tiers for armor (1–5)

Tier governs total stat budget. **Tier 5 caps at 75 total (30/25/20)** — well-confirmed. Lower-tier
ranges differ ~±5 between sources; treat the *shape* (each tier ≈ +5–6, T5 = 75) as reliable:

| Tier | Approx total | Notes |
|------|-------------|-------|
| Tier 1 | ~48–57 | base |
| Tier 2 | ~53–63 | (exotics historically dropped here) |
| Tier 3 | ~59–69 | |
| Tier 4 | ~65–75 | **11 mod energy** (vs 10) — key breakpoint |
| Tier 5 | **75 (30/25/20)** | 11 energy + **stat-tuning slot** (after masterwork) |

- **Tier 5 does NOT have more raw stats than a high Tier 4** — its edge is the **tuning slot**.
- **Mod energy:** Tiers 1–3 = 10; **Tier 4 & 5 = 11**. Tuning mods cost **0** energy.
- **Masterworking** adds **+5 spread across the three stats NOT boosted by the archetype**.

### Stat tuning (Tier 5 only)
- Unlocks after masterworking. One of the six stats is randomly the **"tuned" stat** (cannot be rerolled).
- Choose either: **Swap mod (+5/−5)** move 5 points from any stat into the tuned stat; or **Balanced mod**
  +1 to each of the three lowest stats. Used to chase breakpoints (e.g., push a stat over 100 or toward 200).

## 11. Set bonuses
- Every legendary armor **set** gives a **2-piece** bonus and a stronger **4-piece** bonus (4pc keeps the
  2pc active too). ~56 sets after Monument of Triumph. Think "origin traits for armor."
- Run a **4pc + 1 exotic**, or **2pc + 2pc + 1 exotic**.
- **Exotic armor does NOT count toward set-piece thresholds** (separate slot) — so a full 4pc set + any
  exotic still grants both bonuses. Legendary **class items** DO count as a set piece.
- Keep pieces that complete a bonus you actively run, but **don't hoard for set bonuses** — they're flexible
  round-outs, not build-defining.

## 12. Exotic armor
- New exotic drops use Armor 3.0, biased toward a **fixed/thematic archetype**; Ghost **Armorer mods** raise
  the odds of a desired archetype (now ~1-in-2, up from 1-in-3).
- **You cannot directly reroll an owned exotic's stats.** You influence the roll before it drops (Ghost mods,
  Ada-1 focusing/vouchers, Master Rahool focusing).
- **Post–Edge-of-Fate exotic armor is now Tier 5** (Monument of Triumph) with full tuning-mod access; no
  re-farming needed.
- **Legacy exotics** convert 1:1 but gain no archetype/set/tuning → re-acquire/refocus the ones you use to
  get a modern archetype roll (esp. Weapons/Super). Keep an old copy only if its converted stats are exceptional.
- **Exotic class items:** guaranteed spread **30/20/13 = 63 total**; **left-column perk sets the archetype**,
  **right-column perk sets the tertiary stat**. Worth keeping for the guaranteed distribution.

## 13. Armor keep/dismantle framework
1. **Tier gate first.** Default-keep **Tier 4+ (≥~70)**; dismantle below Tier 3 unless it's a rare-combo legacy
   piece (§9). **2026 practical target: high-stat Tier 4 (73+)**; Tier 5's tuning slot is min-max icing for
   endgame/contest players, not mandatory.
2. **Archetype fit.** Keep pieces whose primary/secondary match a build you run. Rough build→archetype:
   - DPS: **Gunner** (Weapons+Grenade), **Powerhouse** (Weapons+Super), **Paragon** (Super+Melee)
   - Grenade builds: **Grenadier / Demolitionist / Siegebreaker**
   - Melee builds: **Brawler / Skirmisher / Reaver**
   - Survivability: **Bulwark** (Health+Class) / **Colossus**
3. **Total stats.** Up to 75; every point matters on the 0–200 scale.
4. **Set membership.** Bonus for pieces completing a set you use.
5. **Legacy armor is generally dismantle-fodder** — no archetype/set/tier — *except* the 3 unobtainable
   stat pairs in §9, or genuinely high converted totals you still use.

---

# PART III — VAULT MANAGEMENT

## 14. Space & pressure
- **Vault cap: 1,000 slots** (Renegades, up from 700). Revamped filtering (by power/slot/date/rarity).
- Pressure eased but real — Armor 3.0 (multiple archetype sets per build) + tierable weapons still fill it.
  Community advice: stay lean (many suggest keeping well under ~400 curated items).

## 15. Reacquire rules (what's safe to trash)
- **In Collections = safe to trash:** exotics, blue gear, **curated** legendary rolls (reacquirable for
  Glimmer/materials).
- **NOT reacquirable (real judgment needed):** **randomly-rolled** legendary weapons & armor, and
  high-stat exotic *armor* (Collections re-pull comes back at low stats).

## 16. Always-keep vs safe-to-trash
**Almost always KEEP:** exotic armor with high stats/good archetype; crafted patterns / one crafted copy;
meta weapons & role staples per element/ammo type; new **Tier 4/5 armor** in build-matching archetypes;
non-craftable legendary **god rolls**; legacy armor only with an unobtainable stat pair (§9).

**Generally SAFE to dismantle:** exotic weapons you don't run (Collections); duplicates (keep best roll);
old low/mid-stat legacy armor outclassed by tiered gear; blue gear & curated legendaries; "infusion fodder"
(hoarding is outdated); low-tier dup of an owned high-tier god roll.

## 17. How this maps to `rules.yaml` (and to DIM/light.gg)
This tool mirrors **DIM wishlists** (`voltron.txt`) and **light.gg Roll Appraiser**: match perk-name
combinations → god-roll rules → keep/junk. In `rules.yaml`, each weapon's `require` groups are the
Col-3 / Col-4 columns; list acceptable perks per column as alternatives (see §7 patterns). Because the tool
matches by **exact in-game perk/stat name**, use the names in §2/§3/§8/§9 verbatim.

> **Armor caveat:** the current `rules.yaml`/`classify()` logic matches *perk names* — great for weapons, but
> armor keep-value is driven by **archetype + tier + total stats**, which are not socket "perks" in the same
> way. To rank armor, the tool would need to read the instance stats (component 300) + item tier + archetype,
> not just socket plug names. Flag for a future enhancement if we want armor rules.

## 18. Common mass-dismantle mistakes
1. Trashing non-reacquirable random rolls thinking they're in Collections.
2. Deleting legacy armor with a genuinely unobtainable stat pair (§9) before checking.
3. Deleting the last copy of a still-meta exotic and eating the re-grind.
4. Dismantling a good non-craftable roll (can't reshape a world drop's perks after).
5. Dismantling in the moment instead of **tag-then-purge** (lock keepers first — this tool's `lock-keepers`).
6. Panic-cleaning at 900–1000 slots → rushed bad deletes. Stay lean continuously.

---

## Sourcing & uncertainty summary
- **Reliable (multi-source):** new 6 stats + 1:1 mapping + 0–200 scale; 12 armor archetypes & pairings;
  Tier 5 = 75 (30/25/20); 2/4-piece set bonuses; exotics don't count toward sets; vault = 1000; Monument of
  Triumph = final update (2026-06-09); core weapon perk pool.
- **Directional / flagged:** specific weapon tier-list rankings (third-party); exact Tier 1–4 stat ranges
  (sources differ ±5); precise numeric effects of the newest Renegades perks; exact per-tier enhanced-perk
  counts; material cost of swapping tuning mods (unconfirmed).
- **Derived here:** the "only 3 unobtainable stat pairs" analysis (§9) is computed from the 12-archetype
  table, correcting older "Weapons+Super is impossible" guidance.
- Bungie.net primary pages are JS-rendered and could not be fetched directly; claims rest on reputable
  secondary outlets (TheGamer, GamesRadar, PC Gamer, Dot Esports, light.gg, DIM wiki, Nerdschalk, Sportskeeda)
  plus Bungie search snippets. Spot-verify exact numbers against live Bungie patch notes if precision matters.
