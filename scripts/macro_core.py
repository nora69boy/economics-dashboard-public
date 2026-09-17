"""Typed public-statistics boundary: fixed identities, bounded numeric data, no personal input."""
from __future__ import annotations
import csv, io, json, math, re
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from zoneinfo import ZoneInfo
START = '2015-01-01'
CALENDAR_HISTORY_START_YEAR = 2026
CALENDAR_MAX_EVENTS = 140
TREASURY = 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/'
BLS = 'https://api.bls.gov/publicAPI/v1/timeseries/data/'
BEA = 'https://apps.bea.gov/national/Release/TXT/NipaDataM.txt'
FX = 'https://www.federalreserve.gov/releases/h10/hist/dat00_ja.htm'
WTI = 'https://www.eia.gov/dnav/pet/hist/RWTCD.htm'
WTI_RECENT = 'https://www.eia.gov/dnav/pet/PET_PRI_SPT_S1_D.htm'
VIX = 'https://www.cboe.com/tradable-products/vix/vix-historical-data/'
CAL_SOURCES = {'cpi':'https://www.bls.gov/schedule/news_release/cpi.htm','jobs':'https://www.bls.gov/schedule/news_release/empsit.htm','pce':'https://www.bea.gov/news/schedule','fomc':'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'}
META = {'ust10':('daily','percent',TREASURY+'TextView',-5,30),'cpi':('monthly','index_1982_84_100','https://data.bls.gov/timeseries/CUUR0000SA0',1,10000),'pce':('monthly','index_2017_100','https://www.bea.gov/data/personal-consumption-expenditures-price-index',1,10000),'unemployment':('monthly','percent','https://data.bls.gov/timeseries/LNS14000000',0,40),'vix':('daily','points',VIX,0,500),'usdjpy':('daily','JPY_per_USD',FX,1,1000),'wti':('daily','USD_per_barrel',WTI,-100,1000)}
AUX = {'ust10':{'ust2':(-5,30)},'cpi':{'core':(1,10000),'headline_sa':(1,10000),'core_sa':(1,10000)},'pce':{'core':(1,10000)},'unemployment':{'payrolls_thousands':(1,1000000)},'vix':{},'usdjpy':{},'wti':{}}
BLS_IDS = {'CUUR0000SA0':('cpi',None),'CUSR0000SA0':('cpi','headline_sa'),'CUUR0000SA0L1E':('cpi','core'),'CUSR0000SA0L1E':('cpi','core_sa'),'LNS14000000':('unemployment',None),'CES0000000001':('unemployment','payrolls_thousands')}
URLS = {x[2] for x in META.values()} | set(CAL_SOURCES.values()) | {WTI_RECENT,'https://www.cboe.com/terms'}
def require(ok: bool, reason: str) -> None:
 if not ok:raise ValueError(reason)
