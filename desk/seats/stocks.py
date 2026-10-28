"""Seat 5: Stock lists. Insider cluster buys from SEC EDGAR Form 4 (incremental cache). Earnings drift = null (needs QuantGPT)."""
import re
from .common import *
CACHE = os.path.join(STATE, "form4_cache.json")
BUDGET = int(os.environ.get("EDGAR_BUDGET", "400"))  # Form 4 filings parsed per run (SEC limit 10 req/s; we do ~7/s)
def tag(x, t):
    m = re.search(rf"<{t}>\s*(?:<value>)?\s*([^<]*)", x); return m.group(1).strip() if m else None
def parse(txt):
    sym = tag(txt, "issuerTradingSymbol"); own = tag(txt, "rptOwnerName"); buys = 0.0
    for b in re.findall(r"<nonDerivativeTransaction>(.*?)</nonDerivativeTransaction>", txt, re.S):
        if tag(b, "transactionCode") == "P" and tag(b, "transactionAcquiredDisposedCode") == "A":
            try: buys += float(tag(b, "transactionShares")) * float(tag(b, "transactionPricePerShare"))
            except (TypeError, ValueError): pass
    return {"sym": (sym or "").upper(), "owner": own, "p_usd": round(buys, 2)}
def run():
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {"filings": {}, "days": {}}
    days, d, errs = [], NOW.date(), []
    while len(days) < 30: days.append(d); d -= dt.timedelta(days=1)
    todo = []
    for day in days:  # newest first
        if day.weekday() >= 5: continue
        k = day.isoformat()
        if k not in cache["days"]:
            q = (day.month - 1) // 3 + 1
            try:
                idx = get(f"https://www.sec.gov/Archives/edgar/daily-index/{day.year}/QTR{q}/form.{day:%Y%m%d}.idx", ua=SEC_UA, tries=1)
                cache["days"][k] = [l.split()[-1] for l in idx.splitlines() if l.startswith("4 ")]
            except Exception as e:
                if day < NOW.date(): errs.append(f"index {k}: {e}")
                continue
            time.sleep(0.15)
        todo += [(k, p) for p in cache["days"][k] if p not in cache["filings"]]
    done = 0
    for k, p in todo[:BUDGET]:
        try: cache["filings"][p] = {"day": k, **parse(get("https://www.sec.gov/Archives/" + p, ua=SEC_UA, tries=2))}
        except Exception as e: errs.append(f"{p}: {e}"); continue
        done += 1; time.sleep(0.12)
    cutoff = days[-1].isoformat()
    cache["days"] = {k: v for k, v in cache["days"].items() if k >= cutoff}
    live = set(p for v in cache["days"].values() for p in v)
    cache["filings"] = {p: v for p, v in cache["filings"].items() if p in live}
    json.dump(cache, open(CACHE, "w"))
    agg = {}
    for v in cache["filings"].values():
        if v["p_usd"] > 0 and v["sym"] and v["sym"] not in ("NONE", "N/A"):
            a = agg.setdefault(v["sym"], {"insiders": set(), "usd": 0.0}); a["insiders"].add(v["owner"]); a["usd"] += v["p_usd"]
    hits = sorted(({"symbol": s, "insiders": len(a["insiders"]), "open_market_buys_usd": round(a["usd"])} for s, a in agg.items()
                   if len(a["insiders"]) >= 3 and a["usd"] > 500000), key=lambda x: -x["open_market_buys_usd"])
    total = len(live); cov = len(cache["filings"]) / total if total else 0
    return save("stocks", {"insider_buying": {"source": "SEC EDGAR Form 4 (daily index + raw filings)", "rule": ">=3 distinct insiders, code P, >$500k, last 30 days",
                           "coverage": f"{len(cache['filings'])}/{total} Form 4 filings parsed ({cov:.0%}); +{done} this run; fills in over successive runs",
                           "complete": cov >= 0.999, "list": hits[:16]},
                           "earnings_drift": {"list": None, "reason": "needs QuantGPT"}, "errors": errs[:10]})
