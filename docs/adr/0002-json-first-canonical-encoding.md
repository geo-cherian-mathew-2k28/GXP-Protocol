# ADR-0002: JSON/UTF-8 is the initial canonical encoding

- **Status:** accepted
- **Context:** The first profile must be debuggable, reviewable, portable, and
  suitable for an early BusRoot pilot. Binary encodings have value only after
  real bandwidth/CPU/storage measurements identify a problem.
- **Decision:** GXP 0.1 messages use UTF-8 JSON, with exact envelope fields and
  a JSON Schema. A future encoding must preserve the canonical semantics and
  receive its own versioned mapping.
- **Consequences:** Initial messages are larger than CBOR/Protobuf alternatives.
  This is measured rather than guessed; it is not a reason to silently change
  the wire protocol.

