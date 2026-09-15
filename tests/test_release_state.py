"""Contract tests for the v0.7 operational release-state model."""
import copy
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import release_state as state


def valid_state():
    return {
        'schema_version': state.SCHEMA_VERSION,
        'release': {
            'version': '0.7.0',
            'channel': 'public',
            'verified_at': None,
            'build_run_id': '34946711001',
        },
        'market': {
            'delivery_mode': 'provider_hosted',
            'quote_observation': 'not_observed_by_build',
            'data_persisted': False,
            'snapshot_as_of': '2026-09-10',
            'freshness': 'unknown',
        },
        'macro': {
            'attempted_at': '2026-09-15T08:00:00+00:00',
            'available_count': 6,
            'total_count': 6,
            'freshness': 'fresh',
        },
        'calendar': {
            'source_health': 'partial_access_blocked',
            'mode': 'family_merge',
            'verified_at': None,
        },
        'event': {
            'active_event_ids': ['fomc-2026-09','boj-2026-09'],
            'phase': 'pre_event',
            'phase_verified_at': '2026-09-15T17:00:00+09:00',
        },
        'modules': {
            'market': 'available',
            'macro': 'available',
            'events': 'available',
            'research': 'reviewed_static',
        },
        'publication': {
            'legacy_market_public_presence': 'published',
            'legacy_market_visibility': 'hidden',
            'use_legacy_market_for_current_decisions': False,
        },
    }


class ReleaseStateTests(unittest.TestCase):
    def test_valid_state(self):
        value=valid_state()
        self.assertIs(state.validate(value),value)

    def test_canonical_serialization_is_deterministic(self):
        value=valid_state()
        self.assertEqual(state.dumps(value),state.dumps(copy.deepcopy(value)))

    def test_unknown_top_level_field_is_rejected(self):
        value=valid_state();value['private_notes']='bad'
        with self.assertRaises(state.ReleaseStateError):state.validate(value)

    def test_missing_top_level_field_is_rejected(self):
        value=valid_state();del value['calendar']
        with self.assertRaises(state.ReleaseStateError):state.validate(value)

    def test_naive_timestamp_is_rejected(self):
        value=valid_state();value['macro']['attempted_at']='2026-09-15T08:00:00'
        with self.assertRaises(state.ReleaseStateError):state.validate(value)

    def test_bad_semantic_version_is_rejected(self):
        value=valid_state();value['release']['version']='v0.7'
        with self.assertRaises(state.ReleaseStateError):state.validate(value)

    def test_non_numeric_run_id_is_rejected(self):
        value=valid_state();value['release']['build_run_id']='latest'
        with self.assertRaises(state.ReleaseStateError):state.validate(value)

    def test_provider_hosted_market_cannot_be_marked_persisted(self):
        value=valid_state();value['market']['data_persisted']=True
        with self.assertRaises(state.ReleaseStateError):state.validate(value)

    def test_quote_delivery_and_observation_are_separate(self):
        value=valid_state()
        self.assertEqual(value['market']['delivery_mode'],'provider_hosted')
        self.assertEqual(value['market']['quote_observation'],'not_observed_by_build')
        state.validate(value)

    def test_macro_count_cannot_exceed_total(self):
        value=valid_state();value['macro']['available_count']=7
        with self.assertRaises(state.ReleaseStateError):state.validate(value)

    def test_duplicate_active_event_ids_are_rejected(self):
        value=valid_state();value['event']['active_event_ids']=['fomc-2026-09','fomc-2026-09']
        with self.assertRaises(state.ReleaseStateError):state.validate(value)

    def test_not_published_content_cannot_be_visible(self):
        value=valid_state();value['publication']['legacy_market_public_presence']='not_published';value['publication']['legacy_market_visibility']='visible'
        with self.assertRaises(state.ReleaseStateError):state.validate(value)

    def test_hidden_and_not_published_are_not_conflated(self):
        value=valid_state();state.validate(value)
        self.assertEqual(value['publication']['legacy_market_public_presence'],'published')
        self.assertEqual(value['publication']['legacy_market_visibility'],'hidden')

    def test_current_decision_data_must_be_visible(self):
        value=valid_state();value['publication']['use_legacy_market_for_current_decisions']=True
        with self.assertRaises(state.ReleaseStateError):state.validate(value)

    def test_invalid_module_status_is_rejected(self):
        value=valid_state();value['modules']['market']='live'
        with self.assertRaises(state.ReleaseStateError):state.validate(value)


if __name__=='__main__':
    unittest.main()
