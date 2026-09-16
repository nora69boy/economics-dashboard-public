import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import company_theme_expansion as expansion
import relationship_registry
import systemic_registry

class CompanyThemeExpansionTests(unittest.TestCase):
 def test_phase1_cardinality_and_full_seed_coverage(self):
  meta=expansion.validate()
  self.assertEqual(meta['theme_count'],4);self.assertEqual(meta['relationship_count'],7);self.assertEqual(meta['monitor_count'],5)
  self.assertEqual(meta['seed_company_coverage'],12);self.assertEqual(expansion.missing_company_ids(),())
 def test_expansion_targets_exactly_previously_uncovered_issuers(self):
  base=expansion._company_refs(relationship_registry.RELATIONSHIPS)
  expected={c['id'] for c in systemic_registry.COMPANIES}-base
  actual={r['target_ref'].split(':',1)[1] for r in expansion.RELATIONSHIPS}
  self.assertEqual(actual,expected)
  self.assertEqual(actual,{'company-microsoft','company-alphabet','company-amazon','company-broadcom','company-mufg','company-ntt','company-rocket-lab'})
 def test_all_expansion_claims_are_grade_a_facts_with_primary_https_sources(self):
  for rel in expansion.RELATIONSHIPS:
   self.assertEqual(rel['claim_type'],'FACT');self.assertEqual(rel['evidence_grade'],'A');self.assertEqual(rel['publication_state'],'publishable')
   self.assertTrue(rel['source_url'].startswith('https://'));self.assertEqual(rel['verified_at'],'2026-09-17')
 def test_unknown_reference_is_rejected(self):
  rels=list(copy.deepcopy(expansion.RELATIONSHIPS));rels[0]['source_ref']='theme:theme-does-not-exist'
  with self.assertRaisesRegex(ValueError,'unknown relationship ref'):expansion.validate(relationships=tuple(rels))
 def test_fact_cannot_be_downgraded_to_inference_or_grade_b(self):
  rels=list(copy.deepcopy(expansion.RELATIONSHIPS));rels[0]['claim_type']='INFERENCE'
  with self.assertRaisesRegex(ValueError,'expansion facts require grade A'):expansion.validate(relationships=tuple(rels))
  rels=list(copy.deepcopy(expansion.RELATIONSHIPS));rels[0]['evidence_grade']='B'
  with self.assertRaisesRegex(ValueError,'expansion facts require grade A'):expansion.validate(relationships=tuple(rels))
 def test_future_source_date_is_rejected(self):
  rels=list(copy.deepcopy(expansion.RELATIONSHIPS));rels[0]['source_published_at']='2027-01-01'
  with self.assertRaisesRegex(ValueError,'source date after verification'):expansion.validate(relationships=tuple(rels))
 def test_already_covered_issuer_cannot_replace_uncovered_target(self):
  rels=list(copy.deepcopy(expansion.RELATIONSHIPS));rels[0]['target_ref']='company:company-nvidia'
  with self.assertRaisesRegex(ValueError,'phase1 expansion duplicates already-covered issuer'):expansion.validate(relationships=tuple(rels))
 def test_monitor_cannot_reference_unknown_relationship(self):
  monitors=list(copy.deepcopy(expansion.MONITORS));monitors[0]['relationship_ids']=tuple(monitors[0]['relationship_ids'])+('rel-unknown',)
  with self.assertRaisesRegex(ValueError,'monitor relationship refs'):expansion.validate(monitors=tuple(monitors))
 def test_monitors_are_inference_not_trade_signals(self):
  for monitor in expansion.MONITORS:
   self.assertEqual(monitor['claim_type'],'INFERENCE');self.assertTrue(monitor['invalidation']);self.assertTrue(monitor['activation_rule'])
  self.assertIn('not a directional stock signal',next(m for m in expansion.MONITORS if m['id']=='monitor-jp-rate-mufg-fy26')['activation_rule'])
 def test_no_investment_scoring_semantics(self):
  forbidden={'price','target_price','probability','buy_score','score','recommendation','position_size','ranking'}
  self.assertFalse(forbidden.intersection(expansion._walk_keys((expansion.RELATIONSHIPS,expansion.MONITORS))))
 def test_canonical_dump_is_deterministic_and_valid_json(self):
  first=expansion.canonical_dump();second=expansion.canonical_dump();self.assertEqual(first,second)
  import json
  payload=json.loads(first);self.assertEqual(payload['metadata']['seed_company_coverage'],12)

if __name__=='__main__':unittest.main()
