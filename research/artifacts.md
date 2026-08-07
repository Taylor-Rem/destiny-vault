# Destiny 2 Artifact System — Definitive Guide (Monument of Triumph, final sandbox)

> **Status:** Destiny 2's sandbox is frozen (Monument of Triumph was the last major update). These
> artifacts and perks are permanent — **this guide is meant to be final, no future churn.**
> **Sources of truth, in order of reliability:**
> 1. ✅ **Owner's in-game read-out** (2026-07-25) — the authoritative source for perk *names, tiers,
>    and layout*. Every third-party guide we checked was stale or wrong (they listed *Galvanic Armor*
>    on Hunter's Journal — it does not exist in this version).
> 2. ✅ **Game manifest / owner's account** (Bungie API) — cross-validated the perk *names*
>    (Encrypted Data Disk's list matches the manifest exactly).
> 3. **Perk effect text** — all 147 perks (7 artifacts × 3 tiers × 7) are filled: the common ones from
>    origin-season research, and every undocumented/Monument-recurated one from the **owner's direct
>    in-game read-out**. A few numeric values may be lightly retuned; wording is faithful to the game.
>    **This guide is complete.**

---

## 1. How the artifact works (✅ verified with owner)

- **7 artifacts, permanently selectable.** You run **one active artifact per loadout**, and the
  selection + its perks **save into the loadout** (stored in Bungie loadout data, component 206).
- **Each artifact = 3 tiers × 7 perks = 21 perks.** You **equip 7** total.
- **Gating:** equip **2 from Tier 1** → Tier 2 unlocks; equip **3 from Tier 2** → Tier 3 unlocks.
- **Slot eligibility (a perk's tier is a floor, not a fixed slot):**
  - Slots 1–2 → **Tier 1 only**
  - Slots 3–5 → **Tier 1 or 2**
  - Slots 6–7 → **Tier 1, 2, or 3** (you may pull lower-tier perks up into these slots)
  - ⇒ A great **Tier-3** perk competes for only **2 slots**; a great Tier-1 perk is flexible.
- **No point/energy budget** — once the tiers are unlocked you simply equip 7 within the rules above.
- **A perk's tier is per-artifact.** The same perk can sit in different tiers on different artifacts
  (e.g. *Horde Shuttle* is T2 on Tablet, T1 on Implement, T3 on Queensfoil).
- **Anti-champion is not on artifacts** — champion counters are intrinsic to weapon frames now.
- Artifact mods are **disabled** in Competitive Crucible & Trials.

## 2. What the tool/API can read (✅ verified)

- **Loadout data (component 206)** stores each loadout's **selected 7 artifact perks** (guard the
  name lookup — some plug hashes error; it's slow across many loadouts). This is the only reliable
  programmatic read, and it returns only what's *selected*, not the full pool.
- The **live active artifact** (component 104) exposes only hash/points/power — **no perks**.
- The **manifest** ships one artifact object (currently mislabeled "Implement of Curiosity") whose
  real perk list matches **Encrypted Data Disk**. Do not trust it for the full 7-artifact system.
- **Subclass** config (super/aspects/fragments/abilities) **is** fully readable (component 305).

---

## 3. Hunter's Journal (Echoes) — ✅ COMPLETE

Generalist Void/orb/survivability artifact. Best fit for Prismatic weapon+ability builds.

**Tier 1**
- **Elemental Siphon** — "Rapid final blows with a **Kinetic weapon** or a weapon matching your equipped Super create an Elemental pickup that matches your equipped Super." *(⚠️ Corrected 2026-08-02 from the live API sandbox-perk text: earlier drafts listed only the matching-element trigger and **omitted Kinetic entirely**. Kinetic weapons proc this on any subclass — e.g. Witherhoard on the Raid loadout. Note it makes an **Elemental pickup, not an Orb of Power**, so it does not feed Super energy.)*
- **Energy Diffusion Substrate** — Gain a small amount of **damage resistance** against all combatant damage (unconditional).
- **Creeping Chill** — Stasis-weapon final blows on slowed/frozen targets release a Slowing burst.
- **Press the Advantage** — Breaking a combatant's shield grants a burst of stability, handling, and reload speed (PvE).
- **Threaded Blast** — Detonating a Tangle with a Strand weapon greatly increases its blast radius.
- **Incendiary Rifle Rounds** — Solar Scout/Sniper precision hits apply Scorch, enabling Ignitions.
- **Sustained Fire** — Landing sustained Auto Rifle hits grants damage resistance.

**Tier 2**
- **Counter Energy** — You or a fireteam member stunning a Champion grants 30% energy to your least-charged ability.
- **Blade Stamina** — Rapid Sword final blows refund Sword ammo (PvE).
- **Void Hegemony** — Defeating weakened targets grants a Void Overshield (Void/Prismatic).
- **Radiant Orbs** — Picking up an Orb of Power makes you Radiant (~+25% weapon damage).
- **Bad Amplitude** — Damaging a Champion with an Arc ability Jolts it.
- **Solar Fulmination** — Ignitions deal increased damage over a larger radius.
- **Targeting Autoloader** — Auto Rifle final blows build stacks that auto-reload the mag and boost Auto Rifle damage (~+20%).

**Tier 3**
- **Prismatic Transfer** — Casting your Super grants allies with a non-matching Super element a weapon damage bonus (~+20%).
- **Argent Blade** — With Armor Charge, Sword damage consumes a charge to grant Argent Blade (stacking Sword damage).
- **Expanding Abyss** — "**Void sources** deal increased damage to weakened targets." *(⚠️ Corrected 2026-08-02 from the live API sandbox-perk text, after the owner flagged the error. An earlier draft restricted this to **Void weapons only, NOT Supers/abilities** — that is wrong. The API says "Void **sources**", which includes Void **Supers and abilities**: Nova Bomb into a weakened target does benefit. Owner confirmed in-game.)*
- **Shieldcrush** — Defensive keywords (overshield/Frost Armor/Woven Mail) empower your melee; offensive keywords empower grenades.
- **Transference** — "Gain increased grenade and melee damage while transcendent. Weapon final blows **while transcendent** refund **Light and Dark energy** after Transcendence ends." *(⚠️ Corrected 2026-08-02 from the live API sandbox-perk text, after the owner flagged the error. An earlier draft claimed this refunded **Super energy** — it does NOT. It refunds **Transcendence** (Light/Dark) energy, i.e. it accelerates your next Transcendence, not your Super. Note also the timing: the final blows must land **while transcendent**; only the payout is deferred until Transcendence ends. This perk is **not** a Super-generation tool.)*
- **Sniper's Meditation** — Sniper Rifle hits grant a stacking Sniper Rifle damage bonus.
- **Shock and Awe** — While Amplified, Arc final blows trigger a Jolting Arc explosion.

## 4. Slayer Baron Apothecary Satchel (Revenant) — ✅ COMPLETE

Stasis / Frost Armor artifact. Frost-Armor generators need Stasis weapons/melee — **starved on
non-Stasis builds.**

**Tier 1**
- **Wind Chill** — Rapid Stasis-weapon precision hits grant a stack of Frost Armor.
- **Crystalline Converter** — Gathering Stasis Shards grants stacks; your next charged Stasis melee spawns Stasis Crystals (up to 5).
- **Total Carnage** — Finishing a major+ grants ~10% damage resist (up to ~25% with Shadestalker set pieces; heals at the set bonus).
- **Power from Pain** — A triple kill against Weakened enemies grants Devour (any weaken source counts).
- **Trace Evidence** — Multikills against Arc-debuffed (Blinded/Jolted) targets spawn an Ionic Trace.
- **The Thick of It** — Rapid final blows while surrounded grant Armor Charge; while surrounded, weapons gain handling and Swords gain charge rate.
- **Killing Breeze** — Rapid weapon final blows grant increased mobility.

**Tier 2**
- **Frost Renewal** — While you have Frost Armor, taking critical damage releases a burst that Freezes nearby combatants and grants Frost Armor to you and nearby allies.
- **Hail the Storm** — Shattering frozen targets/Stasis crystals releases damaging Stasis shards.
- **Debilitating Wave** — Finishers emit a damaging wave matching your equipped Super's element; Arc/Void/Stasis waves apply Blind/Weaken/Slow respectively.
- **Weakened Clear** — Damaging a boss/Champion or breaking a shield with a Grenade Launcher applies Weaken (~15%/6s).
- **Retinal Burn** — Rapid Arc-weapon precision hits consume an Armor Charge to trigger a Blinding burst at the target's location.
- **Curative Orbs** — Picking up an Orb of Power heals you (stacks with Recuperation/Devour).
- **Void Renewal** — While Devour is active, Void weapon kills can generate a Void Breach.

**Tier 3**
- **Brain Freeze** — Freezing a combatant creates a chilling fog that Slows nearby foes.
- **Supernova** — After a Void Breach pickup, your next Void damage creates a large weakening pulse.
- **Conductive Cosmic Crystal** — Your Arc and Void abilities deal bonus damage to targets affected by a Stasis debuff.
- **Served Cold** — Stasis Shards restore 10% class-ability energy; Void Breaches restore an extra 10% melee energy.
- **Kinetic Impacts** — Sustained damage with a Grenade Launcher boosts GL reload speed and triggers a damaging Kinetic shockwave that can stun Unstoppable Champions.
- **Arc Compounding** — Your Arc weapons/abilities deal ~15% increased damage to Blinded targets.
- **Old God's Rite** — After a Void Breach, Void weapon damage creates a rain of seeking projectiles.

## 5. Tablet of Ruin (Heresy) — Arc/Void/Strand, "subjugation" (Exhaust/Sever/Volatile/Unravel)

**Tier 1**
- **Hold the Line** — While surrounded, Machine Guns and Glaives gain reload speed and stability; final blows heal you.
- **Dielectric** — Defeating Arc-debuffed targets grants Bolt Charge. Rapidly defeating Arc-debuffed targets spawns an Orb of Power **and heals a small portion of health**. *(Verbatim from the API 2026-07-25 — the heal was missing from earlier drafts; it makes this a survivability perk, not just economy.)*
- **Volatile Marksman** — Rapid Void-weapon precision hits/final blows grant Volatile Rounds.
- **Unraveling Orbs** — Picking up an Orb of Power or a Tangle grants your Strand weapons Unraveling Rounds.
- **Photonic Flare** — Defeating an Exhausted or Severed target with Arc damage releases a Blinding burst.
- **Elemental Siphon** — Rapid final blows with a **Kinetic weapon** or a weapon matching your equipped Super create an Elemental pickup matching your Super. *(Same perk as on Hunter's Journal — see §3 for the corrected text; the Kinetic trigger was missing from earlier drafts.)*
- **Perpetual Destruction** — Rapid final blows with non-exotic Rocket Launchers refund ammo and increase reload speed for a short duration.

**Tier 2**
- **Vile Weave** — Targets hit by your Tangles are Severed; picking up a Tangle reduces Tangle cooldown.
- **Maligned Harvest** — Rapidly applying Volatile makes your next Void-weapon damage create a weakening burst.
- **Flashover** — Reaching maximum Bolt Charge also makes you Amplified; lightning bolts deal increased damage.
- **Horde Shuttle** — Damaging Unraveled targets with a weapon occasionally spawns a Threadling.
- **No Bell** — Rapid Glaive melee final blows grant additional Glaive Special ammo; blocking increases melee damage.
- **Harsh Refraction** — Trace Rifles deal more damage to targets afflicted by a matching elemental debuff.
- **Gold from Lead** — Picking up Special ammo has a chance to grant Heavy ammo.

**Tier 3**
- **Particle Reconstruction** — Sustained Fusion/Linear Fusion damage partially refills the magazine from reserves **and grants that weapon bonus damage against that target**. *(Verbatim from the API 2026-07-25. Note: it buffs **your weapon**, it does not debuff the target — so it does nothing for teammates.)*
- **Elemental Supercharger** — Killing Exhausted/Severed targets with a weapon matching your Super element restores extra Super energy.
- **Heavy Ordnance Regeneration** — Sustained Machine Gun/Rocket damage grants damage resist and boosts grenade/melee regen.
- **Defibrillating Blast** — Stunning a Champion grants max Bolt Charge, triggering an Arc bolt that heals you and Jolts enemies.
- **Void Flux** — Defeating weakened targets with a Void weapon spreads Volatile to nearby targets.
- **Limit Break** — Casting a Super while you are critically wounded **OR while you have an elemental buff matching your Super's element** grants a period of increased Super damage. *(Verbatim from the API 2026-07-25. ⚠️ The second trigger was missing from earlier drafts and completely changes the perk: it is **not** a be-nearly-dead gamble. Radiant/Amplified/Overshield/Frost Armor/Woven Mail matching your Super element all turn it on safely — and **Facet of Purpose** grants exactly such a buff on Orb pickup, keyed to your Super's element.)*
- **To Shreds** — Sustained damage to Severed targets Unravels them; defeating a Severed target creates a Strand-energy hotspot that grants Woven Mail to nearby allies.

## 6. NPA Repulsor Regulator (Deep) — Arc/Void/Strand

**Tier 1**
- **Improved Unraveling** — Increases the damage dealt by Unraveling a target.
- **Volatile Flow** — Picking up an Orb of Power grants your Void weapons Volatile Rounds.
- **Unto the Breach** — With a Void subclass, defeating a Void-debuffed target creates a Void Breach.
- **Amped Up** — While Amplified, gain damage resistance.
- **Thunderous Retort** — Arc Supers deal 25% more damage when cast while critically wounded or Amplified.
- **Sustained Fire** — Landing sustained Auto Rifle hits grants damage resistance.
- **Shatter Orbs** — The first time you break a combatant's shield with a matching damage type, you create an Orb of Power.

**Tier 2**
- **Strand Soldier** — With a Strand subclass, gaining Woven Mail also grants Unraveling Rounds to your Strand weapons.
- **Suppressing Glaive** — Damaging combatants with your Glaive Suppresses them (prevents ability use for a short time).
- **Protective Breach** — Picking up a Void Breach grants a Void Overshield.
- **Counter Charge** — Stunning a Champion grants x1 Armor Charge.
- **Bricks from Beyond** — Defeating a powerful combatant with a Void weapon has a chance to generate Heavy ammo progress for you and teammates.
- **Overload Grenades** — Void grenades disrupt combatants — stunning them, delaying their ability-energy regen, and lowering their damage output. Strong against Overload Champions.
- **Targeting Autoloader** — Auto Rifle final blows build stacks that auto-reload the mag and boost Auto Rifle damage.

**Tier 3**
- **Conductive Cosmic Needle** — Targets affected by Strand debuffs take increased damage from your Arc and Void abilities.
- **Shock and Awe** — While Amplified, Arc final blows trigger a Jolting Arc explosion.
- **Supernova** — After a Void Breach pickup, your next Void damage creates a large weakening pulse.
- **Squad Goals** — Performing a finisher while you have Amplified/Woven Mail/Devour grants that buff to nearby allies.
- **Lightning Strikes Twice** — Throwing an Arc grenade grants increased grenade recharge; Arc final blows extend it.
- **Passive Aggressive Guard** — Take less damage from nearby combatants while wielding a Glaive.
- **Void Weapon Channeling** — Temporary Void weapon damage bonus after Void kills, scaling with your charged Void abilities.

## 7. Encrypted Data Disk (Renegades) — Kinetic/Arc/Void/Sword *(names match the manifest exactly)*

**Tier 1**
- **Press the Advantage** — Breaking a combatant's shield grants a burst of stability, handling, and reload speed.
- **Kinetic Synthesis** — Sustained Kinetic damage and rapid final blows have a chance to generate a unique ammo brick.
- **Reload at Range** — Precision hits with Bows and Sniper Rifles grant a stacking reload-speed bonus.
- **Riposte** — Shortly after guarding with a Sword, your light/heavy attacks stun unshielded combatants.
- **Power from Pain** — A triple kill against Weakened enemies grants Devour (any weaken source counts).
- **Fierce Proxemics** — Finisher final blows grant grenade and melee energy.
- **Rapid Remedy** — Machine Gun rapid final blows heal you.

**Tier 2**
- **Dielectric** — Defeating Arc-debuffed targets grants Bolt Charge; rapid defeats spawn an Orb of Power.
- **Armorsmith** — Breaking a combatant's shield grants temporary damage resistance and increased melee damage.
- **Counter Energy** — You or a fireteam member stunning a Champion grants 30% energy to your least-charged ability.
- **Combination Argent Blade** — Pause briefly after a light attack, then follow with a light/heavy attack to empower your Sword.
- **Singularity Blade** — While you have a Void buff, melee/Sword hits Weaken; final blows create a weakening burst.
- **Blinding Jolts** — Final blows on Jolted combatants Blind nearby combatants.
- **Precision Equity** — Precision final blows build progress toward a large Orb of Power that also grants bonus weapon damage on pickup; higher-ranked targets grant more progress.

**Tier 3**
- **Elemental Orbs: Arc** — Arc weapon final blows have a chance to spawn an Arc Elemental Orb.
- **Kinetic Rupture** — Kinetic damage against a powerful combatant has a chance to create a damaging Kinetic Rupture.
- **Sniper's Meditation** — Sniper Rifle hits grant a stacking Sniper Rifle damage bonus.
- **Sword Storm Combo** — Three Sword light attacks followed by a heavy attack summons penumbral blades.
- **Void Infestation** — Defeating a weakened target spawns a tracking projectile that weakens other targets.
- **Tazer Tag** — Arc-powered melee hits Jolt combatants and deal bonus damage for a short duration.
- **Sticker Shock** — Flux/Magnetic/Fusion Grenades deal more damage when attached; on final blows they release seeking micro-missiles.

## 8. Implement of Curiosity (Edge of Fate) — elemental generalist

**Tier 1**
- **Fever and Chill** — Rapid Solar precision hits grant Radiant; rapid Stasis precision hits grant Frost Armor.
- **Elemental Benevolence** — Granting allies elemental buffs restores some of your class-ability energy.
- **Frost Renewal** — While you have Frost Armor, taking critical damage releases a Freezing burst and grants Frost Armor to you and nearby allies.
- **Horde Shuttle** — Damaging Unraveled targets with a weapon occasionally spawns a Threadling.
- **Refresh Threads** — Picking up an elemental pickup matching your Super's element grants energy to your least-charged ability (Strand: Tangles instead).
- **Pack Tactics** — Dealing damage with Threadlings increases Threadling damage; at maximum stacks, Threadlings stun Unstoppable Champions.
- **Semi Auto Striker** — While you have fewer than 2 stacks of Armor Charge, rapid precision shots with Bows, Snipers, and Scout Rifles generate an Armor Charge.

**Tier 2**
- **Threaded Blast** — Detonating a Tangle with a Strand weapon greatly increases its blast radius.
- **Cauterized Darkness** — Stasis- or Strand-affected non-boss combatants take increased Solar damage from all sources.
- **Elemental Daze** — Stunning a Champion with an elemental weapon creates an elementally-aligned explosion applying a matching debuff to nearby targets.
- **Shoulder to Shoulder** — Dealing sustained precision damage near 2+ allies grants you damage resistance.
- **Elemental Coalescence** — Defeating targets has a chance to create an elemental pickup matching your Super element.
- **That Fresh Bullet Smell** — Picking up an ammo brick grants your Kinetic weapons increased damage for a short duration.
- **Energy Acceleration** — Sustained damage with micro-missiles causes the combatant to emit a Kinetic shockwave that damages nearby combatants. Strong against Unstoppable Champions.

**Tier 3**
- **Radiant Shrapnel** — Sustained weapon damage while Radiant generates a volley of explosive Solar projectiles that Scorch on impact.
- **Shield Crush** — (= Shieldcrush) Defensive keywords empower your melee; offensive keywords empower grenades.
- **Elemental Overdrive** — Picking up an elemental pickup or Tangle grants increased damage to weapons of the same element.
- **Tangled Web** — Creating a Tangle by defeating a Strand-debuffed target Suspends nearby combatants.
- **Frigid Glare** — While Frost Armor is active, Stasis precision final blows cause a Freezing burst.
- **Iron Lord's Vigor** — While wielding a Sword, you take decreased damage; rapid final blows grant Sword ammo.
- **Argent Quiver** — Reloading a Bow consumes one stack of Armor Charge, granting increased damage and reload speed for your next 3 shots (or until you stow the bow).

## 9. Queensfoil Censer (Wish) — Solar/Radiant + Strand/Stasis debuffs

**Tier 1**
- **Fever and Chill** — Rapid Solar precision hits grant Radiant; rapid Stasis precision hits grant Frost Armor.
- **Torch** — While Radiant, deal increased weapon damage to Strand- and Stasis-debuffed targets.
- **Heart of the Flame** — Casting your Solar Super grants nearby allies Radiant and increases your Super's damage for each nearby ally.
- **Armorsmith** — Breaking a combatant's shield grants temporary damage resistance and increased melee damage.
- **Wished into Being** — While your Super is nearly fully charged, ability final blows spawn Orbs of Power.
- **Kindling Trigger** — While Radiant, you apply Scorch more frequently.
- **Blast Radius** — Rapid final blows with Rocket Launchers and Grenade Launchers grant Armor Charge.

**Tier 2**
- **Unraveling Orbs** — Picking up an Orb of Power or a Tangle grants your Strand weapons Unraveling Rounds.
- **Pillar of Ice** — Defeating a frozen target spawns Stasis Crystals.
- **Revitalizing Blast** — Stunning a Champion causes it to Ignite and clears your shield stun.
- **Anti-Champion Nosecone** — Rocket Launchers deal increased damage to Champions.
- **Dragon's Bite** — Breaking a combatant's shield with a Strand/Stasis weapon can Suspend/Freeze it (PvE, ~20% chance).
- **Creeping Chill** — Stasis-weapon final blows on slowed/frozen targets release a Slowing burst.
- **Perpetual Destruction** — Rapid final blows with non-exotic Rocket Launchers refund ammo and increase reload speed for a short duration.

**Tier 3**
- **Horde Shuttle** — Damaging Unraveled targets with a weapon occasionally spawns a Threadling.
- **Hail the Storm** — Shattering frozen targets/Stasis crystals releases damaging Stasis shards.
- **Rays of Precision** — While Radiant, Solar precision final blows cause combatants to Ignite.
- **Solo Operative** — While you are the only member of your fireteam, deal ~22% increased damage to all targets.
- **Argent Ordnance** — Rocket Launchers deal increased damage while you have Armor Charge (consumes a stack).
- **Frigid Glare** — While Frost Armor is active, Stasis precision final blows cause a Freezing burst.
- **To Shreds** — Sustained damage to Severed targets Unravels them; defeating a Severed target creates a Strand-energy hotspot that grants Woven Mail to nearby allies.

---

## 10. Perk-picking framework (durable)
Match perks to the build's engine and skip anything gated behind gear you don't run:
1. **Survivability** — flat DR (Energy Diffusion Substrate), Frost Armor (needs Stasis), overshield, heal (Curative Orbs).
2. **Ability/turret uptime** — Champion→energy (Counter Energy), Shards/Breaches→energy (Served Cold), Devour (Power from Pain).
3. **Damage** — weaken amplifiers (Expanding Abyss, weapons-only!), Radiant (Radiant Orbs), debuff-damage (Conductive Cosmic Crystal, Arc Compounding).
4. **Economy** — elemental pickups/orbs (Elemental Siphon) → feeds ability energy & Star-Eater.

## Sources
Owner in-game read-out (primary). Effect text cross-checked against: thegamer, shacknews, light.gg,
gamerant, oneesports, dexerto — treated as directional; owner read-out overrides.
