"""Envelope and BusRoot profile validation independent of a transport."""

from __future__ import annotations

import re
import uuid
from datetime import timedelta
from typing import Any, Mapping

from .errors import (
    CommandExpired,
    FutureEvent,
    InvalidPosition,
    MalformedMessage,
    UnsupportedVersion,
)
from .timeutil import parse_instant, utc_now

GXP_VERSION = "0.1"
KINDS = frozenset({"telemetry", "event", "command", "command_ack", "capability", "health"})
DELIVERY_CLASSES = frozenset({"LIVE_EPHEMERAL", "DURABLE_EVENT", "COMMAND", "BULK", "HEARTBEAT"})
CLOCK_QUALITIES = frozenset({"gnss", "network", "estimated", "unknown"})
QUALITY_STATUSES = frozenset({"valid", "degraded", "invalid", "estimated"})
TENANT_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
MAX_FUTURE_SKEW_MS = 300_000


def _mapping(parent: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = parent.get(name)
    if not isinstance(value, Mapping):
        raise MalformedMessage(f"{name} must be an object.", field=name)
    return value


def _required(parent: Mapping[str, Any], name: str) -> Any:
    if name not in parent:
        raise MalformedMessage(f"Missing required field: {name}.", field=name)
    return parent[name]


def _string(parent: Mapping[str, Any], name: str, *, max_length: int = 256) -> str:
    value = _required(parent, name)
    if not isinstance(value, str) or not value or len(value) > max_length:
        raise MalformedMessage(f"{name} must be a non-empty string.", field=name)
    return value


def _positive_int(parent: Mapping[str, Any], name: str, *, maximum: int | None = None) -> int:
    value = _required(parent, name)
    if type(value) is not int or value < 1 or (maximum is not None and value > maximum):
        raise MalformedMessage(f"{name} must be a positive integer.", field=name)
    return value


def _uuid(parent: Mapping[str, Any], name: str) -> str:
    value = _string(parent, name)
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise MalformedMessage(f"{name} must be a UUID.", field=name) from exc
    return value


def _number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidPosition(f"{field_name} must be a number.", field=field_name)
    return float(value)


def _validate_busroot_position(payload: Mapping[str, Any]) -> None:
    for field_name in ("latitude", "longitude", "gps_fix"):
        _required(payload, field_name)
    latitude = _number(payload["latitude"], "payload.latitude")
    longitude = _number(payload["longitude"], "payload.longitude")
    if not -90 <= latitude <= 90:
        raise InvalidPosition("Latitude must be between -90 and 90.", field="payload.latitude")
    if not -180 <= longitude <= 180:
        raise InvalidPosition("Longitude must be between -180 and 180.", field="payload.longitude")
    if type(payload["gps_fix"]) is not bool:
        raise InvalidPosition("gps_fix must be boolean.", field="payload.gps_fix")
    if "speed_kmh" in payload:
        speed = _number(payload["speed_kmh"], "payload.speed_kmh")
        if not 0 <= speed <= 500:
            raise InvalidPosition("speed_kmh must be between 0 and 500.", field="payload.speed_kmh")
    if "heading_deg" in payload:
        heading = _number(payload["heading_deg"], "payload.heading_deg")
        if not 0 <= heading < 360:
            raise InvalidPosition("heading_deg must be between 0 (inclusive) and 360 (exclusive).", field="payload.heading_deg")


def _validate_command(payload: Mapping[str, Any], now) -> None:
    _uuid(payload, "command_id")
    _string(payload, "issuer")
    _string(payload, "operation")
    expires_at = parse_instant(_required(payload, "expires_at"), "payload.expires_at")
    if expires_at <= now:
        raise CommandExpired()
    if "parameters" not in payload or not isinstance(payload["parameters"], Mapping):
        raise MalformedMessage("Command parameters must be an object.", field="payload.parameters")


def validate_envelope(
    envelope: Mapping[str, Any],
    *,
    now=None,
    max_future_skew_ms: int = MAX_FUTURE_SKEW_MS,
) -> None:
    """Validate GXP 0.1 envelope and known profile constraints.

    This performs semantic validation that the schema alone cannot express. It
    intentionally accepts a `gps_fix: false` position into history; freshness
    evaluation later prevents it becoming live state.
    """

    if not isinstance(envelope, Mapping):
        raise MalformedMessage("Envelope must be an object.")
    if envelope.get("gxp") != GXP_VERSION:
        raise UnsupportedVersion(envelope.get("gxp"))
    kind = _string(envelope, "kind")
    if kind not in KINDS:
        raise MalformedMessage("Unknown event kind.", field="kind", value=kind)
    tenant = _string(envelope, "tenant", max_length=128)
    if not TENANT_RE.fullmatch(tenant):
        raise MalformedMessage("tenant contains unsupported characters.", field="tenant")

    device = _mapping(envelope, "device")
    _string(device, "id", max_length=128)
    _uuid(device, "boot_id")
    _positive_int(device, "sequence")

    event = _mapping(envelope, "event")
    _uuid(event, "id")
    _string(event, "type")
    _string(event, "schema")
    _positive_int(event, "schema_version")
    if event.get("content_type") != "application/json":
        raise MalformedMessage("event.content_type must be application/json.", field="event.content_type")

    reference_time = now or utc_now()
    time_data = _mapping(envelope, "time")
    observed_at = parse_instant(_required(time_data, "observed_at"), "time.observed_at")
    if observed_at > reference_time + timedelta(milliseconds=max_future_skew_ms):
        raise FutureEvent(str(time_data["observed_at"]))
    if "sent_at" in time_data:
        parse_instant(time_data["sent_at"], "time.sent_at")
    clock_quality = _string(time_data, "clock_quality")
    if clock_quality not in CLOCK_QUALITIES:
        raise MalformedMessage("Unknown clock quality.", field="time.clock_quality")

    delivery = _mapping(envelope, "delivery")
    delivery_class = _string(delivery, "class")
    if delivery_class not in DELIVERY_CLASSES:
        raise MalformedMessage("Unknown delivery class.", field="delivery.class")
    priority = _required(delivery, "priority")
    if type(priority) is not int or not 0 <= priority <= 9:
        raise MalformedMessage("delivery.priority must be an integer from 0 to 9.", field="delivery.priority")
    if "max_age_ms" in delivery:
        maximum_age = delivery["max_age_ms"]
        if type(maximum_age) is not int or maximum_age < 0:
            raise MalformedMessage("delivery.max_age_ms must be a non-negative integer.", field="delivery.max_age_ms")
    elif delivery_class == "LIVE_EPHEMERAL":
        raise MalformedMessage("LIVE_EPHEMERAL requires delivery.max_age_ms.", field="delivery.max_age_ms")

    quality = _mapping(envelope, "quality")
    quality_status = _string(quality, "status")
    if quality_status not in QUALITY_STATUSES:
        raise MalformedMessage("Unknown quality status.", field="quality.status")
    if "position_accuracy_m" in quality and _number(quality["position_accuracy_m"], "quality.position_accuracy_m") < 0:
        raise InvalidPosition("position_accuracy_m must be non-negative.", field="quality.position_accuracy_m")

    payload = _mapping(envelope, "payload")
    if event["type"] == "vehicle.position":
        _validate_busroot_position(payload)
    if kind == "command":
        _validate_command(payload, reference_time)


def live_eligible(envelope: Mapping[str, Any], received_at, *, max_future_skew_ms: int = MAX_FUTURE_SKEW_MS) -> bool:
    """Return whether an ingested BusRoot position may change live state."""

    if envelope["event"]["type"] != "vehicle.position":
        return False
    if envelope["delivery"]["class"] != "LIVE_EPHEMERAL":
        return False
    if envelope["quality"]["status"] != "valid" or not envelope["payload"].get("gps_fix"):
        return False
    observed_at = parse_instant(envelope["time"]["observed_at"], "time.observed_at")
    if observed_at > received_at + timedelta(milliseconds=max_future_skew_ms):
        return False
    max_age_ms = envelope["delivery"].get("max_age_ms")
    return type(max_age_ms) is int and received_at - observed_at <= timedelta(milliseconds=max_age_ms)

