"""Secondary gate only: scan privately BEFORE any public commit."""
import argparse,base64,hashlib,html,json,math,re,shutil,subprocess,unicodedata
from pathlib import Path,PurePosixPath
from datetime import date,datetime
from zoneinfo import ZoneInfo
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
SOURCES={'fed':'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm','boj':'https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm','bls':'https://www.bls.gov/schedule/2026/home.htm'}
POLICY=json.loads((ROOT/'scripts/source_policy.json').read_text());URLS=set(SOURCES.values())|set(POLICY['urls'])
PATTERNS={'email':r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b','phone':r'(?<!\d)(?:0\d{1,4}[- ]\d{1,4}[- ]\d{3,4}|0\d{9,10})(?!\d)','international':r'(?<!\w)\+\d{1,3}[ -](?:\d[ -]?){7,14}(?!\d)','credential':r'(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|passwd|private[_-]?key)\b[\s\"\x27]*[:=][\s\"\x27]*[A-Za-z0-9_/-]{6,}','token':r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b','key':r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----','local':r'(?i)(?:file://|localhost|\b127\.0\.0\.1\b|\b192\.168\.\d+\.\d+\b|\b10\.\d+\.\d+\.\d+\b|\b172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+\b)'}
TERMS=['\u6c0f\u540d','\u4f4f\u6240','\u96fb\u8a71\u756a\u53f7','\u751f\u5e74\u6708\u65e5','\u30de\u30a4\u30ca\u30f3\u30d0\u30fc','\u53e3\u5ea7\u756a\u53f7','\u8a3c\u5238\u53e3\u5ea7','\u4fdd\u6709\u682a\u6570','\u53d6\u5f97\u5358\u4fa1','\u8cb7\u4ed8\u4f59\u529b','\u53e3\u5ea7\u6b8b\u9ad8','\u8cc7\u7523\u7dcf\u984d','\u542b\u307f\u76ca','\u542b\u307f\u640d','\u58f2\u8cb7\u5c65\u6b74','home address','date of birth','account number','cost basis','account balance','trading history']
NETWORK=re.compile(r'(?i)\b(?:fetch\s*\(|XMLHttpRequest\b|WebSocket\b|sendBeacon\b|EventSource\b|Worker\b|import\s*\(|eval\s*\(|Function\s*\(|location\b|localStorage\b|sessionStorage\b|indexedDB\b|cookie\b|FileReader\b|RTCPeerConnection\b)|window\s*\.\s*open')
PAYLOAD={'index.html','data/current-state.json','data/market.json','reports/2026-09-11-carry-forward.md'}
REPO={'README.md','.gitignore','.github/workflows/pages.yml','scripts/check_site.py','scripts/source_policy.json','scripts/build_dashboard.py','scripts/market_refresh_guard.py','templates/base.html','templates/charts.js','templates/charts.css','tests/test_site.py','tests/test_market_refresh_guard.py','docs/market-data-auto-refresh.md'}
def require(ok,label):
 if not ok:raise ValueError(label)
def fields(d,names):require(isinstance(d,dict) and set(d)==set(names.split()),'fields')
def pairs(items):
 out={}
 for k,v in items:require(k not in out,'duplicate JSON');out[k]=v
 return out
def loads(s):return json.loads(s,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('non-finite')))
def normal(s):return unicodedata.normalize('NFKC',html.unescape(re.sub(r'\\u([a-fA-F0-9]{4})',lambda m:chr(int(m[1],16)),s)))
def phone_scan_text(s, rights_document):
 """Mask only SHA-256 scalars at known rights-document schema paths."""
 require(rights_document in {'registry.json','migration-baseline.json'},'hash scan context')
 data=loads(s)
 def mask(obj,key):
  if isinstance(obj,dict) and isinstance(obj.get(key),str) and re.fullmatch(r'[0-9a-f]{64}',obj[key]):
   obj[key]='SHA256'
 if isinstance(data,dict):
  datasets=data.get('datasets')
  if rights_document=='migration-baseline.json':
   mask(data,'html_shell_sha256')
   if isinstance(datasets,dict):
    for ident,entry in datasets.items():
     if re.fullmatch(r'[a-z][a-z0-9-]{0,79}',ident):
      mask(entry,'scope_sha256');mask(entry,'content_sha256')
  elif isinstance(datasets,list):
   for entry in datasets:
    if isinstance(entry,dict):
     for evidence in entry.get('evidence',[]):
      mask(evidence,'terms_sha256')
 return json.dumps(data,ensure_ascii=True,separators=(',',':'))
def scan(s, rights_document=None):
 t=normal(phone_scan_text(s,rights_document) if rights_document else s)
 for label,pattern in PATTERNS.items():require(re.search(pattern,t) is None,'sensitive '+label)
 low=t.lower();require(not any(x.lower() in low for x in TERMS),'personal data field')
def url(u):
 from urllib.parse import urlsplit
 p=urlsplit(u);require(p.scheme=='https' and p.hostname and not p.username and not p.password and p.port in (None,443),'url')
def validate_market(data):
 fields(data,'version classification checked_at as_of mode automatic_updates assets indices financials limitations')
 require(data['version']==1 and data['classification']=='public-market-research' and data['mode']=='reviewed_snapshot' and data['automatic_updates'] is False,'market mode')
 date.fromisoformat(data['checked_at']);date.fromisoformat(data['as_of']);require(len(data['assets'])==6 and len(data['indices'])==14,'market count')
 symbols=set()
 for group in ['assets','indices']:
  for a in data[group]:
   require(a['symbol'] not in symbols,'duplicate symbol');symbols.add(a['symbol']);require(a['sources'] and all(u in URLS for u in a['sources']),'source url');require(a['observations'],'market observations')
   last=''
   for o in a['observations']:
    require(last<o['date']<=data['as_of'],'market date');last=o['date']
    for k,v in o.items():
     if k!='date':require(type(v) in (int,float) and math.isfinite(v),'market finite')
def validate_research(data):
 fields(data,'version classification as_of sources facts hypotheses watch_items risks catalysts scenarios note')
 require(data['version']==1 and data['classification']=='public-market-research','research mode');date.fromisoformat(data['as_of']);require(data['sources'] and all(s['url'] in URLS for s in data['sources']),'research source')
def validate(site):
 require(site.resolve().is_dir() and not site.is_symlink(),'site path');files={p.relative_to(site).as_posix() for p in site.rglob('*') if p.is_file()};require(files==PAYLOAD|{'manifest.json'},'public allowlist')
 for p in files:
  raw=(site/p).read_bytes();require(len(raw)<=2000000,'size');text=raw.decode();scan(text)
  if p.endswith('.json'):loads(text)
 validate_market(loads((site/'data/market.json').read_text()));validate_research(loads((site/'data/current-state.json').read_text()));return files
def html_check(text):
 require('<form' not in text.lower(),'form');require('iframe' not in text.lower(),'iframe');require('document.write' not in text,'document write');require(NETWORK.search(text) is None,'network')
 require(text.count('id="')==len(set(re.findall(r'id="([^"]+)"',text))),'duplicate id')
 require("default-src 'none'" in text and "connect-src 'none'" in text and "frame-src 'none'" in text and "object-src 'none'" in text,'csp')
def history():
 ids=subprocess.check_output(['git','log','--all','--format=%ae%n%ce'],cwd=ROOT,text=True).splitlines();require(ids and all(x=='noreply@github.com' or re.fullmatch(r'[^@\s]+@users\.noreply\.github\.com',x) for x in ids),'identity suppressed');tracked=set(subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines());require(tracked==REPO|{'site/'+p for p in PAYLOAD-{'index.html'}}|{'site/manifest.json'},'repo allowlist')
 scan(subprocess.check_output(['git','log','-p','--all','--no-ext-diff'],cwd=ROOT,text=True,errors='replace'))
def manifest(site):
 m=loads((site/'manifest.json').read_text());fields(m,'version classification files');require(m['classification']=='public-market-research','manifest class');require(set(m['files'])==PAYLOAD,'manifest files')
 for p,h in m['files'].items():require(hashlib.sha256((site/p).read_bytes()).hexdigest()==h,'manifest digest')
def main():
 p=argparse.ArgumentParser();p.add_argument('--site',type=Path,default=ROOT/'site');p.add_argument('--history',action='store_true');a=p.parse_args();validate(a.site);html_check((a.site/'index.html').read_text());manifest(a.site);history() if a.history else None;print('PASS')
if __name__=='__main__':main()
