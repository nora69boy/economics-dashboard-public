import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import policy_events
import relationship_registry as registry

class RelationshipRegistryTests(unittest.TestCase):
 def test_phase1_cardinality_and_claim_split(self):
  meta=registry.validate()
  self.assertEqual(meta['relationship_count'],14);self.assertEqual(meta['fact_count'],10);self.assertEqual(meta['inference_count'],4)
  self.assertEqual(meta['catalyst_count'],3);self.assertEqual(meta['confirm_required_count'],0)
  self.assertEqual(meta['publication_scope'],'evidence_backed_relationships_only')
 def test_fact_requires_grade_a(self):
  rels=list(copy.deepcopy(registry.RELATIONSHIPS));rels[0]['evidence_grade']='B'
  with self.assertRaisesRegex(ValueError,'fact requires grade A'):registry.validate(relationships=tuple(rels))
 def test_unknown_reference_is_rejected(self):
  rels=list(copy.deepcopy(registry.RELATIONSHIPS));rels[0]['target_ref']='company:company-unknown'
  with self.assertRaisesRegex(ValueError,'unknown relationship ref'):registry.validate(relationships=tuple(rels))
 def test_inference_requires_invalidation(self):
  rels=list(copy.deepcopy(registry.RELATIONSHIPS));i=next(i for i,r in enumerate(rels) if r['claim_type']=='INFERENCE');rels[i]['invalidation']=''
  with self.assertRaisesRegex(ValueError,'inference requires invalidation'):registry.validate(relationships=tuple(rels))
 def test_grade_c_cannot_be_publishable(self):
  rels=list(copy.deepcopy(registry.RELATIONSHIPS));i=next(i for i,r in enumerate(rels) if r['claim_type']=='INFERENCE');rels[i]['evidence_grade']='C'
  with self.assertRaisesRegex(ValueError,'grade C must require confirmation'):registry.validate(relationships=tuple(rels))
 def test_unresolved_fact_cannot_publish_as_fact(self):
  rels=list(copy.deepcopy(registry.RELATIONSHIPS));rels[0]['publication_state']='confirm_required'
  with self.assertRaisesRegex(ValueError,'unresolved fact cannot publish as fact'):registry.validate(relationships=tuple(rels))
 def test_future_source_publication_is_rejected(self):
  rels=list(copy.deepcopy(registry.RELATIONSHIPS));rels[0]['source_published_at']='2027-01-01'
  with self.assertRaisesRegex(ValueError,'source published after verification'):registry.validate(relationships=tuple(rels))
 def test_undated_evergreen_primary_source_is_explicit(self):
  rel=registry.by_id('rel-us-rate-financial-conditions');self.assertIsNone(rel['source_published_at']);self.assertEqual(rel['verified_at'],'2026-09-16')
 def test_ai_semiconductor_fact_links_use_primary_evidence(self):
  ids={'rel-ai-demand-tsmc','rel-ai-demand-skhynix','rel-ai-demand-advantest','rel-ai-demand-tel','rel-nvidia-tsmc','rel-nvidia-skhynix'}
  for ident in ids:
   rel=registry.by_id(ident);self.assertEqual(rel['claim_type'],'FACT');self.assertEqual(rel['evidence_grade'],'A');self.assertTrue(rel['source_url'].startswith('https://'))
 def test_no_investment_scoring_semantics(self):
  forbidden={'price','target_price','probability','buy_score','score','recommendation','position_size','ranking'}
  def keys(value):
   if isinstance(value,dict):
    for k,v in value.items():yield k;yield from keys(v)
   elif isinstance(value,(tuple,list)):
    for v in value:yield from keys(v)
  self.assertFalse(forbidden.intersection(keys((registry.RELATIONSHIPS,registry.CATALYSTS))))
 def test_policy_catalysts_wait_for_verified_outcome(self):
  fomc=next(c for c in registry.CATALYSTS if c['id']=='catalyst-fomc-2026-09')
  boj=next(c for c in registry.CATALYSTS if c['id']=='catalyst-boj-2026-09')
  self.assertEqual(registry.catalyst_state(fomc),'pending_outcome_verification');self.assertEqual(registry.catalyst_state(boj),'pending_outcome_verification')
  events=list(copy.deepcopy(policy_events.EVENTS));events[0]['outcome_state']='outcome_verified';events[0]['outcome_verified_at']='2026-09-17T03:02:00+09:00'
  self.assertEqual(registry.catalyst_state(fomc,tuple(events)),'outcome_verified_monitoring')
 def test_structural_ai_catalyst_is_monitoring_not_trade_signal(self):
  ai=next(c for c in registry.CATALYSTS if c['id']=='catalyst-ai-semi-demand-2026q3')
  self.assertEqual(registry.catalyst_state(ai),'monitoring');self.assertEqual(ai['claim_type'],'INFERENCE');self.assertIn('primary-source',ai['activation_rule'])
 def test_catalyst_cannot_reference_unknown_relationship(self):
  catalysts=list(copy.deepcopy(registry.CATALYSTS));catalysts[0]['relationship_ids']=tuple(catalysts[0]['relationship_ids'])+('rel-unknown',)
  with self.assertRaisesRegex(ValueError,'catalyst relationships'):registry.validate(catalysts=tuple(catalysts))

if __name__=='__main__':unittest.main()
