"""Extend the existing fail-closed publication boundary by reviewed typed public datasets."""
import argparse,hashlib,html,json,os,re,shutil
from pathlib import Path
import check_site as gate
import macro_core as macro
import publication_rights as rights
import calendar_rights
import dashboard_finalize as presentation
import relationship_registry as relationships
import systemic_registry as systemic
import company_theme_expansion as expansion
import relevance_scoring as relevance
import phase3_feed_health as feed_health
ROOT=Path(__file__).resolve().parents[1]
REGISTRY_URLS={r['source_url'] for r in systemic.INDEXES+systemic.COMPANIES}
RELATIONSHIP_URLS={r['source_url'] for r in relationships.RELATIONSHIPS}
EXPANSION_URLS={r['source_url'] for r in expansion.RELATIONSHIPS}
EXTRA_FILES={'scripts/calendar_snapshot.py','scripts/calendar_publish.py','scripts/run_legacy_tests.py','scripts/macro_core.py','scripts/macro_fetch.py','scripts/wti_probe.py','scripts/build_release.py','scripts/check_release.py','scripts/browser_release.mjs','scripts/release_assertions.js','scripts/dashboard_finalize.py','scripts/presentation_rights.py','scripts/release_state.py','scripts/policy_events.py','scripts/executive_overview.py','scripts/systemic_registry.py','scripts/relationship_registry.py','scripts/company_theme_expansion.py','scripts/relevance_scoring.py','scripts/phase2_overview.py','scripts/phase2_rights.py','scripts/phase3_feed_health.py','scripts/phase3_rights.py','templates/macro.js','templates/macro.css','tests/test_release.py','tests/test_browser_retry.py','tests/test_dashboard_finalize.py','tests/test_release_state.py','tests/test_policy_events.py','tests/test_executive_overview.py','tests/test_systemic_registry.py','tests/test_relationship_registry.py','tests/test_company_theme_expansion.py','tests/test_relevance_scoring.py','tests/test_phase2_overview.py','tests/test_phase3_feed_health.py','tests/test_wti_fallback.py','tests/test_wti_probe.py','docs/data-rights.md','docs/release-v060.md','docs/v07-executive-overview-phase1.md','scripts/publication_rights.py','tests/test_rights.py','data-rights/registry.json','data-rights/migration-baseline.json','data-rights/README.md','scripts/market_refresh_guard.py','tests/test_market_refresh_guard.py','docs/market-data-automation.md','docs/market-data-provider-review-2026-09-14.md','scripts/sec_filings.py','tests/test_sec_filings.py','scripts/calendar_probe.py','tests/test_calendar_probe.py','tests/test_calendar_publish.py','docs/calendar-data-rights-review.md','scripts/calendar_rights.py','data-rights/calendar-approvals.json','tests/test_calendar_rights.py'}
def validate(site:Path, rights_reports=None, require_overview=False):
 gate.PAYLOAD |= {'data/macro.json','data/macro-calendar.json'};gate.URLS |= macro.URLS|REGISTRY_URLS|RELATIONSHIP_URLS|EXPANSION_URLS;gate.REPO |= EXTRA_FILES
 payload=gate.validate(site);m=gate.loads(payload['data/macro.json']);c=gate.loads(payload['data/macro-calendar.json']);macro.validate(m);macro.validate_calendar(c);s=payload['index.html'].decode()
 expansion_meta=expansion.validate();gate.require(expansion_meta['seed_company_coverage']==12 and expansion_meta['relationship_count']==7 and expansion_meta['monitor_count']==5,'Company/theme expansion coverage mismatch')
 relevance_meta=relevance.validate();gate.require(relevance_meta['relationship_count']==21 and relevance_meta['immediate_count']==8 and relevance_meta['active_count']==11 and relevance_meta['watch_count']==1 and relevance_meta['structural_count']==1,'Relevance scoring coverage mismatch')
 for id,name in [('macro-data','data/macro.json'),('macro-calendar-data','data/macro-calendar.json')]:
  match=re.search('<pre id="'+id+'" hidden>(.*?)</pre>',s,re.S);gate.require(match and gate.loads(html.unescape(match[1]))==gate.loads(payload[name]),'Macro embedded mismatch')
 gate.require(s.count("version:'0.6.0'")==2 and 'macro-chart-' in s,'Actual release program')
 if require_overview:
  gate.require(s.count('data-v07-executive-overview="true"')==1,'Executive Overview missing or duplicated')
  gate.require(s.count('data-systemic-registry="true"')==1,'Systemic registry missing or duplicated')
  gate.require(s.count('data-registry-index=')==12 and s.count('data-registry-company=')==12,'Systemic registry cardinality mismatch')
  gate.require('12指数 + 12発行体を共通IDで管理' in s and 'identity metadata only' in s,'Systemic registry disclosure missing')
  gate.require(s.count('data-relationship-registry="true"')==1,'Relationship registry missing or duplicated')
  gate.require(s.count('data-relationship=')==14 and s.count('data-catalyst=')==3,'Relationship registry cardinality mismatch')
  gate.require('Event → Macro → Index → Issuer の根拠付き接続' in s and 'Relationshipは因果を自動認定しません' in s,'Relationship disclosure missing')
  gate.require(s.count('data-company-theme-expansion="true"')==1,'Company/theme expansion missing or duplicated')
  gate.require(s.count('data-company-theme-relationship=')==7 and s.count('data-company-theme-monitor=')==5,'Company/theme presentation cardinality mismatch')
  gate.require('12/12 seed issuers をEvidence Graphへ接続' in s and 'Evidence relationships</div><div class="metric">21</div>' in s,'Company/theme coverage disclosure missing')
  gate.require('coverage ≠ ranking' in s and 'MONITORは売買シグナルではなく' in s,'Company/theme interpretation disclosure missing')
  gate.require('Systemic Market Map' in s and 'BULL / INFERENCE' in s and 'BASE / INFERENCE' in s and 'BEAR / INFERENCE' in s,'Executive Overview analytical layers missing')
  gate.require(s.count('data-relevance-scoring="true"')==1 and s.count('data-relevance-score=')==21,'Relevance scoring Phase 2 missing or incomplete')
  gate.require('Immediate</div><div class="metric">8</div>' in s and 'Active</div><div class="metric">11</div>' in s and 'Watch</div><div class="metric">1</div>' in s and 'Structural</div><div class="metric">1</div>' in s,'Relevance attention counts missing')
  gate.require('LIVE MARKET / PROVIDER-HOSTED' in s and 'TradingView Widgetが閲覧時に配信' in s,'Current-market provider-hosted disclosure missing')
  gate.require("価格の最終収録は '+D.as_of+'" not in s and "pct(ret(a))+' / 9.8 - 9.10'" not in s,'Archive price leaked into current overview runtime')
  gate.require(s.count(feed_health.MARKER)==1,'Market Feed Health missing or duplicated')
  gate.require(s.count('data-feed-delivery="provider_hosted"')==3 and s.count('data-quote-mode="provider_determined"')==3,'Provider feed-health cardinality mismatch')
  gate.require('real-time / delayed / EODはProvider・取引所条件で決まり、当ビルドは判定しません' in s,'Quote-mode disclosure missing')
  gate.require('data-quote-mode="realtime"' not in s and 'Archiveへの自動fallbackもしません' in s,'Feed-health safety boundary missing')
  for series in m['series']:gate.require('data-macro-feed="'+series['id']+'" data-source-status="'+series['status']+'"' in s,'Macro source-health mismatch')
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
