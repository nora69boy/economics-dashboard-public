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

    def test_main_health_usable_if_one_official_path_parses(self):
        with mock.patch.object(wti_probe, 'probe', side_effect=[
            {'source': 'eia_history_html', 'download': 'failed', 'parse': 'not_attempted', 'error_class': 'URLError'},
            {'source': 'eia_recent_html', 'download': 'ok', 'parse': 'ok', 'points': 6, 'latest_observation': '2026-09-15'},
        ]):
            out = io.StringIO()
            with redirect_stdout(out):
                wti_probe.main()
        payload = json.loads(out.getvalue())
        self.assertEqual(payload['wti_probe_health'], 'usable')
        self.assertEqual(len(payload['sources']), 2)


if __name__ == '__main__':
    unittest.main()
