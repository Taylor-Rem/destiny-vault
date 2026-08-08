# God-Roll Reference — Official keep/dismantle vocabulary for `rules.yaml`

> **Purpose:** the repo's standing god-roll documentation. `rules.yaml` is *generated from
> this file's verdicts* — when editing rules, update this doc first so the reasoning survives.
> Owner context: endgame PvE **ability-spam Warlock** (turret/grenade builds; see
> `preferences.yaml` / memory). Priorities: **boss DPS / ad-clear > ability regen
> (Demolitionist, Pugilist, Attrition Orbs, Recycled Energy) > handling filler.**
>
> **Compiled 2026-08-07** via six parallel web-research passes over every vault weapon with
> 2+ REVIEW copies plus the One-Two Punch shotgun candidates (~130 weapons). Sources per
> entry (light.gg community rolls, blueberries.gg, Shacknews, Deltia's, Dexerto, Mobalytics,
> et al. — raw per-batch output with full source lists lives in `scratch/research_batch_*.md`,
> which is gitignored; the source names are repeated inline here). Sandbox is FROZEN since
> Monument of Triumph (9.7.0, 2026-06-09), so these verdicts should not rot.
>
> **Confidence key:** HIGH = multiple independent sources agree. MED = solid but column
> split or frame partially inferred. LOW = pool could not be verified — **never dismantle on
> a LOW-confidence verdict alone.**
>
> Perk names are exact in-game text (case-sensitive) — this is the authoritative vocabulary
> for `rules.yaml`. Note the spelling: "One for All", "Lead from Gold", "Fourth Time's the
> Charm", "One-Two Punch".

---

## ⭐ The One-Two Punch shotgun roster (owner's active hunt)

OTP is NOT in `TRAIT_PERKS`, so without rules these were invisible to dup-collapse — three
OTP-capable Perfect Paradoxes were headed for DISMANTLE before this doc existed. Every
shotgun below has a `require: [[One-Two Punch]]` rule: **any OTP roll = KEEP.**

| Shotgun | Slot/Element | Ideal OTP roll | Verdict | Conf |
|---|---|---|---|---|
| **Perfect Paradox** | Kinetic / Rapid-Fire | **Pugilist + One-Two Punch** (Barrel Shroud, Assault Mag) | The premier farmable OTP shotgun; Pugilist feeds the punch loop. THE target for Winter's Guile/Song of Flame builds | HIGH |
| **Ragnhild-D** | Kinetic / Aggressive | Subsistence (or Slideshot) + One-Two Punch | Hardest single hit per OTP proc; no Pugilist so second to Paradox | HIGH |
| **Fortissimo-11** | Kinetic / Lightweight | Demolitionist (or Subsistence) + One-Two Punch | OTP + grenade energy on one gun; pool attested but not fully verifiable — verify in-game | MED |
| **Precipial** | Energy / Precision (Kepler) | Repulsor Brace/Opening Shot + One-Two Punch | Newest OTP source; Exhaustive Research missile can proc OTP. Alt roll: Repulsor + Destabilizing | MED |
| **The Deicide** | Energy / Rapid-Fire (2021) | Slideshot + One-Two Punch | Full-auto OTP; no origin trait, unfarmable, power-crept by Paradox but a rolled copy is a keeper | MED |

Checked and **do NOT roll OTP:** Someday (its value is Recombination — only non-raid shotgun
with it; craftable), Ded Gramarye IV (unique Discord + Chain Reaction instead), Legato-11
(slug DPS: Triple Tap/Auto-Loading Holster + Cascade Point).
Melee-loop adjacent: Boondoggle Mk. 55 (Pugilist + Swashbuckler is its only PvE role).

## Boss DPS — rockets, heavy GLs, linears (feeder + payoff)

