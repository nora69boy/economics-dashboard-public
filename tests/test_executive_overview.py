import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import executive_overview as overview
import policy_events

class ExecutiveOverviewTests(unittest.TestCase):
 def test_render_uses_all_typed_policy_events(self):
  html=overview.render()
  self.assertEqual(html.count('data-exec-event='),4)
  for event in policy_events.EVENTS:
   self.assertIn(event['id'],html);self.assertIn(event['source_url'],html)
 def test_fact_and_inference_are_separate(self):
  html=overview.render();self.assertIn('FACT / Federal Reserve',html);self.assertIn('FACT / Bank of Japan',html);self.assertGreaterEqual(html.count('INFERENCE'),6)
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
