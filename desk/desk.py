#!/usr/bin/env python3
"""Trading desk orchestrator, gated by /workspace/risk-dial. Usage: desk.py {chief|scan|judge|stocks|runner|size|risk|fills|report|status|all}"""
import sys, json
from seats import chief, scan, judge, stocks, runner, size, risk, fills, report
ORDER = ["chief", "scan", "judge", "stocks", "runner", "size", "risk", "fills", "report"]
MODS = dict(chief=chief, scan=scan, judge=judge, stocks=stocks, runner=runner, size=size, risk=risk, fills=fills, report=report)
STATUS = [("chief", "LIVE", "health checks + NO DIAL NO DESK"), ("dial", "LIVE", "/workspace/risk-dial (FRED, CoinGecko, nasdaq.com)"),
          ("scan", "LIVE", "GeckoTerminal new_pools solana+bsc"), ("judge", "PLACEHOLDER", "rule-based; Jev not connected"),
          ("stocks/insider", "LIVE (partial coverage, fills in daily)", "SEC EDGAR Form 4"), ("stocks/earnings drift", "NULL", "needs QuantGPT"),
          ("runner/trend", "LIVE signal, DRY-RUN orders", "QQQ 200d band -> TQQQ/SHY"), ("size", "LIVE (weights; $ need Alpaca equity)", "dial-gated"),
          ("risk", "LIVE rules; 4% kill needs paper keys", ""), ("fills", "DRY-RUN", "paper only with keys + DESK_PAPER_TRADE=1; memes never"),
          ("report", "LIVE (file/stdout)", "Telegram not connected")]
def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "status":
        for s in STATUS: print(f"{s[0]:<24}{s[1]:<40}{s[2]}")
        return
    for name in (ORDER if cmd == "all" else [cmd]):
        try: out = MODS[name].run()
        except SystemExit: raise
        except Exception as e: print(f"[{name}] ERROR {e}", file=sys.stderr); continue
        if name == "report": print(out)
        elif cmd != "all": print(json.dumps(out, indent=1)[:4000])
        else: print(f"[{name}] done", file=sys.stderr)
if __name__ == "__main__": main()
