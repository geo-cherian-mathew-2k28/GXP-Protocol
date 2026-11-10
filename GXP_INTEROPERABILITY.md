# GXP interoperability

GXP 0.1 is designed so another implementation can create and validate the JSON
envelope without importing this Python package. The schema and specification are
the source of truth.

| Integration | Status | Evidence / limitation |
| --- | --- | --- |
| HTTP/JSON | Reference implemented | Local authenticated integration test. Production TLS/mTLS deployment is not tested. |
| MQTT 5 | Optional publish adapter | Requires `paho-mqtt`; no broker or response-topic ingestion-ack test has run. |
| Sparkplug | Mapping planned | No bridge implemented. |
| OPC UA PubSub | Mapping planned | No bridge implemented. |
| QUIC | Deferred | No adapter or carrier test. |
| Independent implementation | Required before public beta | Not yet available. |

An adapter is only compatible when it preserves canonical identity, source time,
sequence, delivery intent, schema version, and acknowledgement meaning.

