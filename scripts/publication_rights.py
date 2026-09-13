"""Purpose-scoped publication checks. Migration is not a licence or an approval."""
from __future__ import annotations

import hashlib
import html
import ipaddress
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

import check_site
import macro_core

ROOT = Path(__file__).resolve().parents[1]
STATUSES = ('APPROVED', 'CONDITIONAL', 'UNKNOWN', 'PROHIBITED', 'EXPIRED', 'REVOKED')
USES = ('access', 'automated_retrieval', 'storage', 'transformation', 'display',
        'redistribution', 'commercial_use', 'caching', 'ai_processing')
PUBLIC_USES = ('storage', 'transformation', 'display', 'redistribution', 'caching')
DECISIONS = {'ALLOWED', 'DENIED', 'UNKNOWN'}
FIELDS = {'id', 'provider', 'dataset', 'source_url', 'terms_url', *USES,
          'attribution', 'retention', 'reviewed_at', 'evidence', 'status',
          'fields', 'public_targets', 'valid_from', 'valid_until', 'review_due_at',
          'conditions', 'monthly_cost_ceiling_jpy'}
TARGETS = {'index.html', 'data/market.json', 'data/macro.json',
           'data/macro-calendar.json', 'data/current-state.json',
           'reports/2026-09-11-carry-forward.md'}
BASELINE_COMMIT = '7460524c290b22c8c6f6b1c6bf64cbefeb95549f'
# A reviewed, finite migration list, never derived from a candidate registry.
BASELINE_SHA256 = '122da3319c0d22b21697a913758cc34a192c35f387067b5adb9758783d564e0b'


class RightsError(ValueError):
    """Only fixed error codes may cross the CI logging boundary."""


class PublicationBlocked(RightsError):
    def __init__(self, report):
        super().__init__('PUBLICATION_RIGHTS_BLOCKED')
        self.report = report


def require(ok, code='INVALID_REGISTRY'):
    if not ok:
        raise RightsError(code)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def identifier(value):
    return isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9-]{0,79}', value) is not None


def text(value, limit=500):
    require(isinstance(value, str) and 0 < len(value) <= limit)
    require(not any(ord(c) < 32 for c in value))
    try:
        check_site.scan(value)
    except ValueError:
        raise RightsError('UNSAFE_REGISTRY_METADATA') from None


def url(value):
    text(value)
    p = urlsplit(value)
    require(p.scheme == 'https' and p.hostname and not p.username and not p.password
            and not p.query and not p.fragment and p.port in (None, 443))
    require('.' in p.hostname and not p.hostname.endswith(('.local', '.internal')))
    try:
        ipaddress.ip_address(p.hostname)
    except ValueError:
        return
    raise RightsError('INVALID_REGISTRY')


def day(value):
    require(isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value))
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise RightsError('INVALID_REGISTRY') from None


def string_list(values, validator, empty=False):
    require(isinstance(values, list) and len(values) <= 100 and (empty or values))
    require(all(isinstance(v, str) for v in values))
    require(len(set(values)) == len(values))
    for v in values:
        validator(v)


def read_json(path):
    try:
        require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 500000,
                'REGISTRY_OR_BASELINE_MISSING')
        return check_site.loads(path.read_text(encoding='utf-8'))
    except RightsError:
        raise
    except (OSError, ValueError, TypeError, UnicodeError):
        raise RightsError('INVALID_REGISTRY') from None


