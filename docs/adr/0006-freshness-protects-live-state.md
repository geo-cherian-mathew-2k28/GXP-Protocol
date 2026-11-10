# ADR-0006: Freshness and source time protect live state

- **Status:** accepted
- **Context:** An offline bus can replay many old points after reconnecting.
  Arrival time must not make historical data appear live.
- **Decision:** The server supplies `received_at`. It evaluates `observed_at`,
  delivery maximum age, clock policy, quality, and ordering before altering live
  state. Historical event storage remains separate.
- **Consequences:** A successfully ingested event may intentionally leave live
  state unchanged. APIs must expose freshness/staleness instead of equating
  receipt with current location.

