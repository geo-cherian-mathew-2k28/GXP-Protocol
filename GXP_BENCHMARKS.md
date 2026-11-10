# GXP benchmark methodology and results

## Result status

**No comparative benchmark results have been published.** No performance or
reliability superiority claim is made.

One narrow local-harness run completed on 10 November 2026: 50 in-process
Python/SQLite ingestions measured p50 13.685 ms, p95 17.751 ms, p99 22.649 ms,
and mean 13.852 ms. This excludes networking, TLS, MQTT, a broker, GPS, and
cellular behavior, and must not be compared to another system or used as a
protocol performance claim.

## Local harness

`benchmarks/ingest_benchmark.py` performs only a local, in-process SQLite
ingestion measurement and labels its narrow scope in its JSON output.

```powershell
py -3 benchmarks/ingest_benchmark.py --events 1000
```

## Required comparative methodology

Use the same hardware, payload, device rate, storage policy, backend resources,
carrier/SIM, network route/conditions, test duration, and fault scripts to
compare MQTT 5, MQTT/Sparkplug where relevant, plain HTTPS, and GXP over each
implemented transport. Capture latency percentiles, loss, duplication, useful
freshness, recovery, bandwidth, resource use, and power where hardware permits.
Retain raw outputs and configuration. See [benchmarks/README.md](benchmarks/README.md).

