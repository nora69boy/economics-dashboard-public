"""Secondary publication gate. Review privately BEFORE a public commit."""
from __future__ import annotations
import argparse, base64, hashlib, html, json, re, shutil, subprocess, unicodedata
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from zoneinfo import ZoneInfo
ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'fed': 'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm',
    'boj': 'https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm',
    'bls': 'https://www.bls.gov/schedule/2026/home.htm',
}
PATTERNS = {
    'email': r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',
    'phone': r'(?<!\d)(?:0\d{1,4}[- ]\d{1,4}[- ]\d{3,4}|0\d{9,10})(?!\d)',
    'international phone': r'(?<!\w)\+\d{1,3}[ -](?:\d[ -]?){7,14}(?!\d)',
    'credential': r'(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|passwd|private[_-]?key)\b[\s\"\x27]*[:=][\s\"\x27]*[A-Za-z0-9_/-]{6,}',
    'token': r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b',
    'private key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'local address': r'(?i)(?:file://|localhost|\b127\.0\.0\.1\b|\b192\.168\.\d+\.\d+\b|\b10\.\d+\.\d+\.\d+\b)',
}
TERMS = ['\u6c0f\u540d','\u4f4f\u6240','\u96fb\u8a71\u756a\u53f7','\u751f\u5e74\u6708\u65e5','\u30de\u30a4\u30ca\u30f3\u30d0\u30fc','\u53e3\u5ea7\u756a\u53f7','\u8a3c\u5238\u53e3\u5ea7','\u4fdd\u6709\u682a\u6570','\u53d6\u5f97\u5358\u4fa1','\u8cb7\u4ed8\u4f59\u529b','\u53e3\u5ea7\u6b8b\u9ad8','\u8cc7\u7523\u7dcf\u984d','\u542b\u307f\u76ca','\u542b\u307f\u640d','\u58f2\u8cb7\u5c65\u6b74','home address','date of birth','account number','cost basis','account balance','trading history']
NETWORK = re.compile(r'(?i)\b(?:fetch\s*\(|XMLHttpRequest\b|WebSocket\b|sendBeacon\b|EventSource\b|Worker\b|import\s*\(|eval\s*\(|Function\s*\(|location\b|localStorage\b|sessionStorage\b|indexedDB\b|cookie\b|FileReader\b|RTCPeerConnection\b)|window\s*\.\s*open')

def ensure(ok, label):
    if not ok: raise ValueError(label)

def normalized(text):
    text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m[1], 16)), text)
    return unicodedata.normalize('NFKC', html.unescape(text))

def scan(text):
    value = normalized(text)
    for label, pattern in PATTERNS.items(): ensure(not re.search(pattern, value), 'sensitive pattern: ' + label)
    ensure(not any(t.lower() in value.lower() for t in TERMS), 'sensitive term')

def pairs(items):
    result = {}
    for key, value in items:
        ensure(key not in result, 'duplicate JSON key'); result[key] = value
    return result

def loads(text): return json.loads(text, object_pairs_hook=pairs)

def fields(obj, names): ensure(isinstance(obj, dict) and set(obj) == set(names.split()), 'unknown fields')