| Weapon | God roll | Notes | Conf |
|---|---|---|---|
| **Apex Predator** (Solar rocket, craftable) | Reconstruction + Bait and Switch (alt Explosive Light) | Still the benchmark legendary DPS rocket | HIGH |
| **VS Chill Inhibitor** (Stasis rapid GL) | Envious Arsenal/Cascade Point + Bait and Switch/Explosive Light (alt Chill Clip) | Arguably the best boss-DPS heavy GL in the frozen sandbox | HIGH |
| **Edge Transit** (Void GL, BRAVE) | Envious Assassin/Cascade Point/Auto-Loading Holster + Bait and Switch (alt Surrounded) | Former benchmark, still elite; anchors the Raid loadout | HIGH |
| **Bitter/Sweet** (Arc GL, craftable) | Envious Arsenal + Bait and Switch | The triple-weapon-rotation GL; Spike Grenades | HIGH |
| **Cynosure** (Strand rocket) | Envious Arsenal/Reconstruction + Elemental Honing/Bait and Switch/Explosive Light | Best Strand rocket; Demolitionist col3 exists for grenade builds | HIGH |
| **The Hothead** (Arc rocket) | Envious Arsenal/Auto-Loading Holster/Reconstruction + Bait and Switch/Explosive Light | 2025 reissue added EA/BnS — pre-reissue copies lack them | HIGH |
| **Crux Termination IV** (Arc rocket) | Envious Assassin/Reconstruction + Explosive Light/Surrounded | Best Arc legendary rocket; Surrounded out-damages Apex in melee range | HIGH |
| **Koraxis's Distress** (Strand GL, craftable) | Envious Assassin/Demolitionist + Full Court (Spike) | No Bait and Switch in pool — power-crept for DPS; keep the crafted copy | HIGH |
| **Song of Ir Yût** (Arc MG, craftable) | Reconstruction/Rewind Rounds + Target Lock/Bait and Switch | Top legendary LMG; fits Arc loadouts | HIGH |
| **Briar's Contempt** (Solar LFR, craftable) | Rewind Rounds/Reconstruction + Focused Fury/Surrounded | Best legendary LFR, but linears are power-crept as a class | HIGH |
| **Succession** (Kinetic sniper, craftable) | Reconstruction + Vorpal Weapon/Firing Line | Still the GM champion-deleter | HIGH |
| **Finite Maybe** (Solar fusion, raid) | Reconstruction/Heal Clip/Lead from Gold + Controlled Burst/Reservoir Burst | Current S-tier major-killer fusion | HIGH |
| **Techeun Force** (Arc fusion, craftable) | Reconstruction/Lead from Gold/Subsistence + Controlled Burst/Chill Clip | Controlled Burst keeps it relevant | HIGH |
| **The Mountaintop** (Kinetic micro-missile, BRAVE) | Auto-Loading Holster + Recombination | Ability kills feed Recombination — perfect for this playstyle | HIGH |
| **Mint Retrograde** (Strand rocket-assisted pulse) | Rewind Rounds/Envious Arsenal + One for All/Bait and Switch | One of the strongest special-ammo damage weapons post-freeze | HIGH |
| **Legato-11** (Solar slug shotgun) | Triple Tap/Auto-Loading Holster + Cascade Point | Burst-DPS special (old LFR-style rule in rules.yaml was wrong) | MED |
| **Nox Perennial V** (Strand fusion) | Envious Assassin + Controlled Burst | Mid-tier; Wild Card origin adds AoE | MED |
| **Suspectum-4fr** (Stasis LFR) | Envious Assassin + Chill Clip | Utility not DPS: ~12 overflow Chill Clip freeze bolts for champion shutdown | MED |
| **Eyes Unveiled** (Void LFR) | Overflow/Triple Tap + Withering Gaze/Reservoir Burst | Dated pool; weaken-support only, borderline dismantle | MED |

## Arc — jolt / ability-regen engine (Alpha & Delta loadouts)

