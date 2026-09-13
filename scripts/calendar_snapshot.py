"""Reviewed 2026 official calendar. The manual review date is never represented as live."""
from datetime import datetime
from zoneinfo import ZoneInfo
from macro_core import CAL_SOURCES,validate_calendar

def build():
 events=[]
 def add(family,day,period,tm='08:30'):
  d='2026-'+day;t=datetime.fromisoformat(d+'T'+(tm or '00:00')).replace(tzinfo=ZoneInfo('America/New_York'))
  events.append({'id':family+'-'+d,'family':family,'date':d,'period':period,'time_local':tm,'time_jst':t.astimezone(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M') if tm else None,'source':CAL_SOURCES[family],'status':'verified_schedule'})
 for family,days in [('cpi','01-13 02-13 03-11 04-10 05-12 06-10 07-14 08-12 09-11 10-14 11-10 12-10'),('jobs','01-09 02-11 03-06 04-03 05-08 06-05 07-02 08-07 09-04 10-02 11-06 12-04')]:
  for i,d in enumerate(days.split()):add(family,d,'2025-12' if i==0 else f'2026-{i:02}')
 for d in '01-28 03-18 04-29 06-17 07-29 09-16 10-28 12-09'.split():add('fomc',d,None,None)
 for day,period in [('08-26','07'),('09-30','08'),('10-29','09'),('11-25','10'),('12-23','11')]:add('pce',day,'2026-'+period)
 data={'schema':1,'checked_at':'2026-09-13','events':sorted(events,key=lambda e:(e['date'],e['id']))}
 # Validate the immutable reviewed baseline against its own review date, not wall-clock time.
 validate_calendar(data,today=datetime.fromisoformat(data['checked_at']).date())
 return data
