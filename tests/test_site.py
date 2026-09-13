"""Regression checks run before publication; no network or private inputs."""
import copy,hashlib,importlib.util,json,re,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
builder=load('builder',ROOT/'scripts/build_dashboard.py')
if not (ROOT/'site/index.html').exists():builder.build()
g=load('gate',ROOT/'scripts/check_site.py')
class PrivacyTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.site=Path(self.tmp.name)/'site';shutil.copytree(ROOT/'site',self.site)
 def tearDown(self):self.tmp.cleanup()
 def hash(self,n='index.html'):
  p=self.site/'manifest.json';d=json.loads(p.read_text());d['files'][n]=hashlib.sha256((self.site/n).read_bytes()).hexdigest();p.write_text(json.dumps(d))
 def inject(self,x):
  p=self.site/'index.html';p.write_text(p.read_text().replace('</body>',x+'</body>'));self.hash()
 def blocked(self):
  with self.assertRaises((ValueError,OSError,UnicodeError)):g.validate(self.site)
 def test_valid(self):self.assertEqual(len(g.validate(self.site)),4)
 def test_unlisted(self):(self.site/'extra.txt').write_text('test');self.blocked()
 def test_symlink(self):(self.site/'x').symlink_to(self.site/'index.html');self.blocked()
 def test_hash(self):
  p=self.site/'index.html';p.write_bytes(p.read_bytes()+b' ');self.blocked()
 def test_manifest(self):
  p=self.site/'manifest.json';d=json.loads(p.read_text());d['extra']=1;p.write_text(json.dumps(d));self.blocked()
 def test_traversal(self):
  p=self.site/'manifest.json';d=json.loads(p.read_text());d['files']['../x.html']='0'*64;p.write_text(json.dumps(d));self.blocked()
 def test_duplicate_json(self):
  with self.assertRaises(ValueError):g.loads('{"x":1,"x":2}')
 def test_nan_json(self):
  with self.assertRaises(ValueError):g.loads('{"x":NaN}')
 def test_csp(self):
  p=self.site/'index.html';p.write_text(p.read_text().replace('Content-Security-Policy','Other'));self.hash();self.blocked()
 def test_script(self):
  p=self.site/'index.html';p.write_text(p.read_text().replace("'use strict';","'use strict';void 0;"));self.hash();self.blocked()
 def test_embedded(self):
  p=self.site/'data/market.json';d=json.loads(p.read_text());d['assets'][0]['observations'][0]['close']+=.01;p.write_text(json.dumps(d));self.hash('data/market.json');self.blocked()
 def test_deterministic(self):
  b=(ROOT/'site/index.html').read_bytes();builder.build();self.assertEqual(b,(ROOT/'site/index.html').read_bytes())
for name,x in {'email':'<p>unit@example.invalid</p>','encoded_email':'<p>unit&#64;example.invalid</p>','phone':'<p>000-0000-0000</p>','iframe':'<iframe></iframe>','form':'<form></form>','image':'<img src="//example.invalid/x">','event':'<button onclick="void 0">x</button>','duplicate_attr':'<p id="a" id="b">x</p>','duplicate_id':'<p id="age">x</p>','unapproved_link':'<a href="https://example.invalid">x</a>','link_policy':'<a href="https://www.bls.gov/schedule/2026/home.htm">x</a>','secret':'<p>password = example_invalid_only</p>','local_address':'<p>192.168.20.1</p>'}.items():
 def f(self,x=x):self.inject(x);self.blocked()
 setattr(PrivacyTests,'test_'+name,f)
class DataTests(unittest.TestCase):
 def test_valid_research(self):g.research(json.loads((ROOT/'site/data/current-state.json').read_text()))
 def test_valid_market(self):g.market(json.loads((ROOT/'site/data/market.json').read_text()))
 def test_ids(self):
  s=(ROOT/'site/index.html').read_text();d=json.loads((ROOT/'site/data/market.json').read_text());self.assertEqual(set(re.findall(r'data-global-symbol="([^"]+)"',s)),{a['symbol'] for a in d['indices']})
 def test_counts(self):self.assertEqual(len(re.findall(r'id="tab-[^"]+"',(ROOT/'site/index.html').read_text())),9)
 def test_network_patterns(self):
  for s in ["fetch('/x')",'WebSocket','localStorage','location.href','window.open','XMLHttpRequest']:self.assertIsNotNone(g.NETWORK.search(s))
