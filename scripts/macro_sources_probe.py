"""Development-only reads of public government statistics. No credentials."""
from pathlib import Path
import concurrent.futures, hashlib, json, urllib.request, urllib.parse
BASE='https://home.treasury.gov/resource-center/data-chart-center/interest-rates/'
URLS={
 'treasury_2010':BASE+'daily-treasury-rate-archives/par-yield-curve-rates-2010-2019.csv',
 'treasury_2020':BASE+'daily-treasury-rate-archives/par-yield-curve-rates-2020-2023.csv',
 **{'treasury_'+str(y):BASE+'daily-treasury-rates.csv/'+str(y)+'/all?_format=csv&field_tdr_date_value='+str(y)+'&page=&type=daily_treasury_yield_curve' for y in [2024,2025,2026]},
 'bls_history':'https://api.bls.gov/publicAPI/v1/timeseries/data/',
 'bls_recent':'https://api.bls.gov/publicAPI/v1/timeseries/data/',
 'bea_flat':'https://apps.bea.gov/national/Release/TXT/NipaDataM.txt',
 'calendar_cpi':'https://www.bls.gov/schedule/news_release/cpi.htm',
 'calendar_jobs':'https://www.bls.gov/schedule/news_release/empsit.htm',
 'calendar_bea':'https://www.bea.gov/news/schedule',
 'calendar_fed':'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'}
ALLOWED={urllib.parse.urlsplit(u).hostname for u in URLS.values()}
class Redirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  p=urllib.parse.urlsplit(newurl)
  if p.scheme!='https' or p.hostname not in ALLOWED:raise ValueError('Unapproved redirect')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def one(item):
 name,url=item;out={'source':name,'url':url}
 try:
  headers={'User-Agent':'EconomicsResearchDashboard/0.6 (public statistical research)'};body=None
  if name.startswith('bls_'):
   body=json.dumps({'seriesid':['CUUR0000SA0','CUSR0000SA0','CUUR0000SA0L1E','CUSR0000SA0L1E','LNS14000000','CES0000000001'],'startyear':'2015' if name=='bls_history' else '2025','endyear':'2024' if name=='bls_history' else '2026'}).encode();headers['Content-Type']='application/json'
  req=urllib.request.Request(url,data=body,headers=headers)
  with urllib.request.build_opener(Redirect()).open(req,timeout=45) as r:
   if name=='bea_flat':
    selected=[];count=0;seen=0;digest=hashlib.sha256()
    for line in r:
     seen+=len(line);digest.update(line)
     if seen>120000000:raise ValueError('Bounded size exceeded')
     if count<8 or b'DPCERG3' in line or b'DPCCRG3' in line:selected.append(line)
     count+=1
    data=b''.join(selected);out.update(total_bytes=seen,total_rows=count,raw_sha256=digest.hexdigest())
   else:
    data=r.read(15000001)
    if len(data)>15000000:raise ValueError('Bounded size exceeded')
   out.update(status=r.status,content_type=r.headers.get('Content-Type'),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
  Path('macro-source-review/'+name+'.raw').write_bytes(data)
 except Exception as e:out['error']=type(e).__name__;out['status']=getattr(e,'code',None)
 return out
if __name__=='__main__':
 Path('macro-source-review').mkdir(exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:result=list(pool.map(one,URLS.items()))
 Path('macro-source-review/result.json').write_text(json.dumps(result,indent=2))
 print(json.dumps(result,indent=2))
