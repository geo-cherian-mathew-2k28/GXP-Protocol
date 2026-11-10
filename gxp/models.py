"""Small shared data structures used by the reference implementation."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class IngestionAck:
    """A durable GXP ingestion acknowledgement, not a business acknowledgement."""

    status: str
    event_id: str
    received_at: str
    live_state_updated: bool = False

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class OutboxItem:
    event_id: str
    event: dict[str, object]
    attempts: int

