"""HTTP/JSON transport adapter with optional TLS client authentication."""

from __future__ import annotations

import json
import ssl
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..errors import DeliveryRejected, TransportFailure
from ..models import IngestionAck


@dataclass
class HttpTransport:
    endpoint: str
    token: str
    timeout_seconds: float = 10.0
    cafile: str | None = None
    certfile: str | None = None
    keyfile: str | None = None

    def _ssl_context(self):
        if not self.endpoint.startswith("https://"):
            return None
        context = ssl.create_default_context(cafile=self.cafile)
        if self.certfile:
            context.load_cert_chain(self.certfile, self.keyfile)
        return context

    @staticmethod
    def _decode_response(body: bytes) -> dict[str, Any]:
        try:
            parsed = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TransportFailure("Server returned a non-JSON response.") from exc
        if not isinstance(parsed, dict):
            raise TransportFailure("Server returned a malformed JSON response.")
        return parsed

    def send(self, envelope: dict[str, object]) -> IngestionAck:
        body = json.dumps(envelope, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        request = Request(
            self.endpoint,
            data=body,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {self.token}",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds, context=self._ssl_context()) as response:
                payload = self._decode_response(response.read())
        except HTTPError as error:
            response = self._decode_response(error.read())
            error_body = response.get("error", response)
            if not isinstance(error_body, dict):
                raise TransportFailure(f"Server returned HTTP {error.code} without a structured error.")
            raise DeliveryRejected(
                str(error_body.get("code", "GXP_HTTP_REJECTED")),
                str(error_body.get("message", f"Server rejected event with HTTP {error.code}.")),
                error.code,
                **(error_body.get("details") if isinstance(error_body.get("details"), dict) else {}),
            ) from error
        except (URLError, TimeoutError, ssl.SSLError, OSError) as error:
            raise TransportFailure(f"HTTP delivery failed: {error}") from error

        if payload.get("status") not in {"accepted", "duplicate"}:
            raise TransportFailure("Server returned a response without an ingestion acknowledgement.")
        try:
            return IngestionAck(
                str(payload["status"]),
                str(payload["event_id"]),
                str(payload["received_at"]),
                bool(payload.get("live_state_updated", False)),
            )
        except KeyError as error:
            raise TransportFailure("Server acknowledgement is missing a required field.") from error

