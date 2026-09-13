"""Fail-safe market automation gate: never fetch or mutate public quotes without explicit rights."""
from __future__ import annotations
import argparse,json,os
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PUBLIC_USES=('automated_retrieval','storage','transformation','display','redistribution','caching')

def load(path:Path):
    with path.open(encoding='utf-8') as f:return json.load(f)

def identities(market:dict)->set[str]:
    return {'market-'+row['symbol'].lower() for row in market['assets']+market['indices']}

def approved(entry:dict,today:date)->bool:
    if entry.get('status') not in {'APPROVED','CONDITIONAL'}:return False
    if any(entry.get(k)!='ALLOWED' for k in PUBLIC_USES):return False
    if entry.get('retention',{}).get('mode')!='WHILE_VALID':return False
    if not entry.get('terms_url') or not entry.get('evidence'):return False
    if entry.get('valid_from') and today<date.fromisoformat(entry['valid_from']):return False
    if entry.get('valid_until') and today>date.fromisoformat(entry['valid_until']):return False
    if entry.get('review_due_at') and today>date.fromisoformat(entry['review_due_at']):return False
    return True

def evaluate(registry:dict,market:dict,today:date|None=None)->dict:
    today=today or date.today(); entries={e['id']:e for e in registry['datasets']}; ids=sorted(identities(market))
    allowed=[i for i in ids if i in entries and approved(entries[i],today)]
    blocked=[i for i in ids if i not in allowed]
    return {'market_refresh':'ready' if not blocked else 'blocked_by_rights','eligible_count':len(allowed),'blocked_count':len(blocked),'snapshot_as_of':market['as_of'],'automatic_updates':market['automatic_updates']}

def emit(result:dict)->None:
    print(json.dumps(result,sort_keys=True,separators=(',',':')))
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f:f.write('market_refresh='+result['market_refresh']+'\n')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:
            f.write('## Market-data automation gate\n\n')
            f.write('- Status: '+result['market_refresh']+'\n')
            f.write('- Rights-eligible public series: '+str(result['eligible_count'])+'\n')
            f.write('- Blocked series: '+str(result['blocked_count'])+'\n')
            f.write('- Current public stock/index snapshot: '+result['snapshot_as_of']+'\n')
            f.write('- No quote provider was contacted and market.json was not modified.\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--require-approved',action='store_true');a=p.parse_args()
    result=evaluate(load(ROOT/'data-rights/registry.json'),load(ROOT/'site/data/market.json'));emit(result)
    if a.require_approved and result['market_refresh']!='ready':raise SystemExit(2)
if __name__=='__main__':main()
