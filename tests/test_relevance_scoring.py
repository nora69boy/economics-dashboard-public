import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import company_theme_expansion as expansion
import relationship_registry
import relevance_scoring as relevance

class RelevanceScoringTests(unittest.TestCase):
 def test_phase1_covers_all_21_relationships_once(self):
  meta=relevance.validate();self.assertEqual(meta['relationship_count'],21)
  expected={r['id'] for r in relationship_registry.RELATIONSHIPS+expansion.RELATIONSHIPS}
  self.assertEqual({r['relationship_id'] for r in relevance.hydrated_records()},expected)
  self.assertEqual((meta['immediate_count'],meta['active_count'],meta['watch_count'],meta['structural_count']),(8,11,1,1))
 def test_axes_are_independent_zero_to_five_not_total_score(self):
  for record in relevance.hydrated_records():
   for axis in relevance.AXES:self.assertIs(type(record[axis]),int);self.assertGreaterEqual(record[axis],0);self.assertLessEqual(record[axis],5)
   self.assertNotIn('priority_total',record);self.assertNotIn('probability',record);self.assertNotIn('recommendation',record)
 def test_evidence_strength_is_deterministic_from_grade(self):
  rels={r['id']:r for r in relationship_registry.RELATIONSHIPS+expansion.RELATIONSHIPS}
  for record in relevance.hydrated_records():self.assertEqual(record['evidence_strength'],relevance.EVIDENCE_STRENGTH[rels[record['relationship_id']]['evidence_grade']])
  self.assertEqual(relevance.by_relationship_id('rel-us-financial-sp500')['evidence_strength'],4)
  self.assertEqual(relevance.by_relationship_id('rel-ai-cloud-microsoft')['evidence_strength'],5)
 def test_active_policy_catalysts_require_urgency_five(self):
  for relationship_id in ('rel-fomc-policy-rate','rel-us-rate-financial-conditions','rel-us-financial-sp500','rel-us-financial-nasdaq100','rel-fomc-usd-channel','rel-boj-policy-rate','rel-boj-usdjpy','rel-usdjpy-topix'):
   self.assertEqual(relevance.by_relationship_id(relationship_id)['catalyst_urgency'],5)
 def test_structural_monitors_cannot_use_policy_maximum(self):
  for record in relevance.hydrated_records():
   if record['driver_ref'].startswith('monitor:'):self.assertLessEqual(record['catalyst_urgency'],4)
 def test_driver_must_cover_relationship(self):
  rows=list(copy.deepcopy(relevance.RECORDS));rows[0]['driver_ref']='monitor:monitor-space-launch-systems-2026'
  with self.assertRaisesRegex(ValueError,'driver does not cover relationship'):relevance.validate(tuple(rows))
 def test_evidence_strength_cannot_be_manually_promoted(self):
  rows=list(copy.deepcopy(relevance.RECORDS));rows[2]['evidence_strength']=5
  hydrated=relevance.hydrated_records(tuple(rows));self.assertEqual(hydrated[2]['evidence_strength'],4)
 def test_no_buy_score_or_investment_ranking_fields(self):
  text=relevance.canonical_dump().lower()
  for forbidden in ['buy_score','target_price','expected_return','position_size','priority_total','probability\":']:
   self.assertNotIn(forbidden,text)
  self.assertIn('not_investment_ranking',text)
 def test_canonical_dump_is_deterministic(self):
  first=relevance.canonical_dump();second=relevance.canonical_dump();self.assertEqual(first,second);self.assertEqual(json.loads(first)['metadata']['relationship_count'],21)

if __name__=='__main__':unittest.main()
