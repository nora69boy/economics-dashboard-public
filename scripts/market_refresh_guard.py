"""Fail-safe staged market automation gate: never fetch or mutate quotes without explicit rights."""
from __future__ import annotations
import argparse,json,os
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PUBLIC_USES=('automated_retrieval','storage','transformation','display','redistribution','caching')
STAGES={
    'us_stocks':('market-nvda','market-msft','market-aapl','market-googl','market-amzn'),
    'us_etf':('market-spy',),
    'us_indices':('market-spx','market-ixic','market-dji'),
    'japan_indices':('market-n225','market-topix'),
    'europe_indices':('market-ftse','market-dax','market-cac','market-stoxx50e'),
    'asia_indices':('market-hsi','market-ssec','market-kospi','market-nifty','market-asx200'),
}

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

def evaluate_stage(entries:dict,stage:str,today:date)->dict:
    ids=list(STAGES[stage]);allowed=[i for i in ids if i in entries and approved(entries[i],today)];blocked=[i for i in ids if i not in allowed]
    return {'stage':stage,'status':'ready' if not blocked else 'blocked_by_rights','eligible_count':len(allowed),'blocked_count':len(blocked),'eligible':allowed,'blocked':blocked}

def evaluate(registry:dict,market:dict,today:date|None=None)->dict:
    today=today or date.today();entries={e['id']:e for e in registry['datasets']};market_ids=identities(market)
    configured=set(i for ids in STAGES.values() for i in ids)
    if configured!=market_ids:raise ValueError('stage inventory mismatch')
    stages=[evaluate_stage(entries,name,today) for name in STAGES]
    allowed=sum(s['eligible_count'] for s in stages);blocked=sum(s['blocked_count'] for s in stages)
    return {'market_refresh':'ready' if blocked==0 else 'blocked_by_rights','eligible_count':allowed,'blocked_count':blocked,'snapshot_as_of':market['as_of'],'automatic_updates':market['automatic_updates'],'stages':stages}

def emit(result:dict)->None:
    print(json.dumps(result,sort_keys=True,separators=(',',':')))
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f:f.write('market_refresh='+result['market_refresh']+'\n')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:
            f.write('## Market-data automation gate\n\n')
            f.write('- Overall: '+result['market_refresh']+'\n')
            f.write('- Current public stock/index snapshot: '+result['snapshot_as_of']+'\n')
            for s in result['stages']:
                f.write('- '+s['stage']+': '+s['status']+' ('+str(s['eligible_count'])+'/'+str(s['eligible_count']+s['blocked_count'])+' eligible)\n')
            f.write('- No quote provider was contacted and market.json was not modified.\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--require-approved',action='store_true');p.add_argument('--stage',choices=list(STAGES));a=p.parse_args()
    result=evaluate(load(ROOT/'data-rights/registry.json'),load(ROOT/'site/data/market.json'))
    if a.stage:
        result=next(s for s in result['stages'] if s['stage']==a.stage)
    emit(result if 'market_refresh' in result else {'market_refresh':result['status'],'eligible_count':result['eligible_count'],'blocked_count':result['blocked_count'],'snapshot_as_of':load(ROOT/'site/data/market.json')['as_of'],'automatic_updates':False,'stages':[result]})
    if a.require_approved and (result.get('market_refresh') or result.get('status'))!='ready':raise SystemExit(2)
if __name__=='__main__':main()
