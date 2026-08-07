# destiny_vault

A small, local, zero-dependency-ish tool that reads your **Destiny 2** vault via the
Bungie API, classifies items against your god-roll rules, and can **lock the keepers**
so a mass in-game dismantle is safe.

The Bungie API has no dismantle endpoint, so this tool does everything *up to* that
point: it reads your inventory, tells you exactly what to keep vs. trash, and can lock
your keepers via the API. It runs entirely on your machine — your API key, client
secret, and OAuth token live in local files (`.destiny_config.json`, `.destiny_token.json`)
and are never sent anywhere except bungie.net.

---

## Quick start

### 1. Requirements
- Python 3.8+
- [PyYAML](https://pypi.org/project/PyYAML/) (`pip3 install pyyaml`)

```bash
python3 -m venv venv
source venv/bin/activate
pip install pyyaml
```

### 2. Register a Bungie application
1. Go to <https://www.bungie.net/en/Application> and create an app.
2. Set the **Redirect URL** to exactly:
   ```
   https://localhost:7777/callback
   ```
3. Choose an **OAuth Client Type**:
   - **Confidential** (recommended) → you get a **client_secret**, which enables **silent
     auto-refresh**: access tokens renew themselves for ~90 days before you must log in again.
   - **Public** → no client_secret and **no refresh token**, so you must re-run `login` every
     ~1 hour when the access token expires.
4. Note your **API Key**, **OAuth client_id**, and (Confidential only) **client_secret**.

### 3. Configure & log in
```bash
python3 destiny_vault.py setup       # paste API key / client_id / client_secret
python3 destiny_vault.py login       # opens browser; paste the redirected URL back
python3 destiny_vault.py whoami      # confirm account + list characters
```

### 4. Use it

**Read-only — these change nothing:**
```bash
python3 destiny_vault.py loadouts       # list your in-game loadouts per character
python3 destiny_vault.py scan           # read vault, apply rules.yaml, write vault_report.json
python3 destiny_vault.py armor-scan     # rank your armor into the best set per build
python3 destiny_vault.py armor-cleanup  # Warlock armor keep/dismantle report
```

**Lock-state writes — reversible, and never dismantle anything:**
```bash
python3 destiny_vault.py lock-keepers          # lock everything marked KEEP/REVIEW (confirms first)
python3 destiny_vault.py unlock-all            # unlock every locked weapon (clean slate)
python3 destiny_vault.py armor-cleanup --lock  # lock survivors AND unlock dismantle candidates
```

**Live-character writes — transfers and equips gear. Be in orbit:**
```bash
python3 destiny_vault.py equip-armor super-grenade --dry-run
python3 destiny_vault.py apply-loadout class-grenade 3   # equip, then snapshot into loadout slot 3
```

| Flag | Effect |
|---|---|
| `--dry-run` | Print the transfer/equip plan and change nothing. Always try this first. |
| `--exotic "<name>"` | Pin a specific exotic instead of letting stat score pick one. Needed when a build *requires* one (e.g. `--exotic "Secant Filaments"`). |
| `--weapon "<name>"` | Also transfer + equip this weapon. Repeatable, max one per Kinetic/Energy/Power slot. |
| `--balance` | Search whole armor **sets** to push *both* target stats past 100, instead of picking the top-scoring piece per slot. Armor 3.0 pays nothing for overshooting one stat, so this usually wins. |
| `--loadout N` | After equipping, snapshot the result into loadout slot N (1–10). |

Builds: `super-class`, `super-grenade`, `super-melee`, `class-grenade`, `grenade-class`.
(Intellect is now **Super**, Discipline is **Grenade**, Recovery is **Class** — see Armor 3.0 in the reference.)

### 5. (Optional) Personalize
```bash
cp preferences.example.yaml preferences.yaml   # then edit — it's gitignored
cp rules.example.yaml rules.yaml               # then edit — also gitignored
```

---

## How the rules work — `rules.yaml`

Each top-level key is a weapon/armor **name exactly as it appears in-game**. Under it,
`require` is a list of perk **groups**. An item is a KEEP only if it has at least one perk
from **every** group; otherwise it's marked DISMANTLE. Think of each group as one column
of the roll, listing every perk you'd accept in that column.

```yaml
Fatebringer:
  require:
    - [Explosive Payload, Firefly]   # column 3: keep if it has either
    - [Frenzy, Rampage]              # column 4: AND either of these
```

Weapons not listed in `rules.yaml` fall through to the tool's own duplicate/coverage logic
rather than being judged against a roll.

Perk names must match in-game text **exactly** (case-sensitive) — matching is a plain string
compare, so `Kill clip` or `Auto Loading Holster` simply never matches. `scan` warns about any
rule perk it can't find on a single weapon you own, which catches typos and renamed perks.

Matching considers every perk a weapon **can** roll, not just the one currently slotted
(profile component 310), so a high-Gear-Tier weapon that can swap into a god roll is
recognised as one. See [`DESTINY_REFERENCE.md`](DESTINY_REFERENCE.md) for the current perk
pool and god-roll guidance, and [`CLEANUP_PLAN.md`](CLEANUP_PLAN.md) for how KEEP/DISMANTLE/REVIEW
is actually decided.

---

## Files

| File / dir | Committed? | What it is |
|---|---|---|
| `destiny_vault.py` | ✅ | The tool. |
| `rules.example.yaml` | ✅ | Template for your god-roll rules. Copy to `rules.yaml`. |
| `preferences.example.yaml` | ✅ | Template for your personal preferences. |
| `DESTINY_REFERENCE.md` | ✅ | Current-sandbox reference: perks, Armor 3.0, tiers, god rolls. |
| `CLEANUP_PLAN.md` | ✅ | The keep/dismantle methodology the classifier implements. |
| `research/` | ✅ | Full research with source citations behind the reference doc. |
| `rules.yaml` | ❌ gitignored | **Your** keep/dismantle rules — personal, not shipped. |
| `preferences.yaml` | ❌ gitignored | Your personal copy (account name, builds). |
| `.destiny_config.json` | ❌ gitignored | **Secret** — API key + client secret. |
| `.destiny_token.json` | ❌ gitignored | **Secret** — OAuth token. |
| `.manifest_cache.json`, `.weapon_defs_cache.json`, `.armor_defs_cache.json` | ❌ gitignored | Generated hash→name caches (rebuilt on demand). |
| `*_report.json`, `scratch/` | ❌ gitignored | All scan output — **reveals your inventory**. Ignored by pattern so ad-hoc dumps can't leak. |

---

## Safety notes
- **Dismantles are irreversible.** Only exotics and *curated* rolls come back from Collections;
  random-rolled legendaries and high-stat armor do not. The tool only ever **locks** items —
  it never dismantles — but review the KEEP/DISMANTLE report before you mass-delete in-game.
- Your credentials never leave your machine. Keep the two `.destiny_*.json` files private
  (they're gitignored by default).
