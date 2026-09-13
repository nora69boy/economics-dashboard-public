"""Apply explicit calendar rights decisions without broadening any other dataset."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import check_site
import publication_rights as rights

ROOT = Path(__file__).resolve().parents[1]
APPROVALS = ROOT / 'data-rights/calendar-approvals.json'
EXPECTED_IDS = {'calendar-cpi', 'calendar-jobs', 'calendar-pce', 'calendar-fomc'}
PUBLIC_USES = ('storage', 'transformation', 'display', 'redistribution', 'caching')


def load_approvals(path: Path | None = None):
    path = path or APPROVALS
    raw = path.read_text(encoding='utf-8')
    check_site.scan(raw)
    data = check_site.loads(raw)
    rights.require(isinstance(data, dict) and set(data) == {'schema_version', 'approved_at', 'valid_until', 'review_due_at', 'datasets'})
    rights.require(data['schema_version'] == 1)
    approved_at = rights.day(data['approved_at']);valid_until = rights.day(data['valid_until']);review_due_at = rights.day(data['review_due_at'])
    rights.require(approved_at <= review_due_at <= valid_until)
    rights.require(isinstance(data['datasets'], list) and len(data['datasets']) == 4)
    seen = set()
    for item in data['datasets']:
        rights.require(isinstance(item, dict) and set(item) == {'id', 'terms_url', 'reference', 'evidence_text', 'attribution_text'})
        rights.require(rights.identifier(item['id']) and item['id'] not in seen);seen.add(item['id']);rights.url(item['terms_url']);rights.text(item['reference']);rights.text(item['evidence_text']);rights.url(item['attribution_text'])
    rights.require(seen == EXPECTED_IDS)
    return data


def effective_registry(base=None, approvals=None):
    base = copy.deepcopy(base or rights.read_json(ROOT / 'data-rights/registry.json'));approvals = approvals or load_approvals();entries = {entry['id']: entry for entry in base['datasets']};rights.require(EXPECTED_IDS <= set(entries))
    for decision in approvals['datasets']:
        entry = entries[decision['id']]
        entry.update({'terms_url':[decision['terms_url']],'access':'ALLOWED','automated_retrieval':'ALLOWED','storage':'ALLOWED','transformation':'ALLOWED','display':'ALLOWED','redistribution':'ALLOWED','commercial_use':'UNKNOWN','caching':'ALLOWED','ai_processing':'UNKNOWN','attribution':None,'retention':{'mode':'WHILE_VALID','max_age_days':None},'reviewed_at':approvals['approved_at'],'evidence':[{'reference':decision['reference'],'terms_sha256':hashlib.sha256(decision['evidence_text'].encode('utf-8')).hexdigest(),'approved_by_role':'product_owner'}],'status':'CONDITIONAL','valid_from':approvals['approved_at'],'valid_until':approvals['valid_until'],'review_due_at':approvals['review_due_at'],'conditions':[{'type':'attribution','text':decision['attribution_text'],'targets':['data/macro-calendar.json','index.html']}]})
    rights.validate_registry(base);return base


def assess(payload, today=None):
    return rights.assess(effective_registry(), rights.inventory(payload), rights.load_baseline(), payload, today)


def enforce(payload):
    # Preserve the original UNKNOWN migration gate for every non-calendar dataset.
    # The four approved calendar IDs are removed from that legacy assessment only;
    # they are then assessed under the explicit CONDITIONAL effective registry.
    base = rights.read_json(ROOT / 'data-rights/registry.json')
    items = rights.inventory(payload)
    non_calendar = [item for item in items if item['id'] not in EXPECTED_IDS]
    base_report = rights.assess(base, non_calendar, rights.load_baseline(), payload)
    if base_report['blocked']:
        raise rights.PublicationBlocked(base_report)
    report = rights.assess(effective_registry(base), items, rights.load_baseline(), payload)
    if report['blocked']:
        raise rights.PublicationBlocked(report)
    return report
