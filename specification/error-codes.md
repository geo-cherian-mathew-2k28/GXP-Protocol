# GXP 0.1 error codes

| Code | Meaning | HTTP mapping |
| --- | --- | --- |
| `GXP_MALFORMED_MESSAGE` | JSON or envelope has invalid structure/type. | 400 |
| `GXP_UNSUPPORTED_VERSION` | `gxp` version is not supported. | 400 |
| `GXP_INVALID_TIMESTAMP` | A required timestamp is absent, malformed, or has no timezone. | 400 |
| `GXP_INVALID_POSITION` | BusRoot position fails bounds/fix/profile validation. | 400 |
| `GXP_FUTURE_EVENT` | Source time exceeds allowed future skew. | 400 |
| `GXP_COMMAND_EXPIRED` | Command expiry has passed. | 400 |
| `GXP_COMMAND_FORBIDDEN` | Operation is not allowed by the reference profile. | 403 |
| `GXP_UNAUTHENTICATED` | Credential missing or invalid. | 401 |
| `GXP_IDENTITY_MISMATCH` | Authenticated identity differs from envelope identity. | 403 |
| `GXP_SEQUENCE_CONFLICT` | Same device/boot/sequence has another event ID. | 409 |
| `GXP_STORAGE_EXHAUSTED` | Edge spool cannot preserve a new event under policy. | local error |
| `GXP_INTERNAL` | Unexpected server failure. | 500 |

Structured errors contain `code`, `message`, and optional `details`. They MUST
NOT disclose credentials, internal paths, or raw stack traces.

