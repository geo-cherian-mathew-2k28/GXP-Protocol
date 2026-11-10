# GXP versioning policy

GXP has distinct protocol and implementation versions.

- The envelope `gxp` value is the wire-protocol version.
- `event.schema_version` versions a payload/profile independently of the common
  envelope.
- The Python package follows semantic-version-style prerelease labels but does
  not determine interoperable wire compatibility by itself.

For a `0.x` experimental protocol, compatibility is intentionally conservative:

- Add optional fields only in a compatible minor revision.
- Never silently change an existing field's type, unit, or meaning.
- Publish deprecation/migration notes before dropping a field.
- Add fixtures for each supported version and require independent validation
  before declaring a stable protocol release.

