"""Probe official BLS, BEA and Federal Reserve release calendars without publishing them."""
from __future__ import annotations
import argparse,html,json,os,re,urllib.error,urllib.request
from datetime import datetime,timezone
from html.parser import HTMLParser
from zoneinfo import ZoneInfo
import calendar_snapshot

BLS_ICS='https://www.bls.gov/schedule/news_release/bls.ics'
BEA_SCHEDULE='https://www.bea.gov/news/schedule'
FED_FOMC='https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'
USER_AGENT=os.environ.get('CALENDAR_USER_AGENT','EconomicsResearchDashboard/1.0 (+https://github.com/nora69boy/economics-dashboard-public)')
SOURCES={'bls':BLS_ICS,'bea':BEA_SCHEDULE,'fed':FED_FOMC}
MONTHS={name:i for i,name in enumerate('January February March April May June July August September October November December'.split(),1)}

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

def unfold_ics(raw:bytes)->list[str]:
    text=raw.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n')
    lines=[]
    for line in text.split('\n'):
        if line.startswith((' ','\t')) and lines:lines[-1]+=line[1:]
        else:lines.append(line)
    return lines

def parse_ics_dt(value:str)->tuple[str,str]:
    value=value.strip()
    m=re.fullmatch(r'(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})?',value)
    require(m is not None,'ics datetime')
    return f'{m[1]}-{m[2]}-{m[3]}',f'{m[4]}:{m[5]}'

def period_from_summary(summary:str)->str|None:
    months='January|February|March|April|May|June|July|August|September|October|November|December'
    m=re.search(r'\b('+months+r')\s+(20\d{2})\b',summary,re.I)
    if not m:return None
    return f'{m[2]}-{MONTHS[m[1].title()]:02d}'

def parse_bls_ics(raw:bytes)->list[dict]:
    events=[];current=None
    for line in unfold_ics(raw):
        if line=='BEGIN:VEVENT':current={};continue
        if line=='END:VEVENT':
            if current:
                summary=html.unescape(current.get('SUMMARY',''))
                family=None
                if re.search(r'\bConsumer Price Index\b',summary,re.I):family='cpi'
                elif re.search(r'\bEmployment Situation\b',summary,re.I):family='jobs'
                if family and 'DTSTART' in current:
                    day,clock=parse_ics_dt(current['DTSTART'])
                    events.append({'family':family,'date':day,'period':period_from_summary(summary),'time_local':clock,'time_jst':eastern_to_jst(day,clock),'source':BLS_ICS})
            current=None;continue
        if current is not None and ':' in line:
            key,value=line.split(':',1);key=key.split(';',1)[0]
            if key in {'SUMMARY','DTSTART'}:current[key]=value
    require(any(e['family']=='cpi' for e in events),'BLS CPI absent')
    require(any(e['family']=='jobs' for e in events),'BLS jobs absent')
    return sorted(events,key=lambda e:(e['date'],e['family']))

def html_text(raw:bytes)->str:
    p=Text();p.feed(raw.decode('utf-8',errors='strict'));return ' '.join(p.parts)

def parse_bea(raw:bytes,year:int=2026)->list[dict]:
    text=html_text(raw)
    pattern=re.compile(r'('+ '|'.join(MONTHS) +r')\s+(\d{1,2})\s+(\d{1,2}:\d{2})\s*(AM|PM).*?Personal Income and Outlays,\s*('+ '|'.join(MONTHS) +r')\s+(20\d{2})',re.I)
    out=[]
    for m in pattern.finditer(text):
        release_month=MONTHS[m[1].title()];day=f'{year}-{release_month:02d}-{int(m[2]):02d}'
        clock=datetime.strptime(m[3]+' '+m[4].upper(),'%I:%M %p').strftime('%H:%M')
        period=f'{m[6]}-{MONTHS[m[5].title()]:02d}'
        out.append({'family':'pce','date':day,'period':period,'time_local':clock,'time_jst':eastern_to_jst(day,clock),'source':BEA_SCHEDULE})
    require(len(out)>=4,'BEA PCE schedule absent')
    return sorted({(e['date'],e['period']):e for e in out}.values(),key=lambda e:e['date'])

