# Installation and local development

## Requirements

- Python 3.11 or later.
- No mandatory external Python packages for the HTTP reference path.
- Optional: `paho-mqtt` for the MQTT 5 adapter, installed with
  `py -3 -m pip install -e ".[mqtt]"` in your own development environment.

## Validate the checkout

```powershell
py -3 -m unittest discover -s tests -v
```

The project deliberately uses `unittest` for its required test path so that a
test runner dependency does not disguise a missing environment capability.

## Start an isolated demonstrator

```powershell
py -3 -m gxp.cli bootstrap-device --db .\server.db --tenant busroot-kerala --device bus-104-gps
py -3 -m gxp.cli server --db .\server.db --host 127.0.0.1 --port 8080
```

Copy the one-time token only into a protected local environment variable or
secret store. The default binding is loopback by design.

To serve TLS, provide a certificate and key issued for your local test endpoint:

```powershell
py -3 -m gxp.cli server --db .\server.db --host 127.0.0.1 --port 8443 --certfile .\cert.pem --keyfile .\key.pem
```

Do not use self-signed or development credentials for a real fleet. Production
device enrolment, mTLS, authorization, rotation, revocation, monitoring, and
backup/recovery require the unresolved decisions listed in
`HUMAN_ACTION_REQUIRED.md`.

