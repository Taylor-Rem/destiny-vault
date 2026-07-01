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

def _exchange_code(code):
    cfg = load_json(CONFIG_PATH)
    body = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": cfg["client_id"],
    }
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
    print("Logged in. Access token valid ~%s min." % (tok.get("expires_in", 3600) // 60))

def get_token():
    tok = load_json(TOKEN_PATH) or die("Run 'login' first.")
    age = int(time.time()) - tok.get("obtained_at", 0)
    if age > tok.get("expires_in", 3600) - 120:
        print("(access token expired - run 'login' again)")
    return tok["access_token"], tok

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
    save_json(MANIFEST_CACHE, cache)
    return name

# ---------------------------------------------------------------------------
# scan
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
    # 102 vault, 201 char inv, 205 equipped, 300 instances, 305 sockets
    comps = "102,201,205,300,305"
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

def cmd_scan(do_lock=False):
    token, _ = get_token()
    rules = load_rules()
    mtype, mid, prof = fetch_profile(token)

    sockets_data = prof.get("itemComponents", {}).get("sockets", {}).get("data", {})

    # collect items from vault + all character inventories
    items = []
    vault = prof.get("profileInventory", {}).get("data", {}).get("items", [])
    for it in vault:
        it["_loc"] = "Vault"
        items.append(it)
    for cid, inv in prof.get("characterInventories", {}).get("data", {}).items():
        for it in inv.get("items", []):
            it["_loc"] = "Char " + cid[-4:]
            items.append(it)

    keepers, junk, unranked = [], [], []
    for it in items:
        iid = it.get("itemInstanceId")
        if not iid:
            continue  # not an instanced item (materials, etc.)
        name = def_name("DestinyInventoryItemDefinition", it["itemHash"])
        if name not in rules:
            unranked.append((name, it["_loc"], iid))
            continue
        perk_hashes = item_active_perks(iid, sockets_data)
        perk_names = [def_name("DestinyInventoryItemDefinition", h) for h in perk_hashes]
        keep, reason = classify(name, perk_names, rules[name])
        row = (name, it["_loc"], iid, reason, perk_names)
        (keepers if keep else junk).append(row)

    print("\n===== KEEP (%d) =====" % len(keepers))
    for name, loc, iid, reason, perks in keepers:
        print("  [KEEP] %-28s %-10s | %s" % (name[:28], loc, reason))
    print("\n===== DISMANTLE (%d) =====" % len(junk))
    for name, loc, iid, reason, perks in junk:
        print("  [JUNK] %-28s %-10s | %s" % (name[:28], loc, reason))
        print("         has: %s" % ", ".join(perks))
    print("\n===== NOT IN RULES (%d) - skipped =====" % len(unranked))
    for name, loc, iid in unranked[:40]:
        print("  [ -- ] %-28s %-10s" % (name[:28], loc))
    if len(unranked) > 40:
        print("  ...and %d more" % (len(unranked) - 40))

    # write a report file too
    report = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "keep": [{"name": r[0], "loc": r[1], "id": r[2], "reason": r[3]} for r in keepers],
        "dismantle": [{"name": r[0], "loc": r[1], "id": r[2], "reason": r[3],
                        "perks": r[4]} for r in junk],
    }
    save_json(os.path.join(HERE, "vault_report.json"), report)
    print("\nFull report saved to vault_report.json")

    if do_lock:
        _lock_keepers(token, mtype, keepers, prof)

def _char_for_item(iid, prof):
    """Find which character a vault item can be locked from (any works)."""
    chars = list(prof.get("characters", {}).get("data", {}).keys())
    return chars[0] if chars else None

def _lock_keepers(token, mtype, keepers, prof):
    char_id = None
    chars = list(prof.get("characters", {}).get("data", {}).keys())
    if chars:
        char_id = chars[0]
    if not char_id:
        die("No character found to issue lock command.")
    print("\nAbout to LOCK %d keeper items via the API." % len(keepers))
    if input("Type 'yes' to proceed: ").strip().lower() != "yes":
        print("Aborted. Nothing locked.")
        return
    ok = 0
    for name, loc, iid, reason, perks in keepers:
        body = {
            "state": True,
            "itemId": iid,
            "characterId": char_id,
            "membershipType": mtype,
        }
        try:
            api_post("/Destiny2/Actions/Items/SetLockState/", body, token)
            ok += 1
            print("  locked: %s" % name)
        except SystemExit:
            print("  FAILED to lock: %s" % name)
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
