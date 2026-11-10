# GXP — Geo eXchange Protocol

GXP is an experimental, transport-independent application protocol and
reference implementation for industrial events, mobile telemetry, and safe
device commands. Its first application profile is BusRoot, a public-transport
location system.

GXP does **not** replace IP, TLS, MQTT, HTTP, or QUIC. It adds a canonical
event envelope, explicit freshness semantics, durable edge spooling,
idempotent ingestion, and command-lifecycle controls above those transports.

## What is implemented in this repository

- GXP 0.1 JSON envelope validation and a language-neutral JSON Schema.
- Stable event IDs, device boot IDs, per-boot sequence validation, source and
  server receipt timestamps.
- Delivery classes: `LIVE_EPHEMERAL`, `DURABLE_EVENT`, `COMMAND`, `BULK`, and
  `HEARTBEAT`.
- SQLite/WAL durable edge outbox with priority ordering, retry backoff and
  jitter, acknowledgement deletion, and bounded live-event eviction.
- SQLite ingestion engine with transactional deduplication, sequence-conflict
  detection, durable history, freshness calculation, and live-state protection
  against stale or out-of-order positions.
- A standard-library HTTPS-capable HTTP transport and loopback development
  server protected by per-device bearer credentials.
- An optional MQTT 5 adapter, enabled only when the `mqtt` extra is installed.
- BusRoot position validation, simulator, conformance fixtures, and tests.

This is an experimental reference implementation. It is not production-ready,
not a safety system, and must not be exposed to the public Internet as-is.

## Quick start (development only)

The project has no required runtime dependency beyond Python 3.11+.

```powershell
py -3 -m unittest discover -s tests -v
py -3 -m gxp.cli bootstrap-device --db .\server.db --tenant busroot-kerala --device bus-104-gps
py -3 -m gxp.cli server --db .\server.db --host 127.0.0.1 --port 8080
```

The bootstrap command prints a bearer credential once. Store it in a secret
manager, not in source control. See [the installation guide](docs/installation.md)
and [security specification](specification/security-specification.md) before
trying the simulator.

## Repository map

- `specification/` — normative draft protocol documents and schemas.
- `gxp/` — dependency-light reference implementation.
- `tests/` — unit, integration, conformance, and fault tests.
- `examples/` — BusRoot simulator and demonstrators.
- `benchmarks/` — reproducible benchmark harnesses; results are not fabricated.
- `docs/` — architecture review, threat model, and operational guides.
- Root progress files — transparent session status, risks, limitations, and
  human actions.

For a high-level reading path, start with [GXP_SPECIFICATION.md](GXP_SPECIFICATION.md),
[GXP_ARCHITECTURE.md](GXP_ARCHITECTURE.md),
[GXP_DEVELOPER_GUIDE.md](GXP_DEVELOPER_GUIDE.md), and
[RELEASE_READINESS.md](RELEASE_READINESS.md).

## Current status

The Phase 0 architecture review and a first Phase 1–3 reference slice are in
progress. See [PROJECT_STATUS.md](PROJECT_STATUS.md) and
[KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) for the actual state.

