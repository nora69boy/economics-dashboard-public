"""Bounded live diagnostics for official EIA WTI sources.

This probe has no publication side effects and never prints provider response bodies
or price values. It separates retrieval, parsing and continuity failures so the
WTI refresh can be repaired without weakening the retained-data safety boundary.
"""
from __future__ import annotations

import json
import urllib.error

from macro_core import WTI, WTI_RECENT, clean, parse_wti, parse_wti_recent, validate
from macro_fetch import PUBLIC, download


def _fetch_and_parse(label: str, url: str, parser) -> tuple[dict, dict | None]:
    row = {"source": label, "download": "failed", "parse": "not_attempted"}
    try:
        raw = download(url)
    except urllib.error.HTTPError as exc:
        row.update({"error_class": "HTTPError", "http_status": exc.code})
        return row, None
    except urllib.error.URLError:
        row.update({"error_class": "URLError"})
        return row, None
    except TimeoutError:
        row.update({"error_class": "TimeoutError"})
        return row, None
    except Exception as exc:
        row.update({"error_class": type(exc).__name__})
        return row, None
    row["download"] = "ok"
    try:
        parsed = parser(raw)
    except Exception as exc:
        row.update({"parse": "failed", "error_class": type(exc).__name__})
        return row, None
    dates = sorted(parsed)
    row.update({"parse": "ok", "points": len(dates), "latest_observation": dates[-1] if dates else None})
    return row, parsed


def probe(label: str, url: str, parser) -> dict:
    row, _ = _fetch_and_parse(label, url, parser)
    return row


def continuity_probe(parsed_history: dict | None) -> dict:
    """Compare date coverage only; never emit prices or provider response content."""
    row = {"continuity": "not_attempted"}
    if parsed_history is None:
        return row
    try:
        previous = json.loads(download(PUBLIC))
        validate(previous)
        prior = next(s for s in previous["series"] if s["id"] == "wti")
        prior_dates = {d for d, _ in prior["observations"]}
        source_rows = clean(parsed_history)
        source_dates = {d for d, _ in source_rows}
        missing = sorted(prior_dates - source_dates)
        added = sorted(source_dates - prior_dates)
        row.update({
            "continuity": "pass" if not missing else "fail",
            "previous_points": len(prior_dates),
            "source_points_since_2015": len(source_dates),
            "missing_count": len(missing),
            "missing_first": missing[0] if missing else None,
            "missing_last": missing[-1] if missing else None,
            "new_count": len(added),
            "new_first": added[0] if added else None,
            "new_last": added[-1] if added else None,
            "previous_latest": max(prior_dates) if prior_dates else None,
            "source_latest": max(source_dates) if source_dates else None,
        })
    except urllib.error.HTTPError as exc:
        row.update({"continuity": "unavailable", "error_class": "HTTPError", "http_status": exc.code})
    except urllib.error.URLError:
        row.update({"continuity": "unavailable", "error_class": "URLError"})
    except TimeoutError:
        row.update({"continuity": "unavailable", "error_class": "TimeoutError"})
    except Exception as exc:
        row.update({"continuity": "unavailable", "error_class": type(exc).__name__})
    return row


def main() -> None:
    history_row, history = _fetch_and_parse("eia_history_html", WTI, parse_wti)
    recent_row, _ = _fetch_and_parse("eia_recent_html", WTI_RECENT, parse_wti_recent)
    rows = [history_row, recent_row]
    health = "usable" if any(r["download"] == "ok" and r["parse"] == "ok" for r in rows) else "blocked"
    print(json.dumps({
        "wti_probe_health": health,
        "sources": rows,
        "history_continuity": continuity_probe(history),
    }, separators=(",", ":")))


if __name__ == "__main__":
    main()
