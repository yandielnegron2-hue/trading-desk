"""Seat 3: Memecoin scanner on GeckoTerminal new_pools (free, <=10 calls/min)."""
from .common import *
NETS, PAGES, GAP = ("solana", "bsc"), 4, 6.5
def f(x):
    try: return float(x)
    except (TypeError, ValueError): return None
def run():
    d, _ = dial(); md = d["dials"]["meme"]["dial"] if d else None
    pools, errs, calls = [], [], 0
    for net in NETS:
        for p in range(1, PAGES + 1):
            if calls: time.sleep(GAP)
            calls += 1
            try: pools += [(net, x) for x in json.loads(get(f"https://api.geckoterminal.com/api/v2/networks/{net}/new_pools?page={p}", tries=2))["data"]]
            except Exception as e: errs.append(f"{net} p{p}: {e}")
    out, oldest = [], {}
    for net, x in pools:
        a = x["attributes"]
        age_h = (NOW - dt.datetime.fromisoformat(a["pool_created_at"].replace("Z", "+00:00"))).total_seconds() / 3600
        oldest[net] = max(oldest.get(net, 0), age_h)
        liq, vol = f(a.get("reserve_in_usd")), f((a.get("volume_usd") or {}).get("h24"))
        mc = f(a.get("market_cap_usd")); mc_src = "market_cap"
        if mc is None: mc, mc_src = f(a.get("fdv_usd")), "fdv (mcap null)"
        tx = a.get("transactions") or {}
        if not (0.25 <= age_h <= 72) or liq is None or liq <= 12000 or vol is None or vol <= 40000 or mc is None or not (60000 <= mc <= 8e6): continue
        if all(tx.get(w, {}).get("sells", 0) > tx.get(w, {}).get("buys", 0) for w in ("m5", "m15")): continue
        h1, h6 = tx.get("h1", {}), tx.get("h6", {})
        # growth = last-hour buyers vs avg hourly buyers over 6h (and same for txns)
        bg = (h1.get("buyers", 0) / max(h6.get("buyers", 0) / 6, 1e-9)) if h6.get("buyers") else 0
        tg = ((h1.get("buys", 0) + h1.get("sells", 0)) / max((h6.get("buys", 0) + h6.get("sells", 0)) / 6, 1e-9)) if h6 else 0
        out.append({"network": net, "pool": a["address"], "name": a["name"], "dex": x["relationships"]["dex"]["data"]["id"],
                    "age_h": round(age_h, 2), "liquidity_usd": round(liq), "vol24_usd": round(vol), "mcap_usd": round(mc), "mcap_source": mc_src,
                    "h1_buys": h1.get("buys"), "h1_sells": h1.get("sells"), "buyer_growth": round(bg, 2), "txn_growth": round(tg, 2),
                    "url": f"https://www.geckoterminal.com/{net}/pools/{a['address']}"})
    out.sort(key=lambda c: (c["buyer_growth"], c["txn_growth"]), reverse=True); out = out[:10]
    gated = md is None or md < 0.5
    return save("scan", {"meme_dial": md, "api_calls": calls, "pools_seen": len(pools), "oldest_pool_age_h": {k: round(v, 1) for k, v in oldest.items()},
                         "errors": errs, "candidates": out, "handed_on": [] if gated else out,
                         "note": ("meme dial <0.5 or missing: logged only, nothing handed on" if gated else "handed to judge") +
                                 "; coverage limited to the newest ~80 pools per chain (GeckoTerminal new_pools pages 1-4)"})
