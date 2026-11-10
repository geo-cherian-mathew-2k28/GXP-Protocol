# Architecture decisions

This is the short-form index for decision records in `docs/adr/`.

| ID | Decision | Status |
| --- | --- | --- |
| ADR-0001 | GXP is an application-level, event-first protocol. | Accepted |
| ADR-0002 | JSON/UTF-8 is the initial canonical encoding. | Accepted |
| ADR-0003 | SQLite/WAL is the reference edge and demonstrator persistence layer. | Accepted |
| ADR-0004 | HTTP/JSON is implemented first; MQTT 5 is optional; QUIC is deferred. | Accepted |
| ADR-0005 | Transfer is at-least-once; ingestion is transactionally idempotent. | Accepted |
| ADR-0006 | Live state is freshness- and source-time-aware; historical storage is separate. | Accepted |
| ADR-0007 | Commands are allowlisted, expiring, auditable lifecycle records; no vehicle control. | Accepted |
| ADR-0008 | `gxp` and project name remain provisional. | Accepted |

