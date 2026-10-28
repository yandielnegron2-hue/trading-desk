"""Seat 4: Judge. PLACEHOLDER rules (Jev not connected). Picks at most one."""
from .common import *
def run():
    s = load("scan") or {}; c = s.get("handed_on") or []
    ok = [x for x in c if x["buyer_growth"] >= 1.5 and x["liquidity_usd"] >= 0.1 * x["mcap_usd"] and (x["h1_buys"] or 0) > (x["h1_sells"] or 0)]
    pick = max(ok, key=lambda x: x["buyer_growth"]) if ok else None
    return save("judge", {"engine": "PLACEHOLDER rule-based (Jev NOT CONNECTED)",
                          "rules": "buyer_growth>=1.5, liquidity>=10% of mcap, 1h buys>sells; best buyer_growth wins",
                          "considered": len(c), "pick": pick, "verdict": "YES" if pick else "NO (nothing passed)"})
