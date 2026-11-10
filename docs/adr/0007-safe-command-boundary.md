# ADR-0007: Commands are allowlisted lifecycle records

- **Status:** accepted
- **Context:** Device commands are materially more dangerous than telemetry.
- **Decision:** Commands require IDs, target/issuer identity, expiry, an
  allowlisted operation, authorization, dedupe, and lifecycle state. BusRoot
  v0.1 permits diagnostics and non-critical reporting configuration only.
- **Consequences:** No steering, braking, propulsion, or safety-critical control
  is implemented. Device-side policy is required even after cloud acceptance.

