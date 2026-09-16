import copy,html as html_lib,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import company_theme_expansion as expansion
import executive_overview as overview
import policy_events
import relationship_registry
import systemic_registry

class ExecutiveOverviewTests(unittest.TestCase):
 def test_render_uses_all_typed_policy_events(self):
  html=overview.render();self.assertEqual(html.count('data-exec-event='),4)
  for event in policy_events.EVENTS:self.assertIn(event['id'],html);self.assertIn(event['source_url'],html)
 def test_fact_and_inference_are_separate(self):
  html=overview.render();self.assertIn('FACT / Federal Reserve',html);self.assertIn('FACT / Bank of Japan',html);self.assertIn('FACT / SYSTEMIC IDENTITY REGISTRY',html);self.assertIn('FACT + INFERENCE / RELATIONSHIP REGISTRY',html);self.assertIn('FACT + INFERENCE / COMPANY &amp; THEME EXPANSION',html);self.assertGreaterEqual(html.count('INFERENCE'),12)
 def test_registry_is_rendered_from_reviewed_records(self):
  html=overview.render();self.assertEqual(html.count('data-registry-index='),12);self.assertEqual(html.count('data-registry-company='),12)
  self.assertIn('12指数 + 12発行体を共通IDで管理',html);self.assertIn('Instruments</div><div class="metric">15</div>',html)
  for record in systemic_registry.INDEXES+systemic_registry.COMPANIES:self.assertIn(record['id'],html);self.assertIn(html_lib.escape(record['source_url'],quote=True),html)
 def test_relationship_registry_is_rendered_from_reviewed_records(self):
  html=overview.render();self.assertEqual(html.count('data-relationship='),14);self.assertEqual(html.count('data-catalyst='),3)
  self.assertIn('Event → Macro → Index → Issuer の根拠付き接続',html);self.assertIn('FACT</div><div class="metric">10</div>',html);self.assertIn('INFERENCE</div><div class="metric">4</div>',html)
  for rel in relationship_registry.RELATIONSHIPS:
   self.assertIn(rel['id'],html);self.assertIn(html_lib.escape(rel['source_url'],quote=True),html);self.assertIn(rel['invalidation'],html)
 def test_company_theme_expansion_is_rendered_from_reviewed_records(self):
  html=overview.render();self.assertEqual(html.count('data-company-theme-relationship='),7);self.assertEqual(html.count('data-company-theme-monitor='),5)
  self.assertIn('data-company-theme-expansion="true"',html);self.assertIn('12/12 seed issuers をEvidence Graphへ接続',html);self.assertIn('Evidence relationships</div><div class="metric">21</div>',html)
  self.assertIn('Seed coverage</div><div class="metric">12/12</div>',html);self.assertIn('Expansion FACT</div><div class="metric">7</div>',html);self.assertIn('Themes</div><div class="metric">4</div>',html);self.assertIn('Monitors</div><div class="metric">5</div>',html)
  for rel in expansion.RELATIONSHIPS:
   self.assertIn(rel['id'],html);self.assertIn(html_lib.escape(rel['source_url'],quote=True),html);self.assertIn(rel['invalidation'],html)
  for monitor in expansion.MONITORS:self.assertIn(monitor['id'],html);self.assertIn(monitor['invalidation'],html)
 def test_expansion_covers_all_seven_previously_unconnected_issuers(self):
  html=overview.render()
  for name in ['Microsoft Corporation','Alphabet Inc.','Amazon.com, Inc.','Broadcom Inc.','Mitsubishi UFJ Financial Group, Inc.','NTT, Inc.','Rocket Lab Corporation']:self.assertIn(name,html)
 def test_relationship_disclosure_rejects_causality_and_ranking_shortcut(self):
  html=overview.render();self.assertIn('Relationshipは因果を自動認定しません',html);self.assertIn('投資ランキングではありません',html);self.assertIn('coverage ≠ ranking',html);self.assertIn('MONITORは売買シグナルではなく',html)
  for bad in ['buy score','BUY SCORE','採点','勝者','投資推奨順位']:self.assertNotIn(bad,html)
 def test_policy_catalysts_are_pending_until_typed_outcome_verification(self):
  html=overview.render();self.assertEqual(html.count('結果確認待ち'),2);self.assertGreaterEqual(html.count('構造監視中'),6)
  values=list(copy.deepcopy(policy_events.EVENTS));values[0]['outcome_state']='outcome_verified';values[0]['outcome_verified_at']='2026-09-17T03:02:00+09:00'
  html2=overview.render(tuple(values));self.assertEqual(html2.count('結果確認済み / 監視中'),1);self.assertEqual(html2.count('結果確認待ち'),1)
 def test_registry_disclosure_rejects_ranking_interpretation(self):
  html=overview.render();self.assertIn('投資ランキングではありません',html);self.assertIn('identity metadata only',html)
  for bad in ['buy score','BUY SCORE','採点','勝者','投資推奨順位']:self.assertNotIn(bad,html)
 def test_systemic_map_uses_registry_issuer_names(self):
  html=overview.render()
  for name in ['NVIDIA','TSMC','SK hynix','Advantest','Tokyo Electron','Microsoft','Alphabet','Amazon','Broadcom','MUFG','NTT','Rocket Lab']:self.assertIn(name,html)
 def test_scenarios_present_without_probabilities_or_buy_scores(self):
  html=overview.render()
  for label in ['BULL / INFERENCE','BASE / INFERENCE','BEAR / INFERENCE']:self.assertIn(label,html)
  for bad in ['buy score','BUY SCORE','採点','勝者']:self.assertNotIn(bad,html)
 def test_unverified_outcomes_are_not_completed(self):
  html=overview.render();self.assertEqual(html.count('結果未確認'),4);self.assertIn('Outcome verified</div><div class="metric">0</div>',html)
 def test_verified_count_changes_only_from_typed_state(self):
  values=list(copy.deepcopy(policy_events.EVENTS));values[0]['outcome_state']='outcome_verified';values[0]['outcome_verified_at']='2026-09-17T03:02:00+09:00'
  html=overview.render(tuple(values));self.assertIn('Outcome verified</div><div class="metric">1</div>',html)
  self.assertEqual(html.count('<span class="tag good">結果確認済み</span>'),1);self.assertEqual(html.count('結果確認済み / 監視中'),1)
 def test_apply_is_idempotent(self):
  source=overview.ANCHOR+'<p>existing</p></section>';once=overview.apply(source);twice=overview.apply(once);self.assertEqual(once,twice);self.assertEqual(once.count(overview.MARKER),1)
 def test_missing_anchor_fails_closed(self):
  with self.assertRaises(ValueError):overview.apply('<html></html>')

if __name__=='__main__':unittest.main()
