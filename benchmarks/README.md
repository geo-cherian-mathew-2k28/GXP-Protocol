# Benchmark harnesses

`ingest_benchmark.py` measures one narrow thing: local in-process call latency
for the reference SQLite ingestion path. It prints its measurement scope with
the output and makes no network/protocol superiority claim.

```powershell
py -3 benchmarks/ingest_benchmark.py --events 1000
```

## Fair comparative campaign (not yet run)

To evaluate GXP, compare the following under the same payload, hardware, device
rate, carrier/SIM, route/network conditions, backend resources, and retention
configuration:

1. MQTT 5 with appropriate QoS, persistent-session, and expiry configuration.
2. MQTT 5 with Sparkplug when industrial-state semantics are relevant.
3. HTTPS telemetry/batch upload.
4. GXP carried over MQTT 5.
5. GXP carried over HTTPS.
6. GXP over QUIC only if a profile is actually implemented and carrier-tested.

Capture p50/p95/p99 latency, useful-event freshness, loss/duplicate rate,
offline recovery time, bandwidth, CPU, memory, storage, power (on hardware),
throughput, and reconnect behavior. Preserve raw data, configuration, source
code revisions, and fault-injection details. The comparative campaign is
**NOT RUN**.

