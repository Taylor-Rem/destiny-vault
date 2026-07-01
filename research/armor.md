# Research backup — Armor 3.0 (stats, archetypes, tiers, tuning, set bonuses)

> Raw research with full source citations, compiled 2026-07-01 from live web sources.
> Synthesized version in `../DESTINY_REFERENCE.md` (Part II). This file preserves per-claim URLs.

---

## A. New stat system

Introduced with The Edge of Fate (2025-07-15) as "Armor 3.0"; current through Renegades (Nov 2025) and
Monument of Triumph (June 2026). Renegades did NOT overhaul the stat framework itself.

Six new stats (map 1:1 from old): **Weapons** (Mobility), **Health** (Resilience), **Class** (Recovery),
**Grenade** (Discipline), **Super** (Intellect), **Melee** (Strength).

| Stat | 0–100 primary | 101–200 bonus |
|------|---------------|---------------|
| Weapons | +10% reload/handling, +15% dmg vs minors/majors (primary/special), +5% vs Guardians | +15% dmg vs bosses; +6% PvP; double ammo bricks (guaranteed @200) |
| Health | +70 HP/Orb, +10% flinch resist | +20 shield capacity; shields recharge +25% faster |
| Class | −65% class cooldown, +~190% ability energy | Overshield on class-ability cast (+40 PvE/+20 PvP, ~5–10s) |
| Grenade | −65% grenade cooldown, +~190% energy | +65% grenade dmg PvE / +20% PvP |
| Super | +~190% Super energy (NOT base cooldown) | +45% Super dmg PvE / +15% PvP |
| Melee | −65% melee cooldown, +~190% energy | +30% melee dmg PvE / +20% PvP (incl. punches, Glaive) |

Range now 0–200 (was 0–100). Linear per-point scaling, no breakpoints. 100 = old max; 101–200 unlocks a
distinct second benefit. Health widely called weakest PvE stat. Base ~30% PvE DR now fixed for all
Guardians, independent of Health. DR sources stack multiplicatively. Sources:
- TheGamer Armor 3.0 guide (Aug 1 2025): https://www.thegamer.com/destiny-2-edge-of-fate-armor-rework-guide/
- Boosting-Ground Armor 3.0 (Jul 13 2025): https://boosting-ground.com/Destiny2/guides/pve-guides/armor-3-0-complete-guide
- LFCarry armor guide (Jan 20 2026): https://blog.lfcarry.com/destiny-2-armor-guide/
- GameRant best PvE stats: https://gamerant.com/destiny-2-best-pve-stats-armor/
- Sportskeeda stat rework: https://www.sportskeeda.com/mmo/complete-stat-rework-explained-destiny-2-the-edge-fate
- GamesRadar Armor 3.0: https://www.gamesradar.com/games/destiny/destiny-2-armor-3-0/
- PC Gamer Armour 3.0 stats/archetypes: https://www.pcgamer.com/games/fps/destiny-2-armour-3-0-stats-archetypes/
- Bungie Help — Your Guardian: https://help.bungie.net/hc/en-us/articles/45080200239892--3-Your-Guardian-Subclasses-Abilities-and-Gear

**Uncertainty:** Class PvP overshield reported +20 (most) or +10 HP (lfcarry). Bungie Dev Insights pages
JS-rendered, not fetchable directly.

---

## B. Armor archetypes (12 total)

Every Edge-of-Fate+ piece gets a random archetype biasing 2 stats. Renegades doubled 6 → 12. Each piece
rolls 3 stats: primary (+30) / secondary (+25) / tertiary (+20, random from remaining four).

Original 6 (Edge of Fate): Gunner (Weapons/Grenade), Bulwark (Health/Class), Specialist (Class/Weapons),
Paragon (Super/Melee), Grenadier (Grenade/Super), Brawler (Melee/Health).
New 6 (Renegades): Siegebreaker (Health/Grenade), Skirmisher (Melee/Weapons), Demolitionist (Grenade/
Class), Colossus (Super/Health), Reaver (Class/Melee), Powerhouse (Weapons/Super).

**Derived (not from a single source):** of 15 possible stat pairs, the 12 archetypes cover all but 3 —
**Weapons+Health, Class+Super, Grenade+Melee** are the only pairs NOT obtainable as an armor's top two.
This corrects older guides that called Weapons+Super "impossible" (now Powerhouse). Sources:
- Bungie TWID 06/26/2025: https://www.bungie.net/7/en/News/Article/twid_06_26_2025
- Bungie D2_Director tweet: https://x.com/D2_Director/status/1938311501758271746
- dotesports archetypes: https://dotesports.com/destiny/news/destiny-2-armor-archetypes
- Yardbarker new archetypes: https://yardbarker.com/entertainment/articles/destiny_2_armor_30_changes_sees_new_archetypes_and_exotic_armor_changes/s1_17456_43918158
- Skycoach Armor 3.0 (Jun 19 2026): https://skycoach.gg/blog/destiny/articles/armor-3-0-guide

Exotic armor biases toward a fixed/thematic archetype; Ghost Armorer mods raise desired-archetype odds
(1-in-3 → 1-in-2). Exotic class items: 30/20/13 (63 total), left-column perk = archetype, right-column
perk = tertiary stat. Masterworking adds +5 across the three non-archetype stats.

---

## C. Gear Tiers (armor)

Tier 5 caps at 75 total (30/25/20) — well-confirmed. Lower-tier ranges differ ±5 by source:

