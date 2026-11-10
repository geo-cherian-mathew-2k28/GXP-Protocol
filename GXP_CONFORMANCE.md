# GXP conformance requirements — draft 0.1

An implementation may claim only the exact profile it has tested. A future
public conformance process needs independent implementations and governance;
the current suite is a reference-quality starting point.

## Core envelope conformance

An implementation must:

1. Validate all required envelope fields, types, version, UUIDs, tenant syntax,
   positive sequence, content type, timestamps, delivery class, and quality.
2. Reject unsupported versions, malformed values, invalid coordinates, future
   source timestamps beyond policy, and missing live expiry.
3. Preserve source `observed_at`, event ID, boot ID, and sequence through replay.

## Ingestion conformance

1. Treat a repeated `(tenant, device, event_id)` as a successful duplicate.
2. Reject a distinct event ID reusing the same `(tenant, device, boot_id,
   sequence)`.
3. Persist the dedupe record and history before an ingestion acknowledgement.
4. Never allow stale, invalid, or out-of-order live position data to replace a
   newer eligible live state.

## Edge conformance

1. Persist durable events before sending them.
2. Retain them across retryable transport failure.
3. Delete them only after a GXP ingestion acknowledgement or a duplicate result.
4. Never silently evict durable events under storage pressure.

## Current evidence

The `tests/` suite exercises these behaviors and a valid JSON fixture. Run:

```powershell
py -3 -m unittest discover -s tests -v
```

This is not yet independent interoperability certification.

