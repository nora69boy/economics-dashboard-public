import copy,html as html_lib,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import executive_overview as overview
import policy_events
import systemic_registry

class ExecutiveOverviewTests(unittest.TestCase):
 def test_render_uses_all_typed_policy_events(self):
  html=overview.render()
  self.assertEqual(html.count('data-exec-event='),4)
  for event in policy_events.EVENTS:
   self.assertIn(event['id'],html);self.assertIn(event['source_url'],html)
 def test_fact_and_inference_are_separate(self):
  html=overview.render();self.assertIn('FACT / Federal Reserve',html);self.assertIn('FACT / Bank of Japan',html);self.assertIn('FACT / SYSTEMIC IDENTITY REGISTRY',html);self.assertGreaterEqual(html.count('INFERENCE'),7)
 def test_registry_is_rendered_from_reviewed_records(self):
  html=overview.render();self.assertEqual(html.count('data-registry-index='),12);self.assertEqual(html.count('data-registry-company='),12)
  self.assertIn('12指数 + 12発行体を共通IDで管理',html);self.assertIn('Instruments</div><div class="metric">15</div>',html)
  for record in systemic_registry.INDEXES+systemic_registry.COMPANIES:
   self.assertIn(record['id'],html);self.assertIn(html_lib.escape(record['source_url'],quote=True),html)
 def test_registry_disclosure_rejects_ranking_interpretation(self):
  html=overview.render();self.assertIn('投資ランキングではありません',html);self.assertIn('identity metadata only',html)
  for bad in ['buy score','BUY SCORE','採点','勝者','投資推奨順位']:self.assertNotIn(bad,html)
 def test_systemic_map_uses_registry_issuer_names(self):
  html=overview.render()
  for name in ['NVIDIA','Broadcom','TSMC','SK hynix','Advantest','Tokyo Electron','NTT','MUFG','Rocket Lab']:self.assertIn(name,html)
 def test_scenarios_present_without_probabilities_or_buy_scores(self):
  html=overview.render()
  for label in ['BULL / INFERENCE','BASE / INFERENCE','BEAR / INFERENCE']:self.assertIn(label,html)
  for bad in ['buy score','BUY SCORE','採点','勝者']:self.assertNotIn(bad,html)
 def test_unverified_outcomes_are_not_completed(self):
  html=overview.render();self.assertEqual(html.count('結果未確認'),4);self.assertIn('Outcome verified</div><div class="metric">0</div>',html)
 def test_verified_count_changes_only_from_typed_state(self):
  values=list(copy.deepcopy(policy_events.EVENTS));values[0]['outcome_state']='outcome_verified';values[0]['outcome_verified_at']='2026-09-17T03:02:00+09:00'
  html=overview.render(tuple(values));self.assertIn('Outcome verified</div><div class="metric">1</div>',html);self.assertEqual(html.count('結果確認済み'),1)
 def test_apply_is_idempotent(self):
  source=overview.ANCHOR+'<p>existing</p></section>'
  once=overview.apply(source);twice=overview.apply(once);self.assertEqual(once,twice);self.assertEqual(once.count(overview.MARKER),1)
 def test_missing_anchor_fails_closed(self):
  with self.assertRaises(ValueError):overview.apply('<html></html>')

if __name__=='__main__':unittest.main()
