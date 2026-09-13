"""Probe SEC EDGAR submissions for tracked US companies without publishing the data."""
from __future__ import annotations
import argparse,json,os,time,urllib.error,urllib.request
from datetime import datetime,timezone

COMPANIES={
    'NVDA':('0001045810','NVIDIA CORP'),
    'MSFT':('0000789019','MICROSOFT CORP'),
    'AAPL':('0000320193','APPLE INC'),
    'GOOGL':('0001652044','Alphabet Inc.'),
    'AMZN':('0001018724','AMAZON COM INC'),
}
FORMS={'10-K','10-K/A','10-Q','10-Q/A','8-K','8-K/A','DEF 14A'}
BASE='https://data.sec.gov/submissions/CIK{cik}.json'
USER_AGENT=os.environ.get('SEC_USER_AGENT','EconomicsResearchDashboard/1.0 (+https://github.com/nora69boy/economics-dashboard-public)')
MAX_PER_COMPANY=8

def require(ok:bool,label:str)->None:
    if not ok:raise ValueError(label)

def filing_url(cik:str,accession:str)->str:
    compact=accession.replace('-','')
    return 'https://www.sec.gov/Archives/edgar/data/'+str(int(cik))+'/'+compact+'/'+accession+'-index.html'

def normalize(ticker:str,payload:dict)->dict:
    require(ticker in COMPANIES,'ticker')
    cik,name=COMPANIES[ticker]
    require(str(payload.get('cik')).zfill(10)==cik,'cik')
    recent=payload.get('filings',{}).get('recent',{})
    keys=('accessionNumber','filingDate','reportDate','form','primaryDocument')
    require(all(isinstance(recent.get(k),list) for k in keys),'recent arrays')
    n=len(recent['accessionNumber']);require(all(len(recent[k])==n for k in keys),'recent lengths')
    filings=[]
    for i in range(n):
        form=recent['form'][i]
        if form not in FORMS:continue
        accession=recent['accessionNumber'][i];filing_date=recent['filingDate'][i];report_date=recent['reportDate'][i];primary=recent['primaryDocument'][i]
        require(isinstance(accession,str) and len(accession)>=18,'accession')
        require(isinstance(filing_date,str) and len(filing_date)==10,'filing date')
        require(isinstance(report_date,str),'report date')
        require(isinstance(primary,str) and primary and '/' not in primary and '\\' not in primary,'primary document')
        filings.append({'form':form,'filing_date':filing_date,'report_date':report_date or None,'accession_number':accession,'primary_document':primary,'filing_url':filing_url(cik,accession)})
        if len(filings)>=MAX_PER_COMPANY:break
    require(filings,'relevant filings')
    return {'ticker':ticker,'name':name,'cik':cik,'source_url':BASE.format(cik=cik),'latest':filings}

def fetch_json(url:str,timeout:float=20.0)->dict:
    req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT,'Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        require(response.status==200,'http status')
        raw=response.read(5_000_001);require(len(raw)<=5_000_000,'response size')
    data=json.loads(raw.decode('utf-8'));require(isinstance(data,dict),'json object');return data

def probe(fetcher=fetch_json,sleep=time.sleep)->dict:
    companies=[];errors=[]
    for index,ticker in enumerate(COMPANIES):
        cik,_=COMPANIES[ticker]
        try:companies.append(normalize(ticker,fetcher(BASE.format(cik=cik))))
        except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,urllib.error.URLError) as exc:
            errors.append({'ticker':ticker,'error':type(exc).__name__})
        if index<len(COMPANIES)-1:sleep(0.25)
    return {'sec_probe_health':'fresh' if len(companies)==len(COMPANIES) else 'degraded','checked_at':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'),'publication':'disabled_pending_rights_approval','companies':companies,'errors':errors}

def emit(result:dict)->None:
    compact={'sec_probe_health':result['sec_probe_health'],'company_count':len(result['companies']),'error_count':len(result['errors']),'publication':result['publication']}
    print(json.dumps(compact,sort_keys=True,separators=(',',':')))
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f:f.write('sec_probe_health='+result['sec_probe_health']+'\n')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:
            f.write('## SEC filings probe\n\n')
            f.write('- Status: '+result['sec_probe_health']+'\n')
            f.write('- Publication: disabled pending explicit rights approval\n')
            f.write('- Source: SEC EDGAR submissions API\n')
            for company in result['companies']:
                latest=company['latest'][0]
                f.write('- '+company['ticker']+': '+latest['form']+' filed '+latest['filing_date']+'\n')
            for error in result['errors']:f.write('- '+error['ticker']+': probe failed ('+error['error']+')\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--probe',action='store_true');p.add_argument('--strict',action='store_true');args=p.parse_args()
    if not args.probe:raise SystemExit('Use --probe; this module does not publish SEC data.')
    result=probe();emit(result)
    if args.strict and result['sec_probe_health']!='fresh':raise SystemExit(2)
if __name__=='__main__':main()
