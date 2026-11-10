# Smart-feeder native GXP profile — integration draft

## Purpose

This profile applies the future native GXP/1 protocol to a connected cat-food
dispenser. The feeder controls a motor/auger, measures or estimates portions,
reports food/device state, and accepts tightly constrained remote commands.

GXP/1 is designed to become the feeder's protocol, not an MQTT wrapper. MQTT
remains only as a temporary migration bridge until the native embedded client,
server listener, and conformance tests exist.

## Hardware boundary

This guide assumes an **Arduino UNO R4 WiFi**, not an UNO R4 Minima. The WiFi
board combines the RA4M1 application MCU with an ESP32-S3 connectivity module
and ships the `WiFiS3` library in its board package. The Minima has no onboard
Wi-Fi; it needs Ethernet, cellular, or another networking gateway before it can
reach a GXP/TCP endpoint. See the official [UNO R4 WiFi documentation](https://docs.arduino.cc/hardware/uno-r4-wifi/)
and [UNO R4 Minima documentation](https://docs.arduino.cc/hardware/uno-r4-minima/).

The Uno R4's 32 KB of RA4M1 SRAM requires a bounded microcontroller profile.
GXP-M/1 therefore uses limited frame sizes and feature negotiation. It should
delegate durable queueing, certificate operations, or complex history handling
to a gateway when the hardware cannot reliably provide them.

## Target architecture: native GXP, no MQTT broker required

```text
UNO R4 WiFi + feeder sensors/motor
  └─ GXP-M/1 client
       ├─ GXP/1 session handshake
       ├─ EVENT / ACK / COMMAND / COMMAND_RESULT frames
       └─ bounded local command/event journal
                │
                ▼
         TCP + TLS 1.3
                │
                ▼
        Native GXP/1 server
         ├─ identity and capability negotiation
         ├─ durable event/command processing
         ├─ live device state and history
         └─ app/API integration
                │
                ▼
 mobile app, schedule service, inventory alerts, operations dashboard
```

This removes the MQTT topic/broker dependency from the canonical device path.
It does **not** replace TCP, TLS, or Internet routing. The native protocol owns
the session and message behavior above TLS.

## Temporary migration path from MQTT

| Stage | Device connection | Purpose |
| --- | --- | --- |
| 1. Compatibility | Existing MQTT client → MQTT/GXP bridge | Preserve your working dispenser while normalising IDs, delivery classes, and command lifecycle. |
| 2. Native pilot | GXP-M/1 client → GXP/TCP/TLS server | Validate custom frames, session resume, ACKs, commands, and memory limits on real hardware. |
| 3. Native product profile | GXP-M/1 as standard firmware behavior | MQTT becomes optional integration for existing dashboards/brokers, not a feeder requirement. |

Do not remove MQTT from a working food dispenser until the native GXP-M/1 path
has passed power-loss, Wi-Fi-loss, duplicate-command, and jam tests.

## GXP-M/1 feeder capability profile

At session setup, the feeder advertises a bounded capability manifest:

```text
profile: gxp.smart-feeder/1
max_frame_bytes: 512
max_inflight_durable_events: 4
delivery_classes: HEARTBEAT, DURABLE_EVENT, COMMAND
events: feeder.status, feeder.food_level, feeder.dispense_started,
        feeder.dispense_completed, feeder.jam_detected, feeder.feed_skipped
commands: feeder.dispense, feeder.schedule.set, status.request
clock_quality: rtc | network | unknown
durable_storage: none | EEPROM-journal | gateway-required
```

The server selects only features both sides support. If durable storage or a
command capability is missing, the server must not pretend it is available.

## Feeder events

| Event type | Native GXP class | When to send | Why it matters |
| --- | --- | --- | --- |
| `feeder.status` | `HEARTBEAT` | Periodically or after meaningful state change | Shows connectivity, hopper level, schedule version, and device health. |
| `feeder.food_level` | `LIVE_EPHEMERAL` or `DURABLE_EVENT` by policy | Load-cell or level-sensor update | Current food state is useful; a low-food threshold can additionally produce a durable alert. |
| `feeder.dispense_started` | `DURABLE_EVENT` | Motor starts | Creates an audit trail for a physical action. |
| `feeder.dispense_completed` | `DURABLE_EVENT` | Portion confirmed | Records requested/actual portion, duration, and result. |
| `feeder.jam_detected` | `DURABLE_EVENT` | Motor-current, rotation, or timeout fault | Must survive a network interruption and alert the owner. |
| `feeder.feed_skipped` | `DURABLE_EVENT` | Safety policy blocks a feed | Explains why a schedule or command was rejected. |

Each native `EVENT` frame carries a globally unique event ID, device boot epoch,
monotonic sequence, source timestamp, delivery class, profile/schema ID, and
payload. The server returns an application `ACK` only after its declared durable
processing boundary.

## Remote dispensing: safety and idempotency first

`feeder.dispense` is an actuator command, not a convenience message. The native
`COMMAND` frame carries a unique command ID, target, issuer, operation,
parameters, issued time, expiry, and authorization scope. The device answers
with `COMMAND_RESULT` states such as `RECEIVED`, `VALIDATED`, `EXECUTING`,
`SUCCEEDED`, `FAILED`, `EXPIRED`, or `REJECTED`.

Before running the motor, firmware must check:

1. The command is addressed to this feeder and has not expired.
2. The command ID has not already executed; retain completed IDs in durable
   storage or let a trusted gateway perform the execution boundary.
3. The requested portion is within the locally configured maximum.
4. Daily limits and the next scheduled feed are respected.
5. Hopper/door/auger sensors do not indicate a jam, empty hopper, or unsafe
   condition.
6. Motor runtime has both a hardware and firmware timeout.

The device emits a durable completion/failure event after execution. A TLS
session, native frame acknowledgement, or network retry must never cause a
second food dispense by itself.

## Native framing implications for Uno R4 WiFi

The embedded implementation needs these components:

1. `WiFiS3` connection management.
2. A TLS-capable client socket and server certificate validation.
3. GXP-M/1 fixed-prefix parser with strict length limits and timeout handling.
4. A bounded frame encoder/decoder; no unbounded `String` allocation.
5. Session state: version, capability result, session ID, frame number, credit,
   last acknowledged event, and clock-quality state.
6. A small non-volatile journal for command replay protection and any required
   durable events, or a gateway delegation strategy.
7. A motor-control safety layer that remains valid while disconnected.

An Arduino MQTT library is not required for the native target. It remains useful
only for Stage 1 migration or external interoperability.

## Minimum validation plan

- Normal scheduled dispense and manual dispense.
- Wi-Fi unavailable before and after a dispense result.
- TCP/TLS reconnect, session resume, and native ACK loss.
- Duplicate `COMMAND` frame and duplicate network delivery.
- Arduino restart between command acceptance and motor completion.
- Malformed/oversized frame, unsupported version, and exhausted credit.
- Jam, empty hopper, inaccurate load-cell, and motor-timeout conditions.
- Expired command, over-limit portion, daily-limit rejection, and unauthorized
  device connection.

Until GXP-M/1 has a real embedded implementation and hardware tests, this is a
protocol design target—not a certified pet-care or safety system.

