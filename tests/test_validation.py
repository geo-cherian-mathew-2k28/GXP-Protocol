from __future__ import annotations

import tempfile
import unittest
from datetime import timedelta

from gxp.errors import CommandExpired, FutureEvent, InvalidPosition, MalformedMessage
from gxp.timeutil import format_instant, utc_now
from gxp.validation import validate_envelope

from helpers import make_agent, make_position


class ValidationTests(unittest.TestCase):
    def test_valid_busroot_position(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            event = make_position(make_agent(f"{directory}/edge.db"))
            validate_envelope(event)

    def test_rejects_out_of_bounds_coordinates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            event = make_position(make_agent(f"{directory}/edge.db"))
            event["payload"]["latitude"] = 91
            with self.assertRaises(InvalidPosition):
                validate_envelope(event)

    def test_live_event_requires_expiry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            event = make_position(make_agent(f"{directory}/edge.db"))
            del event["delivery"]["max_age_ms"]
            with self.assertRaises(MalformedMessage):
                validate_envelope(event)

    def test_rejects_future_source_time(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            event = make_position(make_agent(f"{directory}/edge.db"))
            event["time"]["observed_at"] = format_instant(utc_now() + timedelta(minutes=6))
            with self.assertRaises(FutureEvent):
                validate_envelope(event)

    def test_expired_command_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            agent = make_agent(f"{directory}/edge.db")
            with self.assertRaises(CommandExpired):
                agent.create_event(
                    kind="command",
                    event_type="device.command",
                    schema="gxp.command",
                    payload={
                        "command_id": "22222222-2222-4222-8222-222222222222",
                        "issuer": "operator:alice",
                        "operation": "diagnostics.snapshot",
                        "expires_at": format_instant(utc_now() - timedelta(seconds=1)),
                        "parameters": {},
                    },
                    delivery_class="COMMAND",
                    priority=9,
                    quality={"status": "valid"},
                )

