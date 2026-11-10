# GXP developer guide

## Run tests

```powershell
py -3 -m unittest discover -s tests -v
```

## Run the offline/replay demonstrator

```powershell
py -3 examples/simulate_busroot.py
```

It simulates an outage, preserves queued event IDs, recovers the fresh live
position after reconnect, and proves a late historical point cannot overwrite
it.

## Run a local HTTP path

```powershell
py -3 -m gxp.cli bootstrap-device --db .\server.db --tenant busroot-kerala --device bus-104-gps
py -3 -m gxp.cli server --db .\server.db --host 127.0.0.1 --port 8080
```

Store the bootstrap token as a secret. Do not commit it. Read the protocol and
security documents before building another implementation.

## Implement another language binding

Use `schemas/gxp-envelope-0.1.schema.json` plus the documents in
`specification/`. Match the conformance requirements before integrating a new
transport or profile. The Python internals are illustrative, not normative.

