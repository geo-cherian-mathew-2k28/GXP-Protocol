# Contributing

GXP is pre-release. Contributions must prioritise interoperability, reproducible
evidence, and precise documentation over feature count.

1. Discuss semantic/wire changes before implementation and add an ADR where a
   trade-off is material.
2. Preserve backward compatibility or document a versioned migration.
3. Add automated tests and conformance fixtures for protocol behavior.
4. Run `py -3 -m unittest discover -s tests -v` before proposing a change.
5. Do not add benchmark results that were not executed or claim production
   readiness without field/security evidence.
6. Do not place credentials, device locations, private data, or secrets in the
   repository.

The project owner must select a licence before accepting external contributions
for a public release.

