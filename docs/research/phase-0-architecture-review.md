# Phase 0 architecture review

**Status:** completed design review; implementation evidence is tracked
separately.  
**Inputs reviewed:** supplied GXP PRD (architecture proposal 0.1), supplied
master engineering prompt, and the standards sources linked below.  
**Decision:** proceed with a small application-protocol reference, not a new
network transport.

## Executive conclusion

The strongest credible GXP proposition is not a new replacement for MQTT, HTTP,
QUIC, TLS, or OPC UA. It is a transport-independent event contract plus a
reliable edge/runtime pattern for five situations that existing transports do
not standardise together:

1. freshness and explicit expiry of mobile telemetry;
2. durable store-and-forward that preserves original event identity and time;
3. deterministic ingestion deduplication and safe live-state ordering;
4. a restricted, expiring, auditable device-command lifecycle; and
5. portable profiles and conformance material above transport-specific details.

The first implementation should be generic at the envelope level and BusRoot
specific at the `vehicle.position` profile level. That avoids a bus-only
protocol while keeping the first testable use case small.

## What the PRD gets right

- It correctly treats freshness as different from transport delivery success:
  delayed GPS belongs in history, not silently in the live position.
- It separates event identity from sequence numbers and avoids claiming magical
  exactly-once business processing.
- It makes edge persistence, replay, priority, device mobility, clock quality,
  and command expiry first-class concerns.
- It positions MQTT, Sparkplug, QUIC, and OPC UA as integration points, not
  competitors to caricature.
- It explicitly prohibits safety-critical vehicle controls and unsubstantiated
  performance claims.

## Standards reality check

| Technology | Existing capability | GXP consequence |
| --- | --- | --- |
| MQTT 5 | Lightweight client/server pub-sub transport with QoS 0/1/2. QoS 1 permits duplicates and QoS 2 is a protocol-peer guarantee. | Do not market GXP as replacing MQTT reliability. Map the GXP envelope to MQTT and retain server-side idempotency. |
| Sparkplug | Defines an MQTT topic namespace, payload conventions, and session/state management for IIoT. | Build a bridge only when target customers need it; never rename Sparkplug features as GXP innovations. |
| QUIC | Provides multiplexed secure streams and client connection migration, subject to endpoint and path support. | Treat QUIC as an optional adapter; application replay remains required when migration is unavailable. |
| OPC UA PubSub | Distributes data/events to observers across device and IT/cloud contexts. | Preserve OPC UA models; provide a mapping later rather than replacing them. |
| URI registration | `gxp` is not a registration merely because it appears in source. The IANA registry has separate permanent/provisional procedures. | Keep the scheme provisional and defer any submission to the project owner. |

## Critical requirements reconciliation

The design inputs contain a few ambiguities that are resolved here.

| Topic | Resolution for v0.1 |
| --- | --- |
| Event vs request/response | Event-first. Commands are envelope kind `command`, but command execution is a separate, explicit lifecycle—not an RPC shortcut. |
| Sequence scope | An event has a globally unique ID and a monotonic positive sequence **within `(tenant, device, boot_id)`**. The agent persists sequence state across a clean restart where possible; `boot_id` makes a reset observable. Event ID is the durable dedupe key. |
| Arrival vs observation time | The server creates `received_at`; the device may supply `observed_at` and `sent_at` only. Live ordering uses source time and validated freshness, never arrival time alone. |
| Live expiry | Expired `LIVE_EPHEMERAL` telemetry can be accepted into history but cannot update live state. `DURABLE_EVENT` remains persistable despite a delayed receipt unless an application profile says otherwise. |
| Authentication | The reference server has a per-device, high-entropy bearer-token development profile over TLS. Production requires an approved mTLS/equivalent lifecycle, authorization, key storage, rotation, and revocation design. |
| JSON vs binary | JSON/UTF-8 is canonical for 0.1. No CBOR/Protobuf profile is added before measurements justify it. |
| Database choice | SQLite/WAL is sufficient for a single edge agent and local demonstrator. It is not the target multi-node ingestion datastore. |

## Missing requirements now made explicit

1. Define the durable transaction boundary: for a new event, the ingestion
   record, dedupe key, sequence observation, history, and permitted live-state
   mutation commit together before an ingestion acknowledgement is returned.
2. Define a clock-skew policy: an event too far in the future is rejected; an
   old event remains historical, and its clock quality is observable.
3. Define sequence conflict: the same device/boot/sequence with a different
   event ID is a conflict, not a duplicate.
4. Separate public passenger data from device ingestion and operator control;
   they cannot share the same unauthenticated endpoint or credentials.
5. Define storage exhaustion behavior: evict only eligible unsent live events;
   never silently evict a durable/critical event. If no eligible record exists,
   reject the new write and surface the failure.
6. Define command replay: command IDs are durable per target; expiry and the
   allowlist are checked before acceptance and again before execution.
7. Define payload ownership: a device cannot self-assert authoritative vehicle
   or route association; provisioning owns those bindings.

## Complexity intentionally deferred

- New UDP/TCP transport, custom cryptography, global name resolution, and
  browser-native `gxp` handlers.
- QUIC implementation and field compatibility claims.
- MQTT broker implementation, Sparkplug/OPC UA bridge, PostGIS, Redis,
  microservices, Kubernetes, and dashboard product.
- Firmware updates, binary bulk transfer, secure-element integration, and
  safety-critical controls.

These are not omissions hidden by a diagram. They are explicitly deferred until
the core semantics have independent-test evidence.

## Architecture selected

```text
sensor/GNSS -> edge normalizer -> GXP envelope -> SQLite/WAL outbox
                                                   | (retry, priority, replay)
                                          HTTP/TLS or MQTT 5 adapter
                                                   |
                                      authenticated GXP ingestion contract
                                                   |
                          validation -> transactional dedupe/history -> freshness gate
                                                                    |              |
                                                              live state        history/events
```

The contract is canonical; adapters must preserve event ID, device identity,
boot ID, sequence, source time, schema version, delivery class, and the
meaning of the acknowledgement. A transport acknowledgement is never
substituted for a GXP ingestion acknowledgement.

## Initial risk register

| Risk | Control / remaining gap |
| --- | --- |
| Provisional name or URI collision | No registration/ownership claim; owner action required. |
| Replayed telemetry or commands | Durable event/command IDs, dedupe, TLS, command expiry; production signing/mTLS remains open. |
| Clock failure makes data look current | `clock_quality`, source/server timestamps, future-skew rejection, freshness gate. |
| Cellular outage fills storage | Quota, live-only eviction, explicit backpressure/error; capacity sizing requires fleet data. |
| Duplicate business effects | At-least-once transfer plus transactionally idempotent ingestion; downstream systems must retain idempotency keys. |
| Unauthorized public access | Loopback development server only; production access model remains a required human-approved decision. |
| Overclaiming | Benchmark harnesses only; no result or superiority claim without measured baseline. |

## Sources consulted

- [OASIS MQTT Version 5.0](https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html)
- [Eclipse Sparkplug specification](https://sparkplug.eclipse.org/specification/)
- [RFC 9000 — QUIC](https://www.rfc-editor.org/rfc/rfc9000.html)
- [OPC UA Part 14 — PubSub](https://reference.opcfoundation.org/specs/OPC-10000-14/full)
- [IANA URI Schemes registry](https://www.iana.org/assignments/uri-schemes)
- [RFC 7595 — URI scheme registration guidelines](https://www.rfc-editor.org/rfc/rfc7595.html)

