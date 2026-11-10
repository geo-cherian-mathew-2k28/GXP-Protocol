# GXP security architecture

Security is a protocol concern, not a future add-on. GXP requires unique device
identity, encrypted transport, least privilege, replay protection, command
expiry, local validation, and auditability.

The actual reference behavior is described in the
[security specification](specification/security-specification.md) and
[threat model](docs/threat-model.md). In brief:

- The development server authenticates a device with a unique high-entropy token
  whose digest is stored in SQLite; production use requires TLS.
- The reference can serve TLS and require a client certificate but does not
  implement the full production mTLS enrolment, authorisation, rotation,
  revocation, secure-element, audit, or rate-limit lifecycle.
- Event and command IDs, sequences, expiry, and transactional deduplication
  mitigate replay. They do not secure compromised device keys.
- Safety-critical vehicle control is prohibited.

This repository is not security-certified or approved for production exposure.

