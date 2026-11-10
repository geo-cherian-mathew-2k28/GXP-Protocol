# GXP protocol overview — draft 0.1

## Status and terminology

This is an experimental draft, not an Internet Standard or a registered URI
scheme. The keywords **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and
**MAY** are used as described by RFC 2119.

GXP is an application-layer event protocol. It defines the meaning of an event
independently of whether an adapter carries it through HTTP/TLS, MQTT 5/TLS, or
a later transport profile.

## Goals

- Preserve original observation time and identity through offline replay.
- Make delivery intent, freshness, and acknowledgement meaning explicit.
- Support at-least-once transfer with idempotent ingestion.
- Prevent delayed live telemetry from overwriting newer live state.
- Make safe command acceptance a lifecycle, not mere message arrival.

## Non-goals

GXP does not replace IP, TCP, UDP, TLS, QUIC, MQTT, Sparkplug, or OPC UA. It
does not guarantee hard real-time delivery, exactly-once business effects, or
safety-critical physical control.

## Versioning

Every envelope contains `gxp: "0.1"`. A receiver MUST reject unsupported major
versions with `GXP_UNSUPPORTED_VERSION`. A compatible minor version may add only
optional fields and MUST NOT alter existing-field semantics. Software package
versions are separate from wire versions.

## Canonical identity

An event is identified by `(tenant, device.id, event.id)`. `event.id` MUST be a
globally unique UUID string produced before local persistence. UUIDv4 is used by
the reference implementation; conforming implementations may use another UUID
variant with equivalent global uniqueness.

`device.boot_id` identifies the producing agent incarnation. `device.sequence`
MUST be a positive integer that strictly increases within `(tenant, device.id,
boot_id)`. A sequence helps detect gaps/reordering; it is not a dedupe key.

## Time

- `time.observed_at` is when the measurement or event happened.
- `time.sent_at`, when present, is when the sender attempted transmission.
- `received_at` is assigned only by the server in stored event metadata and
  acknowledgements. A receiver MUST NOT trust a device-supplied value.
- `time.clock_quality` expresses confidence in source time; it does not turn an
  untrusted clock into server time.

## Kinds

`telemetry`, `event`, `command`, `command_ack`, `capability`, and `health` are
the registered 0.1 kinds. Profiles may define event-type namespaces but MUST NOT
repurpose the envelope fields.

## Acknowledgement levels

1. **Transport acknowledgement:** the transport accepted bytes/message under
   its own specification.
2. **Ingestion acknowledgement:** GXP authenticated, validated, deduplicated,
   and durably committed the event transaction.
3. **Business acknowledgement:** the target business process or device action
   completed its explicit work.

The HTTP 0.1 response is an ingestion acknowledgement. An edge agent MUST keep
a durable event until the required acknowledgement level is reached. A duplicate
ingestion response is success because the original event is already committed.

