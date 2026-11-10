# Implementation plan

## Scope guardrails

GXP is an application-level protocol with its own native GXP/1 frame and
session semantics. It will not invent IP, TLS cryptography, congestion control,
or cellular networking; GXP/TCP uses TLS and a future GXP/QUIC binding uses
QUIC. It will not claim exactly-once business processing, control
safety-critical vehicle functions, or claim standards status.

## Milestones

1. **Native protocol freeze** — define GXP/1 framing, handshake, capability
   negotiation, ACK/resume, credit, error registry, and GXP-M/1 micro profile.
2. **Native reference core** — implement/test frame codec, streaming parser,
   session state machine, payload encoding, and conformance vectors.
3. **Native reliability runtime** — implement GXP/TCP/TLS listener/client,
   durable resume cursor, priority scheduling, and transactional ACK boundary.
4. **Compatibility bridges** — retain HTTP/MQTT adapters only as documented
   bridges into native GXP semantics; broker behavior needs integration tests.
5. **Application profiles** — BusRoot, smart-feeder, and other profiles with
   versioned schemas, constraints, command policy, and fault-oriented tests.
6. **Security and operations** — production device enrolment, mTLS,
   authorisation, audit/rate-limit/metrics, fuzzing, and independent review.

## Acceptance criteria for this session

- A valid BusRoot position is generated, spooled, accepted once, and can be
  acknowledged.
- Replayed duplicate events are accepted idempotently without changing history
  or live state.
- A delayed or expired live position remains historical and cannot replace a
  newer live position.
- Invalid coordinates, sequence conflicts, expired commands, and unauthenticated
  HTTP ingestion are rejected by automated tests.
- Native GXP/1 binary frames encode/decode correctly, reject malformed magic and
  duplicate extensions, and stream-decode fragmented/coalesced input.

