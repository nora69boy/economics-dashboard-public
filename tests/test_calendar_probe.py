import sys,unittest,urllib.error
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import calendar_probe as c

NOW=datetime(2026,9,13,18,0,tzinfo=timezone.utc)
BLS=b'''BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nDTSTART:20261014T083000\r\nSUMMARY:Consumer Price Index - September 2026\r\nEND:VEVENT\r\nBEGIN:VEVENT\r\nDTSTART:20261002T083000\r\nSUMMARY:Employment Situation - September 2026\r\nEND:VEVENT\r\nEND:VCALENDAR'''

def bls_html(title,release_year):
 months=list(c.MONTHS);abbr=list(c.ABBR);periods=[('December',release_year-1)]+[(m,release_year) for m in months[:11]]
 rows=''.join(f'<tr><td>{ref} {ref_year}</td><td>{abbr[i]} 15, {release_year}</td><td>08:30 AM</td></tr>' for i,(ref,ref_year) in enumerate(periods))
 return f'<html><body><h1>Schedule of Releases for the {title}</h1><table>{rows}</table></body></html>'.encode()

BLS_CPI_HTML=bls_html('Consumer Price Index',2026)
BLS_JOBS_HTML=bls_html('Employment Situation',2026)
BLS_CPI_BOTH=BLS_CPI_HTML.replace(b'</table>',bls_html('Consumer Price Index',2027).split(b'<table>',1)[1].split(b'</table>',1)[0]+b'</table>')
BLS_JOBS_BOTH=BLS_JOBS_HTML.replace(b'</table>',bls_html('Employment Situation',2027).split(b'<table>',1)[1].split(b'</table>',1)[0]+b'</table>')
BEA=b'''<html><body>Year 2026 September 30 8:30 AM Personal Income and Outlays, August 2026 October 29 8:30 AM Personal Income and Outlays, September 2026 November 25 8:30 AM Personal Income and Outlays, October 2026 December 23 8:30 AM Personal Income and Outlays, November 2026</body></html>'''
BEA_EMPTY=b'''<html><body>Release Schedule See the Next Year tab for upcoming releases.</body></html>'''

def bea_next(count=12):
 months=list(c.MONTHS);periods=[('December',2026)]+[(m,2027) for m in months[:11]];rows=[]
 for i,(ref,ref_year) in enumerate(periods[:count]):
  rows.append(f'{months[i]} 15 8:30 AM Personal Income and Outlays, {ref} {ref_year}')
 return ('<html><body>Release Schedule Year 2027 '+' '.join(rows)+'</body></html>').encode()

BEA_NEXT=bea_next()
BEA_NEXT_PARTIAL=bea_next(11)
FED=b'''<html><body><h2>2026 FOMC Meetings</h2>January 27-28 March 17-18 April 28-29 June 16-17 July 28-29 September 15-16 October 27-28 December 8-9 <h2>2025 FOMC Meetings</h2>January 28-29 <h2>2027 FOMC Meetings</h2>January 26-27 March 16-17 April 27-28 June 8-9 July 27-28 September 14-15 October 26-27 December 7-8 Note: A two-day meeting is scheduled for January 25-26, 2028.</body></html>'''
FED_2026_ONLY=b'''<html><body><h2>2026 FOMC Meetings</h2>January 27-28 March 17-18 April 28-29 June 16-17 July 28-29 September 15-16 October 27-28 December 8-9 <h2>2025 FOMC Meetings</h2></body></html>'''


def fetcher(bls_ics=BLS,cpi=BLS_CPI_HTML,jobs=BLS_JOBS_HTML,bea_next_raw=BEA_EMPTY,fed=FED):
 def f(url):
  if url==c.BLS_ICS:
   if isinstance(bls_ics,Exception):raise bls_ics
   return bls_ics
  if url==c.BLS_CPI:return cpi
  if url==c.BLS_JOBS:return jobs
  if url==c.BEA_SCHEDULE:return BEA
  if url==c.BEA_NEXT_YEAR:return bea_next_raw
  if url==c.FED_FOMC:return fed
  raise AssertionError(url)
 return f

