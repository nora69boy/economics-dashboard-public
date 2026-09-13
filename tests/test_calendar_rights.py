"""Regressions for the explicit four-dataset calendar rights approval."""
import copy
import hashlib
import json
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import calendar_rights as cr
import publication_rights as r

TODAY=date(2026,9,14)


def payload():
    return {name:(ROOT/'site'/name).read_bytes() for name in r.TARGETS}


class CalendarRightsTests(unittest.TestCase):
    def test_exactly_four_calendar_datasets_are_conditional(self):
        registry=cr.effective_registry()
        entries={e['id']:e for e in registry['datasets']}
        self.assertEqual({k for k,v in entries.items() if v['status']=='CONDITIONAL'},cr.EXPECTED_IDS)
        self.assertEqual(sum(v['status']=='UNKNOWN' for v in entries.values()),36)
        for ident in cr.EXPECTED_IDS:
            entry=entries[ident]
            self.assertTrue(all(entry[u]=='ALLOWED' for u in r.PUBLIC_USES))
            self.assertEqual(entry['commercial_use'],'UNKNOWN')
            self.assertEqual(entry['ai_processing'],'UNKNOWN')
            self.assertEqual(entry['retention'],{'mode':'WHILE_VALID','max_age_days':None})
            self.assertEqual(entry['reviewed_at'],'2026-09-14')
            self.assertEqual(entry['review_due_at'],'2027-08-14')
            self.assertEqual(entry['valid_until'],'2027-09-14')
            self.assertEqual(entry['evidence'][0]['approved_by_role'],'product_owner')

    def test_evidence_hashes_are_reproducible(self):
        approvals=cr.load_approvals()
        registry={e['id']:e for e in cr.effective_registry()['datasets']}
        for decision in approvals['datasets']:
            expected=hashlib.sha256(decision['evidence_text'].encode('utf-8')).hexdigest()
            self.assertEqual(registry[decision['id']]['evidence'][0]['terms_sha256'],expected)

    def test_attribution_urls_exist_in_both_public_targets(self):
        p=payload()
        approvals=cr.load_approvals()
        for decision in approvals['datasets']:
            for target in ['data/macro-calendar.json','index.html']:
                self.assertIn(decision['attribution_text'],p[target].decode())

    def test_effective_release_is_allowed_with_remaining_migration_warnings(self):
        report=cr.assess(payload(),TODAY)
        self.assertEqual(report['result'],'MIGRATION_WARNING')
        self.assertEqual(report['registry_counts']['CONDITIONAL'],4)
        self.assertEqual(report['registry_counts']['UNKNOWN'],36)
        self.assertEqual(len(report['warnings']),35)
        self.assertEqual(report['unpublished_count'],1)
        self.assertFalse(report['blocked'])

    def test_missing_approved_attribution_blocks(self):
        p=payload();registry=cr.effective_registry();items=r.inventory(p)
        entry=next(e for e in registry['datasets'] if e['id']=='calendar-cpi')
        entry['conditions'][0]['text']='https://example.invalid/missing-attribution'
        report=r.assess(registry,items,r.load_baseline(),p,TODAY)
        self.assertIn('CONDITION_UNSATISFIED',{b['code'] for b in report['blocked']})

    def test_non_calendar_entries_are_unchanged(self):
        base=r.read_json(ROOT/'data-rights/registry.json')
        effective=cr.effective_registry(base)
        before={e['id']:e for e in base['datasets'] if e['id'] not in cr.EXPECTED_IDS}
        after={e['id']:e for e in effective['datasets'] if e['id'] not in cr.EXPECTED_IDS}
        self.assertEqual(before,after)


if __name__=='__main__':unittest.main()
