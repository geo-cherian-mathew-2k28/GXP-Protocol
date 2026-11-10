# GXP deployment guide

## Local-only demonstrator

Follow [docs/installation.md](docs/installation.md) or use the Docker material
in `deployment/`. The development server binds to loopback by default.

## Production readiness gate

Before a pilot, approve a deployment architecture that includes:

- TLS/mTLS or equivalent device identity and a certificate/key lifecycle.
- Tenant/device/operator authorisation, audit logs, rate limiting, and secret
  management.
- Production database, backups, retention, recovery, scaling, monitoring, and
  incident-response runbooks.
- Protected edge storage and a hardware/sensor/cellular validation plan.
- Privacy, safety, fleet-owner, and operational approvals.

These are not boilerplate: their absence is why the reference server must not be
Internet-exposed. The detailed human tasks are in `HUMAN_ACTION_REQUIRED.md`.

