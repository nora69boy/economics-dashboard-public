"""Bounded extraction of public BEA monthly price-index source rows."""
from pathlib import Path
import hashlib,json,urllib.request,urllib.parse
URL='https://apps.bea.gov/national/Release/TXT/NipaDataM.txt'
class Redirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  p=urllib.parse.urlsplit(newurl)
  if p.scheme!='https' or p.hostname!='apps.bea.gov':raise ValueError('Unapproved redirect')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
Path('macro-source-review').mkdir(exist_ok=True)
selected=[];seen=0;digest=hashlib.sha256()
with urllib.request.build_opener(Redirect()).open(urllib.request.Request(URL,headers={'User-Agent':'EconomicsResearchDashboard/0.6 (public statistical research)'}),timeout=45) as r:
 for i,line in enumerate(r):
  seen+=len(line);digest.update(line)
  if seen>120000000:raise ValueError('Bounded size exceeded')
  if i==0 or line.startswith((b'DPCERG,',b'DPCCRG,')):selected.append(line)
data=b''.join(selected)
if len(selected)<200:raise ValueError('PCE history absent; do not publish')
Path('macro-source-review/bea_pce.raw').write_bytes(data)
Path('macro-source-review/result.json').write_text(json.dumps({'url':URL,'raw_sha256':digest.hexdigest(),'source_bytes':seen,'selected_rows':len(selected),'selected_sha256':hashlib.sha256(data).hexdigest()},indent=2))
print('BEA public PCE rows:',len(selected))
