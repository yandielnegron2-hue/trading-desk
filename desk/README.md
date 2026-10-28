# Trading desk (gated by the risk dial)

`python3 desk.py all` runs: chief -> scan -> judge -> stocks -> runner -> size -> risk -> fills -> report.
Single seats: `desk.py <seat>`; `desk.py status` prints the seat table. State/logs: `state/` (`log.jsonl`, per-seat json, `report-YYYY-MM-DD.txt`).
Run `/workspace/risk-dial/dial.py` first. **NO DIAL NO DESK**: sizing/fills refuse if `latest.json` is missing or >24h old.

## Safety
- No real orders, ever. Alpaca URL is hard-coded to `paper-api.alpaca.markets`; any other `ALPACA_BASE_URL` makes the desk refuse.
- Default is dry-run. Paper orders need `ALPACA_KEY` + `ALPACA_SECRET` **and** `DESK_PAPER_TRADE=1`.
- Memecoins are never executed (FOMO not connected); intents are logged only.
- Missing data = null = hold (cash). Nothing is padded or invented.

## Seat status
| Seat | Status | Notes |
|---|---|---|
| chief | LIVE | tool health + dial freshness gate |
| dial | LIVE | FRED + CoinGecko + nasdaq.com (no keys) |
| scan | LIVE | GeckoTerminal new_pools solana+bsc, 8 calls/run spaced 6.5s; newest ~80 pools/chain only |
| judge | PLACEHOLDER | rule-based stand-in for Jev; picks at most one |
| stocks: insider buying | LIVE, provisional | SEC EDGAR Form 4 (>=3 insiders, code P, >$500k, 30d). Parses filings incrementally (EDGAR_BUDGET per run, default 400); list is NOT traded until coverage hits 100% |
| stocks: earnings drift | NULL | needs QuantGPT |
| runner/trend | LIVE signal, DRY-RUN | QQQ vs 200d, in >+1%, out <-3%; TQQQ else SHY; 35% |
| size | LIVE weights | $ amounts need Alpaca paper equity (memes need MEME_BANK_USD) |
| risk | LIVE rules | 4% day drawdown kill needs paper keys |
| fills | DRY-RUN | paper only, opt-in |
| report | LIVE (stdout/file) | Telegram not connected |

## What each account unlocks
- **Alpaca paper keys** (free): dollar sizing from paper equity, the 4% drawdown kill, real paper orders for TREND/STOCKS/CRYPTO when `DESK_PAPER_TRADE=1`.
- **QuantGPT** (~$49/mo): earnings-drift list, full stock screens, backtests (client not yet written).
- **Jev**: replaces the placeholder judge with real yes/no scoring.
- **FOMO**: filterTokens data (`FOMO_FILTER_URL`) and, later, meme execution (currently disabled by design).
- **Telegram** (bot token + chat id): push the daily report instead of file/stdout.
