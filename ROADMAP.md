# Roadmap

## 0.1 Experimental reference

- Freeze the draft envelope and delivery semantics.
- Ship the BusRoot simulator, edge spool, ingestion path, HTTP mapping, optional
  MQTT mapping, conformance fixtures, and fault-oriented tests.

## 0.2 Pilot hardening

- Define and implement production device enrollment, mTLS, certificate rotation,
  revocation, tenant/operator authorization, audit export, rate limiting, and
  metrics.
- Test MQTT 5 against a configured broker and move server persistence to a
  production datastore as pilot scale requires.

## 0.3 Interoperability and field evidence

- Add Sparkplug and OPC UA mappings only after their required profile semantics
  are specified.
- Conduct controlled network/power/cellular tests and fair MQTT/HTTPS baselines.
- Invite an independent implementation and run the conformance suite.

## Later

- Evaluate a QUIC profile against carrier and middlebox compatibility evidence.
- Consider binary encodings only after measured JSON and CPU/bandwidth evidence.
- Prepare public-release and standards materials only with owner approval.