| Tier | TheGamer (2025) | Skycoach/lfcarry (2026) | Notes |
|------|-----------------|--------------------------|-------|
| 1 | 52–57 | 48–53 | base |
| 2 | 58–63 | 53–58 | exotics historically here |
| 3 | 64–69 | 59–64 | |
| 4 | 70–75 | 65–72 | 11 mod energy (vs 10) |
| 5 | 75 + tuning | 73–75 + tuning | 30/25/20 fixed |

Tier 5 does NOT have more raw stats than high Tier 4 — its edge is the **tuning slot**. Mod energy: T1–3
= 10, T4–5 = 11; tuning mods cost 0. Tier 5 sources include Master Lost Sectors (Expert only gives T4),
master raids/dungeons, GMs, engram focusing at 500 Power; Renegades added a syndicate/Spider "loot tier
+1" boost (Rank 5 at Spider's Outpost / Lawless Frontier). Max tier still 5 as of June 2026 (no T6).
Sources:
- Nerdschalk Tier 5 farm (Jun 21 2026): https://nerdschalk.com/destiny-2-tier-5-armor-farm/
- Dot Esports Tier 5 gear: https://dotesports.com/destiny/news/how-to-get-tier-5-gear-in-destiny-2
- boosting-ground Renegades Tier 5 farm: https://boosting-ground.com/Destiny2/guides/pve-guides/renegades-tier-5-farm
- Bungie Dev Insights — Weapons & Gear Tiering: https://www.bungie.net/7/en/News/Article/dev_insights_weapon_gear_tier

---

## D. Stat tuning (Tier 5 only)

Tuning slot unlocks after masterworking. One stat per piece is randomly the "tuned" stat (can't be
rerolled). Choose: **Swap (+5/−5)** move 5 pts from any stat into the tuned stat; or **Balanced** +1 to
the three lowest stats. Tuning mods cost 0 energy. Material cost of swapping: UNCONFIRMED. Exotics do NOT
get the Tier 5 tuning slot at legendary parity, though post-EoF exotics are now Tier 5 (Monument). Old +10
ability-stat mods gone; new stat mods: +10 = 3 energy, +5 = 1 energy. Font mods nerfed +30/50/60 →
+20/40/50. Sources:
- TheGamer (Aug 1 2025): https://www.thegamer.com/destiny-2-edge-of-fate-armor-rework-guide/
- Skycoach (Jun 19 2026): https://skycoach.gg/blog/destiny/articles/armor-3-0-guide
- epiccarry Monument build guide (Jun 9 2026): https://epiccarry.com/blogs/destiny-2-monument-of-triumph-build-crafting-guide/
- Shattered Vault buildcrafting: https://shatteredvault.com/kb/armour-buildcrafting/
- patchtracker Renegades armor tuning mirror (Nov 19 2025): https://patchtracker.gg/destiny-2/dev-insights-renegades-armor-tuning-preview

---

## E. Set bonuses

2-piece + 4-piece bonuses per set (4pc keeps 2pc active). ~56 sets after Monument of Triumph. **Exotic
armor does NOT count toward set-piece thresholds** (separate slot); legendary class items DO count.
Examples — Bushido (heal on drawn/reloaded kills; bow/shotgun/sword DR), Techsec (+Kinetic dmg), Last
Discipline (special ammo from Orbs); Renegades sets: Wild Anthem/SUROS, Shrewd Survivor, Ferropotent,
Swordmasters. Sources:
- Bungie TWID 06/26/2025: https://www.bungie.net/7/en/News/Article/twid_06_26_2025
- Sportskeeda Renegades set bonuses: https://www.sportskeeda.com/mmo/every-new-armor-set-bonuses-coming-destiny-2-renegades
- light.gg set bonuses: https://www.light.gg/armor/set-bonuses/
- blueberries armor set bonus: https://www.blueberries.gg/armor/armor-set-bonus/

---

## F. Armor keep/dismantle guidance

Tier gate first: default-keep Tier 4+ (≥~70); 2026 practical target = high-stat Tier 4 (73+), Tier 5
tuning is min-max icing. Archetype fit to build (DPS: Gunner/Powerhouse/Paragon; grenade: Grenadier/
Demolitionist/Siegebreaker; melee: Brawler/Skirmisher/Reaver; tank: Bulwark/Colossus). Legacy (pre-EoF)
armor auto-converts 1:1 but has no archetype/set/tier → generally dismantle-fodder EXCEPT the 3
unobtainable stat pairs (§B) or genuinely high converted totals. Can't directly reroll owned exotic stats
— refocus/re-acquire via Ada-1, Rahool, Ghost mods. Sources:
- destiny2base breakdown: https://destiny2base.com/destiny-2-edge-of-fate-armor-3-0-weapon-changes-breakdown
- TheGamePost Renegades exotic armor: https://thegamepost.com/destiny-2-renegades-all-exotic-armor-changes-detailed/
- destiny2hub exotics/class items: https://www.destiny2hub.com/articles/destiny-2-armor-3-0-exotics-overhaul-stats-class-items-featured-gear-explained.html
- epiccarry Armor 3.0 (updated Mar 20 2026): https://epiccarry.com/blogs/destiny-2-edge-of-tomorrow-armor-3-0/

**Conflicts flagged:** 2025 guides said "chase Tier 5"; 2026 guides soften to "Tier 4 73+ is enough."
Exact "impossible combos" list varied by source before the §B derivation resolved it to 3 pairs.