| Weapon | God roll | Notes | Conf |
|---|---|---|---|
| **Watchful Eye** (MG) | Overflow/Field Prep + Jolting Feedback (alt Rolling Storm) | S-tier: giant no-reload jolt hose; ideal Alpha heavy | HIGH |
| **Whatchamacallit** (SMG) | Collective Pugilism/Light Touch + Jolting Feedback | Jolt + Ionic Traces feeding melee energy — S-tier for Prismatic/Arc | HIGH |
| **Terminus Horizon** (MG) | Reconstruction/Triple Tap + Jolting Feedback/Killing Tally | Best Arc ad-clear heavy pairing; farmable in Rite of the Nine | HIGH |
| **Keraunios** (trace) | Recycled Energy/Shoot to Loot/Reconstruction + Jolting Feedback/Chain Reaction | Recycled Energy = ability energy on kill; unobtainable now (event) — keep good rolls | MED-HIGH |
| **Sublimation** (scout) | Demolitionist + Voltshot (alt Explosive Payload) | Grenade-loop dream scout | HIGH |
| **Undercurrent** (wave GL) | Demolitionist/Ambitious Assassin + Voltshot | Elite for grenade-spam Warlocks; Nightfall-focusable | HIGH |
| **Salvager's Salvo** (breech GL) | Demolitionist/Ambitious Assassin/Trickle Charge/Chain Reaction + Voltshot | 2026 reissue has a NEW pool (Voltshot etc.) — old BRAVE copies differ | MED |
| **Hullabaloo** (compressed wave GL) | Envious Assassin/Voltshot/Demolitionist/Ambitious Assassin/Clown Cartridge + Chain Reaction/One for All | Voltshot + Chain Reaction = jolting Forbearance | HIGH |
| **Subjunctive** (SMG, craftable) | Subsistence/Grave Robber + Voltshot | Jolt-spreading ad-clear; enhanced via crafting | HIGH |
| **Iterative Loop** (fusion, craftable) | any **Voltshot** roll | THE Voltshot fusion | HIGH |
| **Phyllotactic Spiral** (pulse, craftable) | any **Voltshot** roll | Jolt-seeding at pulse range | HIGH |
| **Qua Furor V** (Stasis MG) | Feeding Frenzy/Triple Tap + Dragonfly/Golden Tricorn/One for All | A-tier but Watchful Eye outshines it | MED |
| **IKELOS_SMG_v1.0.3** | Feeding Frenzy/Subsistence + Voltshot | (pre-existing rule, confirmed) | HIGH |

## Void — volatile / overshield engine

