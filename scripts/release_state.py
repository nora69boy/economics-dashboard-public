#!/usr/bin/env python3
"""Typed operational release-state contract for the v0.7 dashboard migration.

This module intentionally contains no network access and no wall-clock reads.  A
caller must provide every timestamp and status explicitly so the resulting state
is deterministic and auditable.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.7-draft1"
VERSION_RE = re.compile(r"^v?\d+\.\d+\.\d+$")

CHANNELS = {"public", "private", "preview"}
DELIVERY_MODES = {"provider_hosted", "self_hosted", "reviewed_static", "unavailable"}
OBSERVATION_STATUSES = {"not_observed_by_build", "available", "degraded", "blocked", "unknown"}
FRESHNESS_STATUSES = {"fresh", "stale", "retained", "unknown"}
PUBLIC_PRESENCE = {"published", "not_published"}
VISIBILITY = {"visible", "hidden", "not_applicable"}
MODULE_STATUSES = {"available", "degraded", "blocked", "reviewed_static", "unavailable"}
CALENDAR_HEALTH = {"fresh", "partial_access_blocked", "source_access_blocked", "degraded", "reviewed_static", "unknown"}


class ReleaseStateError(ValueError):
    """Raised when a release-state document violates the v0.7 contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseStateError(message)


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    _require(isinstance(value, dict), f"{label} must be an object")
    actual = set(value)
    _require(actual == expected, f"{label} keys must be {sorted(expected)}; got {sorted(actual)}")


def _timestamp(value: Any, label: str, *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    _require(isinstance(value, str) and value, f"{label} must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReleaseStateError(f"{label} must be ISO-8601") from exc
    _require(parsed.tzinfo is not None and parsed.utcoffset() is not None, f"{label} must include a timezone")


def validate(state: dict[str, Any]) -> dict[str, Any]:
    """Validate and return *state* without mutating it."""
    _exact_keys(
        state,
        {"schema_version", "release", "market", "macro", "calendar", "event", "modules", "publication"},
        "release_state",
    )
    _require(state["schema_version"] == SCHEMA_VERSION, "unsupported schema_version")

    release = state["release"]
    _exact_keys(release, {"version", "channel", "verified_at", "build_run_id"}, "release")
    _require(isinstance(release["version"], str) and VERSION_RE.match(release["version"]), "release.version must be semantic")
    _require(release["channel"] in CHANNELS, "invalid release.channel")
    _timestamp(release["verified_at"], "release.verified_at", nullable=True)
    _require(release["build_run_id"] is None or str(release["build_run_id"]).isdigit(), "release.build_run_id must be numeric or null")

    market = state["market"]
    _exact_keys(
        market,
        {"delivery_mode", "quote_observation", "data_persisted", "snapshot_as_of", "freshness"},
        "market",
    )
    _require(market["delivery_mode"] in DELIVERY_MODES, "invalid market.delivery_mode")
    _require(market["quote_observation"] in OBSERVATION_STATUSES, "invalid market.quote_observation")
    _require(isinstance(market["data_persisted"], bool), "market.data_persisted must be boolean")
    _require(market["snapshot_as_of"] is None or isinstance(market["snapshot_as_of"], str), "market.snapshot_as_of must be string or null")
    _require(market["freshness"] in FRESHNESS_STATUSES, "invalid market.freshness")
    if market["delivery_mode"] == "provider_hosted":
        _require(market["data_persisted"] is False, "provider-hosted quotes must not be marked persisted")
        _require(
            market["quote_observation"] in {"not_observed_by_build", "available", "degraded", "blocked", "unknown"},
            "invalid provider-hosted quote observation",
        )

    macro = state["macro"]
    _exact_keys(macro, {"attempted_at", "available_count", "total_count", "freshness"}, "macro")
    _timestamp(macro["attempted_at"], "macro.attempted_at", nullable=True)
    for key in ("available_count", "total_count"):
        _require(isinstance(macro[key], int) and not isinstance(macro[key], bool) and macro[key] >= 0, f"macro.{key} must be a non-negative integer")
    _require(macro["available_count"] <= macro["total_count"], "macro.available_count cannot exceed total_count")
    _require(macro["freshness"] in FRESHNESS_STATUSES, "invalid macro.freshness")

    calendar = state["calendar"]
    _exact_keys(calendar, {"source_health", "mode", "verified_at"}, "calendar")
    _require(calendar["source_health"] in CALENDAR_HEALTH, "invalid calendar.source_health")
    _require(isinstance(calendar["mode"], str) and calendar["mode"], "calendar.mode must be a non-empty string")
    _timestamp(calendar["verified_at"], "calendar.verified_at", nullable=True)

    event = state["event"]
    _exact_keys(event, {"active_event_ids", "phase", "phase_verified_at"}, "event")
    _require(isinstance(event["active_event_ids"], list), "event.active_event_ids must be a list")
    _require(len(event["active_event_ids"]) == len(set(event["active_event_ids"])), "event.active_event_ids must be unique")
    _require(all(isinstance(x, str) and x for x in event["active_event_ids"]), "event ids must be non-empty strings")
    _require(isinstance(event["phase"], str) and event["phase"], "event.phase must be a non-empty string")
    _timestamp(event["phase_verified_at"], "event.phase_verified_at", nullable=True)

    modules = state["modules"]
    _require(isinstance(modules, dict) and modules, "modules must be a non-empty object")
    for module_id, status in modules.items():
        _require(isinstance(module_id, str) and module_id, "module ids must be non-empty strings")
        _require(status in MODULE_STATUSES, f"invalid module status for {module_id}")

    publication = state["publication"]
    _exact_keys(publication, {"legacy_market_public_presence", "legacy_market_visibility", "use_legacy_market_for_current_decisions"}, "publication")
    _require(publication["legacy_market_public_presence"] in PUBLIC_PRESENCE, "invalid legacy public presence")
    _require(publication["legacy_market_visibility"] in VISIBILITY, "invalid legacy visibility")
    _require(isinstance(publication["use_legacy_market_for_current_decisions"], bool), "legacy decision flag must be boolean")
    if publication["legacy_market_public_presence"] == "not_published":
        _require(publication["legacy_market_visibility"] != "visible", "not-published content cannot be visible")
    if publication["use_legacy_market_for_current_decisions"]:
        _require(publication["legacy_market_visibility"] == "visible", "decision data must be visibly disclosed")

    return state


def dumps(state: dict[str, Any]) -> str:
    """Return canonical UTF-8 JSON after validation."""
    validate(state)
    return json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load(path: Path) -> dict[str, Any]:
    state = json.loads(path.read_text())
    return validate(state)
