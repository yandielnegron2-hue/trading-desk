"""Seat 9: Kill switch / risk. Runs before fills."""
from .common import *
def run():
    d, why = dial(); rules, kill, acct = [], None, None
    if not d: kill = f"NO DIAL NO DESK: {why}"
    else:
        dl = {k: v["dial"] for k, v in d["dials"].items()}
        rules.append(f"stocks: exit/trim to dial {dl['stocks']} (dial 0 = flatten all stock names)")
        rules.append(f"crypto: exit/trim to dial {dl['crypto']} x momentum targets (current target {d['momentum_12_1']['allocation']})")
        rules.append(f"memes: dial {dl['meme']}; exit any meme when 1h volume < 25% of its 24h hourly average (no meme positions held - FOMO not connected)")
    if alpaca_keys():
        try:
            a = alpaca("GET", "/v2/account"); eq, last = float(a["equity"]), float(a["last_equity"])
            dd = (eq - last) / last if last else 0; acct = {"equity": eq, "last_equity": last, "day_change_pct": round(dd * 100, 2)}
            if dd <= -0.04:
                kill = f"paper account down {dd:.1%} today (<= -4%)"
                if os.environ.get("DESK_PAPER_TRADE") == "1": alpaca("DELETE", "/v2/positions?cancel_orders=true")
        except Exception as e: acct = {"error": str(e)}
    else: acct = "no paper keys - drawdown kill inactive"
    return save("risk", {"kill": kill, "rules": rules, "account": acct, "rule_4pct": "paper account -4% day drawdown -> cancel orders, flatten, desk halts"})