def keys(obj: dict, expected: str) -> None:require(isinstance(obj,dict) and set(obj)==set(expected.split()),'Unexpected fields')
def iso(s: str) -> date:
 require(isinstance(s,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',s) is not None,'Date format');return date.fromisoformat(s)
def timestamp(s: str) -> datetime:
 require(isinstance(s,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',s) is not None,'Timestamp format');return datetime.fromisoformat(s.replace('Z','+00:00'))
def points(rows: list, low: float, high: float, today: date) -> None:
 require(isinstance(rows,list) and len(rows)<=5000,'Series size');previous=''
 for r in rows:
  require(isinstance(r,list) and len(r)==2,'Observation shape');d,v=r
  require(START<=d and previous<d and iso(d)<=today,'Observation date/order');require(type(v) in (int,float) and math.isfinite(v) and low<=v<=high,'Observation value');previous=d
def validate(data: dict, today: date|None=None) -> None:
 today=today or date.today();keys(data,'schema classification attempted_at series revisions')
 require(data['schema']==1 and data['classification']=='public-official-macro','Classification');require(timestamp(data['attempted_at']).date()<=today,'Future retrieval')
 require(isinstance(data['series'],list) and [s.get('id') for s in data['series']]==list(META),'Fixed seven-series set')
 for s in data['series']:
  keys(s,'id status fetched_at source_sha256 observations auxiliary');ident=s['id'];freq,unit,url,lo,hi=META[ident]
  require(s['status'] in {'available','retained','unavailable','rights_pending'},'Status')
  if ident=='vix':
   require(s['status']=='rights_pending' and s['observations']==[] and s['auxiliary']=={} and s['fetched_at'] is None and s['source_sha256'] is None,'VIX rights boundary');continue
  if s['status']=='unavailable':
   require(s['observations']==[] and s['auxiliary']=={} and s['fetched_at'] is None and s['source_sha256'] is None,'Unavailable values');continue
  require(timestamp(s['fetched_at']).date()<=today and s['fetched_at']<=data['attempted_at'],'Retrieval date');require(isinstance(s['source_sha256'],str) and re.fullmatch('[0-9a-f]{64}',s['source_sha256']) is not None,'Provenance digest')
  points(s['observations'],lo,hi,today);require(len(s['observations'])>=(100 if freq=='monthly' else 1500),'Long history absent');require(isinstance(s['auxiliary'],dict) and set(s['auxiliary'])<=set(AUX[ident]),'Auxiliary identities')
  for aid,rows in s['auxiliary'].items():points(rows,*AUX[ident][aid],today)
  if freq=='monthly':require(all(d.endswith('-01') for d,_ in s['observations']),'Reference-month dates')
 require(isinstance(data['revisions'],list) and len(data['revisions'])<=50,'Revision bound')
 for r in data['revisions']:
  keys(r,'series date old new detected_at');require(r['series'] in META and r['series']!='vix','Revision identity');iso(r['date']);timestamp(r['detected_at']);require(all(type(r[k]) in (int,float) and math.isfinite(r[k]) and META[r['series']][3]<=r[k]<=META[r['series']][4] for k in ['old','new']),'Revision values')
def validate_calendar(data: dict, today: date|None=None) -> None:
 today=today or datetime.now(ZoneInfo('Asia/Tokyo')).date();keys(data,'schema checked_at events');require(data['schema']==1 and iso(data['checked_at'])<=today,'Calendar version/date');require(isinstance(data['events'],list) and 1<=len(data['events'])<=CALENDAR_MAX_EVENTS,'Calendar size');ids=set()
 for e in data['events']:
  keys(e,'id family date period time_local time_jst source status');require(e['family'] in CAL_SOURCES and e['source']==CAL_SOURCES[e['family']],'Event source');require(re.fullmatch(r'[a-z]+-\d{4}-\d{2}-\d{2}',e['id']) is not None and e['id'] not in ids,'Event ID');ids.add(e['id'])
  day=iso(e['date']);require(CALENDAR_HISTORY_START_YEAR<=day.year<=today.year+1,'Event range');require(e['status']=='verified_schedule','Schedule is not an actual result');require(e['period'] is None or re.fullmatch(r'\d{4}-\d{2}',e['period']) is not None,'Reference period')
  if e['time_local'] is None:require(e['time_jst'] is None,'Unknown time')
  else:
   require(re.fullmatch(r'\d{2}:\d{2}',e['time_local']) is not None,'Event time');dt=datetime.fromisoformat(e['date']+'T'+e['time_local']).replace(tzinfo=ZoneInfo('America/New_York'));require(e['time_jst']==dt.astimezone(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M'),'DST conversion')
def clean(mapping: dict, today: date|None=None) -> list:
 end=(today or date.today()).isoformat();return [[k,float(v)] for k,v in sorted(mapping.items()) if START<=k<=end]
def parse_bls(raw: bytes) -> dict:
 d=json.loads(raw);require(d.get('status')=='REQUEST_SUCCEEDED','BLS request failed');out={}
 for s in d['Results']['series']:
  ident=s['seriesID'];require(ident in BLS_IDS,'Unknown BLS series');rows={}
  for r in s['data']:
   if re.fullmatch('M(0[1-9]|1[0-2])',r['period']) and re.fullmatch(r'-?\d+(?:\.\d+)?',r['value']):rows[r['year']+'-'+r['period'][1:]+'-01']=float(r['value'])
  out[ident]=rows
 return out
def parse_treasury(raw: bytes) -> tuple[dict,dict]:
 ten={};two={};reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
 if reader.fieldnames:reader.fieldnames=[x.strip().title() for x in reader.fieldnames]
 require(reader.fieldnames is not None and {'Date','2 Yr','10 Yr'}<=set(reader.fieldnames),'Treasury header')
 for r in reader:
  try:d=datetime.strptime(r['Date'],'%m/%d/%Y').date()
  except ValueError:d=datetime.strptime(r['Date'],'%m/%d/%y').date()
  for label,out in [('10 Yr',ten),('2 Yr',two)]:
   if r[label] not in {'','N/A','NA'}:out[d.isoformat()]=float(r[label])
 return ten,two
class Rows(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.rows=[];self.row=None;self.cell=None
 def handle_starttag(self,tag,attrs):
  if tag=='tr':self.row=[]
  if tag in {'td','th'} and self.row is not None:self.cell=[]
 def handle_data(self,s):
  if self.cell is not None:self.cell.append(s)
 def handle_endtag(self,tag):
  if tag in {'td','th'} and self.cell is not None:
   if self.row is not None:self.row.append(' '.join(''.join(self.cell).split()))
   self.cell=None
  if tag=='tr' and self.row is not None:self.rows.append(self.row);self.row=None
def parse_fx(raw: bytes) -> dict:
 p=Rows();p.feed(raw.decode('utf-8'));out={}
 for r in p.rows:
  if len(r)==2 and re.fullmatch(r'\d{1,2}-[A-Z]{3}-\d{2}',r[0]):
   if re.fullmatch(r'\d+\.\d+',r[1]):out[datetime.strptime(r[0],'%d-%b-%y').date().isoformat()]=float(r[1])
 require(len(out)>1500,'FX parser empty');return out
def parse_wti(raw: bytes) -> dict:
 p=Rows();p.feed(raw.decode('utf-8'));out={}
 for r in p.rows:
  if len(r)!=6:continue
  m=re.match(r'(\d{4})\s+([A-Za-z]{3})-\s*(\d{1,2})\s+to',r[0])
  if not m:continue
  d=datetime.strptime(' '.join(m.groups()),'%Y %b %d').date();require(d.weekday()==0,'EIA week alignment')
  for i,v in enumerate(r[1:]):
   if re.fullmatch(r'-?\d+(?:\.\d+)?',v):out[(d+timedelta(days=i)).isoformat()]=float(v)
 require(len(out)>1500,'EIA parser empty');return out
def parse_wti_recent(raw: bytes) -> dict:
 p=Rows();p.feed(raw.decode('utf-8'));dates=[]
 for r in p.rows:
  candidate=[]
  for cell in r:
   if re.fullmatch(r'\d{2}/\d{2}/\d{2}',cell):candidate.append(datetime.strptime(cell,'%m/%d/%y').date())
  if len(candidate)>=2:dates=candidate;break
 require(len(dates)>=2,'EIA recent date header')
 for r in p.rows:
  if not r or not r[0].startswith('WTI - Cushing'):continue
  values=[float(cell) for cell in r[1:] if re.fullmatch(r'-?\d+(?:\.\d+)?',cell)]
  require(len(values)==len(dates),'EIA recent WTI alignment')
  return {d.isoformat():v for d,v in zip(dates,values)}
 raise ValueError('EIA recent WTI row absent')
def parse_bea(lines) -> tuple[dict,dict]:
 out={'DPCERG':{},'DPCCRG':{}}
 for r in csv.reader(lines):
  if len(r)!=3 or r[0] not in out:continue
  m=re.fullmatch(r'(\d{4})M(0[1-9]|1[0-2])',r[1])
  if m:out[r[0]][m[1]+'-'+m[2]+'-01']=float(r[2].replace(',',''))
 require(len(out['DPCERG'])>100,'BEA parser empty');return out['DPCERG'],out['DPCCRG']
def yoy(rows: list) -> list:
 m=dict(rows);out=[]
 for d,v in rows:
  prev=str(int(d[:4])-1)+d[4:]
  if prev in m and m[prev]!=0:out.append([d,(v/m[prev]-1)*100])
 return out
