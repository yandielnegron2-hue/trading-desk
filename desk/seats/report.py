"""Seat 10: End-of-day plain-text desk report from state files."""
from .common import *
def run():
    c, s, j, st, sz, r, f, ru = (load(x) or {} for x in ("chief", "scan", "judge", "stocks", "size", "risk", "fills", "runner"))
    L = [f"DESK REPORT {TODAY} (all times from logs; dry-run desk, no real money)", "=" * 60]
    L.append("DIAL: " + (", ".join(f"{k} {v}" for k, v in (c.get("dials") or {}).items()) or "MISSING") + f"  [{c.get('dial_note')}]")
    L.append("TOOLS: " + "; ".join(f"{k}={v}" for k, v in (c.get("tools") or {}).items()))
    L.append(f"SCAN: {s.get('pools_seen')} new pools seen ({s.get('api_calls')} GeckoTerminal calls), {len(s.get('candidates') or [])} passed filters, {len(s.get('handed_on') or [])} handed on. {s.get('note','')}")
    for x in (s.get("candidates") or []): L.append(f"   - {x['name']} [{x['network']}] age {x['age_h']}h liq ${x['liquidity_usd']:,} vol24 ${x['vol24_usd']:,} mcap ${x['mcap_usd']:,} buyer growth {x['buyer_growth']}x")
    if s.get("errors"): L.append(f"   scan errors: {s['errors']}")
    L.append(f"JUDGE ({j.get('engine')}): {j.get('verdict')}" + (f" -> {j['pick']['name']}" if j.get("pick") else ""))
    ib = st.get("insider_buying") or {}
    L.append(f"STOCKS insider buying: {[x['symbol'] for x in ib.get('list') or []] or 'none qualifying'} | {ib.get('coverage')}" + ("" if ib.get('complete') else " -> PROVISIONAL, not traded until coverage 100%"))
    L.append(f"STOCKS earnings drift: null ({(st.get('earnings_drift') or {}).get('reason')}) -> hold")
    L.append(f"TREND: QQQ {ru.get('qqq_close')} ({ru.get('as_of')}) vs 200d {ru.get('sma200')} [in>{ru.get('enter_above')} out<{ru.get('exit_below')}] -> {ru.get('regime')} => {ru.get('target')} ({ru.get('reason') or ru.get('error')})")
    if sz.get("refused"): L.append("SIZE: " + sz["refused"])
    else:
        m, a = sz.get("meme") or {}, sz.get("alpaca") or {}
        L.append(f"SIZE memes: {m.get('ticket_pct_of_bank')}% of meme bank per ticket; pick={m.get('pick')}; ticket ${m.get('ticket_usd')} {m.get('note') or m.get('fee_note') or ''}")
        L.append(f"SIZE alpaca: weights {a.get('weights')} cash {a.get('cash')} | equity: {a.get('equity_source')}")
        for n in a.get("notes") or []: L.append("   - " + n)
    L.append(f"RISK: kill={'NONE' if not r.get('kill') else r['kill']} | account: {r.get('account')}")
    for x in r.get("rules") or []: L.append("   - " + x)
    L.append(f"FILLS ({f.get('mode')}):")
    for i in f.get("intents") or []: L.append(f"   - {i}")
    if not f.get("intents"): L.append("   - none")
    txt = "\n".join(L)
    open(os.path.join(STATE, f"report-{TODAY}.txt"), "w").write(txt)
    save("report", {"text": txt})
    return txt
