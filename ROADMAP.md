# Roadmap

## 0.1 Native protocol foundation

- Freeze GXP/1 native frame/session architecture and GXP-M/1 constrained profile.
- Implement frame codec, parser, session state machine, field registry, binary
  test vectors, and fuzzing corpus.
- Preserve the JSON/HTTP core and MQTT adapter only as compatibility bridges.

## 0.2 Native runtime and embedded pilot

- Build GXP/TCP/TLS client/server session support, application ACK/resume,
  credit flow control, and production persistence.
- Build and test GXP-M/1 on a constrained board and validate memory, reconnection,
  power-loss, command replay, and actuator-safety behavior.

## 0.3 Security, bridges, and field evidence

- Add production enrolment, mTLS, certificate rotation, revocation,
  tenant/operator authorization, audit export, rate limiting, and metrics.
- Test MQTT/HTTP bridges and add Sparkplug/OPC UA mappings only after their
  required semantics are specified.
- Conduct controlled network/power/cellular tests and fair native-GXP/MQTT/HTTP
  baselines.
- Invite an independent implementation and run the conformance suite.

## Later

- Evaluate a GXP/QUIC binding against carrier and middlebox compatibility
  evidence.
- Freeze a native payload encoding only after embedded CPU/bandwidth and
  interoperability evidence.
- Prepare public-release and standards materials only with owner approval.

