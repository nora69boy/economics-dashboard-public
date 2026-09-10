import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gate', ROOT/'scripts/check_site.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class PrivacyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.site = Path(self.tmp.name)/'site'
        shutil.copytree(ROOT/'site', self.site)
    def tearDown(self):
        self.tmp.cleanup()
    def change(self, extra):
        p = self.site/'index.html'
        p.write_text(p.read_text(encoding='utf-8').replace('</body>', extra+'</body>'), encoding='utf-8')
        self.rehash()
    def rehash(self):
        p = self.site/'manifest.json'
        m = json.loads(p.read_text())
        m['files']['index.html'] = hashlib.sha256((self.site/'index.html').read_bytes()).hexdigest()
        p.write_text(json.dumps(m), encoding='utf-8')
    def blocked(self):
        with self.assertRaises((ValueError, OSError, UnicodeError)):
            gate.validate_site(self.site)
    def test_valid(self):
        self.assertEqual(len(gate.validate_site(self.site)), 3)
    def test_email(self):
        self.change('<p>test-user@example.invalid</p>'); self.blocked()
    def test_encoded_email(self):
        self.change('<p>test-user&#64;example.invalid</p>'); self.blocked()
    def test_phone(self):
        self.change('<p>000-0000-0000</p>'); self.blocked()
    def test_unlisted(self):
        (self.site/'extra.txt').write_text('test'); self.blocked()
    def test_digest(self):
        p = self.site/'index.html'; p.write_bytes(p.read_bytes()+b' '); self.blocked()
    def test_symlink(self):
        (self.site/'extra').symlink_to(self.site/'index.html'); self.blocked()
    def test_traversal(self):
        p = self.site/'manifest.json'; m = json.loads(p.read_text()); m['files']['../outside.html'] = '0'*64
        p.write_text(json.dumps(m)); self.blocked()
    def test_iframe(self):
        self.change('<iframe></iframe>'); self.blocked()
    def test_form(self):
        self.change('<form></form>'); self.blocked()
    def test_missing_csp(self):
        p = self.site/'index.html'; p.write_text(p.read_text().replace('Content-Security-Policy','Other-Policy'))
        self.rehash(); self.blocked()
    def test_changed_script(self):
        p = self.site/'index.html'; p.write_text(p.read_text().replace("'use strict';", "'use strict';\nvoid 0;"))
        self.rehash(); self.blocked()
    def test_network(self):
        self.assertIsNotNone(gate.NETWORK.search("fetch('/test');"))
        p = self.site/'index.html'; p.write_text(p.read_text().replace("'use strict';", "'use strict';\nfetch('/test');"))
        self.rehash(); self.blocked()
    def test_inline_handler(self):
        self.change('<button onclick="void 0">test</button>'); self.blocked()
    def test_manifest_extra_field(self):
        p = self.site/'manifest.json'; m = json.loads(p.read_text()); m['extra'] = 'test'
        p.write_text(json.dumps(m)); self.blocked()
    def test_external_image(self):
        self.change('<img src="//example.invalid/test">'); self.blocked()

if __name__ == '__main__':
    unittest.main()
