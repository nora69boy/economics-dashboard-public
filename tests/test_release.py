"""Regressions for the actual v0.6 release and its public-data boundary."""
import copy,hashlib,io,json,math,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import macro_core as c,macro_fetch as fetch,check_release as gate,build_release
DATA=json.loads((ROOT/'site/data/macro.json').read_text());CAL=json.loads((ROOT/'site/data/macro-calendar.json').read_text())
class MacroTests(unittest.TestCase):
 def setUp(self):
  context=patch.dict(fetch.os.environ,{'GITHUB_OUTPUT':'','GITHUB_STEP_SUMMARY':''});context.start();self.addCleanup(context.stop)
  stdout=patch('sys.stdout',new=io.StringIO());stdout.start();self.addCleanup(stdout.stop)
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

class RefreshHardeningTests(unittest.TestCase):
 def setUp(self):
  context=patch.dict(fetch.os.environ,{'GITHUB_OUTPUT':'','GITHUB_STEP_SUMMARY':''});context.start();self.addCleanup(context.stop)
 def test_unchanged_history_is_accepted(self):
  fetch.ensure_continuity(copy.deepcopy(DATA['series'][0]), DATA['series'][0])
 def test_revised_values_are_accepted(self):
  before=DATA['series'][0];after=copy.deepcopy(before);after['observations'][-1][1]+=0.01
  fetch.ensure_continuity(after,before)
 def test_first_collection_is_accepted(self):
  fetch.ensure_continuity(DATA['series'][0],None)
 def test_dropped_latest_observation_is_rejected(self):
  before=DATA['series'][0];after=copy.deepcopy(before);after['observations'].pop()
  with self.assertRaises(ValueError):fetch.ensure_continuity(after,before)
 def test_dropped_earliest_observation_is_rejected(self):
  before=DATA['series'][0];after=copy.deepcopy(before);after['observations'].pop(0)
  with self.assertRaises(ValueError):fetch.ensure_continuity(after,before)
 def test_interior_hole_is_rejected(self):
  before=DATA['series'][0];after=copy.deepcopy(before);after['observations'].pop(100)
  with self.assertRaises(ValueError):fetch.ensure_continuity(after,before)
 def test_missing_auxiliary_is_rejected(self):
  before=DATA['series'][0];after=copy.deepcopy(before);after['auxiliary']={}
  with self.assertRaises(ValueError):fetch.ensure_continuity(after,before)
 def test_shortened_auxiliary_is_rejected(self):
  before=DATA['series'][0];after=copy.deepcopy(before);after['auxiliary']['ust2'].pop()
  with self.assertRaises(ValueError):fetch.ensure_continuity(after,before)
 def test_truncated_provider_response_retains_previous_timestamp(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'site/data').mkdir(parents=True);previous=root/'previous.json';previous.write_text(json.dumps(DATA));(root/'fx.raw').write_bytes(b'fixture')
   prior=next(s for s in DATA['series'] if s['id']=='usdjpy')
   with patch.object(fetch,'ROOT',root),patch.object(sys,'argv',['macro_fetch','--raw-dir',tmp,'--previous',str(previous)]),patch.object(fetch,'parse_fx',return_value=dict(prior['observations'][:-1])),patch.object(fetch,'download',side_effect=AssertionError('network')),patch('sys.stdout',new=io.StringIO()):
    fetch.main()
   after=next(s for s in json.loads((root/'site/data/macro.json').read_text())['series'] if s['id']=='usdjpy')
   self.assertEqual(after['status'],'retained');self.assertEqual(after['observations'],prior['observations']);self.assertEqual(after['fetched_at'],prior['fetched_at'])
 def test_snapshot_only_does_not_poll_providers_or_change_timestamp(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'site/data').mkdir(parents=True)
   with patch.object(fetch,'ROOT',root),patch.object(sys,'argv',['macro_fetch','--snapshot-only']),patch.object(fetch,'download',return_value=json.dumps(DATA).encode()) as get,patch('sys.stdout',new=io.StringIO()):
    fetch.main()
   get.assert_called_once_with(fetch.PUBLIC);self.assertEqual(json.loads((root/'site/data/macro.json').read_text()),DATA)
 def test_snapshot_only_requires_a_valid_fixture(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'site/data').mkdir(parents=True)
   with patch.object(fetch,'ROOT',root),patch.object(sys,'argv',['macro_fetch','--snapshot-only']),patch.object(fetch,'download',return_value=b'{}'),self.assertRaises(ValueError):fetch.main()
   self.assertFalse((root/'site/data/macro.json').exists())
 def test_snapshot_only_rejects_provider_capture_mode(self):
  with patch.object(sys,'argv',['macro_fetch','--snapshot-only','--raw-dir','unused']),self.assertRaises(ValueError):fetch.main()
 def download_failure(self,error,url=None,body=None,retry=False):
  opener=MagicMock();response=MagicMock();response.__enter__.return_value.read.return_value=b'valid'
  opener.open.side_effect=[error,response]
  with patch.object(fetch.urllib.request,'build_opener',return_value=opener),patch.object(fetch.time,'sleep') as sleep:
   if retry:self.assertEqual(fetch.download(url or fetch.FX,body),b'valid')
   else:
    with self.assertRaises(type(error)):fetch.download(url or fetch.FX,body)
  self.assertEqual(opener.open.call_count,2 if retry else 1);self.assertEqual(sleep.call_count,1 if retry else 0)
 def test_transient_get_network_error_retries_once(self):
  self.download_failure(fetch.urllib.error.URLError('unavailable'),retry=True)
 def test_transient_get_server_error_retries_once(self):
  self.download_failure(fetch.urllib.error.HTTPError(fetch.FX,503,'unavailable',{},None),retry=True)
 def test_get_timeout_retries_once(self):
  self.download_failure(TimeoutError('timeout'),retry=True)
 def test_bls_post_is_not_retried(self):
  self.download_failure(fetch.urllib.error.URLError('unavailable'),fetch.BLS,{'seriesid':list(fetch.BLS_IDS)})
 def test_rate_limit_is_not_retried(self):
  self.download_failure(fetch.urllib.error.HTTPError(fetch.FX,429,'limited',{},None))
 def test_forbidden_is_not_retried(self):
  self.download_failure(fetch.urllib.error.HTTPError(fetch.FX,403,'forbidden',{},None))
 def test_repeated_network_failure_stops_after_two_attempts(self):
  opener=MagicMock();opener.open.side_effect=fetch.urllib.error.URLError('unavailable')
  with patch.object(fetch.urllib.request,'build_opener',return_value=opener),patch.object(fetch.time,'sleep'),self.assertRaises(fetch.urllib.error.URLError):fetch.download(fetch.FX)
  self.assertEqual(opener.open.call_count,2)
 def test_atomic_replace_failure_preserves_old_file(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'site/data').mkdir(parents=True);dest=root/'site/data/macro.json';dest.write_text('old')
   with patch.object(fetch,'ROOT',root),patch.object(Path,'replace',side_effect=OSError('failure')),self.assertRaises(OSError):fetch.write_snapshot(DATA)
   self.assertEqual(dest.read_text(),'old');self.assertFalse(dest.with_suffix('.json.tmp').exists())
 def test_invalid_data_never_overwrites_file(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'site/data').mkdir(parents=True);dest=root/'site/data/macro.json';dest.write_text('old')
   with patch.object(fetch,'ROOT',root),self.assertRaises(ValueError):fetch.write_snapshot({})
   self.assertEqual(dest.read_text(),'old')
 def test_healthy_report_does_not_treat_vix_as_failure(self):
  with patch('sys.stdout',new=io.StringIO()) as output:fetch.emit_status(DATA)
  self.assertEqual(json.loads(output.getvalue())['refresh_health'],'fresh')
 def test_degraded_report_and_ci_summary(self):
  data=copy.deepcopy(DATA);data['series'][0]['status']='retained'
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'output';summary=Path(tmp)/'summary'
   with patch.dict(fetch.os.environ,{'GITHUB_OUTPUT':str(output),'GITHUB_STEP_SUMMARY':str(summary)}),patch('sys.stdout',new=io.StringIO()) as log:fetch.emit_status(data)
   self.assertEqual(output.read_text(),'refresh_health=degraded\n');self.assertIn('Last observation',summary.read_text());self.assertIn(data['series'][0]['fetched_at'],summary.read_text());self.assertIn('::warning::Macro source ust10',log.getvalue())
 def test_fixture_report_is_not_a_successful_refresh(self):
  with patch('sys.stdout',new=io.StringIO()) as output:fetch.emit_status(DATA,'fixture')
  self.assertEqual(json.loads(output.getvalue())['refresh_health'],'fixture')
 def test_six_hour_workflow_and_post_deploy_health(self):
  workflow=(ROOT/'.github/workflows/pages.yml').read_text()
  self.assertIn("cron: '17 4,10,16,22 * * *'",workflow)
  self.assertIn('run: python3 scripts/macro_fetch.py --snapshot-only',workflow)
  self.assertIn('needs: [validate, deploy]',workflow)
  self.assertIn('REFRESH_HEALTH: ${{ needs.validate.outputs.refresh_health }}',workflow)
  self.assertNotIn('contents: write',workflow)

if __name__=='__main__':unittest.main()