def validate_registry(registry, today=None):
    today = today or date.today()
    require(isinstance(registry, dict) and set(registry) == {'schema_version', 'datasets'})
    require(type(registry['schema_version']) is int and registry['schema_version'] == 1)
    entries = registry['datasets']
    require(isinstance(entries, list) and 1 <= len(entries) <= 500)
    ids = set()
    for e in entries:
        require(isinstance(e, dict) and set(e) == FIELDS)
        require(identifier(e['id']) and e['id'] not in ids)
        ids.add(e['id'])
        text(e['provider']); text(e['dataset'])
        string_list(e['source_url'], url)
        string_list(e['terms_url'], url, empty=True)
        require(isinstance(e['status'], str) and e['status'] in STATUSES)
        require(all(isinstance(e[k], str) and e[k] in DECISIONS for k in USES))
        string_list(e['fields'], lambda v: require(identifier(v)))
        string_list(e['public_targets'], lambda v: require(v in TARGETS))
        require(e['attribution'] is None or isinstance(e['attribution'], str))
        if e['attribution'] is not None:
            text(e['attribution'])
        retention = e['retention']
        require(isinstance(retention, dict) and set(retention) == {'mode', 'max_age_days'})
        require(retention['mode'] in {'UNKNOWN', 'NONE', 'WHILE_VALID'})
        days = retention['max_age_days']
        require(days is None or (type(days) is int and 0 <= days <= 36500))
        for k in ('reviewed_at', 'valid_from', 'valid_until', 'review_due_at'):
            if e[k] is not None:
                day(e[k])
        require(e['reviewed_at'] is None or day(e['reviewed_at']) <= today)
        if e['valid_from'] and e['valid_until']:
            require(e['valid_from'] <= e['valid_until'])
        require(type(e['monthly_cost_ceiling_jpy']) is int and e['monthly_cost_ceiling_jpy'] == 0)
        require(isinstance(e['evidence'], list) and len(e['evidence']) <= 20)
        for ev in e['evidence']:
            require(isinstance(ev, dict) and set(ev) == {'reference', 'terms_sha256', 'approved_by_role'})
            require(identifier(ev['reference']) and ev['approved_by_role'] == 'product_owner')
            require(isinstance(ev['terms_sha256'], str) and re.fullmatch('[0-9a-f]{64}', ev['terms_sha256']))
        require(isinstance(e['conditions'], list) and len(e['conditions']) <= 10)
        for cond in e['conditions']:
            require(isinstance(cond, dict) and set(cond) == {'type', 'text', 'targets'})
            require(cond['type'] == 'attribution')
            text(cond['text'])
            string_list(cond['targets'], lambda v: require(v in e['public_targets']))
        if e['status'] in {'APPROVED', 'CONDITIONAL'}:
            require(e['reviewed_at'] and e['terms_url'] and e['evidence'] and e['valid_from']
                    and e['valid_until'] and e['review_due_at'], 'APPROVAL_EVIDENCE_REQUIRED')
            require(e['retention']['mode'] == 'WHILE_VALID', 'RETENTION_PERMISSION_REQUIRED')
            if e['status'] == 'CONDITIONAL':
                require(e['conditions'], 'CONDITIONS_REQUIRED')
    return {e['id']: e for e in entries}


