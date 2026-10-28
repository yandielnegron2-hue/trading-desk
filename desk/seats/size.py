"""Seat 6: Position sizer. Refuses without a fresh dial (NO DIAL NO DESK)."""
from .common import *
def fnum(k):
    v = os.environ.get(k)
    try: return float(v) if v else None
    except ValueError: return None
def run():
    d, why = dial()
    if not d: return save("size", {"refused": f"NO DIAL NO DESK: {why}", "meme": None, "alpaca": None})
    dl = {k: v["dial"] for k, v in d["dials"].items()}
    # --- memes
    bank, pick = fnum("MEME_BANK_USD"), (load("judge") or {}).get("pick")
    frac = min(0.06, 0.06) * dl["meme"]  # kelly-ish clamp: 6% of bank, scaled by dial
    meme = {"ticket_pct_of_bank": round(frac * 100, 2), "bank_usd": bank, "pick": pick["name"] if pick else None, "ticket_usd": None}
    if pick and bank:
        t = min(bank * frac, 0.02 * pick["liquidity_usd"]); fee = max(0.0045 * t, 0.95)
        meme["ticket_usd"] = 0 if 0.0045 * t < 0.95 else round(t, 2)  # $0.95 min fee would exceed 0.45% -> skip
        meme["fee_note"] = f"fee floor 0.45% min $0.95 -> est fee ${fee:.2f}" + ("; ticket too small, zeroed" if meme["ticket_usd"] == 0 else "")
    elif not bank: meme["note"] = "MEME_BANK_USD not set (FOMO not connected) - % only"
    # --- alpaca
    eq, src = None, "unknown (no Alpaca paper keys) - weights only"
    if alpaca_keys():
        try: eq = float(alpaca("GET", "/v2/account")["equity"]); src = "Alpaca paper equity"
        except Exception as e: src = f"Alpaca error {e}"
    run_ = load("runner") or {}; st = load("stocks") or {}
    w = {}
    if run_.get("target"): w[run_["target"]] = 0.35
    ib = st.get("insider_buying") or {}
    names = [x["symbol"] for x in ib.get("list") or []] if ib.get("complete") else []  # partial EDGAR coverage = not trusted = hold
    names += [x["symbol"] for x in (st.get("earnings_drift") or {}).get("list") or []]
    names = list(dict.fromkeys(names))[:16]
    stock_budget = 0.50 * dl["stocks"]
    for s in names: w[s] = w.get(s, 0) + stock_budget / len(names)
    alloc = d["momentum_12_1"]["allocation"]
    cmap = {"BTC": "BTC/USD", "ETH": "ETH/USD", "SOL": "SOL/USD"}
    for k, v in alloc.items():
        if k in cmap and v > 0: w[cmap[k]] = 0.15 * dl["crypto"] * v
    w = {k: round(v, 4) for k, v in w.items() if v > 0}
    cash = round(1 - sum(w.values()), 4)
    unused = []
    if not names: unused.append(f"STOCKS sleeve {stock_budget:.1%} -> cash (no trusted list: insider screen " + ("complete but empty" if ib.get("complete") else "coverage incomplete") + ", earnings drift null; null = hold)")
    if not any(k in cmap for k in alloc if alloc[k] > 0): unused.append(f"CRYPTO sleeve {0.15*dl['crypto']:.1%} -> cash (momentum target 100% cash)")
    if not run_.get("target"): unused.append("TREND 35% -> cash (runner had no data)")
    return save("size", {"dials": dl, "dial_note": why, "meme": meme,
                         "alpaca": {"equity_usd": eq, "equity_source": src, "weights": w, "cash": cash, "notes": unused,
                                    "dollars": {k: round(v * eq, 2) for k, v in w.items()} if eq else None}})
