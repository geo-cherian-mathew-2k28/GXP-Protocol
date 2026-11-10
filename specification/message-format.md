# GXP 0.1 JSON message format

## Encoding

Messages are UTF-8 JSON objects. This document and
`schemas/gxp-envelope-0.1.schema.json` define the envelope; application profiles
define the payload. Unknown optional fields MAY be retained but MUST NOT change
the meaning of known fields.

## Envelope

```json
{
  "gxp": "0.1",
  "kind": "telemetry",
  "tenant": "busroot-kerala",
  "device": {
    "id": "bus-104-gps",
    "boot_id": "ad2d0888-a916-4c6f-b41a-f1a85ce5530d",
    "sequence": 18293
  },
  "event": {
    "id": "a4b6b6bc-65e2-47dd-9747-b67d8836cb48",
    "type": "vehicle.position",
    "schema": "gxp.busroot.position",
    "schema_version": 1,
    "content_type": "application/json"
  },
  "time": {
    "observed_at": "2026-11-10T12:30:05.250Z",
    "sent_at": "2026-11-10T12:30:05.400Z",
    "clock_quality": "gnss"
  },
  "delivery": {
    "class": "LIVE_EPHEMERAL",
    "max_age_ms": 15000,
    "priority": 3
  },
  "quality": { "status": "valid", "position_accuracy_m": 5.0 },
  "payload": {
    "latitude": 9.5661,
    "longitude": 76.7874,
    "speed_kmh": 32.4,
    "heading_deg": 87.0,
    "gps_fix": true
  }
}
```

## Required fields and constraints

| Field | Requirement |
| --- | --- |
| `gxp` | Exactly `"0.1"`. |
| `kind` | Registered string. |
| `tenant` | Non-empty ASCII-like opaque identifier, 1–128 characters. |
| `device.id` | Non-empty opaque identifier, 1–128 characters. |
| `device.boot_id`, `event.id` | UUID strings. |
| `device.sequence` | Integer ≥ 1. |
| `event.type`, `event.schema` | Non-empty profile identifiers. |
| `event.schema_version` | Integer ≥ 1. |
| `event.content_type` | `application/json` in v0.1. |
| `time.observed_at` | RFC 3339/ISO-8601 instant with timezone. |
| `time.clock_quality` | `gnss`, `network`, `estimated`, or `unknown`. |
| `delivery.class` | Registered delivery class. |
| `delivery.priority` | Integer 0–9; 9 is highest. |
| `delivery.max_age_ms` | Optional integer ≥ 0. Required for `LIVE_EPHEMERAL`. |
| `quality.status` | `valid`, `degraded`, `invalid`, or `estimated`. |
| `payload` | JSON object defined by the selected schema/profile. |

## BusRoot `vehicle.position` profile

This profile uses WGS 84 decimal degrees.

| Payload field | Constraint |
| --- | --- |
| `latitude` | number from -90 through 90 |
| `longitude` | number from -180 through 180 |
| `gps_fix` | boolean; MUST be true before a live-state update |
| `speed_kmh` | optional number ≥ 0 and ≤ 500 |
| `heading_deg` | optional number 0 through < 360 |
| `altitude_m` | optional number |
| `route_id` | optional, non-authoritative annotation |

The server records a history event even when a position is too old or invalid
for live state, subject to authentication and envelope validation. Provisioning,
not an untrusted payload, associates a device with a vehicle/route for operator
use.

## Commands

A `kind: "command"` envelope must additionally contain these `payload` fields:

```json
{
  "command_id": "b72cfa75-8fe4-49b5-ad6f-1d1315522ece",
  "issuer": "operator:alice",
  "operation": "diagnostics.snapshot",
  "expires_at": "2026-11-10T12:35:00Z",
  "parameters": {}
}
```

`command_id` MUST be globally unique per target. A device MUST reject a command
that is expired, replayed, outside its locally configured capability policy, or
unauthorized. GXP does not authorise vehicle motion-control operations.

