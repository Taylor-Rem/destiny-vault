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
```bash
python3 destiny_vault.py loadouts      # list your in-game loadouts per character
python3 destiny_vault.py scan          # read vault, apply rules.yaml, write vault_report.json
python3 destiny_vault.py lock-keepers  # lock everything marked KEEP (asks for confirmation)
```

### 5. (Optional) Personalize
```bash
cp preferences.example.yaml preferences.yaml   # then edit — it's gitignored
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

Weapons not listed in `rules.yaml` are left alone (shown under "NOT IN RULES").
Perk names must match in-game text exactly (case-sensitive). See
[`DESTINY_REFERENCE.md`](DESTINY_REFERENCE.md) for the current perk pool and god-roll guidance.

---

## Files

| File / dir | Committed? | What it is |
|---|---|---|
| `destiny_vault.py` | ✅ | The tool. |
| `rules.yaml` | ✅ | Your keep/dismantle rules (starts with examples). |
| `DESTINY_REFERENCE.md` | ✅ | Current-sandbox reference: perks, Armor 3.0, tiers, god rolls (as of 2026-07). |
| `research/` | ✅ | Full research with source citations behind the reference doc. |
| `preferences.example.yaml` | ✅ | Template for your personal preferences. |
| `preferences.yaml` | ❌ gitignored | Your personal copy (account name, builds). |
| `.destiny_config.json` | ❌ gitignored | **Secret** — API key + client secret. |
| `.destiny_token.json` | ❌ gitignored | **Secret** — OAuth token. |
| `.manifest_cache.json` | ❌ gitignored | Generated hash→name cache (rebuilt on demand). |
| `vault_report.json` | ❌ gitignored | Scan output (reveals your inventory). |

---

## Safety notes
- **Dismantles are irreversible.** Only exotics and *curated* rolls come back from Collections;
  random-rolled legendaries and high-stat armor do not. The tool only ever **locks** items —
  it never dismantles — but review the KEEP/DISMANTLE report before you mass-delete in-game.
- Your credentials never leave your machine. Keep the two `.destiny_*.json` files private
  (they're gitignored by default).
