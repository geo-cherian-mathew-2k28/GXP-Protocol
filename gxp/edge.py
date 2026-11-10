"""Reference edge agent: durable event construction, spool, retry, and replay."""

from __future__ import annotations

import json
import random
import sqlite3
import uuid
from contextlib import closing
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Protocol

from .errors import DeliveryRejected, GXPError, StorageExhausted
from .models import IngestionAck, OutboxItem
from .timeutil import format_instant, parse_instant, utc_now
from .validation import GXP_VERSION, validate_envelope


class EventTransport(Protocol):
    def send(self, envelope: dict[str, object]) -> IngestionAck: ...


@dataclass(frozen=True)
class BackoffPolicy:
    base_seconds: float = 1.0
    maximum_seconds: float = 300.0

    def delay_seconds(self, attempt: int) -> float:
        """Capped exponential backoff with full jitter."""

        ceiling = min(self.maximum_seconds, self.base_seconds * (2 ** min(attempt, 20)))
        return random.uniform(0, ceiling)


class SQLiteEdgeSpool:
    """Durable SQLite/WAL outbox with explicit quota and replay policy."""

    def __init__(self, path: str | Path, *, quota_bytes: int = 10_000_000, backoff: BackoffPolicy | None = None) -> None:
        self.path = str(path)
        self.quota_bytes = quota_bytes
        self.backoff = backoff or BackoffPolicy()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS outbox (
                    event_id TEXT PRIMARY KEY,
                    delivery_class TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    event_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    next_attempt_at TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'pending',
                    last_error TEXT,
                    size_bytes INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS outbox_ready ON outbox(status, next_attempt_at, priority DESC, created_at);
                CREATE TABLE IF NOT EXISTS sequence_state (
                    tenant TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    boot_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    PRIMARY KEY (tenant, device_id, boot_id)
                );
                """
            )

    @staticmethod
    def _canonical_json(envelope: dict[str, object]) -> str:
        return json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def next_sequence(self, tenant: str, device_id: str, boot_id: str) -> int:
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT sequence FROM sequence_state WHERE tenant = ? AND device_id = ? AND boot_id = ?",
                (tenant, device_id, boot_id),
            ).fetchone()
            next_value = (int(row["sequence"]) if row else 0) + 1
            connection.execute(
                """
                INSERT INTO sequence_state(tenant, device_id, boot_id, sequence) VALUES (?, ?, ?, ?)
                ON CONFLICT(tenant, device_id, boot_id) DO UPDATE SET sequence = excluded.sequence
                """,
                (tenant, device_id, boot_id, next_value),
            )
            connection.commit()
            return next_value

    def _used_bytes(self, connection: sqlite3.Connection) -> int:
        row = connection.execute("SELECT COALESCE(SUM(size_bytes), 0) AS total FROM outbox WHERE status = 'pending'").fetchone()
        return int(row["total"])

    def _make_space_for(self, connection: sqlite3.Connection, required_bytes: int) -> None:
        while self._used_bytes(connection) + required_bytes > self.quota_bytes:
            candidate = connection.execute(
                """
                SELECT event_id FROM outbox
                WHERE status = 'pending' AND delivery_class = 'LIVE_EPHEMERAL'
                ORDER BY created_at ASC
                LIMIT 1
                """
            ).fetchone()
            if candidate is None:
                raise StorageExhausted(self.quota_bytes)
            connection.execute("DELETE FROM outbox WHERE event_id = ?", (candidate["event_id"],))

    def persist(self, envelope: dict[str, object], *, now=None) -> None:
        validate_envelope(envelope)
        event_id = str(envelope["event"]["id"])
        serialized = self._canonical_json(envelope)
        size_bytes = len(serialized.encode("utf-8"))
        if size_bytes > self.quota_bytes:
            raise StorageExhausted(self.quota_bytes)
        timestamp = format_instant(now or utc_now())
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute("SELECT event_json FROM outbox WHERE event_id = ?", (event_id,)).fetchone()
            if existing is not None:
                if existing["event_json"] != serialized:
                    connection.rollback()
                    raise GXPError("GXP_EVENT_ID_COLLISION", "Event ID already exists with different contents.", 409)
                connection.commit()
                return
            self._make_space_for(connection, size_bytes)
            connection.execute(
                """
                INSERT INTO outbox(event_id, delivery_class, priority, event_json, created_at, next_attempt_at, size_bytes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    envelope["delivery"]["class"],
                    envelope["delivery"]["priority"],
                    serialized,
                    timestamp,
                    timestamp,
                    size_bytes,
                ),
            )
            connection.commit()

    def ready(self, *, limit: int = 100, now=None) -> list[OutboxItem]:
        timestamp = format_instant(now or utc_now())
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT event_id, event_json, attempts FROM outbox
                WHERE status = 'pending' AND next_attempt_at <= ?
                ORDER BY priority DESC, created_at ASC
                LIMIT ?
                """,
                (timestamp, limit),
            ).fetchall()
        return [OutboxItem(row["event_id"], json.loads(row["event_json"]), int(row["attempts"])) for row in rows]

    def acknowledge(self, event_id: str) -> None:
        with closing(self._connect()) as connection:
            connection.execute("DELETE FROM outbox WHERE event_id = ?", (event_id,))

    def record_failure(self, event_id: str, error: Exception, *, now=None) -> None:
        current_time = now or utc_now()
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT attempts FROM outbox WHERE event_id = ?", (event_id,)).fetchone()
            if row is None:
                connection.commit()
                return
            attempts = int(row["attempts"]) + 1
            next_time = current_time + timedelta(seconds=self.backoff.delay_seconds(attempts))
            connection.execute(
                "UPDATE outbox SET attempts = ?, next_attempt_at = ?, last_error = ? WHERE event_id = ?",
                (attempts, format_instant(next_time), str(error)[:500], event_id),
            )
            connection.commit()

    def reject(self, event_id: str, error: DeliveryRejected) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "UPDATE outbox SET status = 'rejected', last_error = ? WHERE event_id = ?",
                (str(error)[:500], event_id),
            )

    def depth(self) -> int:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM outbox WHERE status = 'pending'").fetchone()
        return int(row["count"])

    def rejected_count(self) -> int:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM outbox WHERE status = 'rejected'").fetchone()
        return int(row["count"])


class EdgeAgent:
    """Constructs canonical events and preserves them before delivery."""

    def __init__(
        self,
        tenant: str,
        device_id: str,
        spool: SQLiteEdgeSpool,
        *,
        boot_id: str | None = None,
        clock_quality: str = "unknown",
    ) -> None:
        self.tenant = tenant
        self.device_id = device_id
        self.spool = spool
        self.boot_id = boot_id or str(uuid.uuid4())
        self.clock_quality = clock_quality

    def create_event(
        self,
        *,
        kind: str,
        event_type: str,
        schema: str,
        payload: dict[str, object],
        delivery_class: str,
        priority: int,
        max_age_ms: int | None = None,
        observed_at: str | None = None,
        quality: dict[str, object] | None = None,
    ) -> dict[str, object]:
        now = utc_now()
        observed = parse_instant(observed_at, "time.observed_at") if observed_at else now
        sequence = self.spool.next_sequence(self.tenant, self.device_id, self.boot_id)
        delivery: dict[str, object] = {"class": delivery_class, "priority": priority}
        if max_age_ms is not None:
            delivery["max_age_ms"] = max_age_ms
        envelope: dict[str, object] = {
            "gxp": GXP_VERSION,
            "kind": kind,
            "tenant": self.tenant,
            "device": {"id": self.device_id, "boot_id": self.boot_id, "sequence": sequence},
            "event": {
                "id": str(uuid.uuid4()),
                "type": event_type,
                "schema": schema,
                "schema_version": 1,
                "content_type": "application/json",
            },
            "time": {"observed_at": format_instant(observed), "sent_at": format_instant(now), "clock_quality": self.clock_quality},
            "delivery": delivery,
            "quality": quality or {"status": "valid"},
            "payload": payload,
        }
        validate_envelope(envelope, now=now)
        self.spool.persist(envelope, now=now)
        return envelope

    def flush(self, transport: EventTransport, *, limit: int = 100, now=None) -> dict[str, int]:
        results = {"acknowledged": 0, "retried": 0, "rejected": 0}
        for item in self.spool.ready(limit=limit, now=now):
            try:
                acknowledgement = transport.send(item.event)
                if acknowledgement.status not in {"accepted", "duplicate"}:
                    raise GXPError("GXP_INVALID_ACK", "Transport returned an unrecognised acknowledgement.", 502)
                self.spool.acknowledge(item.event_id)
                results["acknowledged"] += 1
            except DeliveryRejected as error:
                self.spool.reject(item.event_id, error)
                results["rejected"] += 1
            except Exception as error:  # Network and unexpected adapter errors remain retryable.
                self.spool.record_failure(item.event_id, error, now=now)
                results["retried"] += 1
        return results

