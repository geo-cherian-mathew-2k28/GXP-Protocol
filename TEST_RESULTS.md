# Test results

## 10 November 2026 — local reference suite

Command executed:

```powershell
py -3 -m unittest discover -s tests -v
```

Result: **14 passed, 0 failed** in approximately 2 seconds.

Verified behaviors:

- Envelope and BusRoot position validation, including invalid coordinates,
  missing live expiry, future timestamps, and expired commands.
- Canonical conformance fixture validation.
- Durable edge persistence, retry after simulated transport failure, ingestion
  acknowledgement deletion, and no durable-event eviction under quota pressure.
- Transactional duplicate idempotency and sequence-conflict rejection.
- Delayed live GPS data is recorded without replacing a fresher live state.
- Authenticated HTTP ingest is acknowledged; unauthenticated ingest returns 401.

Not executed: MQTT broker tests, TLS/mTLS handshake tests, QUIC, hardware/GNSS,
cellular/power-failure tests, load/performance tests, security assessment, and
independent implementation interoperability. Passing local tests do not establish
production readiness.