def parse_fed(raw:bytes,year:int=2026)->list[dict]:
    text=html_text(raw)
    marker=f'{year} FOMC Meetings';start=text.find(marker);require(start>=0,'FOMC year absent')
    tail=text[start+len(marker):]
    stops=[p for p in (tail.find(f'{year-1} FOMC Meetings'),tail.find(f'{year+1} FOMC Meetings')) if p>=0]
    if stops:tail=tail[:min(stops)]
    positions=[]
    for name in MONTHS:
        for m in re.finditer(r'\b'+name+r'\b',tail):positions.append((m.start(),name))
    positions.sort();out=[]
    for i,(pos,name) in enumerate(positions):
        end=positions[i+1][0] if i+1<len(positions) else len(tail);chunk=tail[pos+len(name):end]
        m=re.search(r'\b(\d{1,2})\s*[-–]\s*(\d{1,2})\b',chunk)
        if not m:continue
        decision_day=int(m[2]);date=f'{year}-{MONTHS[name]:02d}-{decision_day:02d}'
        out.append({'family':'fomc','date':date,'period':None,'time_local':None,'time_jst':None,'source':FED_FOMC})
    require(len(out)>=8,'FOMC schedule incomplete')
    return sorted({e['date']:e for e in out}.values(),key=lambda e:e['date'])

def fetch(url:str,timeout:float=25.0)->bytes:
    req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT,'Accept':'text/html,text/calendar;q=0.9,*/*;q=0.1'})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        require(response.status==200,'http status');raw=response.read(3_000_001);require(len(raw)<=3_000_000,'response size');return raw

def compare(candidate:list[dict])->list[dict]:
    current=calendar_snapshot.build()['events']
    def key(e):return (e['family'],e['date'])
    old={key(e):e for e in current};new={key(e):e for e in candidate};changes=[]
    for k in sorted(set(old)|set(new)):
        if k not in old:changes.append({'kind':'added','family':k[0],'date':k[1]})
        elif k not in new:changes.append({'kind':'removed','family':k[0],'date':k[1]})
        else:
            a,b=old[k],new[k]
            if (a.get('period'),a.get('time_local'))!=(b.get('period'),b.get('time_local')):changes.append({'kind':'changed','family':k[0],'date':k[1]})
    return changes

def probe(fetcher=fetch)->dict:
    parsers={'bls':parse_bls_ics,'bea':parse_bea,'fed':parse_fed};candidate=[];errors=[]
    for name,url in SOURCES.items():
        try:candidate.extend(parsers[name](fetcher(url)))
        except urllib.error.HTTPError as exc:errors.append({'source':name,'error':'HTTPError','code':exc.code})
        except (OSError,UnicodeError,ValueError,TypeError) as exc:errors.append({'source':name,'error':type(exc).__name__,'code':None})
    candidate=sorted(candidate,key=lambda e:(e['date'],e['family']))
    blocked=bool(errors) and len(errors)==len(SOURCES) and all(e['code'] in {403,429} for e in errors)
    health='source_access_blocked' if blocked else ('fresh' if not errors else 'degraded')
    changes=compare(candidate) if candidate else []
    return {'calendar_probe_health':health,'checked_at':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'),'publication':'disabled_pending_rights_approval','candidate_events':candidate,'changes':changes,'errors':errors}

def emit(result:dict)->None:
    print(json.dumps({'calendar_probe_health':result['calendar_probe_health'],'candidate_count':len(result['candidate_events']),'change_count':len(result['changes']),'error_count':len(result['errors']),'publication':result['publication']},sort_keys=True,separators=(',',':')))
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f:f.write('calendar_probe_health='+result['calendar_probe_health']+'\n')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:
            f.write('## Official economic calendar probe\n\n')
            f.write('- Status: '+result['calendar_probe_health']+'\n')
            f.write('- Candidate events: '+str(len(result['candidate_events']))+'\n')
            f.write('- Differences vs reviewed snapshot: '+str(len(result['changes']))+'\n')
            f.write('- Publication: disabled pending explicit rights approval\n')
            for e in result['errors']:f.write('- '+e['source']+': '+e['error']+((' '+str(e['code'])) if e['code'] else '')+'\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--probe',action='store_true');p.add_argument('--strict',action='store_true');args=p.parse_args()
    if not args.probe:raise SystemExit('Use --probe; this module does not publish calendar data.')
    result=probe();emit(result)
    if args.strict and result['calendar_probe_health']!='fresh':raise SystemExit(2)
if __name__=='__main__':main()
