import sys,unittest,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import calendar_probe as c

BLS=b'''BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nDTSTART:20261014T083000\r\nSUMMARY:Consumer Price Index - September 2026\r\nEND:VEVENT\r\nBEGIN:VEVENT\r\nDTSTART:20261002T083000\r\nSUMMARY:Employment Situation - September 2026\r\nEND:VEVENT\r\nEND:VCALENDAR'''
BLS_CPI_HTML=b'''<html><body><h1>Schedule of Releases for the Consumer Price Index</h1><table><tr><td>December 2025</td><td>Jan. 13, 2026</td><td>08:30 AM</td></tr><tr><td>January 2026</td><td>Feb. 13, 2026</td><td>08:30 AM</td></tr><tr><td>February 2026</td><td>Mar. 11, 2026</td><td>08:30 AM</td></tr><tr><td>March 2026</td><td>Apr. 10, 2026</td><td>08:30 AM</td></tr><tr><td>April 2026</td><td>May 12, 2026</td><td>08:30 AM</td></tr><tr><td>May 2026</td><td>Jun. 10, 2026</td><td>08:30 AM</td></tr><tr><td>June 2026</td><td>Jul. 14, 2026</td><td>08:30 AM</td></tr><tr><td>July 2026</td><td>Aug. 12, 2026</td><td>08:30 AM</td></tr><tr><td>August 2026</td><td>Sep. 11, 2026</td><td>08:30 AM</td></tr><tr><td>September 2026</td><td>Oct. 14, 2026</td><td>08:30 AM</td></tr><tr><td>October 2026</td><td>Nov. 10, 2026</td><td>08:30 AM</td></tr><tr><td>November 2026</td><td>Dec. 10, 2026</td><td>08:30 AM</td></tr></table></body></html>'''
BLS_JOBS_HTML=b'''<html><body><h1>Schedule of Releases for the Employment Situation</h1><table><tr><td>December 2025</td><td>Jan. 9, 2026</td><td>08:30 AM</td></tr><tr><td>January 2026</td><td>Feb. 11, 2026</td><td>08:30 AM</td></tr><tr><td>February 2026</td><td>Mar. 6, 2026</td><td>08:30 AM</td></tr><tr><td>March 2026</td><td>Apr. 3, 2026</td><td>08:30 AM</td></tr><tr><td>April 2026</td><td>May 8, 2026</td><td>08:30 AM</td></tr><tr><td>May 2026</td><td>Jun. 5, 2026</td><td>08:30 AM</td></tr><tr><td>June 2026</td><td>Jul. 2, 2026</td><td>08:30 AM</td></tr><tr><td>July 2026</td><td>Aug. 7, 2026</td><td>08:30 AM</td></tr><tr><td>August 2026</td><td>Sep. 4, 2026</td><td>08:30 AM</td></tr><tr><td>September 2026</td><td>Oct. 2, 2026</td><td>08:30 AM</td></tr><tr><td>October 2026</td><td>Nov. 6, 2026</td><td>08:30 AM</td></tr><tr><td>November 2026</td><td>Dec. 4, 2026</td><td>08:30 AM</td></tr></table></body></html>'''
BEA=b'''<html><body>September 30 8:30 AM Personal Income and Outlays, August 2026 October 29 8:30 AM Personal Income and Outlays, September 2026 November 25 8:30 AM Personal Income and Outlays, October 2026 December 23 8:30 AM Personal Income and Outlays, November 2026</body></html>'''
FED=b'''<html><body><h2>2026 FOMC Meetings</h2>January 27-28 March 17-18 April 28-29 June 16-17 July 28-29 September 15-16 October 27-28 December 8-9 <h2>2025 FOMC Meetings</h2></body></html>'''

class CalendarProbeTests(unittest.TestCase):
 def test_bls_ics_and_dst(self):
  e=c.parse_bls_ics(BLS);self.assertEqual(len(e),2);self.assertEqual(next(x for x in e if x['family']=='cpi')['time_jst'],'2026-10-14 21:30')
 def test_bls_cpi_html(self):
  e=c.parse_bls_release_html(BLS_CPI_HTML,'cpi',c.BLS_CPI);self.assertEqual(len(e),12);self.assertEqual(e[9]['period'],'2026-09');self.assertEqual(e[9]['date'],'2026-10-14');self.assertEqual(e[9]['time_jst'],'2026-10-14 21:30')
 def test_bls_jobs_html(self):
  e=c.parse_bls_release_html(BLS_JOBS_HTML,'jobs',c.BLS_JOBS);self.assertEqual(len(e),12);self.assertEqual(e[9]['date'],'2026-10-02')
 def test_bea(self):
  e=c.parse_bea(BEA);self.assertEqual(len(e),4);self.assertEqual(e[0]['period'],'2026-08');self.assertEqual(e[0]['time_jst'],'2026-09-30 21:30')
 def test_fed(self):
  e=c.parse_fed(FED);self.assertEqual(len(e),8);self.assertEqual(e[-1]['date'],'2026-12-09')
 def test_probe_fresh_primary_ics(self):
  def f(url):
   if url==c.BLS_ICS:return BLS
   if url==c.BEA_SCHEDULE:return BEA
   return FED
  r=c.probe(f);self.assertEqual(r['calendar_probe_health'],'fresh');self.assertEqual(len(r['errors']),0);self.assertEqual(r['source_modes']['bls'],'ics');self.assertGreaterEqual(len(r['candidate_events']),14)
 def test_ics_403_uses_html_fallback(self):
  def f(url):
   if url==c.BLS_ICS:raise urllib.error.HTTPError(url,403,'Forbidden',None,None)
   if url==c.BLS_CPI:return BLS_CPI_HTML
   if url==c.BLS_JOBS:return BLS_JOBS_HTML
   if url==c.BEA_SCHEDULE:return BEA
   return FED
  r=c.probe(f);self.assertEqual(r['calendar_probe_health'],'fresh');self.assertEqual(r['source_modes']['bls'],'html_fallback');self.assertEqual(len(r['errors']),0);self.assertEqual(r['advisories'],[{'source':'bls-ics','error':'HTTPError','code':403}]);self.assertEqual(len(r['candidate_events']),36)
 def test_html_parser_failure_remains_degraded(self):
  def f(url):
   if url==c.BLS_ICS:raise urllib.error.HTTPError(url,403,'Forbidden',None,None)
   if url==c.BLS_CPI:return b'broken'
   if url==c.BLS_JOBS:return BLS_JOBS_HTML
   if url==c.BEA_SCHEDULE:return BEA
   return FED
  r=c.probe(f);self.assertEqual(r['calendar_probe_health'],'degraded');self.assertEqual(r['source_modes']['bls'],'partial_html_fallback');self.assertEqual(r['errors'][0]['source'],'bls-cpi-html')
 def test_no_publication_side_effect(self):
  target=ROOT/'site/data/macro-calendar.json';existed=target.exists();before=target.read_bytes() if existed else None
  def f(url):return BLS if url==c.BLS_ICS else (BEA if url==c.BEA_SCHEDULE else FED)
  c.probe(f);self.assertEqual(target.exists(),existed)
  if existed:self.assertEqual(target.read_bytes(),before)
if __name__=='__main__':unittest.main()
