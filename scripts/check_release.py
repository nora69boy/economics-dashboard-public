"""Extend the existing fail-closed publication boundary by two precisely typed public datasets."""
import argparse,hashlib,html,json,os,re,shutil
from pathlib import Path
import check_site as gate
import macro_core as macro
import publication_rights as rights
ROOT=Path(__file__).resolve().parents[1]
EXTRA_FILES={'scripts/calendar_snapshot.py','scripts/run_legacy_tests.py','scripts/macro_core.py','scripts/macro_fetch.py','scripts/build_release.py','scripts/check_release.py','scripts/browser_release.mjs','scripts/release_assertions.js','templates/macro.js','templates/macro.css','tests/test_release.py','docs/data-rights.md','docs/release-v060.md','scripts/publication_rights.py','tests/test_rights.py','data-rights/registry.json','data-rights/migration-baseline.json','data-rights/README.md'}
def validate(site:Path, rights_reports=None):
 gate.PAYLOAD |= {'data/macro.json','data/macro-calendar.json'};gate.URLS |= macro.URLS;gate.REPO |= EXTRA_FILES
 payload=gate.validate(site);m=gate.loads(payload['data/macro.json']);c=gate.loads(payload['data/macro-calendar.json']);macro.validate(m);macro.validate_calendar(c);s=payload['index.html'].decode()
 for id,name in [('macro-data','data/macro.json'),('macro-calendar-data','data/macro-calendar.json')]:
  match=re.search('<pre id="'+id+'" hidden>(.*?)</pre>',s,re.S);gate.require(match and gate.loads(html.unescape(match[1]))==gate.loads(payload[name]),'Macro embedded mismatch')
 gate.require(s.count("version:'0.6.0'")==2 and 'macro-chart-' in s,'Actual release program');gate.require((ROOT/'templates/macro.js').read_text() in s,'Macro template mismatch')
 report=rights.enforce(payload)
 if rights_reports is not None:rights_reports.append(report)
 return payload

def history():
 old=gate.PAYLOAD.copy();gate.PAYLOAD.discard('data/macro.json');gate.PAYLOAD.discard('data/macro-calendar.json')
 try:gate.history()
 finally:gate.PAYLOAD=old

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check-history',action='store_true');ap.add_argument('--build',action='store_true');args=ap.parse_args();reports=[]
 try:out=validate(ROOT/'site',reports)
 except rights.PublicationBlocked as exc:
  rights.emit(exc.report);raise SystemExit('PUBLICATION RIGHTS BLOCKED') from None
 except rights.RightsError:
  raise SystemExit('PUBLICATION RIGHTS BLOCKED: invalid or missing policy; details suppressed') from None
 rights.emit(reports[0])
 if args.check_history:history()
 if args.build:
  dest=ROOT/'.pages-build';gate.require(not dest.is_symlink(),'Output symlink')
  if dest.exists():shutil.rmtree(dest)
  for n,b in out.items():p=dest/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  (dest/'.nojekyll').write_text('')
 digest=hashlib.sha256(out['index.html']).hexdigest()
 if os.environ.get('GITHUB_OUTPUT'):
  with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('index_sha='+digest+'\n')
 print('PASS: 6 validated public files; index SHA-256 '+digest)
if __name__=='__main__':main()
