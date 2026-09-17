import io
import json
import unittest
import urllib.error
from contextlib import redirect_stdout
from unittest import mock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import wti_probe


class TestWtiProbe(unittest.TestCase):
    def test_success_reports_only_bounded_metadata(self):
        with mock.patch.object(wti_probe, 'download', return_value=b'provider-bytes'):
            row = wti_probe.probe('eia_recent_html', 'https://example.invalid', lambda raw: {'2026-09-15': 107.02})
        self.assertEqual(row['download'], 'ok')
        self.assertEqual(row['parse'], 'ok')
        self.assertEqual(row['latest_observation'], '2026-09-15')
        self.assertNotIn('body', row)
        self.assertNotIn('url', row)

    def test_http_error_reports_status_without_body(self):
        err = urllib.error.HTTPError('https://example.invalid', 403, 'Forbidden', {}, io.BytesIO(b'secret body'))
        with mock.patch.object(wti_probe, 'download', side_effect=err):
            row = wti_probe.probe('eia_recent_html', 'https://example.invalid', lambda raw: {})
        self.assertEqual(row, {'source': 'eia_recent_html', 'download': 'failed', 'parse': 'not_attempted', 'error_class': 'HTTPError', 'http_status': 403})

    def test_parser_failure_does_not_echo_exception_message(self):
        with mock.patch.object(wti_probe, 'download', return_value=b'private response'):
            row = wti_probe.probe('eia_recent_html', 'https://example.invalid', lambda raw: (_ for _ in ()).throw(ValueError('sensitive detail')))
        self.assertEqual(row['download'], 'ok')
        self.assertEqual(row['parse'], 'failed')
        self.assertEqual(row['error_class'], 'ValueError')
        self.assertNotIn('sensitive detail', json.dumps(row))

    def test_continuity_reports_dates_only_not_prices(self):
        previous = {
            'schema': 1,
            'classification': 'public-official-macro',
            'attempted_at': '2026-09-16T00:00:00Z',
            'series': [],
            'revisions': [],
        }
        for ident in wti_probe.validate.__globals__['META']:
            if ident == 'vix':
                s = {'id': ident, 'status': 'rights_pending', 'fetched_at': None, 'source_sha256': None, 'observations': [], 'auxiliary': {}}
            else:
                rows = [[f'{2015 + i // 365:04d}-01-01', 1.0] for i in range(1500)] if ident == 'wti' else []
                # Avoid exercising the full schema validator here; it is mocked below.
                s = {'id': ident, 'status': 'available', 'fetched_at': '2026-09-16T00:00:00Z', 'source_sha256': 'a'*64, 'observations': rows, 'auxiliary': {}}
            previous['series'].append(s)
        previous['series'][6]['observations'] = [['2026-09-09', 97.26], ['2026-09-10', 103.57]]
        payload = json.dumps(previous).encode()
        with mock.patch.object(wti_probe, 'download', return_value=payload), mock.patch.object(wti_probe, 'validate'):
            row = wti_probe.continuity_probe({'2026-09-09': 97.26, '2026-09-15': 107.02})
        self.assertEqual(row['continuity'], 'fail')
        self.assertEqual(row['missing_count'], 1)
        self.assertEqual(row['missing_first'], '2026-09-10')
        self.assertEqual(row['new_last'], '2026-09-15')
        self.assertNotIn('97.26', json.dumps(row))
        self.assertNotIn('107.02', json.dumps(row))

    def test_main_health_usable_if_one_official_path_parses(self):
        with mock.patch.object(wti_probe, '_fetch_and_parse', side_effect=[
            ({'source': 'eia_history_html', 'download': 'failed', 'parse': 'not_attempted', 'error_class': 'URLError'}, None),
            ({'source': 'eia_recent_html', 'download': 'ok', 'parse': 'ok', 'points': 6, 'latest_observation': '2026-09-15'}, {'2026-09-15': 107.02}),
        ]), mock.patch.object(wti_probe, 'continuity_probe', return_value={'continuity': 'not_attempted'}):
            out = io.StringIO()
            with redirect_stdout(out):
                wti_probe.main()
        payload = json.loads(out.getvalue())
        self.assertEqual(payload['wti_probe_health'], 'usable')
        self.assertEqual(len(payload['sources']), 2)
        self.assertIn('history_continuity', payload)


if __name__ == '__main__':
    unittest.main()
