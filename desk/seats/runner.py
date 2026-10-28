"""Seat 8: Runner/trend. QQQ vs 200-day, enter > +1%, exit < -3%. Long TQQQ when IN, else SHY. Dry-run unless paper keys."""
from .common import *
def qqq():
    frm = (NOW.date() - dt.timedelta(days=500)).isoformat()
    j = json.loads(get(f"https://api.nasdaq.com/api/quote/QQQ/historical?assetclass=etf&fromdate={frm}&todate={NOW.date()}&limit=9999"))
    return sorted((dt.datetime.strptime(r["date"], "%m/%d/%Y").date().isoformat(), float(r["close"].replace("$", "").replace(",", ""))) for r in j["data"]["tradesTable"]["rows"])
def run():
    prev = (load("runner") or {}).get("regime")
    try: px = qqq()
    except Exception as e: return save("runner", {"regime": prev, "error": f"QQQ data unavailable: {e}", "target": None})
    close, asof = px[-1][1], px[-1][0]; sma = sum(c for _, c in px[-200:]) / 200
    up, dn = sma * 1.01, sma * 0.97
    if close > up: reg = "IN"
    elif close < dn: reg = "OUT"
    else: reg = prev or "OUT"
    why = "above +1% band" if close > up else "below -3% band" if close < dn else f"inside band, holding prior regime ({prev or 'none -> default OUT'})"
    return save("runner", {"qqq_close": close, "as_of": asof, "sma200": round(sma, 2), "enter_above": round(up, 2), "exit_below": round(dn, 2),
                           "regime": reg, "reason": why, "target": "TQQQ" if reg == "IN" else "SHY"})
