# ADR-0005: Transfer is at-least-once; ingestion is idempotent

- **Status:** accepted
- **Context:** A sender can lose an acknowledgement after the receiver commits.
  Network retries therefore produce duplicate deliveries.
- **Decision:** A durable event is retained until a GXP ingestion acknowledgement.
  Ingestion transactionally records `(tenant, device_id, event_id)` and returns
  a duplicate acknowledgement for replay. Downstream operations must use event
  IDs/idempotency keys too.
- **Consequences:** The protocol does not claim exactly-once business effects.
  It supplies a robust boundary on which applications can build them.

