# Known limitations

- GXP 0.1 is experimental. No compatibility, operational, security, or
  performance claim should be inferred from the reference code alone.
- The default server is a loopback development server. It uses per-device bearer
  credentials and can use HTTPS client settings, but it is **not** a complete
  production mTLS provisioning or authorization solution.
- SQLite is suitable for the reference agent and local demonstrator only. A
  horizontally scaled server needs a production database and coordination
  strategy.
- The optional MQTT adapter is not exercised against a broker in this workspace.
- QUIC, Sparkplug and OPC UA bridges are deliberately deferred rather than
  simulated or claimed.
- The `gxp` URI scheme is unregistered and may conflict with an existing name;
  it must not be presented as registered or standards-track.
- No physical GPS, cellular, secure-element, power-loss, carrier handover,
  battery, or bus field tests have run.
- No benchmark result has been generated. Benchmark scripts/report placeholders
  must report `NOT RUN` until an equivalent test environment is available.
- A licence has not been selected by the owner; this repository is not yet an
  open-source release.

