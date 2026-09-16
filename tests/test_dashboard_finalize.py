"""Regression tests for the final public dashboard presentation layer."""
import copy,hashlib,json,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import dashboard_finalize
import presentation_rights
import publication_rights as rights

class DashboardFinalizeTests(unittest.TestCase):
 def setUp(self):self.text=(ROOT/'site/index.html').read_text()
 def payload(self):return {name:(ROOT/'site'/name).read_bytes() for name in rights.TARGETS}
 def test_health_panel_is_embedded(self):
  self.assertIn('data-dashboard-health="true"',self.text);self.assertIn('DASHBOARD HEALTH / CURRENT BUILD',self.text);self.assertIn('BROWSER QA',self.text)
 def test_market_primary_label_is_provider_hosted_not_build_verified_live(self):
  self.assertIn('MARKET / PROVIDER-HOSTED',self.text);self.assertIn('TradingView provider-hosted（配信応答はビルド未検証）',self.text);self.assertNotIn('MARKET LIVE / PROVIDER-HOSTED',self.text);self.assertNotIn('ARCHIVE SNAPSHOT /',self.text)
 def test_market_health_separates_delivery_from_quote_observation(self):
  self.assertIn('<div class="metric pending">PROVIDER-HOSTED</div>',self.text)
  self.assertIn('表示価格の到達・鮮度は当ビルドでは検証しません',self.text)
  self.assertNotIn('<div class="metric good">LIVE VIEW</div>',self.text)
 def test_release_metadata_matches_current_behavior(self):
  self.assertIn('v0.6.0 / 公開版 / MARKET PROVIDER-HOSTED + MACRO AUTO REFRESH',self.text)
  self.assertNotIn('v0.4.0 / 2026-09-13 / 世界指数・株価分析',self.text)
  self.assertIn('株価・指数: TradingView provider-hosted（価格応答は未検証） / マクロ: 1日4回更新 / カレンダー: Source Healthを確認',self.text)
  self.assertNotIn('日程確認：2026-09-13 / 自動更新ではありません',self.text)
 def test_public_presence_and_visual_visibility_are_separate(self):
  self.assertIn('data-market-publication-state="true"',self.text)
  self.assertIn('旧自己ホスト市場データ: 公開HTML内に保持 / 画面非表示 / 現在値判断には不使用。',self.text)
 def test_static_event_note_distinguishes_reviewed_fixture_from_live_calendar(self):
  self.assertIn('このタブの固定8件は2026-09-13レビュー時点。最新の日程確認は「マクロ」の経済カレンダー / Source Healthを参照。',self.text)
  self.assertNotIn('2026年9月13日に公式掲載日程を確認。変更される場合があります。',self.text)
 def test_frontend_connection_note_matches_tradingview_exception(self):
  self.assertIn('TradingView公式Widgetの許可済み接続を除き、任意の外部接続とフォーム送信をCSPで禁止しています。',self.text)
  self.assertNotIn('外部接続とフォーム送信を禁止するブラウザ設定を入れています。',self.text)
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
 def test_operational_state_matches_current_publication_boundary(self):
  macro=json.loads((ROOT/'site/data/macro.json').read_text());market=json.loads((ROOT/'site/data/market.json').read_text());state=dashboard_finalize.operational_state(macro,market,dashboard_finalize.calendar_report(self.text))
  self.assertEqual(state['schema_version'],'0.7-draft1')
  self.assertEqual(state['market']['delivery_mode'],'provider_hosted')
  self.assertEqual(state['market']['quote_observation'],'not_observed_by_build')
  self.assertFalse(state['market']['data_persisted'])
  self.assertEqual(state['publication']['legacy_market_public_presence'],'published')
  self.assertEqual(state['publication']['legacy_market_visibility'],'hidden')
  self.assertFalse(state['publication']['use_legacy_market_for_current_decisions'])
 def test_reviewed_presentation_normalizes_to_baseline_shell(self):
  normalized=presentation_rights.normalize_payload(self.payload());self.assertEqual(rights.shell_hash(normalized),rights.load_baseline()['html_shell_sha256'])
 def test_presentation_normalizer_rejects_health_tampering(self):
  payload=self.payload();payload=copy.copy(payload);payload['index.html']=payload['index.html'].replace(b'>PROVIDER-HOSTED<',b'>PROVIDER-HOSTED TAMPERED<',1)
  with self.assertRaises(rights.RightsError):presentation_rights.normalize_payload(payload)
 def test_presentation_normalizer_rejects_publication_state_tampering(self):
  payload=self.payload();payload=copy.copy(payload);payload['index.html']=payload['index.html'].replace(b'data-market-publication-state="true"',b'data-market-publication-state="tampered"',1)
  with self.assertRaises(rights.RightsError):presentation_rights.normalize_payload(payload)
 def test_presentation_normalizer_rejects_wrapper_tampering(self):
  payload=self.payload();payload=copy.copy(payload);payload['index.html']=payload['index.html'].replace(b'data-market-legacy="true" hidden aria-hidden="true"',b'data-market-legacy="true" aria-hidden="true"',1)
  with self.assertRaises(rights.RightsError):presentation_rights.normalize_payload(payload)
 def test_presentation_normalizer_rejects_release_metadata_tampering(self):
  payload=self.payload();payload=copy.copy(payload);payload['index.html']=payload['index.html'].replace(b'MARKET PROVIDER-HOSTED + MACRO AUTO REFRESH',b'MARKET UNREVIEWED',1)
  with self.assertRaises(rights.RightsError):presentation_rights.normalize_payload(payload)
 def test_presentation_normalizer_rejects_executive_overview_tampering(self):
  payload=self.payload();payload=copy.copy(payload);original=b'Issuer coverage</div><div class="metric">12/12';tampered=b'Issuer coverage</div><div class="metric">13/12';self.assertIn(original,payload['index.html']);payload['index.html']=payload['index.html'].replace(original,tampered,1)
  with self.assertRaises(rights.RightsError):presentation_rights.normalize_payload(payload)

if __name__=='__main__':unittest.main()
