#!/usr/bin/env python3
"""
destiny_vault.py - Read your Destiny 2 vault, classify items against god-roll
rules, and (optionally) lock the keepers so you can safely dismantle the rest
in-game.

The Bungie API has NO dismantle endpoint, so this tool does everything up to
that point: it reads your inventory, tells you exactly what to keep vs. trash,
and can LOCK your keepers via the API so a mass in-game dismantle is safe.

Runs entirely on your machine. Your API key, client secret, and OAuth token
are stored locally in ./ .destiny_config.json and ./ .destiny_token.json and
are never sent anywhere except to bungie.net.

USAGE
    python3 destiny_vault.py setup       # one-time: paste API key / client id
    python3 destiny_vault.py login       # OAuth authorize (opens browser)
    python3 destiny_vault.py whoami       # confirm account + list characters
    python3 destiny_vault.py loadouts     # list your in-game loadouts per character
    python3 destiny_vault.py scan         # read vault, apply rules.yaml, report
    python3 destiny_vault.py lock-keepers # lock everything marked KEEP (asks first)

Requires: Python 3.8+, and PyYAML  (pip3 install pyyaml)
"""

import base64
import http.server
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, ".destiny_config.json")
TOKEN_PATH = os.path.join(HERE, ".destiny_token.json")
MANIFEST_CACHE = os.path.join(HERE, ".manifest_cache.json")
RULES_PATH = os.path.join(HERE, "rules.yaml")

API_ROOT = "https://www.bungie.net/Platform"
AUTH_URL = "https://www.bungie.net/en/OAuth/Authorize"
TOKEN_URL = "https://www.bungie.net/Platform/App/OAuth/token/"
REDIRECT_URI = "https://localhost:7777/callback"  # must match your app registration

# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def load_json(path, default=None):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(path, 0o600)

def die(msg):
    print("ERROR: " + msg)
    sys.exit(1)

def api_get(path, token=None):
    cfg = load_json(CONFIG_PATH) or {}
    req = urllib.request.Request(API_ROOT + path)
    req.add_header("X-API-Key", cfg["api_key"])
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if data.get("ErrorCode", 1) != 1:
        die("Bungie API error %s: %s" % (data.get("ErrorStatus"), data.get("Message")))
    return data["Response"]

def api_post(path, body, token):
    cfg = load_json(CONFIG_PATH) or {}
    raw = json.dumps(body).encode()
    req = urllib.request.Request(API_ROOT + path, data=raw, method="POST")
    req.add_header("X-API-Key", cfg["api_key"])
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if data.get("ErrorCode", 1) != 1:
        die("Bungie API error %s: %s" % (data.get("ErrorStatus"), data.get("Message")))
    return data["Response"]

# ---------------------------------------------------------------------------
# setup + oauth
# ---------------------------------------------------------------------------

def cmd_setup():
    print("Enter the values from your Bungie app at https://www.bungie.net/en/Application")
    print("TIP: choose OAuth Client Type = 'Confidential' to get a client_secret — that enables")
    print("     silent auto-refresh (~90 days between logins). 'Public' apps have no refresh token.")
    api_key = input("  API Key: ").strip()
    client_id = input("  OAuth client_id: ").strip()
    client_secret = input("  OAuth client_secret (blank if Public client): ").strip()
    save_json(CONFIG_PATH, {
        "api_key": api_key,
        "client_id": client_id,
        "client_secret": client_secret,
    })
    print("Saved to %s" % CONFIG_PATH)
    print("Redirect URL registered on your app MUST be exactly: %s" % REDIRECT_URI)

