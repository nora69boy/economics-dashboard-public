"""Probe official BLS, BEA and Federal Reserve release calendars and stage safe candidates."""
from __future__ import annotations
import argparse,html,json,os,re,urllib.error,urllib.request
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo
import calendar_snapshot

ROOT=Path(__file__).resolve().parents[1]
STATE_PATH=ROOT/'.calendar-probe.json'
BLS_ICS='https://www.bls.gov/schedule/news_release/bls.ics'
BLS_CPI='https://www.bls.gov/schedule/news_release/cpi.htm'
BLS_JOBS='https://www.bls.gov/schedule/news_release/empsit.htm'
BEA_SCHEDULE='https://www.bea.gov/news/schedule'
BEA_NEXT_YEAR='https://www.bea.gov/news/schedule/next-year/next-year'
FED_FOMC='https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'
USER_AGENT=os.environ.get('CALENDAR_USER_AGENT','EconomicsResearchDashboard/1.0 (+https://github.com/nora69boy/economics-dashboard-public)')
SOURCES={'bea':BEA_SCHEDULE,'bea-next-year':BEA_NEXT_YEAR,'fed':FED_FOMC}
BLS_HTML={'cpi':BLS_CPI,'jobs':BLS_JOBS}
MONTHS={name:i for i,name in enumerate('January February March April May June July August September October November December'.split(),1)}
ABBR={'Jan.':1,'Feb.':2,'Mar.':3,'Apr.':4,'May':5,'Jun.':6,'Jul.':7,'Aug.':8,'Sep.':9,'Oct.':10,'Nov.':11,'Dec.':12}

