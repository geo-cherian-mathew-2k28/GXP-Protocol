from __future__ import annotations

import tempfile
import unittest

from gxp.errors import SequenceConflict
from gxp.ingestion import IngestionStore

from helpers import clone_event, make_agent, make_position, stale_timestamp


class IngestionTests(unittest.TestCase):
    def test_duplicate_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = IngestionStore(f"{directory}/server.db")
            event = make_position(make_agent(f"{directory}/edge.db"))
            first = store.ingest(event)
            duplicate = store.ingest(event)
            self.assertEqual(first.status, "accepted")
            self.assertEqual(duplicate.status, "duplicate")
            self.assertEqual(store.event_count(), 1)

    def test_same_sequence_with_another_event_is_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = IngestionStore(f"{directory}/server.db")
            event = make_position(make_agent(f"{directory}/edge.db"))
            store.ingest(event)
            conflict = clone_event(event)
            conflict["event"]["id"] = "33333333-3333-4333-8333-333333333333"
            with self.assertRaises(SequenceConflict):
                store.ingest(conflict)

    def test_delayed_position_does_not_replace_fresh_live_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = IngestionStore(f"{directory}/server.db")
            agent = make_agent(f"{directory}/edge.db")
            fresh = make_position(agent, latitude=9.5661)
            accepted = store.ingest(fresh)
            delayed = make_position(agent, latitude=9.5000, observed_at=stale_timestamp(), max_age_ms=1_000)
            delayed_ack = store.ingest(delayed)
            state = store.get_live_state("busroot-kerala", "bus-104-gps")
            self.assertTrue(accepted.live_state_updated)
            self.assertFalse(delayed_ack.live_state_updated)
            self.assertEqual(state["event_id"], fresh["event"]["id"])
            self.assertEqual(state["payload"]["latitude"], 9.5661)
            self.assertEqual(store.event_count(), 2)

