"""Rights policy and final-publication regressions; fixtures confer no real rights."""
import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import publication_rights as r
import check_release

TODAY = date(2026, 9, 13)
REGISTRY = r.read_json(ROOT / 'data-rights/registry.json')
BASELINE = r.load_baseline()


def payload():
    return {name: (ROOT / 'site' / name).read_bytes() for name in r.TARGETS}


class HashPhoneScannerTests(unittest.TestCase):
    def setUp(self):
        self.hash = 'a' * 20 + '0' + '123456789' + 'b' * 34

    def scan(self, data, document='migration-baseline.json'):
        r.check_site.scan(json.dumps(data), rights_document=document)

    def test_only_allowed_hash_paths_are_exempt(self):
        self.scan({'html_shell_sha256': self.hash, 'datasets': {'market-spx': {
            'scope_sha256': self.hash, 'content_sha256': self.hash}}})
        self.scan({'datasets': [{'evidence': [{'terms_sha256': self.hash}]}]}, 'registry.json')
        for data in [{'other': self.hash}, {'content_sha256': self.hash},
                     {'nested': {'html_shell_sha256': self.hash}},
                     {'datasets': {'market-spx': {'terms_sha256': self.hash}}},
                     {'html_shell_sha256': self.hash, 'note': self.hash}]:
            with self.subTest(data=data), self.assertRaisesRegex(ValueError, 'sensitive phone'):
                self.scan(data)
        with self.assertRaisesRegex(ValueError, 'sensitive phone'):
            r.check_site.scan(json.dumps({'html_shell_sha256': self.hash}))
        with self.assertRaisesRegex(ValueError, 'sensitive phone'):
            self.scan({'html_shell_sha256': self.hash}, 'registry.json')

    def test_hash_format_requires_exact_lowercase_hex(self):
        for value in [self.hash[:-1], self.hash + 'a', self.hash.upper(),
                      self.hash + '\n', ' ' + self.hash, self.hash + ' ',
                      self.hash[:-1] + 'g', self.hash.replace('a', '\uff41')]:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'sensitive phone'):
                self.scan({'html_shell_sha256': value})

    def test_other_secret_checks_still_scan_original_hash_values(self):
        for label in ['credential', 'token', 'key']:
            with self.subTest(label=label), patch.dict(r.check_site.PATTERNS, {label: self.hash}):
                with self.assertRaisesRegex(ValueError, 'sensitive ' + label):
                    self.scan({'html_shell_sha256': self.hash})
        for value, label in [('api' + '_key=' + 'a' * 32, 'credential'),
                             ('gh' + 'p_' + 'a' * 30, 'token'),
                             ('-----BEGIN ' + 'PRIVATE KEY-----', 'key')]:
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, 'sensitive ' + label):
                self.scan({'html_shell_sha256': self.hash, 'note': value})

    def test_actual_baseline_false_positive_and_integrity(self):
        content = (ROOT / 'data-rights/migration-baseline.json').read_text()
        with self.assertRaisesRegex(ValueError, 'sensitive phone'):
            r.check_site.scan(content)
        r.check_site.scan(content, rights_document='migration-baseline.json')
        self.assertEqual(r.load_baseline(), BASELINE)
        changed = copy.deepcopy(BASELINE)
        changed['datasets']['market-n225']['content_sha256'] = self.hash
        self.scan(changed)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'migration-baseline.json'
            path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(r.RightsError, 'MIGRATION_BASELINE_CHANGED'):
                r.load_baseline(path)


