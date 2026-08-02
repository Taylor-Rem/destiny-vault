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
    python3 destiny_vault.py unlock-all   # unlock all locked weapons (clean slate)
    python3 destiny_vault.py armor-scan [build]        # rank armor for Super builds
    python3 destiny_vault.py armor-cleanup [--lock]    # Warlock keep/dismantle armor
                                                       #   report; --lock re-syncs locks
    python3 destiny_vault.py equip-armor <build> [--loadout N] [--dry-run]
    python3 destiny_vault.py apply-loadout <build> <slot 1-10> [--dry-run]

      --exotic "<name>"   pin the exotic armour piece instead of letting the
                          stat score choose it (needed when a build REQUIRES a
                          specific exotic, e.g. --exotic "Secant Filaments")
      --weapon "<name>"   also transfer + equip this weapon; repeatable, max one
                          per Kinetic/Energy/Power slot

    builds: super-class | super-grenade | super-melee | class-grenade | grenade-class
            ("Intellect" is now Super)
    equip-armor / apply-loadout write to your LIVE character (be in orbit). Add
    --dry-run to preview the transfer/equip plan without changing anything.

Requires: Python 3.8+, and PyYAML  (pip3 install pyyaml)
"""

import base64
import http.server
import json
import os
import sys
import time
import urllib.error
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

def api_action(path, body, token):
    """POST like api_post but NON-fatal: returns the full response dict (incl.
    ErrorCode/ErrorStatus/Message) instead of dying, so callers can handle
    per-item failures (in-activity, wrong location, etc.) themselves."""
    cfg = load_json(CONFIG_PATH) or {}
    raw = json.dumps(body).encode()
    req = urllib.request.Request(API_ROOT + path, data=raw, method="POST")
    req.add_header("X-API-Key", cfg["api_key"])
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return json.load(e)
        except Exception:
            return {"ErrorCode": -1, "ErrorStatus": "HTTPError", "Message": str(e)}

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

# Curated behavioural weapon perks, split into VALUE TIERS per the owner's policy
# (boss DPS / ad-clear > ability regen > handling). VALUED_PERKS (DPS/ad-clear +
# ability) are worth keeping a *distinct* duplicate for; FILLER_PERKS
# (reload/handling/ammo economy) are not — a copy whose only edge over a kept
# copy is a filler perk is treated as covered and dismantled. TRAIT_PERKS (the
# union) drives sole-source coverage, so it must stay comprehensive. Keep in
# sync with research/weapons-pve-perks.md.
DPS_ADCLEAR_PERKS = {
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
}
ABILITY_PERKS = {  # ability / build economy — this owner (Warlock ability spam) values these
    "Demolitionist", "Wellspring", "Pugilist", "Grave Robber", "Osmosis",
    "Attrition Orbs", "Classy Contender", "Discord",
}
FILLER_PERKS = {   # reload / handling / ammo economy — not worth keeping a dupe for
    "Subsistence", "Feeding Frenzy", "Overflow", "Clown Cartridge",
    "Ambitious Assassin", "Rapid Hit", "Outlaw", "Perpetual Motion",
    "Lead from Gold", "Shoot to Loot",
}
VALUED_PERKS = DPS_ADCLEAR_PERKS | ABILITY_PERKS
TRAIT_PERKS = VALUED_PERKS | FILLER_PERKS

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
    # 102 vault, 201 char inv, 205 equipped, 206 loadouts, 300 instances,
    # 305 sockets (active plugs), 310 reusable plugs (all SELECTABLE perks —
    # needed so high Gear-Tier weapons that can swap perks are judged on what
    # they CAN roll, not just what's currently slotted)
    comps = "102,201,205,206,300,305,310"
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

def item_selectable_perks(instance_id, reuse_data):
    """Every reusable/selectable plug hash across an item's sockets (component
    310) — i.e. perks the weapon CAN swap to, not just the one slotted. Essential
    for high Gear-Tier weapons with multiple perks per trait column; without it a
    swappable god-roll looks identical to a bare roll. Non-trait plugs (barrels,
    mags, shaders) are filtered out later by TRAIT_PERKS."""
    entry = reuse_data.get(instance_id)
    if not entry:
        return []
    out = []
    for _sidx, plugs in entry.get("plugs", {}).items():
        for p in plugs:
            h = p.get("plugItemHash")
            if h:
                out.append(h)
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

def _collect_weapons(prof, sockets_data, reuse_data, protected):
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
        pool = perks + [def_name("DestinyInventoryItemDefinition", h)
                        for h in item_selectable_perks(iid, reuse_data)]
        weapons.append({
            "name": meta["name"], "loc": it["_loc"], "iid": iid,
            "tier": meta.get("tier"), "type": meta.get("type", ""),
            "perks": perks, "sig": frozenset(perks),
            "traits": set(perks) & TRAIT_PERKS,   # currently-slotted behavioural perks
            "pool": set(pool) & TRAIT_PERKS,       # everything it CAN roll (drives decisions)
            "prot": iid in protected,
            "crafted": bool(it.get("state", 0) & 8),  # state flag 8 = Crafted -> never dismantle
            "reason": None,
        })
    return weapons

def cmd_scan(do_lock=False):
    from collections import defaultdict
    token, _ = get_token()
    rules = load_rules()
    mtype, mid, prof = fetch_profile(token)
    sockets_data = prof.get("itemComponents", {}).get("sockets", {}).get("data", {})
    reuse_data = prof.get("itemComponents", {}).get("reusablePlugs", {}).get("data", {})

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

    weapons = _collect_weapons(prof, sockets_data, reuse_data, protected)
    _flush_caches()

    # Pass 2 input: which trait perks are on exactly ONE weapon (vault-relative).
    # Uses the CAN-roll pool, not just slotted perks — a weapon that can swap to a
    # rare perk still counts as a source of it.
    sources = defaultdict(set)
    for w in weapons:
        for p in w["pool"]:
            sources[p].add(w["iid"])

    # base KEEP signals: Pass 0 (protect) > Pass 1 (god roll) > Pass 2 (sole source).
    # God-roll and sole-source both consider the full pool (what the weapon CAN
    # roll), so a swappable god-roll is recognised even when a filler perk is slotted.
    for w in weapons:
        w["godroll"] = bool(w["name"] in rules
                            and classify(w["name"], sorted(w["pool"]), rules[w["name"]])[0])
        w["sole"] = sorted(p for p in w["pool"] if len(sources[p]) == 1)
        if w["prot"]:
            w["reason"] = "in loadout / equipped"
        elif w["crafted"]:
            w["reason"] = "crafted (never dismantle)"
        elif w["godroll"]:
            w["reason"] = "god roll"
        elif w["sole"]:
            w["reason"] = "only source of " + ", ".join(w["sole"])
        elif w["tier"] == 6:
            w["reason"] = "exotic (keep >=1)"      # Pass 3: exotic coverage

    # Passes 3-5: rank copies of the SAME weapon against each other. Keep every
    # copy that carries its own value (protected / god roll / sole-source, or a
    # meaningfully different roll). A copy is a safe DISMANTLE only when some kept
    # copy strictly covers it: same-or-superset behavioural perks AND same-or-
    # higher gear tier. Distinct rolls (a unique perk, or a better chassis) never
    # auto-dismantle -- they fall to REVIEW for a human call.
    def signal(w):
        return w["prot"] or w["crafted"] or w["godroll"] or bool(w["sole"])
    def rank(w):
        return (w["prot"], w["crafted"], w["godroll"], bool(w["sole"]),
                len(w["pool"]), (w["tier"] or 0))
    def valued(w):
        return w["pool"] & VALUED_PERKS
    def covered_by(c, kept):
        # Exotics (tier 6) are frequently random-rolled (Ergo Sum frames, etc.)
        # and their distinguishing perk often isn't in TRAIT_PERKS, so behavioural
        # subsetting would wrongly collapse distinct frames. For exotics we only
        # treat a byte-identical roll as a true duplicate; distinct exotic rolls
        # fall through to REVIEW. Legendaries are covered when a kept copy CAN roll
        # every VALUED perk this copy can (pool subset) at >= gear tier — compared
        # on the can-roll pool, so a copy is only trashed when a kept copy truly
        # matches its full capability, never merely its currently-slotted perk.
        for k in kept:
            if c is k:
                continue
            if c["tier"] == 6:
                if c["sig"] == k["sig"]:
                    return True
            elif valued(c) <= valued(k) and (c["tier"] or 0) <= (k["tier"] or 0):
                return True
        return False

    keep, dismantle, review = [], [], []
    by_name = defaultdict(list)
    for w in weapons:
        by_name[w["name"]].append(w)

    for nm, grp in by_name.items():
        grp.sort(key=rank, reverse=True)   # best copy first
        n = len(grp)
        kept = []                          # copies we've decided to keep in this group
        for i, w in enumerate(grp):
            if i == 0:                     # best copy of this weapon -> always survives
                # keep the keeper if it carries a signal OR is an exotic (Pass 3:
                # never drop your last copy of an exotic); else it's your call.
                if signal(w) or w["tier"] == 6:
                    keep.append(w)
                else:
                    w["reason"] = ("best of %d copies - keep or trim (your call)" % n
                                   if n > 1 else "no god-roll / coverage match")
                    review.append(w)
                kept.append(w)
            elif signal(w):                # a distinct valuable copy (god roll / sole / protected)
                keep.append(w); kept.append(w)
            elif covered_by(w, kept):      # a kept copy already covers this roll -> safe to trash
                tag = "exotic " if w["tier"] == 6 else ""
                if w["pool"] and not (w["pool"] & VALUED_PERKS):
                    w["reason"] = "%sfiller perk only - kept a better copy" % tag
                else:
                    w["reason"] = "%sworse/dup roll - kept a better copy" % tag
                dismantle.append(w)
            else:                          # meaningfully different roll -> your call
                w["reason"] = "distinct roll of %s - your call" % nm
                review.append(w); kept.append(w)

    print("\n===== VAULT CLEANUP (%d weapons) =====" % len(weapons))
    print("  KEEP:      %d" % len(keep))
    print("  DISMANTLE: %d   (worse/dup rolls — a better copy is always kept)" % len(dismantle))
    print("  REVIEW:    %d   (your call — nothing auto-dismantled here)" % len(review))

    print("\n----- DISMANTLE (safe: a better copy of each is kept) -----")
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
                "reason": w["reason"], "perks": sorted(w["traits"]),
                "can_roll": sorted(w["pool"]), "all_perks": sorted(w["perks"]),
                "tier": w["tier"]}
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
        # Lock everything we are NOT dismantling (KEEP + REVIEW) so that the only
        # unlocked weapons left in the vault are the DISMANTLE candidates -- making
        # an in-game "dismantle everything unlocked" pass safe.
        _lock_keepers(token, mtype, keep + review, prof)

def _any_char_id(prof):
    """Any characterId from the profile. SetLockState needs a character even for
    vault items; we don't fetch component 200, so derive it from whatever
    character-keyed component we do have."""
    for comp in ("characters", "characterEquipment", "characterInventories",
                 "characterLoadouts"):
        d = prof.get(comp, {}).get("data", {})
        if d:
            return next(iter(d))
    return None

def _item_char_map(prof):
    """instanceId -> characterId it lives on. SetLockState on an EQUIPPED or
    character-held item must use *that* character's id; issuing it against a
    different character returns 'item not found'. Vault items aren't in here and
    fall back to any character."""
    m = {}
    for comp in ("characterEquipment", "characterInventories"):
        for cid, invd in prof.get(comp, {}).get("data", {}).items():
            for it in invd.get("items", []):
                if it.get("itemInstanceId"):
                    m[it["itemInstanceId"]] = cid
    return m

def cmd_unlock_all():
    """Unlock every currently-locked WEAPON (clean slate before re-locking).
    Reversible and non-destructive -- this never dismantles anything."""
    token, _ = get_token()
    mtype, mid, prof = fetch_profile(token)
    default_char = _any_char_id(prof)
    if not default_char:
        die("No character found to issue unlock command.")
    char_of = _item_char_map(prof)   # equipped/held items must unlock via their own char

    raw = [("Vault", it) for it in
           prof.get("profileInventory", {}).get("data", {}).get("items", [])]
    for cid, invd in prof.get("characterInventories", {}).get("data", {}).items():
        raw += [("Char " + cid[-4:], it) for it in invd.get("items", [])]
    for cid, invd in prof.get("characterEquipment", {}).get("data", {}).items():
        raw += [("Equip " + cid[-4:], it) for it in invd.get("items", [])]

    locked = []
    for loc, it in raw:
        iid = it.get("itemInstanceId")
        if not iid or not (it.get("state", 0) & 1):   # state flag 1 = Locked
            continue
        if item_meta(it["itemHash"]).get("itemType") != 3:   # weapons only
            continue
        locked.append((loc, iid, item_meta(it["itemHash"])["name"]))
    _flush_caches()

    print("Found %d currently-locked weapons." % len(locked))
    if not locked:
        print("Nothing to do -- vault weapons are already all unlocked.")
        return
    print("This will UNLOCK all of them (reversible; nothing is dismantled).")
    if input("Type 'yes' to unlock all: ").strip().lower() != "yes":
        print("Aborted. Nothing changed.")
        return
    ok = fail = 0
    for loc, iid, name in locked:
        body = {"state": False, "itemId": iid,
                "characterId": char_of.get(iid, default_char),
                "membershipType": mtype}
        resp = api_action("/Destiny2/Actions/Items/SetLockState/", body, token)
        if resp.get("ErrorCode") == 1:
            ok += 1
        else:
            fail += 1
            print("  FAILED %-24s %s" % (name[:24], resp.get("Message")))
    print("Unlocked %d/%d weapons (%d failed)." % (ok, len(locked), fail))

def _lock_keepers(token, mtype, keepers, prof):
    default_char = _any_char_id(prof)
    if not default_char:
        die("No character found to issue lock command.")
    char_of = _item_char_map(prof)   # equipped/held items must lock via their own char
    print("\nAbout to LOCK %d items via the API (keepers + review)." % len(keepers))
    if input("Type 'yes' to proceed: ").strip().lower() != "yes":
        print("Aborted. Nothing locked.")
        return
    ok = fail = 0
    for w in keepers:
        body = {"state": True, "itemId": w["iid"],
                "characterId": char_of.get(w["iid"], default_char),
                "membershipType": mtype}
        resp = api_action("/Destiny2/Actions/Items/SetLockState/", body, token)
        if resp.get("ErrorCode") == 1:
            ok += 1
        else:
            fail += 1
            print("  FAILED %-24s %s" % (w["name"][:24], resp.get("Message")))
    print("Locked %d/%d items (%d failed)." % (ok, len(keepers), fail))

# ---------------------------------------------------------------------------
# armor: scan + build ranking  (Armor 3.0 — see DESTINY_REFERENCE.md sec 8-9)
# ---------------------------------------------------------------------------
# Stat names are resolved LIVE from the manifest (Intellect->Super,
# Discipline->Grenade, Strength->Melee, Recovery->Class, Mobility->Weapons,
# Resilience->Health) so we never hardcode a stale hash->name mapping.
ARMOR_SLOTS = {26: "Helmet", 27: "Gauntlets", 28: "Chest", 29: "Legs", 30: "Class Item"}
ARMOR_STATS = {"Weapons", "Health", "Class", "Grenade", "Super", "Melee"}
# build key -> (primary stat, secondary stat). Primary is always Super here.
BUILDS = {
    "super-class":   ("Super", "Class"),
    "super-grenade": ("Super", "Grenade"),
    "super-melee":   ("Super", "Melee"),
    # ability-uptime builds: no Super weighting at all. class-grenade is for
    # rift-loop builds (Empowering Rift engines) where Grenade also scales an
    # aspect's damage (e.g. Child of the Old Gods' Void Soul).
    "class-grenade": ("Class", "Grenade"),
    "grenade-class": ("Grenade", "Class"),
}
ADEF_CACHE = os.path.join(HERE, ".armor_defs_cache.json")
_adefs = None

def armor_meta(hash_):
    """Cached armor def: {name, itemType, subType, classType, tier}. Kept in a
    SEPARATE cache from the weapon def cache, which only stored 4 fields and would
    otherwise return None for subType/classType on already-cached hashes."""
    global _adefs
    if _adefs is None:
        _adefs = load_json(ADEF_CACHE, {})
    k = str(hash_)
    if k in _adefs:
        return _adefs[k]
    try:
        d = api_get("/Destiny2/Manifest/DestinyInventoryItemDefinition/%s/" % hash_)
    except SystemExit:
        d = {}
    _adefs[k] = {
        "name": d.get("displayProperties", {}).get("name", str(hash_)),
        "itemType": d.get("itemType"),
        "subType": d.get("itemSubType"),
        "classType": d.get("classType"),
        "tier": d.get("inventory", {}).get("tierType"),
    }
    _mark_dirty(ADEF_CACHE, _adefs)
    return _adefs[k]

_statname = {}
def stat_name(hash_):
    if hash_ not in _statname:
        _statname[hash_] = def_name("DestinyStatDefinition", hash_)
    return _statname[hash_]

def fetch_armor_profile(token):
    mtype, mid, name = get_membership(token)
    # 200 characters, 102 vault, 201 char inv, 205 equipped, 300 instances
    # (gearTier), 304 item stats, 206 loadouts
    comps = "200,102,201,205,300,304,206"
    prof = api_get("/Destiny2/%s/Profile/%s/?components=%s" % (mtype, mid, comps), token)
    return mtype, mid, name, prof

def collect_armor(prof):
    """Return list of armor piece dicts with per-stat values + current location.
    owner = character id that holds it, or None if in the vault."""
    stats_data = prof.get("itemComponents", {}).get("stats", {}).get("data", {})
    inst_data = prof.get("itemComponents", {}).get("instances", {}).get("data", {})
    raw = []
    for it in prof.get("profileInventory", {}).get("data", {}).get("items", []):
        raw.append((it, None, False))
    for cid, inv in prof.get("characterInventories", {}).get("data", {}).items():
        for it in inv.get("items", []):
            raw.append((it, cid, False))
    for cid, inv in prof.get("characterEquipment", {}).get("data", {}).items():
        for it in inv.get("items", []):
            raw.append((it, cid, True))

    out = []
    for it, owner, equipped in raw:
        iid = it.get("itemInstanceId")
        if not iid:
            continue
        m = armor_meta(it["itemHash"])
        if m.get("itemType") != 2:
            continue  # armor only
        slot = ARMOR_SLOTS.get(m.get("subType"))
        if not slot:
            continue  # skip ghosts / non-gear type-2 items
        s = {}
        for sh, sv in stats_data.get(iid, {}).get("stats", {}).items():
            nm = stat_name(int(sh))
            if nm in ARMOR_STATS:
                s[nm] = sv.get("value", 0)
        if not s:
            continue
        top = sorted(s.items(), key=lambda x: -x[1])
        out.append({
            "name": m["name"], "hash": it["itemHash"], "iid": iid,
            "slot": slot, "classType": m.get("classType"),
            "exotic": m.get("tier") == 6, "owner": owner, "equipped": equipped,
            "stats": s, "total": sum(s.values()),
            # gearTier is the Armor Gear Tier (1-5; 0 = legacy/pre-tier armor) —
            # NOT rarity. Read from the instance component, not the item def.
            "gt": inst_data.get(iid, {}).get("gearTier", 0),
            "top2": {top[0][0], top[1][0]},   # archetype = two highest stats
        })
    return out

def _score(p, primary, sec):
    return p["stats"].get(primary, 0) + p["stats"].get(sec, 0)

# Armor 3.0: a stat only pays the "enhanced" benefit above 100, and there is no
# extra return for overshooting. A plain sum is blind to that — it rates
# (165, 84) the same as (124, 125) — so balanced picking scores each stat only up
# to the threshold, which drives BOTH across 100 before padding either one.
BALANCE_TARGET = 100

def _balanced_key(p, q, target=BALANCE_TARGET):
    return (min(p, target) + min(q, target), min(p, q), p + q)

def _set_totals(combo, primary, sec):
    return (sum(x["stats"].get(primary, 0) for x in combo.values()),
            sum(x["stats"].get(sec, 0) for x in combo.values()))

def _pick_balanced(per_slot, fixed, primary, sec, topk=6):
    """Search armor SETS instead of picking each slot greedily. Greedy-per-slot
    can't optimise a whole-set shape like 'both stats past 100', because the best
    single piece for one stat often starves the other. Keeps the top-k candidates
    per slot by raw score, then brute-forces the combinations (<=k^5)."""
    import itertools
    slots = [s for s in per_slot if s not in fixed]
    pools = []
    for s in slots:
        cands = sorted(per_slot[s],
                       key=lambda p: (_score(p, primary, sec), p["total"]),
                       reverse=True)[:topk]
        if not cands:
            return None
        pools.append(cands)
    best, best_key = None, None
    for pick in itertools.product(*pools):
        combo = dict(fixed)
        combo.update(dict(zip(slots, pick)))
        p, q = _set_totals(combo, primary, sec)
        key = _balanced_key(p, q)
        if best_key is None or key > best_key:
            best_key, best = key, combo
    return best

def pick_build(pieces, class_type, primary, sec, pin_exotic=None, min_gt=4,
               balance=False):
    """Choose the best wearable loadout: best legendary per slot, then the single
    slot whose exotic gives the biggest score gain (only one exotic can be worn).
    Returns (chosen: {slot: piece}, exotic_slot).

    pin_exotic: exotic armor name (case-insensitive substring). When given, that
    exotic is forced into its slot and only its slot is considered for the exotic,
    so a build that NEEDS a specific exotic isn't overridden by raw stat score.

    min_gt: minimum armor gearTier for LEGENDARY picks, matching armor-cleanup's
    keep threshold — without it a stat-dense but gear-tier-2 piece (low total, and
    already flagged DISMANTLE) can out-score a tier-5 one. Falls back per slot if
    nothing meets the bar. Never applied to the exotic, whose slot is fixed."""
    cls = [p for p in pieces if p["classType"] == class_type]
    best_leg, best_exo = {}, {}
    for slot in ARMOR_SLOTS.values():
        cands = [p for p in cls if p["slot"] == slot]
        legs = [p for p in cands if not p["exotic"]]
        tiered = [p for p in legs if p.get("gt", 0) >= min_gt]
        if tiered:
            legs = tiered
        exos = [p for p in cands if p["exotic"]]
        if pin_exotic:
            exos = [p for p in exos if pin_exotic.lower() in p["name"].lower()]
        if legs:
            best_leg[slot] = max(legs, key=lambda p: (_score(p, primary, sec), p["total"]))
        if exos:
            best_exo[slot] = max(exos, key=lambda p: (_score(p, primary, sec), p["total"]))
    if pin_exotic and not best_exo:
        die("No exotic armor matching '%s' found for this class. "
            "Check the name against `armor-cleanup` output." % pin_exotic)
    slots = list(ARMOR_SLOTS.values())

    if balance:
        per_slot = {}
        for slot in slots:
            legs = [p for p in cls if p["slot"] == slot and not p["exotic"]]
            tiered = [p for p in legs if p.get("gt", 0) >= min_gt]
            per_slot[slot] = tiered or legs
        if pin_exotic:
            eslot = next(iter(best_exo))
            combo = _pick_balanced(per_slot, {eslot: best_exo[eslot]}, primary, sec)
            if combo:
                return combo, eslot
        else:
            best, best_key, best_eslot = None, None, None
            for eslot in best_exo:
                combo = _pick_balanced(per_slot, {eslot: best_exo[eslot]}, primary, sec)
                if not combo:
                    continue
                key = _balanced_key(*_set_totals(combo, primary, sec))
                if best_key is None or key > best_key:
                    best_key, best, best_eslot = key, combo, eslot
            if best:
                return best, best_eslot

    best, best_val = None, -1
    for eslot in slots:
        if eslot not in best_exo:
            continue
        combo = dict(best_leg)
        combo[eslot] = best_exo[eslot]
        if len(combo) < len(slots):
            continue  # missing a legendary in some slot; skip
        val = sum(_score(combo[s], primary, sec) for s in slots)
        if val > best_val:
            best_val, best = val, (combo, eslot)
    # fallback: no full legendary set -> just take best of any per slot
    if best is None:
        combo, eslot = {}, None
        for slot in slots:
            cands = [p for p in cls if p["slot"] == slot]
            if pin_exotic:
                # keep the pinned exotic in its own slot, legendaries everywhere else
                if slot in best_exo:
                    combo[slot] = best_exo[slot]
                    eslot = slot
                    continue
                cands = [p for p in cands if not p["exotic"]]
            tiered = [p for p in cands if p.get("gt", 0) >= min_gt]
            if tiered:
                cands = tiered
            if cands:
                combo[slot] = max(cands, key=lambda p: (_score(p, primary, sec), p["total"]))
        return combo, eslot
    return best

CLASS_BY_NAME = {"titan": 0, "hunter": 1, "warlock": 2}

def _print_build(combo, exotic_slot, primary, sec):
    order = ["Weapons", "Health", "Class", "Grenade", "Super", "Melee"]
    tp = ts = 0
    for slot in ARMOR_SLOTS.values():
        p = combo.get(slot)
        if not p:
            print("   %-11s (none found)" % slot); continue
        tp += p["stats"].get(primary, 0); ts += p["stats"].get(sec, 0)
        body = " ".join("%s%d" % (k[0], p["stats"].get(k, 0)) for k in order)
        mark = "*" if slot == exotic_slot else " "
        loc = "equipped" if p["equipped"] else ("vault" if p["owner"] is None else "char")
        print("  %s %-11s %-26s %s%2d/%s%2d  tot%3d  [%s]%s %s" % (
            mark, slot, p["name"][:26], primary[:2], p["stats"].get(primary, 0),
            sec[:3], p["stats"].get(sec, 0), p["total"],
            "EXOTIC" if p["exotic"] else "leg", "", loc))
    print("   ---- set totals: %s=%d  %s=%d  (raw armor, pre mods/fragments)" %
          (primary, tp, sec, ts))

def cmd_armor_scan(build=None):
    token, _ = get_token()
    mtype, mid, name, prof = fetch_armor_profile(token)
    pieces = collect_armor(prof)
    _flush_caches()
    save_json(os.path.join(HERE, "armor_report.json"),
              {"account": name, "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
               "pieces": pieces})
    # which classes actually own armor
    by_cls = {}
    for p in pieces:
        by_cls[p["classType"]] = by_cls.get(p["classType"], 0) + 1
    print("Account: %s  |  armor pieces: %d" % (name, len(pieces)))
    for ct, n in sorted(by_cls.items(), key=lambda kv: -kv[1]):
        print("  %-7s: %d" % (CLASS_TYPES.get(ct, ct), n))
    main_cls = max(by_cls, key=by_cls.get) if by_cls else 2
    builds = [build] if build else list(BUILDS)
    for bk in builds:
        primary, sec = BUILDS[bk]
        combo, eslot = pick_build(pieces, main_cls, primary, sec)
        print("\n===== %s  (%s, best 1-exotic loadout) =====" % (bk, CLASS_TYPES.get(main_cls)))
        _print_build(combo, eslot, primary, sec)
    print("\nSaved armor_report.json")

# ---------------------------------------------------------------------------
# armor: keep/dismantle cleanup  (Warlock; owner's ability-focus policy)
# ---------------------------------------------------------------------------
DESIRED_STATS = {"Super", "Class", "Grenade", "Melee"}  # owner's ability-focus stats

def classify_armor(pieces, protected):
    """Warlock keep/dismantle per owner policy: keep tier-4+ 'pure-ability'
    legendaries (top-2 stats both in DESIRED_STATS) + the best copy of each
    exotic; dismantle tier<4, off-stat (Health/Weapons-forward), and same-
    archetype exotic dupes; distinct exotic archetypes + exotic class items go to
    REVIEW. Off-class (non-Warlock) pieces are returned separately, untouched.
    Uses the real armor gearTier (p['gt']), not rarity."""
    from collections import defaultdict
    keep, dismantle, review, offclass = [], [], [], []
    warlock = []
    for p in pieces:
        p["prot"] = p["iid"] in protected
        (offclass if p["classType"] != 2 else warlock).append(p)
    # Rank/compare exotic copies by ABILITY-stat points (Super/Class/Grenade/Melee),
    # not raw total. Raw total is useless here — every Tier-5 roll totals 75 (30/25/20),
    # so ranking on it ignored the tertiary stat and could keep a roll that wastes
    # its 20 in Weapons/Health over one that puts it in a desired stat.
    def dvec(p):
        return {k: p["stats"].get(k, 0) for k in DESIRED_STATS}
    def dsum(p):
        return sum(dvec(p).values())
    def dominates(a, b):   # a >= b in EVERY ability stat, at >= gear tier
        return a["gt"] >= b["gt"] and all(dvec(a)[k] >= dvec(b)[k] for k in DESIRED_STATS)

    groups = defaultdict(list)
    for p in (x for x in warlock if x["exotic"]):
        groups[p["name"]].append(p)
    for nm, grp in groups.items():
        if grp[0]["slot"] == "Class Item":       # perk combos vary -> your call
            for p in grp:
                p["reason"] = "exotic class item - perk combos vary (review)"
                review.append(p)
            continue
        grp.sort(key=lambda p: (p["prot"], dsum(p), p["gt"], p["total"]), reverse=True)
        kept = []
        for i, p in enumerate(grp):
            if i == 0:
                p["reason"] = "exotic - best ability roll kept (%d in Su/Cl/Gr/Me)" % dsum(p)
                keep.append(p); kept.append(p)
            elif p["prot"]:
                p["reason"] = "exotic (equipped/loadout)"; keep.append(p); kept.append(p)
            elif any(dominates(k, p) for k in kept):
                p["reason"] = "exotic dup - a kept copy beats it in every ability stat"
                dismantle.append(p)
            else:                                 # distinct useful spread -> your call
                p["reason"] = "distinct exotic roll (%d in Su/Cl/Gr/Me) - your call" % dsum(p)
                review.append(p); kept.append(p)
    for p in (x for x in warlock if not x["exotic"]):
        if p["prot"]:
            p["reason"] = "equipped / in loadout"; keep.append(p)
        elif p["gt"] < 4:
            p["reason"] = ("tier %d (<4)" % p["gt"]) if p["gt"] else "legacy (no tier)"
            dismantle.append(p)
        elif not (p["top2"] <= DESIRED_STATS):
            lead = "Health" if "Health" in p["top2"] else "Weapons"
            p["reason"] = "%s-forward (top2 %s)" % (lead, "+".join(sorted(p["top2"])))
            dismantle.append(p)
        else:
            p["reason"] = "tier %d %s" % (p["gt"], "+".join(sorted(p["top2"])))
            keep.append(p)
    return keep, dismantle, review, offclass

def cmd_armor_cleanup(do_lock=False):
    token, _ = get_token()
    mtype, mid, name, prof = fetch_armor_profile(token)
    pieces = collect_armor(prof)
    _flush_caches()
    protected = set()
    for _cid, invd in prof.get("characterEquipment", {}).get("data", {}).items():
        for it in invd.get("items", []):
            if it.get("itemInstanceId"):
                protected.add(it["itemInstanceId"])
    for _cid, cl in prof.get("characterLoadouts", {}).get("data", {}).items():
        for lo in cl.get("loadouts", []):
            for it in lo.get("items", []):
                if it.get("itemInstanceId", "0") != "0":
                    protected.add(it["itemInstanceId"])
    keep, dismantle, review, offclass = classify_armor(pieces, protected)

    print("\n===== WARLOCK ARMOR CLEANUP (%d pieces; %d off-class skipped) =====" %
          (len(keep) + len(dismantle) + len(review), len(offclass)))
    print("  KEEP:      %d" % len(keep))
    print("  DISMANTLE: %d   (tier<4 / off-stat / dup exotic)" % len(dismantle))
    print("  REVIEW:    %d   (exotic class items + distinct exotic rolls)" % len(review))
    print("\n----- DISMANTLE -----")
    for p in sorted(dismantle, key=lambda p: p["slot"])[:60]:
        print("  [DISMANTLE] %-24s %-11s | %s" % (p["name"][:24], p["slot"], p["reason"]))
    if len(dismantle) > 60:
        print("  ...and %d more (see armor_cleanup_report.json)" % (len(dismantle) - 60))

    def row(p):
        return {"name": p["name"], "iid": p["iid"], "slot": p["slot"],
                "exotic": p["exotic"], "gt": p["gt"], "total": p["total"],
                "reason": p["reason"]}
    save_json(os.path.join(HERE, "armor_cleanup_report.json"), {
        "account": name, "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {"keep": len(keep), "dismantle": len(dismantle),
                    "review": len(review), "off_class": len(offclass)},
        "keep": [row(p) for p in keep], "dismantle": [row(p) for p in dismantle],
        "review": [row(p) for p in review]})
    print("\nSaved armor_cleanup_report.json")

    if do_lock:
        _apply_armor_locks(token, mtype, prof, keep + review, offclass, dismantle)

def _apply_armor_locks(token, mtype, prof, survivors, offclass, dismantle):
    """Lock survivors (keep+review) and off-class pieces (protect), unlock the
    dismantle candidates -- so an in-game 'dismantle everything unlocked' hits
    only the flagged pieces. Off-class armor is protected, not classified."""
    default_char = _any_char_id(prof)
    if not default_char:
        die("No character found to issue lock command.")
    char_of = _item_char_map(prof)
    lock_list = survivors + offclass
    print("\nAbout to LOCK %d armor (keep+review+off-class) and UNLOCK %d dismantle "
          "candidates via the API." % (len(lock_list), len(dismantle)))
    if input("Type 'yes' to proceed: ").strip().lower() != "yes":
        print("Aborted. Nothing changed."); return
    def setlock(iid, state):
        body = {"state": state, "itemId": iid,
                "characterId": char_of.get(iid, default_char), "membershipType": mtype}
        return api_action("/Destiny2/Actions/Items/SetLockState/", body, token).get("ErrorCode") == 1
    lok = sum(setlock(p["iid"], True) for p in lock_list)
    uok = sum(setlock(p["iid"], False) for p in dismantle)
    print("Locked %d/%d (keep+review+off-class), unlocked %d/%d (dismantle)." %
          (lok, len(lock_list), uok, len(dismantle)))

# ---------------------------------------------------------------------------
# armor: transfer + equip + loadout snapshot  (live game-state writes)
# ---------------------------------------------------------------------------

def _transfer(token, mtype, item_hash, iid, character_id, to_vault):
    body = {"itemReferenceHash": item_hash, "stackSize": 1,
            "transferToVault": to_vault, "itemId": iid,
            "characterId": character_id, "membershipType": mtype}
    r = api_action("/Destiny2/Actions/Items/TransferItem/", body, token)
    return r.get("ErrorCode") == 1, r.get("ErrorStatus"), r.get("Message")

def plan_equip(combo, target_id):
    """Build the ordered list of (action, piece) needed to get every piece onto
    target_id and equipped. Actions: 'skip' (already equipped), 'equip' (on char),
    'v2c' (vault->char), 'c2v2c' (other char->vault->char), 'blocked' (equipped
    on another character — needs manual unequip)."""
    steps = []
    for slot in ARMOR_SLOTS.values():
        p = combo.get(slot)
        if not p:
            continue
        if p["owner"] == target_id and p["equipped"]:
            steps.append(("skip", p))
        elif p["owner"] == target_id:
            steps.append(("equip", p))
        elif p["owner"] is None:
            steps.append(("v2c", p))
        elif p["equipped"]:
            steps.append(("blocked", p))
        else:
            steps.append(("c2v2c", p))
    return steps

WEAPON_BUCKETS = {1498876634: "Kinetic", 2465295065: "Energy", 953998645: "Power"}

def collect_weapons(prof):
    """Every weapon instance the account holds, with its slot + location.
    Same owner convention as collect_armor: owner=None means it's in the vault."""
    raw = []
    for it in prof.get("profileInventory", {}).get("data", {}).get("items", []):
        raw.append((it, None, False))
    for cid, inv in prof.get("characterInventories", {}).get("data", {}).items():
        for it in inv.get("items", []):
            raw.append((it, cid, False))
    for cid, inv in prof.get("characterEquipment", {}).get("data", {}).items():
        for it in inv.get("items", []):
            raw.append((it, cid, True))

    out = []
    for it, owner, equipped in raw:
        iid = it.get("itemInstanceId")
        if not iid:
            continue
        # item_meta shares the warm weapon-def cache that `scan` populates, so this
        # stays offline for anything already scanned.
        m = item_meta(it["itemHash"])
        if m.get("itemType") != 3:
            continue                            # 3 = weapon
        out.append({"name": m.get("name") or str(it["itemHash"]),
                    "hash": it["itemHash"], "iid": iid, "owner": owner,
                    "equipped": equipped,
                    # character items carry their real slot; vault items report the
                    # vault bucket, so those are resolved lazily in _weapon_bucket().
                    "bucket": WEAPON_BUCKETS.get(it.get("bucketHash")),
                    "type": m.get("type", "")})
    return out