research_cases=[('automated_report_ingestion',True),('live_market_data',True),('extra',1),('sources.0.url','https://example.invalid'),('sources.0.checked_at','2030-01-01'),('topics.0.claim_type','fact'),('topics.0.streams',['unknown']),('topics.0.extra',1),('topics.1.id', 'macro-rates'),('events.0.source','unknown'),('events.0.end','2025-01-01'),('events.0.time_jst','2030-01-01 12:00'),('company_checks',[])]
market_cases=[('automatic_updates',True),('mode','live'),('extra',1),('checked_at','2030-01-01'),('assets.0.kind','index'),('assets.5.kind','index'),('assets.0.currency','JPY'),('assets.0.basis','total_return'),('assets.0.quantity',1),('assets.0.observations.0.low',9999),('assets.0.observations.0.volume',-1),('assets.0.observations.0.volume',True),('assets.0.observations.0.close',float('nan')),('assets.0.observations.0.close',float('inf')),('assets.0.observations.0.close',True),('assets.0.observations.0.close',0),('assets.0.observations.0.date','2026-09-03'),('indices.0.kind','etf'),('indices.0.unit','USD'),('indices.6.basis','price'),('indices.0.zone','Asia/Tokyo'),('indices.0.sources',['https://example.invalid']),('indices.0.observations.0.volume',10),('indices.0.observations.0.date','2030-01-01'),('indices.0.observations.0.close',-1),('financials.basis','non-GAAP'),('financials.unit','USD'),('financials.periods.0.gross_margin',120),('financials.periods.0.period','FY25 Q1')]
for kind,cases in [('research',research_cases),('market',market_cases)]:
 for i,(path,value) in enumerate(cases):
  def f(self,path=path,value=value,kind=kind):
   d=json.loads((ROOT/'site/data'/('market.json' if kind=='market' else 'current-state.json')).read_text());o=d;parts=path.split('.')
   for p in parts[:-1]:o=o[int(p)] if isinstance(o,list) else o[p]
   o[parts[-1]]=value
   with self.assertRaises((ValueError,KeyError,TypeError)):getattr(g,kind)(d)
  setattr(DataTests,'test_'+kind+'_'+str(i),f)

class PortalTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.code=(ROOT/'templates/charts.js').read_text().split('/* Independent, read-only market portal.')[1]
  cls.data=json.loads((ROOT/'site/data/market.json').read_text())
 def test_no_transport(self):self.assertIsNone(g.NETWORK.search(self.code))
 def test_no_html_injection(self):
  for s in ['innerHTML','outerHTML','insertAdjacentHTML','document.write']:self.assertNotIn(s,self.code)
 def test_search_only(self):
  self.assertIn("search.type='search'",self.code);self.assertIn("search.id='instrument-search'",self.code);self.assertIn('search.maxLength=40',self.code)
 def test_no_forms(self):
  for tag in ["el('form'","el('textarea'","el('iframe'","el('img'"]:self.assertNotIn(tag,self.code)
 def test_comparison_basis(self):self.assertIn("a.basis!=='total_return'",self.code);self.assertIn('/derived/i',self.code)
 def test_exact_common_dates(self):
  dates={r['date'] for r in self.data['indices'][0]['observations']}
  for a in self.data['assets']+self.data['indices']:self.assertTrue(dates<={r['date'] for r in a['observations']})
 def test_price_snapshot_unchanged(self):self.assertEqual(self.data['as_of'],'2026-09-10');self.assertFalse(self.data['automatic_updates'])
 def test_bounded_selection(self):self.assertIn('selections.size<4',self.code);self.assertIn('selections.size>1',self.code)
 def test_no_private_endpoints(self):
  for s in ['api.github.com','docs.google.com','mail.google.com']:self.assertNotIn(s,self.code)
 def test_source_urls_allowlisted(self):
  urls=re.findall(r"https://[a-zA-Z0-9./_%?=+-]+",self.code)
  self.assertTrue(set(urls)<=g.URLS)
 def test_pii_search_not_logged(self):
  for s in ['console.log','console.error','search.value+', 'JSON.stringify(F)']:self.assertNotIn(s,self.code)
 def test_no_automatic_actions(self):
  for s in ['setInterval','navigator.','Notification(','serviceWorker']:self.assertNotIn(s,self.code)
 def test_version(self):self.assertIn("version:'0.5.0'",self.code)
 def test_reference_series_not_ranked(self):self.assertIn('D.indices.filter(comparable)',self.code)
 def test_bounded_dom_search(self):self.assertIn("search.value.slice(0,40)",self.code)
 def test_legacy_css_no_external_import(self):
  s=(ROOT/'templates/charts.css').read_text();self.assertNotRegex(s,r'@import|url\s*\(')
if __name__=='__main__':unittest.main()
