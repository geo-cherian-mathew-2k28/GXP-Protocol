from __future__ import annotations

import tempfile
import unittest
from datetime import timedelta
import json

from gxp.errors import StorageExhausted, TransportFailure
from gxp.models import IngestionAck
from gxp.timeutil import utc_now

from helpers import make_agent, make_position


class AcceptingTransport:
    def __init__(self) -> None:
        self.events = []

    def send(self, event):
        self.events.append(event)
        return IngestionAck("accepted", event["event"]["id"], "2026-11-10T12:30:06.000Z")


class FailingTransport:
    def send(self, event):
        raise TransportFailure("simulated outage")


class EdgeSpoolTests(unittest.TestCase):
    def test_event_is_persisted_and_deleted_only_after_ingestion_ack(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            agent = make_agent(f"{directory}/edge.db")
            event = make_position(agent)
            self.assertEqual(agent.spool.depth(), 1)
            failed = agent.flush(FailingTransport())
            self.assertEqual(failed, {"acknowledged": 0, "retried": 1, "rejected": 0})
            self.assertEqual(agent.spool.depth(), 1)
            transport = AcceptingTransport()
            # Make retry eligibility independent of random jitter.
            retried = agent.flush(transport, now=utc_now() + timedelta(minutes=10))
            self.assertEqual(retried, {"acknowledged": 1, "retried": 0, "rejected": 0})
            self.assertEqual(agent.spool.depth(), 0)
            self.assertEqual(event["event"]["id"], transport.events[0]["event"]["id"])

    def test_accepting_transport_removes_event(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            agent = make_agent(f"{directory}/edge.db")
            make_position(agent)
            transport = AcceptingTransport()
            result = agent.flush(transport)
            self.assertEqual(result, {"acknowledged": 1, "retried": 0, "rejected": 0})
            self.assertEqual(agent.spool.depth(), 0)
            self.assertEqual(len(transport.events), 1)

    def test_quota_never_silently_drops_durable_event(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            agent = make_agent(f"{directory}/edge.db")
            first = agent.create_event(
                kind="event",
                event_type="vehicle.door_fault",
                schema="gxp.busroot.fault",
                payload={"door": "front", "state": "open"},
                delivery_class="DURABLE_EVENT",
                priority=9,
                quality={"status": "valid"},
            )
            # Fit exactly the existing durable record but not another one.
            agent.spool.quota_bytes = len(json.dumps(first, separators=(",", ":")).encode("utf-8"))
            with self.assertRaises(StorageExhausted):
                agent.create_event(
                    kind="event",
                    event_type="vehicle.door_fault",
                    schema="gxp.busroot.fault",
                    payload={"door": "rear", "state": "open"},
                    delivery_class="DURABLE_EVENT",
                    priority=9,
                    quality={"status": "valid"},
                )
            self.assertEqual(agent.spool.depth(), 1)

