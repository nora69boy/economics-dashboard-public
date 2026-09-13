import copy,json,sys,unittest
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import market_refresh_guard as g
REG=json.loads((ROOT/'data-rights/registry.json').read_text());MARKET=json.loads((ROOT/'site/data/market.json').read_text())
class MarketRefreshGuardTests(unittest.TestCase):
 def test_current_public_market_is_rights_blocked(self):
  r=g.evaluate(REG,MARKET,date(2026,9,14));self.assertEqual(r['market_refresh'],'blocked_by_rights');self.assertEqual(r['eligible_count'],0);self.assertEqual(r['blocked_count'],20)
 def test_guard_never_changes_market_snapshot(self):
  before=json.dumps(MARKET,sort_keys=True);g.evaluate(REG,MARKET,date(2026,9,14));self.assertEqual(json.dumps(MARKET,sort_keys=True),before)
 def test_explicit_approval_is_required(self):
  reg=copy.deepcopy(REG);ids=g.identities(MARKET)
  for e in reg['datasets']:
   if e['id'] in ids:
    e['status']='APPROVED';e['valid_from']='2026-01-01';e['valid_until']='2026-12-31';e['review_due_at']='2026-12-31';e['terms_url']=['https://example.invalid/terms'];e['evidence']=[{'reference':'synthetic-test-only','terms_sha256':'a'*64,'approved_by_role':'product_owner'}];e['retention']={'mode':'WHILE_VALID','max_age_days':None}
    for k in g.PUBLIC_USES:e[k]='ALLOWED'
  r=g.evaluate(reg,MARKET,date(2026,9,14));self.assertEqual(r['market_refresh'],'ready');self.assertEqual(r['blocked_count'],0)
 def test_expired_approval_blocks(self):
  reg=copy.deepcopy(REG);target=next(e for e in reg['datasets'] if e['id']=='market-nvda');target.update(status='APPROVED',valid_from='2026-01-01',valid_until='2026-09-13',review_due_at='2026-12-31',terms_url=['https://example.invalid/terms'],evidence=[{'reference':'synthetic-test-only','terms_sha256':'a'*64,'approved_by_role':'product_owner'}],retention={'mode':'WHILE_VALID','max_age_days':None})
  for k in g.PUBLIC_USES:target[k]='ALLOWED'
  self.assertEqual(g.evaluate(reg,MARKET,date(2026,9,14))['eligible_count'],0)
if __name__=='__main__':unittest.main()
