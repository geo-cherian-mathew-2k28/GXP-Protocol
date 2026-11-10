"""Loopback-oriented HTTP development server for the GXP ingestion contract."""

from __future__ import annotations

import json
import ssl
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import unquote

from .errors import GXPError, IdentityMismatch, MalformedMessage, Unauthenticated
from .ingestion import IngestionStore


class GXPHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address, request_handler, store: IngestionStore):
        super().__init__(server_address, request_handler)
        self.store = store


class GXPRequestHandler(BaseHTTPRequestHandler):
    server: GXPHTTPServer
    protocol_version = "HTTP/1.1"
    max_body_bytes = 1_000_000

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        """Avoid default request logging; production logging needs redaction/audit design."""

    def _write_json(self, status: int, body: dict[str, object]) -> None:
        encoded = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def _write_error(self, error: GXPError) -> None:
        self._write_json(error.http_status, {"error": error.as_dict()})

    @staticmethod
    def _bearer_token(value: str | None) -> str | None:
        if not value or not value.startswith("Bearer "):
            return None
        token = value[7:].strip()
        return token or None

    def _read_envelope(self) -> dict[str, Any]:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.lower().startswith("application/json"):
            raise MalformedMessage("Content-Type must be application/json.", field="Content-Type")
        length_header = self.headers.get("Content-Length")
        try:
            length = int(length_header or "")
        except ValueError as exc:
            raise MalformedMessage("Content-Length is required.", field="Content-Length") from exc
        if length < 1 or length > self.max_body_bytes:
            raise MalformedMessage("Request body size is invalid.", field="Content-Length")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MalformedMessage("Request body must be UTF-8 JSON.") from exc
        if not isinstance(payload, dict):
            raise MalformedMessage("Envelope must be a JSON object.")
        return payload

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/events":
            self._write_json(HTTPStatus.NOT_FOUND, {"error": {"code": "GXP_NOT_FOUND", "message": "Unknown endpoint."}})
            return
        try:
            envelope = self._read_envelope()
            device = envelope.get("device")
            tenant = envelope.get("tenant")
            if not isinstance(device, dict) or not isinstance(device.get("id"), str) or not isinstance(tenant, str):
                raise Unauthenticated()
            self.server.store.authenticate(tenant, device["id"], self._bearer_token(self.headers.get("Authorization")))
            acknowledgement = self.server.store.ingest(envelope)
            self._write_json(HTTPStatus.CREATED if acknowledgement.status == "accepted" else HTTPStatus.OK, acknowledgement.as_dict())
        except GXPError as error:
            self._write_error(error)
        except Exception:
            self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": {"code": "GXP_INTERNAL", "message": "Internal server error."}})

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            self._write_json(HTTPStatus.OK, {"status": "ok"})
            return
        parts = self.path.split("/")
        # /v1/live/{tenant}/{device}; deliberately loopback-only development API.
        if len(parts) == 5 and parts[1] == "v1" and parts[2] == "live":
            state = self.server.store.get_live_state(unquote(parts[3]), unquote(parts[4]))
            if state is None:
                self._write_json(HTTPStatus.NOT_FOUND, {"error": {"code": "GXP_NOT_FOUND", "message": "No live state for device."}})
            else:
                self._write_json(HTTPStatus.OK, state)
            return
        self._write_json(HTTPStatus.NOT_FOUND, {"error": {"code": "GXP_NOT_FOUND", "message": "Unknown endpoint."}})


def serve(
    store: IngestionStore,
    *,
    host: str = "127.0.0.1",
    port: int = 8080,
    certfile: str | None = None,
    keyfile: str | None = None,
    client_ca_file: str | None = None,
) -> None:
    """Run the development server. Production needs an approved deployment path."""

    httpd = GXPHTTPServer((host, port), GXPRequestHandler, store)
    if certfile:
        if not keyfile:
            raise ValueError("keyfile is required when certfile is configured")
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile, keyfile)
        if client_ca_file:
            context.load_verify_locations(client_ca_file)
            context.verify_mode = ssl.CERT_REQUIRED
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    httpd.serve_forever()

