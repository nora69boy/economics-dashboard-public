"""Bounded live diagnostics for official EIA WTI sources.

This probe has no publication side effects and never prints provider response bodies.
It distinguishes network/HTTP retrieval failures from parser failures so source
resilience can be fixed without weakening the retained-data safety boundary.
"""
from __future__ import annotations

import json
import urllib.error

from macro_core import WTI, WTI_RECENT, parse_wti, parse_wti_recent
from macro_fetch import download


def probe(label: str, url: str, parser) -> dict:
    row = {"source": label, "download": "failed", "parse": "not_attempted"}
    try:
        raw = download(url)
    except urllib.error.HTTPError as exc:
        row.update({"error_class": "HTTPError", "http_status": exc.code})
        return row
    except urllib.error.URLError:
        row.update({"error_class": "URLError"})
        return row
    except TimeoutError:
        row.update({"error_class": "TimeoutError"})
        return row
    except Exception as exc:
        row.update({"error_class": type(exc).__name__})
        return row
    row["download"] = "ok"
    try:
        parsed = parser(raw)
    except Exception as exc:
        row.update({"parse": "failed", "error_class": type(exc).__name__})
        return row
    dates = sorted(parsed)
    row.update({"parse": "ok", "points": len(dates), "latest_observation": dates[-1] if dates else None})
    return row


def main() -> None:
    rows = [
        probe("eia_history_html", WTI, parse_wti),
        probe("eia_recent_html", WTI_RECENT, parse_wti_recent),
    ]
    health = "usable" if any(r["download"] == "ok" and r["parse"] == "ok" for r in rows) else "blocked"
    print(json.dumps({"wti_probe_health": health, "sources": rows}, separators=(",", ":")))


if __name__ == "__main__":
    main()
