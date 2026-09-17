import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import phase3_feed_health as phase3
import phase3_rights
import publication_rights as rights

class MarketFeedHealthTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.text=(ROOT/'site/index.html').read_text();cls.macro=json.loads((ROOT/'site/data/macro.json').read_text())
 def test_phase3_visible_once(self):
  self.assertEqual(self.text.count(phase3.MARKER),1)
  self.assertIn('MARKET FEED HEALTH / DELIVERY ≠ FRESHNESS',self.text)
  self.assertIn('Delivery: 閲覧時に外部Providerへ接続',self.text)
 def test_provider_delivery_does_not_claim_verified_realtime(self):
  self.assertEqual(self.text.count('data-feed-delivery="provider_hosted"'),3)
  self.assertEqual(self.text.count('data-quote-mode="provider_determined"'),3)
  self.assertIn('real-time / delayed / EODはProvider・取引所条件で決まり、当ビルドは判定しません',self.text)
  self.assertNotIn('data-quote-mode="realtime"',self.text)
 def test_archive_never_auto_promoted(self):
  self.assertIn('Archiveへの自動fallbackもしません',self.text)
  self.assertIn('Archive snapshotは監査用',self.text)
 def test_macro_source_statuses_render_from_snapshot(self):
  for series in self.macro['series']:
   self.assertIn('data-macro-feed="'+series['id']+'" data-source-status="'+series['status']+'"',self.text)
 def test_wti_status_matches_snapshot(self):
  wti=next(s for s in self.macro['series'] if s['id']=='wti')
  self.assertIn('Last observation '+(wti['observations'][-1][0] if wti['observations'] else '--'),self.text)
 def test_apply_is_idempotent(self):self.assertEqual(phase3.apply(self.text,self.macro),self.text)
 def test_rights_normalizer_returns_reviewed_baseline(self):
  payload={p:(ROOT/'site'/p).read_bytes() for p in ['index.html','data/current-state.json','data/market.json','data/macro.json','data/macro-calendar.json','reports/2026-09-11-carry-forward.md']}
  normalized=phase3_rights.normalize_payload(payload)
  self.assertEqual(rights.shell_hash(normalized),rights.load_baseline()['html_shell_sha256'])
 def test_tampering_fails_closed(self):
  payload={p:(ROOT/'site'/p).read_bytes() for p in ['index.html','data/current-state.json','data/market.json','data/macro.json','data/macro-calendar.json','reports/2026-09-11-carry-forward.md']}
  bad=copy.copy(payload);bad['index.html']=payload['index.html'].replace(b'provider_determined',b'realtime',1)
  with self.assertRaises(rights.RightsError):phase3_rights.normalize_payload(bad)

if __name__=='__main__':unittest.main()
