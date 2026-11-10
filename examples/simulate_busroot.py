"""Demonstrate BusRoot offline replay without requiring a network service.

This is a deterministic local demonstration of GXP semantics, not a substitute
for a GPS/cellular field trial. Run with:

    py -3 examples/simulate_busroot.py
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

# Support the documented direct-script invocation without requiring installation.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from gxp.edge import EdgeAgent, SQLiteEdgeSpool
from gxp.errors import TransportFailure
from gxp.ingestion import IngestionStore
from gxp.timeutil import format_instant, utc_now


class SimulatedTransport:
    def __init__(self, store: IngestionStore) -> None:
        self.store = store
        self.online = False

    def send(self, envelope):
        if not self.online:
            raise TransportFailure("simulated cellular outage")
        return self.store.ingest(envelope)


def position(agent: EdgeAgent, latitude: float, longitude: float, *, observed_at: str | None = None, max_age_ms: int = 15_000):
    return agent.create_event(
        kind="telemetry",
        event_type="vehicle.position",
        schema="gxp.busroot.position",
        payload={"latitude": latitude, "longitude": longitude, "speed_kmh": 28.0, "heading_deg": 87.0, "gps_fix": True},
        delivery_class="LIVE_EPHEMERAL",
        priority=3,
        max_age_ms=max_age_ms,
        observed_at=observed_at,
        quality={"status": "valid", "position_accuracy_m": 5.0},
    )


def run(workdir: Path) -> dict[str, object]:
    spool = SQLiteEdgeSpool(workdir / "edge.db")
    store = IngestionStore(workdir / "server.db")
    agent = EdgeAgent("busroot-kerala", "bus-104-gps", spool, clock_quality="gnss")
    transport = SimulatedTransport(store)

    # Sampling continues during an outage and is retained locally.
    position(agent, 9.5661, 76.7874)
    position(agent, 9.5665, 76.7880)
    outage = agent.flush(transport)
    queued_during_outage = spool.depth()

    # On reconnect, the existing event IDs/timestamps are replayed; no new event
    # is manufactured merely because connectivity returned.
    transport.online = True
    recovery = agent.flush(transport, now=utc_now() + timedelta(minutes=10))
    live_after_recovery = store.get_live_state("busroot-kerala", "bus-104-gps")

    # A much older point is useful as history but cannot regress current state.
    old = position(
        agent,
        9.5000,
        76.7000,
        observed_at=format_instant(utc_now() - timedelta(minutes=2)),
        max_age_ms=15_000,
    )
    delayed = agent.flush(transport)
    final_live = store.get_live_state("busroot-kerala", "bus-104-gps")
    return {
        "outage_flush": outage,
        "queued_during_outage": queued_during_outage,
        "recovery_flush": recovery,
        "delayed_flush": delayed,
        "history_events": store.event_count(),
        "live_event_after_recovery": live_after_recovery["event_id"] if live_after_recovery else None,
        "old_event_id": old["event"]["id"],
        "final_live_event": final_live["event_id"] if final_live else None,
        "stale_event_rejected_from_live": bool(final_live and final_live["event_id"] != old["event"]["id"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local BusRoot offline/replay simulation")
    parser.add_argument("--workdir", type=Path, help="Optional directory to retain the demonstration SQLite databases")
    args = parser.parse_args()
    if args.workdir:
        args.workdir.mkdir(parents=True, exist_ok=True)
        result = run(args.workdir)
    else:
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = run(Path(temporary_directory))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

