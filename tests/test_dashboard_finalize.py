"""Regression tests for the final public dashboard presentation layer."""
import copy,hashlib,json,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import presentation_rights
import publication_rights as rights

class DashboardFinalizeTests(unittest.TestCase):
 def setUp(self):self.text=(ROOT/'site/index.html').read_text()
 def payload(self):return {name:(ROOT/'site'/name).read_bytes() for name in rights.TARGETS}
 def test_health_panel_is_embedded(self):
  self.assertIn('data-dashboard-health="true"',self.text);self.assertIn('DASHBOARD HEALTH / CURRENT BUILD',self.text);self.assertIn('BROWSER QA',self.text)
 def test_market_primary_label_is_live(self):
  self.assertIn('MARKET LIVE / PROVIDER-HOSTED',self.text);self.assertIn('株価・指数: TradingView live',self.text);self.assertNotIn('ARCHIVE SNAPSHOT /',self.text);self.assertNotIn('株価・指数: 2026-09-10固定',self.text)
 def test_legacy_market_is_hidden_but_retained(self):
  self.assertEqual(self.text.count('data-market-legacy="true" hidden'),2);self.assertEqual(self.text.count('data-market-archive="true"'),2);self.assertIn('旧自己ホスト市場データは監査用に内部保持',self.text);self.assertIn('2026-09-10以前の固定値は通常表示から除外しました',self.text);self.assertIn('data-global-symbol="SPX"',self.text);self.assertIn('data-asset="NVDA"',self.text)
 def test_live_widgets_remain_primary(self):
  self.assertEqual(self.text.count('data-rights-shell="live-market-'),2);self.assertEqual(self.text.count('https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js'),3)
 def test_no_visible_fixed_snapshot_before_legacy_wrappers(self):
  for panel,next_panel in [('world','market'),('market','events')]:
   start=self.text.index(f'<section class="panel" id="{panel}"');end=self.text.index(f'<section class="panel" id="{next_panel}"',start);segment=self.text[start:end];legacy=segment.index('data-market-legacy="true" hidden');visible=segment[:legacy]
   self.assertNotIn('2026-09-10固定値',visible);self.assertNotIn('最終収録値',visible)
 def test_manifest_tracks_finalized_index(self):
  manifest=json.loads((ROOT/'site/manifest.json').read_text());actual=hashlib.sha256((ROOT/'site/index.html').read_bytes()).hexdigest();self.assertEqual(manifest['files']['index.html'],actual)
 def test_reviewed_presentation_normalizes_to_baseline_shell(self):
  normalized=presentation_rights.normalize_payload(self.payload());self.assertEqual(rights.shell_hash(normalized),rights.load_baseline()['html_shell_sha256'])
 def test_presentation_normalizer_rejects_health_tampering(self):
  payload=self.payload();payload=copy.copy(payload);payload['index.html']=payload['index.html'].replace(b'>LIVE VIEW<',b'>LIVE VIEW TAMPERED<',1)
  with self.assertRaises(rights.RightsError):presentation_rights.normalize_payload(payload)
 def test_presentation_normalizer_rejects_wrapper_tampering(self):
  payload=self.payload();payload=copy.copy(payload);payload['index.html']=payload['index.html'].replace(b'data-market-legacy="true" hidden aria-hidden="true"',b'data-market-legacy="true" aria-hidden="true"',1)
  with self.assertRaises(rights.RightsError):presentation_rights.normalize_payload(payload)

if __name__=='__main__':unittest.main()
