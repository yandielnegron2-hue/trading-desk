"""Seat 1: Chief of staff - tool health + NO DIAL NO DESK."""
from .common import *
def run():
    t = {}
    try:
        if alpaca_keys():
            a = alpaca("GET", "/v2/account")
            t["alpaca_paper"] = "OK (ACTIVE)" if a.get("status") == "ACTIVE" else f"FAIL status={a.get('status') or a}"
        else: t["alpaca_paper"] = "NOT CONNECTED (no ALPACA_KEY/ALPACA_SECRET) - dry-run"
    except SystemExit as e: t["alpaca_paper"] = str(e)
    except Exception as e: t["alpaca_paper"] = f"FAIL {e}"
    try: get("https://api.geckoterminal.com/api/v2/networks?page=1", tries=1); t["geckoterminal"] = "OK"
    except Exception as e: t["geckoterminal"] = f"FAIL {e}"
    try: get("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&count=10&output=atom", ua=SEC_UA, tries=1); t["sec_edgar"] = "OK"
    except Exception as e: t["sec_edgar"] = f"FAIL {e}"
    fomo = os.environ.get("FOMO_FILTER_URL")
    if fomo:
        try: get(fomo, tries=1); t["fomo_filterTokens"] = "REACHABLE (read-only; execution still disabled)"
        except Exception as e: t["fomo_filterTokens"] = f"FAIL {e}"
    else: t["fomo_filterTokens"] = "NOT CONNECTED (no FOMO_FILTER_URL; no public filterTokens endpoint known)"
    t["quantgpt"] = "NOT CONNECTED" + (" (QUANTGPT_KEY set but no client implemented)" if os.environ.get("QUANTGPT_KEY") else "")
    t["jev"] = "NOT CONNECTED" + (" (JEV_KEY set but no client implemented)" if os.environ.get("JEV_KEY") else "")
    t["telegram"] = "OK" if os.environ.get("TELEGRAM_CHAT_ID") else "NOT CONNECTED (report printed + saved to file only)"
    d, why = dial()
    return save("chief", {"tools": t, "dial_ok": d is not None, "dial_note": why,
                          "dials": {k: v["dial"] for k, v in d["dials"].items()} if d else None})