| Weapon | God roll | Notes | Conf |
|---|---|---|---|
| **VS Velocity Baton** (area-denial GL) | Demolitionist/Repulsor Brace + Attrition Orbs/Destabilizing Rounds | The "orb printer" — tailor-made for this owner; the vault copy rolling Demo+Attrition+Chain+Repulsor+Destab is a monster | HIGH |
| **VS Gravitic Arrest** (fusion) | Repulsor Brace/Demolitionist/Lead from Gold + Destabilizing Rounds/Withering Gaze/Chain Reaction | Repulsor+Withering/Destab = self-weakening overshield loop | HIGH |
| **Lotus-Eater** (rocket sidearm) | Repulsor Brace/Reconstruction + Destabilizing Rounds/Withering Gaze/Beacon Rounds | One of the best rocket sidearms; GM-farmable | HIGH |
| **Gridskipper** (540 pulse) | Repulsor Brace/Demolitionist + Destabilizing Rounds | Best-in-class Void 540 | HIGH |
| **Age-Old Bond** (360 auto, craftable) | Repulsor Brace + Destabilizing Rounds | Self-contained Void engine | HIGH |
| **Elsie's Rifle** (340 pulse, BRAVE) | Rewind Rounds/Repulsor Brace + Desperate Measures/Destabilizing Rounds | No longer farmable — keep good rolls | HIGH |
| **Vouchsafe** (scout) | Repulsor Brace/Fourth Time's the Charm + Destabilizing Rounds | Top Void scout since Destab buffs | HIGH |
| **Anamnesis** (bow) | Dragonfly/Repulsor Brace/Archer's Tempo + Destabilizing Rounds | Best legendary Void bow — Dragonfly+Destab chains volatile | HIGH |
| **Convened Recurve** (bow) | Repulsor Brace/Withering Gaze/Dimensional Shift + Destabilizing Rounds | Most-used bow in the game right now | MED |
| **Maahes HC4** (heavy burst HC) | Repulsor Brace + Destabilizing Rounds/Golden Tricorn | Only the Void-engine combo is worth keeping (none owned yet — current copies are distinct partial rolls, REVIEW) | MED |
| **High Tyrant** (special pulse, dungeon) | Destabilizing Rounds + Demoralize | Volatile + Weaken debuff engine; strong current pick | MED |
| **Admetus-D** (scout) | Repulsor Brace + Withering Gaze/Demoralize | ADS = free weaken; old kinetic version is dead | MED |
| **Sovereignty** (sniper) | Explosive Payload/Enlightened Action + Withering Gaze/Precision Instrument | Weaken-on-ADS support sniper | MED |
| **Null Composure** (fusion, reissued 2026) | Feeding Frenzy + Reservoir Burst | First-bolt-kill explosions; small pool | MED |
| **Positive Outlook** (450 auto) | Ambitious Assassin + Destabilizing Rounds/Repulsor Brace | Serviceable Void primary, nothing more | MED |
| **Ros Arago IV** (600 auto) | Rewind Rounds/Subsistence + Onslaught/Golden Tricorn | Workhorse, no regen synergy | HIGH |

## Solar — scorch / heal engine

| Weapon | God roll | Notes | Conf |
|---|---|---|---|
| **No Survivors** (SMG, dungeon) | Heal Clip/Rewind Rounds/Demolitionist + Incandescent/Master of Arms | Premier Solar SMG | HIGH |
| **Agape** (heavy burst HC, Kepler) | Heal Clip/Rewind Rounds + Incandescent | Top-tier Solar primary, easy to farm | HIGH |
| **Marsilion-C** (heavy GL) | Envious Assassin/Field Prep + Incandescent/Explosive Light | Rare heavy-slot scorch; Hakke origin bonus vs bosses | MED |
| **Speleologist** (MG, craftable) | Enlightened Action/Envious Assassin/Heal Clip + Incandescent | Incandescent on a 900 heavy = elite ad-clear | HIGH |
| **Avalanche** (MG, Dawning-only) | Rewind Rounds + Incandescent | Unobtainable outside December — keep a good roll | HIGH |
| **Acasia's Dejection** (trace, craftable) | Reconstruction/Rewind Rounds/Shoot to Loot + Incandescent/Frenzy | Premier red-bar hose | HIGH |
| **Tyranny of Heaven** (bow, craftable) | Archer's Tempo + Incandescent | Fun ad-clear keeper, not core | HIGH |
| **Hush** (bow) | Archer's Tempo + Incandescent (also Dragonfly/Hatchling rolls) | Good roll or dismantle | HIGH |
| **Perfect Pitch** (SMG, ritual — fixed roll) | Subsistence + Incandescent | One copy, keep, done | HIGH |
| **Zaouli's Bane** | Rapid Hit/Reconstruction + Incandescent | (pre-existing rule, confirmed) | HIGH |
| **Parabellum** (SMG) | Rewind Rounds/Heal Clip + Frenzy | No Incandescent in pool — mid-tier | MED |

## Stasis — crystal / Frost Armor engine (Bleak Watcher kit)

