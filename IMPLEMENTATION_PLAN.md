# Implementation plan

## Scope guardrails

GXP v0.1 is an application-level event protocol. It will not invent a transport
layer, claim exactly-once business processing, control safety-critical vehicle
functions, or claim standards status.

## Milestones

1. **Architecture and protocol freeze** — draft the canonical envelope,
   validation rules, delivery classes, acknowledgement meanings, error model,
   and BusRoot profile. Add conformance fixtures.
2. **Reference core** — implement encoder/validator, event generation and
   persistent sequence state.
3. **Reliability slice** — implement SQLite/WAL outbox, prioritised replay,
   backoff, acknowledgement deletion, quota policy, server deduplication, and
   live-state freshness protection.
4. **Transport slice** — implement HTTP/JSON over TLS support and an optional
   MQTT 5 adapter. Document the exact semantic mappings.
5. **BusRoot slice** — position schema, simulator, live-state endpoint, and
   fault-oriented tests.
6. **Security and operations** — replace development credential handling with
   deployment-specific mTLS and authorization, add audit/rate-limit/metrics
   integrations, then perform an independent review.

## Acceptance criteria for this session

- A valid BusRoot position is generated, spooled, accepted once, and can be
  acknowledged.
- Replayed duplicate events are accepted idempotently without changing history
  or live state.
- A delayed or expired live position remains historical and cannot replace a
  newer live position.
- Invalid coordinates, sequence conflicts, expired commands, and unauthenticated
  HTTP ingestion are rejected by automated tests.