def _weapon_bucket(p):
    """Resolve a weapon's equip slot, fetching the def only when the instance is in
    the vault (where bucketHash reports the vault, not Kinetic/Energy/Power)."""
    if p.get("bucket"):
        return p["bucket"]
    try:
        d = api_get("/Destiny2/Manifest/DestinyInventoryItemDefinition/%s/" % p["hash"])
        b = d.get("inventory", {}).get("bucketTypeHash")
    except SystemExit:
        b = None
    p["bucket"] = WEAPON_BUCKETS.get(b, "?")
    return p["bucket"]

def plan_weapons(names, wpieces, class_type, target_id):
    """Resolve each requested weapon name to one instance and plan the move+equip.
    Prefers a copy already on the target character, then the vault, then another
    character. Reuses plan_equip's action vocabulary."""
    steps = []
    for want in names:
        cands = [p for p in wpieces if want.lower() in p["name"].lower()]
        if not cands:
            die("No weapon matching '%s' found in your inventory or vault." % want)
        # prefer: already equipped here > on this char > vault > elsewhere
        def rank(p):
            if p["owner"] == target_id and p["equipped"]:
                return 0
            if p["owner"] == target_id:
                return 1
            if p["owner"] is None:
                return 2
            return 4 if p["equipped"] else 3
        p = min(cands, key=rank)
        r = rank(p)
        act = ("skip", "equip", "v2c", "c2v2c", "blocked")[r]
        _weapon_bucket(p)
        steps.append((act, p))
    buckets = [p["bucket"] for _, p in steps]
    dupes = set(b for b in buckets if buckets.count(b) > 1)
    if dupes:
        die("Two or more requested weapons share the %s slot — pick one per slot."
            % "/".join(sorted(dupes)))
    return steps

