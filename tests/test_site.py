import copy,hashlib,importlib.util,json,re,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('gate',ROOT/'scripts/check_site.py')
gate=importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
class PrivacyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.site=Path(self.tmp.name)/'site'; shutil.copytree(ROOT/'site',self.site)
    def tearDown(self): self.tmp.cleanup()
    def rehash(self,name='index.html'):
        p=self.site/'manifest.json'; m=json.loads(p.read_text()); m['files'][name]=hashlib.sha256((self.site/name).read_bytes()).hexdigest(); p.write_text(json.dumps(m))
    def change(self,extra):
        p=self.site/'index.html'; p.write_text(p.read_text().replace('</body>',extra+'</body>')); self.rehash()
    def blocked(self):
        with self.assertRaises((ValueError,OSError,UnicodeError)): gate.validate_site(self.site)
    def test_valid(self): self.assertEqual(len(gate.validate_site(self.site)),3)
    def test_email(self): self.change('<p>test-user@example.invalid</p>'); self.blocked()
    def test_encoded_email(self): self.change('<p>test-user&#64;example.invalid</p>'); self.blocked()
    def test_phone(self): self.change('<p>000-0000-0000</p>'); self.blocked()
    def test_unlisted(self): (self.site/'extra.txt').write_text('test'); self.blocked()
    def test_digest(self):
        p=self.site/'index.html'; p.write_bytes(p.read_bytes()+b' '); self.blocked()
    def test_symlink(self): (self.site/'extra').symlink_to(self.site/'index.html'); self.blocked()
    def test_traversal(self):
        p=self.site/'manifest.json'; m=json.loads(p.read_text()); m['files']['../outside.html']='0'*64; p.write_text(json.dumps(m)); self.blocked()
    def test_iframe(self): self.change('<iframe></iframe>'); self.blocked()
    def test_form(self): self.change('<form></form>'); self.blocked()
    def test_missing_csp(self):
        p=self.site/'index.html'; p.write_text(p.read_text().replace('Content-Security-Policy','Other-Policy')); self.rehash(); self.blocked()
    def test_changed_script(self):
        p=self.site/'index.html'; p.write_text(p.read_text().replace("'use strict';","'use strict';void 0;")); self.rehash(); self.blocked()
    def test_network(self): self.assertIsNotNone(gate.NETWORK.search("fetch('/test');"))
    def test_inline_handler(self): self.change('<button onclick="void 0">test</button>'); self.blocked()
    def test_manifest_extra_field(self):
        p=self.site/'manifest.json'; m=json.loads(p.read_text()); m['extra']='test'; p.write_text(json.dumps(m)); self.blocked()
    def test_external_image(self): self.change('<img src="//example.invalid/test">'); self.blocked()
    def test_duplicate_attribute(self): self.change('<a href="#ok" href="https://example.invalid">x</a>'); self.blocked()
    def test_unapproved_link(self): self.change('<a href="https://example.invalid">x</a>'); self.blocked()
    def test_source_without_referrer(self): self.change('<a href="https://www.bls.gov/schedule/2026/home.htm">x</a>'); self.blocked()
    def test_approved_source(self):
        self.change('<a href="https://www.bls.gov/schedule/2026/home.htm" rel="noopener noreferrer" referrerpolicy="no-referrer">x</a>'); gate.validate_site(self.site)
    def test_duplicate_json(self):
        with self.assertRaises(ValueError): gate.loads('{"a":1,"a":2}')
    def test_duplicate_id(self): self.change('<p id="age">x</p>'); self.blocked()
    def test_quoted_secret(self):
        with self.assertRaises(ValueError): gate.scan('{"password": "example_invalid_only"}')
    def test_navigation_program(self): self.assertIsNotNone(gate.NETWORK.search('location.href'))
class ResearchTests(unittest.TestCase):
    def setUp(self): self.data=json.loads((ROOT/'site/data/current-state.json').read_text())
    def blocked(self):
        with self.assertRaises((ValueError,TypeError,KeyError)): gate.check_research(self.data)
    def test_schema(self): gate.check_research(self.data)
    def test_streams(self): self.assertEqual(len(self.data['streams']),5)
    def test_no_false_ingestion(self): self.data['automated_report_ingestion']=True; self.blocked()
    def test_no_false_live_data(self): self.data['live_market_data']=True; self.blocked()
    def test_unknown_field(self): self.data['extra']='test'; self.blocked()
    def test_duplicate_topic(self): self.data['topics'][1]['id']=self.data['topics'][0]['id']; self.blocked()
    def test_duplicate_event(self): self.data['events'][1]['id']=self.data['events'][0]['id']; self.blocked()
    def test_unknown_source(self): self.data['events'][0]['source']='other'; self.blocked()
    def test_unapproved_url(self): self.data['sources'][0]['url']='https://example.invalid'; self.blocked()
    def test_unknown_routing(self): self.data['topics'][0]['streams'].append('other'); self.blocked()
    def test_claim_type(self): self.data['topics'][0]['claim_type']='fact'; self.blocked()
    def test_unknown_nested_field(self): self.data['topics'][0]['extra']='test'; self.blocked()
    def test_date_only(self): self.data['events'][0]['time_jst']='2026-09-16 12:00'; self.blocked()
    def test_wrong_timezone(self):
        e=next(e for e in self.data['events'] if e['id']=='jobs-nov'); e['time_jst']=e['time_jst'].replace('22:30','21:30'); self.blocked()
    def test_event_order(self): self.data['events'][0]['end']='2026-01-01'; self.blocked()
    def test_future_verification(self): self.data['sources'][0]['checked_at']='2030-01-01'; self.blocked()
    def test_rendered_topic_ids(self):
        text=(ROOT/'site/index.html').read_text(); self.assertEqual(set(re.findall(r'data-topic-id="([^"]+)"',text)),{r['id'] for r in self.data['topics']})
    def test_rendered_event_ids(self):
        text=(ROOT/'site/index.html').read_text(); self.assertEqual(set(re.findall(r'data-event-id="([^"]+)"',text)),{r['id'] for r in self.data['events']})
    def test_rendered_times(self):
        text=(ROOT/'site/index.html').read_text()
        for e in self.data['events']:
            if e['time_jst']: self.assertIn(e['time_jst'],text)
    def test_company_checklist(self): self.assertEqual(len(self.data['company_checks']),14)
if __name__=='__main__': unittest.main()
