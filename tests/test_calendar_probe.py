import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import calendar_probe as c

BLS=b'''BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nDTSTART:20261014T083000\r\nSUMMARY:Consumer Price Index - September 2026\r\nEND:VEVENT\r\nBEGIN:VEVENT\r\nDTSTART:20261002T083000\r\nSUMMARY:Employment Situation - September 2026\r\nEND:VEVENT\r\nEND:VCALENDAR'''
BEA=b'''<html><body>September 30 8:30 AM Personal Income and Outlays, August 2026 October 29 8:30 AM Personal Income and Outlays, September 2026 November 25 8:30 AM Personal Income and Outlays, October 2026 December 23 8:30 AM Personal Income and Outlays, November 2026</body></html>'''
FED=b'''<html><body><h2>2026 FOMC Meetings</h2>January 27-28 March 17-18 April 28-29 June 16-17 July 28-29 September 15-16 October 27-28 December 8-9 <h2>2025 FOMC Meetings</h2></body></html>'''

class CalendarProbeTests(unittest.TestCase):
 def test_bls_ics_and_dst(self):
  e=c.parse_bls_ics(BLS);self.assertEqual(len(e),2);self.assertEqual(next(x for x in e if x['family']=='cpi')['time_jst'],'2026-10-14 21:30')
 def test_bea(self):
  e=c.parse_bea(BEA);self.assertEqual(len(e),4);self.assertEqual(e[0]['period'],'2026-08');self.assertEqual(e[0]['time_jst'],'2026-09-30 21:30')
 def test_fed(self):
  e=c.parse_fed(FED);self.assertEqual(len(e),8);self.assertEqual(e[-1]['date'],'2026-12-09')
 def test_probe_fresh(self):
  def f(url):
   if url==c.BLS_ICS:return BLS
   if url==c.BEA_SCHEDULE:return BEA
   return FED
  r=c.probe(f);self.assertEqual(r['calendar_probe_health'],'fresh');self.assertEqual(len(r['errors']),0);self.assertGreaterEqual(len(r['candidate_events']),14);self.assertEqual(r['publication'],'disabled_pending_rights_approval')
 def test_no_publication_side_effect(self):
  target=ROOT/'site/data/macro-calendar.json';existed=target.exists();before=target.read_bytes() if existed else None
  def f(url):return BLS if url==c.BLS_ICS else (BEA if url==c.BEA_SCHEDULE else FED)
  c.probe(f);self.assertEqual(target.exists(),existed)
  if existed:self.assertEqual(target.read_bytes(),before)
if __name__=='__main__':unittest.main()
