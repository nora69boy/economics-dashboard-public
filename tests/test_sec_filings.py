import sys,unittest,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import sec_filings as s

def payload(ticker):
 cik,name=s.COMPANIES[ticker]
 return {'cik':int(cik),'name':name,'filings':{'recent':{
  'accessionNumber':['0000000000-26-000001','0000000000-26-000002'],
  'filingDate':['2026-09-10','2026-08-01'],'reportDate':['2026-09-10','2026-07-31'],
  'form':['8-K','10-Q'],'primaryDocument':['a.htm','b.htm']}}}

class SecFilingsTests(unittest.TestCase):
 def test_normalize_relevant_filings(self):
  r=s.normalize('NVDA',payload('NVDA'));self.assertEqual(r['ticker'],'NVDA');self.assertEqual([x['form'] for x in r['latest']],['8-K','10-Q']);self.assertTrue(r['latest'][0]['filing_url'].startswith('https://www.sec.gov/Archives/edgar/data/'))
 def test_reject_wrong_cik(self):
  p=payload('NVDA');p['cik']=1
  with self.assertRaises(ValueError):s.normalize('NVDA',p)
 def test_probe_fresh(self):
  def f(url):
   ticker=next(t for t,(cik,_) in s.COMPANIES.items() if cik in url);return payload(ticker)
  r=s.probe(f,lambda _:None);self.assertEqual(r['sec_probe_health'],'fresh');self.assertEqual(len(r['companies']),5);self.assertEqual(r['publication'],'disabled_pending_rights_approval')
 def test_probe_degraded_without_throwing(self):
  calls={'n':0}
  def f(url):
   calls['n']+=1
   if calls['n']==1:raise OSError('synthetic')
   ticker=next(t for t,(cik,_) in s.COMPANIES.items() if cik in url);return payload(ticker)
  r=s.probe(f,lambda _:None);self.assertEqual(r['sec_probe_health'],'degraded');self.assertEqual(len(r['errors']),1);self.assertEqual(len(r['companies']),4)
 def test_all_403_is_source_access_blocked(self):
  def f(url):raise urllib.error.HTTPError(url,403,'Forbidden',None,None)
  r=s.probe(f,lambda _:None);self.assertEqual(r['sec_probe_health'],'source_access_blocked');self.assertEqual({e['error'] for e in r['errors']},{'HTTP_403'})
 def test_no_publication_side_effect(self):
  before=(ROOT/'site/data/market.json').read_bytes();s.probe(lambda url:payload(next(t for t,(cik,_) in s.COMPANIES.items() if cik in url)),lambda _:None);self.assertEqual((ROOT/'site/data/market.json').read_bytes(),before)
if __name__=='__main__':unittest.main()
