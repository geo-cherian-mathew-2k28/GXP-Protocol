# ADR-0003: SQLite/WAL is the reference persistence layer

- **Status:** accepted
- **Context:** The edge agent needs crash-resilient local durability without a
  broker or additional service. The initial server is a single-node demonstrator.
- **Decision:** Use SQLite with WAL mode and explicit transactions for the edge
  outbox and reference ingestion store.
- **Consequences:** A transaction defines the ingestion acknowledgement
  durability boundary. Production horizontal scale requires a different,
  deployment-specific persistence and coordination design.