def cmd_equip_armor(build, dry_run=False, do_snapshot_slot=None, pin_exotic=None,
                    weapons=None, balance=False):
    if build not in BUILDS:
        die("Unknown build '%s'. Choose: %s" % (build, ", ".join(BUILDS)))
    primary, sec = BUILDS[build]
    token, _ = get_token()
    mtype, mid, name, prof = fetch_armor_profile(token)
    pieces = collect_armor(prof)
    _flush_caches()
    chars = prof.get("characters", {}).get("data", {})
    # target = the character whose class matches the build's owning class (main = most armor)
    by_cls = {}
    for p in pieces:
        by_cls[p["classType"]] = by_cls.get(p["classType"], 0) + 1
    target_cls = max(by_cls, key=by_cls.get) if by_cls else 2
    target_id = next((cid for cid, ch in chars.items()
                      if ch.get("classType") == target_cls), None)
    if not target_id:
        die("No character found for class %s." % CLASS_TYPES.get(target_cls))

    combo, eslot = pick_build(pieces, target_cls, primary, sec, pin_exotic=pin_exotic,
                              balance=balance)
    steps = plan_equip(combo, target_id)

    wsteps = []
    if weapons:
        wpieces = collect_weapons(prof)
        wsteps = plan_weapons(weapons, wpieces, target_cls, target_id)

    print("=== EQUIP PLAN: %s onto %s (char ...%s) ===" %
          (build, CLASS_TYPES.get(target_cls), target_id[-4:]))
    if pin_exotic:
        print("    (exotic pinned to '%s')" % pin_exotic)
    _print_build(combo, eslot, primary, sec)
    if wsteps:
        print("\n  Weapons:")
        for act, p in wsteps:
            print("    %-9s %-26s %s" % (p["bucket"], p["name"][:26],
                                         "" if act != "blocked" else "(equipped elsewhere)"))
    print("\nActions:")
    verbs = {"skip": "already equipped, skip", "equip": "equip (already on char)",
             "v2c": "vault -> character, then equip",
             "c2v2c": "other char -> vault -> character, then equip",
             "blocked": "EQUIPPED ON ANOTHER CHARACTER — unequip it in-game first"}
    for act, p in steps + wsteps:
        print("  - %-9s %-26s : %s" % (p.get("slot") or p.get("bucket"),
                                       p["name"][:26], verbs[act]))
    if any(a == "blocked" for a, _ in steps + wsteps):
        print("\n! One or more items are equipped on another character. Unequip them "
              "in-game (equip something else there) and re-run.")
    if do_snapshot_slot is not None:
        los = prof.get("characterLoadouts", {}).get("data", {}).get(target_id, {}).get("loadouts", [])
        cur = "(empty)"
        if 0 <= do_snapshot_slot - 1 < len(los):
            lo = los[do_snapshot_slot - 1]
            cur = (def_name("DestinyLoadoutNameDefinition", lo["nameHash"])
                   if lo.get("nameHash") else "(unnamed)")
        print("\nThen SNAPSHOT the equipped kit into loadout slot %d (currently: %s)." %
              (do_snapshot_slot, cur))
        print("! Snapshot captures your WHOLE equipped set (weapons + subclass + armor),"
              " not just these 5 pieces.")

    if dry_run:
        print("\n[dry-run] No changes made.")
        return
    print("\nThis writes to your live character. You must be IN ORBIT or a social space"
          " (not in an activity).")
    if input("Type 'yes' to proceed: ").strip().lower() != "yes":
        print("Aborted. Nothing changed.")
        return

    # 1) get every piece onto the target character
    for act, p in steps + wsteps:
        if act in ("skip", "equip"):
            continue
        if act == "blocked":
            print("  SKIP %s (equipped elsewhere)" % p["name"]); continue
        if act == "c2v2c":
            ok, st, msg = _transfer(token, mtype, p["hash"], p["iid"], p["owner"], True)
            if not ok:
                print("  FAIL move-to-vault %s: %s %s" % (p["name"], st, msg)); continue
        ok, st, msg = _transfer(token, mtype, p["hash"], p["iid"], target_id, False)
        if not ok:
            print("  FAIL move-to-char %s: %s %s" % (p["name"], st, msg)); continue
        print("  moved %s -> character" % p["name"])
    # 2) equip everything (skip pieces still not on the character)
    equip_ids = [p["iid"] for act, p in steps + wsteps if act != "blocked"]
    body = {"itemIds": equip_ids, "characterId": target_id, "membershipType": mtype}
    r = api_action("/Destiny2/Actions/Items/EquipItems/", body, token)
    if r.get("ErrorCode") != 1:
        print("  EquipItems error: %s %s" % (r.get("ErrorStatus"), r.get("Message")))
    for res in r.get("Response", {}).get("equipResults", []):
        code = res.get("equipStatus")
        tag = "OK" if code == 1 else ("err %s" % code)
        print("  equip %s: %s" % (res.get("itemInstanceId"), tag))
    # 3) optional loadout snapshot
    if do_snapshot_slot is not None:
        sbody = {"loadoutIndex": do_snapshot_slot - 1,
                 "characterId": target_id, "membershipType": mtype}
        sr = api_action("/Destiny2/Actions/Loadouts/SnapshotLoadout/", sbody, token)
        if sr.get("ErrorCode") == 1:
            print("  snapshotted into loadout slot %d" % do_snapshot_slot)
        else:
            print("  snapshot error: %s %s" % (sr.get("ErrorStatus"), sr.get("Message")))
    print("Done.")

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
    elif cmd == "unlock-all":
        cmd_unlock_all()
    elif cmd == "armor-scan":
        build = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else None
        if build and build not in BUILDS:
            die("Unknown build '%s'. Choose: %s" % (build, ", ".join(BUILDS)))
        cmd_armor_scan(build)
    elif cmd == "armor-cleanup":
        cmd_armor_cleanup(do_lock="--lock" in sys.argv)
    elif cmd in ("equip-armor", "apply-loadout"):
        args = sys.argv[2:]
        dry = "--dry-run" in args
        args = [a for a in args if a != "--dry-run"]

        # --exotic "<name>" pins the exotic armour piece; --weapon "<name>" may be
        # repeated (max one per Kinetic/Energy/Power slot).
        balance = "--balance" in args
        args = [a for a in args if a != "--balance"]
        pin_exotic, want_weapons, rest = None, [], []
        i = 0
        while i < len(args):
            a = args[i]
            if a == "--exotic" and i + 1 < len(args):
                pin_exotic = args[i + 1]; i += 2; continue
            if a == "--weapon" and i + 1 < len(args):
                want_weapons.append(args[i + 1]); i += 2; continue
            if a == "--loadout" and i + 1 < len(args):
                i += 2; continue          # handled below off sys.argv
            rest.append(a); i += 1
        args = rest
        if not args:
            die("Usage: %s <build> %s [--exotic NAME] [--weapon NAME ...]" % (
                cmd, "<slot 1-10>" if cmd == "apply-loadout" else "[--loadout N] [--dry-run]"))
        build = args[0]
        slot = None
        if cmd == "apply-loadout":
            if len(args) < 2 or not args[1].isdigit():
                die("apply-loadout needs a loadout slot 1-10, e.g. apply-loadout %s 3" % build)
            slot = int(args[1])
        elif "--loadout" in sys.argv:
            i = sys.argv.index("--loadout")
            if i + 1 < len(sys.argv) and sys.argv[i + 1].isdigit():
                slot = int(sys.argv[i + 1])
        if slot is not None and not (1 <= slot <= 10):
            die("Loadout slot must be 1-10.")
        cmd_equip_armor(build, dry_run=dry, do_snapshot_slot=slot,
                        pin_exotic=pin_exotic, weapons=want_weapons or None,
                        balance=balance)
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
