# GXP architecture

GXP separates generic protocol semantics from application profiles and
transports:

```text
device/sensor -> normalizer -> envelope -> durable edge spool -> adapter
                                                          |             |
                                              retry/replay/priority  HTTP/TLS, MQTT 5/TLS
                                                                        |
                                                                authenticated ingestion
                                                                        |
                                       validation -> dedupe/history -> freshness gate -> live state
```

The BusRoot profile supplies `vehicle.position`. A generic core keeps the same
identity, time, delivery, quality, and schema semantics available to other
industrial applications.

The current reference implementation is deliberately a single-process,
SQLite-backed design. It demonstrates the correctness boundary, not a
multi-region production topology. The
[Phase 0 architecture review](docs/research/phase-0-architecture-review.md) and
[ADRs](ARCHITECTURE_DECISIONS.md) document the rationale and deferred work.

