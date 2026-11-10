# ADR-0001: GXP is an application-level, event-first protocol

- **Status:** accepted
- **Context:** Creating a custom TCP/UDP/IP replacement would impose congestion,
  NAT, path-MTU, security, middlebox, and operating-system deployment work
  without addressing GXP's differentiated problems.
- **Decision:** Define a canonical application envelope and delivery semantics
  above existing secure transports. Telemetry is event-first; commands use a
  separate lifecycle.
- **Consequences:** MQTT 5 and HTTPS can carry identical GXP events. No claim is
  made that GXP replaces MQTT/QUIC/OPC UA. Independent implementations can
  adopt the envelope without adopting Python.

