# Project status

## Current milestone

**Phase 0 complete; Phase 1–3 reference slice implemented and locally tested.**

The project started from an empty repository on 10 November 2026. The supplied
PRD and master engineering prompt were reviewed as design inputs, not treated
as authority over verified standards or the user's instructions.

## Completed in this session

- Cloned the supplied, empty GitHub repository.
- Reviewed the PRD and master engineering prompt.
- Performed initial standards research and wrote the architecture review.
- Chosen a deliberately small v0.1 boundary: JSON, Python standard library,
  SQLite, HTTP/TLS mapping, optional MQTT 5 mapping, and no QUIC implementation.
- Implemented and tested the envelope validator, SQLite/WAL edge outbox,
  retry/replay behavior, transactionally idempotent ingestion, freshness-aware
  BusRoot live state, development credential registry, HTTP/JSON transport and
  server, and optional MQTT publish adapter.
- Added a local BusRoot outage/replay simulator, a narrowly scoped in-process
  ingestion benchmark harness, CI configuration, developer/release-readiness
  documents, and Docker development material.
- Pivoted GXP's canonical direction to a native GXP/1 framed application
  protocol; added the architectural specification, ADR, binary frame codec, and
  parser tests. HTTP/MQTT remain compatibility paths rather than GXP's core.

## In progress

- Native GXP/TCP/TLS session listener/client, GXP-M/1 embedded client, complete
  frame registry/test vectors, and a production-environment design reviewed
  with the owner.

## Not complete

- Production mTLS/certificate lifecycle, HSM/secure-element support, operator
  authentication, rate limiting, PostgreSQL/PostGIS, Redis, MQTT broker
  integration testing, native GXP/TCP session runtime, embedded GXP-M/1,
  QUIC, Sparkplug/OPC UA bridges, independent
  implementation, physical-device testing, and benchmarks.

See `TEST_RESULTS.md` for test execution evidence after the first test run.

