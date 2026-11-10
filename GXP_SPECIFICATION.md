# GXP specification — draft 0.1

**Status:** experimental technical draft. This is an entry point to the
normative draft set; it does not claim standards-body approval.

GXP is a transport-independent application protocol for operational events and
safe device commands. Its core contribution is a consistent envelope and
delivery contract above mature transports. It is not a replacement for IP, TLS,
MQTT, HTTP, QUIC, Sparkplug, or OPC UA.

Read the draft in this order:

1. [Protocol overview](specification/protocol-overview.md)
2. [Message format](specification/message-format.md) and
   [JSON Schema](schemas/gxp-envelope-0.1.schema.json)
3. [Delivery semantics](specification/delivery-semantics.md)
4. [Transport mappings](specification/transport-mappings.md)
5. [Error codes](specification/error-codes.md)
6. [Versioning](specification/versioning.md)

The protocol's current assurance boundary is clear: at-least-once transfer plus
transactionally idempotent ingestion; no claim of exactly-once business effects
or hard real-time public-cellular delivery.

