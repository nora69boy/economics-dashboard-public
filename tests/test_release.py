"""Regressions for the actual v0.6 release and its public-data boundary."""
import copy,hashlib,io,json,math,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import macro_core as c,macro_fetch as fetch,check_release as gate,build_release
DATA=json.loads((ROOT/'site/data/macro.json').read_text());CAL=json.loads((ROOT/'site/data/macro-calendar.json').read_text())
class MacroTests(unittest.TestCase):
 def test_valid_data(self):c.validate(DATA)
 def test_valid_calendar(self):c.validate_calendar(CAL)
 def test_all_government_series_present(self):self.assertEqual(sum(bool(s['observations']) for s in DATA['series']),6)
 def test_missing_not_zero(self):self.assertEqual(DATA['series'][4]['observations'],[])
 def test_long_history(self):self.assertTrue(all(s['observations'][0][0]<='2016-01-01' for s in DATA['series'] if s['observations']))
 def test_yoy_reference_month(self):
  r=c.yoy([['2024-01-01',100],['2025-01-01',110],['2025-03-01',120]]);self.assertEqual(len(r),1);self.assertAlmostEqual(r[0][1],10)
 def test_bls_missing_and_annual(self):
  d={'status':'REQUEST_SUCCEEDED','Results':{'series':[{'seriesID':'CUUR0000SA0','data':[{'year':'2026','period':'M13','value':'100'},{'year':'2026','period':'M08','value':'-'},{'year':'2026','period':'M07','value':'330'}]}]}};self.assertEqual(c.parse_bls(json.dumps(d).encode())['CUUR0000SA0'],{'2026-07-01':330})
 def test_treasury_header_variants(self):
  for header in ['Date,2 Yr,10 Yr','date,2 yr,10 yr']:
   a,b=c.parse_treasury((header+'\n09/11/2026,4.63,4.96\n').encode());self.assertEqual(a['2026-09-11'],4.96)
 def test_bls_failed_response(self):
  with self.assertRaises(ValueError):c.parse_bls(b'{"status":"REQUEST_FAILED"}')
 def test_dst(self):
  e={x['id']:x for x in CAL['events']};self.assertTrue(e['cpi-2026-09-11']['time_jst'].endswith('21:30'));self.assertTrue(e['cpi-2026-11-10']['time_jst'].endswith('22:30'))
 def test_unknown_fomc_times(self):self.assertTrue(all(e['time_local'] is None and e['time_jst'] is None for e in CAL['events'] if e['family']=='fomc'))
 def test_no_consensus_fabrication(self):self.assertTrue(all('forecast' not in e and 'actual' not in e for e in CAL['events']))
 def test_negative_oil_allowed(self):
  d=copy.deepcopy(DATA);d['series'][-1]['observations'][0][1]=-36.98;c.validate(d)
 def test_endpoint_allowlist(self):
  for u in ['https://example.invalid/x','http://api.bls.gov/','https://api.bls.gov/private-path','https://127.0.0.1/']:
   with self.assertRaises(ValueError):fetch.download(u)
 def test_retains_previous_on_source_failure(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'site/data').mkdir(parents=True);previous=root/'previous.json';previous.write_text(json.dumps(DATA))
   with patch.object(fetch,'ROOT',root),patch.object(sys,'argv',['macro_fetch','--raw-dir',tmp,'--previous',str(previous)]),patch.object(fetch,'download',side_effect=AssertionError('network')):fetch.main()
   d=json.loads((root/'site/data/macro.json').read_text());c.validate(d)
   for old,new in zip(DATA['series'],d['series']):
    self.assertEqual(new['observations'],old['observations']);self.assertEqual(new['fetched_at'],old['fetched_at']);self.assertEqual(new['status'],'rights_pending' if old['id']=='vix' else 'retained')
 def test_first_failure_blocks_publication(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'site/data').mkdir(parents=True)
   with patch.object(fetch,'ROOT',root),patch.object(sys,'argv',['macro_fetch','--raw-dir',tmp]),self.assertRaises(ValueError):fetch.main()
   self.assertFalse((root/'site/data/macro.json').exists())
class ArtifactTests(unittest.TestCase):
 def test_actual_release(self):self.assertEqual(len(gate.validate(ROOT/'site')),6)
 def test_deterministic(self):
  before=(ROOT/'site/index.html').read_bytes();build_release.build();self.assertEqual(before,(ROOT/'site/index.html').read_bytes())
 def test_market_snapshot_unchanged(self):self.assertEqual(json.loads((ROOT/'site/data/market.json').read_text())['as_of'],'2026-09-10')
 def test_no_frontend_transport(self):self.assertIsNone(gate.gate.NETWORK.search((ROOT/'templates/macro.js').read_text()))
 def test_no_dom_injection(self):
  code=(ROOT/'templates/macro.js').read_text()
  for bad in ['innerHTML','outerHTML','insertAdjacentHTML','document.write']:self.assertNotIn(bad,code)
 def test_no_workflow_post_test_patch(self):
  text=(ROOT/'.github/workflows/pages.yml').read_text();self.assertNotIn('macro snapshot patch',text)
 def test_no_private_transfer(self):
  code=(ROOT/'scripts/macro_fetch.py').read_text();self.assertNotIn('Authorization',code);self.assertNotIn('secrets.',code)
 def test_final_csp(self):gate.gate.html_check((ROOT/'site/index.html').read_text())
BAD=[('extra_field',lambda d:d.update({'private_notes':'bad'})),('nan',lambda d:d['series'][0]['observations'][0].__setitem__(1,float('nan'))),('infinite',lambda d:d['series'][0]['observations'][0].__setitem__(1,float('inf'))),('bool',lambda d:d['series'][0]['observations'][0].__setitem__(1,True)),('future',lambda d:d['series'][0]['observations'][-1].__setitem__(0,'2099-01-01')),('duplicate',lambda d:d['series'][0]['observations'].append(d['series'][0]['observations'][-1])),('unknown_series',lambda d:d['series'][0].__setitem__('id','private')),('vix_data',lambda d:d['series'][4]['observations'].append(['2026-09-11',15.84])),('false_licence',lambda d:d['series'][4].__setitem__('status','available')),('too_short',lambda d:d['series'][0].__setitem__('observations',[['2026-09-11',4.96]])),('tampered_timestamp',lambda d:d['series'][0].__setitem__('fetched_at','2099-01-01T00:00:00Z')),('invalid_aux',lambda d:d['series'][0]['auxiliary'].update({'account':[]}))]
for name,mutate in BAD:
 def test(self,mutate=mutate):
  d=copy.deepcopy(DATA);mutate(d)
  with self.assertRaises((ValueError,KeyError,TypeError)):c.validate(d)
 setattr(MacroTests,'test_reject_'+name,test)
if __name__=='__main__':unittest.main()
