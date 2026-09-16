import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import systemic_registry as registry

class SystemicRegistryTests(unittest.TestCase):
 def test_phase1_cardinality_and_identity_only_scope(self):
  meta=registry.validate()
  self.assertEqual(meta['index_count'],12);self.assertEqual(meta['company_count'],12);self.assertEqual(meta['instrument_count'],15)
  self.assertEqual(meta['publication_scope'],'identity_metadata_only')
  self.assertEqual(meta['selection_basis'],'architecture_seed_not_investment_ranking')
 def test_all_records_use_grade_a_primary_identity_sources(self):
  for record in registry.INDEXES+registry.COMPANIES:
   self.assertEqual(record['evidence_grade'],'A');self.assertEqual(record['verified_at'],'2026-09-16');self.assertTrue(record['source_url'].startswith('https://'))
 def test_no_market_values_scores_or_recommendations(self):
  forbidden={'price','index_level','market_cap','weight','revenue','earnings','valuation','score','recommendation','position_size','probability'}
  def keys(value):
   if isinstance(value,dict):
    for k,v in value.items():yield k;yield from keys(v)
   elif isinstance(value,(tuple,list)):
    for v in value:yield from keys(v)
  self.assertFalse(forbidden.intersection(keys(registry.INDEXES+registry.COMPANIES)))
 def test_issuer_dedupe_for_share_classes_and_adrs(self):
  self.assertEqual(registry.issuer_for_instrument('NASDAQ','GOOGL'),'company-alphabet')
  self.assertEqual(registry.issuer_for_instrument('NASDAQ','GOOG'),'company-alphabet')
  self.assertEqual(registry.issuer_for_instrument('TWSE','2330'),'company-tsmc')
  self.assertEqual(registry.issuer_for_instrument('NYSE','TSM'),'company-tsmc')
  self.assertEqual(registry.issuer_for_instrument('TSE_PRIME','6857'),'company-advantest')
  self.assertEqual(registry.issuer_for_instrument('US_OTC_ADR','ATEYY'),'company-advantest')
 def test_duplicate_instrument_across_issuers_is_rejected(self):
  companies=list(copy.deepcopy(registry.COMPANIES));companies[1]['canonical_instrument']=copy.deepcopy(companies[0]['canonical_instrument'])
  with self.assertRaises(ValueError):registry.validate(companies=tuple(companies))
 def test_duplicate_issuer_group_is_rejected(self):
  companies=list(copy.deepcopy(registry.COMPANIES));companies[1]['dedupe_group']=companies[0]['dedupe_group']
  with self.assertRaises(ValueError):registry.validate(companies=tuple(companies))
 def test_unknown_instrument_does_not_guess(self):
  self.assertIsNone(registry.issuer_for_instrument('NASDAQ','UNKNOWN'))
  with self.assertRaises(KeyError):registry.by_id('company-unknown')

if __name__=='__main__':unittest.main()
