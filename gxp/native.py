"""Experimental GXP/1 native binary frame codec.

This module establishes a custom application wire boundary. It deliberately
does not implement custom cryptography, congestion control, or IP transport;
GXP/TCP is intended to run inside TLS and a GXP/QUIC binding can reuse QUIC.
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Mapping

from .errors import GXPError

MAGIC = b"GX"
NATIVE_VERSION = 1
PREFIX_FORMAT = "!2sBBHHIQQ"
PREFIX_SIZE = struct.calcsize(PREFIX_FORMAT)
DEFAULT_MAX_FRAME_BYTES = 1_048_576


class FrameType(IntEnum):
    CLIENT_HELLO = 1
    SERVER_HELLO = 2
    AUTH_RESULT = 3
    RESUME = 4
    RESUME_RESULT = 5
    EVENT = 10
    ACK = 11
    COMMAND = 12
    COMMAND_RESULT = 13
    CREDIT = 14
    PING = 15
    PONG = 16
    ERROR = 17
    CLOSE = 18


class ExtensionType(IntEnum):
    EVENT_ID = 1
    TENANT = 2
    DEVICE_ID = 3
    BOOT_ID = 4
    SEQUENCE = 5
    PROFILE = 6
    OBSERVED_AT = 7
    DELIVERY_CLASS = 8
    ACK_RANGE = 9
    ERROR_CODE = 10
    CAPABILITIES = 11
    CONTENT_TYPE = 12


class NativeProtocolError(GXPError):
    def __init__(self, code: str, message: str, **details: object) -> None:
        super().__init__(code, message, 400, dict(details))


def _bounded_uint(name: str, value: int, maximum: int) -> None:
    if type(value) is not int or not 0 <= value <= maximum:
        raise NativeProtocolError("GXP_NATIVE_INVALID_FRAME", f"{name} is out of range.")


def encode_extensions(extensions: Mapping[int | ExtensionType, bytes]) -> bytes:
    """Encode a compact typed extension area with one value per registered type."""

    encoded = bytearray()
    for extension_type, value in extensions.items():
        _bounded_uint("extension type", int(extension_type), 255)
        if not isinstance(value, bytes) or len(value) > 65_535:
            raise NativeProtocolError("GXP_NATIVE_INVALID_EXTENSION", "Extension value must be bytes up to 65535 bytes.")
        encoded.extend(struct.pack("!BH", int(extension_type), len(value)))
        encoded.extend(value)
    return bytes(encoded)


def decode_extensions(encoded: bytes) -> dict[int, bytes]:
    """Decode a strict extension area; duplicates are protocol errors."""

    extensions: dict[int, bytes] = {}
    position = 0
    while position < len(encoded):
        if len(encoded) - position < 3:
            raise NativeProtocolError("GXP_NATIVE_INVALID_EXTENSION", "Truncated extension header.")
        extension_type, length = struct.unpack("!BH", encoded[position : position + 3])
        position += 3
        if len(encoded) - position < length:
            raise NativeProtocolError("GXP_NATIVE_INVALID_EXTENSION", "Truncated extension value.")
        if extension_type in extensions:
            raise NativeProtocolError("GXP_NATIVE_INVALID_EXTENSION", "Duplicate extension type.", extension_type=extension_type)
        extensions[extension_type] = encoded[position : position + length]
        position += length
    return extensions


@dataclass(frozen=True)
class NativeFrame:
    """One complete GXP/1 frame, independent of a TCP or QUIC binding."""

    frame_type: FrameType
    payload: bytes = b""
    extensions: Mapping[int | ExtensionType, bytes] = field(default_factory=dict)
    flags: int = 0
    session_id: int = 0
    frame_number: int = 0
    version: int = NATIVE_VERSION

    def encode(self, *, maximum_frame_bytes: int = DEFAULT_MAX_FRAME_BYTES) -> bytes:
        _bounded_uint("version", self.version, 255)
        _bounded_uint("flags", self.flags, 65_535)
        _bounded_uint("session ID", self.session_id, (1 << 64) - 1)
        _bounded_uint("frame number", self.frame_number, (1 << 64) - 1)
        if not isinstance(self.payload, bytes):
            raise NativeProtocolError("GXP_NATIVE_INVALID_FRAME", "Payload must be bytes.")
        extension_bytes = encode_extensions(self.extensions)
        total_length = PREFIX_SIZE + len(extension_bytes) + len(self.payload)
        if total_length > maximum_frame_bytes:
            raise NativeProtocolError("GXP_NATIVE_FRAME_TOO_LARGE", "Frame exceeds negotiated maximum.", maximum_frame_bytes=maximum_frame_bytes)
        prefix = struct.pack(
            PREFIX_FORMAT,
            MAGIC,
            self.version,
            int(self.frame_type),
            self.flags,
            len(extension_bytes),
            len(self.payload),
            self.session_id,
            self.frame_number,
        )
        return prefix + extension_bytes + self.payload

    @classmethod
    def decode(cls, encoded: bytes, *, maximum_frame_bytes: int = DEFAULT_MAX_FRAME_BYTES) -> "NativeFrame":
        if len(encoded) < PREFIX_SIZE:
            raise NativeProtocolError("GXP_NATIVE_TRUNCATED_FRAME", "Frame is shorter than the native prefix.")
        magic, version, frame_type, flags, extension_length, payload_length, session_id, frame_number = struct.unpack(
            PREFIX_FORMAT, encoded[:PREFIX_SIZE]
        )
        if magic != MAGIC:
            raise NativeProtocolError("GXP_NATIVE_BAD_MAGIC", "Frame does not begin with GXP magic bytes.")
        if version != NATIVE_VERSION:
            raise NativeProtocolError("GXP_NATIVE_UNSUPPORTED_VERSION", "Unsupported native GXP version.", version=version)
        expected_length = PREFIX_SIZE + extension_length + payload_length
        if expected_length > maximum_frame_bytes:
            raise NativeProtocolError("GXP_NATIVE_FRAME_TOO_LARGE", "Frame exceeds negotiated maximum.", maximum_frame_bytes=maximum_frame_bytes)
        if len(encoded) != expected_length:
            raise NativeProtocolError("GXP_NATIVE_TRUNCATED_FRAME", "Frame length does not match its prefix.")
        try:
            typed_frame = FrameType(frame_type)
        except ValueError as exc:
            raise NativeProtocolError("GXP_NATIVE_UNKNOWN_FRAME", "Unknown frame type.", frame_type=frame_type) from exc
        extension_start = PREFIX_SIZE
        extension_end = extension_start + extension_length
        return cls(
            frame_type=typed_frame,
            payload=encoded[extension_end:],
            extensions=decode_extensions(encoded[extension_start:extension_end]),
            flags=flags,
            session_id=session_id,
            frame_number=frame_number,
            version=version,
        )


class NativeFrameDecoder:
    """Incrementally extracts complete GXP/1 frames from a byte stream."""

    def __init__(self, *, maximum_frame_bytes: int = DEFAULT_MAX_FRAME_BYTES) -> None:
        self.maximum_frame_bytes = maximum_frame_bytes
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[NativeFrame]:
        if not isinstance(data, bytes):
            raise TypeError("Native frame decoder accepts bytes only.")
        self._buffer.extend(data)
        frames: list[NativeFrame] = []
        while len(self._buffer) >= PREFIX_SIZE:
            magic, version, _, _, extension_length, payload_length, _, _ = struct.unpack(PREFIX_FORMAT, self._buffer[:PREFIX_SIZE])
            if magic != MAGIC:
                raise NativeProtocolError("GXP_NATIVE_BAD_MAGIC", "Stream does not begin with GXP magic bytes.")
            if version != NATIVE_VERSION:
                raise NativeProtocolError("GXP_NATIVE_UNSUPPORTED_VERSION", "Unsupported native GXP version.", version=version)
            frame_length = PREFIX_SIZE + extension_length + payload_length
            if frame_length > self.maximum_frame_bytes:
                raise NativeProtocolError("GXP_NATIVE_FRAME_TOO_LARGE", "Frame exceeds negotiated maximum.", maximum_frame_bytes=self.maximum_frame_bytes)
            if len(self._buffer) < frame_length:
                break
            frame_bytes = bytes(self._buffer[:frame_length])
            del self._buffer[:frame_length]
            frames.append(NativeFrame.decode(frame_bytes, maximum_frame_bytes=self.maximum_frame_bytes))
        return frames


def encode_json_payload(value: object) -> bytes:
    """Bridge representation until GXP/1's native payload encoding is frozen."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def decode_json_payload(payload: bytes) -> object:
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NativeProtocolError("GXP_NATIVE_INVALID_PAYLOAD", "Expected a UTF-8 JSON bridge payload.") from exc