class Text(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.parts=[]
    def handle_data(self,data):
        value=' '.join(data.split())
        if value:self.parts.append(value)

def require(ok:bool,label:str)->None:
    if not ok:raise ValueError(label)

def eastern_to_jst(day:str,clock:str)->str:
    dt=datetime.fromisoformat(day+'T'+clock).replace(tzinfo=ZoneInfo('America/New_York'))
    return dt.astimezone(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M')

def local_year(now:datetime|None=None)->int:
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:now=now.replace(tzinfo=timezone.utc)
    return now.astimezone(ZoneInfo('Asia/Tokyo')).year

def unfold_ics(raw:bytes)->list[str]:
    text=raw.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n');lines=[]
    for line in text.split('\n'):
        if line.startswith((' ','\t')) and lines:lines[-1]+=line[1:]
        else:lines.append(line)
    return lines

def parse_ics_dt(value:str)->tuple[str,str]:
    value=value.strip();m=re.fullmatch(r'(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})?',value);require(m is not None,'ics datetime')
    return f'{m[1]}-{m[2]}-{m[3]}',f'{m[4]}:{m[5]}'

def period_from_summary(summary:str)->str|None:
    months='January|February|March|April|May|June|July|August|September|October|November|December';m=re.search(r'\b('+months+r')\s+(20\d{2})\b',summary,re.I)
    return None if not m else f'{m[2]}-{MONTHS[m[1].title()]:02d}'

def parse_bls_ics(raw:bytes)->list[dict]:
    events=[];current=None
    for line in unfold_ics(raw):
        if line=='BEGIN:VEVENT':current={};continue
        if line=='END:VEVENT':
            if current:
                summary=html.unescape(current.get('SUMMARY',''));family=None
                if re.search(r'\bConsumer Price Index\b',summary,re.I):family='cpi'
                elif re.search(r'\bEmployment Situation\b',summary,re.I):family='jobs'
                if family and 'DTSTART' in current:
                    day,clock=parse_ics_dt(current['DTSTART']);events.append({'family':family,'date':day,'period':period_from_summary(summary),'time_local':clock,'time_jst':eastern_to_jst(day,clock),'source':BLS_ICS})
            current=None;continue
        if current is not None and ':' in line:
            key,value=line.split(':',1);key=key.split(';',1)[0]
            if key in {'SUMMARY','DTSTART'}:current[key]=value
    require(any(e['family']=='cpi' for e in events),'BLS CPI absent');require(any(e['family']=='jobs' for e in events),'BLS jobs absent')
    return sorted(events,key=lambda e:(e['date'],e['family']))

def html_text(raw:bytes)->str:
    p=Text();p.feed(raw.decode('utf-8',errors='strict'));return ' '.join(p.parts)

def parse_bls_release_html(raw:bytes,family:str,source:str,year:int|None=2026)->list[dict]:
    require(family in BLS_HTML,'BLS family');text=html_text(raw);title='Consumer Price Index' if family=='cpi' else 'Employment Situation';require('Schedule of Releases for the '+title in text,'BLS schedule title')
    full='|'.join(MONTHS);abbr='|'.join(re.escape(k) for k in ABBR);pattern=re.compile(r'\b('+full+r')\s+(20\d{2})\s+('+abbr+r')\s+(\d{1,2}),\s+(20\d{2})\s+(\d{1,2}:\d{2})\s*(AM|PM)\b',re.I);out=[]
    for m in pattern.finditer(text):
        release_year=int(m[5])
        if year is not None and release_year!=year:continue
        ref_name=m[1].title();ref_year=int(m[2]);release_token=m[3].title();token=next((k for k in ABBR if k.lower()==release_token.lower()),None);require(token is not None,'BLS release month')
        day=f'{release_year}-{ABBR[token]:02d}-{int(m[4]):02d}';clock=datetime.strptime(m[6]+' '+m[7].upper(),'%I:%M %p').strftime('%H:%M');out.append({'family':family,'date':day,'period':f'{ref_year}-{MONTHS[ref_name]:02d}','time_local':clock,'time_jst':eastern_to_jst(day,clock),'source':source})
    out=sorted({(e['date'],e['period']):e for e in out}.values(),key=lambda e:e['date']);require(bool(out),'BLS '+family+' schedule absent')
    if year is not None:require(len(out)==12,'BLS '+family+' annual schedule incomplete')
    return out

def parse_bea(raw:bytes,year:int=2026,source:str=BEA_SCHEDULE,minimum:int=1)->list[dict]:
    text=html_text(raw);pattern=re.compile(r'('+ '|'.join(MONTHS) +r')\s+(\d{1,2})\s+(\d{1,2}:\d{2})\s*(AM|PM).*?Personal Income and Outlays,\s*('+ '|'.join(MONTHS) +r')\s+(20\d{2})',re.I);out=[]
    for m in pattern.finditer(text):
        release_month=MONTHS[m[1].title()];day=f'{year}-{release_month:02d}-{int(m[2]):02d}';clock=datetime.strptime(m[3]+' '+m[4].upper(),'%I:%M %p').strftime('%H:%M');period=f'{m[6]}-{MONTHS[m[5].title()]:02d}';out.append({'family':'pce','date':day,'period':period,'time_local':clock,'time_jst':eastern_to_jst(day,clock),'source':source})
    out=sorted({(e['date'],e['period']):e for e in out}.values(),key=lambda e:e['date']);require(len(out)>=minimum,'BEA PCE schedule absent');return out

def complete_monthly_year(events:list[dict],release_year:int)->bool:
    rows=[e for e in events if e['date'].startswith(str(release_year)+'-')]
    return len(rows)==12 and len({e['date'] for e in rows})==12 and len({e['period'] for e in rows})==12

def parse_fed(raw:bytes,year:int=2026)->list[dict]:
    text=html_text(raw);marker=f'{year} FOMC Meetings';start=text.find(marker);require(start>=0,'FOMC year absent');tail=text[start+len(marker):];stops=[p for p in (tail.find(f'{year-1} FOMC Meetings'),tail.find(f'{year+1} FOMC Meetings'),tail.find('Note:')) if p>=0]
    if stops:tail=tail[:min(stops)]
    positions=[]
    for name in MONTHS:
        for m in re.finditer(r'\b'+name+r'\b',tail):positions.append((m.start(),name))
    positions.sort();out=[]
    for i,(pos,name) in enumerate(positions):
        end=positions[i+1][0] if i+1<len(positions) else len(tail);chunk=tail[pos+len(name):end];m=re.search(r'\b(\d{1,2})\s*[-–]\s*(\d{1,2})\b',chunk)
        if m:out.append({'family':'fomc','date':f'{year}-{MONTHS[name]:02d}-{int(m[2]):02d}','period':None,'time_local':None,'time_jst':None,'source':FED_FOMC})
    require(len(out)>=8,'FOMC schedule incomplete');return sorted({e['date']:e for e in out}.values(),key=lambda e:e['date'])

def fetch(url:str,timeout:float=25.0)->bytes:
    req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT,'Accept':'text/html,text/calendar;q=0.9,*/*;q=0.1'})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        require(response.status==200,'http status');raw=response.read(3_000_001);require(len(raw)<=3_000_000,'response size');return raw

