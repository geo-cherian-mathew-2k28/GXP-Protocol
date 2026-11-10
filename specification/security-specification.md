# GXP 0.1 security specification

## Security model

1. A device has a unique identity bound to a tenant and credentials.
2. The transport encrypts and authenticates the server; production deployments
   should use mTLS or an equivalently strong device authentication design.
3. Authorisation is device-scoped: a device may publish only as itself and only
   allowed event kinds/types.
4. Ingestion checks identity before accepting data and records server receipt
   time independently from device time.
5. Commands are more restrictive: expiry, target, issuer, operation allowlist,
   authorization, and durable replay protection all apply.

## Reference development profile

The demonstrator stores a SHA-256 digest of an independently generated 256-bit
or stronger device bearer token and compares it using constant-time comparison.
The raw token is printed once when the device is bootstrapped. It MUST be sent
only over TLS outside loopback testing, held in a secret store, and rotated by
re-enrolment.

This profile demonstrates tenant/device binding and unauthenticated-request
rejection. It is not a full production PKI, certificate rotation, revocation,
rate-limit, audit-export, or operator IAM system.

## Production requirements before a pilot

- Mutual device authentication and validated TLS configuration.
- Protected private-key storage, unique device credentials, rotation,
  revocation, and decommissioning procedures.
- Device/tenant/operation authorization and separate operator identities.
- Rate limits, resource quotas, structured audit events, and alerting.
- Encrypted/protected edge storage appropriate to hardware threat model.
- Secure configuration/firmware integrity and incident-response procedures.
- Privacy, retention, access, and disclosure controls for location data.

## Prohibited use

The BusRoot profile MUST NOT operate steering, braking, propulsion, or any
safety-critical vehicle function. Local device validation remains mandatory even
after a command is accepted by a server.

