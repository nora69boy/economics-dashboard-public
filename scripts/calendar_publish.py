"""Build a safe public calendar by merging complete official-source families only."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import calendar_probe
import calendar_snapshot
from macro_core import CAL_SOURCES, validate_calendar

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE = ROOT / '.calendar-probe.json'
FAMILIES = ('cpi', 'jobs', 'pce', 'fomc')
PERIOD_FAMILIES = {'cpi', 'jobs', 'pce'}
ALLOWED_RAW_SOURCES = {
    'cpi': {calendar_probe.BLS_ICS, calendar_probe.BLS_CPI},
    'jobs': {calendar_probe.BLS_ICS, calendar_probe.BLS_JOBS},
    'pce': {calendar_probe.BEA_SCHEDULE},
    'fomc': {calendar_probe.FED_FOMC},
}


def require(ok: bool, label: str) -> None:
    if not ok:
        raise ValueError(label)


def parse_checked_at(value: str) -> datetime:
    require(isinstance(value, str) and value.endswith('Z'), 'calendar state timestamp')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(dt.tzinfo is not None, 'calendar state timezone')
    return dt.astimezone(timezone.utc)


def load_state(path: Path = DEFAULT_STATE, now: datetime | None = None) -> dict | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding='utf-8'))
    required = {'calendar_probe_health', 'checked_at', 'publication', 'candidate_events', 'changes', 'errors', 'advisories', 'source_modes'}
    require(isinstance(data, dict) and set(data) == required, 'calendar state shape')
    checked = parse_checked_at(data['checked_at'])
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    require(checked <= now + timedelta(minutes=5), 'calendar state future')
    if now - checked > timedelta(hours=2):
        return None
    require(isinstance(data['candidate_events'], list), 'calendar candidates')
    require(isinstance(data['errors'], list) and isinstance(data['advisories'], list), 'calendar diagnostics')
    require(isinstance(data['source_modes'], dict), 'calendar source modes')
    return data


def normalize_candidate(event: dict) -> dict:
    require(isinstance(event, dict) and set(event) == {'family', 'date', 'period', 'time_local', 'time_jst', 'source'}, 'candidate shape')
    family = event['family']
    require(family in FAMILIES, 'candidate family')
    require(event['source'] in ALLOWED_RAW_SOURCES[family], 'candidate source')
    require(isinstance(event['date'], str), 'candidate date')
    if family in PERIOD_FAMILIES:
        require(isinstance(event['period'], str), 'candidate period')
        require(isinstance(event['time_local'], str) and isinstance(event['time_jst'], str), 'candidate time')
    else:
        require(event['period'] is None and event['time_local'] is None and event['time_jst'] is None, 'fomc candidate time')
    return {
        'id': family + '-' + event['date'],
        'family': family,
        'date': event['date'],
        'period': event['period'],
        'time_local': event['time_local'],
        'time_jst': event['time_jst'],
        'source': CAL_SOURCES[family],
        'status': 'verified_schedule',
    }


def complete_family(reviewed: list[dict], candidates: list[dict], family: str, cutoff: str) -> tuple[bool, list[dict]]:
    old_future = [e for e in reviewed if e['family'] == family and e['date'] >= cutoff]
    if not old_future:
        return False, []
    raw = [normalize_candidate(e) for e in candidates if e.get('family') == family]
    new_future = [e for e in raw if e['date'] >= cutoff]
    if family in PERIOD_FAMILIES:
        expected = [e['period'] for e in old_future]
        observed = [e['period'] for e in new_future]
        complete = len(observed) == len(set(observed)) and set(observed) == set(expected)
    else:
        complete = len(new_future) == len(old_future) and len({e['date'] for e in new_future}) == len(new_future)
    return complete, sorted(new_future, key=lambda e: (e['date'], e['id']))


def build(state_path: Path = DEFAULT_STATE, now: datetime | None = None) -> tuple[dict, dict]:
    reviewed = calendar_snapshot.build()
    state = load_state(state_path, now)
    report = {
        'mode': 'reviewed_static',
        'live_families': [],
        'retained_families': list(FAMILIES),
        'cutoff_jst': None,
    }
    if state is None:
        return reviewed, report

    checked = parse_checked_at(state['checked_at'])
    cutoff = checked.astimezone(ZoneInfo('Asia/Tokyo')).date().isoformat()
    final_events = []
    live = []
    retained = []
    for family in FAMILIES:
        complete, future = complete_family(reviewed['events'], state['candidate_events'], family, cutoff)
        if complete:
            final_events.extend(e for e in reviewed['events'] if e['family'] == family and e['date'] < cutoff)
            final_events.extend(future)
            live.append(family)
        else:
            final_events.extend(e for e in reviewed['events'] if e['family'] == family)
            retained.append(family)

    data = {
        'schema': 1,
        'checked_at': checked.date().isoformat() if live else reviewed['checked_at'],
        'events': sorted(final_events, key=lambda e: (e['date'], e['id'])),
    }
    validate_calendar(data, today=max(checked.date(), datetime.now(timezone.utc).date()))
    report = {
        'mode': 'family_merge' if live else 'reviewed_static',
        'live_families': live,
        'retained_families': retained,
        'cutoff_jst': cutoff,
    }
    return data, report