def compare(candidate:list[dict])->list[dict]:
    current=calendar_snapshot.build()['events'];key=lambda e:(e['family'],e['date']);old={key(e):e for e in current};new={key(e):e for e in candidate};changes=[]
    for k in sorted(set(old)|set(new)):
        if k not in old:changes.append({'kind':'added','family':k[0],'date':k[1]})
        elif k not in new:changes.append({'kind':'removed','family':k[0],'date':k[1]})
        elif (old[k].get('period'),old[k].get('time_local'))!=(new[k].get('period'),new[k].get('time_local')):changes.append({'kind':'changed','family':k[0],'date':k[1]})
    return changes

def probe_bls(fetcher,year:int=2026):
    advisories=[];errors=[]
    try:
        events=parse_bls_ics(fetcher(BLS_ICS));events=[e for e in events if int(e['date'][:4]) in {year,year+1}]
        mode='ics_current_plus_next_year' if any(e['date'].startswith(str(year+1)+'-') for e in events) else 'ics'
        return events,errors,advisories,mode
    except urllib.error.HTTPError as exc:
        if exc.code not in {403,429}:return [],[{'source':'bls-ics','error':'HTTPError','code':exc.code}],advisories,'failed'
        advisories.append({'source':'bls-ics','error':'HTTPError','code':exc.code})
    except (OSError,UnicodeError,ValueError,TypeError) as exc:return [],[{'source':'bls-ics','error':type(exc).__name__,'code':None}],advisories,'failed'
    events=[]
    for family,url in BLS_HTML.items():
        try:
            parsed=parse_bls_release_html(fetcher(url),family,url,None)
            events.extend(e for e in parsed if int(e['date'][:4]) in {year,year+1})
        except urllib.error.HTTPError as exc:errors.append({'source':'bls-'+family+'-html','error':'HTTPError','code':exc.code})
        except (OSError,UnicodeError,ValueError,TypeError) as exc:errors.append({'source':'bls-'+family+'-html','error':type(exc).__name__,'code':None})
    next_year=any(e['date'].startswith(str(year+1)+'-') for e in events)
    mode=('html_fallback_current_plus_next_year' if next_year and not errors else ('html_fallback' if not errors else 'partial_html_fallback'))
    return sorted(events,key=lambda e:(e['date'],e['family'])),errors,advisories,mode

def probe_bea(fetcher,year:int=2026):
    errors=[];advisories=[];events=[];mode='primary'
    try:events.extend(parse_bea(fetcher(BEA_SCHEDULE),year,BEA_SCHEDULE,1))
    except urllib.error.HTTPError as exc:return [],[{'source':'bea','error':'HTTPError','code':exc.code}],advisories,'failed'
    except (OSError,UnicodeError,ValueError,TypeError) as exc:return [],[{'source':'bea','error':type(exc).__name__,'code':None}],advisories,'failed'
    try:
        raw=fetcher(BEA_NEXT_YEAR);text=html_text(raw)
        if f'Year {year+1}' in text:
            try:future=parse_bea(raw,year+1,BEA_NEXT_YEAR,1)
            except ValueError:future=[]
            if complete_monthly_year(future,year+1):
                events.extend(future);mode='primary_current_plus_next_year'
            else:
                advisories.append({'source':'bea-next-year','error':'ScheduleIncomplete','code':None});mode='primary_next_year_incomplete'
    except urllib.error.HTTPError as exc:
        if exc.code not in {404}:advisories.append({'source':'bea-next-year','error':'HTTPError','code':exc.code})
    except (OSError,UnicodeError,ValueError,TypeError) as exc:advisories.append({'source':'bea-next-year','error':type(exc).__name__,'code':None})
    return sorted(events,key=lambda e:e['date']),errors,advisories,mode

