import copy,json,sys,unittest
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import market_refresh_guard as g
REG=json.loads((ROOT/'data-rights/registry.json').read_text());MARKET=json.loads((ROOT/'site/data/market.json').read_text())

def approve(reg,ids):
 for e in reg['datasets']:
  if e['id'] in ids:
   e['status']='APPROVED';e['valid_from']='2026-01-01';e['valid_until']='2026-12-31';e['review_due_at']='2026-12-31';e['terms_url']=['https://example.invalid/terms'];e['evidence']=[{'reference':'synthetic-test-only','terms_sha256':'a'*64,'approved_by_role':'product_owner'}];e['retention']={'mode':'WHILE_VALID','max_age_days':None}
   for k in g.PUBLIC_USES:e[k]='ALLOWED'

class MarketRefreshGuardTests(unittest.TestCase):
 def test_current_public_market_is_rights_blocked(self):
  r=g.evaluate(REG,MARKET,date(2026,9,14));self.assertEqual(r['market_refresh'],'blocked_by_rights');self.assertEqual(r['eligible_count'],0);self.assertEqual(r['blocked_count'],20);self.assertEqual(len(r['stages']),6);self.assertTrue(all(s['status']=='blocked_by_rights' for s in r['stages']))
 def test_stage_inventory_exactly_covers_market(self):
  configured={i for ids in g.STAGES.values() for i in ids};self.assertEqual(configured,g.identities(MARKET));self.assertEqual(len(configured),20)
 def test_guard_never_changes_market_snapshot(self):
  before=json.dumps(MARKET,sort_keys=True);g.evaluate(REG,MARKET,date(2026,9,14));self.assertEqual(json.dumps(MARKET,sort_keys=True),before)
 def test_us_stocks_can_be_approved_without_unlocking_other_stages(self):
  reg=copy.deepcopy(REG);approve(reg,set(g.STAGES['us_stocks']));r=g.evaluate(reg,MARKET,date(2026,9,14));stages={s['stage']:s for s in r['stages']};self.assertEqual(stages['us_stocks']['status'],'ready');self.assertEqual(stages['us_stocks']['eligible_count'],5);self.assertEqual(r['eligible_count'],5);self.assertEqual(r['blocked_count'],15);self.assertEqual(r['market_refresh'],'blocked_by_rights')
 def test_all_stages_require_explicit_approval(self):
  reg=copy.deepcopy(REG);approve(reg,g.identities(MARKET));r=g.evaluate(reg,MARKET,date(2026,9,14));self.assertEqual(r['market_refresh'],'ready');self.assertEqual(r['blocked_count'],0);self.assertTrue(all(s['status']=='ready' for s in r['stages']))
 def test_expired_approval_blocks_only_its_stage(self):
  reg=copy.deepcopy(REG);approve(reg,set(g.STAGES['us_stocks']));target=next(e for e in reg['datasets'] if e['id']=='market-nvda');target['valid_until']='2026-09-13';r=g.evaluate(reg,MARKET,date(2026,9,14));stage=next(s for s in r['stages'] if s['stage']=='us_stocks');self.assertEqual(stage['eligible_count'],4);self.assertEqual(stage['blocked_count'],1);self.assertEqual(stage['status'],'blocked_by_rights')
if __name__=='__main__':unittest.main()
