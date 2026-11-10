"""Typed protocol errors. Error messages are safe to return to a client."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GXPError(Exception):
    code: str
    message: str
    http_status: int = 400
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details:
            result["details"] = self.details
        return result


class MalformedMessage(GXPError):
    def __init__(self, message: str, **details: Any) -> None:
        super().__init__("GXP_MALFORMED_MESSAGE", message, 400, details)


class UnsupportedVersion(GXPError):
    def __init__(self, version: object) -> None:
        super().__init__("GXP_UNSUPPORTED_VERSION", "Unsupported GXP version.", 400, {"version": version})


class InvalidTimestamp(GXPError):
    def __init__(self, field_name: str, message: str = "Timestamp must be an RFC 3339 instant with timezone.") -> None:
        super().__init__("GXP_INVALID_TIMESTAMP", message, 400, {"field": field_name})


class InvalidPosition(GXPError):
    def __init__(self, message: str, **details: Any) -> None:
        super().__init__("GXP_INVALID_POSITION", message, 400, details)


class FutureEvent(GXPError):
    def __init__(self, observed_at: str) -> None:
        super().__init__("GXP_FUTURE_EVENT", "Event observation time exceeds allowed future clock skew.", 400, {"observed_at": observed_at})


class CommandExpired(GXPError):
    def __init__(self) -> None:
        super().__init__("GXP_COMMAND_EXPIRED", "Command has expired.", 400)


class CommandForbidden(GXPError):
    def __init__(self, operation: object) -> None:
        super().__init__("GXP_COMMAND_FORBIDDEN", "Command operation is not allowed by this profile.", 403, {"operation": operation})


class CommandReplay(GXPError):
    def __init__(self, command_id: str) -> None:
        super().__init__("GXP_COMMAND_REPLAY", "Command ID was already accepted for this target.", 409, {"command_id": command_id})


class Unauthenticated(GXPError):
    def __init__(self) -> None:
        super().__init__("GXP_UNAUTHENTICATED", "Missing or invalid device credential.", 401)


class IdentityMismatch(GXPError):
    def __init__(self) -> None:
        super().__init__("GXP_IDENTITY_MISMATCH", "Credential is not valid for the envelope tenant and device.", 403)


class SequenceConflict(GXPError):
    def __init__(self, sequence: int) -> None:
        super().__init__("GXP_SEQUENCE_CONFLICT", "Sequence was already used by a different event.", 409, {"sequence": sequence})


class StorageExhausted(GXPError):
    def __init__(self, quota_bytes: int) -> None:
        super().__init__("GXP_STORAGE_EXHAUSTED", "Edge spool cannot preserve this event within its quota.", 507, {"quota_bytes": quota_bytes})


class DeliveryRejected(GXPError):
    """A server rejected an event permanently; the edge outbox quarantines it."""

    def __init__(self, code: str, message: str, http_status: int = 400, **details: Any) -> None:
        super().__init__(code, message, http_status, details)


class TransportFailure(GXPError):
    """A transient adapter failure. The edge outbox should retry it."""

    def __init__(self, message: str) -> None:
        super().__init__("GXP_TRANSPORT_FAILURE", message, 503)