def probe(fetcher=fetch,now:datetime|None=None)->dict:
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:now=now.replace(tzinfo=timezone.utc)
    year=local_year(now);candidate=[];errors=[];advisories=[];source_modes={}
    bls_events,bls_errors,bls_advisories,bls_mode=probe_bls(fetcher,year);candidate.extend(bls_events);errors.extend(bls_errors);advisories.extend(bls_advisories);source_modes['bls']=bls_mode
    bea_events,bea_errors,bea_advisories,bea_mode=probe_bea(fetcher,year);candidate.extend(bea_events);errors.extend(bea_errors);advisories.extend(bea_advisories);source_modes['bea']=bea_mode
    try:
        fed_raw=fetcher(FED_FOMC);candidate.extend(parse_fed(fed_raw,year));fed_text=html_text(fed_raw);source_modes['fed']='primary'
        if f'{year+1} FOMC Meetings' in fed_text:
            candidate.extend(parse_fed(fed_raw,year+1));source_modes['fed']='primary_current_plus_next_year'
    except urllib.error.HTTPError as exc:errors.append({'source':'fed','error':'HTTPError','code':exc.code});source_modes['fed']='failed'
    except (OSError,UnicodeError,ValueError,TypeError) as exc:errors.append({'source':'fed','error':type(exc).__name__,'code':None});source_modes['fed']='failed'
    candidate=sorted({(e['family'],e['date']):e for e in candidate}.values(),key=lambda e:(e['date'],e['family']));access_errors=[e for e in errors if e['code'] in {403,429}]
    health='fresh' if not errors else ('source_access_blocked' if len(access_errors)==len(errors) and not candidate else ('partial_access_blocked' if len(access_errors)==len(errors) and candidate else 'degraded'))
    changes=compare(candidate) if candidate else []
    return {'calendar_probe_health':health,'checked_at':now.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'),'publication':'staged_for_completeness_gate','candidate_events':candidate,'changes':changes,'errors':errors,'advisories':advisories,'source_modes':source_modes}

def save_state(result:dict,path:Path=STATE_PATH)->None:
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8');tmp.replace(path)

def emit(result:dict)->None:
    compact={'calendar_probe_health':result['calendar_probe_health'],'candidate_count':len(result['candidate_events']),'change_count':len(result['changes']),'error_count':len(result['errors']),'errors':result['errors'],'advisories':result['advisories'],'source_modes':result['source_modes'],'publication':result['publication']};print(json.dumps(compact,sort_keys=True,separators=(',',':')))
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f:f.write('calendar_probe_health='+result['calendar_probe_health']+'\n')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:
            f.write('## Official economic calendar probe\n\n- Status: '+result['calendar_probe_health']+'\n- Candidate events: '+str(len(result['candidate_events']))+'\n- Differences vs reviewed snapshot: '+str(len(result['changes']))+'\n- BLS mode: '+result['source_modes'].get('bls','unknown')+'\n- BEA mode: '+result['source_modes'].get('bea','unknown')+'\n- Federal Reserve mode: '+result['source_modes'].get('fed','unknown')+'\n- Publication: staged for family completeness gate\n')
            for e in result['advisories']:f.write('- Advisory '+e['source']+': '+e['error']+((' '+str(e['code'])) if e['code'] else '')+'\n')
            for e in result['errors']:f.write('- Error '+e['source']+': '+e['error']+((' '+str(e['code'])) if e['code'] else '')+'\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--probe',action='store_true');p.add_argument('--strict',action='store_true');args=p.parse_args()
    if not args.probe:raise SystemExit('Use --probe; this module only stages candidates for the completeness gate.')
    result=probe();save_state(result);emit(result)
    if args.strict and result['calendar_probe_health']!='fresh':raise SystemExit(2)
if __name__=='__main__':main()
