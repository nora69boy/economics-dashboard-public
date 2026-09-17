"""Fetch only allowlisted government series; failed sources retain validated public data."""
from __future__ import annotations
import argparse,copy,hashlib,io,json,os,sys,time,urllib.request,urllib.parse,urllib.error
from datetime import datetime,timezone,date
from pathlib import Path
from macro_core import *
ROOT=Path(__file__).resolve().parents[1]
PUBLIC='https://nora69boy.github.io/economics-dashboard-public/data/macro.json'
ENDPOINTS={BLS,BEA,FX,WTI,WTI_RECENT,PUBLIC,TREASURY+'daily-treasury-rate-archives/par-yield-curve-rates-2010-2019.csv',TREASURY+'daily-treasury-rate-archives/par-yield-curve-rates-2020-2023.csv'} | {TREASURY+'daily-treasury-rates.csv/'+str(y)+'/all?_format=csv&field_tdr_date_value='+str(y)+'&page=&type=daily_treasury_yield_curve' for y in range(2024,date.today().year+1)}
HOSTS={'home.treasury.gov','api.bls.gov','apps.bea.gov','www.federalreserve.gov','www.eia.gov','nora69boy.github.io'}
class Redirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  p=urllib.parse.urlsplit(newurl);require(p.scheme=='https' and p.hostname==urllib.parse.urlsplit(req.full_url).hostname,'Unexpected redirect');return super().redirect_request(req,fp,code,msg,headers,newurl)
def download(url: str, body: dict | None = None) -> bytes:
    """Retry one transient GET failure; never retry quota-limited BLS POSTs."""
    p = urllib.parse.urlsplit(url)
    require(url in ENDPOINTS and p.scheme == 'https' and p.hostname in HOSTS
            and not p.username and not p.password, 'Endpoint')
    headers = {'User-Agent': 'EconomicsResearchDashboard/0.6 (public statistical research)'}
    if body is not None:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers=headers)
    cap = 120000000 if url == BEA else 4000000
    attempts = 1 if body is not None else 2
    opener = urllib.request.build_opener(Redirect())
    for attempt in range(attempts):
        try:
            with opener.open(req, timeout=30) as response:
                value = response.read(cap + 1)
                require(len(value) <= cap, 'Size limit')
                return value
        except urllib.error.HTTPError as exc:
            if exc.code not in {500, 502, 503, 504} or attempt + 1 == attempts:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt + 1 == attempts:
                raise
        time.sleep(1)
    raise ValueError('Download failed')


def ensure_continuity(candidate: dict, previous: dict | None) -> None:
    """Do not promote a truncated response to a newly fetched valid history."""
    if not previous or not previous['observations']:
        return
    def preserved(before, after):
        require({row[0] for row in before} <= {row[0] for row in after},
                'History coverage regression')
    preserved(previous['observations'], candidate['observations'])
    for ident, rows in previous['auxiliary'].items():
        require(ident in candidate['auxiliary'], 'Auxiliary coverage regression')
        preserved(rows, candidate['auxiliary'][ident])


def write_snapshot(data: dict) -> None:
    """Replace the local output atomically, only after full validation."""
    validate(data)
    require(all(s['observations'] for s in data['series'] if s['id'] != 'vix'),
            'Initial complete government history required')
    dest = ROOT / 'site/data/macro.json'
    temporary = dest.with_suffix('.json.tmp')
    try:
        temporary.write_text(json.dumps(data, separators=(',', ':'), allow_nan=False) + '\n', encoding='utf-8')
        temporary.replace(dest)
    finally:
        temporary.unlink(missing_ok=True)


