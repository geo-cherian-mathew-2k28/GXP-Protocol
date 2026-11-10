# GXP URI syntax — provisional technical draft

## Status

`gxp` is a provisional identifier used only for design discussion. It is not
registered, claimed, or guaranteed available. This document is a technical draft
and is not an IANA registration request.

## Syntax

```text
gxp://authority/path[?query]
```

- `authority` identifies an administrative namespace, not necessarily a network
  host or transport endpoint.
- `path` is an opaque, slash-separated resource identifier. Recommended
  BusRoot forms include `/buses/{bus-id}/position`,
  `/devices/{device-id}/status`, and `/routes/{route-id}`.
- Query parameters are profile-defined and MUST NOT carry credentials, private
  keys, or mutable transport selection.

Examples:

```text
gxp://fleet.example/buses/bus-104/position
gxp://fleet.example/devices/bus-104-gps/status
gxp://fleet.example/routes/KTM-PON-01
```

## Semantics and security

A GXP URI identifies a logical resource. It does not dictate MQTT topic, HTTP
URL, DNS resolution, browser handling, or a network connection. A mapping from
a resource URI to a transport endpoint is deployment configuration and may be
access-controlled.

Before external use, the owner must verify the registry/name status and decide
whether registration is justified. See `HUMAN_ACTION_REQUIRED.md`.