class RightsTests(unittest.TestCase):
    def setUp(self):
        self.registry = copy.deepcopy(REGISTRY)
        self.payload = payload()
        self.items = r.inventory(self.payload)
        self.item = next(i for i in self.items if i['id'] == 'market-spx')
        self.entry = next(e for e in self.registry['datasets'] if e['id'] == self.item['id'])

    def report(self, items=None):
        return r.assess(self.registry, items or [self.item], BASELINE, self.payload, TODAY)

    def codes(self, items=None):
        return {b['code'] for b in self.report(items)['blocked']}

    def approve(self, conditional=False):
        self.entry.update(status='CONDITIONAL' if conditional else 'APPROVED',
                          reviewed_at='2026-09-13', valid_from='2026-01-01',
                          valid_until='2026-12-31', review_due_at='2026-12-31',
                          terms_url=['https://example.invalid/terms'],
                          evidence=[{'reference': 'synthetic-test-only',
                                     'terms_sha256': 'a' * 64, 'approved_by_role': 'product_owner'}],
                          retention={'mode': 'WHILE_VALID', 'max_age_days': None})
        for use in r.PUBLIC_USES:
            self.entry[use] = 'ALLOWED'
        if conditional:
            self.entry['conditions'] = [{'type': 'attribution', 'text': 'VIX withheld', 'targets': ['index.html']}]

    def test_registry_schema(self):
        entries = r.validate_registry(self.registry, TODAY)
        self.assertEqual(len(entries), 40)
        self.assertEqual({e['status'] for e in entries.values()}, {'UNKNOWN'})

    def test_required_fields(self):
        for field in r.FIELDS:
            with self.subTest(field=field):
                changed = copy.deepcopy(self.registry)
                del changed['datasets'][0][field]
                with self.assertRaises(r.RightsError):
                    r.validate_registry(changed, TODAY)

    def test_invalid_schema_types_and_extra_fields(self):
        for mutate in [lambda e: e.update(existing=True), lambda e: e.update(status='approved'),
                       lambda e: e.update(display=True), lambda e: e.update(evidence='approved'),
                       lambda e: e.update(fields=['value', 'value']),
                       lambda e: e.update(monthly_cost_ceiling_jpy=True),
                       lambda e: e.update(retention={'mode': 'UNKNOWN', 'max_age_days': -1}),
                       lambda e: e.update(reviewed_at='2099-01-01')]:
            changed = copy.deepcopy(self.registry); mutate(changed['datasets'][0])
            with self.assertRaises((r.RightsError, TypeError)):
                r.validate_registry(changed, TODAY)

    def test_duplicate_registry_id(self):
        self.registry['datasets'].append(copy.deepcopy(self.entry))
        with self.assertRaises(r.RightsError):
            r.validate_registry(self.registry, TODAY)

    def test_missing_registry_file(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(r, 'ROOT', Path(tmp)):
            with self.assertRaises(r.RightsError):
                r.enforce(self.payload)

    def test_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'registry.json'; p.write_text('{"schema_version":1,"schema_version":1}')
            with self.assertRaises(r.RightsError):
                r.read_json(p)

    def test_missing_registry_entry(self):
        self.registry['datasets'].remove(self.entry)
        self.assertIn('MISSING_REGISTRY_ENTRY', self.codes())

    def test_new_unknown_rejected_even_if_in_registry(self):
        self.entry['id'] = self.item['id'] = 'new-series'
        self.assertIn('NEW_UNKNOWN', self.codes())

    def test_new_unknown_missing_entry_rejected(self):
        self.item['id'] = 'new-series'
        self.assertIn('MISSING_REGISTRY_ENTRY', self.codes())

    def test_prohibited_existing_rejected(self):
        self.entry['status'] = 'PROHIBITED'
        self.assertIn('PROHIBITED', self.codes())

    def test_expired_existing_rejected(self):
        self.entry['status'] = 'EXPIRED'
        self.assertIn('EXPIRED', self.codes())

    def test_revoked_existing_rejected(self):
        self.entry['status'] = 'REVOKED'
        self.assertIn('REVOKED', self.codes())

    def test_restricted_new_rejected(self):
        self.entry['id'] = self.item['id'] = 'new-series'
        for status in ('PROHIBITED', 'EXPIRED', 'REVOKED'):
            self.entry['status'] = status
            self.assertIn(status, self.codes())

    def test_approved_new_accepted(self):
        self.entry['id'] = self.item['id'] = 'new-series'
        self.approve()
        self.assertEqual(self.report()['result'], 'ALLOWED')

    def test_approved_without_evidence_rejected(self):
        self.entry['status'] = 'APPROVED'
        with self.assertRaises(r.RightsError):
            self.report()

    def test_approved_missing_each_required_permission(self):
        self.approve()
        for use in r.PUBLIC_USES:
            self.entry[use] = 'UNKNOWN'
            self.assertIn('PURPOSE_PERMISSION_REQUIRED', self.codes())
            self.entry[use] = 'ALLOWED'

    def test_elapsed_validity_overrides_migration(self):
        self.entry['valid_until'] = '2026-09-12'
        self.assertIn('EXPIRED', self.codes())

    def test_validity_inclusive_and_future_start(self):
        self.approve(); self.entry['valid_until'] = TODAY.isoformat()
        self.assertEqual(self.report()['result'], 'ALLOWED')
        self.entry['valid_until'] = '2026-12-31'; self.entry['valid_from'] = '2026-09-14'
        self.assertIn('NOT_YET_VALID', self.codes())

    def test_review_deadline_blocks_approved(self):
        self.approve(); self.entry['review_due_at'] = '2026-09-12'
        self.assertIn('RIGHTS_REVIEW_OVERDUE', self.codes())

    def test_conditional_accepted_only_when_rule_satisfied(self):
        self.approve(conditional=True)
        self.assertEqual(self.report()['result'], 'ALLOWED')
        self.entry['conditions'][0]['text'] = 'Missing required acknowledgement'
        self.assertIn('CONDITION_UNSATISFIED', self.codes())

    def test_conditional_without_rules_rejected(self):
        self.approve(); self.entry['status'] = 'CONDITIONAL'
        with self.assertRaises(r.RightsError):
            self.report()

    def test_unsupported_condition_rejected(self):
        self.approve(conditional=True); self.entry['conditions'][0]['type'] = 'promise'
        with self.assertRaises(r.RightsError):
            self.report()

    def test_attribution_must_exist_in_every_target(self):
        self.approve(); self.entry['attribution'] = 'VIX withheld'
        self.assertIn('CONDITION_UNSATISFIED', self.codes())

    def test_existing_unknown_migration(self):
        report = self.report(self.items)
        self.assertEqual(report['result'], 'MIGRATION_WARNING')
        self.assertEqual(len(report['warnings']), 39)
        self.assertEqual(report['migration_status'], 'PENDING_RIGHTS_REVIEW')
        self.assertEqual(report['unpublished_count'], 1)
        self.assertEqual(report['registry_counts'], {s: 40 if s == 'UNKNOWN' else 0 for s in r.STATUSES})

    def test_existing_snapshot_change_not_grandfathered(self):
        self.item['content_sha256'] = '0' * 64
        self.assertIn('CHANGED_UNKNOWN_SNAPSHOT', self.codes())

    def test_source_field_and_target_changes_not_grandfathered(self):
        original_entry = copy.deepcopy(self.entry)
        for key, value in [('source_url', ['https://example.invalid/new']), ('fields', ['new-field']),
                           ('public_targets', ['data/current-state.json'])]:
            old = copy.deepcopy(self.item)
            self.entry.clear(); self.entry.update(copy.deepcopy(original_entry))
            self.item[key] = value; self.entry[key] = value
            self.assertIn('NEW_UNKNOWN', self.codes())
            self.item = old

    def test_registry_scope_must_cover_payload(self):
        self.entry['fields'] = ['date']
        self.assertIn('PUBLICATION_SCOPE_MISMATCH', self.codes())

    def test_existing_macro_refresh_stays_in_migration(self):
        item = next(i for i in self.items if i['id'] == 'macro-ust10')
        item['content_sha256'] = '0' * 64
        self.assertEqual(self.report([item])['result'], 'MIGRATION_WARNING')

    def test_new_auxiliary_not_grandfathered(self):
        item = next(i for i in self.items if i['id'] == 'macro-ust10-ust2')
        e = next(e for e in self.registry['datasets'] if e['id'] == item['id'])
        e['id'] = item['id'] = 'macro-ust10-new-aux'
        self.assertIn('NEW_UNKNOWN', self.codes([item]))

    def test_vix_values_rejected(self):
        item = copy.deepcopy(next(i for i in self.items if i['id'] == 'macro-ust10'))
        e = next(e for e in self.registry['datasets'] if e['id'] == 'macro-vix')
        for key in ('id', 'source_url', 'fields', 'public_targets'):
            item[key] = copy.deepcopy(e[key])
        self.assertIn('NEW_UNKNOWN', self.codes([item]))

    def test_retention_and_purpose_denial_override_migration(self):
        self.entry['retention']['mode'] = 'NONE'
        self.assertIn('PURPOSE_OR_RETENTION_DENIED', self.codes())
        self.entry['retention']['mode'] = 'UNKNOWN'; self.entry['display'] = 'DENIED'
        self.assertIn('PURPOSE_OR_RETENTION_DENIED', self.codes())

    def test_retention_age_and_unknown_date(self):
        self.entry['retention']['max_age_days'] = 1
        self.assertIn('RETENTION_LIMIT', self.codes())
        self.item['oldest_date'] = None
        self.assertIn('RETENTION_LIMIT', self.codes())

    def test_revisions_in_inventory_even_without_observations(self):
        d = json.loads(self.payload['data/macro.json'])
        d['series'][0]['observations'] = []
        d['revisions'] = [{'series': 'ust10', 'date': '2026-09-10', 'old': 1, 'new': 2,
                           'detected_at': '2026-09-13T00:00:00Z'}]
        self.payload['data/macro.json'] = json.dumps(d).encode()
        self.assertIn('macro-ust10', {i['id'] for i in r.inventory(self.payload)})

    def test_unmapped_public_file_rejected(self):
        self.payload['new.json'] = b'{}'
        with self.assertRaises(r.RightsError):
            r.inventory(self.payload)

    def test_html_only_data_rejected(self):
        self.payload['index.html'] = self.payload['index.html'].replace(b'</body>', b'<p>New numeric series: 123</p></body>')
        self.assertIn('UNMAPPED_HTML_CONTENT', self.codes())

    def test_html_fallback_tampering_rejected(self):
        self.payload['index.html'] = self.payload['index.html'].replace(b'Raw value', b'Unregistered value')
        with self.assertRaises(r.RightsError):
            self.report()

    def test_baseline_cannot_self_enrol(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'baseline.json'
            b = copy.deepcopy(BASELINE); b['datasets']['new-series'] = b['datasets']['market-spx']
            p.write_text(json.dumps(b))
            with self.assertRaises(r.RightsError):
                r.load_baseline(p)

    def test_safe_report_does_not_echo_registry_metadata(self):
        self.entry['dataset'] = 'PUBLIC-METADATA-MARKER'
        report = self.report()
        out = io.StringIO()
        with redirect_stdout(out):
            r.emit(report)
        self.assertNotIn('PUBLIC-METADATA-MARKER', out.getvalue())
        self.assertNotIn('https://', out.getvalue())
        self.assertIn('::warning::', out.getvalue())

    def test_unsafe_metadata_rejected_without_echo(self):
        self.entry['provider'] = 'bad\n::warning::injected'
        with self.assertRaises(r.RightsError) as exc:
            r.validate_registry(self.registry, TODAY)
        self.assertNotIn('injected', str(exc.exception))

    def test_final_release_gate_is_wired(self):
        with patch.object(r, 'enforce', side_effect=r.RightsError('TEST_BLOCK')):
            with self.assertRaises(r.RightsError):
                check_release.validate(ROOT / 'site')

    def test_actual_payload_revocation_reaches_release_gate(self):
        self.entry['status'] = 'REVOKED'
        original = r.read_json
        def read_policy(path):
            return self.registry if path.name == 'registry.json' else original(path)
        with patch.object(r, 'read_json', side_effect=read_policy):
            with self.assertRaises(r.PublicationBlocked) as exc:
                check_release.validate(ROOT / 'site')
        self.assertIn({'id': 'market-spx', 'code': 'REVOKED'}, exc.exception.report['blocked'])

    def test_actual_payload_missing_registration_reaches_release_gate(self):
        self.registry['datasets'].remove(self.entry)
        original = r.read_json
        def read_policy(path):
            return self.registry if path.name == 'registry.json' else original(path)
        with patch.object(r, 'read_json', side_effect=read_policy):
            with self.assertRaises(r.PublicationBlocked) as exc:
                check_release.validate(ROOT / 'site')
        self.assertIn({'id': 'market-spx', 'code': 'MISSING_REGISTRY_ENTRY'}, exc.exception.report['blocked'])

    def test_blocked_release_does_not_prepare_artifact(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(check_release, 'ROOT', Path(tmp)), \
             patch.object(check_release, 'validate', side_effect=r.RightsError('TEST_BLOCK')), \
             patch.object(sys, 'argv', ['check_release', '--build']):
            with self.assertRaises(SystemExit):
                check_release.main()
            self.assertFalse((Path(tmp) / '.pages-build').exists())

    def test_development_files_not_in_public_targets(self):
        self.assertEqual(r.TARGETS, check_release.gate.PAYLOAD | {'data/macro.json', 'data/macro-calendar.json'})
        self.assertTrue(all(not name.startswith('data-rights/') for name in r.TARGETS))

    def test_ci_runs_rights_tests_and_final_gate(self):
        workflow = (ROOT / '.github/workflows/pages.yml').read_text()
        self.assertIn('python3 -m unittest discover -s tests -p test_rights.py -v', workflow)
        self.assertLess(workflow.index('scripts/check_release.py --check-history --build'),
                        workflow.index('Upload validated public artifact'))


if __name__ == '__main__':
    unittest.main()