def _token_request(body):
    """POST to the OAuth token endpoint (authorization_code or refresh_token grant),
    stamp + persist the resulting token, and return it. Shared by login and refresh."""
    cfg = load_json(CONFIG_PATH)
    body = dict(body, client_id=cfg["client_id"])
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if cfg.get("client_secret"):
        basic = base64.b64encode(
            ("%s:%s" % (cfg["client_id"], cfg["client_secret"])).encode()
        ).decode()
        headers["Authorization"] = "Basic " + basic
    data = urllib.parse.urlencode(body).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    with urllib.request.urlopen(req) as r:
        tok = json.load(r)
    tok["obtained_at"] = int(time.time())
    save_json(TOKEN_PATH, tok)
    return tok

def _exchange_code(code):
    return _token_request({"grant_type": "authorization_code", "code": code})

def _refresh_token(tok):
    """Use the stored refresh_token to get a fresh access token silently.
    Only works for Confidential OAuth apps (Public apps get no refresh_token)."""
    return _token_request({
        "grant_type": "refresh_token",
        "refresh_token": tok["refresh_token"],
    })

def cmd_login():
    cfg = load_json(CONFIG_PATH) or die("Run 'setup' first.")
    params = {
        "client_id": cfg["client_id"],
        "response_type": "code",
        "state": "vaultmgr",
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)
    print("Opening your browser to authorize...")
    print("If it doesn't open, paste this URL manually:\n  " + url)
    webbrowser.open(url)
    print()
    print("After you approve, your browser will try to load %s..." % REDIRECT_URI)
    print("It will look like an error page - that is expected.")
    print("Copy the FULL URL from the address bar and paste it below.")
    pasted = input("Pasted redirect URL (or just the code): ").strip()
    if "code=" in pasted:
        code = urllib.parse.parse_qs(urllib.parse.urlparse(pasted).query)["code"][0]
    else:
        code = pasted
    tok = _exchange_code(code)
    if tok.get("refresh_token"):
        print("Logged in. Access token ~%s min; auto-refresh ENABLED (~%s days before re-login)."
              % (tok.get("expires_in", 3600) // 60, tok.get("refresh_expires_in", 7776000) // 86400))
    else:
        print("Logged in. Access token valid ~%s min. (Public app: NO auto-refresh — you'll re-run "
              "'login' each time it expires. Switch to a Confidential app to enable auto-refresh.)"
              % (tok.get("expires_in", 3600) // 60))

def get_token():
    tok = load_json(TOKEN_PATH) or die("Run 'login' first.")
    age = int(time.time()) - tok.get("obtained_at", 0)
    if age <= tok.get("expires_in", 3600) - 120:
        return tok["access_token"], tok
    # Access token expired. If we have a refresh token (Confidential apps only),
    # renew silently; refresh tokens themselves last ~90 days.
    if tok.get("refresh_token"):
        if age > tok.get("refresh_expires_in", 7776000) - 120:
            die("Session fully expired (>90 days). Re-run: python3 destiny_vault.py login")
        try:
            tok = _refresh_token(tok)
            print("(access token auto-refreshed)")
            return tok["access_token"], tok
        except Exception as e:
            die("Auto-refresh failed (%s). Re-run: python3 destiny_vault.py login" % e)
    # Public OAuth client: no refresh token exists, so we can't renew silently.
    die("Access token expired (~1h) and this is a Public app with no refresh token.\n"
        "  Re-run: python3 destiny_vault.py login\n"
        "  To enable auto-refresh, switch your Bungie app to a Confidential client "
        "(gives a client_secret), then re-run 'setup' and 'login'.")

# ---------------------------------------------------------------------------
# account / membership
# ---------------------------------------------------------------------------

def get_membership(token):
    r = api_get("/User/GetMembershipsForCurrentUser/", token)
    dm = r.get("primaryMembershipId")
    memberships = r["destinyMemberships"]
    chosen = None
    for m in memberships:
        if str(m["membershipId"]) == str(dm):
            chosen = m
    if not chosen:
        chosen = memberships[0]
    return chosen["membershipType"], chosen["membershipId"], chosen.get("displayName")

def cmd_whoami():
    token, _ = get_token()
    mtype, mid, name = get_membership(token)
    print("Account: %s  (membershipType=%s, id=%s)" % (name, mtype, mid))
    prof = api_get("/Destiny2/%s/Profile/%s/?components=200" % (mtype, mid), token)
    for cid, ch in prof["characters"]["data"].items():
        print("  Character %s : light %s, class %s" % (cid, ch["light"], ch["classType"]))

CLASS_TYPES = {0: "Titan", 1: "Hunter", 2: "Warlock"}

def cmd_loadouts():
    """Print every in-game loadout for each character (component 206)."""
    token, _ = get_token()
    mtype, mid, _name = get_membership(token)
    # 200 characters, 206 loadouts, 102/201/205 so we can name the equipped items
    prof = api_get(
        "/Destiny2/%s/Profile/%s/?components=200,206,102,201,205" % (mtype, mid),
        token,
    )
    chars = prof.get("characters", {}).get("data", {})
    loadouts = prof.get("characterLoadouts", {}).get("data", {})

    # loadout entries reference items only by instanceId; build instanceId -> hash
    inst = {}
    def _index(items):
        for it in items:
            iid = it.get("itemInstanceId")
            if iid:
                inst[iid] = it["itemHash"]
    _index(prof.get("profileInventory", {}).get("data", {}).get("items", []))
    for _cid, invd in prof.get("characterInventories", {}).get("data", {}).items():
        _index(invd.get("items", []))
    for _cid, invd in prof.get("characterEquipment", {}).get("data", {}).items():
        _index(invd.get("items", []))

    if not loadouts:
        print("No loadouts found (component 206 empty).")
        return

    for cid, ch in chars.items():
        cls = CLASS_TYPES.get(ch.get("classType"), "?")
        los = loadouts.get(cid, {}).get("loadouts", [])
        used = [(i, lo) for i, lo in enumerate(los)
                if any(it.get("itemInstanceId", "0") != "0" for it in lo.get("items", []))]
        print("\n=== %s  (light %s, char ...%s)  %d/%d slots filled ===" % (
            cls, ch.get("light"), cid[-4:], len(used), len(los)))
        for i, lo in used:
            lname = (def_name("DestinyLoadoutNameDefinition", lo["nameHash"])
                     if lo.get("nameHash") else "(unnamed)")
            print("  [%2d] %s" % (i + 1, lname))
            for it in lo.get("items", []):
                iid = it.get("itemInstanceId", "0")
                if iid == "0":
                    continue
                h = inst.get(iid)
                iname = def_name("DestinyInventoryItemDefinition", h) if h else "(not in inventory)"
                print("         - %s" % iname)

# ---------------------------------------------------------------------------
# manifest (hash -> human name), cached on demand
# ---------------------------------------------------------------------------

_manifest = None

def _mcache():
    global _manifest
    if _manifest is None:
        _manifest = load_json(MANIFEST_CACHE, {})
    return _manifest

def def_name(entity_type, hash_):
    """Look up a definition's display name, caching results locally."""
    cache = _mcache()
    key = "%s:%s" % (entity_type, hash_)
    if key in cache:
        return cache[key]
    try:
        d = api_get("/Destiny2/Manifest/%s/%s/" % (entity_type, hash_))
        # Most defs carry the label under displayProperties.name, but some
        # (e.g. DestinyLoadoutName/Color/IconDefinition) put it in a top-level
        # "name" field instead. Fall back to that before giving up on the hash.
        name = (d.get("displayProperties", {}).get("name")
                or d.get("name")
                or str(hash_))
    except SystemExit:
        name = str(hash_)
    cache[key] = name
    _mark_dirty(MANIFEST_CACHE, cache)
    return name

# Periodic cache flush: heavy scans do thousands of lookups, so we avoid
# rewriting the whole cache file on every single one (that made scans crawl).
_dirty = {}
def _mark_dirty(path, cache):
    _dirty[path] = cache
    if len(cache) % 200 == 0:
        save_json(path, cache)
def _flush_caches():
    for path, cache in _dirty.items():
        save_json(path, cache)
    _dirty.clear()

# richer per-item metadata (name / itemType / tier / weapon type), cached on disk
WDEF_CACHE = os.path.join(HERE, ".weapon_defs_cache.json")
_wdefs = None
def item_meta(hash_):
    """Cached {name, itemType, tier, type}. itemType 3 == Weapon; tier 6 == Exotic."""
    global _wdefs
    if _wdefs is None:
        _wdefs = load_json(WDEF_CACHE, {})
    k = str(hash_)
    if k in _wdefs:
        return _wdefs[k]
    try:
        d = api_get("/Destiny2/Manifest/DestinyInventoryItemDefinition/%s/" % hash_)
    except SystemExit:
        d = {}
    _wdefs[k] = {
        "name": d.get("displayProperties", {}).get("name", str(hash_)),
        "itemType": d.get("itemType"),
        "tier": d.get("inventory", {}).get("tierType"),
        "type": d.get("itemTypeDisplayName", ""),
    }
    _mark_dirty(WDEF_CACHE, _wdefs)
    return _wdefs[k]

# Curated behavioural weapon perks. Used for (a) sole-source coverage and (b) as
# a signal set — NOT for duplicate detection (that uses the full plug set). Keep
# in sync with research/weapons-pve-perks.md.
TRAIT_PERKS = {
    # boss / DPS
    "Bait and Switch", "Envious Arsenal", "Envious Assassin", "Reconstruction",
    "Triple Tap", "Focused Fury", "Vorpal Weapon", "Firing Line", "Cascade Point",
    "Fourth Time's the Charm", "Bipod", "Killing Tally", "High-Impact Reserves",
    "Explosive Light", "Recombination", "Target Lock", "Frenzy", "Successful Warm-Up",
    "Rewind Rounds", "Precision Instrument",
    # ad-clear / verbs
    "Incandescent", "Voltshot", "Chain Reaction", "Destabilizing Rounds",
    "Jolting Feedback", "Dragonfly", "Firefly", "Hatchling", "Chill Clip",
    "Golden Tricorn", "Adagio", "Onslaught", "Kinetic Tremors", "Headstone",
    "Sword Logic", "One for All", "Collective Action", "Repulsor Brace",
    # ability / economy
    "Demolitionist", "Wellspring", "Pugilist", "Grave Robber", "Osmosis",
    "Attrition Orbs", "Classy Contender", "Subsistence", "Feeding Frenzy",
    "Overflow", "Clown Cartridge", "Ambitious Assassin", "Rapid Hit", "Outlaw",
    "Perpetual Motion", "Discord", "Lead from Gold", "Shoot to Loot",
}

# ---------------------------------------------------------------------------
# scan / classify
# ---------------------------------------------------------------------------

def load_rules():
    try:
        import yaml
    except ImportError:
        die("PyYAML not installed. Run: pip3 install pyyaml")
    if not os.path.exists(RULES_PATH):
        die("No rules.yaml found next to this script.")
    with open(RULES_PATH) as f:
        return yaml.safe_load(f) or {}

def fetch_profile(token):
    mtype, mid, name = get_membership(token)
    # 102 vault, 201 char inv, 205 equipped, 206 loadouts, 300 instances, 305 sockets
    comps = "102,201,205,206,300,305"
    prof = api_get("/Destiny2/%s/Profile/%s/?components=%s" % (mtype, mid, comps), token)
    return mtype, mid, prof

def item_active_perks(instance_id, sockets_data):
    """Return list of (plugHash) for active plugs on an instanced item."""
    entry = sockets_data.get(instance_id)
    if not entry:
        return []
    out = []
    for s in entry.get("sockets", []):
        if s.get("isVisible", True) and "plugHash" in s:
            out.append(s["plugHash"])
    return out

def classify(item_name, perk_names, rule):
    """
    rule format (per weapon in rules.yaml):
        require:            # keep only if item has >=1 perk from EACH group
          - [Perk A, Perk B]
          - [Perk C]
    Returns (keep: bool, reason: str)
    """
    groups = rule.get("require", [])
    if not groups:
        return True, "no perk requirement (keep by default)"
    missing = []
    for group in groups:
        if not any(p in perk_names for p in group):
            missing.append(" or ".join(group))
    if missing:
        return False, "missing: " + "; ".join(missing)
    return True, "matches god roll"

def _collect_weapons(prof, sockets_data, protected):
    """Return a list of weapon dicts (weapons only) with metadata + perks."""
    raw = []
    for it in prof.get("profileInventory", {}).get("data", {}).get("items", []):
        it["_loc"] = "Vault"; raw.append(it)
    for cid, inv in prof.get("characterInventories", {}).get("data", {}).items():
        for it in inv.get("items", []):
            it["_loc"] = "Char " + cid[-4:]; raw.append(it)
    for cid, inv in prof.get("characterEquipment", {}).get("data", {}).items():
        for it in inv.get("items", []):
            it["_loc"] = "Equip " + cid[-4:]; raw.append(it)

    weapons = []
    for it in raw:
        iid = it.get("itemInstanceId")
        if not iid:
            continue
        meta = item_meta(it["itemHash"])
        if meta.get("itemType") != 3:
            continue  # weapons only; armor keep-value needs different logic
        perks = [def_name("DestinyInventoryItemDefinition", h)
                 for h in item_active_perks(iid, sockets_data)]
        weapons.append({
            "name": meta["name"], "loc": it["_loc"], "iid": iid,
            "tier": meta.get("tier"), "type": meta.get("type", ""),
            "perks": perks, "sig": frozenset(perks),
            "traits": set(perks) & TRAIT_PERKS, "prot": iid in protected,
            "reason": None,
        })
    return weapons

def cmd_scan(do_lock=False):
    from collections import defaultdict
    token, _ = get_token()
    rules = load_rules()
    mtype, mid, prof = fetch_profile(token)
    sockets_data = prof.get("itemComponents", {}).get("sockets", {}).get("data", {})

    # Pass 0 inputs: instances that are equipped or sit in an in-game loadout
    protected = set()
    for _cid, invd in prof.get("characterEquipment", {}).get("data", {}).items():
        for it in invd.get("items", []):
            if it.get("itemInstanceId"):
                protected.add(it["itemInstanceId"])
    for _cid, cl in prof.get("characterLoadouts", {}).get("data", {}).items():
        for lo in cl.get("loadouts", []):
            for it in lo.get("items", []):
                iid = it.get("itemInstanceId", "0")
                if iid != "0":
                    protected.add(iid)

    weapons = _collect_weapons(prof, sockets_data, protected)
    _flush_caches()

    # Pass 2 input: which trait perks are on exactly ONE weapon (vault-relative)
    sources = defaultdict(set)
    for w in weapons:
        for p in w["traits"]:
            sources[p].add(w["iid"])

    # base KEEP reasons: Pass 0 (protect) > Pass 1 (god roll) > Pass 2 (sole source)
    for w in weapons:
        if w["prot"]:
            w["reason"] = "in loadout / equipped"
        elif w["name"] in rules and classify(w["name"], w["perks"], rules[w["name"]])[0]:
            w["reason"] = "god roll"
        else:
            sole = sorted(p for p in w["traits"] if len(sources[p]) == 1)
            if sole:
                w["reason"] = "only source of " + ", ".join(sole)

    # Passes 3-5: group by (name + identical full roll); collapse exact duplicates.
    keep, dismantle, review = [], [], []
    groups = defaultdict(list)
    for w in weapons:
        groups[(w["name"], w["sig"])].append(w)
    for (nm, sig), grp in groups.items():
        # representative = protected first, then has-a-reason, then highest tier
        grp.sort(key=lambda w: (not w["prot"], w["reason"] is None, -(w["tier"] or 0)))
        rep, extras = grp[0], grp[1:]
        if extras:  # >1 identical copy: keep one, the rest are exact-dup candidates
            rep["reason"] = rep["reason"] or ("kept 1 of %d identical" % len(grp))
            keep.append(rep)
            for w in extras:
                if w["prot"] or (w["reason"] and w["reason"].startswith("only source")):
                    keep.append(w)                       # never dismantle a protected/sole copy
                elif rep["tier"] == 6:
                    w["reason"] = "duplicate exotic (keep 1)"
                    review.append(w)                     # exotics -> review (Ergo Sum etc.)
                else:
                    w["reason"] = "exact duplicate roll"
                    dismantle.append(w)                  # only truly identical legendaries
        else:  # single copy
            if rep["reason"]:
                keep.append(rep)
            else:
                rep["reason"] = "no god-roll / coverage match"
                review.append(rep)                       # conservative: your call, not auto-dismantle

    print("\n===== VAULT CLEANUP (%d weapons) =====" % len(weapons))
    print("  KEEP:      %d" % len(keep))
    print("  DISMANTLE: %d   (exact-duplicate rolls only)" % len(dismantle))
    print("  REVIEW:    %d   (your call — nothing auto-dismantled here)" % len(review))

    print("\n----- DISMANTLE (safe: identical duplicates) -----")
    for w in sorted(dismantle, key=lambda w: w["name"])[:60]:
        print("  [DISMANTLE] %-26s %-9s | %s" % (w["name"][:26], w["loc"], w["reason"]))
    if len(dismantle) > 60:
        print("  ...and %d more (see vault_report.json)" % (len(dismantle) - 60))

    print("\n----- REVIEW (sample) -----")
    for w in review[:25]:
        print("  [REVIEW] %-26s %-9s | %s" % (w["name"][:26], w["loc"], w["reason"]))
    if len(review) > 25:
        print("  ...and %d more (see vault_report.json)" % (len(review) - 25))

    def row(w):
        return {"name": w["name"], "loc": w["loc"], "id": w["iid"],
                "reason": w["reason"], "perks": sorted(w["traits"])}
    report = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {"weapons": len(weapons), "keep": len(keep),
                    "dismantle": len(dismantle), "review": len(review)},
        "keep": [row(w) for w in keep],
        "dismantle": [row(w) for w in dismantle],
        "review": [row(w) for w in review],
    }
    save_json(os.path.join(HERE, "vault_report.json"), report)
    print("\nFull report saved to vault_report.json")

    if do_lock:
        _lock_keepers(token, mtype, keep, prof)

def _lock_keepers(token, mtype, keepers, prof):
    chars = list(prof.get("characters", {}).get("data", {}).keys())
    char_id = chars[0] if chars else None
    if not char_id:
        die("No character found to issue lock command.")
    print("\nAbout to LOCK %d keeper items via the API." % len(keepers))
    if input("Type 'yes' to proceed: ").strip().lower() != "yes":
        print("Aborted. Nothing locked.")
        return
    ok = 0
    for w in keepers:
        body = {"state": True, "itemId": w["iid"],
                "characterId": char_id, "membershipType": mtype}
        try:
            api_post("/Destiny2/Actions/Items/SetLockState/", body, token)
            ok += 1
        except SystemExit:
            print("  FAILED to lock: %s" % w["name"])
    print("Locked %d/%d keepers." % (ok, len(keepers)))

# ---------------------------------------------------------------------------
# entry
# ---------------------------------------------------------------------------

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "setup":
        cmd_setup()
    elif cmd == "login":
        cmd_login()
    elif cmd == "whoami":
        cmd_whoami()
    elif cmd == "loadouts":
        cmd_loadouts()
    elif cmd == "scan":
        cmd_scan(do_lock=False)
    elif cmd == "lock-keepers":
        cmd_scan(do_lock=True)
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