def check_research(d):
    fields(d, 'version as_of publication live_market_data automated_report_ingestion sources streams topics events company_checks')
    ensure(d['version']=='0.3.0' and d['publication']=='public_dashboard', 'release metadata')
    ensure(d['live_market_data'] is False and d['automated_report_ingestion'] is False, 'unverified automation')
    asof = date.fromisoformat(d['as_of'])
    for key, count in [('sources',3),('streams',5),('topics',13),('events',8)]:
        rows=d[key]; ensure(isinstance(rows,list) and len(rows)==count, 'record count')
        ids=[x['id'] for x in rows]; ensure(len(set(ids))==count, 'duplicate record')
        ensure(all(isinstance(i,str) and re.fullmatch(r'[a-z0-9-]+',i) for i in ids), 'record identifier')
    ensure({s['id'] for s in d['sources']}==set(SOURCES), 'source set')
    for s in d['sources']:
        fields(s,'id label url checked_at'); ensure(s['url']==SOURCES[s['id']], 'source URL')
        ensure(date.fromisoformat(s['checked_at'])<=asof, 'future source date')
    stream_ids={'brief','breaking','event','autumn','topix'}
    ensure({s['id'] for s in d['streams']}==stream_ids, 'stream set')
    for s in d['streams']: fields(s,'id label scope')
    for t in d['topics']:
        fields(t,'id title category priority streams summary question refutation claim_type')
        ensure(t['claim_type']=='research_question' and t['priority'] in {'P1','P2'}, 'topic classification')
        ensure(t['category'] in {'macro','ai','japan','flow','frontier'}, 'topic category')
        ensure(isinstance(t['streams'],list) and t['streams'] and len(t['streams'])==len(set(t['streams'])) and set(t['streams'])<=stream_ids, 'topic routing')
    for e in d['events']:
        fields(e,'id title start end zone time_local time_jst source status')
        ensure(e['source'] in SOURCES and e['status']=='verified_schedule_only', 'event source/status')
        ensure(date.fromisoformat(e['start'])<=date.fromisoformat(e['end']), 'event order')
        ensure(e['zone'] in {'America/New_York','Asia/Tokyo'}, 'time zone')
        if e['time_local'] is None: ensure(e['time_jst'] is None, 'invented time')
        else:
            ensure(e['start']==e['end'] and re.fullmatch(r'\d{2}:\d{2}',e['time_local']), 'event time')
            local=datetime.fromisoformat(e['start']+'T'+e['time_local']).replace(tzinfo=ZoneInfo(e['zone']))
            ensure(e['time_jst']==local.astimezone(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M'), 'time conversion')
    ensure(isinstance(d['company_checks'],list) and len(d['company_checks'])==len(set(d['company_checks']))==14, 'company checklist')

class PageParser(HTMLParser):
    def __init__(self, allowed):
        super().__init__(convert_charrefs=True)
        self.allowed=allowed; self.csp=[]; self.referrer=[]; self.ids=set(); self.head=True
    def handle_starttag(self, tag, attrs):
        ensure(len(attrs)==len(dict(attrs)), 'duplicate attribute'); v=dict(attrs)
        ensure(tag not in {'iframe','object','embed','form','input','textarea','select','img','svg','math','audio','video','source','base','link'}, 'active tag')
        ensure(not any(k.startswith('on') for k,_ in attrs), 'inline handler')
        ensure(not any(k in v for k in ('src','srcset','srcdoc','ping')), 'resource attribute')
        if 'id' in v:
            ensure(v['id'] not in self.ids, 'duplicate id'); self.ids.add(v['id'])
        if 'href' in v:
            href=v['href'] or ''; safe=href.startswith('#') or href in self.allowed
            if href in SOURCES.values():
                ensure(tag=='a' and v.get('referrerpolicy')=='no-referrer' and {'noopener','noreferrer'}<=set(v.get('rel','').split()), 'source link policy'); safe=True
            ensure(safe, 'unapproved navigation')
        if tag=='body': self.head=False
        if tag=='meta':
            kind=v.get('http-equiv','').lower(); ensure(kind!='refresh', 'automatic navigation')
            if kind=='content-security-policy':
                ensure(self.head,'late CSP'); self.csp.append(v.get('content',''))
            if v.get('name','').lower()=='referrer': self.referrer.append(v.get('content'))
    def handle_startendtag(self, tag, attrs): self.handle_starttag(tag, attrs)

def check_html(text, allowed):
    page=PageParser(allowed); page.feed(text)
    scripts=re.findall(r'<script\b[^>]*>(.*?)</script\s*>',text,re.I|re.S)
    ensure(len(scripts)==1,'one reviewed program required'); script=scripts[0]
    ensure(not NETWORK.search(normalized(script)),'network or persistence')
    digest=base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    policy="default-src 'none'; script-src 'sha256-"+digest+"'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; font-src 'none'; object-src 'none'; frame-src 'none'; form-action 'none'; base-uri 'none'; upgrade-insecure-requests"
    ensure(page.csp==[policy] and page.referrer==['no-referrer'],'CSP or referrer mismatch')
    ensure(not re.search(r'@import|url\s*\(',text,re.I),'CSS resource')
    ensure(text.rstrip().endswith('</html>'),'incomplete HTML')

def validate_site(site):
    ensure(site.is_dir() and not site.is_symlink(),'site missing or linked')
    mp=site/'manifest.json'; ensure(mp.is_file() and not mp.is_symlink() and mp.stat().st_size<=1_000_000,'manifest')
    m=loads(mp.read_text(encoding='utf-8'))
    ensure(set(m)=={'version','classification','files'} and m['version']==2 and m['classification']=='public-market-research','manifest fields')
    files=m['files']; ensure(isinstance(files,dict) and 'index.html' in files and 'data/current-state.json' in files,'allowlist')
    for name,digest in files.items():
        ensure(isinstance(name,str) and re.fullmatch(r'[a-z0-9][a-z0-9_./-]*',name),'path')
        parts=PurePosixPath(name).parts
        ensure('..' not in parts and '.' not in parts and str(PurePosixPath(name))==name,'noncanonical path')
        ensure(Path(name).suffix in {'.html','.json','.md','.css','.js'},'extension')
        ensure(not any(p.startswith('.') or p in {'private','personal','accounts','credentials'} for p in parts),'restricted path')
        ensure(isinstance(digest,str) and re.fullmatch(r'[0-9a-f]{64}',digest),'digest')
    actual=set()
    for p in site.rglob('*'):
        ensure(not p.is_symlink() and (p.is_file() or p.is_dir()),'linked or special file')
        if p.is_file():
            ensure(p.stat().st_nlink==1,'hardlink'); actual.add(p.relative_to(site).as_posix())
    ensure(actual==set(files)|{'manifest.json'},'unapproved files')
    payload={}
    for name,digest in sorted(files.items()):
        p=site/name; ensure(p.stat().st_size<=1_000_000,'oversized')
        blob=p.read_bytes(); ensure(hashlib.sha256(blob).hexdigest()==digest,'unreviewed hash')
        text=blob.decode('utf-8'); scan(text)
        if p.suffix=='.html': check_html(text,set(files))
        elif p.suffix=='.json':
            value=loads(text); scan(json.dumps(value,ensure_ascii=False))
            if name=='data/current-state.json': check_research(value)
        elif p.suffix in {'.js','.css'}: ensure(not NETWORK.search(normalized(text)),'active code')
        payload[name]=blob
    return payload

def check_history():
    identities=subprocess.check_output(['git','log','--all','--format=%ae%n%ce'],cwd=ROOT,text=True).splitlines()
    ensure(identities and all(v=='noreply@github.com' or v.endswith('@users.noreply.github.com') for v in identities),'non-noreply identity; value suppressed')
    allowed={'README.md','.gitignore','scripts/check_site.py','tests/test_site.py','.github/workflows/pages.yml'}
    allowed|={'site/'+p for p in validate_site(ROOT/'site')}|{'site/manifest.json'}
    tracked=set(subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines())
    ensure(tracked==allowed,'repository allowlist')

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--check-history',action='store_true'); parser.add_argument('--build',action='store_true'); args=parser.parse_args()
    payload=validate_site(ROOT/'site')
    if args.check_history: check_history()
    if args.build:
        dest=ROOT/'.pages-build'; ensure(not dest.is_symlink(),'linked output')
        if dest.exists(): shutil.rmtree(dest)
        for name,blob in payload.items():
            target=dest/name; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(blob)
        (dest/'.nojekyll').write_text('',encoding='utf-8')
    print(f'PASS: {len(payload)} reviewed files; sensitive values suppressed')
if __name__=='__main__':
    try: main()
    except (ValueError,OSError,UnicodeError,TypeError,KeyError,subprocess.SubprocessError):
        raise SystemExit('PUBLICATION BLOCKED: inspect privately; do not log sensitive values')
