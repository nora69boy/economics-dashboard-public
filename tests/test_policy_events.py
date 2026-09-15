"""Tests for the v0.7 typed strategic policy-event model."""
import copy
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import policy_events as events

class PolicyEventTests(unittest.TestCase):
 def test_reviewed_event_set_is_valid_and_unique(self):
  values=events.validate_events();self.assertEqual(len(values),4);self.assertEqual(len({x['id'] for x in values}),4)
 def test_schedule_claims_are_fact_not_outcome_claims(self):
  for event in events.EVENTS:
   self.assertEqual(event['claim_class'],'FACT');self.assertEqual(event['outcome_state'],'scheduled');self.assertIsNone(event['outcome_verified_at'])
 def test_unknown_boj_decision_time_has_no_invented_timestamp(self):
  event=events.by_id('boj-policy-decision-2026-09');self.assertEqual(event['time_precision'],'unknown');self.assertIsNone(event['scheduled_at'])
 def test_exact_times_require_timezone(self):
  values=list(copy.deepcopy(events.EVENTS));values[0]['scheduled_at']='2026-09-17T03:00:00'
  with self.assertRaises(events.PolicyEventError):events.validate_events(tuple(values))
 def test_unknown_time_rejects_timestamp(self):
  values=list(copy.deepcopy(events.EVENTS));values[2]['scheduled_at']='2026-09-18T12:00:00+09:00'
  with self.assertRaises(events.PolicyEventError):events.validate_events(tuple(values))
 def test_duplicate_ids_rejected(self):
  values=list(copy.deepcopy(events.EVENTS));values[1]['id']=values[0]['id']
  with self.assertRaises(events.PolicyEventError):events.validate_events(tuple(values))
 def test_pre_fomc_phase(self):
  at=datetime.fromisoformat('2026-09-16T12:00:00+09:00');self.assertEqual(events.phase_at(at),'pre_fomc')
 def test_clock_passage_does_not_mark_fomc_complete(self):
  at=datetime.fromisoformat('2026-09-17T03:05:00+09:00');self.assertEqual(events.phase_at(at),'fomc_statement_due_unverified')
 def test_even_later_clock_passage_still_requires_outcome_verification(self):
  at=datetime.fromisoformat('2026-09-19T12:00:00+09:00');self.assertEqual(events.phase_at(at),'fomc_statement_due_unverified')
 def test_verified_fomc_statement_allows_next_phase_only(self):
  values=list(copy.deepcopy(events.EVENTS));values[0]['outcome_state']='outcome_verified';values[0]['outcome_verified_at']='2026-09-17T03:02:00+09:00'
  at=datetime.fromisoformat('2026-09-17T03:10:00+09:00');self.assertEqual(events.phase_at(at,tuple(values)),'fomc_statement_verified_press_conference_pending')
 def test_active_ids_use_explicit_validity_window(self):
  active=events.active_event_ids(datetime.fromisoformat('2026-09-15T17:00:00+09:00'));self.assertEqual(set(active),{x['id'] for x in events.EVENTS})
  self.assertEqual(events.active_event_ids(datetime.fromisoformat('2026-09-22T00:00:00+09:00')),[])
 def test_naive_phase_time_rejected(self):
  with self.assertRaises(events.PolicyEventError):events.phase_at(datetime(2026,9,17,3,5))

if __name__=='__main__':unittest.main()
