"""Completeness and retention tests for live official calendar publication."""
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


def candidate_from_reviewed(event):
    raw_source={
        'cpi':probe.BLS_CPI,
        'jobs':probe.BLS_JOBS,
        'pce':probe.BEA_SCHEDULE,
        'fomc':probe.FED_FOMC,
    }[event['family']]
    return {k:event[k] for k in ['family','date','period','time_local','time_jst']} | {'source':raw_source}


def state(candidates,checked_at='2026-09-13T17:50:00Z'):
    return {
        'calendar_probe_health':'partial_access_blocked',
        'checked_at':checked_at,
        'publication':'staged_for_completeness_gate',
        'candidate_events':candidates,
        'changes':[],
        'errors':[{'source':'bls-cpi-html','error':'HTTPError','code':403}],
        'advisories':[{'source':'bls-ics','error':'HTTPError','code':403}],
        'source_modes':{'bls':'partial_html_fallback','bea':'primary','fed':'primary'},
    }


class CalendarPublishTests(unittest.TestCase):
    def write_state(self,data,tmp):
        path=Path(tmp)/'state.json';path.write_text(json.dumps(data),encoding='utf-8');return path

    def reviewed_future(self,family):
        return [e for e in calendar_snapshot.build()['events'] if e['family']==family and e['date']>='2026-09-14']

    def test_bea_and_fed_live_bls_retained(self):
        candidates=[candidate_from_reviewed(e) for family in ('pce','fomc') for e in self.reviewed_future(family)]
        pce=next(e for e in candidates if e['family']=='pce' and e['period']=='2026-08');pce['date']='2026-10-01';pce['time_jst']='2026-10-01 21:30'
        with tempfile.TemporaryDirectory() as tmp:
            data,report=publish.build(self.write_state(state(candidates),tmp),NOW)
        self.assertEqual(report['live_families'],['pce','fomc'])
        self.assertEqual(report['retained_families'],['cpi','jobs'])
        self.assertIn('2026-10-01',{e['date'] for e in data['events'] if e['family']=='pce'})
        self.assertEqual([e for e in data['events'] if e['family']=='cpi'],[e for e in calendar_snapshot.build()['events'] if e['family']=='cpi'])

    def test_incomplete_pce_family_is_fully_retained(self):
        pce=self.reviewed_future('pce')[:-1];fed=self.reviewed_future('fomc');candidates=[candidate_from_reviewed(e) for e in pce+fed]
        with tempfile.TemporaryDirectory() as tmp:
            data,report=publish.build(self.write_state(state(candidates),tmp),NOW)
        self.assertNotIn('pce',report['live_families']);self.assertIn('pce',report['retained_families'])
        self.assertEqual([e for e in data['events'] if e['family']=='pce'],[e for e in calendar_snapshot.build()['events'] if e['family']=='pce'])

    def test_past_events_never_rewritten(self):
        candidates=[candidate_from_reviewed(e) for family in ('pce','fomc') for e in self.reviewed_future(family)]
        with tempfile.TemporaryDirectory() as tmp:
            data,_=publish.build(self.write_state(state(candidates),tmp),NOW)
        old=[e for e in calendar_snapshot.build()['events'] if e['date']<'2026-09-14'];new=[e for e in data['events'] if e['date']<'2026-09-14'];self.assertEqual(old,new)

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
