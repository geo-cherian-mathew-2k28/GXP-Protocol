"""Transactional reference ingestion, deduplication, and BusRoot live state."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
from contextlib import closing
from datetime import timedelta
from pathlib import Path
from typing import Any, Mapping

from .errors import CommandForbidden, CommandReplay, IdentityMismatch, SequenceConflict, Unauthenticated
from .models import IngestionAck
from .timeutil import format_instant, parse_instant, utc_now
from .validation import live_eligible, validate_envelope

ALLOWED_COMMAND_OPERATIONS = frozenset({"diagnostics.snapshot", "reporting.interval.set", "status.request"})


class IngestionStore:
    """Single-node durable GXP ingestion reference backed by SQLite/WAL.

    Every ingestion acknowledgement follows one SQLite transaction that commits
    dedupe state, history, sequence observation, command record (if relevant),
    and any permitted live-state change.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    tenant TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    token_digest TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (tenant, device_id)
                );
                CREATE TABLE IF NOT EXISTS events (
                    tenant TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    boot_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    delivery_class TEXT NOT NULL,
                    live_eligible INTEGER NOT NULL,
                    raw_json TEXT NOT NULL,
                    PRIMARY KEY (tenant, device_id, event_id)
                );
                CREATE INDEX IF NOT EXISTS events_device_observed ON events(tenant, device_id, observed_at);
                CREATE TABLE IF NOT EXISTS sequence_observations (
                    tenant TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    boot_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    event_id TEXT NOT NULL,
                    PRIMARY KEY (tenant, device_id, boot_id, sequence)
                );
                CREATE TABLE IF NOT EXISTS live_state (
                    tenant TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    stale_after TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    quality_json TEXT NOT NULL,
                    PRIMARY KEY (tenant, device_id)
                );
                CREATE TABLE IF NOT EXISTS commands (
                    tenant TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    command_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    issuer TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    state TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    PRIMARY KEY (tenant, device_id, command_id)
                );
                """
            )

    def bootstrap_device(self, tenant: str, device_id: str, *, replace: bool = False) -> str:
        """Create a development credential and return it exactly once to the caller."""

        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        created_at = format_instant(utc_now())
        with closing(self._connect()) as connection:
            existing = connection.execute(
                "SELECT 1 FROM devices WHERE tenant = ? AND device_id = ?", (tenant, device_id)
            ).fetchone()
            if existing and not replace:
                raise ValueError("Device already exists; use replace=True to rotate its development token.")
            connection.execute(
                """
                INSERT INTO devices(tenant, device_id, token_digest, active, created_at) VALUES (?, ?, ?, 1, ?)
                ON CONFLICT(tenant, device_id) DO UPDATE SET token_digest = excluded.token_digest, active = 1, created_at = excluded.created_at
                """,
                (tenant, device_id, digest, created_at),
            )
        return token

    def authenticate(self, tenant: str, device_id: str, token: str | None) -> None:
        if not token:
            raise Unauthenticated()
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT token_digest, active FROM devices WHERE tenant = ? AND device_id = ?", (tenant, device_id)
            ).fetchone()
        actual = hashlib.sha256(token.encode("utf-8")).hexdigest()
        if row is None or not row["active"] or not hmac.compare_digest(row["token_digest"], actual):
            raise Unauthenticated()

    @staticmethod
    def _canonical_json(value: Mapping[str, Any]) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def _insert_command(self, connection: sqlite3.Connection, envelope: Mapping[str, Any], received_at: str) -> None:
        payload = envelope["payload"]
        operation = payload["operation"]
        if operation not in ALLOWED_COMMAND_OPERATIONS:
            raise CommandForbidden(operation)
        tenant = envelope["tenant"]
        device_id = envelope["device"]["id"]
        existing = connection.execute(
            "SELECT event_id FROM commands WHERE tenant = ? AND device_id = ? AND command_id = ?",
            (tenant, device_id, payload["command_id"]),
        ).fetchone()
        if existing is not None and existing["event_id"] != envelope["event"]["id"]:
            raise CommandReplay(payload["command_id"])
        if existing is None:
            connection.execute(
                """
                INSERT INTO commands(tenant, device_id, command_id, event_id, operation, issuer, expires_at, state, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'RECEIVED', ?)
                """,
                (
                    tenant,
                    device_id,
                    payload["command_id"],
                    envelope["event"]["id"],
                    operation,
                    payload["issuer"],
                    payload["expires_at"],
                    received_at,
                ),
            )

    def ingest(self, envelope: Mapping[str, Any], *, received_at=None) -> IngestionAck:
        receipt_time = received_at or utc_now()
        validate_envelope(envelope, now=receipt_time)
        receipt = format_instant(receipt_time)
        tenant = envelope["tenant"]
        device_id = envelope["device"]["id"]
        event_id = envelope["event"]["id"]
        boot_id = envelope["device"]["boot_id"]
        sequence = envelope["device"]["sequence"]
        raw_json = self._canonical_json(envelope)
        eligible = live_eligible(envelope, receipt_time)
        live_state_updated = False

        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            duplicate = connection.execute(
                "SELECT received_at FROM events WHERE tenant = ? AND device_id = ? AND event_id = ?",
                (tenant, device_id, event_id),
            ).fetchone()
            if duplicate is not None:
                connection.commit()
                return IngestionAck("duplicate", str(event_id), duplicate["received_at"], False)

            sequence_row = connection.execute(
                """
                SELECT event_id FROM sequence_observations
                WHERE tenant = ? AND device_id = ? AND boot_id = ? AND sequence = ?
                """,
                (tenant, device_id, boot_id, sequence),
            ).fetchone()
            if sequence_row is not None and sequence_row["event_id"] != event_id:
                connection.rollback()
                raise SequenceConflict(int(sequence))

            if envelope["kind"] == "command":
                self._insert_command(connection, envelope, receipt)

            connection.execute(
                """
                INSERT INTO events(tenant, device_id, event_id, boot_id, sequence, kind, event_type, observed_at, received_at, delivery_class, live_eligible, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tenant,
                    device_id,
                    event_id,
                    boot_id,
                    sequence,
                    envelope["kind"],
                    envelope["event"]["type"],
                    envelope["time"]["observed_at"],
                    receipt,
                    envelope["delivery"]["class"],
                    int(eligible),
                    raw_json,
                ),
            )
            connection.execute(
                """
                INSERT INTO sequence_observations(tenant, device_id, boot_id, sequence, event_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (tenant, device_id, boot_id, sequence, event_id),
            )

            if eligible:
                previous = connection.execute(
                    "SELECT observed_at FROM live_state WHERE tenant = ? AND device_id = ?", (tenant, device_id)
                ).fetchone()
                observed_at = parse_instant(envelope["time"]["observed_at"], "time.observed_at")
                previous_time = parse_instant(previous["observed_at"], "live_state.observed_at") if previous else None
                if previous_time is None or observed_at > previous_time:
                    stale_after = observed_at + timedelta(
                        milliseconds=int(envelope["delivery"]["max_age_ms"])
                    )
                    connection.execute(
                        """
                        INSERT INTO live_state(tenant, device_id, event_id, observed_at, received_at, stale_after, payload_json, quality_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(tenant, device_id) DO UPDATE SET
                            event_id = excluded.event_id,
                            observed_at = excluded.observed_at,
                            received_at = excluded.received_at,
                            stale_after = excluded.stale_after,
                            payload_json = excluded.payload_json,
                            quality_json = excluded.quality_json
                        """,
                        (
                            tenant,
                            device_id,
                            event_id,
                            envelope["time"]["observed_at"],
                            receipt,
                            format_instant(stale_after),
                            self._canonical_json(envelope["payload"]),
                            self._canonical_json(envelope["quality"]),
                        ),
                    )
                    live_state_updated = True
            connection.commit()

        return IngestionAck("accepted", str(event_id), receipt, live_state_updated)

    def get_live_state(self, tenant: str, device_id: str, *, now=None) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM live_state WHERE tenant = ? AND device_id = ?", (tenant, device_id)
            ).fetchone()
        if row is None:
            return None
        timestamp = now or utc_now()
        return {
            "tenant": row["tenant"],
            "device_id": row["device_id"],
            "event_id": row["event_id"],
            "observed_at": row["observed_at"],
            "received_at": row["received_at"],
            "stale_after": row["stale_after"],
            "stale": timestamp > parse_instant(row["stale_after"], "live_state.stale_after"),
            "payload": json.loads(row["payload_json"]),
            "quality": json.loads(row["quality_json"]),
        }

    def event_count(self) -> int:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM events").fetchone()
        return int(row["count"])

