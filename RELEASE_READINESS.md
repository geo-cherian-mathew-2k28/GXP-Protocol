# Release readiness

## Verdict

**Not ready for a public production release or standards submission.** The
repository is ready for isolated technical evaluation of a narrow reference
slice.

## Present evidence

- Architecture review, ADRs, draft specification, schema, threat model, and
  human-action checklist exist.
- Local Python suite: 14 tests passed on 10 November 2026.
- The test suite covers envelope validation, offline-retry mechanics, dedupe,
  sequence conflict, stale-live-state prevention, command expiry, and local HTTP
  credential rejection.

## Release blockers

- Owner-selected licence, naming/trademark/domain decisions, and URI status.
- Production identity/enrolment, mTLS, authorisation, rotation, revocation,
  secrets, audit, rate limit, and independent security review.
- Production persistence/scaling/recovery/monitoring, backup/restore, and
  incident response.
- MQTT broker, TLS/mTLS, QUIC, Sparkplug, OPC UA, and independent implementation
  testing where claimed.
- Real GPS/cellular/power/hardware and fleet/operator/privacy validation.
- Fair measured benchmark campaign and public contribution/governance process.

See `KNOWN_LIMITATIONS.md`, `HUMAN_ACTION_REQUIRED.md`, and `TEST_RESULTS.md`
for current evidence and remediation direction.

