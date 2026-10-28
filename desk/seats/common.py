import json, os, time, subprocess, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state")
DIAL = "/workspace/risk-dial/latest.json"
NOW = dt.datetime.now(dt.timezone.utc)
TODAY = NOW.astimezone(dt.timezone(dt.timedelta(hours=-4))).date().isoformat()
UA = "Mozilla/5.0 (X11; Linux x86_64) Chrome/124"
SEC_UA = "YandielDesk research-bot desk-admin@example.org"
PAPER = "https://paper-api.alpaca.markets"  # hard-coded. Live endpoint is never used.
os.makedirs(STATE, exist_ok=True)

def get(url, ua=UA, headers=(), tries=3, timeout=30):
    err = ""
    for i in range(tries):
        h = sum((["-H", x] for x in headers), [])
        r = subprocess.run(["curl", "-sSfL", "--http1.1", "-m", str(timeout), "-A", ua, *h, url], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout: return r.stdout
        err = r.stderr.strip() or f"curl exit {r.returncode}"
        time.sleep(2 * (i + 1))
    raise RuntimeError(err[:200])

def alpaca_keys():
    k, s = os.environ.get("ALPACA_KEY"), os.environ.get("ALPACA_SECRET")
    base = os.environ.get("ALPACA_BASE_URL", PAPER)
    if base.rstrip("/") != PAPER:
        raise SystemExit("REFUSED: non-paper Alpaca endpoint configured. This desk only talks to paper-api.alpaca.markets.")
    return (k, s) if k and s else None

def alpaca(method, path, body=None):
    ks = alpaca_keys()
    if not ks: raise RuntimeError("no Alpaca paper keys")
    cmd = ["curl", "-sS", "-m", "20", "-X", method, "-H", f"APCA-API-KEY-ID: {ks[0]}", "-H", f"APCA-API-SECRET-KEY: {ks[1]}"]
    if body is not None: cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    r = subprocess.run(cmd + [PAPER + path], capture_output=True, text=True)
    return json.loads(r.stdout)

def save(name, obj):
    obj = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), **obj}
    json.dump(obj, open(os.path.join(STATE, f"{name}.json"), "w"), indent=1)
    with open(os.path.join(STATE, "log.jsonl"), "a") as f: f.write(json.dumps({"seat": name, **obj}) + "\n")
    return obj

def load(name):
    p = os.path.join(STATE, f"{name}.json")
    return json.load(open(p)) if os.path.exists(p) else None

def dial():
    """NO DIAL NO DESK: returns dial dict or None with reason."""
    if not os.path.exists(DIAL): return None, "latest.json missing"
    d = json.load(open(DIAL))
    age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(d["generated_utc"])).total_seconds() / 3600
    if age > 24: return None, f"dial is {age:.1f}h old (>24h)"
    return d, f"dial age {age:.1f}h"
