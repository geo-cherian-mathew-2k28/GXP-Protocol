# ADR-0009: GXP/1 is a native framed application protocol

- **Status:** accepted
- **Context:** GXP must be more than a renamed MQTT payload convention if it is
  to provide a distinct, independently implementable protocol. MQTT and HTTP do
  not define GXP's target semantics for capability negotiation, application
  resume, acknowledgement ranges, command lifecycle, freshness, priority, and
  profile selection as one coherent wire contract.
- **Decision:** Define GXP/1 as a native binary-framed application protocol with
  its own handshake, frame types, capability negotiation, message identity,
  acknowledgement, replay cursor, credit-based flow control, and error model.
  The initial secure binding is GXP/TCP over TLS 1.3. MQTT and HTTP are optional
  bridges for migration and ecosystem integration; they are not the canonical
  wire protocol. A GXP/QUIC binding is deferred until implementation and field
  evidence exist.
- **Consequences:** GXP gains a real protocol boundary and can receive native
  embedded, gateway, and server implementations. It also assumes substantial
  specification, test, security, interoperability, and performance work. GXP
  will not invent cryptography, TLS, congestion control, IP, or cellular
  networking. Claims of superiority remain unproven until fair benchmarks and
  independent deployments exist.