def emit_status(data: dict, mode: str = 'refresh') -> None:
    """CI diagnostics contain fixed identities and dates, never provider error bodies."""
    validate(data)
    rows = [{k: s[k] for k in ['id', 'status', 'fetched_at']} |
            {'points': len(s['observations']),
             'latest_observation': s['observations'][-1][0] if s['observations'] else None}
            for s in data['series']]
    affected = [s for s in rows if s['id'] != 'vix' and s['status'] != 'available']
    health = 'fixture' if mode == 'fixture' else ('degraded' if affected else 'fresh')
    print(json.dumps({'mode': mode, 'refresh_health': health, 'series': rows}))
    if mode != 'fixture':
        for row in affected:
            print('::warning::Macro source ' + row['id'] + ': previous validated data retained; retrieval did not succeed.')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as handle:
            handle.write('refresh_health=' + health + '\n')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        lines = ['## Macro refresh: ' + health, '',
                 'Mode: ' + mode + '. Source retrieval success is not proof of a new observation.',
                 'Attempt timestamp (UTC): ' + data['attempted_at'], '',
                 '| Series | Retrieval status | Last successful retrieval (UTC) | Last observation | Points |',
                 '|---|---|---|---|---|']
        for row in rows:
            lines.append('| ' + ' | '.join(str(row[key] if row[key] is not None else '--')
                         for key in ['id', 'status', 'fetched_at', 'latest_observation', 'points']) + ' |')
        lines += ['', 'Stocks, indices, news, calendar review and VIX are not refreshed by this job.', '']
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as handle:
            handle.write('\n'.join(lines))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--raw-dir',type=Path);ap.add_argument('--previous',type=Path);ap.add_argument('--snapshot-only',action='store_true');a=ap.parse_args()
 require(not (a.snapshot_only and a.raw_dir),'Fixture mode cannot read provider captures')
 now=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ');previous=None
 try:
  if a.previous:previous=json.loads(a.previous.read_text())
  elif not a.raw_dir:previous=json.loads(download(PUBLIC))
  if previous is not None:validate(previous)
 except Exception:previous=None
 if a.snapshot_only:
  require(previous is not None,'Validated published fixture required');write_snapshot(previous);emit_status(previous,'fixture');return
 old={s['id']:s for s in previous['series']} if previous else {}
 result={'schema':1,'classification':'public-official-macro','attempted_at':now,'series':[],'revisions':previous['revisions'][:] if previous else []}
 def get(name,url,body=None):return (a.raw_dir/(name+'.raw')).read_bytes() if a.raw_dir else download(url,body)
 def entry(ident,rows,aux,raws):return {'id':ident,'status':'available','fetched_at':now,'source_sha256':hashlib.sha256(b''.join(raws)).hexdigest(),'observations':clean(rows),'auxiliary':{k:clean(v) for k,v in aux.items()}}
 def failed(ident):
  if ident in old and old[ident]['observations']:
   s=copy.deepcopy(old[ident]);s['status']='retained';return s
  return {'id':ident,'status':'unavailable','fetched_at':None,'source_sha256':None,'observations':[],'auxiliary':{}}
 collected={}
 try:
  ten={};two={};raws=[];specs=[('treasury_2010',TREASURY+'daily-treasury-rate-archives/par-yield-curve-rates-2010-2019.csv'),('treasury_2020',TREASURY+'daily-treasury-rate-archives/par-yield-curve-rates-2020-2023.csv')]
  specs += [('treasury_'+str(y),TREASURY+'daily-treasury-rates.csv/'+str(y)+'/all?_format=csv&field_tdr_date_value='+str(y)+'&page=&type=daily_treasury_yield_curve') for y in range(2024,date.today().year+1)]
  for name,url in specs:
   raw=get(name,url);x,y=parse_treasury(raw);ten.update(x);two.update(y);raws.append(raw)
  collected['ust10']=entry('ust10',ten,{'ust2':two},raws)
 except Exception:collected['ust10']=failed('ust10')
 try:
  allrows={k:{} for k in BLS_IDS};raws=[]
  for name,start,end in [('bls_history',2015,2024),('bls_recent',2025,date.today().year)]:
   raw=get(name,BLS,{'seriesid':list(BLS_IDS),'startyear':str(start),'endyear':str(end)});raws.append(raw);parsed=parse_bls(raw);require(set(parsed)==set(BLS_IDS),'BLS series coverage')
   for key,rows in parsed.items():allrows[key].update(rows)
  for ident in ['cpi','unemployment']:
   primary=next(rows for key,rows in allrows.items() if BLS_IDS[key]==(ident,None));aux={BLS_IDS[key][1]:rows for key,rows in allrows.items() if BLS_IDS[key][0]==ident and BLS_IDS[key][1] is not None};collected[ident]=entry(ident,primary,aux,raws)
 except Exception:
  for ident in ['cpi','unemployment']:collected[ident]=failed(ident)
 try:
  raw=get('bea_pce',BEA);x,y=parse_bea(io.StringIO(raw.decode('utf-8-sig')));collected['pce']=entry('pce',x,{'core':y},[raw])
 except Exception:collected['pce']=failed('pce')
 try:
  raw=get('fx',FX);collected['usdjpy']=entry('usdjpy',parse_fx(raw),{},[raw])
 except Exception:collected['usdjpy']=failed('usdjpy')
 try:
  raw=get('wti',WTI);collected['wti']=entry('wti',parse_wti(raw),{},[raw])
 except Exception:
  try:
   prior=old.get('wti');require(prior is not None and prior['observations'],'WTI fallback requires validated history')
   raw=get('wti_recent',WTI_RECENT);merged=dict(prior['observations']);merged.update(parse_wti_recent(raw))
   provenance=(prior['source_sha256'] or '').encode()+raw
   collected['wti']=entry('wti',merged,{},[provenance])
  except Exception:collected['wti']=failed('wti')
 collected['vix']={'id':'vix','status':'rights_pending','fetched_at':None,'source_sha256':None,'observations':[],'auxiliary':{}}
 for ident in META:
  s=collected[ident]
  try:
   trial={'schema':1,'classification':result['classification'],'attempted_at':now,'series':[s if i==ident else {'id':i,'status':'rights_pending' if i=='vix' else 'unavailable','fetched_at':None,'source_sha256':None,'observations':[],'auxiliary':{}} for i in META],'revisions':[]};validate(trial)
   if s['status']=='available':ensure_continuity(s,old.get(ident))
  except Exception:
   if ident!='vix':s=failed(ident);collected[ident]=s
  if s['status']=='available' and ident in old:
   before=dict(old[ident]['observations'])
   for d,v in s['observations']:
    if d in before and before[d]!=v:result['revisions'].append({'series':ident,'date':d,'old':before[d],'new':v,'detected_at':now})
  result['series'].append(s)
 result['revisions']=result['revisions'][-50:];validate(result);require(all(s['observations'] for s in result['series'] if s['id']!='vix'),'Initial complete government history required')
 write_snapshot(result);emit_status(result)
if __name__=='__main__':main()
