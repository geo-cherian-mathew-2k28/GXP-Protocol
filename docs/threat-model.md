# Threat model — experimental GXP 0.1

## Assets

- Device credentials and private keys.
- Truthfulness, ordering, and freshness of telemetry.
- Command authority and audit trail.
- Edge spool availability and confidentiality.
- Tenant separation, location history, and live-state APIs.

## Trust boundaries

1. Sensor/GNSS data enters the device agent and can be faulty or spoofed.
2. The device agent persists data locally before it crosses a hostile network.
3. The transport terminates at authenticated GXP ingestion.
4. Ingestion supplies server receipt time and applies policy before updating
   state used by operators or passenger services.
5. Public passenger APIs and privileged operations are distinct future surfaces,
   not part of the development server.

## Primary threats and controls

| Threat | Current control | Required before production |
| --- | --- | --- |
| Network interception/tampering | HTTPS client support; no plaintext deployment recommendation | Mandatory TLS policy, mTLS, certificate pinning/lifecycle where appropriate |
| Stolen/replayed telemetry | Event-ID dedupe, sequence conflict checks, freshness gate | Device revocation, protected keys, anomaly detection |
| Replayed command | Durable command ID and expiry validation | Signed commands where risk requires, device-side persistent replay store |
| Unauthorized publishing | Per-device bearer credential in development profile | mTLS/equivalent identity, least privilege, tenant/device authorization |
| Credential disclosure | Token hashes in registry; token printed only once | Secret manager, secure element/TPM, rotation and revocation process |
| Local spool theft/tampering | File access is an operating-system responsibility | Encrypted storage/key protection, signed software, tamper response |
| Queue exhaustion | Size quota and live-only eviction | Capacity planning, monitoring, alerting, tested recovery playbook |
| Bad GNSS/clock data | Coordinate validation, quality/status, freshness/future-skew checks | GNSS spoofing detection and calibrated time uncertainty |
| Denial of service | Loopback default | Network perimeter, TLS termination, rate limits, resource quotas, WAF/broker policy |
| Privacy breach | No public deployment claim | Retention policy, access control, audit, DPIA/legal review |

## Security assertions deliberately not made

- The development bearer-token profile is not represented as a production device
  PKI.
- No secure element, certificate authority, revocation service, firmware signing,
  operator IAM, rate limiter, or penetration test has been implemented.
- No command causes safety-critical physical control.

