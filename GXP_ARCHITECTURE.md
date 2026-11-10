# GXP architecture

GXP separates generic protocol semantics from application profiles and
transports. Its canonical direction is native GXP/1 framed sessions over
GXP/TCP/TLS; HTTP and MQTT are compatibility bridges:

```text
device/sensor -> GXP-M/1 or GXP/1 client -> durable edge spool -> GXP/TCP/TLS
                                            |                       |
                                 retry/replay/priority         native GXP ingress
                                                                            |
                                           validation -> dedupe/history -> freshness gate -> live state
```

The BusRoot profile supplies `vehicle.position`. A generic core keeps the same
identity, time, delivery, quality, and schema semantics available to other
industrial applications.

The native frame codec is implemented and tested, but a native TLS session
listener/client and embedded client remain future work. The current HTTP/JSON
reference is a compatibility bridge and a single-process, SQLite-backed design.
It demonstrates a correctness boundary, not a multi-region production topology. The
[Phase 0 architecture review](docs/research/phase-0-architecture-review.md) and
[ADRs](ARCHITECTURE_DECISIONS.md) document the rationale and deferred work.