class CalendarProbeTests(unittest.TestCase):
 def test_bls_ics_and_dst(self):
  e=c.parse_bls_ics(BLS);self.assertEqual(len(e),2);self.assertEqual(next(x for x in e if x['family']=='cpi')['time_jst'],'2026-10-14 21:30')
 def test_bls_cpi_html(self):
  e=c.parse_bls_release_html(BLS_CPI_HTML,'cpi',c.BLS_CPI);self.assertEqual(len(e),12);self.assertEqual(e[0]['period'],'2025-12');self.assertEqual(e[-1]['period'],'2026-11')
 def test_bls_html_can_discover_current_and_next_year(self):
  e=c.parse_bls_release_html(BLS_CPI_BOTH,'cpi',c.BLS_CPI,None);self.assertEqual(len(e),24);self.assertEqual(len([x for x in e if x['date'].startswith('2027-')]),12)
 def test_bls_jobs_html(self):
  e=c.parse_bls_release_html(BLS_JOBS_HTML,'jobs',c.BLS_JOBS);self.assertEqual(len(e),12);self.assertEqual(e[0]['date'],'2026-01-15')
 def test_bea(self):
  e=c.parse_bea(BEA);self.assertEqual(len(e),4);self.assertEqual(e[0]['period'],'2026-08');self.assertEqual(e[0]['time_jst'],'2026-09-30 21:30')
 def test_bea_complete_next_year_parser(self):
  e=c.parse_bea(BEA_NEXT,2027,c.BEA_NEXT_YEAR);self.assertTrue(c.complete_monthly_year(e,2027));self.assertEqual(len(e),12);self.assertEqual({x['source'] for x in e},{c.BEA_NEXT_YEAR})
 def test_fed_current_and_next_year(self):
  current=c.parse_fed(FED,2026);future=c.parse_fed(FED,2027);self.assertEqual(len(current),8);self.assertEqual(len(future),8);self.assertEqual(future[0]['date'],'2027-01-27');self.assertEqual(future[-1]['date'],'2027-12-08')
 def test_probe_fresh_primary_ics_discovers_next_fomc_year(self):
  r=c.probe(fetcher(),NOW);self.assertEqual(r['calendar_probe_health'],'fresh');self.assertEqual(len(r['errors']),0);self.assertEqual(r['source_modes']['bls'],'ics');self.assertEqual(r['source_modes']['bea'],'primary');self.assertEqual(r['source_modes']['fed'],'primary_current_plus_next_year');self.assertEqual(len([e for e in r['candidate_events'] if e['family']=='fomc' and e['date'].startswith('2027-')]),8)
 def test_probe_stages_complete_next_bea_year(self):
  r=c.probe(fetcher(bea_next_raw=BEA_NEXT),NOW);self.assertEqual(r['source_modes']['bea'],'primary_current_plus_next_year');self.assertEqual(len([e for e in r['candidate_events'] if e['family']=='pce' and e['date'].startswith('2027-')]),12)
 def test_probe_rejects_partial_next_bea_year(self):
  r=c.probe(fetcher(bea_next_raw=BEA_NEXT_PARTIAL),NOW);self.assertEqual(r['source_modes']['bea'],'primary_next_year_incomplete');self.assertFalse(any(e['family']=='pce' and e['date'].startswith('2027-') for e in r['candidate_events']));self.assertIn({'source':'bea-next-year','error':'ScheduleIncomplete','code':None},r['advisories'])
 def test_probe_without_next_fomc_year_stays_current_only(self):
  r=c.probe(fetcher(fed=FED_2026_ONLY),NOW);self.assertEqual(r['source_modes']['fed'],'primary');self.assertFalse(any(e['family']=='fomc' and e['date'].startswith('2027-') for e in r['candidate_events']))
 def test_ics_403_uses_html_fallback(self):
  err=urllib.error.HTTPError(c.BLS_ICS,403,'Forbidden',None,None);r=c.probe(fetcher(bls_ics=err),NOW);self.assertEqual(r['calendar_probe_health'],'fresh');self.assertEqual(r['source_modes']['bls'],'html_fallback');self.assertEqual(len(r['errors']),0);self.assertEqual(r['advisories'],[{'source':'bls-ics','error':'HTTPError','code':403}]);self.assertEqual(len(r['candidate_events']),44)
 def test_html_fallback_discovers_next_bls_year(self):
  err=urllib.error.HTTPError(c.BLS_ICS,403,'Forbidden',None,None);r=c.probe(fetcher(bls_ics=err,cpi=BLS_CPI_BOTH,jobs=BLS_JOBS_BOTH),NOW);self.assertEqual(r['source_modes']['bls'],'html_fallback_current_plus_next_year');self.assertEqual(len([e for e in r['candidate_events'] if e['family'] in {'cpi','jobs'} and e['date'].startswith('2027-')]),24)
 def test_html_parser_failure_remains_degraded(self):
  err=urllib.error.HTTPError(c.BLS_ICS,403,'Forbidden',None,None);r=c.probe(fetcher(bls_ics=err,cpi=b'broken'),NOW);self.assertEqual(r['calendar_probe_health'],'degraded');self.assertEqual(r['source_modes']['bls'],'partial_html_fallback');self.assertEqual(r['errors'][0]['source'],'bls-cpi-html')
 def test_no_publication_side_effect(self):
  target=ROOT/'site/data/macro-calendar.json';existed=target.exists();before=target.read_bytes() if existed else None;c.probe(fetcher(),NOW);self.assertEqual(target.exists(),existed)
  if existed:self.assertEqual(target.read_bytes(),before)
if __name__=='__main__':unittest.main()
