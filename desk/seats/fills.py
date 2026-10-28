"""Seat 7: Order placer. Dry-run intents; PAPER orders only if paper keys; memes never executed."""
from .common import *
def run():
    sz = load("size") or {}; risk = load("risk") or {}
    if sz.get("refused"): return save("fills", {"mode": "REFUSED", "reason": sz["refused"], "intents": []})
    if risk.get("kill"): return save("fills", {"mode": "KILLED", "reason": risk["kill"], "intents": []})
    keys = alpaca_keys() and os.environ.get("DESK_PAPER_TRADE") == "1"
    mode = "PAPER" if keys else "DRY-RUN"
    intents, results = [], []
    m = sz.get("meme") or {}
    if m.get("pick"): intents.append({"venue": "FOMO", "side": "buy", "symbol": m["pick"], "usd": m.get("ticket_usd"), "status": "INTENT ONLY - FOMO not connected, never executed"})
    a = sz.get("alpaca") or {}
    held = {}
    if keys:
        for p in alpaca("GET", "/v2/positions"): held[p["symbol"]] = float(p["market_value"])
    eq = a.get("equity_usd")
    for sym, wt in (a.get("weights") or {}).items():
        it = {"venue": "alpaca-paper", "symbol": sym, "target_weight": wt}
        if eq:
            delta = round(wt * eq - held.get(sym.replace("/", ""), 0), 2)
            it.update(side="buy" if delta > 0 else "sell", notional=abs(delta))
            if keys and abs(delta) >= 1:
                r = alpaca("POST", "/v2/orders", {"symbol": sym, "notional": str(abs(delta)), "side": it["side"], "type": "market",
                                                  "time_in_force": "gtc" if "/" in sym else "day"})
                it["status"] = f"PAPER order {r.get('status') or r}"
            else: it["status"] = "DRY-RUN intent"
        else: it["status"] = "DRY-RUN intent (weight only; no equity known)"
        intents.append(it)
    return save("fills", {"mode": mode, "intents": intents, "note": "paper trading needs ALPACA_KEY+ALPACA_SECRET AND DESK_PAPER_TRADE=1; live endpoint is hard-refused"})
