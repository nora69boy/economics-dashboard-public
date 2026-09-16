import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import phase2_overview as phase2
import phase2_rights
import presentation_rights
import publication_rights as rights

class Phase2OverviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.text=(ROOT/'site/index.html').read_text()
 def test_phase2_is_visible_and_complete(self):
  self.assertEqual(self.text.count(phase2.MARKER),1);self.assertEqual(self.text.count('data-relevance-score='),21)
  for label,count in [('Immediate',8),('Active',11),('Watch',1),('Structural',1)]:self.assertIn(label+'</div><div class="metric">'+str(count)+'</div>',self.text)
  self.assertIn('Market Impact',self.text);self.assertIn('Catalyst Urgency',self.text);self.assertIn('Evidence Strength',self.text)
  self.assertIn('買いシグナルではありません',self.text);self.assertNotIn('priority_total',self.text)
 def test_current_overview_uses_provider_hosted_market_semantics(self):
  self.assertIn('LIVE MARKET / PROVIDER-HOSTED',self.text);self.assertIn('TradingView Widgetが閲覧時に配信',self.text)
  self.assertNotIn("価格の最終収録は '+D.as_of+'",self.text);self.assertNotIn("pct(ret(a))+' / 9.8 - 9.10'",self.text)
  self.assertIn('世界指数 LIVE',self.text);self.assertIn('主要株・ETF LIVE',self.text);self.assertIn('政策反応 LIVE',self.text)
 def test_archive_comparison_is_explicit(self):
  self.assertIn('REVIEWED ARCHIVE / COMPARE & SCREEN',self.text);self.assertIn('監査用固定スナップショットの比較',self.text)
 def test_runtime_preserves_executive_overview(self):
  self.assertIn("homeExecutive=home.querySelector('[data-v07-executive-overview]')",self.text);self.assertIn('if(homeExecutive)home.append(homeExecutive)',self.text)
 def test_apply_is_idempotent(self):self.assertEqual(phase2.apply(self.text),self.text)
 def test_rights_normalizer_returns_reviewed_baseline(self):
  payload={p:(ROOT/'site'/p).read_bytes() for p in ['index.html','data/current-state.json','data/market.json','data/macro.json','data/macro-calendar.json','reports/2026-09-11-carry-forward.md']}
  normalized=phase2_rights.normalize_payload(payload)
  self.assertEqual(rights.shell_hash(normalized),rights.load_baseline()['html_shell_sha256'])
 def test_tampering_fails_closed(self):
  payload={p:(ROOT/'site'/p).read_bytes() for p in ['index.html','data/current-state.json','data/market.json','data/macro.json','data/macro-calendar.json','reports/2026-09-11-carry-forward.md']}
  bad=copy.copy(payload);bad['index.html']=payload['index.html'].replace(b'Market Impact 5/5',b'Market Impact 1/5',1)
  with self.assertRaises(rights.RightsError):phase2_rights.normalize_payload(bad)

if __name__=='__main__':unittest.main()