def inventory(payload):
    """Inventory the validated final payload, not a caller's claimed list of IDs."""
    require(set(payload) == TARGETS, 'UNMAPPED_PUBLIC_FILE')
    market = check_site.loads(payload['data/market.json'])
    macro = check_site.loads(payload['data/macro.json'])
    cal = check_site.loads(payload['data/macro-calendar.json'])
    state = check_site.loads(payload['data/current-state.json'])
    items = []

    def add(ident, sources, fields, targets, content, oldest=None):
        require(identifier(ident), 'UNMAPPED_DATASET')
        items.append({'id': ident, 'source_url': sorted(sources), 'fields': sorted(fields),
                      'public_targets': sorted(targets), 'content_sha256': digest(content),
                      'oldest_date': oldest})

    for a in market['indices'] + market['assets']:
        fields = sorted({k for row in a['observations'] for k in row})
        add('market-' + a['symbol'].lower(), a['sources'], fields,
            ['index.html', 'data/market.json'], a, min(r['date'] for r in a['observations']))
    f = market['financials']
    add('financial-' + f['symbol'].lower(), [f['source']],
        sorted({k.replace('_', '-') for q in f['periods'] for k in q}),
        ['index.html', 'data/market.json'], f, min(q['end'] for q in f['periods']))
    revisions = macro['revisions']
    for s in macro['series']:
        ident = s['id']
        own_revisions = [r for r in revisions if r['series'] == ident]
        if s['observations'] or own_revisions:
            dates = [r[0] for r in s['observations']] + [r['date'] for r in own_revisions]
            add('macro-' + ident, [macro_core.META[ident][2]], ['date', 'value', 'revisions'],
                ['index.html', 'data/macro.json'], [s['observations'], own_revisions], min(dates))
        for aid, rows in s['auxiliary'].items():
            if rows:
                add('macro-' + ident + '-' + aid.replace('_', '-'), [macro_core.META[ident][2]],
                    ['date', 'value'], ['index.html', 'data/macro.json'], rows, min(r[0] for r in rows))
    require(all(r['series'] in {s['id'] for s in macro['series']} for r in revisions), 'UNMAPPED_REVISION')
    for family in sorted({e['family'] for e in cal['events']}):
        events = [e for e in cal['events'] if e['family'] == family]
        add('calendar-' + family, sorted({e['source'] for e in events}),
            sorted({k.replace('_', '-') for e in events for k in e}),
            ['index.html', 'data/macro-calendar.json'], events, min(e['date'] for e in events))
    add('research-state', [s['url'] for s in state['sources']], sorted(k.replace('_', '-') for k in state),
        ['index.html', 'data/current-state.json'], state)
    add('research-report', [s['url'] for s in state['sources']], ['text'],
        ['index.html', 'reports/2026-09-11-carry-forward.md'],
        payload['reports/2026-09-11-carry-forward.md'].decode().replace('\r\n', '\n'))
    require(len({i['id'] for i in items}) == len(items), 'DUPLICATE_PUBLIC_DATASET')
    return items


def scope_hash(item):
    return digest({k: item[k] for k in ('id', 'source_url', 'fields', 'public_targets')})


def shell_hash(payload):
    """Pin static HTML too: new HTML-only values must not bypass JSON inventory."""
    content = payload['index.html'].decode().replace('\r\n', '\n')
    for ident, name in [('macro-data', 'data/macro.json'), ('macro-calendar-data', 'data/macro-calendar.json')]:
        pattern = '<pre id="' + ident + '" hidden>(.*?)</pre>'
        matches = re.findall(pattern, content, re.S)
        require(len(matches) == 1 and check_site.loads(html.unescape(matches[0])) == check_site.loads(payload[name]),
                'UNMAPPED_HTML_CONTENT')
        content = re.sub(pattern, '<pre id="' + ident + '" hidden>RIGHTS_PAYLOAD</pre>', content, flags=re.S)
    macro = check_site.loads(payload['data/macro.json'])
    fallback = '<noscript><article><h2>Macro data / JavaScript disabled</h2><p>Static observations only. VIX withheld pending republication permission. Calendar and charts require JavaScript.</p><table><thead><tr><th>Series</th><th>Observation date</th><th>Raw value</th><th>Status</th></tr></thead><tbody>'
    for s in macro['series']:
        latest = s['observations'][-1] if s['observations'] else ['--', '--']
        fallback += '<tr>' + ''.join('<td>' + html.escape(str(v)) + '</td>' for v in [s['id'], *latest, s['status']]) + '</tr>'
    fallback += '</tbody></table></article></noscript>'
    require(content.count(fallback) == 1, 'UNMAPPED_HTML_CONTENT')
    return digest(content.replace(fallback, '<noscript>RIGHTS_FALLBACK</noscript>'))


def load_baseline(path=None):
    baseline = read_json(path or ROOT / 'data-rights/migration-baseline.json')
    require(digest(baseline) == BASELINE_SHA256, 'MIGRATION_BASELINE_CHANGED')
    return baseline


