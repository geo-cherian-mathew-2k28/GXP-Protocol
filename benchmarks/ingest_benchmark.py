"""Small, reproducible in-process ingestion benchmark harness.

It intentionally reports only what it executes. It does not compare MQTT,
HTTPS, Sparkplug, QUIC, hardware power, or real cellular performance; those
need an equivalent external test environment.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

# Support the documented direct-script invocation without requiring installation.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from gxp.edge import EdgeAgent, SQLiteEdgeSpool
from gxp.ingestion import IngestionStore


def percentile(values: list[float], percentage: float) -> float:
    if not values:
        return 0.0
    index = min(len(values) - 1, round((len(values) - 1) * percentage))
    return sorted(values)[index]


def run(event_count: int, workdir: Path) -> dict[str, object]:
    store = IngestionStore(workdir / "server.db")
    agent = EdgeAgent("benchmark", "device-1", SQLiteEdgeSpool(workdir / "edge.db"), clock_quality="network")
    timings_ms: list[float] = []
    for number in range(event_count):
        event = agent.create_event(
            kind="telemetry",
            event_type="vehicle.position",
            schema="gxp.busroot.position",
            payload={"latitude": 9.5661 + number / 1_000_000, "longitude": 76.7874, "gps_fix": True},
            delivery_class="LIVE_EPHEMERAL",
            priority=3,
            max_age_ms=60_000,
            quality={"status": "valid"},
        )
        started = time.perf_counter()
        store.ingest(event)
        timings_ms.append((time.perf_counter() - started) * 1000)
    return {
        "status": "MEASURED_LOCAL_IN_PROCESS_ONLY",
        "events": event_count,
        "latency_ms": {
            "min": min(timings_ms),
            "mean": statistics.mean(timings_ms),
            "p50": percentile(timings_ms, 0.50),
            "p95": percentile(timings_ms, 0.95),
            "p99": percentile(timings_ms, 0.99),
            "max": max(timings_ms),
        },
        "scope": "Python process + SQLite on this host; excludes network, TLS, MQTT broker, GPS, and cellular behavior.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark local GXP ingestion")
    parser.add_argument("--events", type=int, default=1_000)
    parser.add_argument("--workdir", type=Path)
    args = parser.parse_args()
    if args.events < 1:
        parser.error("--events must be positive")
    if args.workdir:
        args.workdir.mkdir(parents=True, exist_ok=True)
        result = run(args.events, args.workdir)
    else:
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = run(args.events, Path(temporary_directory))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

