from __future__ import annotations

import copy
from datetime import timedelta

from gxp.edge import EdgeAgent, SQLiteEdgeSpool
from gxp.timeutil import format_instant, utc_now


def make_agent(path, *, quota_bytes: int = 10_000_000, boot_id: str = "11111111-1111-4111-8111-111111111111") -> EdgeAgent:
    return EdgeAgent("busroot-kerala", "bus-104-gps", SQLiteEdgeSpool(path, quota_bytes=quota_bytes), boot_id=boot_id, clock_quality="gnss")


def make_position(agent: EdgeAgent, *, latitude: float = 9.5661, longitude: float = 76.7874, observed_at: str | None = None, max_age_ms: int = 15_000):
    return agent.create_event(
        kind="telemetry",
        event_type="vehicle.position",
        schema="gxp.busroot.position",
        payload={"latitude": latitude, "longitude": longitude, "speed_kmh": 32.4, "heading_deg": 87.0, "gps_fix": True},
        delivery_class="LIVE_EPHEMERAL",
        priority=3,
        max_age_ms=max_age_ms,
        observed_at=observed_at,
        quality={"status": "valid", "position_accuracy_m": 5.0},
    )


def stale_timestamp(seconds: int = 60) -> str:
    return format_instant(utc_now() - timedelta(seconds=seconds))


def clone_event(envelope):
    return copy.deepcopy(envelope)