| Weapon | God roll | Notes | Conf |
|---|---|---|---|
| **Liturgy** (double-fire GL) | Envious Arsenal/Rimestealer + Chill Clip/One for All | Only double-fire GL with Chill Clip — unique CC niche | HIGH |
| **Deliverance** (fusion, craftable) | Demolitionist + Chill Clip | Exactly the priority stack; craft enhanced | HIGH |
| **Stay Frosty** (pulse, Dawning-only) | Rimestealer + Headstone | Best Stasis pulse for crystal loops | HIGH |
| **Fair Judgment** (450 auto, ritual) | Rimestealer + Headstone | Self-feeding Frost Armor loop | MED |
| **Appetence** (trace, craftable) | Demolitionist/Overflow + Headstone/Killing Tally | First legendary Stasis trace; Demo+Headstone for this owner | HIGH |
| **Red Tape** (scout, craftable) | Attrition Orbs/Rimestealer/Fourth Time's the Charm + Explosive Payload/Headstone/Focused Fury | Two god rolls: orb engine (Alpha) or crystal build | HIGH |
| **Prolonged Engagement** (SMG) | Subsistence + Headstone/One for All | Keep one Headstone copy | MED |
| **Qullim's Terminus** (MG, craftable) | Ensemble/Unrelenting + Killing Tally/Headstone | Crystal-spawning LMG; power-crept for raw DPS | MED |
| **Senuna SI6** (sidearm) | any **Headstone** roll | Only PvE value; otherwise dismantle | MED |
| **Psi Hermetic V** (pulse) | Outlaw + Headstone | Headstone or dismantle | MED |
| **False Promises** (400 auto, reissued Stasis) | Surplus + Headstone | Pool unverified — do not dismantle on this verdict | LOW |

## Strand — threadling / suspend engine (Beta/Strand loadouts)

| Weapon | God roll | Notes | Conf |
|---|---|---|---|
| **The Call** (rocket sidearm, craftable) | Lead from Gold/Demolitionist + Vorpal Weapon/One for All/Hatchling | Arguably the best legendary sidearm in the game; unconditional keep | HIGH |
| **Marcato-45** (MG) | Demolitionist/Attrition Orbs/Slice + Onslaught/Hatchling/Golden Tricorn | Col3 tailor-made for this owner | MED |
| **Synchronic Roulette** (SMG, craftable) | Envious Assassin/Subsistence + Hatchling | Threadling generator | MED |
| **Mykel's Reverence** (sidearm, craftable) | Rewind Rounds/Pugilist + Hatchling/Frenzy | Rewind+Hatchling = endless Threadlings; Pugilist feeds punch builds | MED |
| **Imminence** (900 SMG, craftable) | Demolitionist/Slice/Pugilist + Chaos Reshaped/Hatchling | Demolitionist grenade battery | HIGH |
| **Resounding** (fusion, ritual) | Subsistence + Hatchling | Shotgun-like Strand spread | MED |
| **Dragoncult Sickle** (caster sword) | Slice/Tireless Blade + Hatchling/Surrounded | B-tier; Strand-verb utility only | HIGH |
| **Thin Precipice** (sword, craftable) | Tireless Blade + Chain Reaction | Budget Strand ad-clear | MED |
| **Last Thursday** (pulse) | Demolitionist/Rapid Hit/Strategist + Slice/Dragonfly/Hatchling | Solid grenade-feeding workhorse | MED |
| **All or Nothing** (540 pulse, Renegades) | Slice/Firefly/Keep Away + Sword Logic/Thermal Atomization/Tear | Primary-slot filler; Firefly+Thermal is the AoE combo | MED |
| **Irukandji** (sniper, craftable) | Fourth Time's the Charm + Firing Line | Power-crept; pattern covers it | MED |

## Kinetic utility & Tremors

