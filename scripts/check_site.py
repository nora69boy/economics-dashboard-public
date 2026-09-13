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
REPO={'README.md','.gitignore','.github/workflows/pages.yml','scripts/check_site.py','scripts/source_policy.json','scripts/build_dashboard.py','templates/base.html','templates/charts.js','templates/charts.css','tests/test_site.py'}
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
    evidence=entry.get('evidence') if isinstance(entry,dict) else None
    if isinstance(evidence,list):
     for item in evidence:mask(item,'terms_sha256')
 return normal(json.dumps(data,ensure_ascii=True))

def scan(s, *, rights_document=None):
 phone_text=phone_scan_text(s,rights_document) if rights_document is not None else normal(s)
 s=normal(s)
 for label,p in PATTERNS.items():require(not re.search(p,phone_text if label=='phone' else s),'sensitive '+label)
 require(not any(t.lower() in s.lower() for t in TERMS),'sensitive term')
def number(v):require(type(v) in (int,float) and math.isfinite(v) and v>0,'number')
def research(d):
 fields(d,'version as_of publication live_market_data automated_report_ingestion sources streams topics events company_checks')
 require(d['version']=='0.3.0' and d['publication']=='public_dashboard' and d['live_market_data'] is False and d['automated_report_ingestion'] is False,'research state');asof=date.fromisoformat(d['as_of'])
 for k,n in [('sources',3),('streams',5),('topics',13),('events',8)]:
  a=d[k];require(isinstance(a,list) and len(a)==n and len({x['id'] for x in a})==n,'count');require(all(re.fullmatch(r'[a-z0-9-]+',x['id']) for x in a),'ID')
 for s in d['sources']:fields(s,'id label url checked_at');require(s['url']==SOURCES[s['id']] and date.fromisoformat(s['checked_at'])<=asof,'source')
 require({s['id'] for s in d['sources']}==set(SOURCES),'source set')
 ids={'brief','breaking','event','autumn','topix'};require({s['id'] for s in d['streams']}==ids,'stream set')
 for s in d['streams']:fields(s,'id label scope')
 for t in d['topics']:
  fields(t,'id title category priority streams summary question refutation claim_type');require(t['claim_type']=='research_question' and t['priority'] in {'P1','P2'} and t['category'] in {'macro','ai','japan','flow','frontier'},'topic');require(t['streams'] and len(t['streams'])==len(set(t['streams'])) and set(t['streams'])<=ids,'routing')
 for e in d['events']:
  fields(e,'id title start end zone time_local time_jst source status');require(e['source'] in SOURCES and e['status']=='verified_schedule_only' and date.fromisoformat(e['start'])<=date.fromisoformat(e['end']),'event');require(e['zone'] in {'America/New_York','Asia/Tokyo'},'zone')
  if e['time_local'] is None:require(e['time_jst'] is None,'invented time')
  else:
   require(e['start']==e['end'] and re.fullmatch(r'\d{2}:\d{2}',e['time_local']),'time');v=datetime.fromisoformat(e['start']+'T'+e['time_local']).replace(tzinfo=ZoneInfo(e['zone']));require(e['time_jst']==v.astimezone(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M'),'time conversion')
 require(len(d['company_checks'])==len(set(d['company_checks']))==14,'checklist')
def market(d):
 fields(d,'version classification checked_at as_of mode automatic_updates assets indices financials limitations');require(d['version']==1 and d['classification']=='public-market-research' and d['mode']=='reviewed_snapshot' and d['automatic_updates'] is False,'market state');require(date.fromisoformat(d['as_of'])<=date.fromisoformat(d['checked_at'])<=date.today(),'asof')
 require(len(d['indices'])==14 and {a['symbol'] for a in d['indices']}==set(POLICY['indices']),'index set');require(len(d['assets'])==6 and {a['symbol'] for a in d['assets']}==set(POLICY['assets']),'asset set')
 for a in d['indices']+d['assets']:
  ix=a in d['indices'];fields(a,'symbol name kind region currency unit zone quality basis note sources observations' if ix else 'symbol name kind currency zone quality basis sources observations');require(a['quality']=='secondary_snapshot','quality')
  if ix:
   require(a['kind']=='index' and a['unit']=='points','index identity')
   for k in ['region','currency','zone','basis','sources']:require(a[k]==POLICY['indices'][a['symbol']][k],'index metadata')
  else:require(a['kind']==('etf' if a['symbol']=='SPY' else 'stock') and a['sources']==POLICY['assets'][a['symbol']] and a['currency']=='USD' and a['zone']=='America/New_York' and a['basis']=='close_not_dividend_adjusted','asset metadata')
  dates=['2026-09-08','2026-09-09','2026-09-10'];dates=dates if ix else ['2026-09-02','2026-09-03','2026-09-04']+dates
  require([r['date'] for r in a['observations']]==dates,'observations')
  for r in a['observations']:
   fields(r,'date close' if ix else 'date open high low close volume');number(r['close'])
   if not ix:
    for k in ['open','high','low']:number(r[k])
    require(r['low']<=min(r['open'],r['close'])<=max(r['open'],r['close'])<=r['high'],'OHLC');require(type(r['volume']) is int and r['volume']>=0,'volume')
 f=d['financials'];fields(f,'symbol basis unit source periods');require(f['symbol']=='NVDA' and f['basis']=='GAAP' and f['unit']=='USD_million' and f['source']==POLICY['financial_source'],'financial identity');require([x['period'] for x in f['periods']]==['FY26 Q2','FY27 Q1','FY27 Q2'],'financial period')
 for q in f['periods']:
  fields(q,'period end revenue operating_income gross_margin');require(date.fromisoformat(q['end'])<=date.fromisoformat(d['as_of']),'period')
  for k in ['revenue','operating_income','gross_margin']:number(q[k])
  require(q['gross_margin']<=100 and q['operating_income']<q['revenue'],'financial ratio')
 require(isinstance(d['limitations'],list) and all(isinstance(x,str) for x in d['limitations']),'limitations')
class Parser(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.ids=set();self.csp=[];self.ref=[];self.head=True
 def handle_starttag(self,t,a):
  require(len(a)==len(dict(a)),'duplicate attribute');v=dict(a);require(t not in {'iframe','object','embed','form','input','textarea','select','img','svg','math','audio','video','source','base','link'},'active tag');require(not any(k.startswith('on') or k in {'src','srcset','srcdoc','ping'} for k,_ in a),'active attribute')
  if 'id' in v:require(v['id'] not in self.ids,'duplicate id');self.ids.add(v['id'])
  if 'href' in v:
   h=v['href'] or '';require(h.startswith('#') or h in PAYLOAD or (t=='a' and h in URLS and v.get('referrerpolicy')=='no-referrer' and {'noopener','noreferrer'}<=set(v.get('rel','').split())),'link')
  if t=='body':self.head=False
  if t=='meta':
   k=v.get('http-equiv','').lower();require(k!='refresh','refresh')
   if k=='content-security-policy':require(self.head,'late CSP');self.csp.append(v.get('content'))
   if v.get('name','').lower()=='referrer':self.ref.append(v.get('content'))
 def handle_startendtag(self,t,a):self.handle_starttag(t,a)
def html_check(s):
 p=Parser();p.feed(s);a=re.findall(r'<script\b[^>]*>(.*?)</script\s*>',s,re.I|re.S);require(len(a)==1 and not NETWORK.search(normal(a[0])),'program');h=base64.b64encode(hashlib.sha256(a[0].encode()).digest()).decode();c="default-src 'none'; script-src 'sha256-"+h+"'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; font-src 'none'; object-src 'none'; frame-src 'none'; form-action 'none'; base-uri 'none'; upgrade-insecure-requests";require(p.csp==[c] and p.ref==['no-referrer'],'CSP');require(not re.search(r'@import|url\s*\(',s,re.I) and s.rstrip().endswith('</html>'),'HTML')
def validate(site):
 require(site.is_dir() and not site.is_symlink(),'site');mp=site/'manifest.json';require(mp.is_file() and not mp.is_symlink() and mp.stat().st_size<1000000,'manifest');m=loads(mp.read_text());fields(m,'version classification files');require(m['version']==2 and m['classification']=='public-market-research' and set(m['files'])==PAYLOAD,'manifest state');actual=set()
 for p in site.rglob('*'):
  require(not p.is_symlink() and (p.is_dir() or p.is_file()),'link/special')
  if p.is_file():require(p.stat().st_nlink==1,'hardlink');actual.add(p.relative_to(site).as_posix())
 require(actual==PAYLOAD|{'manifest.json'},'unexpected file');out={}
 for n,h in m['files'].items():
  p=site/n;require(p.stat().st_size<1000000 and re.fullmatch(r'[0-9a-f]{64}',h),'size/digest');b=p.read_bytes();require(hashlib.sha256(b).hexdigest()==h,'hash');s=b.decode();scan(s);out[n]=b
  if n=='index.html':html_check(s)
  elif n=='data/market.json':market(loads(s))
  elif n=='data/current-state.json':research(loads(s))
 e=re.search(r'<pre id="market-data" hidden>(.*?)</pre>',out['index.html'].decode(),re.S);require(e and loads(html.unescape(e[1]))==loads(out['data/market.json']),'embedded mismatch');return out
def history():
 ids=subprocess.check_output(['git','log','--all','--format=%ae%n%ce'],cwd=ROOT,text=True).splitlines();require(ids and all(x=='noreply@github.com' or re.fullmatch(r'[^@\s]+@users\.noreply\.github\.com',x) for x in ids),'identity suppressed');tracked=set(subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines());require(tracked==REPO|{'site/'+p for p in PAYLOAD-{'index.html'}}|{'site/manifest.json'},'repo allowlist')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check-history',action='store_true');ap.add_argument('--build',action='store_true');a=ap.parse_args()
 if not (ROOT/'site/index.html').exists():subprocess.run(['python3',str(ROOT/'scripts/build_dashboard.py')],check=True)
 out=validate(ROOT/'site')
 if a.check_history:history()
 if a.build:
  dest=ROOT/'.pages-build';require(not dest.is_symlink(),'output link')
  if dest.exists():shutil.rmtree(dest)
  for n,b in out.items():p=dest/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  (dest/'.nojekyll').write_text('')
 print('PASS: 4 reviewed files; sensitive values suppressed')
if __name__=='__main__':
 try:main()
 except (ValueError,KeyError,TypeError,OSError,UnicodeError,subprocess.SubprocessError):raise SystemExit('PUBLICATION BLOCKED: inspect privately; values suppressed')
