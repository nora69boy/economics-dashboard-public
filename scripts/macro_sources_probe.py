"""Read public official data endpoints; never use credentials or private data."""
from pathlib import Path
import concurrent.futures, hashlib, json, urllib.request, urllib.error, urllib.parse, zipfile, io
URLS={
 'treasury':'https://home.treasury.gov/resource-center-data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2026',
 'cpi':'https://api.bls.gov/publicAPI/v1/timeseries/data/CUUR0000SA0?startyear=2015&endyear=2024',
 'unemployment':'https://api.bls.gov/publicAPI/v1/timeseries/data/LNS14000000?startyear=2015&endyear=2024',
 'fx':'https://www.federalreserve.gov/releases/h10/hist/dat00_ja.htm',
 'wti':'https://www.eia.gov/dnav/pet/hist/RWTCD.htm',
 'bea_csv':'https://apps.bea.gov/national/Release/TXT/Section2All_csv.zip',
 'bea_flat':'https://apps.bea.gov/national/Release/TXT/NipaDataM.txt'}
ALLOWED={urllib.parse.urlsplit(u).hostname for u in URLS.values()}
class Redirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  p=urllib.parse.urlsplit(newurl)
  if p.scheme!='https' or p.hostname not in ALLOWED:raise ValueError('Unapproved redirect')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def one(item):
 name,url=item;out={'source':name,'url':url}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'EconomicsResearchDashboard/0.6 (public statistics research)'})
  with urllib.request.build_opener(Redirect()).open(req,timeout=25) as r:
   data=r.read(15000001)
   if len(data)>15000000:raise ValueError('Size limit')
   out.update(status=r.status,content_type=r.headers.get('Content-Type'),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
  if name=='bea_csv' and data.startswith(b'PK'):
   z=zipfile.ZipFile(io.BytesIO(data));out['members']=[x.filename for x in z.infolist()][:20]
  # The archive is a temporary development artifact containing only already-public official statistics.
  Path('macro-source-review/'+name+'.raw').write_bytes(data)
 except Exception as e:out['error']=type(e).__name__;out['status']=getattr(e,'code',None)
 return out
if __name__=='__main__':
 Path('macro-source-review').mkdir(exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:result=list(pool.map(one,URLS.items()))
 Path('macro-source-review/result.json').write_text(json.dumps(result,indent=2))
 print(json.dumps(result,indent=2))
