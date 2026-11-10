# GXP 0.1 delivery semantics

| Class | Edge persistence | Retry/expiry behavior | Ingestion behavior |
| --- | --- | --- | --- |
| `LIVE_EPHEMERAL` | MAY be spooled for transient outage; eligible for coalescing/eviction | Newest eligible sample is preferred; stale samples do not update live state | History MAY retain it; live state only changes when fresh, valid, and newer |
| `DURABLE_EVENT` | MUST persist before sending | Retry with bounded exponential backoff and jitter until ingestion acknowledgement or explicit profile policy | Transactionally record and dedupe before acknowledgement |
| `COMMAND` | Sender persists according to command policy | Must expire; retry cannot extend expiry | Validate identity, target, allowlist, expiry, and replay before acceptance/execution |
| `BULK` | Profile-defined resumable persistence | Integrity and resumability required; not implemented in 0.1 reference | Do not treat as ordinary telemetry |
| `HEARTBEAT` | Low-priority; persistence optional | Periodic and compact | Updates liveness confidence, not data freshness |

## Edge queue behavior

1. Construct ID, sequence, and timestamps before persistence.
2. Persist a durable event before the first network attempt.
3. Schedule attempts by descending priority and next-attempt time. Fresh live
   events may be prioritised over backlogged historical samples.
4. On transient failure, use capped exponential backoff with random jitter.
5. Delete only after an ingestion acknowledgement or duplicate acknowledgement.
6. If quota is exceeded, evict only oldest unsent `LIVE_EPHEMERAL` entries.
   Never silently evict durable events. If no eligible space exists, reject the
   new write and raise an observable storage-exhaustion condition.

## Freshness calculation

For an event with `max_age_ms`, the server calculates
`received_at - observed_at <= max_age_ms`. A position with an invalid GPS fix,
an invalid quality status, excessive future clock skew, or elapsed maximum age
is not live-eligible. It may still be stored in history.

## Live-state ordering

For a given device, a live-eligible position replaces prior live state only if
its `observed_at` is strictly newer. Equal source times do not replace existing
state. Arrival order and replay time MUST NOT make a historical point current.

## Idempotency

The durable dedupe key is `(tenant, device.id, event.id)`. A repeated key is a
successful duplicate, not an error. The same `(tenant, device.id, boot_id,
sequence)` paired with another event ID is `GXP_SEQUENCE_CONFLICT`.

