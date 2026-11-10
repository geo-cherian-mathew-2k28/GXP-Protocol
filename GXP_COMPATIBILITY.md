# GXP compatibility policy

Compatibility is defined by wire version and profile schema, not by a Python
package number. `gxp: "0.1"` is the only current version.

- A receiver rejects unsupported major wire versions.
- Compatible minor changes can add optional fields but cannot alter a known
  field's type or meaning.
- Payload schemas version independently through `event.schema` and
  `event.schema_version`.
- New delivery classes, encodings, transports, or authentication profiles need
  explicit versioned mappings and conformance fixtures.
- No transport adapter may silently weaken identity, event ID, source-time,
  delivery-class, schema-version, or acknowledgement semantics.

The detailed policy is [here](specification/versioning.md).

