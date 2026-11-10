# GXP transport mappings — draft 0.1

## Common contract

Every transport adapter must preserve the envelope byte content/meaning, tenant
and device identity, event ID, boot ID, sequence, source times, delivery class,
schema version, and acknowledgement level. An adapter MUST document a semantic
loss instead of silently substituting a weaker guarantee.

## HTTP/JSON over TLS

- Endpoint: `POST /v1/events`
- Content type: `application/json; charset=utf-8`
- Authentication: reference development profile uses `Authorization: Bearer
  <device-token>` over TLS. The registry binds token to tenant/device and the
  payload identity must match.
- Successful new event: `201 Created` with `{"status":"accepted", ...}`.
- Duplicate: `200 OK` with `{"status":"duplicate", ...}`.
- Validation error: `400` with a structured GXP error.
- Authentication failure: `401` or identity mismatch `403`.
- Sequence conflict: `409`.

The HTTP response is a GXP **ingestion** acknowledgement, not a business
acknowledgement. The server should be TLS-terminated with verified client
identity in production; the included server is loopback development tooling.

## MQTT 5 over TLS

The optional adapter maps an envelope JSON payload to a configured publish topic
such as `gxp/v1/<tenant>/<device>/events`. The broker's QoS acknowledgement is
only a transport acknowledgement. The deployment must provide a GXP ingestion
acknowledgement through a configured response topic/correlation scheme before an
edge agent deletes durable data.

Recommended starting mapping:

| GXP class | MQTT QoS | MQTT expiry note |
| --- | --- | --- |
| `LIVE_EPHEMERAL` | 0 or 1 by profile | Map `max_age_ms` to message expiry where supported; still enforce freshness at GXP ingestion. |
| `DURABLE_EVENT` | 1 | GXP event ID and ingestion dedupe still required because QoS 1 duplicates. |
| `COMMAND` | 1 | Command expiry and device policy remain GXP responsibilities. |

MQTT QoS 2 does not make application-side database effects globally exactly
once. The reference does not implement a broker or an MQTT response/ack channel
yet.

## QUIC

No QUIC profile is implemented. QUIC migration may improve a client transition
between usable paths, but carrier/middlebox support and endpoint configuration
are deployment facts, not protocol guarantees. Any future profile must retain
the same application-level resume/replay behavior when migration fails.

