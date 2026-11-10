# ADR-0004: Implement HTTP first, MQTT as optional, defer QUIC

- **Status:** accepted
- **Context:** HTTP/TLS is available from the Python standard library and is
  straightforward to validate end-to-end. MQTT is needed for interoperability
  but needs an external client/broker. QUIC field support cannot be assumed.
- **Decision:** Implement an HTTP/JSON transport and an optional MQTT 5 adapter.
  Keep QUIC as an evaluated future profile, not a placeholder implementation.
- **Consequences:** The first test suite validates HTTP semantics. MQTT has a
  dependency and broker test gap. No QUIC capability is advertised.