| Weapon | God roll | Notes | Conf |
|---|---|---|---|
| **Giver's Blessing** (720 auto, Kepler) | Rewind Rounds/Feeding Frenzy + Kinetic Tremors/Adrenaline Junkie | S-tier kinetic ad-clear; "a better Chroma Rush"; chase Tier 5 | HIGH |
| **Hung Jury SR4** (scout, NF) | Kinetic Tremors/Rewind Rounds + Precision Instrument/One for All | Benchmark GM scout | HIGH |
| **Blast Furnace** (pulse, BRAVE) | Kinetic Tremors + Chaos Reshaped/Frenzy | Best kinetic legendary pulse | MED |
| **Chroma Rush** (720 auto) | Subsistence + Kinetic Tremors | Good filler; outclassed by Giver's Blessing | HIGH |
| **Tigerspite** (450 auto) | Demolitionist/Attrition Orbs/Overflow + Kinetic Tremors/Frenzy | Reissue perks hit the owner's priorities exactly | MED |
| **Inbound Surveillance** (150 scout) | Rapid Hit/Keep Away + Kinetic Tremors/Explosive Payload | Keep one high-tier roll | MED |
| **Transfiguration** (scout, craftable) | Rapid Hit/Demolitionist + Kinetic Tremors | Redundant with Hung Jury | MED |
| **Nameless Midnight** (scout) | Triple Tap + Kinetic Tremors | Power-crept otherwise | HIGH |
| **D.F.A.** (140 HC) | Explosive Payload/Rapid Hit/Subsistence + One for All/Frenzy/Attrition Orbs | Attrition Orbs roll worth keeping for orb builds | HIGH |
| **Ded Gramarye IV** (Arc shotgun) | Discord + Chain Reaction | Genuinely unique self-sustaining AoE shotgun | HIGH |

## Swords

| Weapon | God roll | Notes | Conf |
|---|---|---|---|
| **The Slammer / (Adept)** (Stasis vortex, GM) | Relentless Strikes/Eager Edge + Bait and Switch/Cold Steel | Meta sword; Eager Edge copy = movement utility | HIGH |
| **Falling Guillotine** (Void vortex, craftable) | Relentless Strikes + Bait and Switch/Surrounded/Whirlwind Blade | Benchmark vortex | HIGH |
| **Bequest** (Arc, craftable, DSC) | Relentless Strikes + Surrounded | Highest-Impact legendary sword — irreplaceable stat block | HIGH |
| **False Idols** (Solar vortex, craftable) | Relentless Strikes/Incandescent + Bait and Switch/Chain Reaction | Both DPS and ad-clear flavors via enhancing | HIGH |
| **Eighty-Six** (Strand vortex, Renegades) | Relentless Strikes/Tireless Blade + Elemental Honing | Bray Legacy origin dumps ability energy on heavy attacks | HIGH |
| **Abyssal Edge** (Strand wave) | Relentless Strikes + Sword Logic/Surrounded | Niche | HIGH |
| **Temptation's Hook** (Arc caster) | Tireless Blade + Energy Transfer/Valiant Charge | No damage column — utility/fun only, power-crept | MED |

## Power-crept / dismantle-tier (documented so we stop re-litigating)

No rules for these — dup/coverage logic decides, and extra copies are safe dismantles:
**Brass Attacks** (sidearm, PvP archetype only — the 9 engram copies are fodder),
**Waking Vigil**, **Service Revolver** (LOW conf), **Insidious** (craftable; pattern is the keep),
**Steelfeather Repeater** (Giver's Blessing outclasses it), **Bygones**, **Main Ingredient**,
**Chain of Command** (built for removed Match Game mechanic), **Veles-X** (fixed roll,
power-crept), **Ecliptic Distaff** (LOW conf, glaive), **Punching Out** (LOW conf),
**Infinite Paths 8** (LOW conf — keep only a Demolitionist copy), **Nameless Midnight** and
**Chroma Rush** beyond one good roll, **Boondoggle Mk. 55** (except Pugilist+Swashbuckler).

**Ergo Sum / exotics:** never ruled here — exotic policy (distinct element+perk+frame =
distinct roll) lives in the classifier and memory; REVIEW is intentional.
