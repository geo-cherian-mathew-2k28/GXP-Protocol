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

## 10 November 2026 — local demonstrations

The offline/replay example was run with:

```powershell
py -3 examples/simulate_busroot.py
```

Observed result: two events remained queued during a simulated outage; both
received ingestion acknowledgements after recovery; a third delayed event was
accepted into history but did not replace the recovered live state.

The narrow in-process harness was run with:

```powershell
py -3 benchmarks/ingest_benchmark.py --events 50
```

It measured the Python/SQLite local ingestion call only: p50 13.685 ms, p95
17.751 ms, p99 22.649 ms, mean 13.852 ms. This is **not** an end-to-end,
network, MQTT, HTTPS, broker, carrier, hardware, or comparative benchmark. It
must not be reused as a performance claim.

