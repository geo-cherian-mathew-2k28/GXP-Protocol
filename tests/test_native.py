from __future__ import annotations

import unittest
import struct

from gxp.native import (
    ExtensionType,
    FrameType,
    MAGIC,
    NativeFrame,
    NativeFrameDecoder,
    NativeProtocolError,
    PREFIX_FORMAT,
    decode_json_payload,
    encode_json_payload,
)


class NativeFrameTests(unittest.TestCase):
    def test_binary_frame_round_trip(self) -> None:
        original = NativeFrame(
            frame_type=FrameType.EVENT,
            payload=encode_json_payload({"type": "feeder.status", "hopper_percent": 42}),
            extensions={
                ExtensionType.EVENT_ID: b"event-123",
                ExtensionType.TENANT: b"home-demo",
                ExtensionType.DELIVERY_CLASS: b"DURABLE_EVENT",
            },
            session_id=99,
            frame_number=7,
        )
        restored = NativeFrame.decode(original.encode())
        self.assertEqual(restored.frame_type, FrameType.EVENT)
        self.assertEqual(restored.session_id, 99)
        self.assertEqual(restored.frame_number, 7)
        self.assertEqual(restored.extensions[int(ExtensionType.EVENT_ID)], b"event-123")
        self.assertEqual(decode_json_payload(restored.payload)["hopper_percent"], 42)

    def test_stream_decoder_handles_fragmented_and_coalesced_frames(self) -> None:
        first = NativeFrame(FrameType.PING, frame_number=1).encode()
        second = NativeFrame(FrameType.PONG, frame_number=2).encode()
        decoder = NativeFrameDecoder()
        self.assertEqual(decoder.feed(first[:9]), [])
        frames = decoder.feed(first[9:] + second)
        self.assertEqual([frame.frame_type for frame in frames], [FrameType.PING, FrameType.PONG])

    def test_bad_magic_is_rejected(self) -> None:
        encoded = bytearray(NativeFrame(FrameType.PING).encode())
        encoded[0] = 0
        with self.assertRaises(NativeProtocolError) as context:
            NativeFrame.decode(bytes(encoded))
        self.assertEqual(context.exception.code, "GXP_NATIVE_BAD_MAGIC")

    def test_duplicate_extension_type_is_rejected(self) -> None:
        # Header says two one-byte extensions with the same type.
        malformed = struct.pack(PREFIX_FORMAT, MAGIC, 1, int(FrameType.PING), 0, 8, 0, 0, 0)
        malformed += b"\x01\x00\x01a\x01\x00\x01b"
        with self.assertRaises(NativeProtocolError) as context:
            NativeFrame.decode(malformed)
        self.assertEqual(context.exception.code, "GXP_NATIVE_INVALID_EXTENSION")