def assess(registry, items, baseline, payload, today=None):
    today = today or date.today()
    entries = validate_registry(registry, today)
    counts = {s: sum(e['status'] == s for e in entries.values()) for s in STATUSES}
    report = {'schema_version': 1, 'mode': 'migration-audit', 'registry_counts': counts,
              'published_dataset_count': len(items), 'migration_status': 'NOT_USED',
              'warnings': [], 'blocked': [], 'unpublished_count': len(set(entries) - {i['id'] for i in items})}
    if shell_hash(payload) != baseline['html_shell_sha256']:
        report['blocked'].append({'code': 'UNMAPPED_HTML_CONTENT'})
    for item in sorted(items, key=lambda i: i['id']):
        ident = item['id']; e = entries.get(ident)
        def block(code):
            report['blocked'].append({'id': ident, 'code': code})
        if e is None:
            block('MISSING_REGISTRY_ENTRY'); continue
        if sorted(e['source_url']) != item['source_url'] or not set(item['fields']) <= set(e['fields']) or not set(item['public_targets']) <= set(e['public_targets']):
            block('PUBLICATION_SCOPE_MISMATCH'); continue
        if e['status'] in {'PROHIBITED', 'EXPIRED', 'REVOKED'}:
            block(e['status']); continue
        if e['valid_until'] and today > day(e['valid_until']):
            block('EXPIRED'); continue
        if e['valid_from'] and today < day(e['valid_from']):
            block('NOT_YET_VALID'); continue
        if any(e[k] == 'DENIED' for k in PUBLIC_USES) or e['retention']['mode'] == 'NONE':
            block('PURPOSE_OR_RETENTION_DENIED'); continue
        max_age = e['retention']['max_age_days']
        if max_age is not None and (item['oldest_date'] is None or (today - day(item['oldest_date'])).days > max_age):
            block('RETENTION_LIMIT'); continue
        if e['status'] == 'UNKNOWN':
            old = baseline['datasets'].get(ident)
            if not old or old['scope_sha256'] != scope_hash(item):
                block('NEW_UNKNOWN'); continue
            if old['content_sha256'] is not None and old['content_sha256'] != item['content_sha256']:
                block('CHANGED_UNKNOWN_SNAPSHOT'); continue
            report['warnings'].append({'id': ident, 'code': 'EXISTING_UNKNOWN',
                                       'migration_status': 'PENDING_RIGHTS_REVIEW'})
            continue
        if any(e[k] != 'ALLOWED' for k in PUBLIC_USES):
            block('PURPOSE_PERMISSION_REQUIRED'); continue
        if today > day(e['review_due_at']):
            block('RIGHTS_REVIEW_OVERDUE'); continue
        conditions = list(e['conditions'])
        if e['attribution']:
            conditions.append({'type': 'attribution', 'text': e['attribution'], 'targets': item['public_targets']})
        if any(not all(cond['text'] in html.unescape(payload[target].decode()) for target in cond['targets']) for cond in conditions):
            block('CONDITION_UNSATISFIED')
    if report['warnings']:
        report['migration_status'] = 'PENDING_RIGHTS_REVIEW'
    report['result'] = 'BLOCKED' if report['blocked'] else ('MIGRATION_WARNING' if report['warnings'] else 'ALLOWED')
    return report


def enforce(payload):
    try:
        report = assess(read_json(ROOT / 'data-rights/registry.json'), inventory(payload),
                        load_baseline(), payload)
    except RightsError:
        raise
    except (KeyError, TypeError, ValueError, UnicodeError, OSError):
        raise RightsError('INVALID_RIGHTS_INPUT') from None
    if report['blocked']:
        raise PublicationBlocked(report)
    return report


def emit(report):
    # No providers, URLs, evidence bodies, values or error text are copied to CI.
    print('RIGHTS_REPORT ' + json.dumps(report, sort_keys=True, separators=(',', ':')))
    if report['warnings']:
        print('::warning::Existing UNKNOWN datasets remain in explicit rights migration; this is not rights approval.')
