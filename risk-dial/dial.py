#!/usr/bin/env python3
"""Daily market risk dial from free public data (FRED + Yahoo/Stooq/CoinGecko). No API keys."""
import csv, io, json, math, datetime as dt, urllib.request, os
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
HERE = os.path.dirname(os.path.abspath(__file__))
NOW = dt.datetime.now(dt.timezone.utc)
LAG_H = {"WALCL": 8*24, "WTREGEN": 8*24, "RRPONTSYD": 4*24, "VIXCLS": 4*24, "BAMLH0A0HYM2": 4*24}
flags = []

def get(url, tries=4):
    import subprocess, time
    ua = [] if "stlouisfed" in url else ["-A", UA["User-Agent"]]
    err = ""
    for i in range(tries):
        r = subprocess.run(["curl", "-sSfL", "--http1.1", "-m", "30", *ua, url], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout: return r.stdout
        err = r.stderr.strip() or f"curl exit {r.returncode}"
        time.sleep(2 * (i + 1))
    raise RuntimeError(err)

def fred(sid):
    rows = list(csv.reader(io.StringIO(get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"))))[1:]
    data = [(dt.date.fromisoformat(d), float(v)) for d, v in rows if v not in (".", "")]
    last = data[-1][0]
    age = (NOW - dt.datetime(last.year, last.month, last.day, tzinfo=dt.timezone.utc)).total_seconds()/3600
    deg = age > LAG_H[sid]
    if deg: flags.append(f"{sid} DEGRADED (age {age:.0f}h > {LAG_H[sid]}h)")
    return {"data": data, "last_date": str(last), "age_hours": round(age, 1), "degraded": deg}

def prices(sym):
    """Returns list of (date, close) daily, oldest first."""
    errs = []
    try:
        try: j = json.loads(get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=2y&interval=1d"))["chart"]["result"][0]
        except Exception: j = json.loads(get(f"https://query2.finance.yahoo.com/v8/finance/chart/{sym}?range=2y&interval=1d"))["chart"]["result"][0]
        out = [(dt.datetime.fromtimestamp(t, dt.timezone.utc).date(), c) for t, c in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]) if c is not None]
        if len(out) > 250: return out, "yahoo"
    except Exception as e: errs.append(f"yahoo:{e}")
    try:
        s = {"BTC-USD": "btcusd", "ETH-USD": "ethusd", "SOL-USD": "solusd", "QQQ": "qqq.us"}[sym]
        rows = list(csv.DictReader(io.StringIO(get(f"https://stooq.com/q/d/l/?s={s}&i=d"))))
        out = [(dt.date.fromisoformat(r["Date"]), float(r["Close"])) for r in rows][-730:]
        if len(out) > 250: return out, "stooq"
    except Exception as e: errs.append(f"stooq:{e}")
    if sym == "QQQ":
        try:
            frm = (NOW.date() - dt.timedelta(days=500)).isoformat()
            j = json.loads(get(f"https://api.nasdaq.com/api/quote/QQQ/historical?assetclass=etf&fromdate={frm}&todate={NOW.date()}&limit=9999"))
            out = sorted((dt.datetime.strptime(r["date"], "%m/%d/%Y").date(), float(r["close"].replace("$", "").replace(",", ""))) for r in j["data"]["tradesTable"]["rows"])
            if len(out) > 250: return out, "nasdaq.com"
        except Exception as e: errs.append(f"nasdaq:{e}")
    cg = {"BTC-USD": "bitcoin", "ETH-USD": "ethereum", "SOL-USD": "solana"}.get(sym)
    if cg:
        try:
            j = json.loads(get(f"https://api.coingecko.com/api/v3/coins/{cg}/market_chart?vs_currency=usd&days=365&interval=daily"))
            out = [(dt.datetime.fromtimestamp(t/1000, dt.timezone.utc).date(), p) for t, p in j["prices"]]
            if len(out) > 200: return out, "coingecko"
        except Exception as e: errs.append(f"coingecko:{e}")
    raise RuntimeError("; ".join(errs) or "insufficient data")

def sma_test(sym, n):
    try:
        px, src = prices(sym)
        closes = [c for _, c in px]
        sma = sum(closes[-n:])/n
        return {"green": closes[-1] > sma, "close": round(closes[-1], 2), f"sma{n}": round(sma, 2), "as_of": str(px[-1][0]), "source": src}, px
    except Exception as e:
        flags.append(f"{sym} FETCH FAILED: {e}"); return {"green": False, "error": str(e)}, None

inputs, fr = {}, {}
for s in LAG_H:
    try: fr[s] = fred(s)
    except Exception as e: fr[s] = None; flags.append(f"{s} FETCH FAILED: {e}")
fred_meta = {s: ({k: v for k, v in m.items() if k != "data"} if m else {"error": "fetch failed"}) for s, m in fr.items()}

# 1. Net liquidity (billions), aligned to WALCL weekly dates
try:
    w, t, r = fr["WALCL"]["data"], dict(fr["WTREGEN"]["data"]), fr["RRPONTSYD"]["data"]
    def rrp_on(d):
        v = [x for dd, x in r if dd <= d]; return v[-1] if v else None
    nl = [(d, wv/1000 - t[d]/1000 - rrp_on(d)) for d, wv in w if d in t and rrp_on(d) is not None]
    chg = nl[-1][1] - nl[-5][1]
    deg = any(fr[s]["degraded"] for s in ("WALCL", "WTREGEN", "RRPONTSYD"))
    inputs["liquidity"] = {"green": chg > 0 and not deg, "net_liq_bn": round(nl[-1][1], 1), "chg_4w_bn": round(chg, 1), "as_of": str(nl[-1][0]), "degraded": deg}
except Exception as e:
    inputs["liquidity"] = {"green": False, "error": str(e)}; flags.append(f"liquidity FAILED: {e}")
# 2. VIX
try:
    v = fr["VIXCLS"]; last = v["data"][-1][1]
    inputs["volatility"] = {"green": last < 22 and not v["degraded"], "vix": last, "as_of": v["last_date"], "degraded": v["degraded"]}
except Exception as e:
    inputs["volatility"] = {"green": False, "error": str(e)}
# 3. Credit (4w change: last vs value on/before 28 days earlier)
try:
    c = fr["BAMLH0A0HYM2"]; d0, last = c["data"][-1]
    prior = [x for d, x in c["data"] if d <= d0 - dt.timedelta(days=28)][-1]
    inputs["credit"] = {"green": (last - prior) <= 0 and not c["degraded"], "hy_oas": last, "chg_4w": round(last - prior, 2), "as_of": str(d0), "degraded": c["degraded"]}
except Exception as e:
    inputs["credit"] = {"green": False, "error": str(e)}
inputs["btc"], btc_px = sma_test("BTC-USD", 200)
inputs["sol"], sol_px = sma_test("SOL-USD", 50)
inputs["nasdaq"], _ = sma_test("QQQ", 200)

def dial(keys):
    x = sum(inputs[k]["green"] for k in keys)/len(keys)
    x = math.floor(x*100)/100
    st = "STAND DOWN" if x < .5 else "HALF" if x < .75 else "THREE QUARTERS" if x < 1 else "FULL"
    return {"dial": x, "status": st, "inputs": keys}
dials = {"meme": dial(["liquidity", "volatility", "btc", "sol"]),
         "stocks": dial(["liquidity", "volatility", "credit", "nasdaq"]),
         "crypto": dial(["liquidity", "credit", "btc"])}

# 12-1 momentum
mom = {}
eth_px = None
try: eth_px, _ = prices("ETH-USD")
except Exception as e: flags.append(f"ETH-USD FETCH FAILED: {e}")
for name, px in (("BTC", btc_px), ("ETH", eth_px), ("SOL", sol_px)):
    if not px: mom[name] = None; continue
    end = px[-1][0]
    def on(days):
        tgt = end - dt.timedelta(days=days)
        d, c = min(px, key=lambda p: abs((p[0] - tgt).days))
        if abs((d - tgt).days) > 5: raise ValueError
        return c
    try: mom[name] = round(on(30)/on(365) - 1, 4)
    except Exception: mom[name] = None; flags.append(f"{name} momentum: insufficient history")
pos = sorted([(k, v) for k, v in mom.items() if v is not None and v > 0], key=lambda x: -x[1])[:2]
alloc = {k: round(1/len(pos), 4) for k, _ in pos} if pos else {"CASH": 1.0}

out = {"generated_utc": NOW.isoformat(timespec="seconds"), "inputs": inputs, "fred": fred_meta, "dials": dials,
       "momentum_12_1": {"returns": mom, "allocation": alloc}, "flags": flags}
json.dump(out, open(os.path.join(HERE, "latest.json"), "w"), indent=2)
open(os.path.join(HERE, "history.jsonl"), "a").write(json.dumps(out) + "\n")

G = lambda k: "GREEN" if inputs[k]["green"] else "RED"
L = [f"RISK DIAL  {out['generated_utc']}"]
li = inputs["liquidity"]; L.append(f"Liquidity  {G('liquidity')}  net {li.get('net_liq_bn')}bn, 4w chg {li.get('chg_4w_bn')}bn (as of {li.get('as_of')})")
vi = inputs["volatility"]; L.append(f"VIX        {G('volatility')}  {vi.get('vix')} (as of {vi.get('as_of')})")
cr = inputs["credit"]; L.append(f"Credit     {G('credit')}  HY OAS {cr.get('hy_oas')}, 4w chg {cr.get('chg_4w')} (as of {cr.get('as_of')})")
for k, n in (("btc", 200), ("sol", 50), ("nasdaq", 200)):
    i = inputs[k]; L.append(f"{k.upper():<10} {G(k)}  close {i.get('close')} vs SMA{n} {i.get(f'sma{n}')} ({i.get('source')}, {i.get('as_of')})")
L.append("FRED ages: " + ", ".join(f"{s} {m.get('age_hours')}h{' DEGRADED' if m.get('degraded') else ''}" for s, m in fred_meta.items()))
for k, d in dials.items(): L.append(f"Dial {k:<7} {d['dial']:.2f}  {d['status']}")
L.append("12-1 momentum: " + ", ".join(f"{k} {v:+.1%}" if v is not None else f"{k} n/a" for k, v in mom.items()) + f"  -> {alloc}")
L.append("Flags: " + ("; ".join(flags) if flags else "none"))
print("\n".join(L))
