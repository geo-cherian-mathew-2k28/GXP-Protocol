# GXP/1 native protocol — architecture draft

## Status

GXP/1 is the proposed native wire protocol for GXP. This document freezes the
first architectural direction; it is not a completed, interoperable
specification or a production implementation yet.

GXP/1 is custom at the **application protocol** layer. It owns its frame types,
session semantics, acknowledgements, resume, flow control, event/command model,
and profile negotiation. It deliberately reuses proven transport security and
congestion control rather than inventing encryption or a new Internet transport.

## The protocol stack

```text
GXP application profiles     BusRoot · smart feeder · industrial asset
GXP/1 native protocol        handshake · frames · ACK · resume · command safety
GXP transport binding        GXP/TCP/TLS 1.3 first; GXP/QUIC later
Internet transport           TCP/IP or QUIC/UDP/IP
```

MQTT and HTTP may bridge into or out of GXP/1 for migration. They do not define
the canonical GXP/1 protocol.

## Initial bindings

| Binding | Role | Status |
| --- | --- | --- |
| `GXP/TCP` | Native persistent duplex session over TCP + TLS 1.3 | First implementation target |
| `GXP/QUIC` | Native streams/datagrams over QUIC | Design target; deferred |
| MQTT bridge | Maps external MQTT messages to a GXP/1 session/server | Compatibility path; not canonical |
| HTTP bridge | Maps request/response ingest to GXP/1 server semantics | Compatibility path; not canonical |

TLS 1.3 provides peer authentication, negotiated cryptography, and protected
application traffic. Commands and other non-idempotent operations MUST NOT use
TLS 0-RTT because TLS 1.3 documents weaker replay guarantees for early data.
See [RFC 8446](https://www.rfc-editor.org/rfc/rfc8446.html).

## Session lifecycle

```text
TCP + TLS 1.3 connection
  → CLIENT_HELLO (protocol versions, device identity, profile, capabilities)
  → SERVER_HELLO (chosen version/profile, session ID, limits, server time)
  → AUTH_RESULT (accepted scopes or structured rejection)
  → RESUME (last accepted durable cursor and command cursor)
  → READY
  → EVENT / COMMAND / ACK / CREDIT / PING frames
  → CLOSE
```

Capabilities negotiate maximum frame size, supported profile versions, payload
encodings, compression policy, durable-store capacity, command set, and optional
transport features. A device cannot silently assume a server feature exists.

## Frame layer

Every GXP/1 frame has a fixed binary prefix followed by a typed header extension
and payload. All multi-byte integers use network byte order.

| Field | Size | Purpose |
| --- | ---: | --- |
| Magic | 2 bytes | `GX` protocol discriminator |
| Major version | 1 byte | Native GXP wire major version |
| Frame type | 1 byte | Control, event, acknowledgement, command, or error type |
| Flags | 2 bytes | Frame-specific options; unknown critical flags are rejected |
| Header length | 2 bytes | Typed extension length; bounded by negotiated maximum |
| Payload length | 4 bytes | Payload length; receiver rejects frames above negotiated maximum |
| Session ID | 8 bytes | Server-selected session context after handshake |
| Frame number | 8 bytes | Monotonic per-direction diagnostic/order number |

The header extension carries the metadata relevant to that frame: event ID,
device epoch, sequence, tenant/device identity, profile/schema version,
observation time, freshness budget, priority, acknowledgement range, credit,
or error code. A complete field registry and test vectors are required before
declaring the wire format frozen.

## Core frame types

| Type | Direction | Meaning |
| --- | --- | --- |
| `CLIENT_HELLO` / `SERVER_HELLO` | both | Version, capability, and profile negotiation |
| `AUTH_RESULT` | server → client | Accepted identity/scopes or structured rejection |
| `RESUME` / `RESUME_RESULT` | both | Durable event and command cursor reconciliation |
| `EVENT` | both | Telemetry, health, durable operational event, or bulk chunk |
| `ACK` | both | Explicit application-level acknowledgement ranges and result codes |
| `COMMAND` | server → device | Expiring, authorised request with command ID and parameters |
| `COMMAND_RESULT` | device → server | Received, validated, executing, succeeded, failed, rejected, or expired |
| `CREDIT` | both | Flow-control allowance by delivery class/stream |
| `PING` / `PONG` | both | Liveness and round-trip observation |
| `ERROR` / `CLOSE` | both | Typed protocol failure and controlled session termination |

## Delivery model

GXP/1 delivery classes remain part of the native protocol, not QoS aliases:

- `LIVE_EPHEMERAL`: newest useful state wins; stale observations never update
  live state.
- `DURABLE_EVENT`: persist before send; retain until GXP/1 ingestion ACK or a
  profile-defined terminal result.
- `COMMAND`: expiry, target, authorization, operation policy, replay defence,
  and lifecycle result are required.
- `BULK`: resumable, integrity-checked chunks with bounded flow control.
- `HEARTBEAT`: compact liveness and health data with lower priority.

An `ACK` means a specific GXP/1 result—not merely that bytes reached a socket.
The server returns application-level acceptance, duplicate, rejection, or error
codes after durable processing at the declared acknowledgement boundary.

## Ordering, replay, and flow control

- Every event has a globally unique event ID plus `(device, boot epoch,
  sequence)` ordering metadata.
- The durable replay cursor advances only after the required `ACK` result.
- A duplicate event ID is successful and idempotent; a reused sequence paired
  with a different ID is a conflict.
- Credit frames bound outstanding data so a small device or a congested server
  can apply backpressure without dropping critical events.
- Priority scheduling reserves a path for fresh live state while durable backlog
  is replayed.

## Payload encoding

The current JSON envelope remains a readable bridge and test representation.
GXP/1's native encoding choice is intentionally **not frozen** until the project
compares canonical JSON, CBOR, and a compact embedded profile against actual
Uno R4/gateway memory, bandwidth, CPU, and interoperability measurements.

The native frame/session semantics are independent of payload encoding. A future
encoding decision must have a field registry, canonicalization rules, conformance
vectors, and a migration policy.

## GXP-M/1 micro profile

GXP-M/1 is the constrained-device profile for boards such as the UNO R4 WiFi.
It has a bounded frame size, a restricted capability set, static profile IDs,
and minimal frame types: hello, event, ACK, command, command-result, ping/pong,
and error. It requires a gateway when the board cannot safely provide durable
storage, certificate handling, or the application profile's full replay policy.

## Required evidence before a GXP/1 release

1. Multiple independent client/server implementations.
2. Binary-wire test vectors, fuzzing corpus, and conformance suite.
3. TLS/mTLS, authorization, replay, parser, and denial-of-service security
   review.
4. Hardware tests on constrained devices, gateways, and real networks.
5. Fair baseline comparisons against configured MQTT, HTTP, and (where relevant)
   QUIC.
6. Documented version governance, licence, and public security disclosure path.

