"""Completeness, extension and year-rollover tests for official calendar publication."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import calendar_probe as probe
import calendar_publish as publish
import calendar_snapshot

NOW=datetime(2026,9,13,18,0,tzinfo=timezone.utc)
NOW_2027=datetime(2026,12,31,15,20,tzinfo=timezone.utc)


def candidate_from_reviewed(event):
    raw_source={
        'cpi':probe.BLS_CPI,
        'jobs':probe.BLS_JOBS,
        'pce':probe.BEA_SCHEDULE,
        'fomc':probe.FED_FOMC,
    }[event['family']]
    return {k:event[k] for k in ['family','date','period','time_local','time_jst']} | {'source':raw_source}


def fomc(year, dates):
    return [{'family':'fomc','date':f'{year}-{day}','period':None,'time_local':None,'time_jst':None,'source':probe.FED_FOMC} for day in dates]


def monthly_family(family,release_year,source):
    periods=[f'{release_year-1}-12']+[f'{release_year}-{m:02d}' for m in range(1,12)]
    return [{'family':family,'date':f'{release_year}-{m:02d}-15','period':period,'time_local':'08:30','time_jst':f'{release_year}-{m:02d}-15 '+('21:30' if 3<=m<=10 else '22:30'),'source':source} for m,period in enumerate(periods,1)]


def state(candidates,checked_at='2026-09-13T17:50:00Z'):
    return {
        'calendar_probe_health':'partial_access_blocked',
        'checked_at':checked_at,
        'publication':'staged_for_completeness_gate',
        'candidate_events':candidates,
        'changes':[],
        'errors':[{'source':'bls-cpi-html','error':'HTTPError','code':403}],
        'advisories':[{'source':'bls-ics','error':'HTTPError','code':403}],
        'source_modes':{'bls':'partial_html_fallback','bea':'primary','fed':'primary_current_plus_next_year'},
    }


class CalendarPublishTests(unittest.TestCase):
    def write_state(self,data,tmp):
        path=Path(tmp)/'state.json';path.write_text(json.dumps(data),encoding='utf-8');return path

    def reviewed_future(self,family):
        return [e for e in calendar_snapshot.build()['events'] if e['family']==family and e['date']>='2026-09-14']

    def current_live_candidates(self):
        return [candidate_from_reviewed(e) for family in ('pce','fomc') for e in self.reviewed_future(family)]

    def test_bea_and_fed_live_bls_retained(self):
        candidates=self.current_live_candidates()
        pce=next(e for e in candidates if e['family']=='pce' and e['period']=='2026-08');pce['date']='2026-10-01';pce['time_jst']='2026-10-01 21:30'
        with tempfile.TemporaryDirectory() as tmp:
            data,report=publish.build(self.write_state(state(candidates),tmp),NOW)
        self.assertEqual(report['live_families'],['pce','fomc'])
        self.assertEqual(report['retained_families'],['cpi','jobs'])
        self.assertEqual(report['extended_years'],{})
        self.assertIn('2026-10-01',{e['date'] for e in data['events'] if e['family']=='pce'})
        self.assertEqual([e for e in data['events'] if e['family']=='cpi'],[e for e in calendar_snapshot.build()['events'] if e['family']=='cpi'])

    def test_complete_next_year_fomc_is_extended(self):
        candidates=self.current_live_candidates()+fomc(2027,['01-27','03-17','04-28','06-09','07-28','09-15','10-27','12-08'])
        with tempfile.TemporaryDirectory() as tmp:
            data,report=publish.build(self.write_state(state(candidates),tmp),NOW)
        self.assertEqual(report['extended_years'],{'fomc':[2027]})
        future=[e for e in data['events'] if e['family']=='fomc' and e['date'].startswith('2027-')]
        self.assertEqual(len(future),8)
        self.assertEqual(future[0]['date'],'2027-01-27')

    def test_complete_next_year_pce_from_bea_next_year_source_is_extended(self):
        candidates=self.current_live_candidates()+monthly_family('pce',2027,probe.BEA_NEXT_YEAR)
        with tempfile.TemporaryDirectory() as tmp:
            data,report=publish.build(self.write_state(state(candidates),tmp),NOW)
        self.assertEqual(report['extended_years'],{'pce':[2027]})
        future=[e for e in data['events'] if e['family']=='pce' and e['date'].startswith('2027-')]
        self.assertEqual(len(future),12)
        self.assertTrue(all(e['source']==publish.CAL_SOURCES['pce'] for e in future))

    def test_partial_next_year_fomc_is_not_published(self):
        candidates=self.current_live_candidates()+fomc(2027,['01-27','03-17','04-28','06-09','07-28','09-15','10-27'])
        with tempfile.TemporaryDirectory() as tmp:
            data,report=publish.build(self.write_state(state(candidates),tmp),NOW)
        self.assertIn('fomc',report['live_families'])
        self.assertEqual(report['extended_years'],{})
        self.assertFalse(any(e['date'].startswith('2027-') for e in data['events']))

    def test_incomplete_pce_family_is_fully_retained(self):
        pce=self.reviewed_future('pce')[:-1];fed=self.reviewed_future('fomc');candidates=[candidate_from_reviewed(e) for e in pce+fed]
        with tempfile.TemporaryDirectory() as tmp:
            data,report=publish.build(self.write_state(state(candidates),tmp),NOW)
        self.assertNotIn('pce',report['live_families']);self.assertIn('pce',report['retained_families'])
        self.assertEqual([e for e in data['events'] if e['family']=='pce'],[e for e in calendar_snapshot.build()['events'] if e['family']=='pce'])

    def test_past_events_never_rewritten(self):
        candidates=self.current_live_candidates()+fomc(2027,['01-27','03-17','04-28','06-09','07-28','09-15','10-27','12-08'])
        with tempfile.TemporaryDirectory() as tmp:
            data,_=publish.build(self.write_state(state(candidates),tmp),NOW)
        old=[e for e in calendar_snapshot.build()['events'] if e['date']<'2026-09-14'];new=[e for e in data['events'] if e['date']<'2026-09-14'];self.assertEqual(old,new)

    def test_rollover_accepts_complete_new_year_family_when_reviewed_future_is_empty(self):
        candidates=fomc(2027,['01-27','03-17','04-28','06-09','07-28','09-15','10-27','12-08'])
        with tempfile.TemporaryDirectory() as tmp:
            data,report=publish.build(self.write_state(state(candidates,'2026-12-31T15:10:00Z'),tmp),NOW_2027)
        self.assertIn('fomc',report['live_families'])
        self.assertEqual(report['extended_years'],{'fomc':[2027]})
        self.assertEqual(len([e for e in data['events'] if e['family']=='fomc' and e['date'].startswith('2027-')]),8)

    def test_rollover_rejects_incomplete_new_year_family(self):
        candidates=fomc(2027,['01-27','03-17','04-28','06-09','07-28','09-15','10-27'])
        with tempfile.TemporaryDirectory() as tmp:
            data,report=publish.build(self.write_state(state(candidates,'2026-12-31T15:10:00Z'),tmp),NOW_2027)
        self.assertNotIn('fomc',report['live_families']);self.assertIn('fomc',report['retained_families'])
        self.assertFalse(any(e['date'].startswith('2027-') for e in data['events']))

    def test_rollover_monthly_family_requires_all_twelve_reference_periods(self):
        cpi=monthly_family('cpi',2027,probe.BLS_ICS)
        self.assertTrue(publish.annual_complete([publish.normalize_candidate(e) for e in cpi],'cpi',2027))
        self.assertFalse(publish.annual_complete([publish.normalize_candidate(e) for e in cpi[:-1]],'cpi',2027))

    def test_stale_state_falls_back_to_reviewed_snapshot(self):
        candidates=[candidate_from_reviewed(e) for e in self.reviewed_future('pce')]
        with tempfile.TemporaryDirectory() as tmp:
            data,report=publish.build(self.write_state(state(candidates,'2026-09-13T10:00:00Z'),tmp),NOW)
        self.assertEqual(report['mode'],'reviewed_static');self.assertEqual(data,calendar_snapshot.build())

    def test_unapproved_candidate_source_is_rejected(self):
        candidates=[candidate_from_reviewed(e) for e in self.reviewed_future('pce')]
        candidates[0]['source']='https://example.invalid/calendar'
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'candidate source'):
                publish.build(self.write_state(state(candidates),tmp),NOW)

    def test_no_state_file_uses_reviewed_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            data,report=publish.build(Path(tmp)/'missing.json',NOW)
        self.assertEqual(data,calendar_snapshot.build());self.assertEqual(report['live_families'],[])


if __name__=='__main__':unittest.main()
