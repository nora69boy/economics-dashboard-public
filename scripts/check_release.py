"""Extend the existing fail-closed publication boundary by reviewed typed public datasets."""
import argparse,hashlib,html,json,os,re,shutil
from pathlib import Path
import check_site as gate
import macro_core as macro
import publication_rights as rights
import calendar_rights
import dashboard_finalize as presentation
import systemic_registry as systemic
ROOT=Path(__file__).resolve().parents[1]
REGISTRY_URLS={r['source_url'] for r in systemic.INDEXES+systemic.COMPANIES}
EXTRA_FILES={'scripts/calendar_snapshot.py','scripts/calendar_publish.py','scripts/run_legacy_tests.py','scripts/macro_core.py','scripts/macro_fetch.py','scripts/build_release.py','scripts/check_release.py','scripts/browser_release.mjs','scripts/release_assertions.js','scripts/dashboard_finalize.py','scripts/presentation_rights.py','scripts/release_state.py','scripts/policy_events.py','scripts/executive_overview.py','scripts/systemic_registry.py','templates/macro.js','templates/macro.css','tests/test_release.py','tests/test_browser_retry.py','tests/test_dashboard_finalize.py','tests/test_release_state.py','tests/test_policy_events.py','tests/test_executive_overview.py','tests/test_systemic_registry.py','docs/data-rights.md','docs/release-v060.md','docs/v07-executive-overview-phase1.md','scripts/publication_rights.py','tests/test_rights.py','data-rights/registry.json','data-rights/migration-baseline.json','data-rights/README.md','scripts/market_refresh_guard.py','tests/test_market_refresh_guard.py','docs/market-data-automation.md','docs/market-data-provider-review-2026-09-14.md','scripts/sec_filings.py','tests/test_sec_filings.py','scripts/calendar_probe.py','tests/test_calendar_probe.py','tests/test_calendar_publish.py','docs/calendar-data-rights-review.md','scripts/calendar_rights.py','data-rights/calendar-approvals.json','tests/test_calendar_rights.py'}
def validate(site:Path, rights_reports=None, require_overview=False):
 gate.PAYLOAD |= {'data/macro.json','data/macro-calendar.json'};gate.URLS |= macro.URLS|REGISTRY_URLS;gate.REPO |= EXTRA_FILES
 payload=gate.validate(site);m=gate.loads(payload['data/macro.json']);c=gate.loads(payload['data/macro-calendar.json']);macro.validate(m);macro.validate_calendar(c);s=payload['index.html'].decode()
 for id,name in [('macro-data','data/macro.json'),('macro-calendar-data','data/macro-calendar.json')]:
  match=re.search('<pre id="'+id+'" hidden>(.*?)</pre>',s,re.S);gate.require(match and gate.loads(html.unescape(match[1]))==gate.loads(payload[name]),'Macro embedded mismatch')
 gate.require(s.count("version:'0.6.0'")==2 and 'macro-chart-' in s,'Actual release program')
 if require_overview:
  gate.require(s.count('data-v07-executive-overview="true"')==1,'Executive Overview missing or duplicated')
  gate.require(s.count('data-systemic-registry="true"')==1,'Systemic registry missing or duplicated')
  gate.require(s.count('data-registry-index=')==12 and s.count('data-registry-company=')==12,'Systemic registry cardinality mismatch')
  gate.require('12指数 + 12発行体を共通IDで管理' in s and 'identity metadata only' in s,'Systemic registry disclosure missing')
  gate.require('Systemic Market Map' in s and 'BULL / INFERENCE' in s and 'BASE / INFERENCE' in s and 'BEAR / INFERENCE' in s,'Executive Overview analytical layers missing')
 source_macro=(ROOT/'templates/macro.js').read_text();gate.require(source_macro.count(presentation.AGE_OLD)==1,'Macro presentation transform source');expected_macro=source_macro.replace(presentation.AGE_OLD,presentation.AGE_NEW,1);gate.require(sum((source_macro in s,expected_macro in s))==1,'Macro template state')
 report=calendar_rights.enforce(payload)
 if rights_reports is not None:rights_reports.append(report)
 return payload

def history():
 old=gate.PAYLOAD.copy();gate.PAYLOAD.discard('data/macro.json');gate.PAYLOAD.discard('data/macro-calendar.json')
 try:gate.history()
 finally:gate.PAYLOAD=old

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check-history',action='store_true');ap.add_argument('--build',action='store_true');args=ap.parse_args();reports=[]
 try:out=validate(ROOT/'site',reports,require_overview=True)
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
