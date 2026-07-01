# Research backup — Vault management & keep/dismantle heuristics

> Raw research with full source citations, compiled 2026-07-01 from live web sources.
> Synthesized version in `../DESTINY_REFERENCE.md` (Part III). This file preserves per-claim URLs.

---

## Vault size & pressure
- Cap: **1,000 slots** (Renegades, 2025-12-02; up from 700). History: 600 (S17, 2022) → 700 → 1,000.
  Renegades overhauled filtering (power/slot/date/rarity). Pressure eased but real; community advice:
  stay lean (often "keep under ~400"). Sources:
  - Threads/@destinythegame: https://www.threads.com/@destinythegame/post/DRA3N1zEod8/
  - TechnoSports: https://technosports.co.in/destiny-2-renegades-delivers-300-extra-vault/
  - GameSpot S17 vault: https://www.gamespot.com/articles/destiny-2-vault-size-increasing-by-100-in-season-17/1100-6503654/
  - Sportskeeda Renegades vault changes: https://www.sportskeeda.com/mmo/vault-changes-announced-destiny-2-renegades

## Reacquire rules
- In Collections = safe to trash: exotics, blue gear, curated legendary rolls. NOT reacquirable:
  randomly-rolled legendary weapons/armor, high-stat exotic armor (re-pull comes back low-stat). Sources:
  - Steam discussion: https://steamcommunity.com/app/1085660/discussions/0/3104647961258614791/
  - Gamepur Collections: https://www.gamepur.com/guides/how-do-collections-work-in-destiny-2-answered
  - Overgear exotics: https://overgear.com/guides/destiny2/how-to-get-exotics-in-destiny-2/

## Armor 3.0 impact on vault-cleaning
Old armor converts 1:1, stays usable, but no archetype/set bonus and lower ceiling → generally
outclassed ("soft sunset"). Keep legacy pieces only with still-unobtainable stat combos (see armor.md §B:
the 3 remaining pairs are Weapons+Health, Class+Super, Grenade+Melee) or exceptional converted totals.
Prioritize new Tier 4/5 armor in build-matching archetypes. Sources:
- TheGamer Armor 3.0: https://www.thegamer.com/destiny-2-edge-of-fate-armor-rework-guide/
- Vortex Gaming vault cleaning 2026: https://vortexgaming.io/en/postdetail/658342
- destiny2base breakdown: https://destiny2base.com/destiny-2-edge-of-fate-armor-3-0-weapon-changes-breakdown

## Tools (parallels to this project)
- **DIM wishlists:** perk-combination rules; matched items get a thumbs-up (`is:wishlist`), matched perks
  highlighted. Default `voltron.txt` (community master list); stricter `choosy_voltron.txt`. Tags: Keep/
  Junk/Infuse/Favorite/Archive. https://github.com/DestinyItemManager/DIM/wiki/Wish-Lists
- **light.gg Roll Appraiser:** scores rolls vs community/curated/personal god rolls; can push Keep/Junk
  tags into DIM; paid "Heroic" tier auto-tags by popularity rank. https://www.light.gg/god-roll/roll-appraiser/
- This project mirrors that pattern: match perk names → keep rules → flag/lock.

## Crafting/enhancing & duplicates
- Craftable: keep one crafted copy (or just the pattern); dismantle random dups.
- Monument of Triumph (2026-06-09) added weapon Tier-Upgrading for world drops (reach T5, enhanced perks)
  but CAN'T add new perks — so for non-craftable god rolls, keep distinct perk-combo drops. Sources:
  - Sportskeeda Monument: https://www.sportskeeda.com/mmo/all-new-returning-content-destiny-2-monument-triumph
  - Bungie Dev Insights: https://www.bungie.net/7/en/News/article/dev_insights_weapons_artifacts_focusing_preview
- Conflict: some 2026 guides say crafted weapons are power-crept vs high-tier world drops; others say a
  fully-upgraded crafted weapon reaches T5-equivalent. Treat "crafted is dead" as opinion.

## Always-keep vs safe-to-trash
KEEP: high-stat exotic armor; crafted patterns / one crafted copy; meta weapons & role staples; new T4/T5
armor in build archetypes; non-craftable legendary god rolls; legacy armor only with unobtainable stat
pair. TRASH: exotic weapons you don't run (Collections); duplicates; old low/mid-stat legacy armor; blue
gear & curated legendaries; infusion fodder (outdated to hoard).

## Common mass-dismantle mistakes
1. Trashing non-reacquirable random rolls thinking they're in Collections.
2. Deleting legacy armor with an unobtainable stat combo before checking.
3. Deleting the last copy of a still-meta exotic (re-grind cost).
4. Dismantling a good non-craftable roll (can't reshape perks after).
5. Dismantling in the moment vs tag-then-purge (lock keepers first).
6. Panic-cleaning at 900–1000 slots.

**Sourcing caveat:** much long-form content is from guide/booster sites; mechanical facts corroborate the
neutral outlets and Bungie posts, but exact tier numbers and "obsolete item" claims should be verified
in-game / against live Bungie patch notes.
